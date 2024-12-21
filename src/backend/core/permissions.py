"""
Core permission classes for the Medical Research Platform.
Implements role-based access control (RBAC) with enhanced security features,
audit logging, and performance optimizations.

Version: 1.0.0
"""

from rest_framework.permissions import BasePermission  # version: ^3.14.0
from django.conf import settings
from django.core.cache import cache  # version: ^4.2.0
import logging  # version: ^3.0.0

from core.exceptions import AuthorizationException
from core.authentication import JWTAuthentication

# Configure logger
logger = logging.getLogger(__name__)

class BaseRolePermission(BasePermission):
    """
    Enhanced base class for role-based permissions with audit logging and caching.
    Implements core permission logic with security controls and performance optimizations.
    """
    
    def __init__(self):
        """Initialize base role permission with audit logging configuration."""
        super().__init__()
        self.allowed_roles = []
        self.cache_timeout = getattr(settings, 'PERMISSION_CACHE_TIMEOUT', 300)  # 5 minutes default
        self.jwt_auth = JWTAuthentication()

    def has_permission(self, request, view):
        """
        Enhanced permission check with caching and audit logging.
        
        Args:
            request: The incoming request object
            view: The view being accessed
            
        Returns:
            bool: Permission granted or denied
            
        Raises:
            AuthorizationException: If permission check fails
        """
        try:
            # Generate cache key
            cache_key = f'perm_{request.user.id}_{view.__class__.__name__}'
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Validate JWT token
            auth_result = self.jwt_auth.authenticate(request)
            if not auth_result:
                raise AuthorizationException(
                    message="Authentication required",
                    details={"error": "No valid authentication provided"}
                )
            
            user, _ = auth_result
            
            # Check if user is active
            if not user.is_active:
                raise AuthorizationException(
                    message="User account is inactive",
                    details={"user_status": "inactive"}
                )
            
            # Superuser override
            if user.is_superuser:
                cache.set(cache_key, True, self.cache_timeout)
                return True
            
            # Role-based check
            has_role = any(user.has_role(role) for role in self.allowed_roles)
            
            if not has_role:
                raise AuthorizationException(
                    message="Insufficient permissions",
                    details={
                        "required_roles": self.allowed_roles,
                        "user_role": user.role
                    }
                )
            
            # Cache successful result
            cache.set(cache_key, True, self.cache_timeout)
            
            # Audit logging
            logger.info(
                "Permission granted",
                extra={
                    "user_id": user.id,
                    "role": user.role,
                    "view": view.__class__.__name__,
                    "method": request.method
                }
            )
            
            return True
            
        except AuthorizationException as e:
            # Log authorization failures
            logger.warning(
                "Permission denied",
                extra={
                    "user_id": getattr(request.user, 'id', None),
                    "error": str(e),
                    "view": view.__class__.__name__,
                    "method": request.method
                }
            )
            raise
        
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            raise AuthorizationException(
                message="Permission check failed",
                details={"error": str(e)}
            )

class ParticipantPermission(BaseRolePermission):
    """
    Enhanced permission class for study participants with protocol enrollment validation.
    Implements object-level permissions with caching and audit logging.
    """
    
    def __init__(self):
        """Initialize participant permission with protocol cache."""
        super().__init__()
        self.allowed_roles = ['participant']
        self.protocol_cache = {}

    def has_object_permission(self, request, view, obj):
        """
        Enhanced object-level permissions for participants with caching.
        
        Args:
            request: The incoming request object
            view: The view being accessed
            obj: The object being accessed
            
        Returns:
            bool: Permission granted or denied
            
        Raises:
            AuthorizationException: If permission check fails
        """
        try:
            user = request.user
            
            # Generate cache key for protocol enrollment
            cache_key = f'protocol_enrollment_{user.id}_{getattr(obj, "protocol_id", None)}'
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Verify protocol enrollment
            if hasattr(obj, 'protocol_id'):
                is_enrolled = any(
                    p.protocol_id == obj.protocol_id 
                    for p in user.participation_set.all()
                )
                
                if not is_enrolled:
                    raise AuthorizationException(
                        message="Not enrolled in protocol",
                        details={
                            "protocol_id": obj.protocol_id,
                            "user_id": user.id
                        }
                    )
            
            # Verify data access permissions
            if hasattr(obj, 'user_id') and obj.user_id != user.id:
                raise AuthorizationException(
                    message="Cannot access other user's data",
                    details={
                        "requested_user_id": obj.user_id,
                        "current_user_id": user.id
                    }
                )
            
            # Cache successful result
            cache.set(cache_key, True, self.cache_timeout)
            
            # Audit logging
            logger.info(
                "Object permission granted",
                extra={
                    "user_id": user.id,
                    "object_type": obj.__class__.__name__,
                    "object_id": getattr(obj, 'id', None),
                    "method": request.method
                }
            )
            
            return True
            
        except AuthorizationException as e:
            logger.warning(
                "Object permission denied",
                extra={
                    "user_id": request.user.id,
                    "error": str(e),
                    "object_type": obj.__class__.__name__,
                    "object_id": getattr(obj, 'id', None)
                }
            )
            raise
        
        except Exception as e:
            logger.error(f"Object permission check error: {str(e)}")
            raise AuthorizationException(
                message="Object permission check failed",
                details={"error": str(e)}
            )