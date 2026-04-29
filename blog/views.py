from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from .models import Opportunity, Guide, Category, Subscriber
from .forms import ContactForm, SuscriberForm
from django.db.models import Q
from django.views.generic import ListView, View
from .forms import ContactForm
from django.core.mail import send_mail
from django.contrib import messages
import requests




def error_404(request, exception):
        return render(request,'404.html')

def error_500(request):
        return render(request,'500.html')
        
def error_403(request, exception):
        return render(request,'403.html')

def error_400(request,  exception):
        return render(request,'400.html')


def subscribe_email(request):
    if request.method == "POST":
        form = SuscriberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Avoid duplicate emails
            if not Subscriber.objects.filter(email=email).exists():
                Subscriber.objects.create(email=email)
                messages.success(request, "Subscribed successfully!")
            else:
                messages.info(request, "You are already subscribed.")

        else:
            messages.error(request, "Invalid email address.")

    return redirect(request.META.get('HTTP_REFERER', '/'))

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

class AboutUsView(TemplateView):
    template_name = 'about_us.html'

class DisclaimerView(TemplateView):
    template_name = 'disclaimer.html'

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

# class ContactUs(TemplateView):
#     template_name = 'contact_us.html'



class ContactUs(View):

    template_name = "contact_us.html"

    def get(self, request):
        form = ContactForm()
        return render(request, self.template_name, {
            "form": form,
            "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY
        })

    def post(self, request):

        form = ContactForm(request.POST)

        if form.is_valid():

            name = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
        # verify captcha
        recaptcha_response = request.POST.get('g-recaptcha-response')

        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }

        r = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data=data
        )

        result = r.json()

        if not result['success']:
            messages.error(request, "Captcha verification failed.")
            return redirect("contact")

        # Email to admin
        message_body = f"""
            New Contact Message

            Name: {name}
            Email: {email}

            Message:
            {message}
            """

        send_mail(
            subject,
            message_body,
            settings.EMAIL_HOST_USER,
            ["dhakalamrit19@gmail.com"],
            fail_silently=False
        )

        # Auto reply to user
        auto_reply = f"""
Hi {name},

Thank you for contacting MastersGrant.

We have received your message and will respond soon.

Your message:
{message}

Best Regards,
MastersGrant Team
"""

        send_mail(
            "We received your message",
            auto_reply,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=True
        )

        messages.success(request,"Your message has been sent successfully!")

        return redirect("contact")





class GuideDetailView(DetailView):
    model = Guide
    template_name = 'guide_detail.html'
    context_object_name = 'guide'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch 4 latest guides excluding the current one
        context['similar_guides'] = Guide.objects.exclude(id=self.object.id).order_by('-created_at')[:4]
        return context

class ScholarshipListView(ListView):
    model = Opportunity
    template_name = "scholarships.html"
    context_object_name = "opportunities"
    paginate_by = 10

    def get_queryset(self):
        # 1. Start with active opportunities and optimize DB hits with prefetch_related
        qs = Opportunity.objects.filter(is_active=True).prefetch_related('education_levels', 'target_countries')

        # 2. Check URL name for hard-coded category filters
        url_name = self.request.resolver_match.url_name
        url_map = {
            "summer_schools": "Other", # Or 'Event' depending on your model choices
            "internships": "Internship",
            "conferences": "Event",
            "exchange_programs": "Other",
        }

        if url_name in url_map:
            qs = qs.filter(opportunity_type=url_map[url_name])
            return qs.order_by("-created_at")

        # 3. Handle normal filtering for /scholarships/
        q = self.request.GET.get("q")
        level = self.request.GET.get("level")
        type_ = self.request.GET.get("type")

        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                # Updated: Search in related country names instead of a text field
                Q(target_countries__name__icontains=q) | 
                Q(description__icontains=q)
            )

        if level:
            # Updated: Filter through the ManyToMany relationship
            qs = qs.filter(education_levels__name__iexact=level)

        if type_:
            qs = qs.filter(
                opportunity_type=type_.replace("-", " ").title()
            )

        # 4. Use distinct() to avoid duplicate results caused by ManyToMany filters
        return qs.distinct().order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        url_name = self.request.resolver_match.url_name
        q = self.request.GET.get("q", "")
        level = self.request.GET.get("level", "")
        type_ = self.request.GET.get("type", "")

        # Default SEO
        title = "Fully Funded Scholarships 2026 | Study Abroad"
        desc = "Explore fully funded scholarships for international students 2026. Find scholarships worldwide with deadlines and eligibility."
        h1 = "All Scholarships & Opportunities"

        # Dynamic SEO based on URL
        seo_map = {
            "summer_schools": ("Fully Funded Summer Schools 2026", "Find best summer schools...", "Summer Schools"),
            "internships": ("Paid International Internships 2026", "Apply for internships...", "International Internships"),
            "conferences": ("International Conferences 2026", "Discover conferences...", "Conferences & Youth Summits"),
            "exchange_programs": ("Student Exchange Programs 2026", "Explore exchange programs...", "Exchange Programs"),
        }

        if url_name in seo_map:
            title, desc, h1 = seo_map[url_name]
        
        elif q:
            title = f"Search Results for '{q}' | MastersGrant"
            h1 = f"Search Results for '{q}'"
        elif level or type_:
            level_text = level if level else ""
            type_text = type_.replace("-", " ").title() if type_ else "Scholarships"
            title = f"{level_text} {type_text} 2026 | Fully Funded"
            h1 = f"{level_text} {type_text}".strip()
            
        context.update({
            'page_title': title,
            'meta_description': desc,
            'page_h1': h1,
        })
        
        # Preserve query parameters for pagination
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_string'] = query_params.urlencode()

        return context

class CountriesView(View):
    def get(self, request):
        return render(request, 'countries.html')