"""
Protocol service schema definitions and validation rules.
Implements comprehensive JSON schemas for protocol data structures with enhanced validation.

Version: 1.0.0
"""

from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError  # version 4.17.0
from core.validators import validate_protocol_requirements
from core.exceptions import ValidationException

# Regular expressions for field validation
VALIDATION_PATTERNS = {
    'title': r'^[a-zA-Z0-9\s\-_]{3,100}$',
    'measurement_unit': r'^[a-zA-Z/%]+$',
    'marker_name': r'^[a-zA-Z0-9\s\-_]{2,50}$',
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
}

# Base schema for measurement ranges
MEASUREMENT_RANGE_SCHEMA = {
    "type": "object",
    "required": ["min", "max", "unit"],
    "properties": {
        "min": {"type": "number"},
        "max": {"type": "number"},
        "unit": {"type": "string", "pattern": VALIDATION_PATTERNS['measurement_unit']},
        "alert_threshold": {"type": "number"},
        "critical_threshold": {"type": "number"}
    },
    "additionalProperties": False
}

# Protocol requirements schema
PROTOCOL_REQUIREMENTS_SCHEMA = {
    "type": "object",
    "required": ["title", "duration", "data_collection_frequency", "measurements"],
    "properties": {
        "title": {
            "type": "string",
            "pattern": VALIDATION_PATTERNS['title'],
            "minLength": 3,
            "maxLength": 100
        },
        "duration": {
            "type": "integer",
            "minimum": 1,
            "maximum": 52,
            "description": "Duration in weeks"
        },
        "data_collection_frequency": {
            "type": "string",
            "enum": ["daily", "weekly", "monthly"]
        },
        "measurements": {
            "type": "object",
            "minProperties": 1,
            "patternProperties": {
                VALIDATION_PATTERNS['marker_name']: MEASUREMENT_RANGE_SCHEMA
            }
        },
        "description": {
            "type": "string",
            "maxLength": 2000
        },
        "prerequisites": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 200
            }
        },
        "exclusion_criteria": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 200
            }
        }
    },
    "additionalProperties": False
}

# Safety parameters schema
SAFETY_PARAMETERS_SCHEMA = {
    "type": "object",
    "required": ["markers", "intervention_triggers"],
    "properties": {
        "markers": {
            "type": "object",
            "minProperties": 1,
            "patternProperties": {
                VALIDATION_PATTERNS['marker_name']: {
                    "type": "object",
                    "required": ["critical_ranges", "alert_ranges"],
                    "properties": {
                        "critical_ranges": MEASUREMENT_RANGE_SCHEMA,
                        "alert_ranges": MEASUREMENT_RANGE_SCHEMA,
                        "intervention_required": {"type": "boolean"}
                    }
                }
            }
        },
        "intervention_triggers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["condition", "action"],
                "properties": {
                    "condition": {"type": "string"},
                    "action": {"type": "string"},
                    "notification_required": {"type": "boolean"},
                    "immediate_action": {"type": "boolean"}
                }
            }
        }
    },
    "additionalProperties": False
}

# Blood work data schema
BLOOD_WORK_SCHEMA = {
    "type": "object",
    "required": ["test_date", "lab_name", "lab_certification", "markers"],
    "properties": {
        "test_date": {"type": "string", "format": "date-time"},
        "lab_name": {"type": "string", "maxLength": 100},
        "lab_certification": {"type": "string", "pattern": r'^[A-Z0-9]{4,10}$'},
        "markers": {
            "type": "object",
            "minProperties": 1,
            "patternProperties": {
                VALIDATION_PATTERNS['marker_name']: {
                    "type": "object",
                    "required": ["value", "unit"],
                    "properties": {
                        "value": {"type": "number"},
                        "unit": {"type": "string", "pattern": VALIDATION_PATTERNS['measurement_unit']},
                        "reference_range": MEASUREMENT_RANGE_SCHEMA
                    }
                }
            }
        }
    },
    "additionalProperties": False
}

# Biometric data schema
BIOMETRIC_SCHEMA = {
    "type": "object",
    "required": ["timestamp", "measurements"],
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "measurements": {
            "type": "object",
            "minProperties": 1,
            "patternProperties": {
                VALIDATION_PATTERNS['marker_name']: {
                    "type": "object",
                    "required": ["value", "unit"],
                    "properties": {
                        "value": {"type": "number", "minimum": 0},
                        "unit": {"type": "string", "pattern": VALIDATION_PATTERNS['measurement_unit']}
                    }
                }
            }
        }
    },
    "additionalProperties": False
}

# Check-in data schema
CHECK_IN_SCHEMA = {
    "type": "object",
    "required": ["timestamp", "energy_level", "sleep_quality", "notes"],
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "energy_level": {"type": "integer", "minimum": 1, "maximum": 5},
        "sleep_quality": {"type": "integer", "minimum": 1, "maximum": 5},
        "notes": {"type": "string", "maxLength": 1000},
        "side_effects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description", "severity"],
                "properties": {
                    "description": {"type": "string", "maxLength": 200},
                    "severity": {"type": "integer", "minimum": 1, "maximum": 5}
                }
            }
        }
    },
    "additionalProperties": False
}

def validate_requirements_schema(requirements: Dict[str, Any]) -> bool:
    """
    Validates protocol requirements with enhanced type checking and cross-field validation.
    
    Args:
        requirements: Dictionary containing protocol requirements
        
    Returns:
        True if valid
        
    Raises:
        ValidationException: If validation fails with detailed error context
    """
    try:
        # Validate against JSON schema
        validate(instance=requirements, schema=PROTOCOL_REQUIREMENTS_SCHEMA)
        
        # Perform additional cross-field validations using core validator
        validate_protocol_requirements(requirements)
        
        return True
        
    except ValidationError as e:
        raise ValidationException(
            message="Protocol requirements validation failed",
            details={
                "fields": {
                    "schema_error": e.message,
                    "schema_path": " -> ".join([str(p) for p in e.path])
                }
            }
        )

def validate_safety_parameters(safety_params: Dict[str, Any]) -> bool:
    """
    Validates safety parameters with strict threshold checking.
    
    Args:
        safety_params: Dictionary containing safety parameters
        
    Returns:
        True if valid
        
    Raises:
        ValidationException: If validation fails with threshold violation details
    """
    try:
        # Validate against JSON schema
        validate(instance=safety_params, schema=SAFETY_PARAMETERS_SCHEMA)
        
        # Additional validation for threshold relationships
        for marker, params in safety_params.get('markers', {}).items():
            critical = params.get('critical_ranges', {})
            alert = params.get('alert_ranges', {})
            
            # Validate that alert ranges are within critical ranges
            if (critical.get('min') > alert.get('min') or 
                critical.get('max') < alert.get('max')):
                raise ValidationException(
                    message=f"Invalid threshold ranges for marker: {marker}",
                    details={
                        "fields": {
                            marker: "Alert ranges must be within critical ranges"
                        }
                    }
                )
        
        return True
        
    except ValidationError as e:
        raise ValidationException(
            message="Safety parameters validation failed",
            details={
                "fields": {
                    "schema_error": e.message,
                    "schema_path": " -> ".join([str(p) for p in e.path])
                }
            }
        )