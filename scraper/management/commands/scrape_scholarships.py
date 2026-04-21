import os
import re
import time
import hashlib
import unicodedata
import requests
from io import BytesIO
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import textwrap

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.text import slugify

from blog.models import Opportunity, Category, ScrapeModels, Country, EducationLevel


# ══════════════════════════════════════════════════════════════════
# 1. TITLE REWRITER
# ══════════════════════════════════════════════════════════════════

class TitleRewriter:
    """
    Rewrites the scraped title to be non-verbatim while keeping all
    SEO-valuable tokens (programme name, year, funding keywords).
    Also fixes Unicode artefacts like the replacement char (□/□).
    """

    PREFIXES = [
        "Apply Now:",
        "Now Open:",
        "Applications Open:",
        "Accepting Applications:",
        "Open for Applications:",
        "{year} Applications Open:",
        "Deadline Approaching:",
    ]

    STRIP_PHRASES = [
        r"\(fully[\s-]funded\)",
        r"fully[\s-]funded\s*[-\u2013\u2014]?",
        r"cycle\s*\d+",
        r"call for applications",
        r"applications?\s+(?:are\s+)?(?:now\s+)?open",
        r"\s*[-\u2013\u2014|]\s*$",
    ]

    NORMALISE = {
        "scholarships": "Scholarships", "scholarship": "Scholarship",
        "fellowship": "Fellowship",     "fellowships": "Fellowships",
        "internship": "Internship",     "grant": "Grant",
        "award": "Award",
    }

    def rewrite(self, raw: str, year: int = None) -> str:
        if not raw:
            return raw

        # Fix broken unicode
        title = raw.encode("utf-8", "ignore").decode("utf-8")
        title = title.replace("\ufffd", "").replace("\u00c2", "")
        title = unicodedata.normalize("NFKC", title)
        title = re.sub(r"[^\x09\x0a\x0d\x20-\x7e\u00a0-\uffef]", "", title)
        title = re.sub(r"\s+", " ", title).strip()

        if not year:
            m = re.search(r"\b(20\d{2})\b", title)
            year = int(m.group(1)) if m else datetime.now().year

        for pat in self.STRIP_PHRASES:
            title = re.sub(pat, " ", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+", " ", title).strip(" \u2013\u2014-")

        has_year = bool(re.search(r"\b20\d{2}\b", title))
        if not has_year:
            title = f"{title} {year}"

        idx    = int(hashlib.md5(raw.encode()).hexdigest(), 16) % len(self.PREFIXES)
        prefix = self.PREFIXES[idx]
        if "{year}" in prefix:
            prefix = prefix.format(year=year)

        result = f"{prefix} {title}"
        for k, v in self.NORMALISE.items():
            result = re.sub(rf"\b{k}\b", v, result, flags=re.IGNORECASE)

        return re.sub(r"\s+", " ", result).strip()


# ══════════════════════════════════════════════════════════════════
# 2. FIELD EXTRACTOR
# ══════════════════════════════════════════════════════════════════

class FieldExtractor:

    TYPE_KEYWORDS = {
        "Fellowship":    ["fellowship", "fellow"],
        "Scholarship":   ["scholarship", "bursary"],
        "Internship":    ["internship", "intern"],
        "Grant":         ["grant", "seed fund", "funding call"],
        "Assistantship": ["assistantship", "research assistant", "teaching assistant"],
        "Competition":   ["competition", "contest", "hackathon", "prize"],
        "Event":         ["conference", "workshop", "seminar", "summit"],
        "Job":           ["job", "vacancy", "position", "career"],
    }

    FUNDING_KEYWORDS = {
        "Fully Funded":       ["fully funded", "full funding", "all expenses covered",
                               "full scholarship", "covers tuition and", "includes airfare",
                               "travel grant", "accommodation provided"],
        "Tuition Fee Waiver": ["tuition waiver", "fee waiver", "waives tuition"],
        "Stipend Only":       ["stipend only", "living allowance only"],
        "Unpaid":             ["unpaid", "voluntary", "no compensation"],
        "Partial Funding":    ["partial funding", "co-funded", "partial scholarship"],
    }

    EDUCATION_KEYWORDS = {
        "Undergraduate": ["undergraduate", "bachelor", "b.sc", "b.a.", "undergrad"],
        "Masters":       ["master", "msc", "m.a.", "postgraduate", "graduate students"],
        "PhD":           ["phd", "ph.d", "doctoral", "doctorate"],
        "Postdoctoral":  ["postdoctoral", "post-doctoral", "postdoc"],
        "High School":   ["high school", "secondary school", "grade 12", "a-level"],
        "Any":           ["open to all", "all levels", "any degree"],
    }

    STIPEND_PATTERNS = [
        r"[\$\u20ac\xa3]\s*[\d,]+(?:\.\d+)?\s*(?:per month|monthly|/month|per year|annually|/year)",
        r"[\d,]+\s+(?:USD|EUR|GBP|CAD|AUD)\s*(?:per month|monthly|per year)",
        r"(?:stipend|allowance|salary)\s+of\s+[\$\u20ac\xa3][\d,]+",
    ]

    AMOUNT_PATTERNS = [
        r"up to\s+[\$\u20ac\xa3][\d,]+",
        r"worth\s+[\$\u20ac\xa3][\d,]+",
        r"[\$\u20ac\xa3]\s*[\d,]+(?:,\d{3})*(?:\.\d+)?",
        r"[\d,]+\s*(?:USD|EUR|GBP|CAD|AUD)",
    ]

    KNOWN_COUNTRIES = [
        "United States","USA","United Kingdom","UK","Canada","Australia",
        "Germany","France","Japan","China","India","Brazil","South Africa",
        "Netherlands","Sweden","Switzerland","Italy","Spain","Mexico",
        "Ireland","New Zealand","Singapore","South Korea","Norway","Denmark",
        "Finland","Belgium","Austria","Russia","Poland","Argentina","Turkey",
        "Saudi Arabia","UAE","United Arab Emirates","Taiwan","Hong Kong",
        "Philippines","Bangladesh","Pakistan","Nigeria","Kenya","Ghana",
        "Ethiopia","Uganda","Tanzania","Egypt","Morocco","Nepal","Sri Lanka",
        "Vietnam","Thailand","Indonesia","Malaysia","Colombia","Peru","Chile",
    ]

    TARGET_SIGNALS = [
        "open to","eligible","applicants from","citizens of","nationals of",
        "students from","residents of","developing countries",
        "all nationalities","international students",
    ]

    HOST_SIGNALS = [
        "hosted in","held in","located in","based in","university in",
        "institution in","programme in","study in","research in",
    ]

    def get_opportunity_type(self, title, text):
        combined = (title + " " + text).lower()
        for t, kws in self.TYPE_KEYWORDS.items():
            if any(k in combined for k in kws):
                return t
        return "Scholarship"

    def get_funding_type(self, text):
        t = text.lower()
        for ft, kws in self.FUNDING_KEYWORDS.items():
            if any(k in t for k in kws):
                return ft
        if "tuition" in t and ("stipend" in t or "allowance" in t):
            return "Fully Funded"
        return "Partial Funding"

    def get_funding_amount(self, text):
        for pat in self.AMOUNT_PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        return ""

    def get_stipend(self, text):
        for pat in self.STIPEND_PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return True, m.group(0).strip()
        if re.search(r'\bstipend\b|\ballowance\b', text, re.IGNORECASE):
            return True, ""
        return False, ""

    def get_education_levels(self, text):
        t = text.lower()
        found = [lvl for lvl, kws in self.EDUCATION_KEYWORDS.items()
                 if any(k in t for k in kws)]
        return found if found else ["Any"]

    def get_countries(self, text):
        target, host = [], []
        for sentence in re.split(r'[.!?\n]', text):
            sl = sentence.lower()
            is_target = any(sig in sl for sig in self.TARGET_SIGNALS)
            is_host   = any(sig in sl for sig in self.HOST_SIGNALS)
            for country in self.KNOWN_COUNTRIES:
                if country.lower() in sl:
                    if is_host and country not in host:
                        host.append(country)
                    elif country not in target:
                        target.append(country)
        if re.search(r'all nationalities|international students|open to all',
                     text, re.IGNORECASE):
            target = ["International (All Countries)"]
        return target[:10], host[:5]

    def get_meta(self, title, desc_html, opp_type, funding):
        plain = re.sub(r'<[^>]+>', ' ', desc_html)
        plain = re.sub(r'\s+', ' ', plain).strip()
        return {
            "meta_title":       f"{title} – {opp_type} | MastersGrant"[:60],
            "meta_description": f"{funding} {opp_type}: {plain[:110]}..."[:160],
            "focus_keywords":   f"{opp_type.lower()}, {funding.lower()}, "
                                f"{slugify(title).replace('-',' ')}",
        }


# ══════════════════════════════════════════════════════════════════
# 3. RICH CONTENT SCRAPER
# ══════════════════════════════════════════════════════════════════

class RichContentScraper:
    """
    Extracts granular facts from the article body and assembles them
    into structured HTML sections.  No sentence-level copying.
    """

    SECTION_KEYS = {
        "overview":     ["about","overview","introduction","background","description","program","programme"],
        "eligibility":  ["eligible","eligib","criteria","requirement","who can","applicant","qualification"],
        "benefits":     ["benefit","fund","stipend","tuition","award","cover","grant",
                         "allowance","salary","fellowship","financial","support"],
        "how_to_apply": ["apply","application","submit","register","step","procedure",
                         "how to","upload","portal","process"],
        "important":    ["note","important","attention","please","ensure","required document",
                         "document","passport","transcript","recommendation"],
    }

    SECTION_HEADING_MAP = {
        "overview":     "About the Opportunity",
        "eligibility":  "Eligibility Criteria",
        "benefits":     "Funding & Benefits",
        "how_to_apply": "How to Apply",
        "important":    "Important Notes",
    }

    SECTION_ICONS = {
        "overview":     "",
        "eligibility":  "&#10004; ",
        "benefits":     "&#128176; ",
        "how_to_apply": "&#8594; ",
        "important":    "&#9888; ",
    }

    def extract(self, content_tag, raw_title: str) -> dict:
        sections = {k: [] for k in self.SECTION_KEYS}
        seen = set()

        for el in content_tag.find_all(["h2","h3","h4","p","li","dd"]):
            if el.name in ("h2","h3","h4"):
                continue  # skip source headings; we generate our own

            raw = el.get_text(" ", strip=True)
            raw = unicodedata.normalize("NFKC", raw)
            raw = re.sub(r"\ufffd", "", raw)
            raw = re.sub(r"\s+", " ", raw).strip()

            if not raw or len(raw) < 15 or raw in seen:
                continue
            if raw.lower() == raw_title.lower():
                continue

            seen.add(raw)
            rl = raw.lower()

            best_section, best_score = None, 0
            for section, keywords in self.SECTION_KEYS.items():
                score = sum(1 for k in keywords if k in rl)
                if score > best_score:
                    best_score, best_section = score, section

            if best_section and best_score > 0:
                if len(raw.split()) > 35:
                    for chunk in self._split_long(raw)[:4]:
                        if len(sections[best_section]) < 10:
                            sections[best_section].append(chunk)
                else:
                    if len(sections[best_section]) < 10:
                        sections[best_section].append(raw)

        return sections

    def _split_long(self, text: str):
        parts = re.split(r'(?<=[;:,])\s+', text)
        out   = []
        for p in parts:
            words = p.split()
            if len(words) <= 25:
                chunk = p.strip(" ,;:")
                if len(chunk) > 14:
                    out.append(chunk)
            else:
                for i in range(0, len(words), 20):
                    chunk = " ".join(words[i:i+20]).strip(" ,;:")
                    if len(chunk) > 14:
                        out.append(chunk)
        return out

    def build_html(self, sections, funding_type, funding_amount,
                   stipend_amount, deadline_note,
                   target_countries, host_countries, official_link):

        def ul(items, icon=""):
            if not items:
                return "<p>Visit the official website for details.</p>"
            lis = "".join(f"<li>{icon}{i}</li>" for i in items)
            return f"<ul>{lis}</ul>"

        facts = []
        if funding_type:
            fa = f" &mdash; {funding_amount}" if funding_amount else ""
            facts.append(f"<strong>Funding:</strong> {funding_type}{fa}")
        if stipend_amount:
            facts.append(f"<strong>Stipend / Allowance:</strong> {stipend_amount}")
        if target_countries:
            facts.append(f"<strong>Open To:</strong> {', '.join(target_countries[:5])}")
        if host_countries:
            facts.append(f"<strong>Host Country:</strong> {', '.join(host_countries[:3])}")
        if deadline_note:
            facts.append(f"<strong>Deadline:</strong> {deadline_note}")

        facts_html = "".join(f"<p>{f}</p>" for f in facts)

        body_html = ""
        for key, heading in self.SECTION_HEADING_MAP.items():
            items = sections.get(key, [])
            if items:
                icon = self.SECTION_ICONS.get(key, "")
                body_html += f"\n<h3>{heading}</h3>\n{ul(items, icon)}"

        return f"""<div class="opportunity-article">
  <div class="quick-facts">{facts_html}</div>
  {body_html}
  <div class="disclaimer-cta">
    <p><strong>Disclaimer:</strong> MastersGrant provides informational summaries only.
    Always verify details on the official provider&rsquo;s website before applying.</p>
    <a href="{official_link}" target="_blank" rel="noopener noreferrer">Apply on Official Website &rarr;</a>
  </div>
</div>"""


# ══════════════════════════════════════════════════════════════════
# 4. IMAGE GENERATOR  (visual-first)
# ══════════════════════════════════════════════════════════════════

class ScholarshipImageGenerator:
    """
    Generates a 1920x1080 JPEG that looks like a real designed image:
    - Large layered geometric shapes fill the right 40% of canvas
    - Frosted dark panel on the left 65% keeps text legible
    - Minimal text: category badge, title (max 2 lines), funding pill, deadline chip
    - Country / org icon top-left with glow ring
    """

    W, H = 1920, 1080

    THEMES = [
        # Navy + Gold
        {"bg_a": (6,14,42),   "bg_b": (10,25,70),
         "sh_a": (13,80,200), "sh_b": (8,40,110),
         "acc":  (255,195,50),"txt": (240,248,255),"sub": (170,200,235)},
        # Forest + Lime
        {"bg_a": (4,22,14),   "bg_b": (8,38,24),
         "sh_a": (15,110,65), "sh_b": (8,60,35),
         "acc":  (170,240,90),"txt": (235,252,240),"sub": (145,210,170)},
        # Plum + Coral
        {"bg_a": (18,6,32),   "bg_b": (32,12,55),
         "sh_a": (110,40,180),"sh_b": (65,20,110),
         "acc":  (255,110,90),"txt": (248,242,255),"sub": (195,165,225)},
        # Steel + Sky
        {"bg_a": (10,16,28),  "bg_b": (16,26,48),
         "sh_a": (35,100,175),"sh_b": (20,55,110),
         "acc":  (80,215,255),"txt": (225,238,255),"sub": (150,185,220)},
    ]

    def __init__(self):
        self.font_path    = os.path.join(settings.BASE_DIR, "static", "fonts")
        self._font_cache  = {}
        self.country_map  = {
            "uk":"gb.png","united kingdom":"gb.png","great britain":"gb.png",
            "england":"gb.png","scotland":"gb.png","usa":"us.png",
            "united states":"us.png","america":"us.png","canada":"ca.png",
            "germany":"de.png","australia":"au.png","japan":"jp.png",
            "france":"fr.png","india":"in.png","china":"cn.png",
            "brazil":"br.png","south africa":"za.png","netherlands":"nl.png",
            "sweden":"se.png","switzerland":"ch.png","italy":"it.png",
            "spain":"es.png","mexico":"mx.png","ireland":"ie.png",
            "new zealand":"nz.png","singapore":"sg.png","south korea":"kr.png",
            "norway":"no.png","denmark":"dk.png","finland":"fi.png",
            "belgium":"be.png","austria":"at.png","turkey":"tr.png",
            "uae":"ae.png","united arab emirates":"ae.png","taiwan":"tw.png",
            "hong kong":"hk.png","philippines":"ph.png",
        }
        self.org_map = {
            "unicef":"unicef.png","unesco":"unesco.png","rotary":"rotary.png",
            "mastercard":"mastercard.png","fulbright":"fulbright.png",
            "chevening":"chevening.png","erasmus":"erasmus.png",
            "commonwealth":"commonwealth.png","gates":"gates.png",
            "ford foundation":"ford.png","nasa":"nasa.png",
            "oxford":"oxford.png","harvard":"harvard.png","mit":"mit.png",
            "stanford":"stanford.png","cambridge":"cambridge.png",
            "google":"google.png","microsoft":"microsoft.png",
            "world bank":"worldbank.png","daad":"daad.png","who":"who.png",
        }

    def _font(self, name, size):
        k = (name, size)
        if k not in self._font_cache:
            try:
                self._font_cache[k] = ImageFont.truetype(
                    os.path.join(self.font_path, name), size)
            except Exception:
                self._font_cache[k] = ImageFont.load_default(size=size)
        return self._font_cache[k]

    def _icon(self, search_text):
        if not search_text:
            return None
        s = search_text.lower()
        for mapping in (self.org_map, self.country_map):
            for key, fname in mapping.items():
                if key in s:
                    p = os.path.join(settings.BASE_DIR, "static", "icons", fname)
                    if os.path.exists(p):
                        try:
                            return Image.open(p).convert("RGBA")
                        except Exception:
                            pass
        return None

    def _gradient(self, img, theme):
        draw = ImageDraw.Draw(img)
        a, b = theme["bg_a"], theme["bg_b"]
        for y in range(self.H):
            t = y / self.H
            draw.line([(0,y),(self.W,y)],
                      fill=(int(a[0]*(1-t)+b[0]*t),
                            int(a[1]*(1-t)+b[1]*t),
                            int(a[2]*(1-t)+b[2]*t)))

    def _bg_shapes(self, img, theme):
        ov   = Image.new("RGBA", (self.W, self.H), (0,0,0,0))
        draw = ImageDraw.Draw(ov)
        sa, sb, acc = theme["sh_a"], theme["sh_b"], theme["acc"]

        # Large circle — top-right
        draw.ellipse([self.W-900, -300, self.W+300, 900], fill=sa+(55,))
        # Medium circle — bottom-left
        draw.ellipse([-150, self.H-500, 650, self.H+100], fill=sb+(45,))
        # Diagonal polygon — lower-right
        draw.polygon([(int(self.W*0.42), self.H),
                      (self.W, int(self.H*0.30)),
                      (self.W, self.H)], fill=sb+(38,))
        # Small accent circle — mid-right
        draw.ellipse([self.W-500, 300, self.W-100, 700], fill=acc+(20,))
        # Arc rings — top-right corner
        for i in range(7):
            r = 220 + i*120
            draw.arc([self.W-r-80, -r+80, self.W+r-80, r+80],
                     start=130, end=210, fill=acc+(28-i*3,), width=3)
        # Dot grid — left column
        for row in range(16):
            for col in range(4):
                dx, dy = 55+col*58, 100+row*60
                draw.ellipse([dx-2,dy-2,dx+2,dy+2], fill=acc+(16,))
        # Top accent stripe
        draw.rectangle([0, 0, self.W, 10], fill=acc+(180,))

        return Image.alpha_composite(img.convert("RGBA"), ov)

    def _text_panel(self, img):
        """Left-to-right fade: opaque dark → transparent. Makes text readable."""
        ov   = Image.new("RGBA", (self.W, self.H), (0,0,0,0))
        draw = ImageDraw.Draw(ov)
        pw   = int(self.W * 0.70)
        for x in range(pw):
            t     = x / pw
            alpha = int(200 * (1 - t**1.7))
            draw.line([(x,0),(x,self.H)], fill=(0,0,0,alpha))
        return Image.alpha_composite(img, ov)

    def generate(self, title, category_name, deadline="Open Now",
                 benefits_list=None, target_countries=None,
                 funding_type=None, opportunity_type=None):

        idx   = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(self.THEMES)
        theme = self.THEMES[idx]
        acc, txt, sub = theme["acc"], theme["txt"], theme["sub"]

        # Build canvas
        img = Image.new("RGB", (self.W, self.H), theme["bg_a"])
        self._gradient(img, theme)
        img  = self._bg_shapes(img, theme)
        img  = self._text_panel(img)
        draw = ImageDraw.Draw(img)

        curr_y = 80

        # ── Country / org icon ────────────────────────────────────
        icon = self._icon(target_countries) or self._icon(title)
        if icon:
            icon.thumbnail((170,170), Image.Resampling.LANCZOS)
            iw, ih = icon.size
            gr = max(iw,ih)//2 + 22
            draw.ellipse([80-gr, curr_y-gr, 80+iw+gr, curr_y+ih+gr],
                         fill=(255,255,255,18))
            img.paste(icon, (80, curr_y), icon if icon.mode=="RGBA" else None)
            curr_y += ih + 32

        # ── Category pill ─────────────────────────────────────────
        f_pill  = self._font("Inter-Black.ttf", 44)
        pill_tx = category_name.upper()
        if opportunity_type and opportunity_type.upper() != category_name.upper():
            pill_tx += f"  \u00b7  {opportunity_type.upper()}"
        pb = draw.textbbox((0,0), pill_tx, font=f_pill)
        pw2, ph = pb[2]-pb[0], pb[3]-pb[1]
        draw.rounded_rectangle([80, curr_y, 80+pw2+56, curr_y+ph+24],
                               radius=10, fill=theme["sh_a"])
        draw.text((108, curr_y+12), pill_tx, font=f_pill, fill=txt)
        curr_y += ph + 24 + 38

        # ── Funding badge (outline pill) ──────────────────────────
        if funding_type:
            f_fund  = self._font("Inter-SemiBold.ttf", 40)
            fund_tx = f"  {funding_type}"
            fb = draw.textbbox((0,0), fund_tx, font=f_fund)
            fw, fh = fb[2]-fb[0], fb[3]-fb[1]
            draw.rounded_rectangle([80, curr_y, 80+fw+48, curr_y+fh+22],
                                   radius=22, outline=acc, width=2,
                                   fill=(0,0,0,0))
            draw.text((104, curr_y+11), fund_tx, font=f_fund, fill=acc)
            curr_y += fh + 52

        # ── Title ─────────────────────────────────────────────────
        clean  = re.sub(r'[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]', '', title)
        lines  = textwrap.wrap(clean, width=28)[:3]
        f_title= self._font("Inter-Bold.ttf", 108 if len(lines)<=2 else 82)
        for line in lines:
            tb = draw.textbbox((0,0), line, font=f_title)
            th = tb[3]-tb[1]
            draw.text((83, curr_y+3), line, font=f_title, fill=(0,0,0,110))  # shadow
            draw.text((80, curr_y),   line, font=f_title, fill=txt)
            curr_y += th + 12
        curr_y += 26

        # ── Gold accent divider ───────────────────────────────────
        draw.rectangle([80, curr_y, 640, curr_y+4], fill=acc)
        curr_y += 34

        # ── Benefit lines (max 2) ─────────────────────────────────
        if benefits_list:
            f_body = self._font("Inter-Medium.ttf", 48)
            for b in benefits_list[:2]:
                clean_b = (b[:60]+"...") if len(b)>60 else b
                draw.text((80, curr_y), f"  {clean_b}", font=f_body, fill=sub)
                bb2 = draw.textbbox((0,0), clean_b, font=f_body)
                curr_y += (bb2[3]-bb2[1]) + 18

        # ── Deadline chip ─────────────────────────────────────────
        f_dl  = self._font("Inter-Bold.ttf", 50)
        dl_tx = f"  DEADLINE: {re.sub(chr(65533),'',str(deadline)).upper()}"
        db    = draw.textbbox((0,0), dl_tx, font=f_dl)
        dw, dh= db[2]-db[0], db[3]-db[1]
        cy    = self.H - 158
        draw.rounded_rectangle([80, cy, 80+dw+48, cy+dh+22],
                               radius=12, fill=(0,0,0,150))
        draw.text((104, cy+11), dl_tx, font=f_dl, fill=acc)

        # ── Footer bar ────────────────────────────────────────────
        bar_y = self.H - 74
        draw.rectangle([0, bar_y, self.W, self.H], fill=theme["sh_a"])
        f_foot = self._font("Inter-SemiBold.ttf", 40)
        draw.text((64, bar_y+17), "mastersgrant.com", font=f_foot, fill=txt)
        tagline = "Your Gateway to Global Opportunities"
        tb3 = draw.textbbox((0,0), tagline, font=f_foot)
        draw.text((self.W-(tb3[2]-tb3[0])-64, bar_y+17),
                  tagline, font=f_foot, fill=acc)

        buf = BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=93, optimize=True)
        return ContentFile(buf.getvalue(),
                           name=f"opp_{slugify(title[:40])}_{int(time.time())}.jpg")


# ══════════════════════════════════════════════════════════════════
# 5. MANAGEMENT COMMAND
# ══════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = "Scrape + publish opportunities: rich content, visual images, rewritten titles"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=6)
        parser.add_argument(
            "--categories", nargs="+",
            choices=["scholarships","internships","grants","fellowships"],
            default=["scholarships","internships","grants"],
        )
        parser.add_argument("--dry-run", action="store_true",
                            help="Parse but do NOT write to DB")

    def handle(self, *args, **kwargs):
        self.limit   = kwargs["limit"]
        self.dry_run = kwargs["dry_run"]
        self.cats    = kwargs["categories"]

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        })

        self.title_rw  = TitleRewriter()
        self.extractor = FieldExtractor()
        self.scraper   = RichContentScraper()
        self.img_gen   = ScholarshipImageGenerator()

        TARGETS = {
            "scholarships": ("Scholarships","scholarships",
                             "https://opportunitydesk.org/category/fellowships-and-scholarships/"),
            "internships":  ("Internships","internships",
                             "https://opportunitydesk.org/category/jobs-and-internships/"),
            "grants":       ("Grants","grants",
                             "https://opportunitydesk.org/category/grants/"),
            "fellowships":  ("Fellowships","fellowships",
                             "https://opportunitydesk.org/category/fellowships-and-scholarships/"),
        }

        for key in self.cats:
            name, slug, url = TARGETS[key]
            cat, _ = Category.objects.get_or_create(name=name, slug=slug)
            self.stdout.write(self.style.HTTP_INFO(f"\n── {name} ──"))
            self.process_category(cat, url)

        self.stdout.write(self.style.SUCCESS("\n  All done."))

    def process_category(self, category, url):
        try:
            res = self.session.get(url, timeout=15)
            res.raise_for_status()
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"  Fetch failed: {e}"))
            return

        soup  = BeautifulSoup(res.text, "lxml")
        cards = soup.select("article h2 a")[:self.limit]
        if not cards:
            self.stdout.write(self.style.WARNING("  No links found."))
            return

        saved = 0
        for card in cards:
            link = (card.get("href") or "").strip()
            if not link:
                continue
            if ScrapeModels.objects.filter(od_url=link).exists():
                self.stdout.write(f"  Skip (seen): {link}")
                continue
            if self.process_detail(link, category):
                saved += 1
            time.sleep(2)

        self.stdout.write(f"  {saved} saved in {category.name}")

    def process_detail(self, url, category):
        self.stdout.write(f"  -> {url}")
        try:
            res = self.session.get(url, timeout=15)
            res.raise_for_status()
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"     Fetch error: {e}"))
            return False

        soup = BeautifulSoup(res.text, "lxml")
        h1   = soup.find("h1")
        if not h1:
            return False

        raw_title = h1.get_text(strip=True)
        new_title = self.title_rw.rewrite(raw_title)

        if (Opportunity.objects.filter(title=raw_title).exists() or
                Opportunity.objects.filter(title=new_title).exists()):
            ScrapeModels.objects.get_or_create(od_url=url)
            return False

        content = soup.select_one(".post-content,.entry-content,article")
        if not content:
            return False

        full_text = content.get_text(" ", strip=True)

        ex = self.extractor
        opp_type     = ex.get_opportunity_type(raw_title, full_text)
        funding_type = ex.get_funding_type(full_text)
        funding_amt  = ex.get_funding_amount(full_text)
        has_stip, stip_amt = ex.get_stipend(full_text)
        edu_levels   = ex.get_education_levels(full_text)
        target_c, host_c = ex.get_countries(full_text)
        dl_date, dl_note = self._extract_deadline(content)

        ext_links = [
            a["href"] for a in content.find_all("a", href=True)
            if "opportunitydesk.org" not in a["href"]
            and a["href"].startswith("http")
        ]
        official_link = ext_links[-1] if ext_links else url

        sections = self.scraper.extract(content, raw_title)

        # Fallback for empty benefits
        if not sections["benefits"]:
            sections["benefits"] = self._bullets(
                content,
                ["benefit","fund","stipend","tuition","award","cover","grant","allowance"]
            )

        description = self.scraper.build_html(
            sections=sections,
            funding_type=funding_type,
            funding_amount=funding_amt,
            stipend_amount=stip_amt,
            deadline_note=dl_note,
            target_countries=target_c,
            host_countries=host_c,
            official_link=official_link,
        )

        meta = ex.get_meta(new_title, description, opp_type, funding_type)

        image_benefits = [
            re.sub(r'<[^>]+>', '', b)[:60] for b in sections["benefits"]
        ][:3]

        banner = self.img_gen.generate(
            title=new_title,
            category_name=category.name,
            deadline=dl_note or "Open Now",
            benefits_list=image_benefits,
            target_countries=", ".join(target_c),
            funding_type=funding_type,
            opportunity_type=opp_type,
        )

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                f"     [DRY RUN]\n"
                f"     Raw  : {raw_title}\n"
                f"     New  : {new_title}\n"
                f"     Type={opp_type}, Funding={funding_type}, "
                f"Countries={target_c[:3]}\n"
                f"     Sections: { {k:len(v) for k,v in sections.items()} }"
            ))
            return True

        try:
            opp = Opportunity(
                title=new_title,
                description=description,
                official_link=official_link,
                category=category,
                image=banner,
                deadline=dl_date,
                deadline_note=dl_note,
                opportunity_type=opp_type,
                funding_type=funding_type,
                funding_amount=funding_amt,
                provides_stipend=has_stip,
                stipend_amount=stip_amt,
                meta_title=meta["meta_title"],
                meta_description=meta["meta_description"],
                focus_keywords=meta["focus_keywords"],
                image_alt_text=f"{new_title} – {opp_type} Banner"[:125],
                is_active=True,
            )
            opp.save()

            for lvl in edu_levels:
                l, _ = EducationLevel.objects.get_or_create(
                    name=lvl, defaults={"slug": slugify(lvl)})
                opp.education_levels.add(l)
            for c in target_c:
                co, _ = Country.objects.get_or_create(name=c)
                opp.target_countries.add(co)
            for c in host_c:
                co, _ = Country.objects.get_or_create(name=c)
                opp.host_countries.add(co)

            ScrapeModels.objects.get_or_create(od_url=url)
            self.stdout.write(self.style.SUCCESS(
                f"     Saved: {new_title}  [{opp_type} | {funding_type}]"))
            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"     DB error: {e}"))
            return False

    def _bullets(self, content, keywords, limit=8):
        out, seen = [], set()
        for el in content.find_all(["li","p","dd"]):
            t = unicodedata.normalize("NFKC", el.get_text(" ", strip=True))
            if len(t) < 15 or len(t) > 220:
                continue
            if any(k in t.lower() for k in keywords) and t not in seen:
                seen.add(t); out.append(t)
            if len(out) >= limit:
                break
        return out

    def _extract_deadline(self, content_div):
        dl_note = "Check official website"
        db_date = None
        for strong in content_div.find_all("strong"):
            t = strong.get_text(" ", strip=True)
            if t.lower().startswith("deadline"):
                dl_note = t
                m = re.search(r"([A-Z][a-z]+ \d{1,2},?\s*\d{4})", t)
                if m:
                    raw = m.group(1).replace(",","")
                    for fmt in ("%B %d %Y", "%B %d, %Y"):
                        try:
                            db_date = datetime.strptime(raw, fmt).date(); break
                        except ValueError:
                            pass
                return db_date, dl_note

        full = content_div.get_text(" ", strip=True)
        m2 = re.search(r"[Dd]eadline[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})", full)
        if m2:
            dl_note = f"Deadline: {m2.group(1)}"
            raw = m2.group(1).replace(",","")
            for fmt in ("%B %d %Y", "%B %d, %Y"):
                try:
                    db_date = datetime.strptime(raw, fmt).date(); break
                except ValueError:
                    pass
        return db_date, dl_note