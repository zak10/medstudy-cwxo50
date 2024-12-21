"""
Core validation utilities for the Medical Research Platform backend.
Provides comprehensive validation functions for data collection and protocol management.

Version: 1.0.0
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.core.exceptions import ValidationError
from core.exceptions import ValidationException

# Constants for validation
ALLOWED_FREQUENCIES = ['daily', 'weekly', 'monthly']
MAX_PROTOCOL_WEEKS = 52
MIN_PROTOCOL_WEEKS = 1
MAX_TEXT_LENGTH = 1000
RATING_SCALE_RANGE = (1, 5)

# Regular expressions for validation
LAB_CERTIFICATION_PATTERN = r'^[A-Z0-9]{4,10}$'
MEASUREMENT_UNIT_PATTERN = r'^[a-zA-Z/%]+$'

def validate_protocol_requirements(requirements: Dict[str, Any]) -> bool:
    """
    Validates protocol requirements schema and data collection specifications.
    
    Args:
        requirements: Dictionary containing protocol requirements
        
    Returns:
        True if valid
        
    Raises:
        ValidationException: If validation fails with detailed error context
    """
    required_fields = ['title', 'duration', 'data_collection_frequency']
    validation_errors = {}

    # Validate required fields presence
    for field in required_fields:
        if field not in requirements:
            validation_errors[field] = f"Missing required field: {field}"

    if validation_errors:
        raise ValidationException("Missing required protocol fields", {"fields": validation_errors})

    # Validate data collection frequency
    if requirements['data_collection_frequency'] not in ALLOWED_FREQUENCIES:
        validation_errors['data_collection_frequency'] = f"Invalid frequency. Must be one of: {', '.join(ALLOWED_FREQUENCIES)}"

    # Validate protocol duration
    try:
        duration_weeks = int(requirements.get('duration', 0))
        if not MIN_PROTOCOL_WEEKS <= duration_weeks <= MAX_PROTOCOL_WEEKS:
            validation_errors['duration'] = f"Duration must be between {MIN_PROTOCOL_WEEKS} and {MAX_PROTOCOL_WEEKS} weeks"
    except ValueError:
        validation_errors['duration'] = "Duration must be a valid integer"

    # Validate measurement units if present
    if 'measurement_units' in requirements:
        for unit in requirements['measurement_units']:
            if not re.match(MEASUREMENT_UNIT_PATTERN, unit):
                validation_errors.setdefault('measurement_units', []).append(f"Invalid unit format: {unit}")

    # Validate safety thresholds
    if 'safety_thresholds' in requirements:
        for marker, threshold in requirements['safety_thresholds'].items():
            if not all(key in threshold for key in ['min', 'max']):
                validation_errors.setdefault('safety_thresholds', {})[marker] = "Missing min/max values"
            elif threshold['min'] >= threshold['max']:
                validation_errors.setdefault('safety_thresholds', {})[marker] = "Min value must be less than max value"

    if validation_errors:
        raise ValidationException("Invalid protocol requirements", {"fields": validation_errors})

    return True

def validate_blood_work_data(blood_work_data: Dict[str, Any]) -> bool:
    """
    Validates blood test results data format and ranges.
    
    Args:
        blood_work_data: Dictionary containing blood work results
        
    Returns:
        True if valid
        
    Raises:
        ValidationException: If validation fails with detailed error context
    """
    validation_errors = {}
    required_fields = ['test_date', 'lab_name', 'lab_certification', 'markers']

    # Validate required fields
    for field in required_fields:
        if field not in blood_work_data:
            validation_errors[field] = f"Missing required field: {field}"

    if validation_errors:
        raise ValidationException("Missing required blood work fields", {"fields": validation_errors})

    # Validate lab certification format
    if not re.match(LAB_CERTIFICATION_PATTERN, blood_work_data.get('lab_certification', '')):
        validation_errors['lab_certification'] = "Invalid lab certification format"

    # Validate test date
    try:
        test_date = datetime.fromisoformat(blood_work_data['test_date'])
        if test_date > datetime.now():
            validation_errors['test_date'] = "Test date cannot be in the future"
        if test_date < (datetime.now() - timedelta(days=30)):
            validation_errors['test_date'] = "Test results must be within the last 30 days"
    except ValueError:
        validation_errors['test_date'] = "Invalid date format"

    # Validate blood markers
    if 'markers' in blood_work_data:
        for marker, value in blood_work_data['markers'].items():
            if not isinstance(value, (int, float)):
                validation_errors.setdefault('markers', {})[marker] = "Marker value must be numeric"
            elif value < 0:
                validation_errors.setdefault('markers', {})[marker] = "Marker value cannot be negative"

    if validation_errors:
        raise ValidationException("Invalid blood work data", {"fields": validation_errors})

    return True

def validate_biometric_data(biometric_data: Dict[str, Any]) -> bool:
    """
    Validates participant biometric measurements.
    
    Args:
        biometric_data: Dictionary containing biometric measurements
        
    Returns:
        True if valid
        
    Raises:
        ValidationException: If validation fails with detailed error context
    """
    validation_errors = {}
    required_fields = ['timestamp', 'measurements']

    # Validate required fields
    for field in required_fields:
        if field not in biometric_data:
            validation_errors[field] = f"Missing required field: {field}"

    if validation_errors:
        raise ValidationException("Missing required biometric fields", {"fields": validation_errors})

    # Validate timestamp
    try:
        measurement_time = datetime.fromisoformat(biometric_data['timestamp'])
        if measurement_time > datetime.now():
            validation_errors['timestamp'] = "Measurement time cannot be in the future"
    except ValueError:
        validation_errors['timestamp'] = "Invalid timestamp format"

    # Validate measurements
    if 'measurements' in biometric_data:
        for measure, data in biometric_data['measurements'].items():
            if not all(key in data for key in ['value', 'unit']):
                validation_errors.setdefault('measurements', {})[measure] = "Missing value or unit"
            elif not re.match(MEASUREMENT_UNIT_PATTERN, data['unit']):
                validation_errors.setdefault('measurements', {})[measure] = "Invalid unit format"
            elif not isinstance(data['value'], (int, float)) or data['value'] < 0:
                validation_errors.setdefault('measurements', {})[measure] = "Invalid measurement value"

    if validation_errors:
        raise ValidationException("Invalid biometric data", {"fields": validation_errors})

    return True

def validate_check_in_data(check_in_data: Dict[str, Any]) -> bool:
    """
    Validates weekly check-in submission data.
    
    Args:
        check_in_data: Dictionary containing check-in data
        
    Returns:
        True if valid
        
    Raises:
        ValidationException: If validation fails with detailed error context
    """
    validation_errors = {}
    required_fields = ['timestamp', 'energy_level', 'sleep_quality', 'notes']

    # Validate required fields
    for field in required_fields:
        if field not in check_in_data:
            validation_errors[field] = f"Missing required field: {field}"

    if validation_errors:
        raise ValidationException("Missing required check-in fields", {"fields": validation_errors})

    # Validate rating scales
    for rating_field in ['energy_level', 'sleep_quality']:
        if rating_field in check_in_data:
            try:
                rating = int(check_in_data[rating_field])
                if not RATING_SCALE_RANGE[0] <= rating <= RATING_SCALE_RANGE[1]:
                    validation_errors[rating_field] = f"Rating must be between {RATING_SCALE_RANGE[0]} and {RATING_SCALE_RANGE[1]}"
            except ValueError:
                validation_errors[rating_field] = "Rating must be a valid integer"

    # Validate text fields
    if 'notes' in check_in_data and len(check_in_data['notes']) > MAX_TEXT_LENGTH:
        validation_errors['notes'] = f"Notes cannot exceed {MAX_TEXT_LENGTH} characters"

    # Validate timestamp
    try:
        check_in_time = datetime.fromisoformat(check_in_data['timestamp'])
        if check_in_time > datetime.now():
            validation_errors['timestamp'] = "Check-in time cannot be in the future"
    except ValueError:
        validation_errors['timestamp'] = "Invalid timestamp format"

    if validation_errors:
        raise ValidationException("Invalid check-in data", {"fields": validation_errors})

    return True

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Validates date range for protocol duration.
    
    Args:
        start_date: Protocol start date
        end_date: Protocol end date
        
    Returns:
        True if valid
        
    Raises:
        ValidationException: If validation fails with detailed error context
    """
    validation_errors = {}

    # Validate date objects
    if not all(isinstance(date, datetime) for date in [start_date, end_date]):
        raise ValidationException("Invalid date format", {"fields": {"dates": "Both dates must be datetime objects"}})

    # Validate start date is not in the past
    if start_date.date() < datetime.now().date():
        validation_errors['start_date'] = "Start date cannot be in the past"

    # Validate end date is after start date
    if end_date <= start_date:
        validation_errors['end_date'] = "End date must be after start date"

    # Validate protocol duration
    duration_weeks = (end_date - start_date).days / 7
    if not MIN_PROTOCOL_WEEKS <= duration_weeks <= MAX_PROTOCOL_WEEKS:
        validation_errors['duration'] = f"Protocol duration must be between {MIN_PROTOCOL_WEEKS} and {MAX_PROTOCOL_WEEKS} weeks"

    if validation_errors:
        raise ValidationException("Invalid date range", {"fields": validation_errors})

    return True