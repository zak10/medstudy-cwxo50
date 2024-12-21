"""
API v1 view implementations for the Medical Research Platform.
Provides secure, validated endpoints for user management, protocol operations,
data collection, analysis, and community features.

Version: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from uuid import UUID

from django_ninja import NinjaAPI  # v0.22.0
from django.core.cache import cache
from django.conf import settings
from django_ratelimit.decorators import ratelimit  # v3.0.1
import jwt  # v2.7.0

from api.v1.schemas import APIResponse
from services.protocol.schemas import (
    validate_requirements_schema,
    validate_safety_parameters,
    PROTOCOL_REQUIREMENTS_SCHEMA
)
from services.data.schemas import (
    DataPointSchema,
    BloodWorkSchema,
    WeeklyCheckInSchema
)
from services.user.schemas import (
    UserRegistrationSchema,
    MFASetupSchema
)
from services.user.models import User, ROLE_CHOICES
from core.exceptions import ValidationException
from core.validators import (
    validate_blood_work_data,
    validate_biometric_data,
    validate_check_in_data
)

# Configure logging
logger = logging.getLogger(__name__)

# API Configuration
api_router = NinjaAPI(
    title="Medical Research Platform API",
    version="1.0",
    description="Secure API for medical research protocol management",
    docs_url="/api/v1/docs"
)

# Rate limiting settings
RATE_LIMIT_SETTINGS = {
    "default": "100/h",  # Default rate limit
    "auth": "5/m",      # Authentication endpoints
    "sensitive": "20/m"  # Sensitive operations
}

class JWTAuth:
    """Enhanced JWT authentication handler with refresh token support."""
    
    def __init__(
        self,
        algorithm: str = "RS256",
        access_lifetime: int = 3600,  # 1 hour
        refresh_lifetime: int = 604800  # 1 week
    ):
        """Initialize JWT auth handler with security settings."""
        self.algorithm = algorithm
        self.access_token_lifetime = access_lifetime
        self.refresh_token_lifetime = refresh_lifetime
        self.secret_key = settings.JWT_SECRET_KEY
        self.refresh_token_secret = settings.JWT_REFRESH_SECRET
        
        # Initialize token blacklist cache
        self.token_blacklist = cache.get_client("tokens")
    
    def authenticate(self, request) -> Optional[User]:
        """
        Authenticates API request with enhanced security checks.
        
        Args:
            request: HTTP request object
            
        Returns:
            Optional[User]: Authenticated user or None
        """
        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return None
                
            token = auth_header.split(" ")[1]
            
            # Check token blacklist
            if self.token_blacklist.get(f"bl_{token}"):
                logger.warning("Blacklisted token used", extra={"token": token[:8]})
                return None
            
            # Verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Get and validate user
            user = User.objects.get(id=payload["user_id"])
            if not user.is_active:
                logger.warning(
                    "Inactive user attempted access",
                    extra={"user_id": user.id}
                )
                return None
                
            return user
            
        except (jwt.InvalidTokenError, User.DoesNotExist) as e:
            logger.warning(
                "Authentication failed",
                extra={"error": str(e)}
            )
            return None
    
    def generate_token_pair(self, user: User) -> Dict[str, str]:
        """
        Generates secure access and refresh tokens.
        
        Args:
            user: User instance
            
        Returns:
            Dict containing access and refresh tokens
        """
        # Generate access token
        access_payload = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(seconds=self.access_token_lifetime)
        }
        
        access_token = jwt.encode(
            access_payload,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # Generate refresh token
        refresh_payload = {
            "user_id": str(user.id),
            "token_type": "refresh",
            "exp": datetime.utcnow() + timedelta(seconds=self.refresh_token_lifetime)
        }
        
        refresh_token = jwt.encode(
            refresh_payload,
            self.refresh_token_secret,
            algorithm=self.algorithm
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.access_token_lifetime
        }

# Authentication endpoints
@api_router.post("/auth/register", response=APIResponse)
@ratelimit(key="ip", rate=RATE_LIMIT_SETTINGS["auth"])
async def register_user(request, data: UserRegistrationSchema) -> APIResponse:
    """
    Handles secure user registration with validation.
    
    Args:
        request: HTTP request
        data: Registration data
        
    Returns:
        APIResponse with registration result
    """
    try:
        # Validate registration data
        if User.objects.filter(email=data.email).exists():
            raise ValidationException("Email already registered")
        
        # Create user account
        user = User.objects.create_user(
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            profile=data.profile
        )
        
        # Generate auth tokens
        auth_handler = JWTAuth()
        tokens = auth_handler.generate_token_pair(user)
        
        logger.info(f"User registered successfully: {user.email}")
        
        return APIResponse(
            success=True,
            message="Registration successful",
            data={
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role
                },
                **tokens
            }
        )
        
    except ValidationException as e:
        logger.warning(
            "Registration validation failed",
            extra={"error": str(e)}
        )
        return APIResponse(
            success=False,
            message="Registration failed",
            errors=e.to_dict()
        )
    
    except Exception as e:
        logger.error(
            "Registration error",
            extra={"error": str(e)},
            exc_info=True
        )
        return APIResponse(
            success=False,
            message="An error occurred during registration"
        )

@api_router.post("/auth/refresh", response=APIResponse)
@ratelimit(key="ip", rate=RATE_LIMIT_SETTINGS["auth"])
async def refresh_token(request, refresh_token: str) -> APIResponse:
    """
    Handles JWT refresh token operations securely.
    
    Args:
        request: HTTP request
        refresh_token: Refresh token string
        
    Returns:
        APIResponse with new access token
    """
    try:
        auth_handler = JWTAuth()
        
        # Verify refresh token
        payload = jwt.decode(
            refresh_token,
            auth_handler.refresh_token_secret,
            algorithms=[auth_handler.algorithm]
        )
        
        # Validate token type
        if payload.get("token_type") != "refresh":
            raise jwt.InvalidTokenError("Invalid token type")
        
        # Get user and generate new access token
        user = User.objects.get(id=payload["user_id"])
        new_tokens = auth_handler.generate_token_pair(user)
        
        # Blacklist old refresh token
        auth_handler.token_blacklist.set(
            f"bl_{refresh_token}",
            "1",
            timeout=auth_handler.refresh_token_lifetime
        )
        
        return APIResponse(
            success=True,
            message="Token refresh successful",
            data=new_tokens
        )
        
    except (jwt.InvalidTokenError, User.DoesNotExist) as e:
        logger.warning(
            "Token refresh failed",
            extra={"error": str(e)}
        )
        return APIResponse(
            success=False,
            message="Invalid refresh token"
        )

# Export the router for URL configuration
__all__ = ['api_router']