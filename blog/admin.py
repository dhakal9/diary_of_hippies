from django.contrib import admin
from .models import Opportunity, EducationLevel, Country, Guide, Category, SuccessStory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    # list_display cannot contain 'education_levels' directly. 
    # Use the custom method 'get_education_levels' instead.
    list_display = ('title', 'opportunity_type', 'get_education_levels', 'deadline', 'is_active')
    
    # Updated list_filter to use the new related field
    list_filter = ('opportunity_type', 'is_active', 'education_levels', 'funding_type')
    
    search_fields = ('title', 'description', 'meta_title')
    prepopulated_fields = {'slug': ('title',)}
    
    # This allows you to select multiple levels and countries easily in the admin
    filter_horizontal = ('education_levels', 'target_countries', 'host_countries')

    # Custom method to show education levels in the list view
    def get_education_levels(self, obj):
        return ", ".join([level.name for level in obj.education_levels.all()])
    
    get_education_levels.short_description = 'Education Levels'
    

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'content')

@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'story')