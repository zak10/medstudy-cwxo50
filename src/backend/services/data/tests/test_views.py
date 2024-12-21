"""
Test suite for data collection API views in the Medical Research Platform.
Validates data submission, security controls, and quality requirements for blood work,
biometrics, and participant experiences.

Version: 1.0.0
"""

import json
from datetime import datetime, timedelta
import uuid
from unittest.mock import patch, MagicMock

import pytest
from rest_framework.test import APIClient
from rest_framework import status

from services.data.views import DataPointView, BloodWorkView, CheckInView
from services.data.models import DataPoint, BloodworkResult
from services.protocol.models import Protocol, Participation
from services.user.models import User
from core.exceptions import ValidationException

# Test data constants
VALID_BLOOD_WORK_DATA = {
    "markers": {
        "vitamin_d": 45.2,
        "crp": 0.8,
        "hdl": 62,
        "ldl": 89,
        "triglycerides": 120
    },
    "test_date": datetime.now().isoformat(),
    "lab_name": "Quest Diagnostics",
    "file_hash": "a" * 64,
    "reference_ranges": {
        "vitamin_d": {"min": 30, "max": 100},
        "crp": {"min": 0, "max": 3},
        "hdl": {"min": 40, "max": 100},
        "ldl": {"min": 0, "max": 100},
        "triglycerides": {"min": 0, "max": 150}
    }
}

VALID_CHECK_IN_DATA = {
    "energy_level": 4,
    "sleep_quality": 3,
    "side_effects": "Mild headache in the morning",
    "additional_notes": {"mood": "Stable", "appetite": "Normal"},
    "symptoms": ["headache", "fatigue"]
}

@pytest.mark.django_db
class TestDataPointView:
    """Test cases for data point submission and retrieval."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test protocol
        self.protocol = Protocol.objects.create(
            title="Test Protocol",
            creator=self.user,
            requirements={
                "data_points": ["blood_work", "check_in"],
                "frequency": "weekly",
                "duration": 12
            },
            safety_params={
                "vitamin_d": {"min": 30, "max": 100}
            },
            duration_weeks=12,
            max_participants=100
        )
        
        # Create participation
        self.participation = Participation.objects.create(
            protocol=self.protocol,
            user=self.user,
            status="active"
        )

    def test_create_data_point_blood_work_success(self):
        """Test successful creation of blood work data point."""
        data = {
            "type": "blood_work",
            "protocol_id": str(self.protocol.id),
            "data": VALID_BLOOD_WORK_DATA,
            "recorded_at": datetime.now().isoformat()
        }
        
        response = self.client.post(
            "/api/v1/data-points/",
            data=json.dumps(data),
            content_type="application/json"
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "data_point_id" in response.data
        assert DataPoint.objects.count() == 1
        
        # Verify data encryption
        data_point = DataPoint.objects.first()
        assert "encryption_metadata" in data_point.data
        assert data_point.type == "blood_work"

    def test_create_data_point_check_in_success(self):
        """Test successful creation of check-in data point."""
        data = {
            "type": "check_in",
            "protocol_id": str(self.protocol.id),
            "data": VALID_CHECK_IN_DATA,
            "recorded_at": datetime.now().isoformat()
        }
        
        response = self.client.post(
            "/api/v1/data-points/",
            data=json.dumps(data),
            content_type="application/json"
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert DataPoint.objects.count() == 1
        
        # Verify data sanitization
        data_point = DataPoint.objects.first()
        assert "<" not in data_point.data["side_effects"]
        assert data_point.type == "check_in"

    def test_create_data_point_invalid_type(self):
        """Test validation of invalid data point type."""
        data = {
            "type": "invalid_type",
            "protocol_id": str(self.protocol.id),
            "data": {},
            "recorded_at": datetime.now().isoformat()
        }
        
        response = self.client.post(
            "/api/v1/data-points/",
            data=json.dumps(data),
            content_type="application/json"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "type" in response.data["details"]["fields"]

    def test_create_data_point_invalid_protocol(self):
        """Test validation of non-existent protocol."""
        data = {
            "type": "blood_work",
            "protocol_id": str(uuid.uuid4()),
            "data": VALID_BLOOD_WORK_DATA,
            "recorded_at": datetime.now().isoformat()
        }
        
        response = self.client.post(
            "/api/v1/data-points/",
            data=json.dumps(data),
            content_type="application/json"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "protocol" in response.data["details"]["fields"]

    def test_get_data_points_success(self):
        """Test successful retrieval of data points."""
        # Create test data points
        DataPoint.objects.create(
            user=self.user,
            protocol=self.protocol,
            type="blood_work",
            data=VALID_BLOOD_WORK_DATA,
            recorded_at=datetime.now()
        )
        
        response = self.client.get("/api/v1/data-points/")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["count"] == 1

    def test_get_data_points_with_filters(self):
        """Test data point retrieval with filters."""
        # Create test data points
        DataPoint.objects.create(
            user=self.user,
            protocol=self.protocol,
            type="blood_work",
            data=VALID_BLOOD_WORK_DATA,
            recorded_at=datetime.now()
        )
        DataPoint.objects.create(
            user=self.user,
            protocol=self.protocol,
            type="check_in",
            data=VALID_CHECK_IN_DATA,
            recorded_at=datetime.now()
        )
        
        response = self.client.get(
            "/api/v1/data-points/",
            {"type": "blood_work"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["type"] == "blood_work"

@pytest.mark.django_db
class TestBloodWorkView:
    """Test cases for blood work submission and validation."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock S3 client
        self.s3_patcher = patch('boto3.client')
        self.mock_s3 = self.s3_patcher.start()

    def teardown_method(self):
        """Clean up after each test method."""
        self.s3_patcher.stop()

    @patch('services.data.views.BloodWorkView.validate_lab_report')
    def test_submit_blood_work_success(self, mock_validate):
        """Test successful blood work submission with file upload."""
        mock_validate.return_value = True
        
        # Create test file
        test_file = MagicMock()
        test_file.name = "test_report.pdf"
        test_file.read.return_value = b"test content"
        
        data = {
            "report_file": test_file,
            **VALID_BLOOD_WORK_DATA
        }
        
        response = self.client.post(
            "/api/v1/blood-work/",
            data=data,
            format="multipart"
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert BloodworkResult.objects.count() == 1
        assert self.mock_s3.return_value.upload_fileobj.called

    def test_submit_blood_work_invalid_markers(self):
        """Test validation of invalid blood work markers."""
        data = {
            **VALID_BLOOD_WORK_DATA,
            "markers": {
                "vitamin_d": -1,  # Invalid negative value
                "invalid_marker": 100
            }
        }
        
        response = self.client.post(
            "/api/v1/blood-work/",
            data=data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "markers" in response.data["details"]["fields"]

    def test_submit_blood_work_missing_required_markers(self):
        """Test validation of missing required blood markers."""
        data = {
            **VALID_BLOOD_WORK_DATA,
            "markers": {
                "vitamin_d": 45.2  # Missing other required markers
            }
        }
        
        response = self.client.post(
            "/api/v1/blood-work/",
            data=data,
            format="json"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "markers" in response.data["details"]["fields"]