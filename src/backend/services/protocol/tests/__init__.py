"""
Protocol service test package initialization.
Configures test settings, shared test utilities, and comprehensive test data fixtures
for protocol management testing with enhanced validation and security features.

Version: 1.0.0
"""

import pytest
from freezegun import freeze_time
from services.protocol.models import Protocol, Participation

# Test protocol data with comprehensive requirements and safety parameters
TEST_PROTOCOL_DATA = {
    "title": "Test Protocol",
    "description": "Comprehensive protocol for testing all features",
    "requirements": {
        "data_points": [
            {
                "name": "vitamin_d",
                "type": "numeric",
                "unit": "ng/mL",
                "range": {"min": 20, "max": 80}
            },
            {
                "name": "omega_3",
                "type": "numeric", 
                "unit": "mg/dL",
                "range": {"min": 100, "max": 300}
            }
        ],
        "frequency": {
            "type": "monthly",
            "value": 1
        },
        "duration": 12
    },
    "safety_params": {
        "min_age": 18,
        "max_age": 65,
        "exclusion_criteria": ["pregnancy", "heart_condition"],
        "required_clearance": ["physician_approval"]
    },
    "duration_weeks": 12,
    "min_participants": 1,
    "max_participants": 100,
    "safety_violation_thresholds": {
        "vitamin_d": {"min": 10, "max": 100},
        "omega_3": {"min": 50, "max": 400}
    },
    "data_collection_frequency": {
        "blood_work": "monthly",
        "check_ins": "weekly"
    }
}

# Test participation data with progress tracking and safety checks
TEST_PARTICIPATION_DATA = {
    "status": "enrolled",
    "progress_percentage": 0.0,
    "participation_metrics": {
        "completed_steps": 0,
        "total_steps": 12,
        "last_checkin": None,
        "next_blood_work_due": None,
        "compliance_rate": 0.0
    },
    "completion_data": {},
    "audit_log": []
}

def pytest_configure(config):
    """
    Configure pytest settings and environment for protocol service tests.
    
    Args:
        config: pytest configuration object
        
    Configures:
        - Test database settings
        - Custom test markers
        - Coverage requirements
        - Time freezing
        - Test fixtures
    """
    # Register custom markers for test organization
    config.addinivalue_line(
        "markers",
        "protocol: mark test as protocol management related"
    )
    config.addinivalue_line(
        "markers", 
        "participation: mark test as protocol participation related"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring multiple components"
    )
    config.addinivalue_line(
        "markers",
        "temporal: mark test as time-dependent"
    )
    
    # Configure test database settings
    config.option.database_name = "test_protocol_db"
    config.option.database_isolation = True
    
    # Set minimum test coverage requirements (80%)
    config.option.cov_fail_under = 80
    config.option.cov_branch = True
    
    # Configure time freezing for temporal consistency
    config.option.freezegun_default_time = "2024-01-01T00:00:00Z"
    
    # Set up test fixtures path
    config.option.fixtures_path = "tests/fixtures"
    
    # Configure test logging
    config.option.log_level = "DEBUG"
    config.option.log_format = (
        "%(asctime)s [%(levelname)s] "
        "%(name)s:%(lineno)d - %(message)s"
    )

# Register custom test fixtures
@pytest.fixture
def test_protocol():
    """
    Creates a test protocol instance with comprehensive test data.
    
    Returns:
        Protocol: Configured test protocol instance
    """
    return Protocol.objects.create(**TEST_PROTOCOL_DATA)

@pytest.fixture
def test_participation(test_protocol, test_user):
    """
    Creates a test participation instance with progress tracking.
    
    Args:
        test_protocol: Protocol fixture
        test_user: User fixture
        
    Returns:
        Participation: Configured test participation instance
    """
    return Participation.objects.create(
        protocol=test_protocol,
        user=test_user,
        **TEST_PARTICIPATION_DATA
    )

@pytest.fixture
def freeze_test_time():
    """
    Freezes time for temporal test consistency.
    
    Yields:
        datetime: Frozen datetime object
    """
    with freeze_time("2024-01-01T00:00:00Z"):
        yield