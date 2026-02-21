from django.contrib import admin
from .models import Opportunity, Guide, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    # What you see in the list view (Crucial for fast management)
    list_display = ('title', 'opportunity_type', 'education_level', 'deadline', 'deadline_note', 'is_active', 'created_at')
    
    # Filters on the right side (Helps you find specific content quickly)
    list_filter = ('is_active', 'opportunity_type', 'education_level', 'category', 'created_at')
    
    # Search functionality
    search_fields = ('title', 'description', 'target_countries')
    
    # Auto-fills the slug while you type the title (Great for SEO speed)
    prepopulated_fields = {"slug": ("title",)}
    
    # Grouping fields for better UI
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'opportunity_type', 'category', 'image')
        }),
        ('Financials & Eligibility', {
            'fields': ('amount', 'deadline', 'deadline_note', 'education_level', 'target_countries')
        }),
        ('Content & Links', {
            'fields': ('description', 'official_link', 'is_active')
        }),
    )

    # Performance: only loads needed data for the foreign key dropdown
    list_select_related = ('category',)
    

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'content')

