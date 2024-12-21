"""
API v1 Pydantic schemas for the Medical Research Platform.
Implements comprehensive request/response validation with enhanced security features.

Version: 1.0.0
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr  # v2.0.0
import bleach  # v6.0.0
from jose import jwt  # v3.3.0

from services.protocol.schemas import ProtocolBaseSchema
from services.data.schemas import DataPointSchema
from services.user.schemas import UserBase

# Constants for validation and security
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20
ALLOWED_SORT_ORDERS = ['asc', 'desc']
HTML_ALLOWED_TAGS = ['p', 'br', 'strong', 'em']
REQUEST_TIMEOUT = 30  # seconds

class APIResponse(BaseModel):
    """
    Enhanced base schema for all API responses with security features and HIPAA compliance.
    """
    success: bool = Field(
        ...,
        description="Indicates if the request was successful"
    )
    message: Optional[str] = Field(
        None,
        description="Human-readable response message"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Response payload data"
    )
    errors: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of validation or processing errors"
    )
    request_id: Optional[str] = Field(
        None,
        description="Unique request identifier for tracing"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )

    def format_errors(self, error_list: List[Any], sanitize_output: bool = True) -> List[Dict[str, Any]]:
        """
        Formats validation errors into HIPAA-compliant structure.
        
        Args:
            error_list: List of error objects
            sanitize_output: Whether to sanitize sensitive information
            
        Returns:
            List of formatted and sanitized errors
        """
        formatted_errors = []
        
        for error in error_list:
            error_dict = {
                "code": getattr(error, "code", "VALIDATION_ERROR"),
                "message": str(error),
                "location": getattr(error, "loc", None),
                "context": getattr(error, "ctx", {})
            }
            
            if sanitize_output:
                # Remove sensitive information
                sensitive_fields = ["password", "token", "secret", "key"]
                for field in sensitive_fields:
                    if field in error_dict.get("context", {}):
                        error_dict["context"][field] = "[REDACTED]"
            
            formatted_errors.append(error_dict)
        
        return formatted_errors

    def sanitize_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes response data for security.
        
        Args:
            response_data: Raw response data
            
        Returns:
            Sanitized response data
        """
        if not response_data:
            return {}
            
        sanitized = response_data.copy()
        
        # Sanitize HTML content
        for key, value in sanitized.items():
            if isinstance(value, str):
                sanitized[key] = bleach.clean(
                    value,
                    tags=HTML_ALLOWED_TAGS,
                    strip=True
                )
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_response(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_response(item) if isinstance(item, dict)
                    else bleach.clean(item, tags=HTML_ALLOWED_TAGS, strip=True) if isinstance(item, str)
                    else item
                    for item in value
                ]
        
        return sanitized

class PaginationParams(BaseModel):
    """
    Enhanced schema for pagination parameters with validation.
    """
    page: int = Field(
        default=1,
        ge=1,
        description="Page number"
    )
    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Number of items per page"
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by"
    )
    sort_order: Optional[str] = Field(
        default="asc",
        description="Sort direction"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Query filters"
    )

    def validate_pagination(self) -> bool:
        """
        Validates and sanitizes pagination parameters.
        
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        # Validate page size
        if self.page_size > MAX_PAGE_SIZE:
            raise ValueError(f"Page size cannot exceed {MAX_PAGE_SIZE}")
            
        # Validate sort order
        if self.sort_order and self.sort_order.lower() not in ALLOWED_SORT_ORDERS:
            raise ValueError(f"Sort order must be one of: {', '.join(ALLOWED_SORT_ORDERS)}")
            
        # Sanitize filters
        if self.filters:
            # Remove any SQL injection attempts
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "UNION"]
            for key, value in self.filters.items():
                if isinstance(value, str):
                    for keyword in sql_keywords:
                        if keyword.lower() in value.lower():
                            raise ValueError("Invalid filter value")
        
        return True

class ProtocolAPISchema(ProtocolBaseSchema):
    """
    Enhanced API schema for protocol endpoints with comprehensive validation.
    """
    id: UUID = Field(
        ...,
        description="Unique protocol identifier"
    )
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Protocol title"
    )
    description: str = Field(
        ...,
        max_length=2000,
        description="Protocol description"
    )
    requirements: Dict[str, Any] = Field(
        ...,
        description="Protocol requirements specification"
    )
    safety_params: Dict[str, Any] = Field(
        ...,
        description="Safety monitoring parameters"
    )
    start_date: datetime = Field(
        ...,
        description="Protocol start date"
    )
    duration_weeks: int = Field(
        ...,
        ge=1,
        le=52,
        description="Protocol duration in weeks"
    )
    participant_count: int = Field(
        default=0,
        ge=0,
        description="Current number of participants"
    )
    completion_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Protocol completion rate"
    )
    safety_monitoring: Dict[str, Any] = Field(
        default_factory=dict,
        description="Safety monitoring configuration"
    )
    data_collection_schedule: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Data collection schedule"
    )

    def validate_api_constraints(self) -> bool:
        """
        Comprehensive validation of protocol constraints.
        
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        # Validate protocol metadata
        if not self.title or not self.description:
            raise ValueError("Protocol title and description are required")
            
        # Validate dates using parent class method
        self.validate_dates()
        
        # Validate safety parameters using parent class method
        self.validate_safety_params()
        
        # Validate data collection schedule
        if self.data_collection_schedule:
            for schedule in self.data_collection_schedule:
                if not all(key in schedule for key in ["type", "frequency", "start_week"]):
                    raise ValueError("Invalid data collection schedule format")
                
                if schedule["start_week"] > self.duration_weeks:
                    raise ValueError("Schedule start week cannot exceed protocol duration")
        
        return True

    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
        validate_assignment = True
        extra = "forbid"