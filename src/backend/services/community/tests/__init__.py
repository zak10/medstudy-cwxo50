"""
Test package initialization and configuration for the community service test suite.
Configures pytest environment, database settings, test fixtures, and coverage tracking
for comprehensive testing of forum threads, posts, direct messaging, and content moderation features.

Version: 1.0
"""

# pytest v7.4+
import pytest
import os
from typing import Dict, Any

def pytest_configure(config: Dict[Any, Any]) -> None:
    """
    Configures pytest settings and environment for community service test suite.
    
    Args:
        config: Pytest configuration dictionary containing test settings
        
    Returns:
        None
        
    Configuration includes:
    - Database access and settings
    - Coverage tracking
    - Test isolation
    - WebSocket testing support
    - Content moderation test environment
    """
    
    # Register django_db marker for database access
    config.addinivalue_line(
        "markers",
        "django_db: mark test to use Django database transactions"
    )
    
    # Configure test database settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
    os.environ.setdefault('COMMUNITY_DB_NAME', 'test_community')
    
    # Set up test environment variables
    os.environ.setdefault('FORUM_THREAD_LIMIT', '50')  
    os.environ.setdefault('MESSAGE_RETENTION_DAYS', '30')
    os.environ.setdefault('MODERATION_QUEUE_SIZE', '100')
    
    # Configure coverage tracking
    config.option.cov_config = '.coveragerc'
    config.option.cov_branch = True
    config.option.cov_report = 'term-missing'
    config.option.cov_fail_under = 80  # Minimum required coverage
    
    # Enable WebSocket test support
    config.addinivalue_line(
        "markers",
        "websocket: mark test to use WebSocket testing utilities"
    )
    
    # Configure parallel test execution
    config.option.numprocesses = 'auto'
    
    # Set up test isolation
    config.option.strict = True
    config.option.strict_markers = True
    
    # Configure test cleanup
    config.option.tb = 'short'
    config.option.show_capture = 'no'
    
    # Initialize content moderation test environment
    os.environ.setdefault('MODERATION_TEST_MODE', 'True')
    os.environ.setdefault('AUTO_MODERATION_THRESHOLD', '0.8')
    os.environ.setdefault('REPORT_THRESHOLD', '3')