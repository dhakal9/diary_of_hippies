
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Opportunity, Guide # Import your Guide model here

# 1. Homepage
class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'
    def items(self):
        return ['index'] # Add your static page names here
    def location(self, item):
        return reverse(item)

# 2. Scholarships
class ScholarshipSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    def items(self):
        return Opportunity.objects.all()
    def lastmod(self, obj):
        return obj.updated_at 

# 3. SOP & Writing Guides (New!)
class GuideSitemap(Sitemap):
    changefreq = "monthly" # Guides don't change as often as scholarship deadlines
    priority = 0.7 
    def items(self):
        return Guide.objects.all()
    def lastmod(self, obj):
        return obj.created_at

class ContactViewSitemap(Sitemap):
    priority = 0.3
    changefreq = 'monthly'
    def items(self):
        return ['about_us', 'contact' ] # Add your static page names here
    def location(self, item):
        return reverse(item)