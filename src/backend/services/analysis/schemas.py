"""
Pydantic schemas for analysis service data validation and serialization.
Implements comprehensive validation rules for statistical analysis, pattern detection,
and visualization configurations with enhanced error handling.

Version: 1.0.0
"""

from datetime import datetime  # version 3.11
from typing import Dict, List, Optional, Union
from uuid import UUID  # version 3.11
from pydantic import BaseModel, Field, validator  # version ^2.0

from services.analysis.models import AnalysisResult
from core.validators import validate_protocol_requirements

# Constants for validation
MIN_CONFIDENCE_THRESHOLD = 0.6
MAX_CONFIDENCE_THRESHOLD = 0.99
ALLOWED_CHART_TYPES = ['time_series', 'distribution', 'scatter', 'heatmap']

class StatisticalSummarySchema(BaseModel):
    """Enhanced schema for statistical analysis summary data with comprehensive validation."""
    
    basic_stats: Dict[str, Dict[str, Union[float, Dict]]] = Field(
        description="Basic statistical measures for each metric",
        default_factory=dict
    )
    correlations: Optional[Dict[str, Dict[str, float]]] = Field(
        description="Correlation analysis results",
        default=None
    )
    time_series_metrics: Optional[Dict[str, Dict[str, Union[str, int]]]] = Field(
        description="Time-based analysis metrics",
        default=None
    )
    computed_at: datetime = Field(
        description="Timestamp of statistical computation"
    )

    @validator('basic_stats')
    def validate_basic_stats(cls, value: Dict) -> Dict:
        """Validates basic statistical metrics with enhanced error handling."""
        if not value:
            raise ValueError("Basic statistics cannot be empty")

        required_metrics = {'mean', 'median', 'std_dev', 'quartiles', 'range'}
        
        for metric, stats in value.items():
            missing_metrics = required_metrics - set(stats.keys())
            if missing_metrics:
                raise ValueError(f"Missing required statistics for {metric}: {missing_metrics}")
            
            # Validate numeric values
            for stat_name, stat_value in stats.items():
                if stat_name != 'quartiles' and not isinstance(stat_value, (int, float)):
                    raise ValueError(f"Invalid value type for {metric}.{stat_name}")
                
            # Validate quartiles structure
            if 'quartiles' in stats:
                required_quartiles = {'q1', 'q2', 'q3'}
                if not all(q in stats['quartiles'] for q in required_quartiles):
                    raise ValueError(f"Missing required quartiles for {metric}")

        return value

class PatternDetectionSchema(BaseModel):
    """Enhanced schema for pattern detection results with confidence scoring."""
    
    patterns: List[Dict[str, Union[str, float, Dict]]] = Field(
        description="Detected patterns with metadata",
        default_factory=list
    )
    confidence_threshold: float = Field(
        description="Minimum confidence threshold for pattern detection",
        ge=MIN_CONFIDENCE_THRESHOLD,
        le=MAX_CONFIDENCE_THRESHOLD
    )
    detected_at: datetime = Field(
        description="Timestamp of pattern detection"
    )

    @validator('patterns')
    def validate_patterns(cls, patterns: List) -> List:
        """Validates detected patterns with confidence scoring."""
        if not isinstance(patterns, list):
            raise ValueError("Patterns must be a list")

        valid_pattern_types = {'trend', 'seasonality', 'correlation'}
        
        for pattern in patterns:
            if 'type' not in pattern:
                raise ValueError("Pattern missing required 'type' field")
                
            if pattern['type'] not in valid_pattern_types:
                raise ValueError(f"Invalid pattern type: {pattern['type']}")
                
            if 'confidence' not in pattern:
                raise ValueError("Pattern missing required 'confidence' field")
                
            if not MIN_CONFIDENCE_THRESHOLD <= pattern['confidence'] <= MAX_CONFIDENCE_THRESHOLD:
                raise ValueError(f"Invalid confidence score: {pattern['confidence']}")
                
            # Validate type-specific requirements
            if pattern['type'] == 'correlation':
                if 'metrics' not in pattern or len(pattern['metrics']) != 2:
                    raise ValueError("Correlation pattern must specify exactly two metrics")
                    
            elif pattern['type'] in {'trend', 'seasonality'}:
                if 'metric' not in pattern:
                    raise ValueError(f"{pattern['type']} pattern must specify a metric")

        return patterns

class VisualizationConfigSchema(BaseModel):
    """Enhanced schema for interactive data visualization configurations."""
    
    chart_type: str = Field(
        description="Type of visualization chart",
        regex=f"^({'|'.join(ALLOWED_CHART_TYPES)})$"
    )
    config: Dict[str, Union[str, bool, Dict]] = Field(
        description="Chart configuration options",
        default_factory=dict
    )
    data: Dict[str, Union[List, Dict]] = Field(
        description="Data for visualization",
        default_factory=dict
    )
    layout: Dict[str, Union[str, Dict]] = Field(
        description="Chart layout configuration",
        default_factory=dict
    )

    @validator('config')
    def validate_chart_config(cls, config: Dict, values: Dict) -> Dict:
        """Validates chart configuration with interactive features."""
        if not config:
            raise ValueError("Chart configuration cannot be empty")

        chart_type = values.get('chart_type')
        if not chart_type:
            raise ValueError("Chart type is required")

        required_configs = {
            'time_series': {'x_axis', 'y_axis', 'title'},
            'distribution': {'title', 'show_quartiles'},
            'scatter': {'x_axis', 'y_axis', 'title'},
            'heatmap': {'title', 'colorscale'}
        }

        missing_configs = required_configs[chart_type] - set(config.keys())
        if missing_configs:
            raise ValueError(f"Missing required configurations for {chart_type}: {missing_configs}")

        return config

class AnalysisRequestSchema(BaseModel):
    """Enhanced schema for analysis request validation with protocol compliance."""
    
    protocol_id: UUID = Field(
        description="UUID of the protocol to analyze"
    )
    data_points: List[Dict[str, Union[str, float, datetime]]] = Field(
        description="Data points to analyze",
        min_items=1
    )
    confidence_threshold: float = Field(
        description="Confidence threshold for analysis",
        ge=MIN_CONFIDENCE_THRESHOLD,
        le=MAX_CONFIDENCE_THRESHOLD,
        default=0.8
    )
    analysis_options: Dict[str, Union[bool, Dict]] = Field(
        description="Analysis configuration options",
        default_factory=dict
    )

    @validator('analysis_options')
    def validate_analysis_options(cls, options: Dict) -> Dict:
        """Validates analysis configuration with protocol compliance."""
        if not options:
            return {
                'compute_statistics': True,
                'detect_patterns': True,
                'generate_visualizations': True
            }

        valid_options = {
            'compute_statistics', 'detect_patterns', 'generate_visualizations',
            'statistical_tests', 'visualization_preferences'
        }

        invalid_options = set(options.keys()) - valid_options
        if invalid_options:
            raise ValueError(f"Invalid analysis options: {invalid_options}")

        # Validate statistical tests if specified
        if 'statistical_tests' in options:
            valid_tests = {'t_test', 'chi_square', 'anova', 'correlation'}
            invalid_tests = set(options['statistical_tests']) - valid_tests
            if invalid_tests:
                raise ValueError(f"Invalid statistical tests: {invalid_tests}")

        return options