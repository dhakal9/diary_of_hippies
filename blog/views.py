from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from .models import Opportunity, Guide, Category
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

