import re
from django.utils.text import slugify
from django.utils.html import strip_tags

def generate_unique_slug(model_class, value, slug_field="slug", instance=None):
    """
    Generates a unique, SEO-optimized slug for StudentFundingHub.
    Removes stop words to keep URLs short and keyword-focused.
    """
    # 1. Strip HTML tags and convert to lowercase
    clean_value = strip_tags(value).lower()

    # 2. SEO Optimization: Remove "Stop Words" (Optional but recommended)
    # This prevents slugs like /how-to-apply-for-a-scholarship-in-the-usa/
    # And turns them into /apply-scholarship-usa/
    stop_words = ['a', 'an', 'the', 'for', 'in', 'of', 'on', 'at', 'to', 'is', 'and']
    query_words = clean_value.split()
    result_words = [word for word in query_words if word not in stop_words]
    
    # 3. Join words and slugify
    base_slug = slugify(' '.join(result_words))
    
    # Fallback if slugify results in empty string (e.g. only stop words)
    if not base_slug:
        base_slug = slugify(value)

    slug = base_slug
    counter = 1

    # 4. Ensure Uniqueness
    queryset = model_class.objects.all()
    if instance:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug