import os
import re
import time
import requests
from io import BytesIO
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.text import slugify

from blog.models import Opportunity, Category, ScrapeModels


# =====================================================
# IMAGE GENERATOR (UPGRADED)
# =====================================================

class ScholarshipImageGenerator:
    def __init__(self):
        # 4K-ish aspect ratio but manageable
        self.W, self.H = 2400, 1260  

        # Modern Color Palette
        self.primary_color = (13, 110, 253)    # Electric Blue
        self.accent_gold = (255, 193, 7)      # Vivid Gold
        self.white = (255, 255, 255)
        self.dark_bg = (10, 15, 30)           # Deeper Navy
        self.text_secondary = (200, 210, 230) # Soft Blue-Grey

        # Path to your fonts
        self.font_path = os.path.join(settings.BASE_DIR, "static/fonts")
        self.font_title = self.load_font("Inter-Bold.ttf", 160)
        self.font_body = self.load_font("Inter-Medium.ttf", 80)
        self.font_badge = self.load_font("Inter-Black.ttf", 60)
        self.font_footer = self.load_font("Inter-SemiBold.ttf", 70)
        
        self.country_map = {
            "uk": "gb.png",
            "united kingdom": "gb.png",
            "great britain": "gb.png",
            "britain": "gb.png",
            "england": "gb.png",
            "scotland": "gb.png",
            "wales": "gb.png",

            "usa": "us.png",
            "u.s.a": "us.png",
            "united states": "us.png",
            "united states of america": "us.png",
            "america": "us.png",
            "canada": "ca.png",
            'germany': 'de.png',
            'australia': 'au.png',
            'japan': 'jp.png',
            'france': 'fr.png',
            'india': 'in.png',
            'china': 'cn.png',
            'brazil': 'br.png',
            'south africa': 'za.png',
            'netherlands': 'nl.png',
            'sweden': 'se.png',
            'switzerland': 'ch.png',
            'italy': 'it.png',
            'spain': 'es.png',
            'mexico': 'mx.png',
            'ireland': 'ie.png',
            'new zealand': 'nz.png',
            'singapore': 'sg.png',
            'south korea': 'kr.png',
            'norway': 'no.png',
            'denmark': 'dk.png',
            'finland': 'fi.png',
            'belgium': 'be.png',
            'austria': 'at.png',
            'russia': 'ru.png',
            'poland': 'pl.png',
            'argentina': 'ar.png',
            'turkey': 'tr.png',
            'saudi arabia': 'sa.png',
            'uae': 'ae.png',
            'united arab emirates': 'ae.png',
            'dubai': 'ae.png',
            'uae': 'ae.png',
            'u.a.e': 'ae.png',
            'taiwán': 'tw.png',
            'taiwan': 'tw.png',
            'hong kong': 'hk.png',
            'philippines': 'ph.png'

            
        }
        
        self.org_map = {
            'unicef': 'unicef.png',
            'unesco': 'unesco.png',
            'rotary': 'rotary.png',
            'mastercard': 'mastercard.png',
            'master card': 'mastercard.png',
            'fulbright': 'fulbright.png',
            'chevening': 'chevening.png',
            'erasmus': 'erasmus.png',
            'commonwealth': 'commonwealth.png',
            'gates': 'gates.png',
            'ford foundation': 'ford.png',
            'nasa': 'nasa.png',
            'who': 'who.png',
            'world health organization': 'who.png',
            'oxford': 'oxford.png',
            'AfOx': 'oxford.png',
            'harvard': 'harvard.png',
            'mit': 'mit.png',
            'stanford': 'stanford.png',
            'cambridge': 'cambridge.png',
            'lions': 'lions.png',
            'ai': 'ai.png',
            'climate': 'climate.png',
            'daad': 'daad.png',
            'google': 'google.png',
            'microsoft': 'microsoft.png',
            'facebook': 'facebook.png',
            'world bank': 'worldbank.png',
            'imf': 'imf.png',

            }
            

        # Path to your fonts
        self.font_path = os.path.join(settings.BASE_DIR, "static", "fonts") # Update this to your actual path

        # Large, readable font sizes
        self.font_title = self.load_font("Inter-Bold.ttf", 160)
        self.font_body = self.load_font("Inter-Medium.ttf", 80)
        self.font_badge = self.load_font("Inter-Black.ttf", 60)
        self.font_footer = self.load_font("Inter-SemiBold.ttf", 70)

    def load_font(self, name, size):
        try:
            return ImageFont.truetype(os.path.join(self.font_path, name), size)
        except:
            # Fallback for local testing
            return ImageFont.load_default(size=size)

    
    def detect_icon(self, search_text):
        if not search_text:
            return None
            
        search_text_lower = search_text.lower()
        for mapping in (self.org_map, self.country_map):
            for key, filename in mapping.items():
                if key in search_text_lower:
                    path = os.path.join(settings.BASE_DIR, "static/icons", filename)
                    if os.path.exists(path):
                        return Image.open(path).convert("RGBA")
        return None

    def generate(self, title, category_name, deadline="Open Now", benefits_list=None, target_countries=None):
        image = Image.new("RGB", (self.W, self.H), self.dark_bg)
        draw = ImageDraw.Draw(image)
        center_x = self.W // 2

        # Try to detect icon from target_countries first, then fallback to title
        current_y = 100
        icon = self.detect_icon(target_countries) or self.detect_icon(title)
        
        if icon:
            icon.thumbnail((300, 300), Image.Resampling.LANCZOS)
            icon_x = center_x - (icon.width // 2)
            image.paste(icon, (icon_x, current_y), icon if icon.mode == 'RGBA' else None)
            current_y += icon.height + 60

        # 2. Centered Category Badge
        badge_text = category_name.upper()
        bbox = draw.textbbox((0, 0), badge_text, font=self.font_badge)
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rounded_rectangle(
            [center_x - (bw//2) - 40, current_y, center_x + (bw//2) + 40, current_y + bh + 40],
            radius=15, fill=self.primary_color
        )
        draw.text((center_x - (bw//2), current_y + 15), badge_text, font=self.font_badge, fill=self.white)
        current_y += bh + 120

        # 3. Centered Title
        lines = textwrap.wrap(title, width=25)
        for line in lines[:2]:
            t_bbox = draw.textbbox((0, 0), line, font=self.font_title)
            t_w = t_bbox[2] - t_bbox[0]
            draw.text((center_x - (t_w // 2), current_y), line, font=self.font_title, fill=self.white)
            current_y += 170

        # 4. Centered Benefits (Only if provided)
        if benefits_list:
            current_y += 40
            # Clean strings and limit to top 2 for design space
            for benefit in benefits_list[:2]:
                clean_benefit = benefit[:60] + "..." if len(benefit) > 60 else benefit
                b_bbox = draw.textbbox((0, 0), clean_benefit, font=self.font_body)
                b_w = b_bbox[2] - b_bbox[0]
                draw.text((center_x - (b_w // 2), current_y), clean_benefit, font=self.font_body, fill=self.text_secondary)
                current_y += 100

        # 5. Centered Deadline
        footer_text = f"DEADLINE: {str(deadline).upper()}"
        f_bbox = draw.textbbox((0, 0), footer_text, font=self.font_footer)
        f_w = f_bbox[2] - f_bbox[0]
        draw.text((center_x - (f_w // 2), self.H - 180), footer_text, font=self.font_footer, fill=self.accent_gold)

        # Output
        buf = BytesIO()
        image.save(buf, format="JPEG", quality=95)
        return ContentFile(buf.getvalue(), name=f"banner_{int(time.time())}.jpg")

    
class Command(BaseCommand):
    help = "Fast, copyright-safe scraper with dedup"

    def handle(self, *args, **kwargs):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

        self.img = ScholarshipImageGenerator()

        targets = [
            ("Scholarships", "scholarships", "https://opportunitydesk.org/category/fellowships-and-scholarships/"),
            ("Internships", "internships", "https://opportunitydesk.org/category/jobs-and-internships/"),
            ("Grants", "grants", "https://opportunitydesk.org/category/grants/"),
        ]

        for name, slug, url in targets:
            cat, _ = Category.objects.get_or_create(name=name, slug=slug)
            self.process_category(cat, url)

    # -------------------------------------------------
    
    def process_category(self, category, url):
        res = self.session.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")
        cards = soup.select("article h2 a")[:6]

        for c in cards:
            link = c["href"]
            if ScrapeModels.objects.filter(od_url=link).exists():
                continue
            self.process_detail(link, category)
    
    def extract_deadline(self, content_div):
    
        deadline_note = "Check official website"
        db_date = None

        strong_tags = content_div.find_all("strong")

        for strong in strong_tags:
            text = strong.get_text(" ", strip=True)

            if text.lower().startswith("deadline"):
                deadline_note = text

                match = re.search(
                    r'([A-Z][a-z]+ \d{1,2}, \d{4})',
                    text
                )
                if match:
                    try:
                        db_date = datetime.strptime(
                            match.group(1),
                            "%B %d, %Y"
                        ).date()
                    except:
                        pass
                break

        return db_date, deadline_note

    # -------------------------------------------------

    def extract_points(self, content, keys, limit=6):
        out = []
        for el in content.find_all(["li", "p"]):
            t = el.get_text(" ", strip=True)
            if any(k in t.lower() for k in keys):
                if len(t) < 180:
                    out.append(t)
            if len(out) >= limit:
                break
        return out

    # -------------------------------------------------

    def process_detail(self, url, category):
        try:
            res = self.session.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "lxml")

            title = soup.find("h1").get_text(strip=True)
            slug = slugify(title)

            if Opportunity.objects.filter(slug=slug).exists():
                ScrapeModels.objects.create(od_url=url)
                return

            content = soup.select_one(".post-content")
            if not content:
                return

            eligibility = self.extract_points(content, ["eligible", "criteria", "applicant"])
            benefits = self.extract_points(content, ["benefit", "fund", "stipend", "tuition"])
            steps = self.extract_points(content, ["apply", "application", "submit"])

            ext_links = [
                a["href"] for a in content.find_all("a", href=True)
                if "opportunitydesk.org" not in a["href"] and a["href"].startswith("http")
            ]
            official = ext_links[-1] if ext_links else url

            description = self.build_description(
                title, eligibility, benefits, steps, official
            )

            banner = self.img.generate(title, category.name)
            deadline, deadline_note = self.extract_deadline(content)

            Opportunity.objects.create(
                    title=title,
                    slug=slug,
                    description=description,
                    official_link=official,
                    category=category,
                    image=banner,
                    deadline=deadline,              # ✅ Parsed date
                    deadline_note=deadline_note,    # ✅ "Deadline: January 7, 2026"
                    is_active=True
                )

            ScrapeModels.objects.create(od_url=url)
            self.stdout.write(self.style.SUCCESS(f"Saved: {title}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e)))

    # -------------------------------------------------

    def build_description(self, title, elig, ben, steps, link):
        def ul(items):
            return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

        return f"""
        <p><strong>{title}</strong> is an international opportunity currently open for applications.
        Below is a summarized overview created for informational purposes.</p>

        <h3>Eligibility Overview</h3>
        {ul(elig) if elig else "<p>Refer to official website.</p>"}

        <h3>Funding & Benefits</h3>
        {ul(ben) if ben else "<p>Benefits vary by applicant.</p>"}

        <h3>Application Process</h3>
        {ul(steps) if steps else "<p>Follow official guidelines.</p>"}

        <div class="cta">
            <p><strong>Disclaimer:</strong> This is a summarized listing. Always verify details from the official source.</p>
            <a href="{link}" target="_blank">Apply on Official Website</a>
        </div>
        """