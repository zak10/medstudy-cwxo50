"""
Test suite for analysis service API views with enhanced security and validation.
Implements comprehensive testing of analysis endpoints, data quality validation,
and security features.

Version: 1.0.0
"""

import pytest  # version ^7.4.0
from rest_framework.test import APIClient  # version ^3.14.0
from rest_framework import status  # version ^3.14.0
from django.utils import timezone
import uuid
import json
from datetime import datetime, timedelta

from services.analysis.views import AnalysisViewSet
from services.analysis.models import AnalysisResult
from services.protocol.models import Protocol
from services.data.models import DataPoint
from core.authentication import JWTAuthentication
from core.exceptions import ValidationException

# Mark all tests to use DB transactions
pytestmark = pytest.mark.django_db

class TestAnalysisViewSet:
    """
    Comprehensive test suite for AnalysisViewSet with enhanced security and validation.
    Tests analysis creation, result retrieval, and visualization endpoints.
    """

    def setup_method(self):
        """Set up test environment with enhanced security and data validation."""
        self.client = APIClient()
        self.auth = JWTAuthentication()
        
        # Create test user with protocol creator role
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
            role="protocol_creator"
        )
        
        # Create test protocol
        self.protocol = Protocol.objects.create(
            title="Test Protocol",
            creator=self.user,
            requirements={
                "data_points": [
                    {"name": "vitamin_d", "type": "numeric", "unit": "ng/mL"},
                    {"name": "energy_level", "type": "numeric", "unit": "score"}
                ],
                "frequency": {"type": "weekly", "value": 1},
                "duration": 12
            },
            status="active",
            max_participants=100
        )
        
        # Create test data points
        self.data_points = []
        base_date = timezone.now() - timedelta(weeks=4)
        
        for week in range(4):
            self.data_points.append(
                DataPoint.objects.create(
                    protocol=self.protocol,
                    user=self.user,
                    type="blood_work",
                    data={
                        "vitamin_d": 30 + week * 5,
                        "energy_level": 3 + week * 0.5
                    },
                    recorded_at=base_date + timedelta(weeks=week),
                    status="validated"
                )
            )
        
        # Get authentication token
        self.token = self.auth.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_analysis_authenticated(self):
        """Test successful analysis creation with enhanced security and data quality validation."""
        # Prepare request data
        request_data = {
            "protocol_id": str(self.protocol.id),
            "data_points": [dp.data for dp in self.data_points],
            "confidence_threshold": 0.8,
            "analysis_options": {
                "compute_statistics": True,
                "detect_patterns": True,
                "generate_visualizations": True
            }
        }
        
        # Send request
        response = self.client.post('/api/v1/analysis/', request_data, format='json')
        
        # Verify response
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert response.data["status"] == "completed"
        
        # Verify analysis result creation
        analysis = AnalysisResult.objects.get(id=response.data["id"])
        assert analysis.protocol == self.protocol
        assert analysis.status == "completed"
        
        # Verify statistical summary
        assert "basic_stats" in analysis.statistical_summary
        assert "vitamin_d" in analysis.statistical_summary["basic_stats"]
        assert "energy_level" in analysis.statistical_summary["basic_stats"]
        
        # Verify data quality compliance
        for metric in analysis.statistical_summary["basic_stats"].values():
            assert "mean" in metric
            assert "std_dev" in metric
            assert "quartiles" in metric

    def test_create_analysis_unauthenticated(self):
        """Test analysis creation rejection with enhanced security validation."""
        # Remove authentication
        self.client.credentials()
        
        request_data = {
            "protocol_id": str(self.protocol.id),
            "data_points": [dp.data for dp in self.data_points]
        }
        
        # Send request
        response = self.client.post('/api/v1/analysis/', request_data, format='json')
        
        # Verify rejection
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        
        # Verify security headers
        assert "WWW-Authenticate" in response
        assert response["WWW-Authenticate"].startswith("Bearer")

    def test_get_analysis_results(self):
        """Test retrieval of analysis results with enhanced pattern detection."""
        # Create test analysis result
        analysis = AnalysisResult.objects.create(
            protocol=self.protocol,
            statistical_summary={
                "basic_stats": {
                    "vitamin_d": {
                        "mean": 40.0,
                        "std_dev": 5.0,
                        "quartiles": {"q1": 35.0, "q2": 40.0, "q3": 45.0}
                    }
                }
            },
            patterns_detected=[
                {
                    "type": "trend",
                    "metric": "vitamin_d",
                    "direction": "increasing",
                    "confidence": 0.95
                }
            ],
            status="completed"
        )
        
        # Send request
        response = self.client.get(f'/api/v1/analysis/{self.protocol.id}/results/')
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1
        
        # Verify result data
        result = response.data["results"][0]
        assert result["id"] == str(analysis.id)
        assert "statistical_summary" in result
        assert "patterns_detected" in result
        
        # Verify pattern detection
        pattern = result["patterns_detected"][0]
        assert pattern["type"] == "trend"
        assert pattern["confidence"] >= 0.8

    def test_get_visualizations(self):
        """Test retrieval of visualization configurations with accessibility compliance."""
        # Create test analysis with visualizations
        analysis = AnalysisResult.objects.create(
            protocol=self.protocol,
            visualizations=[
                {
                    "chart_type": "time_series",
                    "config": {
                        "x_axis": {"label": "Week", "type": "datetime"},
                        "y_axis": {"label": "Vitamin D (ng/mL)", "type": "numeric"},
                        "title": "Vitamin D Levels Over Time",
                        "accessibility": {"aria_label": "Vitamin D trend chart"}
                    }
                }
            ],
            status="completed"
        )
        
        # Send request
        response = self.client.get(f'/api/v1/analysis/{analysis.id}/visualizations/')
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert "visualizations" in response.data
        
        # Verify visualization config
        viz = response.data["visualizations"][0]
        assert viz["chart_type"] == "time_series"
        assert "config" in viz
        assert "accessibility" in viz["config"]
        
        # Verify WCAG compliance
        config = viz["config"]
        assert "aria_label" in config["accessibility"]
        assert config["x_axis"]["label"] is not None
        assert config["y_axis"]["label"] is not None