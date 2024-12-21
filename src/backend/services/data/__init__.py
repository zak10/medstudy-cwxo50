"""
Data service initialization module for the Medical Research Platform.

This module exposes core models and views for protocol data collection, including blood work results,
weekly check-ins, and other participant data submissions. It provides a centralized interface for
structured data capture and storage with enhanced security and validation features.

Version: 1.0.0
"""

# Import core models
from .models import (
    DataPoint,
    BloodWorkResult,
    WeeklyCheckIn,
)

# Import API views
from .views import (
    DataPointView,
)

# Import validation schemas
from .schemas import (
    DataPointSchema,
    BloodWorkSchema,
    WeeklyCheckInSchema,
)

# Define package version
__version__ = '1.0.0'

# Define public API
__all__ = [
    # Models
    'DataPoint',
    'BloodWorkResult',
    'WeeklyCheckIn',
    
    # Views
    'DataPointView',
    
    # Schemas
    'DataPointSchema',
    'BloodWorkSchema', 
    'WeeklyCheckInSchema',
]

# Module level docstring
__doc__ = """
Medical Research Platform Data Service

This service provides core functionality for structured data collection and storage,
including:

- Blood work results with lab verification
- Weekly participant check-ins with subjective measures
- Biometric measurements and tracking
- Protocol-specific data validation
- Secure data storage with encryption
- Comprehensive audit logging

The service implements strict validation rules and security controls to ensure data
quality and participant privacy.

For detailed API documentation, see the schema definitions in schemas.py.
"""