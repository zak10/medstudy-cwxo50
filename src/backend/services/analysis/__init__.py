"""
Analysis service initialization module for the Medical Research Platform.

This module exposes core analysis functionality including statistical analysis,
pattern detection, and data visualization capabilities. It implements comprehensive
data analysis features with validation and security controls.

Version: 1.0.0
"""

# Internal imports - version from models.py
from services.analysis.models import AnalysisResult, SignalDetection

# Module version
__version__ = '1.0.0'

# Define exports
__all__ = [
    'AnalysisResult',
    'SignalDetection'
]

# Validate imports and initialize logging
import logging
logger = logging.getLogger(__name__)

try:
    # Verify core analysis capabilities are available
    required_methods = [
        getattr(AnalysisResult, 'compute_statistics'),
        getattr(AnalysisResult, 'detect_patterns'),
        getattr(AnalysisResult, 'generate_visualizations'),
        getattr(SignalDetection, 'calculate_confidence')
    ]
    logger.info("Analysis service initialized successfully")
    
except AttributeError as e:
    logger.error(f"Failed to initialize analysis service: {str(e)}")
    raise ImportError("Required analysis methods not found")

except Exception as e:
    logger.error(f"Unexpected error initializing analysis service: {str(e)}")
    raise