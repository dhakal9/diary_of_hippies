from django.views.generic import ListView, DetailView, TemplateView
from .models import Opportunity, Guide, Category
from django.db.models import Q
from django.views.generic import ListView

# blog/views.py
class IndexView(ListView):
    model = Opportunity
    template_name = 'index.html'
    context_object_name = 'latest_opportunities' # THIS MUST MATCH YOUR HTML LOOP
    
    def get_queryset(self):
        return Opportunity.objects.filter(is_active=True).select_related('category').order_by('-created_at')[:6]

class PrivacyPolicyView(TemplateView):
    template_name = 'privacy_policy.html'

class TermsView(TemplateView):
    template_name = 'terms.html'

class OpportunityDetailView(DetailView):
    """Detail Page: Optimized for single object retrieval."""
    model = Opportunity
    template_name = 'opportunity_details.html'
    context_object_name = 'opportunity'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Revenue Tip: Fetch 3 related opportunities to increase page views/AdSense exposure
        context['related_items'] = Opportunity.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id)[:3]
        return context

class GuideListView(ListView):
    """Informative Blogs/Guides for SEO traffic."""
    model = Guide
    template_name = 'guide_list.html'
    context_object_name = 'guides'
    paginate_by = 10

class ContactUs(TemplateView):
    template_name = 'contact_us.html'


class GuideDetailView(DetailView):
    model = Guide
    template_name = 'guide_detail.html'
    context_object_name = 'guide'

class ScholarshipListView(ListView):
    model = Opportunity
    template_name = "scholarships.html"
    context_object_name = "opportunities"
    paginate_by = 10

    def get_queryset(self):
        qs = Opportunity.objects.filter(is_active=True)

        q = self.request.GET.get("q")
        level = self.request.GET.get("level")
        type_ = self.request.GET.get("type")

        # 🔥 FORCE Summer School when using /summer-schools/
        if self.request.resolver_match.url_name == "summer_schools":
            qs = qs.filter(opportunity_type="Summer School")
            return qs.order_by("-created_at")
        # 🔥 FORCE Internships when using /internships/
        if self.request.resolver_match.url_name == "internships":
            qs = qs.filter(opportunity_type="Internship")
            return qs.order_by("-created_at")
        # 🔥 FORCE Conferences when using /conferences/
        if self.request.resolver_match.url_name == "conferences":
            qs = qs.filter(opportunity_type="Conference")
            return qs.order_by("-created_at")
        # 🔥 FORCE Exchange Programs when using /exchange_programs/
        if self.request.resolver_match.url_name == "exchange_programs":
            qs = qs.filter(opportunity_type="Exchange Program")
            return qs.order_by("-created_at")

        # Normal filtering for /scholarships/
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(target_countries__icontains=q) |
                Q(description__icontains=q)
            )

        if level:
            qs = qs.filter(education_level=level)

        if type_:
            qs = qs.filter(
                opportunity_type=type_.replace("-", " ").title()
            )

        return qs.order_by("-created_at")

