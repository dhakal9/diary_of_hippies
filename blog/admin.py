from django.contrib import admin
from .models import Opportunity, EducationLevel, Country, Guide, Category, SuccessStory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'opportunity_type', 'get_education_levels', 'deadline', 'is_active')
    list_filter = ('opportunity_type', 'is_active', 'education_levels', 'funding_type')
    search_fields = ('title', 'description', 'meta_title')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('education_levels', 'target_countries', 'host_countries')

    def get_education_levels(self, obj):
        return ", ".join([level.name for level in obj.education_levels.all()])
    
    get_education_levels.short_description = 'Education Levels'

@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    # FIXED: Replaced 'slug' with 'code' to match your Model
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    # Removed prepopulated_fields because Country doesn't have a slug field

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'content')

@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'story')