"""
Test package initialization for Celery tasks testing.

Provides shared test configurations, fixtures and utilities for comprehensive
testing of Celery tasks across analysis, data processing and notification modules.
Implements test coverage tracking, structured logging, and isolated test environments.

Version: 1.0.0
"""

import logging
import pytest
from celery import current_app
from celery.contrib.testing.app import TestApp
from celery.contrib.testing.worker import start_worker
from config.settings.test import CELERY_TASK_ALWAYS_EAGER

# Test Celery configuration with eager execution and result tracking
TEST_CELERY_CONFIG = {
    'CELERY_TASK_ALWAYS_EAGER': True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'CELERY_TASK_STORE_EAGER_RESULT': True,
    'CELERY_TASK_TRACK_STARTED': True,
    'CELERY_RESULT_BACKEND': 'django-db',
    'CELERY_CACHE_BACKEND': 'memory'
}

# Configure test logger
test_logger = logging.getLogger('celery.task.tests')

def pytest_configure(config):
    """
    Configure pytest environment for comprehensive task testing.
    
    Args:
        config: pytest configuration object
    """
    # Register custom markers for task categories
    config.addinivalue_line(
        "markers", 
        "analysis: mark test as analysis task test"
    )
    config.addinivalue_line(
        "markers", 
        "processing: mark test as data processing task test"
    )
    config.addinivalue_line(
        "markers", 
        "notification: mark test as notification task test"
    )

    # Configure coverage reporting
    config.option.cov_config = '.coveragerc'
    config.option.cov_branch = True
    config.option.cov_report = 'term-missing:skip-covered'
    config.option.cov_fail_under = 80

    # Configure logging for tests
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(logging.StreamHandler())

class CeleryTestMixin:
    """
    Comprehensive mixin class providing utilities for Celery task testing.
    
    Provides setup, teardown, mock management, and test isolation utilities
    for reliable Celery task testing.
    """

    def __init__(self):
        """Initialize the Celery test mixin with test tracking and state management."""
        self.is_celery_test = True
        self.task_mocks = {}
        self.test_state = {}
        self._original_app = current_app._get_current_object()

    def setUp(self):
        """
        Prepare test environment for each test case execution.
        
        Sets up Celery for test execution with eager task processing,
        initializes mocks, and configures test isolation.
        """
        # Configure test Celery app
        self.app = TestApp()
        self.app.config_from_object(TEST_CELERY_CONFIG)
        
        # Store original Celery app state
        self._original_config = dict(self._original_app.conf)
        
        # Configure eager execution
        self._original_app.conf.update(TEST_CELERY_CONFIG)
        
        # Set up test logging context
        self.test_logger = test_logger.getChild(self.__class__.__name__)
        
        # Initialize test state
        self.test_state.clear()
        
        # Set up result collectors
        self.results = []
        
        self.test_logger.info("Test setup complete", extra={
            'test_class': self.__class__.__name__,
            'test_method': self._testMethodName
        })

    def tearDown(self):
        """
        Clean up test environment after each test case execution.
        
        Resets Celery configuration, clears mocks, and cleans up test state.
        """
        # Restore original Celery configuration
        self._original_app.conf.clear()
        self._original_app.conf.update(self._original_config)
        
        # Clear task mocks
        self.task_mocks.clear()
        
        # Clear test state
        self.test_state.clear()
        
        # Clear results
        self.results.clear()
        
        self.test_logger.info("Test teardown complete", extra={
            'test_class': self.__class__.__name__,
            'test_method': self._testMethodName
        })

    @property
    def is_celery_test(self):
        """Flag indicating this is a Celery task test."""
        return True

    @property
    def task_mocks(self):
        """Dictionary of task mocks for test isolation."""
        return self._task_mocks

    @property
    def test_state(self):
        """Dictionary for maintaining test state."""
        return self._test_state