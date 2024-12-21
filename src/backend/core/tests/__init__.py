"""
Test package initialization for core module tests.

Configures test environment with enhanced security, authentication, and logging settings.
Implements test collection modification for optimized test execution and proper isolation.

Version: 1.0.0
"""

import os
import tempfile
from typing import List

import pytest
from django.test import override_settings
from config.settings.test import TESTING

# Mark all tests to use database transactions by default
pytestmark = pytest.mark.django_db(transaction=True)

def pytest_configure(config: pytest.Config) -> None:
    """
    Configure pytest environment for core module tests with enhanced security and logging settings.
    
    Args:
        config: pytest configuration object
    """
    # Create temporary directories for test artifacts
    test_artifacts_dir = tempfile.mkdtemp(prefix='test_artifacts_')
    test_keys_dir = os.path.join(test_artifacts_dir, 'keys')
    os.makedirs(test_keys_dir, exist_ok=True)

    # Test-specific settings overrides
    test_settings = {
        # Enhanced logging configuration for tests
        'LOGGING': {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json_test': {
                    '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                    'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(test_id)s'
                },
            },
            'handlers': {
                'test_console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'json_test',
                },
            },
            'root': {
                'handlers': ['test_console'],
                'level': 'INFO',
            },
        },
        
        # Security test configurations
        'SECURE_SSL_REDIRECT': False,  # Disabled for testing
        'SESSION_COOKIE_SECURE': False,  # Disabled for testing
        'CSRF_COOKIE_SECURE': False,  # Disabled for testing
        
        # Test authentication settings
        'JWT_AUTH': {
            'JWT_SECRET_KEY': 'test-secret-key',
            'JWT_ALGORITHM': 'RS256',
            'JWT_PRIVATE_KEY_PATH': os.path.join(test_keys_dir, 'jwt-private.pem'),
            'JWT_PUBLIC_KEY_PATH': os.path.join(test_keys_dir, 'jwt-public.pem'),
        },
        
        # Test rate limiting settings
        'REST_FRAMEWORK': {
            'DEFAULT_THROTTLE_CLASSES': [],  # Disabled for testing
            'DEFAULT_THROTTLE_RATES': {},
        },
        
        # Test MFA settings
        'MFA_REQUIRED': False,  # Disabled by default for tests
        
        # Test OAuth settings
        'OAUTH_PROVIDERS': {
            'google': {
                'client_id': 'test-client-id',
                'client_secret': 'test-client-secret',
            },
        },
    }
    
    # Apply test settings
    override_settings(**test_settings).enable()

def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]) -> None:
    """
    Modify test collection to add security, authentication, and middleware markers.
    
    Args:
        config: pytest configuration object
        items: List of collected test items
    """
    # Add markers for different test categories
    for item in items:
        # Database transaction marker
        item.add_marker(pytest.mark.django_db(transaction=True))
        
        # Add security-related markers based on test path/name
        if 'security' in item.nodeid:
            item.add_marker(pytest.mark.security)
        if 'authentication' in item.nodeid:
            item.add_marker(pytest.mark.authentication)
        if 'rate_limiting' in item.nodeid:
            item.add_marker(pytest.mark.rate_limiting)
        
        # Add middleware test markers
        if 'middleware' in item.nodeid:
            item.add_marker(pytest.mark.middleware)
            
        # Add permission test markers
        if 'permissions' in item.nodeid:
            item.add_marker(pytest.mark.permissions)
            
        # Add performance monitoring markers
        if 'performance' in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Configure test isolation and retry behavior
        item.add_marker(pytest.mark.isolation)
        if 'flaky' in item.keywords:
            item.add_marker(pytest.mark.flaky(reruns=3))