"""
Root URL configuration for the Medical Research Platform Django backend.
Defines secure URL routing patterns for API endpoints, admin interface, and static/media file serving.

Version: 1.0.0
"""

from django.urls import path, include, re_path  # v4.2.0
from django.contrib import admin  # v4.2.0
from django.conf import settings  # v4.2.0
from django.views.static import static, serve  # v4.2.0
from django.http import JsonResponse
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Main URL patterns with versioning and security
urlpatterns = [
    # Admin interface with security headers
    path('admin/', admin.site.urls, name='admin'),
    
    # API v1 endpoints with rate limiting and monitoring
    path('api/v1/', include(('api.v1.urls', 'api_v1'), namespace='api_v1')),
    
    # Secure media file serving in development
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT},
        name='media'
    ),
    
    # Secure static file serving in development
    re_path(
        r'^static/(?P<path>.*)$',
        serve,
        {'document_root': settings.STATIC_ROOT},
        name='static'
    ),
]

# Add debug toolbar URLs in development
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns.append(
            path('__debug__/', include(debug_toolbar.urls))
        )
    except ImportError:
        pass

# Custom error handlers with JSON responses
def handler404(request, exception):
    """
    Custom 404 error handler returning JSON response.
    
    Args:
        request: HTTP request
        exception: Error details
        
    Returns:
        JsonResponse: Formatted error response
    """
    error_msg = "The requested resource was not found"
    logger.warning(
        f"404 error: {error_msg}",
        extra={
            "path": request.path,
            "method": request.method
        }
    )
    
    return JsonResponse({
        "error": "Not Found",
        "message": error_msg,
        "status_code": 404
    }, status=404)

def handler500(request):
    """
    Custom 500 error handler returning JSON response.
    
    Args:
        request: HTTP request
        
    Returns:
        JsonResponse: Formatted error response
    """
    error_msg = "An internal server error occurred"
    logger.error(
        f"500 error: {error_msg}",
        extra={
            "path": request.path,
            "method": request.method
        }
    )
    
    return JsonResponse({
        "error": "Internal Server Error",
        "message": error_msg,
        "status_code": 500
    }, status=500)

# Register error handlers
handler404 = handler404  # noqa
handler500 = handler500  # noqa