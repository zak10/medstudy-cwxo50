"""
Unit tests for analysis service models.

This module implements comprehensive test cases for statistical analysis,
pattern detection, visualization generation, and time series analysis with
robust data validation and error handling.

Version: 1.0.0
"""

import pytest  # version 7.4
import numpy as np  # version 1.24
from django.test import TestCase  # version 4.2
from django.utils import timezone  # version 4.2
from datetime import timedelta
import uuid

from ..models import AnalysisResult, TimeSeriesMetric
from services.protocol.models import Protocol
from services.data.models import DataPoint
from core.exceptions import ValidationException

@pytest.fixture
def create_test_data_points(protocol, count=30, distribution_params=None):
    """
    Generate test data points with controlled statistical properties.
    
    Args:
        protocol: Protocol instance
        count: Number of data points to generate
        distribution_params: Statistical distribution parameters
        
    Returns:
        List of DataPoint instances
    """
    if distribution_params is None:
        distribution_params = {
            'mean': 100,
            'std': 15
        }
    
    data_points = []
    base_time = timezone.now()
    
    # Generate data points with known distribution
    for i in range(count):
        value = np.random.normal(
            distribution_params['mean'],
            distribution_params['std']
        )
        
        data_point = DataPoint(
            id=uuid.uuid4(),
            protocol=protocol,
            type='biometric',
            data={
                'value': float(value),
                'unit': 'mg/dL'
            },
            recorded_at=base_time + timedelta(days=i),
            status='validated'
        )
        data_points.append(data_point)
    
    return data_points

class TestAnalysisResult(TestCase):
    """
    Comprehensive test suite for AnalysisResult model covering statistical analysis,
    pattern detection, and visualization generation.
    """
    
    def setUp(self):
        """Initialize test environment with protocol, data points, and analysis configuration."""
        # Create test protocol
        self.protocol = Protocol.objects.create(
            title="Test Protocol",
            description="Test protocol for analysis",
            duration_weeks=12,
            max_participants=100
        )
        
        # Test configuration
        self.test_config = {
            'metrics': ['value'],
            'time_series': True,
            'correlation_analysis': True
        }
        
        # Set confidence threshold for pattern detection
        self.confidence_threshold = 0.8
        
        # Create analysis result instance
        self.analysis_result = AnalysisResult.objects.create(
            protocol=self.protocol
        )
        
        # Generate test data points
        self.data_points = create_test_data_points(
            self.protocol,
            count=30,
            distribution_params={'mean': 100, 'std': 15}
        )

    def test_compute_statistics(self):
        """Validate statistical computation accuracy and correlation analysis."""
        # Compute statistics
        stats = self.analysis_result.compute_statistics(self.data_points)
        
        # Validate basic statistical measures
        self.assertIn('metrics', stats)
        self.assertIn('value', stats['metrics'])
        
        value_stats = stats['metrics']['value']
        
        # Test mean calculation
        self.assertAlmostEqual(
            value_stats['mean'],
            100,
            delta=5,
            msg="Mean should be approximately 100"
        )
        
        # Test standard deviation
        self.assertAlmostEqual(
            value_stats['std_dev'],
            15,
            delta=3,
            msg="Standard deviation should be approximately 15"
        )
        
        # Validate confidence intervals
        self.assertIn('confidence_interval_95', value_stats)
        ci = value_stats['confidence_interval_95']
        self.assertLess(ci['lower'], value_stats['mean'])
        self.assertGreater(ci['upper'], value_stats['mean'])
        
        # Validate quartiles
        self.assertIn('quartiles', value_stats)
        self.assertLess(
            value_stats['quartiles']['q1'],
            value_stats['quartiles']['q2']
        )
        self.assertLess(
            value_stats['quartiles']['q2'],
            value_stats['quartiles']['q3']
        )
        
        # Validate time metrics
        self.assertIn('time_metrics', stats)
        self.assertEqual(
            stats['time_metrics']['duration_days'],
            29,
            msg="Duration should be 29 days for 30 daily measurements"
        )

    def test_detect_patterns(self):
        """Test pattern detection algorithms and threshold sensitivity."""
        # Create data points with known trend
        trend_data = create_test_data_points(
            self.protocol,
            count=30,
            distribution_params={'mean': 100, 'std': 5}
        )
        
        # Add linear trend
        for i, dp in enumerate(trend_data):
            dp.data['value'] += i * 0.5  # Add increasing trend
        
        # Detect patterns
        patterns = self.analysis_result.detect_patterns(
            trend_data,
            confidence_threshold=self.confidence_threshold
        )
        
        # Validate trend detection
        trend_patterns = [p for p in patterns if p['type'] == 'trend']
        self.assertTrue(
            len(trend_patterns) > 0,
            msg="Should detect increasing trend"
        )
        
        # Validate trend direction
        trend = trend_patterns[0]
        self.assertEqual(
            trend['direction'],
            'increasing',
            msg="Should identify increasing trend"
        )
        
        # Validate confidence level
        self.assertGreaterEqual(
            trend['confidence'],
            self.confidence_threshold,
            msg="Trend confidence should meet threshold"
        )
        
        # Test seasonality detection
        seasonal_data = create_test_data_points(
            self.protocol,
            count=60
        )
        # Add seasonal pattern
        for i, dp in enumerate(seasonal_data):
            dp.data['value'] += 10 * np.sin(2 * np.pi * i / 7)  # Weekly pattern
            
        patterns = self.analysis_result.detect_patterns(seasonal_data)
        seasonal_patterns = [p for p in patterns if p['type'] == 'seasonality']
        
        self.assertTrue(
            len(seasonal_patterns) > 0,
            msg="Should detect seasonal pattern"
        )

    def test_generate_visualizations(self):
        """Verify visualization generation and configuration accuracy."""
        # Compute statistics and detect patterns
        stats = self.analysis_result.compute_statistics(self.data_points)
        patterns = self.analysis_result.detect_patterns(self.data_points)
        
        # Generate visualizations
        visualizations = self.analysis_result.generate_visualizations(
            stats,
            patterns
        )
        
        # Validate time series visualization
        time_series_viz = next(
            (v for v in visualizations if v['type'] == 'time_series'),
            None
        )
        self.assertIsNotNone(time_series_viz)
        self.assertEqual(time_series_viz['metric'], 'value')
        self.assertTrue(time_series_viz['config']['include_trend'])
        self.assertTrue(time_series_viz['config']['confidence_interval'])
        
        # Validate distribution visualization
        dist_viz = next(
            (v for v in visualizations if v['type'] == 'distribution'),
            None
        )
        self.assertIsNotNone(dist_viz)
        self.assertTrue(dist_viz['config']['show_quartiles'])
        self.assertTrue(dist_viz['config']['include_stats'])
        
        # Validate visualization configs
        for viz in visualizations:
            self.assertIn('title', viz['config'])
            self.assertIsInstance(viz['config'], dict)

class TestTimeSeriesMetric(TestCase):
    """
    Test suite for TimeSeriesMetric model focusing on trend analysis
    and time-based patterns.
    """
    
    def setUp(self):
        """Set up time series test environment with sample data."""
        # Create test protocol
        self.protocol = Protocol.objects.create(
            title="Time Series Test Protocol",
            description="Protocol for time series analysis",
            duration_weeks=8,
            max_participants=50
        )
        
        # Create analysis result
        self.analysis_result = AnalysisResult.objects.create(
            protocol=self.protocol
        )
        
        # Configure trend analysis
        self.trend_config = {
            'window_size': 7,
            'min_periods': 3,
            'center': True
        }
        
        # Generate time series data
        self.data_points = create_test_data_points(
            self.protocol,
            count=60
        )

    def test_analyze_trend(self):
        """Validate trend analysis functionality and metrics."""
        # Add known trend to data
        for i, dp in enumerate(self.data_points):
            # Linear trend + seasonal component
            dp.data['value'] += i * 0.3  # Linear trend
            dp.data['value'] += 5 * np.sin(2 * np.pi * i / 7)  # Weekly seasonality
        
        # Perform trend analysis
        stats = self.analysis_result.compute_statistics(self.data_points)
        patterns = self.analysis_result.detect_patterns(
            self.data_points,
            confidence_threshold=0.8
        )
        
        # Validate trend detection
        trend_patterns = [p for p in patterns if p['type'] == 'trend']
        self.assertTrue(len(trend_patterns) > 0)
        
        trend = trend_patterns[0]
        self.assertEqual(trend['direction'], 'increasing')
        self.assertGreater(trend['confidence'], 0.8)
        
        # Validate seasonal pattern detection
        seasonal_patterns = [p for p in patterns if p['type'] == 'seasonality']
        self.assertTrue(len(seasonal_patterns) > 0)
        
        seasonal = seasonal_patterns[0]
        self.assertAlmostEqual(
            seasonal['details']['period_days'],
            7,
            delta=1,
            msg="Should detect weekly seasonality"
        )