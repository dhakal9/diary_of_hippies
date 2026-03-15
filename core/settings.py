import os
from pathlib import Path
import dj_database_url
from django.contrib.messages import constants as messages
from dotenv import load_dotenv
load_dotenv()
# Build paths inside the project

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG') == 'True'

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
    'whitenoise.runserver_nostatic',  # Disable static file handling in development 
    'whitenoise',  # Add WhiteNoise for static file handling in production
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise middleware for static file handling
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
    'CLOUD_NAME': os.getenv('CLOUD_NAME'),
    'API_KEY': os.getenv('API_KEY'),
    'API_SECRET': os.getenv('API_SECRET'),
}

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
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

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Security Settings

CSRF_TRUSTED_ORIGINS = [
    "https://mastersgrant.com",
    "https://www.mastersgrant.com",
    "http://localhost:8000",
]
if not DEBUG:
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
# // {
# //   "version": 2,
# //   "routes": [
# //     {
# //       "src": "/(.*)",
# //       "dest": "api/index.py"
# //     }
# //   ]
# // }

# // vercel.json

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv('EMAIL_ADDRESS')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASS')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# reCAPTCHA Settings
RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY')
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')