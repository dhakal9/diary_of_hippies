# blog/context_processor.py
from .models import Category, Opportunity

def scholarship_context(request):
    return {
        'all_categories': Category.objects.only('name', 'slug'),
        'urgent_scholarships': Opportunity.objects.filter(
            is_active=True
        ).only('title', 'slug', 'deadline').order_by('deadline')[:5],
    }
