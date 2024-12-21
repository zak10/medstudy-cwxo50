"""
Test initialization module for API v1 test suite.

Configures pytest environment, coverage requirements, and test infrastructure for
comprehensive API testing. Implements test fixtures and utilities used across
API test modules.

Version: 1.0.0
"""

import os
import pytest
from config.settings.test import DJANGO_SETTINGS_MODULE

# Register required pytest plugins
pytest_plugins = [
    'pytest_django.fixtures',  # Django test fixtures
    'pytest_cov.plugin',      # Coverage reporting
]

def pytest_configure(config):
    """
    Configure pytest environment with required settings and test infrastructure.
    
    Args:
        config: Pytest configuration object
        
    Sets up:
        - Django test settings
        - Test markers and categories
        - Coverage requirements
        - Test collection rules
        - Result reporting
    """
    # Ensure correct Django settings module is used
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)

    # Register custom test markers
    config.addinivalue_line(
        "markers",
        "unit: Unit tests that test individual components in isolation"
    )
    config.addinivalue_line(
        "markers", 
        "integration: Integration tests that test component interactions"
    )
    config.addinivalue_line(
        "markers",
        "api: API tests that test HTTP endpoints and responses"
    )

    # Configure test collection
    config.addinivalue_line(
        "testpaths", ["src/backend/api/v1/tests"]
    )
    config.addinivalue_line(
        "python_files", "test_*.py"
    )
    config.addinivalue_line(
        "python_classes", "Test*"
    )
    config.addinivalue_line(
        "python_functions", "test_*"
    )

    # Configure coverage requirements and reporting
    config.option.cov_config = ".coveragerc"
    config.option.cov = True
    config.option.cov_report = {
        'term-missing': True,
        'html': 'coverage_html',
        'xml': 'coverage.xml'
    }
    config.option.cov_fail_under = 80.0  # Minimum required coverage
    
    # Configure test execution
    config.option.verbose = 2  # Detailed test output
    config.option.showlocals = True  # Show local variables on failure
    config.option.strict_markers = True  # Enforce marker registration
    config.option.junit_family = "xunit2"  # JUnit XML format
    
    # Configure parallel execution settings
    if not config.option.numprocesses:
        config.option.numprocesses = 'auto'
    
    # Configure test isolation
    config.option.strict = True  # Strict mode for better isolation
    config.option.tb = 'short'  # Shorter tracebacks
    
    # Configure security-sensitive component mocking
    os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')