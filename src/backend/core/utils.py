"""
Core utility functions for the Medical Research Platform backend.
Provides reusable helper functions for data processing, formatting, security operations,
and system utilities with comprehensive error handling and logging.

Version: 1.0.0
"""

# Standard library imports - version from Python 3.11.0
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, BinaryIO, Union
import json
import uuid
import hashlib
import logging

# Third-party imports
import bleach  # version 6.0.0

# Internal imports
from core.exceptions import ValidationException

# Configure logger
logger = logging.getLogger(__name__)

# Constants
CHUNK_SIZE = 8192  # 8KB chunks for file processing
MAX_CONTENT_LENGTH = 1000000  # 1MB max content length
DEFAULT_ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'span', 'div', 'a'
]
DEFAULT_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'span': ['class'],
    'div': ['class']
}

def generate_unique_id(prefix: Optional[str] = None) -> str:
    """
    Generates a unique identifier with optional prefix support.
    
    Args:
        prefix: Optional string prefix for the UUID
        
    Returns:
        Formatted UUID string with optional prefix
        
    Raises:
        ValidationException: If prefix contains invalid characters
    """
    try:
        # Generate UUID
        unique_id = str(uuid.uuid4())
        
        # Validate and process prefix if provided
        if prefix:
            if not prefix.isalnum():
                raise ValidationException("Prefix must be alphanumeric")
            unique_id = f"{prefix}-{unique_id}"
            
        logger.debug(f"Generated unique ID: {unique_id}")
        return unique_id
        
    except Exception as e:
        logger.error(f"Error generating unique ID: {str(e)}")
        raise

def format_datetime(
    dt: Optional[datetime],
    format_string: Optional[str] = None
) -> Optional[str]:
    """
    Formats datetime objects to ISO 8601 format with timezone handling.
    
    Args:
        dt: Datetime object to format
        format_string: Optional custom format string
        
    Returns:
        Formatted datetime string or None if input is None
        
    Raises:
        ValidationException: If datetime object is invalid
    """
    try:
        if dt is None:
            return None
            
        if not isinstance(dt, datetime):
            raise ValidationException("Invalid datetime object")
            
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        # Format datetime
        if format_string:
            formatted = dt.strftime(format_string)
        else:
            formatted = dt.isoformat()
            
        logger.debug(f"Formatted datetime: {formatted}")
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting datetime: {str(e)}")
        raise

def sanitize_html(
    content: str,
    allowed_tags: Optional[List[str]] = None,
    allowed_attributes: Optional[Dict[str, List[str]]] = None
) -> str:
    """
    Sanitizes HTML content with security checks and validation.
    
    Args:
        content: HTML content to sanitize
        allowed_tags: List of allowed HTML tags
        allowed_attributes: Dictionary of allowed attributes per tag
        
    Returns:
        Sanitized HTML string
        
    Raises:
        ValidationException: If content is invalid or exceeds length limits
    """
    try:
        # Validate input
        if not isinstance(content, str):
            raise ValidationException("Content must be a string")
            
        if len(content) > MAX_CONTENT_LENGTH:
            raise ValidationException("Content exceeds maximum length")
            
        # Use default or custom allowed elements
        tags = allowed_tags if allowed_tags is not None else DEFAULT_ALLOWED_TAGS
        attributes = allowed_attributes if allowed_attributes is not None else DEFAULT_ALLOWED_ATTRIBUTES
        
        # Sanitize content
        clean_content = bleach.clean(
            content,
            tags=tags,
            attributes=attributes,
            strip=True
        )
        
        logger.debug("HTML content sanitized successfully")
        return clean_content
        
    except Exception as e:
        logger.error(f"Error sanitizing HTML: {str(e)}")
        raise

def hash_file(
    file_obj: BinaryIO,
    chunk_size: int = CHUNK_SIZE
) -> str:
    """
    Generates SHA-256 hash of file with memory-efficient chunk processing.
    
    Args:
        file_obj: File-like object to hash
        chunk_size: Size of chunks to process
        
    Returns:
        Hexadecimal SHA-256 hash string
        
    Raises:
        ValidationException: If file object is invalid
    """
    try:
        if not hasattr(file_obj, 'read'):
            raise ValidationException("Invalid file object")
            
        # Initialize hasher
        sha256_hash = hashlib.sha256()
        
        # Process file in chunks
        for chunk in iter(lambda: file_obj.read(chunk_size), b''):
            sha256_hash.update(chunk)
            
        # Generate hash
        file_hash = sha256_hash.hexdigest()
        
        logger.debug(f"Generated file hash: {file_hash}")
        return file_hash
        
    except Exception as e:
        logger.error(f"Error hashing file: {str(e)}")
        raise
    finally:
        # Ensure file pointer is reset
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)

def parse_json_safely(
    json_str: str,
    schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Safely parses JSON data with validation and error handling.
    
    Args:
        json_str: JSON string to parse
        schema: Optional schema for validation
        
    Returns:
        Parsed and validated JSON data
        
    Raises:
        ValidationException: If JSON is invalid or fails schema validation
    """
    try:
        # Validate input
        if not isinstance(json_str, str):
            raise ValidationException("Input must be a string")
            
        if not json_str.strip():
            raise ValidationException("Empty JSON string")
            
        # Parse JSON
        parsed_data = json.loads(json_str)
        
        # Validate against schema if provided
        if schema is not None:
            _validate_against_schema(parsed_data, schema)
            
        logger.debug("JSON parsed and validated successfully")
        return parsed_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise ValidationException("Invalid JSON format")
    except Exception as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        raise

class DataFormatter:
    """
    Utility class for data formatting operations with validation rules.
    
    Attributes:
        _format_rules: Dictionary of formatting rules
        _validators: Dictionary of validation functions
        _transformers: Dictionary of data transformation functions
    """
    
    def __init__(
        self,
        format_rules: Dict[str, Any],
        validators: Optional[Dict[str, callable]] = None
    ):
        """
        Initialize data formatter with rules and validation.
        
        Args:
            format_rules: Dictionary of formatting rules
            validators: Optional dictionary of validation functions
        """
        self._format_rules = self._validate_rules(format_rules)
        self._validators = validators or {}
        self._transformers = self._setup_transformers()
        
        logger.debug("DataFormatter initialized with rules")
        
    def _validate_rules(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates formatting rules structure.
        
        Args:
            rules: Dictionary of formatting rules
            
        Returns:
            Validated rules dictionary
        """
        if not isinstance(rules, dict):
            raise ValidationException("Format rules must be a dictionary")
        return rules
        
    def _setup_transformers(self) -> Dict[str, callable]:
        """
        Sets up data transformation functions.
        
        Returns:
            Dictionary of transformer functions
        """
        return {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'datetime': lambda x: format_datetime(x),
            'json': lambda x: parse_json_safely(x)
        }
        
    def format_data(
        self,
        data: Dict[str, Any],
        strict: bool = True
    ) -> Dict[str, Any]:
        """
        Formats data according to rules with validation.
        
        Args:
            data: Data to format
            strict: Whether to enforce strict validation
            
        Returns:
            Formatted and validated data
            
        Raises:
            ValidationException: If validation fails
        """
        try:
            if not isinstance(data, dict):
                raise ValidationException("Input must be a dictionary")
                
            formatted_data = {}
            errors = {}
            
            # Process each field according to rules
            for field, rule in self._format_rules.items():
                try:
                    value = data.get(field)
                    
                    # Apply transformation
                    if 'type' in rule and value is not None:
                        transformer = self._transformers.get(rule['type'])
                        if transformer:
                            value = transformer(value)
                            
                    # Apply validation
                    if field in self._validators:
                        self._validators[field](value)
                        
                    formatted_data[field] = value
                    
                except Exception as e:
                    errors[field] = str(e)
                    if strict:
                        raise ValidationException(f"Validation failed for {field}", errors)
                        
            if errors and strict:
                raise ValidationException("Data validation failed", errors)
                
            logger.debug("Data formatted successfully")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error formatting data: {str(e)}")
            raise

def _validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validates data against provided schema.
    
    Args:
        data: Data to validate
        schema: Validation schema
        
    Raises:
        ValidationException: If validation fails
    """
    try:
        # Basic schema validation
        for field, rules in schema.items():
            if field not in data and rules.get('required', False):
                raise ValidationException(f"Missing required field: {field}")
                
            value = data.get(field)
            if value is not None:
                # Type validation
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    raise ValidationException(f"Invalid type for field {field}")
                    
                # Range validation
                if 'min' in rules and value < rules['min']:
                    raise ValidationException(f"Value too small for field {field}")
                if 'max' in rules and value > rules['max']:
                    raise ValidationException(f"Value too large for field {field}")
                    
    except Exception as e:
        logger.error(f"Schema validation error: {str(e)}")
        raise