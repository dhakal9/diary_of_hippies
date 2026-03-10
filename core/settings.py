import os
from pathlib import Path
import dj_database_url

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-h1xlm5#l(qpecmj$pyg6&37@$_%_hhc8-bxi9x2)cmt=+p1x=k'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'cloudinary_storage',       # MUST be above staticfiles
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', 
    'cloudinary',               # Low-level SDK
    'ckeditor',
    'blog',
    'scraper',   
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # If using WhiteNoise, it would go here, but since you use Cloudinary, it is not needed.
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'blog.context_processor.scholarship_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.app'

# Cloudinary Configuration
# This dictionary format is required for the django-cloudinary-storage engine
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dsi0pqrcy',
    'API_KEY': '474493794259973',
    'API_SECRET': 'ytnPQexg8XvYC0XdO2ORlxr-Ji8',
}

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://neondb_owner:npg_Qo1sEgTr5iwv@ep-proud-frost-aibysccf-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static and Media Files
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# Source folders
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Collection folder (Local fallback)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Storage Engines
# Use Hashed storage to bust cache on Cloudinary
STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticCloudinaryStorage'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Security Settings
CSRF_TRUSTED_ORIGINS = [
    "https://mastersgrant.com",
    "https://www.mastersgrant.com",
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

AUTOSLUG_SLUGIFY_FUNCTION = 'django.utils.text.slugify'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# wjwOEl8qWN5q46cJ
