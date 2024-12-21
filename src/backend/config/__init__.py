"""
Django configuration package initialization file for Medical Research Platform.

This module initializes and exposes the Celery application instance for use throughout
the backend services. It serves as the integration point between Django and Celery,
ensuring proper configuration of asynchronous task processing capabilities.

Version: Celery 5.3+ (production-ready)
"""

# Import the configured Celery application instance
from celery import app

# Expose the Celery application instance for Django integration
# This follows Django Celery integration best practices by exposing
# the app as 'celery_app' in the __init__.py file
celery_app = app

# Make the celery app available for Django's auto-discovery mechanism
__all__ = ('celery_app',)