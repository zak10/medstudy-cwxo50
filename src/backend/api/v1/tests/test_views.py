"""
Comprehensive test suite for API v1 view handlers.
Tests authentication flows, protocol management, data submission, analysis endpoints,
security validation, and error handling scenarios.

Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
import uuid
from unittest.mock import patch, Mock
from freezegun import freeze_time  # v1.2.0
from faker import Faker  # v19.3.0
import jwt

from api.v1.views import api_router, JWTAuth
from api.v1.schemas import APIResponse
from services.user.models import User, ROLE_CHOICES
from services.protocol.schemas import (
    PROTOCOL_REQUIREMENTS_SCHEMA,
    SAFETY_PARAMETERS_SCHEMA
)
from core.exceptions import ValidationException
from core.validators import validate_blood_work_data

# Initialize faker for consistent test data
fake = Faker()

@pytest.fixture
def jwt_auth():
    """Fixture for JWT authentication handler."""
    return JWTAuth(
        algorithm="RS256",
        access_lifetime=3600,
        refresh_lifetime=604800
    )

@pytest.fixture
def test_user(db):
    """Fixture for creating a test user."""
    return User.objects.create_user(
        email=fake.email(),
        password="TestPass123!",
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )

@pytest.fixture
def auth_headers(jwt_auth, test_user):
    """Fixture for authentication headers."""
    tokens = jwt_auth.generate_token_pair(test_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}

@pytest.mark.django_db
class TestAuthViews:
    """Test cases for authentication endpoints."""

    def setup_method(self):
        """Set up test environment."""
        self.fake = Faker()
        self.client = api_router.get_api_client()

    def test_register_user_success(self):
        """Test successful user registration with valid data."""
        registration_data = {
            "email": self.fake.email(),
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "profile": {"bio": "Test user"}
        }

        response = self.client.post("/auth/register", json=registration_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        
        # Verify user creation
        user = User.objects.get(email=registration_data["email"])
        assert user.first_name == registration_data["first_name"]
        assert user.check_password(registration_data["password"])

    def test_register_user_validation(self):
        """Test input validation for registration."""
        invalid_data = {
            "email": "invalid-email",
            "password": "weak",
            "password_confirm": "different",
            "first_name": "",
            "last_name": fake.last_name()
        }

        response = self.client.post("/auth/register", json=invalid_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["success"] is False
        assert "errors" in data
        assert any("email" in error["field"] for error in data["errors"])
        assert any("password" in error["field"] for error in data["errors"])

    def test_login_user_success(self, test_user):
        """Test successful user login flow."""
        login_data = {
            "email": test_user.email,
            "password": "TestPass123!"
        }

        response = self.client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    def test_refresh_token_success(self, jwt_auth, test_user):
        """Test successful token refresh."""
        tokens = jwt_auth.generate_token_pair(test_user)
        refresh_data = {"refresh_token": tokens["refresh_token"]}

        response = self.client.post("/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["access_token"] != tokens["access_token"]

@pytest.mark.django_db
class TestProtocolViews:
    """Test cases for protocol management endpoints."""

    def setup_method(self):
        """Set up test environment."""
        self.fake = Faker()
        self.client = api_router.get_api_client()

    def test_create_protocol_success(self, auth_headers):
        """Test successful protocol creation."""
        protocol_data = {
            "title": "Test Protocol",
            "description": "Test protocol description",
            "duration": 12,
            "requirements": {
                "title": "Test Requirements",
                "duration": 12,
                "data_collection_frequency": "weekly",
                "measurements": {
                    "vitamin_d": {
                        "min": 30,
                        "max": 100,
                        "unit": "ng/mL"
                    }
                }
            },
            "safety_params": {
                "markers": {
                    "vitamin_d": {
                        "critical_ranges": {
                            "min": 20,
                            "max": 150,
                            "unit": "ng/mL"
                        },
                        "alert_ranges": {
                            "min": 30,
                            "max": 100,
                            "unit": "ng/mL"
                        }
                    }
                },
                "intervention_triggers": [
                    {
                        "condition": "vitamin_d < 20",
                        "action": "notify_participant",
                        "notification_required": True
                    }
                ]
            }
        }

        response = self.client.post("/protocols", json=protocol_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert "protocol_id" in data["data"]
        assert data["data"]["title"] == protocol_data["title"]

    def test_submit_data_point_validation(self, auth_headers, test_user):
        """Test data point submission validation."""
        data_point = {
            "type": "blood_work",
            "data": {
                "test_date": datetime.now().isoformat(),
                "lab_name": "Test Lab",
                "lab_certification": "ABC123",
                "markers": {
                    "vitamin_d": {
                        "value": 45.5,
                        "unit": "ng/mL"
                    }
                }
            }
        }

        response = self.client.post("/data-points", json=data_point, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert "data_point_id" in data["data"]

@pytest.mark.django_db
class TestAnalysisViews:
    """Test cases for analysis endpoints."""

    def setup_method(self):
        """Set up test environment."""
        self.fake = Faker()
        self.client = api_router.get_api_client()

    def test_get_protocol_results_success(self, auth_headers):
        """Test successful retrieval of protocol results."""
        protocol_id = str(uuid.uuid4())
        
        response = self.client.get(
            f"/protocols/{protocol_id}/results",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "results" in data["data"]
        assert "statistics" in data["data"]

def test_rate_limiting():
    """Test rate limiting on API endpoints."""
    client = api_router.get_api_client()
    
    # Test auth endpoint rate limiting
    for _ in range(6):  # Exceeds 5/minute limit
        response = client.post("/auth/login", json={
            "email": fake.email(),
            "password": "TestPass123!"
        })
    
    assert response.status_code == 429
    assert "Too many requests" in response.json()["message"]

@pytest.mark.parametrize("token", [
    "invalid_token",
    "expired_token",
    None
])
def test_authentication_failure(token):
    """Test authentication failure scenarios."""
    client = api_router.get_api_client()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = client.get("/protocols", headers=headers)
    assert response.status_code == 401
    assert response.json()["success"] is False