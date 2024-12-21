"""
Test package initialization for the data service test suite.
Configures pytest settings, coverage requirements, and test environment.

Version: 1.0
Coverage Requirements: 80% minimum with branch coverage
Database: PostgreSQL with serializable isolation
"""

# External imports - versions specified in comments
import pytest  # v7.4+
from pytest_django.plugin import django_db_setup  # v4.5+
from coverage.files import FileLocator  # v7.2+

# Configure required pytest plugins
pytest_plugins = [
    'pytest_django.fixtures',
    'pytest_cov.plugin'
]

# Django settings module for tests
DJANGO_SETTINGS_MODULE = 'backend.services.data.tests.test_settings'

def pytest_configure(config):
    """
    Configure pytest settings for the data service test suite.
    
    Args:
        config (pytest.Config): Pytest configuration object
    
    Returns:
        None: Configuration settings are applied to the pytest environment
    """
    # Register markers for test categorization
    config.addinivalue_line(
        "markers",
        "models: marks tests as model tests"
    )
    config.addinivalue_line(
        "markers", 
        "views: marks tests as view/endpoint tests"
    )

    # Configure test database settings
    config.option.database_isolation_level = 'serializable'
    config.option.database_engine = 'django.db.backends.postgresql'
    config.option.database_name = 'test_db'

    # Configure coverage settings
    config.option.cov_branch = True
    config.option.cov_fail_under = 80
    config.option.cov_report = {
        'term-missing': True,
        'html': 'coverage_html',
        'xml': 'coverage.xml'
    }
    
    # Set coverage source and omit patterns
    config.option.cov_source = ['backend.services.data']
    config.option.cov_omit = [
        '*/migrations/*',
        '*/tests/*',
        '*/test_*.py'
    ]

    # Configure test environment
    config.option.env = {
        'TEST_MODE': 'True',
        'DEBUG': 'False',
        'ASYNC_MODE': 'True'
    }

    # Configure test reporting
    config.option.verbose = 2
    config.option.showlocals = True
    config.option.tb = 'short'

    # Configure parallel execution settings
    config.option.numprocesses = 'auto'
    
    # Configure logging for tests
    config.option.log_level = 'INFO'
    config.option.log_format = '%(asctime)s %(levelname)s %(message)s'
    config.option.log_date_format = '%Y-%m-%d %H:%M:%S'

    # Configure test collection
    config.option.testpaths = ['tests']
    config.option.python_files = ['test_*.py']
    config.option.python_classes = ['Test*']
    config.option.python_functions = ['test_*']

    # Configure fixture behavior
    config.option.fixture_scope = 'function'
    config.option.fixture_max_share = 2

    # Configure cleanup procedures
    config.option.cleanup = 'always'