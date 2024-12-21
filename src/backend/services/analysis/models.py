"""
Analysis models for the Medical Research Platform.

This module defines models for storing and managing protocol analysis results,
including statistical summaries, pattern detection, and data visualizations.
Implements comprehensive data analysis capabilities with validation.

Version: 1.0.0
"""

from django.db import models  # version 4.2
from django.utils import timezone  # version 4.2
from django.utils.encoding import python_2_unicode_compatible
import numpy as np  # version 1.24
import pandas as pd  # version 2.0
from scipy import stats  # version 1.11
import uuid
import logging

from services.protocol.models import Protocol
from services.data.models import DataPoint
from core.utils import format_datetime
from core.exceptions import ValidationException

# Configure logger
logger = logging.getLogger(__name__)

# Analysis status choices
ANALYSIS_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('archived', 'Archived')
)

# Pattern confidence levels
CONFIDENCE_LEVELS = {
    'high': 0.95,
    'medium': 0.80,
    'low': 0.60
}

@python_2_unicode_compatible
class AnalysisResult(models.Model):
    """
    Core model for storing protocol analysis results with enhanced statistical processing.
    Implements comprehensive analysis capabilities including statistical summaries,
    pattern detection, and data visualization configurations.
    """
    
    # Identity and relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.PROTECT,
        related_name='analysis_results'
    )
    
    # Analysis data
    statistical_summary = models.JSONField(default=dict)
    patterns_detected = models.JSONField(default=list)
    visualizations = models.JSONField(default=list)
    
    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=ANALYSIS_STATUS_CHOICES,
        default='pending'
    )
    analysis_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['analysis_date']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"Analysis - {self.protocol.title} - {self.analysis_date}"

    def compute_statistics(self, data_points):
        """
        Enhanced computation of statistical summary with validation and correlation analysis.
        
        Args:
            data_points: List of DataPoint instances to analyze
            
        Returns:
            dict: Comprehensive statistical summary
            
        Raises:
            ValidationException: If data validation fails
        """
        try:
            if not data_points:
                raise ValidationException("No data points provided for analysis")

            # Convert data points to DataFrame
            df = pd.DataFrame([dp.data for dp in data_points])
            
            # Basic statistical measures
            stats_summary = {
                'sample_size': len(df),
                'metrics': {}
            }
            
            # Calculate statistics for each numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                col_stats = {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std_dev': float(df[col].std()),
                    'quartiles': {
                        'q1': float(df[col].quantile(0.25)),
                        'q2': float(df[col].quantile(0.50)),
                        'q3': float(df[col].quantile(0.75))
                    },
                    'range': {
                        'min': float(df[col].min()),
                        'max': float(df[col].max())
                    }
                }
                
                # Add confidence intervals
                ci = stats.t.interval(
                    alpha=0.95,
                    df=len(df[col])-1,
                    loc=df[col].mean(),
                    scale=stats.sem(df[col])
                )
                col_stats['confidence_interval_95'] = {
                    'lower': float(ci[0]),
                    'upper': float(ci[1])
                }
                
                stats_summary['metrics'][col] = col_stats
            
            # Correlation analysis
            if len(numeric_cols) > 1:
                correlations = {
                    'pearson': df[numeric_cols].corr(method='pearson').to_dict(),
                    'spearman': df[numeric_cols].corr(method='spearman').to_dict()
                }
                stats_summary['correlations'] = correlations
            
            # Time series metrics if temporal data exists
            if 'recorded_at' in df.columns:
                df['recorded_at'] = pd.to_datetime(df['recorded_at'])
                time_metrics = {
                    'start_date': df['recorded_at'].min().isoformat(),
                    'end_date': df['recorded_at'].max().isoformat(),
                    'duration_days': (df['recorded_at'].max() - df['recorded_at'].min()).days
                }
                stats_summary['time_metrics'] = time_metrics
            
            return stats_summary
            
        except Exception as e:
            logger.error(f"Error computing statistics: {str(e)}")
            raise ValidationException(f"Statistical computation failed: {str(e)}")

    def detect_patterns(self, data_points, confidence_threshold=CONFIDENCE_LEVELS['medium']):
        """
        Advanced pattern detection with confidence scoring.
        
        Args:
            data_points: List of DataPoint instances
            confidence_threshold: Minimum confidence level for pattern detection
            
        Returns:
            list: Detected patterns with confidence scores
        """
        try:
            if not data_points:
                return []

            patterns = []
            df = pd.DataFrame([dp.data for dp in data_points])
            
            # Time series pattern detection
            if 'recorded_at' in df.columns:
                df['recorded_at'] = pd.to_datetime(df['recorded_at'])
                df = df.sort_values('recorded_at')
                
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    # Trend analysis
                    trend = np.polyfit(range(len(df)), df[col], 1)
                    trend_confidence = abs(np.corrcoef(range(len(df)), df[col])[0, 1])
                    
                    if trend_confidence >= confidence_threshold:
                        patterns.append({
                            'type': 'trend',
                            'metric': col,
                            'direction': 'increasing' if trend[0] > 0 else 'decreasing',
                            'confidence': float(trend_confidence),
                            'details': {
                                'slope': float(trend[0]),
                                'intercept': float(trend[1])
                            }
                        })
                    
                    # Seasonality detection using FFT
                    if len(df) >= 4:  # Minimum points for seasonality
                        fft = np.fft.fft(df[col])
                        frequencies = np.fft.fftfreq(len(df))
                        magnitude = np.abs(fft)
                        peak_freq = frequencies[np.argmax(magnitude[1:])]
                        
                        if peak_freq > 0:
                            patterns.append({
                                'type': 'seasonality',
                                'metric': col,
                                'confidence': float(max(magnitude[1:]) / sum(magnitude[1:])),
                                'details': {
                                    'period_days': float(1 / peak_freq)
                                }
                            })
            
            # Correlation patterns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                for i in range(len(numeric_cols)):
                    for j in range(i + 1, len(numeric_cols)):
                        correlation = corr_matrix.iloc[i, j]
                        if abs(correlation) >= confidence_threshold:
                            patterns.append({
                                'type': 'correlation',
                                'metrics': [numeric_cols[i], numeric_cols[j]],
                                'correlation': float(correlation),
                                'confidence': float(abs(correlation)),
                                'direction': 'positive' if correlation > 0 else 'negative'
                            })
            
            return [p for p in patterns if p['confidence'] >= confidence_threshold]
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {str(e)}")
            raise ValidationException(f"Pattern detection failed: {str(e)}")

    def generate_visualizations(self, statistical_summary, patterns):
        """
        Creates comprehensive visualization configurations.
        
        Args:
            statistical_summary: Statistical analysis results
            patterns: Detected patterns
            
        Returns:
            list: Visualization configurations
        """
        try:
            visualizations = []
            
            # Time series visualizations
            if 'time_metrics' in statistical_summary:
                for metric, stats in statistical_summary['metrics'].items():
                    visualizations.append({
                        'type': 'time_series',
                        'metric': metric,
                        'config': {
                            'title': f'{metric} Over Time',
                            'x_axis': {'label': 'Date', 'type': 'datetime'},
                            'y_axis': {'label': metric, 'type': 'numeric'},
                            'include_trend': True,
                            'confidence_interval': True
                        }
                    })
            
            # Distribution plots
            for metric, stats in statistical_summary['metrics'].items():
                visualizations.append({
                    'type': 'distribution',
                    'metric': metric,
                    'config': {
                        'title': f'{metric} Distribution',
                        'show_quartiles': True,
                        'include_stats': True,
                        'stats_summary': stats
                    }
                })
            
            # Correlation heatmap
            if 'correlations' in statistical_summary:
                visualizations.append({
                    'type': 'heatmap',
                    'data': statistical_summary['correlations']['pearson'],
                    'config': {
                        'title': 'Correlation Heatmap',
                        'colorscale': 'RdBu',
                        'symmetric': True
                    }
                })
            
            # Pattern visualizations
            for pattern in patterns:
                if pattern['type'] == 'trend':
                    visualizations.append({
                        'type': 'trend_overlay',
                        'metric': pattern['metric'],
                        'config': {
                            'direction': pattern['direction'],
                            'confidence': pattern['confidence'],
                            'trend_line': True
                        }
                    })
                elif pattern['type'] == 'correlation':
                    visualizations.append({
                        'type': 'scatter',
                        'metrics': pattern['metrics'],
                        'config': {
                            'title': f"Correlation: {' vs '.join(pattern['metrics'])}",
                            'trend_line': True,
                            'correlation_stats': {
                                'value': pattern['correlation'],
                                'confidence': pattern['confidence']
                            }
                        }
                    })
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
            raise ValidationException(f"Visualization generation failed: {str(e)}")