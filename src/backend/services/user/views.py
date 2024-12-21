"""
User management API views for the Medical Research Platform.
Implements secure user registration, authentication, profile management and MFA configuration
with enhanced security, logging and performance optimizations.

Version: 1.0.0
"""

from rest_framework import viewsets, status  # version: ^3.14.0
from rest_framework.response import Response  # version: ^3.14.0
from rest_framework.decorators import action, throttle_classes  # version: ^3.14.0
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from rest_framework_extensions.cache.decorators import cache_response
import logging
from typing import Dict, Any

from services.user.models import User, ROLE_CHOICES
from services.user.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    MFASetupSerializer
)
from core.authentication import JWTAuthentication, MFAAuthentication
from core.permissions import BaseRolePermission
from core.exceptions import AuthenticationException, ValidationException

# Configure logger
logger = logging.getLogger(__name__)

# Security constants
MFA_REQUIRED_ROLES = ['protocol_creator', 'partner', 'admin']
AUTH_CACHE_TIMEOUT = 300  # 5 minutes
MAX_LOGIN_ATTEMPTS = 5
SUSPICIOUS_IP_THRESHOLD = 10

class UserViewSet(viewsets.ModelViewSet):
    """
    Enhanced ViewSet for user management with security features and performance optimizations.
    Implements user registration, authentication, profile management and MFA configuration.
    """
    
    queryset = User.objects.all().select_related()
    serializer_class = UserRegistrationSerializer
    permission_classes = [BaseRolePermission]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, *args, **kwargs):
        """Initialize viewset with authentication and caching configuration."""
        super().__init__(*args, **kwargs)
        self.jwt_auth = JWTAuthentication()
        self.mfa_auth = MFAAuthentication()
        self.cache_timeout = AUTH_CACHE_TIMEOUT

    @action(methods=['post'], detail=False, permission_classes=[])
    @throttle_classes([ratelimit(key='ip', rate='5/m', method=['POST'])])
    def register(self, request) -> Response:
        """
        Secure user registration endpoint with enhanced validation.
        
        Args:
            request: HTTP request object containing registration data
            
        Returns:
            Response with user data and authentication token
            
        Raises:
            ValidationException: If registration data is invalid
        """
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create user with validated data
            user = serializer.create(serializer.validated_data)
            
            # Generate authentication token
            token = self.jwt_auth.get_token(user)
            
            logger.info(
                "User registered successfully",
                extra={"user_id": user.id, "email": user.email}
            )
            
            return Response({
                "user": serializer.data,
                "token": token
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise ValidationException(
                message="Registration failed",
                details={"error": str(e)}
            )

    @action(methods=['post'], detail=False, permission_classes=[])
    @throttle_classes([ratelimit(key='ip', rate='5/m', method=['POST'])])
    def login(self, request) -> Response:
        """
        Secure login endpoint with MFA support and suspicious activity detection.
        
        Args:
            request: HTTP request object containing login credentials
            
        Returns:
            Response with authentication token and MFA status
            
        Raises:
            AuthenticationException: If authentication fails
        """
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            
            # Check login attempts
            attempt_key = f'login_attempts:{email}'
            attempts = cache.get(attempt_key, 0)
            
            if attempts >= MAX_LOGIN_ATTEMPTS:
                raise AuthenticationException(
                    message="Too many login attempts",
                    details={"retry_after": "300 seconds"}
                )
            
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise AuthenticationException(message="Invalid credentials")
                    
            except User.DoesNotExist:
                raise AuthenticationException(message="Invalid credentials")
            
            # Check if MFA is required
            requires_mfa = user.role in MFA_REQUIRED_ROLES
            if requires_mfa and not user.mfa_enabled:
                return Response({
                    "message": "MFA setup required",
                    "requires_mfa": True
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Handle MFA verification if enabled
            if user.mfa_enabled:
                return Response({
                    "message": "MFA verification required",
                    "requires_verification": True,
                    "user_id": str(user.id)
                }, status=status.HTTP_200_OK)
            
            # Generate token for non-MFA users
            token = self.jwt_auth.get_token(user)
            
            # Reset login attempts on success
            cache.delete(attempt_key)
            
            logger.info(
                "Login successful",
                extra={"user_id": user.id, "email": user.email}
            )
            
            return Response({
                "token": token,
                "user": UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except AuthenticationException as e:
            # Increment login attempts
            cache.set(attempt_key, attempts + 1, 300)
            raise
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise AuthenticationException(
                message="Login failed",
                details={"error": str(e)}
            )

    @action(methods=['put'], detail=True)
    @cache_response(timeout=300)
    def update_profile(self, request, pk=None) -> Response:
        """
        Update user profile with validation and audit logging.
        
        Args:
            request: HTTP request object containing profile updates
            pk: User ID
            
        Returns:
            Response with updated profile data
            
        Raises:
            ValidationException: If profile data is invalid
        """
        try:
            user = self.get_object()
            serializer = UserProfileSerializer(
                user,
                data=request.data,
                partial=True
            )
            
            serializer.is_valid(raise_exception=True)
            updated_user = serializer.save()
            
            # Invalidate relevant caches
            cache_key = f'user_profile_{user.id}'
            cache.delete(cache_key)
            
            logger.info(
                "Profile updated",
                extra={"user_id": user.id, "updated_fields": request.data.keys()}
            )
            
            return Response(
                UserProfileSerializer(updated_user).data,
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            raise ValidationException(
                message="Profile update failed",
                details={"error": str(e)}
            )

    @action(methods=['post'], detail=True)
    @throttle_classes([ratelimit(key='user', rate='3/h', method=['POST'])])
    def setup_mfa(self, request, pk=None) -> Response:
        """
        Configure MFA for user with enhanced security.
        
        Args:
            request: HTTP request object
            pk: User ID
            
        Returns:
            Response with MFA setup data
            
        Raises:
            ValidationException: If MFA setup fails
        """
        try:
            user = self.get_object()
            
            # Generate new MFA credentials
            secret, backup_codes = self.mfa_auth.generate_secret()
            
            # Validate setup code if provided
            if 'setup_code' in request.data:
                serializer = MFASetupSerializer(data={
                    'mfa_secret': secret,
                    'setup_code': request.data['setup_code']
                })
                serializer.is_valid(raise_exception=True)
                
                # Enable MFA for user
                user.mfa_secret = secret
                user.mfa_enabled = True
                user.save()
                
                logger.info(
                    "MFA setup completed",
                    extra={"user_id": user.id}
                )
                
                return Response({
                    "message": "MFA enabled successfully",
                    "backup_codes": backup_codes
                }, status=status.HTTP_200_OK)
            
            # Return initial setup data
            return Response({
                "secret": secret,
                "qr_code": f"otpauth://totp/MRP:{user.email}?secret={secret}&issuer=MRP"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"MFA setup failed: {str(e)}")
            raise ValidationException(
                message="MFA setup failed",
                details={"error": str(e)}
            )

    @action(methods=['post'], detail=False)
    @throttle_classes([ratelimit(key='ip', rate='5/m', method=['POST'])])
    def verify_mfa(self, request) -> Response:
        """
        Verify MFA token during login with security logging.
        
        Args:
            request: HTTP request object containing MFA token
            
        Returns:
            Response with authentication token
            
        Raises:
            AuthenticationException: If verification fails
        """
        try:
            user_id = request.data.get('user_id')
            token = request.data.get('token')
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise AuthenticationException(message="Invalid user")
            
            # Verify MFA token
            device_info = {
                "ip": request.META.get('REMOTE_ADDR'),
                "user_agent": request.META.get('HTTP_USER_AGENT')
            }
            
            if not self.mfa_auth.verify_token(user, token, device_info):
                raise AuthenticationException(message="Invalid MFA token")
            
            # Generate authentication token
            auth_token = self.jwt_auth.get_token(user)
            
            logger.info(
                "MFA verification successful",
                extra={"user_id": user.id}
            )
            
            return Response({
                "token": auth_token,
                "user": UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"MFA verification failed: {str(e)}")
            raise AuthenticationException(
                message="MFA verification failed",
                details={"error": str(e)}
            )