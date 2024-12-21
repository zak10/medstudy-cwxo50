"""
Core authentication implementation for the Medical Research Platform.
Implements secure JWT-based authentication with RS256 signing, MFA support,
rate limiting, and session management.

Version: 1.0.0
"""

from rest_framework.authentication import BaseAuthentication  # version: 3.14.0
import jwt  # version: 2.7.0
from django.conf import settings
import pyotp  # version: 2.8.0
from redis import Redis  # version: 4.5.0
from django_ratelimit.decorators import ratelimit  # version: 3.0.1
import logging
from datetime import datetime, timedelta
import secrets
import json
from typing import Optional, Tuple, List, Dict, Any

from core.exceptions import AuthenticationException
from services.user.models import User

# Configure logger
logger = logging.getLogger(__name__)

class JWTAuthentication(BaseAuthentication):
    """
    JWT token-based authentication with RS256 signing, token blacklisting,
    and rate limiting for enhanced security.
    """
    
    def __init__(self) -> None:
        """Initialize JWT authentication with Redis connection and key paths."""
        self.auth_header_prefix = 'Bearer'
        self.auth_header_type = 'JWT'
        
        # Initialize Redis for token management
        self.redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_AUTH_DB,
            decode_responses=True
        )
        
        # Load RS256 keys
        try:
            with open(settings.JWT_PRIVATE_KEY_PATH, 'r') as f:
                self.private_key = f.read()
            with open(settings.JWT_PUBLIC_KEY_PATH, 'r') as f:
                self.public_key = f.read()
        except Exception as e:
            logger.critical(f"Failed to load JWT keys: {str(e)}")
            raise
            
        self.token_expiry = settings.JWT_TOKEN_EXPIRY

    def authenticate(self, request) -> Optional[Tuple[User, str]]:
        """
        Authenticates requests using JWT tokens with blacklist check.
        
        Args:
            request: The incoming request object
            
        Returns:
            Tuple of (user, token) if valid, None otherwise
            
        Raises:
            AuthenticationException: If authentication fails
        """
        try:
            auth_header = request.headers.get('Authorization', '').split()
            
            if not auth_header or len(auth_header) != 2:
                return None
                
            if auth_header[0] != self.auth_header_prefix:
                return None
                
            token = auth_header[1]
            
            # Check token blacklist
            if self.redis_client.sismember('token_blacklist', token):
                raise AuthenticationException(
                    message="Token has been revoked",
                    details={"token_status": "blacklisted"}
                )
            
            # Verify and decode token
            try:
                payload = jwt.decode(
                    token,
                    self.public_key,
                    algorithms=['RS256'],
                    audience=settings.JWT_AUDIENCE,
                    issuer=settings.JWT_ISSUER
                )
            except jwt.ExpiredSignatureError:
                raise AuthenticationException(
                    message="Token has expired",
                    details={"token_status": "expired"}
                )
            except jwt.InvalidTokenError as e:
                raise AuthenticationException(
                    message="Invalid token",
                    details={"error": str(e)}
                )
            
            # Get and validate user
            try:
                user = User.objects.get(id=payload['sub'])
                if not user.is_active:
                    raise AuthenticationException(
                        message="User account is disabled",
                        details={"user_status": "inactive"}
                    )
            except User.DoesNotExist:
                raise AuthenticationException(
                    message="User not found",
                    details={"user_status": "not_found"}
                )
            
            logger.info(
                "Successful authentication",
                extra={
                    "user_id": user.id,
                    "token_type": self.auth_header_type
                }
            )
            
            return (user, token)
            
        except Exception as e:
            logger.error(
                f"Authentication error: {str(e)}",
                extra={"error_type": type(e).__name__}
            )
            raise

    @ratelimit(key='user', rate='10/m', method=['POST'])
    def get_token(self, user: User) -> str:
        """
        Generates RS256 signed JWT token with rate limiting.
        
        Args:
            user: User instance to generate token for
            
        Returns:
            Encoded JWT token string
            
        Raises:
            AuthenticationException: If token generation fails
        """
        try:
            now = datetime.utcnow()
            expiry = now + timedelta(seconds=self.token_expiry)
            
            payload = {
                'sub': str(user.id),
                'email': user.email,
                'role': user.role,
                'iat': now,
                'exp': expiry,
                'iss': settings.JWT_ISSUER,
                'aud': settings.JWT_AUDIENCE,
                'jti': secrets.token_urlsafe(32)
            }
            
            token = jwt.encode(
                payload,
                self.private_key,
                algorithm='RS256'
            )
            
            # Store token metadata
            self.redis_client.setex(
                f'token:{payload["jti"]}',
                self.token_expiry,
                json.dumps({
                    'user_id': str(user.id),
                    'issued_at': now.isoformat(),
                    'expires_at': expiry.isoformat()
                })
            )
            
            logger.info(
                "Token generated",
                extra={
                    "user_id": user.id,
                    "token_jti": payload["jti"]
                }
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Token generation error: {str(e)}")
            raise AuthenticationException(
                message="Failed to generate token",
                details={"error": str(e)}
            )

    def blacklist_token(self, token: str) -> bool:
        """
        Adds token to blacklist in Redis.
        
        Args:
            token: JWT token to blacklist
            
        Returns:
            True if blacklisted successfully
        """
        try:
            # Decode without verification to get expiry
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            # Add to blacklist with expiry
            expiry = datetime.fromtimestamp(payload['exp']) - datetime.utcnow()
            self.redis_client.sadd('token_blacklist', token)
            self.redis_client.expire('token_blacklist', int(expiry.total_seconds()))
            
            logger.info(
                "Token blacklisted",
                extra={"token_jti": payload.get("jti")}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Token blacklist error: {str(e)}")
            return False


class MFAAuthentication:
    """
    Multi-factor authentication with TOTP, backup codes,
    and device tracking for enhanced security.
    """
    
    def __init__(self) -> None:
        """Initialize MFA with Redis for session tracking."""
        self.token_validity = 30  # TOTP token validity in seconds
        self.backup_codes_count = 10
        self.max_attempts = 5
        
        # Initialize Redis connection
        self.redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_AUTH_DB,
            decode_responses=True
        )

    @ratelimit(key='ip', rate='5/m', method=['POST'])
    def verify_token(self, user: User, token: str, device_info: Dict[str, Any]) -> bool:
        """
        Verifies TOTP token with rate limiting and device tracking.
        
        Args:
            user: User to verify token for
            token: TOTP token or backup code
            device_info: Device metadata for tracking
            
        Returns:
            True if verification successful
            
        Raises:
            AuthenticationException: If verification fails
        """
        try:
            # Check attempt count
            attempt_key = f'mfa_attempts:{user.id}'
            attempts = int(self.redis_client.get(attempt_key) or 0)
            
            if attempts >= self.max_attempts:
                raise AuthenticationException(
                    message="Maximum verification attempts exceeded",
                    details={"retry_after": "300 seconds"}
                )
            
            # Increment attempt counter
            self.redis_client.incr(attempt_key)
            self.redis_client.expire(attempt_key, 300)  # Reset after 5 minutes
            
            # Check if token is a backup code
            backup_codes_key = f'backup_codes:{user.id}'
            if self.redis_client.sismember(backup_codes_key, token):
                self.redis_client.srem(backup_codes_key, token)
                self._track_device(user.id, device_info)
                return True
            
            # Verify TOTP token
            totp = pyotp.TOTP(user.mfa_secret)
            if totp.verify(token, valid_window=1):
                self._track_device(user.id, device_info)
                self.redis_client.delete(attempt_key)
                return True
                
            raise AuthenticationException(
                message="Invalid verification token",
                details={"attempts_remaining": self.max_attempts - attempts - 1}
            )
            
        except Exception as e:
            logger.error(f"MFA verification error: {str(e)}")
            raise

    def generate_secret(self) -> Tuple[str, List[str]]:
        """
        Generates new MFA secret and backup codes.
        
        Returns:
            Tuple of (secret, backup_codes)
        """
        try:
            # Generate random base32 secret
            secret = pyotp.random_base32()
            
            # Generate backup codes
            backup_codes = [
                secrets.token_urlsafe(12)
                for _ in range(self.backup_codes_count)
            ]
            
            logger.info("Generated new MFA credentials")
            
            return secret, backup_codes
            
        except Exception as e:
            logger.error(f"MFA generation error: {str(e)}")
            raise AuthenticationException(
                message="Failed to generate MFA credentials",
                details={"error": str(e)}
            )

    def _track_device(self, user_id: str, device_info: Dict[str, Any]) -> None:
        """
        Tracks verified devices for security monitoring.
        
        Args:
            user_id: User ID
            device_info: Device metadata
        """
        try:
            device_key = f'mfa_devices:{user_id}'
            device_data = {
                'verified_at': datetime.utcnow().isoformat(),
                **device_info
            }
            self.redis_client.lpush(device_key, json.dumps(device_data))
            self.redis_client.ltrim(device_key, 0, 9)  # Keep last 10 devices
            
        except Exception as e:
            logger.error(f"Device tracking error: {str(e)}")