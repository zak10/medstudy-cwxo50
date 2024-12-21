"""
Root package initializer for the Medical Research Platform API.
Configures and exposes the main API router and version-specific packages.
Implements URI-based versioning and integrates with security monitoring and rate limiting controls.

Version: 1.0.0
"""

from django.urls import path, include  # v4.2.0
from api.v1 import api as api_v1  # Main API instance for v1
from api.v1.urls import urlpatterns as api_v1_urls  # URL routing configuration

# Configure default Django app settings
default_app_config = 'api.apps.ApiConfig'
app_name = 'api'

# Re-export v1 API package with complete routing and security configuration
__all__ = [
    'api_v1',
    'api_v1_urls',
    'urlpatterns'
]

# Main URL patterns with versioning support
urlpatterns = [
    # Version 1 API routes with security middleware
    path('v1/', include((api_v1_urls, 'v1'), namespace='api_v1')),
]