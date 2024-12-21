"""
Unit tests for protocol data analysis tasks.
Tests statistical computations, pattern detection, visualization generation,
safety monitoring, and data quality validation with comprehensive coverage.

Version: 1.0.0
"""

# Standard library imports
import uuid
from datetime import datetime, timedelta

# Third-party imports
import pytest  # version 7.4+
from unittest.mock import Mock, patch, call  # version 3.11+
import numpy as np  # version 1.24
from freezegun import freeze_time  # version 1.2+

# Internal imports
from tasks.analysis import (
    analyze_protocol_data,
    update_time_series_metrics,
    detect_safety_violations
)
from services.analysis.models import AnalysisResult
from services.protocol.models import Protocol
from services.data.models import DataPoint
from core.exceptions import ValidationException

@pytest.fixture
def mock_protocol():
    """Fixture for test protocol instance."""
    protocol = Mock(spec=Protocol)
    protocol.id = uuid.uuid4()
    protocol.title = "Test Protocol"
    protocol.requirements = {
        "data_points": [
            {"name": "vitamin_d", "type": "numeric", "unit": "ng/mL"},
            {"name": "energy_level", "type": "numeric", "unit": "score"}
        ],
        "frequency": {"type": "weekly", "value": 1},
        "duration": 12
    }
    protocol.safety_violation_thresholds = {
        "vitamin_d": {"min": 20, "max": 100},
        "energy_level": {"min": 1, "max": 5}
    }
    return protocol

@pytest.fixture
def mock_data_points():
    """Fixture for test data points."""
    data_points = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(10):
        dp = Mock(spec=DataPoint)
        dp.id = uuid.uuid4()
        dp.recorded_at = base_date + timedelta(days=i*3)
        dp.data = {
            "vitamin_d": 40 + i,
            "energy_level": 3 + (i % 3)
        }
        dp.status = "validated"
        data_points.append(dp)
    
    return data_points

@pytest.mark.asyncio
class TestAnalysisTask:
    """Test cases for protocol data analysis tasks."""

    def setup_method(self):
        """Set up test environment."""
        self.test_data = np.array([
            [40, 3], [45, 4], [50, 3], [55, 5],
            [60, 4], [65, 3], [70, 5], [75, 4]
        ])

    @pytest.mark.django_db
    @patch('tasks.analysis.AnalysisResult')
    async def test_analyze_protocol_data_success(
        self, mock_analysis_result, mock_protocol, mock_data_points
    ):
        """Test successful protocol data analysis."""
        # Setup mocks
        mock_result = Mock(spec=AnalysisResult)
        mock_result.id = uuid.uuid4()
        mock_analysis_result.objects.create.return_value = mock_result
        
        # Mock analysis methods
        mock_result.compute_statistics.return_value = {
            "sample_size": 8,
            "metrics": {
                "vitamin_d": {
                    "mean": 57.5,
                    "std_dev": 12.5,
                    "range": {"min": 40, "max": 75}
                },
                "energy_level": {
                    "mean": 3.875,
                    "std_dev": 0.83,
                    "range": {"min": 3, "max": 5}
                }
            }
        }
        
        mock_result.detect_patterns.return_value = [
            {
                "type": "trend",
                "metric": "vitamin_d",
                "direction": "increasing",
                "confidence": 0.95
            }
        ]
        
        mock_result.generate_visualizations.return_value = [
            {
                "type": "time_series",
                "metric": "vitamin_d",
                "config": {
                    "title": "Vitamin D Levels Over Time",
                    "include_trend": True
                }
            }
        ]

        # Execute task
        result_id = await analyze_protocol_data(mock_protocol.id)

        # Verify analysis result creation
        mock_analysis_result.objects.create.assert_called_once_with(
            protocol=mock_protocol,
            status='processing'
        )

        # Verify analysis method calls
        mock_result.compute_statistics.assert_called_once()
        mock_result.detect_patterns.assert_called_once_with(
            mock_data_points,
            confidence_threshold=0.80
        )
        mock_result.generate_visualizations.assert_called_once()

        # Verify result updates
        assert mock_result.status == 'completed'
        mock_result.save.assert_called()
        assert str(result_id) == str(mock_result.id)

    @pytest.mark.django_db
    @patch('tasks.analysis.AnalysisResult')
    async def test_analyze_protocol_data_no_data_points(
        self, mock_analysis_result, mock_protocol
    ):
        """Test analysis task with no data points."""
        with pytest.raises(ValidationException) as exc:
            await analyze_protocol_data(mock_protocol.id)
        assert "No validated data points found for analysis" in str(exc.value)

    @pytest.mark.django_db
    @freeze_time("2024-01-01 12:00:00")
    async def test_update_time_series_metrics(self, mock_protocol, mock_data_points):
        """Test time series metrics update task."""
        # Execute task
        metrics = await update_time_series_metrics(mock_protocol.id)

        # Verify metrics structure
        assert "vitamin_d" in metrics
        assert "energy_level" in metrics

        # Verify metric components
        for metric_name in ["vitamin_d", "energy_level"]:
            metric_data = metrics[metric_name]
            assert "trend" in metric_data
            assert "seasonal" in metric_data
            assert "change_rate" in metric_data
            assert "volatility" in metric_data
            assert "significance" in metric_data
            assert isinstance(metric_data["change_rate"], float)
            assert isinstance(metric_data["volatility"], float)

    @pytest.mark.django_db
    async def test_detect_safety_violations(self, mock_protocol, mock_data_points):
        """Test safety violation detection task."""
        # Modify a data point to trigger violation
        mock_data_points[0].data["vitamin_d"] = 15  # Below minimum threshold
        
        # Execute task
        violations = await detect_safety_violations(mock_protocol.id)

        # Verify violations detection
        assert len(violations) > 0
        violation = violations[0]
        assert violation["data_point_id"] == str(mock_data_points[0].id)
        assert "severity_score" in violation
        assert violation["requires_action"] == True
        assert "vitamin_d" in violation["details"]
        assert violation["details"]["vitamin_d"]["type"] == "below_minimum"

    @pytest.mark.django_db
    @patch('tasks.analysis.AnalysisResult')
    async def test_analyze_protocol_data_validation(
        self, mock_analysis_result, mock_protocol, mock_data_points
    ):
        """Test data quality validation in analysis task."""
        # Mock validation failure
        mock_result = Mock(spec=AnalysisResult)
        mock_result.compute_statistics.side_effect = ValidationException(
            "Invalid data format"
        )
        mock_analysis_result.objects.create.return_value = mock_result

        # Execute and verify exception
        with pytest.raises(ValidationException) as exc:
            await analyze_protocol_data(mock_protocol.id)
        assert "Invalid data format" in str(exc.value)
        assert mock_result.status == 'failed'

def pytest_configure(config):
    """Configure pytest environment."""
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )
    
    # Configure test timeouts
    config.addinivalue_line(
        "markers",
        "timeout: mark test execution timeout"
    )