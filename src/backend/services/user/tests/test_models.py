"""
Test suite for User model and UserManager implementations.
Tests user creation, authentication, role-based access control, and security features.

Version: 1.0.0
"""

import pytest
from django.core.exceptions import ValidationError  # version: 4.2.0
from freezegun import freeze_time  # version: 1.2.0
from services.user.models import User, ROLE_CHOICES
import json
import re

pytestmark = pytest.mark.django_db

class UserModelTestCase:
    """Comprehensive test case class for User model security features."""
    
    @pytest.fixture
    def valid_user_data(self):
        """Fixture providing valid test user data."""
        return {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'profile': {
                'age': 30,
                'location': 'Test City',
                'preferences': {'notifications': True}
            }
        }

def test_create_user(valid_user_data):
    """Test user creation with comprehensive validation of security features."""
    # Create user with valid data
    user = User.objects.create_user(
        email=valid_user_data['email'],
        password=valid_user_data['password'],
        first_name=valid_user_data['first_name'],
        last_name=valid_user_data['last_name'],
        profile=valid_user_data['profile']
    )

    # Verify email normalization and case sensitivity
    assert user.email == valid_user_data['email'].lower()
    assert User.objects.filter(email=valid_user_data['email'].upper()).first() == user

    # Verify password is properly hashed (not stored in plaintext)
    assert user.password != valid_user_data['password']
    assert user.password.startswith('argon2')

    # Verify default role assignment
    assert user.role == 'participant'
    assert user.has_role('participant')
    assert not user.has_role('admin')

    # Verify profile sanitization
    assert 'password' not in user.profile
    assert 'secret' not in user.profile
    assert user.profile['age'] == 30

    # Verify MFA is initially disabled
    assert not user.mfa_enabled
    assert user.mfa_secret is None

    # Verify timestamps
    assert user.created_at is not None
    assert user.updated_at is not None

def test_create_user_invalid_email():
    """Test user creation security validations."""
    invalid_emails = [
        '',  # Empty email
        'invalid',  # No domain
        'test@',  # Incomplete domain
        'test@.com',  # Invalid domain
        'test@domain.',  # Invalid TLD
        'test@domain.c',  # TLD too short
        'test@@domain.com',  # Double @
        'test@domain..com',  # Double dot
        'test@domain.com;drop table users',  # SQL injection attempt
        'a' * 246 + '@domain.com'  # Email too long
    ]

    for invalid_email in invalid_emails:
        with pytest.raises(ValueError) as exc_info:
            User.objects.create_user(
                email=invalid_email,
                password='SecurePass123!',
                first_name='Test',
                last_name='User'
            )
        assert 'Invalid email' in str(exc_info.value)

def test_user_profile_json():
    """Test secure JSON profile field handling."""
    # Test valid profile data
    user = User.objects.create_user(
        email='profile@test.com',
        password='SecurePass123!',
        first_name='Profile',
        last_name='Test',
        profile={
            'bio': 'Test bio',
            'preferences': {'theme': 'dark'},
            'metadata': {'last_login_ip': '127.0.0.1'}
        }
    )

    # Verify profile sanitization
    assert 'password' not in user.profile
    assert 'secret' not in user.profile
    assert 'token' not in user.profile
    assert 'key' not in user.profile

    # Test profile update
    user.profile['new_field'] = 'test value'
    user.save()
    
    # Verify updated profile
    user.refresh_from_db()
    assert user.profile['new_field'] == 'test value'
    assert isinstance(user.profile, dict)

@freeze_time('2024-01-01 12:00:00')
def test_user_timestamps():
    """Test secure timestamp handling."""
    user = User.objects.create_user(
        email='time@test.com',
        password='SecurePass123!',
        first_name='Time',
        last_name='Test'
    )

    initial_created = user.created_at
    initial_updated = user.updated_at

    # Verify initial timestamps
    assert user.created_at.isoformat() == '2024-01-01T12:00:00+00:00'
    assert user.updated_at.isoformat() == '2024-01-01T12:00:00+00:00'

    # Update user and verify timestamps
    with freeze_time('2024-01-01 13:00:00'):
        user.first_name = 'Updated'
        user.save()
        
        # Verify created_at remains unchanged while updated_at changes
        assert user.created_at == initial_created
        assert user.updated_at > initial_updated
        assert user.updated_at.isoformat() == '2024-01-01T13:00:00+00:00'

def test_mfa_functionality():
    """Test MFA implementation security."""
    user = User.objects.create_user(
        email='mfa@test.com',
        password='SecurePass123!',
        first_name='MFA',
        last_name='Test'
    )

    # Verify initial MFA state
    assert not user.mfa_enabled
    assert user.mfa_secret is None

    # Test MFA secret format when enabled
    user.mfa_secret = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
    user.mfa_enabled = True
    user.save()

    # Verify MFA state after enabling
    assert user.mfa_enabled
    assert len(user.mfa_secret) == 32
    assert re.match(r'^[A-Z2-7]+$', user.mfa_secret)

def test_user_role_management():
    """Test role-based access control implementation."""
    user = User.objects.create_user(
        email='roles@test.com',
        password='SecurePass123!',
        first_name='Role',
        last_name='Test'
    )

    # Test default role
    assert user.role == 'participant'
    assert user.has_role('participant')

    # Test role validation
    with pytest.raises(ValueError):
        user.role = 'invalid_role'
        user.save()

    # Test valid role change
    valid_roles = dict(ROLE_CHOICES).keys()
    for role in valid_roles:
        user.role = role
        user.save()
        assert user.has_role(role)

    # Test superuser roles
    superuser = User.objects.create_superuser(
        email='admin@test.com',
        password='SecurePass123!',
        first_name='Admin',
        last_name='User'
    )
    
    # Verify superuser has all roles
    for role in valid_roles:
        assert superuser.has_role(role)