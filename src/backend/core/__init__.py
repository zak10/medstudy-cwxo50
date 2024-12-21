"""
Core package initializer for the Medical Research Platform.
Exposes essential functionality for authentication, error handling, and middleware components.

Version: 1.0.0
"""

# Authentication components
from core.authentication import (  # version: 1.0.0
    JWTAuthentication,
    MFAAuthentication
)

# Exception classes
from core.exceptions import (  # version: 1.0.0
    BaseAPIException,
    ValidationException as ValidationError,  # Aliased for consistency
)

# Middleware components
from core.middleware import (  # version: 1.0.0
    RequestLoggingMiddleware,
    JWTAuthMiddleware,
    ExceptionMiddleware
)

# Package metadata
__version__ = '1.0.0'
__author__ = 'Medical Research Platform Team'

# Expose core authentication components
__all__ = [
    # Authentication
    'JWTAuthentication',
    'MFAAuthentication',
    
    # Exceptions
    'BaseAPIException',
    'ValidationError',
    
    # Middleware
    'RequestLoggingMiddleware',
    'JWTAuthMiddleware',
    'ExceptionMiddleware',
]

# Configure default security settings
default_app_config = 'core.apps.CoreConfig'

# Security-related constants
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; frame-ancestors 'none'",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}

# Authentication configuration
AUTH_CONFIG = {
    'TOKEN_EXPIRY': 3600,  # 1 hour in seconds
    'REFRESH_TOKEN_EXPIRY': 604800,  # 7 days in seconds
    'MFA_TOKEN_VALIDITY': 30,  # 30 seconds
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,  # 5 minutes in seconds
    'PASSWORD_MIN_LENGTH': 8,
    'REQUIRE_MFA_FOR_ROLES': ['admin', 'protocol_creator']
}

# Rate limiting configuration
RATE_LIMITS = {
    'LOGIN': '5/minute',
    'TOKEN_GENERATION': '10/minute',
    'API_CALLS': '100/minute'
}

def get_version():
    """Returns the current version of the core package."""
    return __version__

def get_security_headers():
    """Returns the default security headers configuration."""
    return SECURITY_HEADERS.copy()

def get_auth_config():
    """Returns the authentication configuration settings."""
    return AUTH_CONFIG.copy()

def get_rate_limits():
    """Returns the rate limiting configuration."""
    return RATE_LIMITS.copy()