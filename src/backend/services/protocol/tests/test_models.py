"""
Comprehensive test suite for Protocol and Participation models.
Tests protocol management, data collection, safety parameters, timeline management,
and capacity controls with extensive coverage of core functionality and edge cases.

Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from faker import Faker
import json

from services.protocol.models import Protocol, Participation
from services.user.models import User
from core.exceptions import ValidationException

# Configure Faker
fake = Faker()

# Mark all tests to use database
pytestmark = pytest.mark.django_db

# Test data constants
VALID_REQUIREMENTS = {
    "data_points": [
        {
            "name": "vitamin_d",
            "type": "number",
            "unit": "ng/mL",
            "range": {"min": 20, "max": 80}
        },
        {
            "name": "energy_level",
            "type": "number",
            "unit": "score",
            "range": {"min": 1, "max": 5}
        }
    ],
    "frequency": {"type": "weekly", "value": 1},
    "duration": 12
}

VALID_SAFETY_PARAMS = {
    "vitamin_d": {
        "min": 10,
        "max": 100,
        "critical_min": 5,
        "critical_max": 150
    },
    "energy_level": {
        "min": 1,
        "max": 5
    }
}

@pytest.fixture
def test_user():
    """Create test user with required profile."""
    return User.objects.create_user(
        email=fake.email(),
        password="TestPass123!",
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        profile={"age": 30, "gender": "F"}
    )

@pytest.fixture
def test_protocol(test_user):
    """Create test protocol with valid configuration."""
    return Protocol.objects.create(
        title="Test Vitamin D Protocol",
        description="Test protocol for vitamin D supplementation",
        creator=test_user,
        requirements=VALID_REQUIREMENTS,
        safety_params=VALID_SAFETY_PARAMS,
        duration_weeks=12,
        min_participants=5,
        max_participants=100,
        version="1.0.0"
    )

class TestProtocolModel:
    """Comprehensive test suite for Protocol model."""

    def test_protocol_creation(self, test_user):
        """Test protocol creation with all required fields."""
        protocol = Protocol.objects.create(
            title="Test Protocol",
            description="Test description",
            creator=test_user,
            requirements=VALID_REQUIREMENTS,
            safety_params=VALID_SAFETY_PARAMS,
            duration_weeks=12,
            min_participants=5,
            max_participants=100
        )

        assert protocol.id is not None
        assert protocol.title == "Test Protocol"
        assert protocol.status == "draft"
        assert protocol.created_at is not None
        assert protocol.updated_at is not None
        assert len(protocol.audit_log) == 1
        assert protocol.version == "1.0.0"

    def test_protocol_requirements_validation(self, test_protocol):
        """Test protocol requirements validation."""
        # Test valid requirements
        assert test_protocol.validate_requirements() is True

        # Test invalid requirements
        invalid_requirements = VALID_REQUIREMENTS.copy()
        invalid_requirements["data_points"][0].pop("type")
        
        test_protocol.requirements = invalid_requirements
        assert test_protocol.validate_requirements() is False

        # Test missing required fields
        with pytest.raises(ValidationException):
            test_protocol.requirements = {}
            test_protocol.save()

    @pytest.mark.parametrize("safety_scenario", [
        {"param": "vitamin_d", "value": 5, "expected_violation": True},
        {"param": "vitamin_d", "value": 50, "expected_violation": False},
        {"param": "vitamin_d", "value": 160, "expected_violation": True},
        {"param": "energy_level", "value": 0, "expected_violation": True},
        {"param": "energy_level", "value": 3, "expected_violation": False}
    ])
    def test_safety_parameter_validation(self, test_protocol, safety_scenario):
        """Test safety parameter validation with various scenarios."""
        data_point = {
            safety_scenario["param"]: safety_scenario["value"]
        }

        violation_found, message, details = test_protocol.check_safety_violation(data_point)
        assert violation_found == safety_scenario["expected_violation"]
        
        if violation_found:
            assert message == "Safety parameter violation detected"
            assert safety_scenario["param"] in details

    @freeze_time("2023-01-01")
    def test_protocol_timeline_management(self, test_protocol):
        """Test protocol timeline validation and management."""
        # Test start date validation
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=test_protocol.duration_weeks)
        
        test_protocol.start_date = start_date
        test_protocol.end_date = end_date
        test_protocol.save()

        # Test invalid timeline
        with pytest.raises(ValidationException):
            test_protocol.start_date = end_date
            test_protocol.end_date = start_date
            test_protocol.save()

        # Test duration validation
        assert (test_protocol.end_date - test_protocol.start_date).days == test_protocol.duration_weeks * 7

    def test_protocol_capacity_management(self, test_protocol, test_user):
        """Test protocol capacity controls and validation."""
        # Create participants up to minimum
        for _ in range(test_protocol.min_participants):
            user = User.objects.create_user(
                email=fake.email(),
                password="TestPass123!",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            Participation.objects.create(
                protocol=test_protocol,
                user=user
            )

        # Verify protocol can be activated
        test_protocol.status = "active"
        test_protocol.save()

        # Test maximum capacity
        test_protocol.max_participants = test_protocol.participations.count()
        test_protocol.save()

        # Verify cannot exceed capacity
        with pytest.raises(ValidationException):
            Participation.objects.create(
                protocol=test_protocol,
                user=test_user
            )

class TestParticipationModel:
    """Comprehensive test suite for Participation model."""

    def test_participation_enrollment(self, test_protocol, test_user):
        """Test participation enrollment and validation."""
        participation = Participation.objects.create(
            protocol=test_protocol,
            user=test_user
        )

        assert participation.id is not None
        assert participation.status == "enrolled"
        assert participation.enrolled_at is not None
        assert participation.progress_percentage == 0.0
        assert len(participation.audit_log) == 1

    def test_participation_completion_tracking(self, test_protocol, test_user):
        """Test participation completion tracking and validation."""
        participation = Participation.objects.create(
            protocol=test_protocol,
            user=test_user
        )

        # Test partial completion
        participation.completion_data = {
            "vitamin_d": [{"value": 45, "date": "2023-01-01"}]
        }
        participation.save()

        completion_status = participation.check_completion()
        assert not completion_status["completed"]
        assert len(completion_status["missing_requirements"]) == 1
        assert completion_status["progress"] == 50.0

        # Test full completion
        participation.completion_data = {
            "vitamin_d": [{"value": 45, "date": "2023-01-01"}],
            "energy_level": [{"value": 4, "date": "2023-01-01"}]
        }
        participation.save()

        completion_status = participation.check_completion()
        assert completion_status["completed"]
        assert len(completion_status["missing_requirements"]) == 0
        assert completion_status["progress"] == 100.0

    @freeze_time("2023-01-01")
    def test_participation_timeline_compliance(self, test_protocol, test_user):
        """Test participation timeline compliance and validation."""
        participation = Participation.objects.create(
            protocol=test_protocol,
            user=test_user
        )

        # Set protocol timeline
        test_protocol.start_date = datetime.now()
        test_protocol.end_date = test_protocol.start_date + timedelta(weeks=test_protocol.duration_weeks)
        test_protocol.save()

        # Test completion within timeline
        participation.completion_data = {
            "vitamin_d": [{"value": 45, "date": "2023-01-15"}],
            "energy_level": [{"value": 4, "date": "2023-01-15"}]
        }
        participation.save()

        # Verify completion date
        assert participation.completed_at is not None
        assert participation.completed_at <= test_protocol.end_date