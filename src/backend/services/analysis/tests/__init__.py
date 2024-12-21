"""
Test package initialization for the Medical Research Platform's analysis service.
Configures test settings, shared test utilities, and comprehensive test coverage tracking
for statistical analysis, pattern detection, and data visualization components.

Version: 1.0.0
"""

# Third-party imports
import pytest  # version 7.4.0
import numpy as np  # version 1.24.0
import pandas as pd  # version 2.0.0
import logging
from typing import Dict, Any

# Internal imports
from services.analysis.models import AnalysisResult

# Configure logger
logger = logging.getLogger(__name__)

# Test markers for analysis service components
ANALYSIS_TEST_MARKERS = [
    ('analysis', 'mark test as analysis service test'),
    ('statistics', 'mark test as statistical computation test'),
    ('patterns', 'mark test as pattern detection test'),
    ('visualization', 'mark test as visualization generation test'),
    ('data_quality', 'mark test as data validation test'),
    ('confidence', 'mark test as confidence level test'),
    ('performance', 'mark test as performance benchmark test')
]

# Coverage threshold (95% as per requirements)
COVERAGE_THRESHOLD = 0.95

# Performance thresholds in milliseconds
PERFORMANCE_THRESHOLDS = {
    "compute_statistics": 1000,  # 1 second max for statistical computation
    "detect_patterns": 2000,     # 2 seconds max for pattern detection
    "generate_visualization": 500 # 500ms max for visualization generation
}

# Test data version for reproducibility
TEST_DATA_VERSION = "1.0.0"

def pytest_configure(config):
    """
    Configures pytest settings for the analysis service test suite with enhanced
    coverage tracking and validation.

    Args:
        config: pytest configuration object

    Returns:
        None: Test configuration applied to pytest environment
    """
    try:
        # Register test markers
        for marker, description in ANALYSIS_TEST_MARKERS:
            config.addinivalue_line(
                "markers",
                f"{marker}: {description}"
            )

        # Set numpy random seed for reproducible tests
        np.random.seed(42)

        # Configure test database settings
        config.addinivalue_line(
            "env",
            "test_db_name=test_analysis_db"
        )
        config.addinivalue_line(
            "env",
            "test_db_isolation=true"
        )

        # Configure coverage settings
        config.option.cov_fail_under = float(COVERAGE_THRESHOLD * 100)
        config.option.cov_branch = True
        config.option.cov_report = "term-missing:skip-covered"

        # Configure test data paths
        config.option.test_data_dir = "tests/data"
        config.option.test_data_version = TEST_DATA_VERSION

        # Configure performance test settings
        for operation, threshold in PERFORMANCE_THRESHOLDS.items():
            config.addinivalue_line(
                "env",
                f"performance_threshold_{operation}={threshold}"
            )

        # Configure test result caching
        config.option.cache_dir = ".pytest_cache/analysis"
        config.option.cache_clear = False

        # Configure parallel test execution
        config.option.numprocesses = 'auto'

        # Configure test result reporting
        config.option.verbosity = 2
        config.option.showlocals = True
        config.option.tb = "short"

        # Configure data validation rules
        config.addinivalue_line(
            "env",
            "validate_statistical_significance=true"
        )
        config.addinivalue_line(
            "env",
            "minimum_confidence_level=0.95"
        )
        config.addinivalue_line(
            "env",
            "require_pattern_validation=true"
        )

        logger.info("Analysis service test configuration completed successfully")

    except Exception as e:
        logger.error(f"Error configuring analysis tests: {str(e)}")
        raise