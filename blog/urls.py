from django.urls import path, reverse
from .views import (
    IndexView,  
    OpportunityDetailView, 
    GuideListView, 
    ContactUs,
    GuideDetailView,
    ScholarshipListView,
    PrivacyPolicyView,
    
)




urlpatterns = [
    # Homepage
    path('', IndexView.as_view(), name="index"),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    # Opportunities (Scholarships, Grants, etc.)
    # SEO Tip: Using 'scholarships' in the path helps rank for that high-volume keyword
    path('scholarships/<slug:slug>/', OpportunityDetailView.as_view(), name="opportunity_detail"),
    
    # Information Guides (How-to articles)
    path('guides/', GuideListView.as_view(), name="guide_list"),
    
    # Static Pages
    path('contact-us/', ContactUs.as_view(), name="contact"),
    path('guides/<slug:slug>/', GuideDetailView.as_view(), name='guide_detail'),
    # Static Pages
    path("scholarships/", ScholarshipListView.as_view(), name="scholarship_list"),

    #inherited from Scholarship ListView
    path("summer-schools/", ScholarshipListView.as_view(), name="summer_schools"),
    path("internships/", ScholarshipListView.as_view(), name="internships"),
    path("conferences/", ScholarshipListView.as_view(), name="conferences"),
    path("exchange_programs/", ScholarshipListView.as_view(), name="exchange_programs"),
    
]

def get_absolute_url(self):
    return reverse('opportunity_detail', kwargs={'slug': self.slug})