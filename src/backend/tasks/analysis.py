"""
Celery tasks for asynchronous protocol data analysis.
Implements comprehensive data analysis, pattern detection, visualization generation,
and enhanced safety monitoring with error handling and performance optimizations.

Version: 1.0.0
"""

# Standard library imports
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

# Third-party imports
from celery import Task, shared_task  # version 5.3
import numpy as np  # version 1.24
import pandas as pd  # version 2.0
from scipy import stats  # version 1.11

# Internal imports
from services.analysis.models import AnalysisResult
from services.data.models import DataPoint
from services.protocol.models import Protocol
from core.exceptions import ValidationException

# Configure logger
logger = logging.getLogger(__name__)

class AnalysisTask(Task):
    """Base task class with enhanced error handling and retries."""
    
    max_retries = 3
    retry_backoff = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Enhanced failure handling with detailed logging."""
        logger.error(
            f"Analysis task failed: {task_id}",
            extra={
                "exception": str(exc),
                "args": args,
                "kwargs": kwargs,
                "traceback": einfo
            }
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

@shared_task(bind=True, base=AnalysisTask)
def analyze_protocol_data(self, protocol_id: str) -> str:
    """
    Enhanced Celery task for comprehensive protocol data analysis.
    
    Args:
        protocol_id: UUID of the protocol to analyze
        
    Returns:
        UUID of the created AnalysisResult
        
    Raises:
        ValidationException: If validation fails
    """
    try:
        logger.info(f"Starting protocol analysis for: {protocol_id}")
        
        # Retrieve protocol and validate
        protocol = Protocol.objects.get(id=protocol_id)
        if not protocol:
            raise ValidationException(f"Protocol not found: {protocol_id}")
            
        # Retrieve data points with optimized query
        data_points = DataPoint.objects.filter(
            protocol_id=protocol_id,
            status='validated'
        ).select_related('user').order_by('recorded_at')
        
        if not data_points:
            raise ValidationException("No validated data points found for analysis")
            
        # Create analysis result instance
        analysis_result = AnalysisResult.objects.create(
            protocol=protocol,
            status='processing'
        )
        
        try:
            # Compute statistical summary
            stats_summary = analysis_result.compute_statistics(data_points)
            analysis_result.statistical_summary = stats_summary
            
            # Detect patterns with enhanced algorithm
            patterns = analysis_result.detect_patterns(
                data_points,
                confidence_threshold=0.80
            )
            analysis_result.patterns_detected = patterns
            
            # Generate visualizations
            visualizations = analysis_result.generate_visualizations(
                stats_summary,
                patterns
            )
            analysis_result.visualizations = visualizations
            
            # Update status and save
            analysis_result.status = 'completed'
            analysis_result.save()
            
            logger.info(f"Analysis completed for protocol: {protocol_id}")
            return str(analysis_result.id)
            
        except Exception as e:
            analysis_result.status = 'failed'
            analysis_result.save()
            raise e
            
    except Exception as e:
        logger.error(f"Analysis failed for protocol {protocol_id}: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, base=AnalysisTask)
def update_time_series_metrics(self, protocol_id: str) -> Dict[str, Any]:
    """
    Enhanced task for real-time time series analysis with trend detection.
    
    Args:
        protocol_id: UUID of the protocol to analyze
        
    Returns:
        Dictionary containing updated metrics and trends
    """
    try:
        logger.info(f"Updating time series metrics for: {protocol_id}")
        
        # Retrieve recent data points
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data_points = DataPoint.objects.filter(
            protocol_id=protocol_id,
            status='validated',
            recorded_at__range=(start_date, end_date)
        ).order_by('recorded_at')
        
        if not data_points:
            return {"status": "no_data"}
            
        # Convert to DataFrame for analysis
        df = pd.DataFrame([dp.data for dp in data_points])
        df['recorded_at'] = pd.to_datetime([dp.recorded_at for dp in data_points])
        df.set_index('recorded_at', inplace=True)
        
        metrics = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Decompose time series
            try:
                decomposition = stats.seasonal_decompose(
                    df[col],
                    period=7,  # Weekly seasonality
                    extrapolate_trend='freq'
                )
                
                # Calculate metrics
                metrics[col] = {
                    'trend': decomposition.trend.iloc[-1],
                    'seasonal': decomposition.seasonal.iloc[-1],
                    'change_rate': float(np.polyfit(range(len(df)), df[col], 1)[0]),
                    'volatility': float(df[col].std()),
                    'last_value': float(df[col].iloc[-1]),
                    'mean': float(df[col].mean())
                }
                
                # Add statistical significance
                t_stat, p_value = stats.ttest_ind(
                    df[col].iloc[:len(df)//2],
                    df[col].iloc[len(df)//2:]
                )
                metrics[col]['significance'] = {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value)
                }
                
            except Exception as e:
                logger.warning(f"Error analyzing {col}: {str(e)}")
                continue
        
        logger.info(f"Time series metrics updated for: {protocol_id}")
        return metrics
        
    except Exception as e:
        logger.error(f"Time series analysis failed: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, base=AnalysisTask)
def detect_safety_violations(self, protocol_id: str) -> List[Dict[str, Any]]:
    """
    Enhanced task for comprehensive safety violation detection with severity scoring.
    
    Args:
        protocol_id: UUID of the protocol to check
        
    Returns:
        List of detected violations with severity scores
    """
    try:
        logger.info(f"Checking safety violations for: {protocol_id}")
        
        # Retrieve protocol and recent data
        protocol = Protocol.objects.get(id=protocol_id)
        recent_data = DataPoint.objects.filter(
            protocol_id=protocol_id,
            status='validated'
        ).order_by('-recorded_at')[:100]
        
        violations = []
        
        for data_point in recent_data:
            # Check for safety violations
            violation_found, message, details = protocol.check_safety_violation(
                data_point.data
            )
            
            if violation_found:
                # Calculate violation severity
                severity_score = _calculate_severity_score(details)
                
                violation = {
                    'data_point_id': str(data_point.id),
                    'recorded_at': data_point.recorded_at.isoformat(),
                    'message': message,
                    'details': details,
                    'severity_score': severity_score,
                    'requires_action': severity_score >= 0.7
                }
                violations.append(violation)
                
                # Log high-severity violations
                if severity_score >= 0.7:
                    logger.warning(
                        f"High-severity safety violation detected",
                        extra={
                            'protocol_id': protocol_id,
                            'violation': violation
                        }
                    )
        
        return violations
        
    except Exception as e:
        logger.error(f"Safety violation detection failed: {str(e)}")
        raise self.retry(exc=e)

def _calculate_severity_score(violation_details: Dict[str, Any]) -> float:
    """
    Calculates severity score for safety violations.
    
    Args:
        violation_details: Dictionary containing violation details
        
    Returns:
        Severity score between 0 and 1
    """
    try:
        severity_score = 0.0
        
        for param, details in violation_details.items():
            if details['type'] == 'above_maximum':
                # Calculate how far above maximum
                excess = (details['value'] - details['threshold']) / details['threshold']
                severity_score = max(severity_score, min(1.0, excess))
            elif details['type'] == 'below_minimum':
                # Calculate how far below minimum
                deficit = (details['threshold'] - details['value']) / details['threshold']
                severity_score = max(severity_score, min(1.0, deficit))
        
        return round(severity_score, 3)
        
    except Exception as e:
        logger.error(f"Error calculating severity score: {str(e)}")
        return 1.0  # Return maximum severity on error