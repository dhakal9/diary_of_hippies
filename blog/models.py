from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from .utils import generate_unique_slug # Keeping your utility
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Opportunity(models.Model):
    TYPES = [
        ('Scholarship', 'Scholarship'),
        ('Fully Funded Scholarship', 'Fully Funded Scholarship'),
        ('Partial Scholarship', 'Partial Scholarship'),

        ('Internship', 'Internship'),
        ('Paid Internship', 'Paid Internship'),
        ('Remote Internship', 'Remote Internship'),
        ('Summer Internship', 'Summer Internship'),

        ('Fellowship', 'Fellowship'),
        ('Research Fellowship', 'Research Fellowship'),
        ('Postdoctoral Fellowship', 'Postdoctoral Fellowship'),

        ('Assistantship', 'Assistantship'),
        ('Teaching Assistantship', 'Teaching Assistantship'),
        ('Research Assistantship', 'Research Assistantship'),

        ('Grant', 'Grant'),
        ('Research Grant', 'Research Grant'),
        ('Startup Grant', 'Startup Grant'),

        ('Competition', 'Competition'),
        ('Hackathon', 'Hackathon'),
        ('Essay Competition', 'Essay Competition'),
        ('Case Competition', 'Case Competition'),

        ('Conference', 'Conference'),
        ('Workshop', 'Workshop'),
        ('Seminar', 'Seminar'),
        ('Summer School', 'Summer School'),
        ('Exchange Program', 'Exchange Program'),

        ('Training Program', 'Training Program'),
        ('Leadership Program', 'Leadership Program'),
        ('Bootcamp', 'Bootcamp'),

        ('Job Opportunity', 'Job Opportunity'),
        ('Volunteer Program', 'Volunteer Program'),

        ('Travel Grant', 'Travel Grant'),
        ('Fully Funded Program', 'Fully Funded Program'),

        ('Other', 'Other'),
    ]


    LEVEL_CHOICES = [
        ('High School', 'High School'),
        ('Pre-University', 'Pre-University'),

        ('Undergraduate', 'Undergraduate'),
        ('Bachelors', 'Bachelors'),

        ('Masters', 'Masters'),
        ('Postgraduate', 'Postgraduate'),

        ('PhD', 'PhD'),
        ('Doctoral', 'Doctoral'),
        ('Postdoctoral', 'Postdoctoral'),

        ('Diploma', 'Diploma'),
        ('Certificate', 'Certificate'),

        ('Short Course', 'Short Course'),
        ('Online Course', 'Online Course'),
        ('Professional Course', 'Professional Course'),

        ('Early Career', 'Early Career'),
        ('Mid Career', 'Mid Career'),

        ('All Levels', 'All Levels'),
    ]


    title = models.CharField(max_length=255)
    opportunity_type = models.CharField(max_length=50, choices=TYPES, default='Scholarship')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    
    # Financial Details (High value for SEO)
    amount = models.CharField(max_length=255, help_text="e.g., $5000 or Full Tuition")
    deadline = models.DateField()   
    deadline_note = models.CharField(max_length=100, help_text="e.g. '11:59 PM CET'", blank=True, null=True)
    
    # Eligibility & Description
    education_level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    target_countries = models.CharField(max_length=255, help_text="Countries eligible for this")
    description = RichTextField()
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    
    # Metadata
    image = models.ImageField(upload_to='opportunity_images', blank=True, null=True)
    official_link = models.URLField(help_text="Link to the official provider")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Adds the type to the slug for better SEO context
            # Result: scholarship-chevening-excellence-award
            combined_text = f"{self.opportunity_type}-{self.title}"
            self.slug = generate_unique_slug(Opportunity, combined_text, instance=self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('opportunity_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

class Guide(models.Model):
    title = models.CharField(max_length=255)

    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="SEO title (max 60 characters)"
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO description (max 160 characters)"
    )

    content = RichTextField()
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    author = models.CharField(max_length=100, default='Admin')
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

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