"""
Test suite for JWT and MFA authentication implementations in the Medical Research Platform.
Tests cover token validation, expiry, rate limiting, and MFA verification scenarios.

Version: 1.0.0
"""

import pytest  # version: 7.4.0
from freezegun import freeze_time  # version: 1.2.0
import jwt  # version: 2.7.0
import pyotp  # version: 2.8.0
from redis import Redis  # version: 4.5.0
from datetime import datetime, timedelta
import json
from unittest.mock import patch

from core.authentication import JWTAuthentication, MFAAuthentication
from core.exceptions import AuthenticationException
from services.user.models import User

class TestJWTAuthentication:
    """Test suite for JWT authentication functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Set up test environment before each test."""
        self.auth_handler = JWTAuthentication()
        self.redis_client = Redis(decode_responses=True)
        
        # Create test user
        self.test_user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User"
        )
        
        # Standard token payload
        self.token_payload = {
            'sub': str(self.test_user.id),
            'email': self.test_user.email,
            'role': 'participant',
            'iss': 'medical-research-platform',
            'aud': 'mrp-api'
        }

    def teardown_method(self):
        """Clean up after each test."""
        self.test_user.delete()
        self.redis_client.flushdb()

    def test_jwt_authentication_valid_token(self):
        """Test successful JWT authentication with valid token."""
        # Generate valid token
        token = self.auth_handler.get_token(self.test_user)
        
        # Create mock request
        class MockRequest:
            def __init__(self, token):
                self.headers = {'Authorization': f'Bearer {token}'}
        
        request = MockRequest(token)
        
        # Test authentication
        user, auth_token = self.auth_handler.authenticate(request)
        
        assert user == self.test_user
        assert auth_token == token
        assert not self.redis_client.sismember('token_blacklist', token)

    def test_jwt_authentication_invalid_token(self):
        """Test JWT authentication failure scenarios."""
        invalid_tokens = [
            'invalid.token.format',
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.invalid',
            jwt.encode({'exp': datetime.utcnow() - timedelta(hours=1)}, 'invalid_key', algorithm='HS256')
        ]
        
        for token in invalid_tokens:
            request = type('MockRequest', (), {'headers': {'Authorization': f'Bearer {token}'}})
            
            with pytest.raises(AuthenticationException) as exc:
                self.auth_handler.authenticate(request)
            
            assert exc.value.status_code == 401
            assert "Invalid token" in str(exc.value)

    @freeze_time("2023-01-01 12:00:00")
    def test_jwt_token_expiry(self):
        """Test JWT token expiration handling."""
        token = self.auth_handler.get_token(self.test_user)
        request = type('MockRequest', (), {'headers': {'Authorization': f'Bearer {token}'}})
        
        # Token should be valid initially
        user, _ = self.auth_handler.authenticate(request)
        assert user == self.test_user
        
        # Advance time to just before expiry (59 minutes)
        with freeze_time("2023-01-01 12:59:00"):
            user, _ = self.auth_handler.authenticate(request)
            assert user == self.test_user
        
        # Advance time past expiry (61 minutes)
        with freeze_time("2023-01-01 13:01:00"):
            with pytest.raises(AuthenticationException) as exc:
                self.auth_handler.authenticate(request)
            assert "Token has expired" in str(exc.value)
            assert self.redis_client.sismember('token_blacklist', token)

    def test_token_blacklist(self):
        """Test token blacklisting functionality."""
        token = self.auth_handler.get_token(self.test_user)
        request = type('MockRequest', (), {'headers': {'Authorization': f'Bearer {token}'}})
        
        # Blacklist token
        assert self.auth_handler.blacklist_token(token)
        
        # Attempt authentication with blacklisted token
        with pytest.raises(AuthenticationException) as exc:
            self.auth_handler.authenticate(request)
        assert "Token has been revoked" in str(exc.value)

class TestMFAAuthentication:
    """Test suite for MFA functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Set up test environment before each test."""
        self.mfa_handler = MFAAuthentication()
        self.redis_client = Redis(decode_responses=True)
        
        # Create test user with MFA enabled
        self.test_user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User"
        )
        
        # Generate and set MFA secret
        self.test_secret, self.backup_codes = self.mfa_handler.generate_secret()
        self.test_user.mfa_secret = self.test_secret
        self.test_user.mfa_enabled = True
        self.test_user.save()
        
        # Store backup codes
        backup_codes_key = f'backup_codes:{self.test_user.id}'
        self.redis_client.sadd(backup_codes_key, *self.backup_codes)

    def teardown_method(self):
        """Clean up after each test."""
        self.test_user.delete()
        self.redis_client.flushdb()

    def test_mfa_verification_valid_token(self):
        """Test MFA verification with valid TOTP token."""
        # Generate valid TOTP token
        totp = pyotp.TOTP(self.test_secret)
        token = totp.now()
        
        device_info = {
            'device_id': 'test-device',
            'device_type': 'browser',
            'ip_address': '127.0.0.1'
        }
        
        # Verify token
        assert self.mfa_handler.verify_token(self.test_user, token, device_info)
        
        # Check device tracking
        device_key = f'mfa_devices:{self.test_user.id}'
        tracked_devices = self.redis_client.lrange(device_key, 0, -1)
        assert len(tracked_devices) == 1
        tracked_device = json.loads(tracked_devices[0])
        assert tracked_device['device_id'] == 'test-device'

    def test_mfa_verification_invalid_token(self):
        """Test MFA verification failure scenarios."""
        device_info = {'device_id': 'test-device'}
        
        # Test with invalid token
        with pytest.raises(AuthenticationException) as exc:
            self.mfa_handler.verify_token(self.test_user, "000000", device_info)
        assert "Invalid verification token" in str(exc.value)
        
        # Test rate limiting
        for _ in range(5):
            with pytest.raises(AuthenticationException):
                self.mfa_handler.verify_token(self.test_user, "000000", device_info)
        
        # Verify max attempts exceeded
        with pytest.raises(AuthenticationException) as exc:
            self.mfa_handler.verify_token(self.test_user, "000000", device_info)
        assert "Maximum verification attempts exceeded" in str(exc.value)

    def test_backup_codes(self):
        """Test backup code verification."""
        device_info = {'device_id': 'test-device'}
        
        # Use valid backup code
        assert self.mfa_handler.verify_token(self.test_user, self.backup_codes[0], device_info)
        
        # Verify backup code was consumed
        backup_codes_key = f'backup_codes:{self.test_user.id}'
        assert not self.redis_client.sismember(backup_codes_key, self.backup_codes[0])
        
        # Attempt to reuse backup code
        with pytest.raises(AuthenticationException):
            self.mfa_handler.verify_token(self.test_user, self.backup_codes[0], device_info)

    def test_generate_mfa_credentials(self):
        """Test MFA secret and backup code generation."""
        secret, backup_codes = self.mfa_handler.generate_secret()
        
        # Verify secret format
        assert len(secret) == 32
        assert pyotp.TOTP(secret).verify(pyotp.TOTP(secret).now())
        
        # Verify backup codes
        assert len(backup_codes) == 10
        assert all(len(code) >= 16 for code in backup_codes)
        assert len(set(backup_codes)) == 10  # All codes should be unique