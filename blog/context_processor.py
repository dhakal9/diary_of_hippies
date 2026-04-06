from .models import Category, Opportunity, SuccessStory, EducationLevel
from django.utils import timezone

def scholarship_context(request):
    # Fetch categories for navigation/sidebar
    all_categories = Category.objects.all().only('name', 'slug')
    
    # Fetch Education Levels (New: useful for a "Browse by Level" footer or menu)
    all_education_levels = EducationLevel.objects.all().only('name', 'slug')

    # Urgent Scholarships: 
    # We filter for 'Specific Date' types that haven't passed yet, 
    # then sort by the closest deadline.
    urgent_scholarships = Opportunity.objects.filter(
        is_active=True,
        deadline_type='Specific Date',
        deadline__gte=timezone.now().date()
    ).only('title', 'slug', 'deadline').order_by('deadline')[:5]

    return {
        'all_categories': all_categories,
        'all_education_levels': all_education_levels,
        'urgent_scholarships': urgent_scholarships,
    }

def success_stories_context(request):
    # Success stories remain straightforward, 
    # but we limit the fields to keep the global context lightweight.
    return {
        'success_stories': SuccessStory.objects.all().only(
            'name', 'story', 'image'
        ).order_by('-created_at')[:3]
    }