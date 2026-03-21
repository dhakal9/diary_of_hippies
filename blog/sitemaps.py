from django.contrib.sitemaps import Sitemap
from .models import  Opportunity# Replace with your actual model name

class ScholarshipSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # This pulls all your scholarship posts
        return Opportunity.objects.all()

    def lastmod(self, obj):
        # Assumes you have a 'updated_at' field in your model
        return obj.updated_at