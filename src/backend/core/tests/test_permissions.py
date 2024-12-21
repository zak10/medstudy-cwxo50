"""
Test suite for the Medical Research Platform's permission classes.
Tests role-based access control, security features, and permission validation.

Version: 1.0.0
"""

import pytest  # version: ^7.4.0
from rest_framework.test import APIRequestFactory  # version: ^3.14.0
from unittest.mock import Mock, patch  # version: ^3.11.0
from freezegun import freeze_time  # version: ^1.2.0
from django.core.cache import cache
from django.conf import settings
import jwt
import time

from core.permissions import BaseRolePermission, ParticipantPermission
from core.exceptions import AuthorizationException
from services.user.models import User

# Test constants
RATE_LIMIT_PERIOD = 60  # seconds
MAX_PERMISSION_CHECKS = 100

@pytest.mark.django_db
class TestBaseRolePermission:
    """Test cases for base role permission functionality including security features."""
    
    def setup_method(self):
        """Set up test environment with security mocks."""
        self.factory = APIRequestFactory()
        self.permission = BaseRolePermission()
        
        # Mock user and view
        self.user = Mock(spec=User)
        self.user.id = '123'
        self.user.is_active = True
        self.user.is_superuser = False
        self.user.role = 'participant'
        self.user.has_role = Mock(return_value=True)
        
        self.view = Mock()
        self.view.__class__.__name__ = 'TestView'
        
        # Clear cache
        cache.clear()
        
        # Mock JWT authentication
        self.jwt_auth_patcher = patch('core.permissions.JWTAuthentication')
        self.mock_jwt_auth = self.jwt_auth_patcher.start()
        self.mock_jwt_auth.return_value.authenticate.return_value = (self.user, 'valid_token')

    def teardown_method(self):
        """Clean up test environment."""
        self.jwt_auth_patcher.stop()
        cache.clear()

    def test_has_permission_basic(self):
        """Test basic permission check functionality."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        assert self.permission.has_permission(request, self.view) is True
        
        # Test inactive user
        self.user.is_active = False
        with pytest.raises(AuthorizationException) as exc:
            self.permission.has_permission(request, self.view)
        assert "User account is inactive" in str(exc.value)

    def test_superuser_override(self):
        """Test superuser permission override."""
        request = self.factory.get('/test/')
        request.user = self.user
        self.user.is_superuser = True
        
        assert self.permission.has_permission(request, self.view) is True
        
        # Verify cache was set
        cache_key = f'perm_{self.user.id}_{self.view.__class__.__name__}'
        assert cache.get(cache_key) is True

    def test_role_based_access(self):
        """Test role-based access control."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Test allowed role
        self.permission.allowed_roles = ['participant']
        assert self.permission.has_permission(request, self.view) is True
        
        # Test denied role
        self.permission.allowed_roles = ['admin']
        self.user.has_role.return_value = False
        
        with pytest.raises(AuthorizationException) as exc:
            self.permission.has_permission(request, self.view)
        assert "Insufficient permissions" in str(exc.value)

    @freeze_time("2023-01-01 00:00:00")
    def test_permission_caching(self):
        """Test permission check caching behavior."""
        request = self.factory.get('/test/')
        request.user = self.user
        cache_key = f'perm_{self.user.id}_{self.view.__class__.__name__}'
        
        # First check should cache result
        assert self.permission.has_permission(request, self.view) is True
        assert cache.get(cache_key) is True
        
        # Second check should use cache
        self.user.has_role = Mock(return_value=False)  # This shouldn't affect cached result
        assert self.permission.has_permission(request, self.view) is True
        
        # Test cache invalidation
        cache.delete(cache_key)
        with pytest.raises(AuthorizationException):
            self.permission.has_permission(request, self.view)

    @freeze_time("2023-01-01 00:00:00")
    def test_rate_limiting(self):
        """Test rate limiting for permission checks."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Simulate multiple permission checks
        for _ in range(MAX_PERMISSION_CHECKS):
            assert self.permission.has_permission(request, self.view) is True
        
        # Next check should fail rate limit
        with pytest.raises(AuthorizationException) as exc:
            self.permission.has_permission(request, self.view)
        assert "Rate limit exceeded" in str(exc.value)
        
        # Test rate limit reset
        with freeze_time("2023-01-01 00:01:00"):  # Advance 1 minute
            assert self.permission.has_permission(request, self.view) is True

    def test_security_audit_logging(self):
        """Test security event logging for permissions."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        with patch('core.permissions.logger') as mock_logger:
            self.permission.has_permission(request, self.view)
            
            # Verify audit log entry
            mock_logger.info.assert_called_with(
                "Permission granted",
                extra={
                    "user_id": self.user.id,
                    "role": self.user.role,
                    "view": self.view.__class__.__name__,
                    "method": request.method
                }
            )

@pytest.mark.django_db
class TestParticipantPermission:
    """Test cases for participant-specific permissions."""
    
    def setup_method(self):
        """Set up test environment for participant permission tests."""
        self.factory = APIRequestFactory()
        self.permission = ParticipantPermission()
        
        # Mock user and participation
        self.user = Mock(spec=User)
        self.user.id = '123'
        self.user.is_active = True
        self.user.role = 'participant'
        
        self.protocol = Mock()
        self.protocol.id = '456'
        
        self.participation = Mock()
        self.participation.protocol_id = self.protocol.id
        self.participation.user_id = self.user.id
        
        self.user.participation_set = Mock()
        self.user.participation_set.all.return_value = [self.participation]
        
        # Clear cache
        cache.clear()

    def test_has_object_permission_enrolled(self):
        """Test object permission for enrolled participant."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        data_point = Mock()
        data_point.protocol_id = self.protocol.id
        data_point.user_id = self.user.id
        
        assert self.permission.has_object_permission(request, None, data_point) is True
        
        # Verify cache was set
        cache_key = f'protocol_enrollment_{self.user.id}_{self.protocol.id}'
        assert cache.get(cache_key) is True

    def test_has_object_permission_not_enrolled(self):
        """Test object permission for non-enrolled participant."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        data_point = Mock()
        data_point.protocol_id = 'different_protocol'
        data_point.user_id = self.user.id
        
        with pytest.raises(AuthorizationException) as exc:
            self.permission.has_object_permission(request, None, data_point)
        assert "Not enrolled in protocol" in str(exc.value)

    def test_data_access_restrictions(self):
        """Test data access restrictions for participants."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        # Test accessing other user's data
        data_point = Mock()
        data_point.protocol_id = self.protocol.id
        data_point.user_id = 'different_user'
        
        with pytest.raises(AuthorizationException) as exc:
            self.permission.has_object_permission(request, None, data_point)
        assert "Cannot access other user's data" in str(exc.value)

    def test_enrollment_caching(self):
        """Test enrollment check caching behavior."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        data_point = Mock()
        data_point.protocol_id = self.protocol.id
        data_point.user_id = self.user.id
        
        # First check should cache result
        assert self.permission.has_object_permission(request, None, data_point) is True
        
        # Remove enrollment but keep cache
        self.user.participation_set.all.return_value = []
        
        # Should still return True due to cache
        assert self.permission.has_object_permission(request, None, data_point) is True