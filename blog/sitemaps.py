# blog/sitemaps.py
# ================================================================
# MASTERSGRANT.COM — Production Sitemap
# ================================================================
# KEY FACTS from Google's own documentation (Dec 2025):
#   ✅ <lastmod>    — Google DOES use this. Must be accurate.
#   ❌ <priority>   — Google IGNORES this completely.
#   ❌ <changefreq> — Google IGNORES this completely.
#
# Source: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
# "Google ignores <priority> and <changefreq> values."
# "Google uses the <lastmod> value if it's consistently and
#  verifiably accurate."
#
# WHAT THIS MEANS FOR YOUR SITE:
#   → Keep priority/changefreq (Bing still reads them, and they
#     help organise your own thinking about page importance).
#   → But the ONLY one that actually affects Google crawling is
#     lastmod — so make it ACCURATE and AUTOMATIC.
#   → Never hardcode lastmod. Always return the real updated_at.
# ================================================================

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from .models import Opportunity, Guide, Category, Country


# ── Helper: guarantee every lastmod is a timezone-aware datetime ─
# Django's sitemap framework compares all lastmod values with >
# to find the most recent one for the <lastmod> tag on the index.
# If you mix date + datetime Python raises:
#   TypeError: '>' not supported between instances of
#   'datetime.date' and 'datetime.datetime'
# Solution: always return datetime, never bare date.

def _as_dt(value):
    """
    Convert any value to a timezone-aware datetime, or return None.
    Handles:  datetime (aware/naive)  |  date  |  None
    """
    if value is None:
        return None
    # Already a datetime
    if hasattr(value, "hour"):
        if timezone.is_naive(value):
            return timezone.make_aware(value)
        return value
    # Plain date object — convert to midnight UTC datetime
    from datetime import datetime as _dt
    return timezone.make_aware(_dt(value.year, value.month, value.day))



# ────────────────────────────────────────────────────────────────
# 1. HOMEPAGE
# ────────────────────────────────────────────────────────────────
class HomepageSitemap(Sitemap):
    """
    Priority 1.0 — the most important page on the site.
    lastmod: today's date because home shows latest opportunities daily.
    """
    priority    = 1.0
    changefreq  = "daily"
    protocol    = "https"

    def items(self):
        return ["index"]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        latest = (
            Opportunity.objects
            .filter(is_active=True)
            .order_by("-updated_at")
            .values_list("updated_at", flat=True)
            .first()
        )
        return _as_dt(latest) or timezone.now()


# ────────────────────────────────────────────────────────────────
# 2. OPPORTUNITIES (Scholarships, Internships, Grants etc.)
# ────────────────────────────────────────────────────────────────
class OpportunitySitemap(Sitemap):
    """
    Individual opportunity detail pages.
    lastmod uses updated_at — Google re-crawls when this changes.
    Only active opportunities are included.
    Filtered to exclude pages without a slug (shouldn't happen, but safe).
    """
    priority    = 0.9
    changefreq  = "weekly"
    protocol    = "https"

    def items(self):
        return (
            Opportunity.objects
            .filter(is_active=True)
            .exclude(slug="")
            .only("id", "slug", "updated_at", "created_at")
            .order_by("-updated_at")
        )

    def lastmod(self, obj):
        val = getattr(obj, "updated_at", None) or getattr(obj, "created_at", None)
        return _as_dt(val)

    def location(self, obj):
        return obj.get_absolute_url()


# ────────────────────────────────────────────────────────────────
# 3. GUIDES (SOPs, Motivation Letters, Application Tips)
# ────────────────────────────────────────────────────────────────
class GuideSitemap(Sitemap):
    """
    Guides are evergreen content — change less often than opportunities.
    lastmod uses created_at (guides rarely get significant updates).
    If you add an updated_at field to Guide model, switch to that.
    """
    priority    = 0.8
    changefreq  = "monthly"
    protocol    = "https"

    def items(self):
        return (
            Guide.objects
            .exclude(slug="")
            .only("id", "slug", "created_at")
            .order_by("-created_at")
        )

    def lastmod(self, obj):
        val = getattr(obj, "updated_at", None) or getattr(obj, "created_at", None)
        return _as_dt(val)

    def location(self, obj):
        return obj.get_absolute_url()


# ────────────────────────────────────────────────────────────────
# 4. SCHOLARSHIP LIST (main browse page + category filter pages)
# ────────────────────────────────────────────────────────────────
class ScholarshipListSitemap(Sitemap):
    """
    The main /scholarships/ listing page.
    High priority — it's a primary landing page for SEO.
    lastmod reflects when the newest opportunity was added.
    """
    priority    = 0.9
    changefreq  = "daily"
    protocol    = "https"

    def items(self):
        return ["scholarship_list"]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        latest = (
            Opportunity.objects
            .filter(is_active=True)
            .order_by("-updated_at")
            .values_list("updated_at", flat=True)
            .first()
        )
        return _as_dt(latest) or timezone.now()


# ────────────────────────────────────────────────────────────────
# 5. CATEGORY PAGES (Scholarships, Internships, Grants, Fellowships)
# ────────────────────────────────────────────────────────────────
class CategorySitemap(Sitemap):
    """
    One URL per category landing page.
    e.g. /scholarships/, /internships/, /grants/, /fellowships/

    Maps category slug → URL name in your urls.py.
    Adjust the slug_to_url_name dict to match your actual URL names.
    """
    priority    = 0.8
    changefreq  = "daily"
    protocol    = "https"

    # Map your category slugs to their URL names
    # Update this dict to match your urls.py
    SLUG_TO_URL = {
        "scholarships": "scholarship_list",
        "internships":  "internships",
        "grants":       "scholarship_list",   # adjust if you have a grants page
        "fellowships":  "scholarship_list",   # adjust if you have a fellowships page
    }

    def items(self):
        return Category.objects.all().only("id", "slug", "name").order_by("id")

    def location(self, obj):
        url_name = self.SLUG_TO_URL.get(obj.slug)
        if url_name:
            try:
                return reverse(url_name)
            except Exception:
                pass
        # Fallback: link to scholarship list filtered by category
        return f"{reverse('scholarship_list')}?type={obj.name}"

    def lastmod(self, obj):
        latest = (
            Opportunity.objects
            .filter(category=obj, is_active=True)
            .order_by("-updated_at")
            .values_list("updated_at", flat=True)
            .first()
        )
        return _as_dt(latest) or timezone.now()


# ────────────────────────────────────────────────────────────────
# 6. COUNTRY / STUDY ABROAD PAGES
# ────────────────────────────────────────────────────────────────
class CountrySitemap(Sitemap):
    """
    Study-in-[Country] landing pages.
    e.g. /study-abroad/usa/, /study-abroad/uk/

    Only include countries that have at least 1 active opportunity.
    This prevents thin/empty country pages from being indexed.
    """
    priority    = 0.7
    changefreq  = "weekly"
    protocol    = "https"

    def items(self):
        return (
            Country.objects
            .filter(hosted_opportunities__is_active=True)
            .distinct()
            .only("id", "name", "code")
            .order_by("id")
        )

    def location(self, obj):
        # Adjust to your actual country URL pattern
        try:
            return reverse("study_abroad_country", kwargs={"slug": obj.code.lower()})
        except Exception:
            # Fallback: search results page for this country
            return f"{reverse('scholarship_list')}?q={obj.name}"

    def lastmod(self, obj):
        latest = (
            Opportunity.objects
            .filter(host_countries=obj, is_active=True)
            .order_by("-updated_at")
            .values_list("updated_at", flat=True)
            .first()
        )
        return _as_dt(latest)


# ────────────────────────────────────────────────────────────────
# 7. STATIC PAGES
# ────────────────────────────────────────────────────────────────
class StaticPagesSitemap(Sitemap):
    """
    Static informational pages.
    Low-to-medium priority — they don't change often.
    """
    protocol = "https"

    # (url_name, priority, changefreq)
    PAGES = [
        ("guide_list",        0.8, "weekly"),
        ("internships",       0.8, "daily"),
        ("summer_schools",    0.7, "weekly"),
        ("exchange_programs", 0.7, "weekly"),
        ("conferences",       0.7, "weekly"),
        ("about_us",          0.4, "monthly"),
        ("contact",           0.3, "monthly"),
    ]

    def items(self):
        valid = []
        for page in self.PAGES:
            try:
                reverse(page[0])
                valid.append(page)
            except Exception:
                pass
        return valid

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]

    def changefreq(self, item):
        return item[2]

    def lastmod(self, item):
        url_name = item[0]

        if url_name == "guide_list":
            val = (
                Guide.objects
                .order_by("-created_at")
                .values_list("created_at", flat=True)
                .first()
            )
            return _as_dt(val)

        if url_name in ("internships", "summer_schools", "exchange_programs", "conferences"):
            val = (
                Opportunity.objects
                .filter(is_active=True)
                .order_by("-updated_at")
                .values_list("updated_at", flat=True)
                .first()
            )
            return _as_dt(val)

        # Truly static pages — return a fixed aware datetime, not a bare date
        # This prevents the date vs datetime comparison TypeError
        from datetime import datetime as _dt
        static_dates = {
            "about_us": timezone.make_aware(_dt(2026, 1, 1)),
            "contact":  timezone.make_aware(_dt(2026, 1, 1)),
        }
        return static_dates.get(url_name)


# ────────────────────────────────────────────────────────────────
# 8. GUIDE LIST PAGE
# ────────────────────────────────────────────────────────────────
class GuideListSitemap(Sitemap):
    """Separate sitemap entry for the guides index page."""
    priority   = 0.8
    changefreq = "weekly"
    protocol   = "https"

    def items(self):
        return ["guide_list"]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        val = (
            Guide.objects
            .order_by("-created_at")
            .values_list("created_at", flat=True)
            .first()
        )
        return _as_dt(val)