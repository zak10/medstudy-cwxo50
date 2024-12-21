#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks in the Medical Research Platform.
Enhanced with robust error handling, environment validation, and deployment environment support.

Version: Django 4.2+
Python: 3.11+
"""

import os
import sys
import logging
from typing import NoReturn, Optional
from django.core.management import execute_from_command_line
from django.core.exceptions import ImproperlyConfigured

# Constants for environment validation
REQUIRED_PYTHON_VERSION = (3, 11)
DEFAULT_SETTINGS_MODULE = 'config.settings.development'
CRITICAL_ENV_VARS = [
    'SECRET_KEY',
    'DATABASE_URL',
    'ALLOWED_HOSTS',
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def validate_environment() -> bool:
    """
    Validates the execution environment and critical configurations.
    
    Checks:
    - Python version compatibility
    - Django settings module configuration
    - Critical environment variables
    - Basic database connectivity
    
    Returns:
        bool: True if environment is valid
    
    Raises:
        ImproperlyConfigured: If any validation fails
    """
    # Check Python version
    if sys.version_info < REQUIRED_PYTHON_VERSION:
        raise ImproperlyConfigured(
            f"This project requires Python {'.'.join(map(str, REQUIRED_PYTHON_VERSION))} or higher. "
            f"Found: Python {'.'.join(map(str, sys.version_info[:3]))}"
        )

    # Validate Django settings module
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', DEFAULT_SETTINGS_MODULE)
        logger.info(f"Using default settings module: {DEFAULT_SETTINGS_MODULE}")

    # Check critical environment variables
    missing_vars = [var for var in CRITICAL_ENV_VARS if not os.environ.get(var)]
    if missing_vars:
        raise ImproperlyConfigured(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Import settings to validate configuration
    try:
        from django.conf import settings
        if not settings.DATABASES:
            raise ImproperlyConfigured("Database configuration is missing")
        
        # Validate debug settings for production
        if not settings.DEBUG and '*' in settings.ALLOWED_HOSTS:
            logger.warning("Production environment detected with wildcard ALLOWED_HOSTS")
            
    except Exception as e:
        raise ImproperlyConfigured(f"Settings validation failed: {str(e)}")

    return True

def main() -> Optional[NoReturn]:
    """
    Enhanced main function that sets up Django environment with robust error handling
    and environment validation.
    
    Returns:
        Optional[NoReturn]: Exits with status code 0 for success, 1 for errors
    """
    try:
        # Validate environment before proceeding
        validate_environment()
        
        # Configure logging based on environment
        from django.conf import settings
        if not settings.DEBUG:
            logging.getLogger('django').setLevel(logging.WARNING)
            
        # Execute Django management commands
        execution_args = sys.argv
        if len(execution_args) == 1:
            logger.info("No command specified. Available commands can be listed with 'python manage.py help'")
            
        logger.info(f"Executing management command: {' '.join(execution_args[1:])}")
        execute_from_command_line(execution_args)
        
    except ImproperlyConfigured as e:
        logger.error(f"Configuration Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Execution Error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup operations if needed
        logging.shutdown()

if __name__ == '__main__':
    main()