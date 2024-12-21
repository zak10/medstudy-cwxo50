"""
Development environment specific Django settings.
Extends base settings with development-specific configurations including:
- Debug options
- Local database settings
- Development-only middleware and apps
- Local service endpoints
"""

import os
from pathlib import Path
from environ import Env  # django-environ v0.11.2

# Import all settings from base settings
from .base import *  # noqa: F403

# Initialize environment variables
env = Env()
env.read_env(os.path.join(BASE_DIR, '.env'))  # noqa: F405

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all local development hosts
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '[::1]',  # IPv6 localhost
]

# Required for Django Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]

# CORS settings for local development
CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',  # Frontend development server
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True
SECURE_SSL_REDIRECT = False  # Disable SSL redirect for local development
SESSION_COOKIE_SECURE = False  # Allow non-HTTPS cookies in development
CSRF_COOKIE_SECURE = False  # Allow non-HTTPS CSRF in development

# Database configuration for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.str('DB_NAME', default='medical_research'),
        'USER': env.str('DB_USER', default='postgres'),
        'PASSWORD': env.str('DB_PASSWORD', default='postgres'),
        'HOST': env.str('DB_HOST', default='localhost'),
        'PORT': env.str('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Cache configuration for local development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env.str('REDIS_URL', default='redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
    }
}

# Celery configuration for local development
CELERY_BROKER_URL = env.str('CELERY_BROKER_URL', default='amqp://guest:guest@localhost:5672//')
CELERY_RESULT_BACKEND = env.str('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)

# Email backend for development (prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static and media files configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'static')  # noqa: F405
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # noqa: F405
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Add development specific apps
INSTALLED_APPS += [  # noqa: F405
    'debug_toolbar',  # django-debug-toolbar v4.2+
    'django_extensions',  # django-extensions v3.2+
]

# Add development specific middleware
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE  # noqa: F405

# Debug Toolbar configuration
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}

# Development-specific logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'medical_research': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Development-specific REST Framework settings
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'core.authentication.JWTAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',  # Increased rate for development
        'user': '5000/hour',  # Increased rate for development
    },
}

# Disable security features that might interfere with local development
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False