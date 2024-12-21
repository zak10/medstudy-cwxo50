"""
Pydantic schemas for user-related data validation in the Medical Research Platform.
Implements secure validation rules for user registration, profile management, and MFA.

Version: 1.0.0
"""

from typing import Dict, Optional
import re
from pydantic import BaseModel, Field, EmailStr, constr  # v2.0.0
from services.user.models import User, ROLE_CHOICES
from core.exceptions import ValidationException

# Security constants
PASSWORD_MIN_LENGTH = 12
PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{12,}$"
MFA_CODE_REGEX = r"^\d{6}$"
MFA_CODE_EXPIRY = 30  # seconds

# Sensitive fields that should be sanitized
SENSITIVE_FIELDS = {'password', 'secret', 'token', 'key', 'mfa_secret'}

class BaseUserSchema(BaseModel):
    """
    Base schema for common user fields with enhanced security validation.
    Implements core field validation with sanitization.
    """
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        example="user@example.com"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="User's first name",
        example="John"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="User's last name",
        example="Doe"
    )
    role: str = Field(
        default="participant",
        description="User's role in the system"
    )

    def validate_role(self, role: str) -> str:
        """
        Validates user role against allowed choices with security checks.
        
        Args:
            role: Role to validate
            
        Returns:
            Validated role string
            
        Raises:
            ValidationException: If role is invalid
        """
        # Sanitize input
        role = role.lower().strip()
        
        # Validate against allowed choices
        valid_roles = dict(ROLE_CHOICES)
        if role not in valid_roles:
            raise ValidationException(
                message="Invalid role specified",
                details={"allowed_roles": list(valid_roles.keys())}
            )
        
        return role

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            # Custom JSON encoders if needed
        }
        extra = "forbid"  # Prevent additional fields

class UserRegistrationSchema(BaseUserSchema):
    """
    Schema for secure user registration with enhanced password validation.
    Implements comprehensive password security rules.
    """
    
    password: constr(regex=PASSWORD_REGEX) = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        description="User's password (min 12 chars, must include uppercase, lowercase, number, symbol)"
    )
    password_confirm: str = Field(
        ...,
        description="Password confirmation"
    )
    profile: Optional[Dict] = Field(
        default={},
        description="Additional user profile data"
    )

    def validate_password(self, password: str, password_confirm: str) -> str:
        """
        Validates password with comprehensive security checks.
        
        Args:
            password: Primary password
            password_confirm: Password confirmation
            
        Returns:
            Validated password
            
        Raises:
            ValidationException: If password validation fails
        """
        # Check password match
        if password != password_confirm:
            raise ValidationException(
                message="Passwords do not match",
                details={"field": "password_confirm"}
            )
        
        # Validate password complexity
        if not re.match(PASSWORD_REGEX, password):
            raise ValidationException(
                message="Password does not meet complexity requirements",
                details={
                    "requirements": {
                        "min_length": PASSWORD_MIN_LENGTH,
                        "uppercase": "At least one uppercase letter",
                        "lowercase": "At least one lowercase letter",
                        "number": "At least one number",
                        "symbol": "At least one symbol (@$!%*#?&)"
                    }
                }
            )
        
        return password

    def sanitize_profile(self, profile: Dict) -> Dict:
        """
        Sanitizes profile data by removing sensitive fields.
        
        Args:
            profile: Raw profile data
            
        Returns:
            Sanitized profile dictionary
        """
        if not profile:
            return {}
            
        sanitized = profile.copy()
        for field in SENSITIVE_FIELDS:
            sanitized.pop(field, None)
            
        return sanitized

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "profile": {"bio": "Research enthusiast"}
            }
        }

class MFASetupSchema(BaseModel):
    """
    Enhanced schema for secure MFA configuration.
    Implements validation for MFA setup and verification.
    """
    
    mfa_secret: str = Field(
        ...,
        min_length=32,
        max_length=32,
        description="MFA secret key"
    )
    setup_code: constr(regex=MFA_CODE_REGEX) = Field(
        ...,
        description="6-digit MFA setup verification code"
    )

    def validate_setup_code(self, setup_code: str) -> str:
        """
        Validates MFA setup code with comprehensive security checks.
        
        Args:
            setup_code: 6-digit verification code
            
        Returns:
            Validated setup code
            
        Raises:
            ValidationException: If code validation fails
        """
        # Sanitize input
        setup_code = setup_code.strip()
        
        # Validate code format
        if not re.match(MFA_CODE_REGEX, setup_code):
            raise ValidationException(
                message="Invalid MFA setup code format",
                details={"format": "6-digit numeric code required"}
            )
        
        return setup_code

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "mfa_secret": "JBSWY3DPEHPK3PXP",
                "setup_code": "123456"
            }
        }