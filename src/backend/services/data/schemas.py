"""
Pydantic schemas for validating data collection in the Medical Research Platform.
Implements comprehensive validation for blood work, biometrics, and participant check-ins.

Version: 1.0.0
"""

from datetime import datetime
from uuid import UUID
import html
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, validator  # v1.10.0

from core.validators import (
    validate_blood_work_data,
    validate_biometric_data,
    validate_check_in_data
)
from core.exceptions import ValidationException

# Constants for validation
ALLOWED_DATA_TYPES = ['blood_work', 'check_in', 'biometric']
MAX_TEXT_LENGTH = 1000
RATING_SCALE_RANGE = (1, 5)
REQUIRED_BLOOD_MARKERS = ['vitamin_d', 'crp', 'hdl', 'ldl', 'triglycerides']

class DataPointSchema(BaseModel):
    """
    Base schema for all data point types with enhanced validation and security features.
    """
    id: UUID = Field(..., description="Unique identifier for the data point")
    protocol_id: UUID = Field(..., description="Associated protocol identifier")
    type: str = Field(..., description="Type of data point")
    data: Dict[str, Any] = Field(..., description="Data point content")
    recorded_at: datetime = Field(default_factory=datetime.now, description="Recording timestamp")

    class Config:
        title = "Data Point Schema"
        extra = "forbid"
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

    @validator('type')
    def validate_type(cls, value: str) -> str:
        """
        Validates data point type with security checks.
        
        Args:
            value: Data point type string
            
        Returns:
            Validated type string
            
        Raises:
            ValidationError: If type is invalid
        """
        if not value or value.strip() not in ALLOWED_DATA_TYPES:
            raise ValueError(f"Invalid data type. Must be one of: {', '.join(ALLOWED_DATA_TYPES)}")
        return value.strip().lower()

    @validator('data')
    def validate_data(cls, value: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive data validation with type-specific checks.
        
        Args:
            value: Data dictionary to validate
            values: Other field values
            
        Returns:
            Validated data dictionary
            
        Raises:
            ValidationError: If data validation fails
        """
        try:
            data_type = values.get('type')
            if data_type == 'blood_work':
                validate_blood_work_data(value)
            elif data_type == 'biometric':
                validate_biometric_data(value)
            elif data_type == 'check_in':
                validate_check_in_data(value)
            return value
        except ValidationException as e:
            raise ValueError(str(e))

class BloodWorkSchema(BaseModel):
    """
    Enhanced schema for blood test results with comprehensive validation.
    """
    markers: Dict[str, float] = Field(..., description="Blood test markers and values")
    test_date: datetime = Field(..., description="Date of blood test")
    lab_name: str = Field(..., min_length=2, max_length=100, description="Testing laboratory name")
    file_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash of lab report")
    reference_ranges: Dict[str, Dict[str, float]] = Field(..., description="Reference ranges for markers")

    class Config:
        title = "Blood Work Schema"
        extra = "forbid"
        validate_assignment = True

    @validator('markers')
    def validate_markers(cls, value: Dict[str, float]) -> Dict[str, float]:
        """
        Comprehensive validation of blood work markers with range checks.
        
        Args:
            value: Dictionary of blood markers and values
            
        Returns:
            Validated markers dictionary
            
        Raises:
            ValidationError: If marker validation fails
        """
        # Validate required markers
        missing_markers = [marker for marker in REQUIRED_BLOOD_MARKERS if marker not in value]
        if missing_markers:
            raise ValueError(f"Missing required markers: {', '.join(missing_markers)}")

        # Validate marker values
        for marker, marker_value in value.items():
            if not isinstance(marker_value, (int, float)):
                raise ValueError(f"Invalid value for marker {marker}: must be numeric")
            if marker_value < 0:
                raise ValueError(f"Invalid value for marker {marker}: cannot be negative")

        return value

class WeeklyCheckInSchema(BaseModel):
    """
    Enhanced schema for weekly check-ins with text sanitization.
    """
    energy_level: int = Field(..., ge=1, le=5, description="Energy level rating (1-5)")
    sleep_quality: int = Field(..., ge=1, le=5, description="Sleep quality rating (1-5)")
    side_effects: str = Field("", max_length=MAX_TEXT_LENGTH, description="Reported side effects")
    additional_notes: Dict[str, str] = Field(default_factory=dict, description="Additional observations")
    symptoms: List[str] = Field(default_factory=list, description="Reported symptoms")

    class Config:
        title = "Weekly Check-in Schema"
        extra = "forbid"
        validate_assignment = True

    @validator('energy_level', 'sleep_quality')
    def validate_ratings(cls, value: int) -> int:
        """
        Enhanced validation of rating scale values.
        
        Args:
            value: Rating value to validate
            
        Returns:
            Validated rating value
            
        Raises:
            ValidationError: If rating is invalid
        """
        if not RATING_SCALE_RANGE[0] <= value <= RATING_SCALE_RANGE[1]:
            raise ValueError(f"Rating must be between {RATING_SCALE_RANGE[0]} and {RATING_SCALE_RANGE[1]}")
        return value

    @validator('side_effects', 'additional_notes')
    def sanitize_text_fields(cls, value: Any) -> Any:
        """
        Security-focused text field sanitization.
        
        Args:
            value: Text value to sanitize
            
        Returns:
            Sanitized text value
            
        Raises:
            ValidationError: If text validation fails
        """
        if isinstance(value, str):
            # Sanitize and validate string
            sanitized = html.escape(value.strip())
            if len(sanitized) > MAX_TEXT_LENGTH:
                raise ValueError(f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters")
            return sanitized
        elif isinstance(value, dict):
            # Sanitize dictionary values
            return {
                k: html.escape(str(v).strip()) if isinstance(v, str) else v
                for k, v in value.items()
            }
        return value