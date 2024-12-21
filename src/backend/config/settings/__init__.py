"""
Django settings initialization module for Medical Research Platform.

Dynamically loads environment-specific settings with enhanced validation,
error handling, and security controls. Supports development, production,
and test environments with comprehensive configuration management.

Version: 1.0.0
"""

import os
import importlib
import logging
from typing import Any, List, Tuple, Type

# Configure logging for settings initialization
logger = logging.getLogger(__name__)

# Environment configuration
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')
VALID_ENVIRONMENTS = ['development', 'production', 'test']

# Required settings with their expected types
REQUIRED_SETTINGS: List[Tuple[str, Type[Any]]] = [
    ('INSTALLED_APPS', list),
    ('MIDDLEWARE', list),
    ('DATABASES', dict),
    ('DEBUG', bool),
    ('ALLOWED_HOSTS', list),
    ('SECRET_KEY', str),
]

# Production-required security settings
PRODUCTION_SECURITY_SETTINGS = [
    'SECURE_SSL_REDIRECT',
    'SESSION_COOKIE_SECURE',
    'CSRF_COOKIE_SECURE',
    'SECURE_HSTS_SECONDS',
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    'SECURE_HSTS_PRELOAD',
]

def validate_environment(environment: str) -> bool:
    """
    Validates if the specified environment is supported.
    
    Args:
        environment: The environment name to validate
        
    Returns:
        bool: True if environment is valid
        
    Raises:
        ValueError: If environment is not supported
    """
    if environment not in VALID_ENVIRONMENTS:
        error_msg = (
            f"Invalid environment '{environment}'. "
            f"Must be one of: {', '.join(VALID_ENVIRONMENTS)}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    return True

def validate_settings(settings_module: Any) -> bool:
    """
    Validates that all required settings are present and of correct type.
    
    Args:
        settings_module: The loaded settings module to validate
        
    Returns:
        bool: True if all settings are valid
        
    Raises:
        ValueError: If required settings are missing or invalid
    """
    # Validate required settings and their types
    for setting_name, expected_type in REQUIRED_SETTINGS:
        if not hasattr(settings_module, setting_name):
            error_msg = f"Required setting '{setting_name}' is missing"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        setting_value = getattr(settings_module, setting_name)
        if not isinstance(setting_value, expected_type):
            error_msg = (
                f"Setting '{setting_name}' has invalid type. "
                f"Expected {expected_type.__name__}, got {type(setting_value).__name__}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    # Additional validation for production environment
    if DJANGO_ENV == 'production':
        for security_setting in PRODUCTION_SECURITY_SETTINGS:
            if not hasattr(settings_module, security_setting):
                error_msg = f"Production requires security setting: {security_setting}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not getattr(settings_module, security_setting):
                error_msg = f"Production security setting must be enabled: {security_setting}"
                logger.error(error_msg)
                raise ValueError(error_msg)
    
    logger.info(f"Settings validation successful for environment: {DJANGO_ENV}")
    return True

def load_settings() -> Any:
    """
    Dynamically loads and validates the appropriate settings module.
    
    Returns:
        module: The validated settings module
        
    Raises:
        ImportError: If settings module cannot be imported
        ValueError: If settings validation fails
    """
    try:
        # Validate environment before proceeding
        validate_environment(DJANGO_ENV)
        
        # Construct settings module path
        settings_module_path = f'config.settings.{DJANGO_ENV}'
        logger.info(f"Loading settings from: {settings_module_path}")
        
        # Import settings module
        settings_module = importlib.import_module(settings_module_path)
        
        # Validate settings
        validate_settings(settings_module)
        
        logger.info(f"Successfully loaded settings for environment: {DJANGO_ENV}")
        return settings_module
        
    except ImportError as e:
        error_msg = f"Failed to import settings module: {str(e)}"
        logger.error(error_msg)
        raise ImportError(error_msg)
    except Exception as e:
        error_msg = f"Error loading settings: {str(e)}"
        logger.error(error_msg)
        raise

# Load settings module
settings_module = load_settings()

# Export all settings from the loaded module
globals().update({
    name: getattr(settings_module, name)
    for name in dir(settings_module)
    if not name.startswith('_')
})