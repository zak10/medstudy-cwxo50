"""
WSGI configuration for Medical Research Platform.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It exposes the WSGI callable as a 
module-level variable named 'application' for production deployment with 
Gunicorn/uWSGI.

For more information on this file, see:
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os  # version: python3.11+
from django.core.wsgi import get_wsgi_application  # version: django4.2+

# Set the Django settings module to production settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Get the WSGI application callable
# This will load all production settings including:
# - Security configurations
# - Database connections
# - Cache settings
# - AWS integrations
# - Monitoring and logging
application = get_wsgi_application()