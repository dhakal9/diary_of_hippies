from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from .utils import generate_unique_slug
from django.urls import reverse
from django.utils.html import strip_tags

# --- Helper Models ---

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class EducationLevel(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 code (e.g., US, UK, AU)", blank=True)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name

# --- Main Opportunity Model ---

class Opportunity(models.Model):
    TYPES = [
        ('Scholarship', 'Scholarship'),
        ('Internship', 'Internship'),
        ('Fellowship', 'Fellowship'),
        ('Assistantship', 'Assistantship'),
        ('Grant', 'Grant'),
        ('Competition', 'Competition'),
        ('Event', 'Conference / Workshop / Seminar'),
        ('Job', 'Job Opportunity'),
        ('Other', 'Other'),
    ]

    FUNDING_TYPES = [
        ('Fully Funded', 'Fully Funded'),
        ('Partial Funding', 'Partial Funding'),
        ('Tuition Fee Waiver', 'Tuition Fee Waiver'),
        ('Stipend Only', 'Stipend Only'),
        ('Unpaid', 'Unpaid'),
    ]

    DEADLINE_TYPES = [
        ('Specific Date', 'Specific Date'),
        ('Varies by Country', 'Varies by Country'),
        ('Rolling', 'Rolling / Continuous'),
        ('Always Open', 'Always Open'),
    ]

    # Core Information
    title = models.CharField(max_length=255)
    opportunity_type = models.CharField(max_length=50, choices=TYPES, default='Scholarship')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='opportunities')
    
    # Relational Fields
    education_levels = models.ManyToManyField(EducationLevel, related_name='opportunities')
    target_countries = models.ManyToManyField(Country, related_name='targeted_opportunities', blank=True)
    host_countries = models.ManyToManyField(Country, related_name='hosted_opportunities', blank=True)

    # Financial Details
    funding_type = models.CharField(max_length=50, choices=FUNDING_TYPES, default='Partial Funding')
    funding_amount = models.CharField(max_length=255, blank=True, help_text="e.g., $5000, Full Tuition")
    provides_stipend = models.BooleanField(default=False)
    stipend_amount = models.CharField(max_length=255, blank=True, help_text="e.g., $1500 monthly living allowance")

    # Deadline Logic
    deadline_type = models.CharField(max_length=50, choices=DEADLINE_TYPES, default='Specific Date')
    deadline = models.DateField(blank=True, null=True, help_text="Leave blank if Rolling or Varies by Country")   
    # Fixed: null=True added to prevent migration crash on existing data
    deadline_note = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. '11:59 PM CET'")
    
    # Content
    description = RichTextField()
    official_link = models.URLField(max_length=500, help_text="Link to the official provider")
    image = models.ImageField(upload_to='opportunity_images', blank=True, null=True)
    
    # SEO & Metadata
    meta_title = models.CharField(max_length=60, blank=True, help_text="Keep under 60 chars.")
    meta_description = models.CharField(max_length=160, blank=True, help_text="Keep under 160 chars.")
    focus_keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords")
    image_alt_text = models.CharField(max_length=125, blank=True)
    
    # System
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Opportunities"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Opportunity, self.title, instance=self)
        
        # Auto-generate basic SEO tags if forgotten
        if not self.meta_title:
            self.meta_title = f"{self.title} - {self.get_opportunity_type_display()}"[:60]
        if not self.meta_description and self.description:
            self.meta_description = strip_tags(self.description)[:157] + "..."
            
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('opportunity_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

# --- Additional Features ---

class Guide(models.Model):
    title = models.CharField(max_length=255)
    content = RichTextField()
    author = models.CharField(max_length=100, default='Admin')
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (max 60 characters)")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO description (max 160 characters)")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Guide, self.title, instance=self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('guide_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

class ScrapeModels(models.Model):
    od_url = models.URLField(unique=True, help_text="Source URL from OpportunityDesk")
    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.od_url

class SuccessStory(models.Model):
    name = models.CharField(max_length=100)
    story = RichTextField()
    image = models.ImageField(upload_to='success_stories', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-subscribed_at']