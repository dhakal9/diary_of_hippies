import os
import sys

from django.core.wsgi import get_wsgi_application
from whitenoise.middleware import WhiteNoiseMiddleware # Import WhiteNoiseMiddleware

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")



application = get_wsgi_application()
application = WhiteNoiseMiddleware(application) # Wrap the application
app = application  # Add this line to create an alias for the WSGI application


