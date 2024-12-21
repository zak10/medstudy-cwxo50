"""
Core exception classes for the Medical Research Platform backend.
Implements a comprehensive hierarchy of custom exceptions for standardized error handling.

Version: 1.0.0
"""

from rest_framework import status
from django.core.exceptions import ValidationError
from typing import Dict, Any, Optional
import json
import uuid
import logging

# Constants
ERROR_CODE_PREFIX = 'MRP'
DEFAULT_ERROR_MESSAGE = 'An unexpected error occurred'
SENSITIVE_FIELDS = ['password', 'token', 'key']

# Configure logger
logger = logging.getLogger(__name__)

class BaseAPIException(Exception):
    """
    Base exception class for all API-related errors with enhanced validation and security features.
    
    Attributes:
        message (str): Human-readable error message
        details (Dict[str, Any]): Additional error context and details
        status_code (int): HTTP status code for the error
        error_code (str): Unique error identifier
    """
    
    def __init__(
        self, 
        message: str = DEFAULT_ERROR_MESSAGE,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> None:
        """
        Initialize the base API exception with validation.
        
        Args:
            message: Human-readable error description
            details: Additional error context
            status_code: HTTP status code
        """
        super().__init__(message)
        
        # Validate and set message
        self.message = str(message) if message else DEFAULT_ERROR_MESSAGE
        
        # Validate and set details
        self.details = self.validate_details(details if details else {})
        
        # Validate and set status code
        if not isinstance(status_code, int) or status_code < 100 or status_code > 599:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.status_code = status_code
        
        # Generate unique error code
        self.error_code = f"{ERROR_CODE_PREFIX}-{str(uuid.uuid4())[:8]}"
        
        # Log exception creation
        logger.error(
            "API Exception occurred",
            extra={
                "error_code": self.error_code,
                "status_code": self.status_code,
                "message": self.message,
                "details": self.details
            }
        )

    def validate_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates error details structure and sanitizes sensitive data.
        
        Args:
            details: Dictionary containing error details
            
        Returns:
            Validated and sanitized details dictionary
        """
        if not isinstance(details, dict):
            return {}
            
        # Create a copy to avoid modifying the original
        sanitized_details = details.copy()
        
        # Remove sensitive information
        for field in SENSITIVE_FIELDS:
            if field in sanitized_details:
                sanitized_details[field] = "[REDACTED]"
                
        # Ensure all values are serializable
        try:
            json.dumps(sanitized_details)
        except (TypeError, ValueError):
            return {}
            
        return sanitized_details

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts exception to serializable dictionary format.
        
        Returns:
            Dictionary representation of the error
        """
        return {
            "message": self.message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "details": self.details
        }


class ValidationException(BaseAPIException):
    """
    Exception for data validation errors with enhanced detail validation.
    
    Extends BaseAPIException with specific handling for validation errors.
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize validation exception with enhanced validation.
        
        Args:
            message: Validation error description
            details: Field-specific validation errors
        """
        # Initialize with 400 Bad Request status
        super().__init__(
            message=message,
            details=self._format_validation_details(details),
            status_code=status.HTTP_400_BAD_REQUEST
        )
        
        # Log validation specific context
        logger.warning(
            "Validation error occurred",
            extra={
                "error_code": self.error_code,
                "validation_details": self.details
            }
        )
    
    def _format_validation_details(self, details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Formats validation-specific error details.
        
        Args:
            details: Raw validation error details
            
        Returns:
            Formatted validation error details
        """
        if not details:
            return {}
            
        # Handle Django ValidationError conversion
        if isinstance(details, ValidationError):
            return {"fields": details.message_dict}
            
        # Ensure details has a fields key for consistency
        if "fields" not in details:
            return {"fields": details}
            
        return details