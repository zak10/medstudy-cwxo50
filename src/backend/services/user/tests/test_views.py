"""
Test suite for user service API views with comprehensive security validation.
Implements test cases for user registration, authentication, profile management,
MFA configuration, rate limiting and security features.

Version: 1.0.0
"""

from rest_framework.test import APITestCase  # version: ^3.14.0
from rest_framework import status  # version: ^3.14.0
from django.urls import reverse  # version: ^4.2.0
from unittest.mock import patch  # version: ^3.11.0
from django.core.cache import cache
from django.conf import settings
import jwt
import json

from services.user.models import User
from services.user.views import UserViewSet
from core.exceptions import AuthenticationException

class UserViewSetTestCase(APITestCase):
    """
    Comprehensive test suite for UserViewSet endpoints with security validation.
    Tests user registration, authentication, profile management and MFA features.
    """

    def setUp(self):
        """Initialize test environment with security configurations."""
        # Clear cache
        cache.clear()

        # Set up test URLs
        self.register_url = reverse('user-register')
        self.login_url = reverse('user-login')
        self.profile_url = reverse('user-profile')
        self.mfa_setup_url = reverse('user-setup-mfa')
        self.mfa_verify_url = reverse('user-verify-mfa')

        # Set up test data
        self.valid_user_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'participant'
        }

        self.valid_profile_data = {
            'bio': 'Test bio',
            'location': 'Test City',
            'preferences': {
                'notifications': True,
                'two_factor_auth': False
            }
        }

        self.mfa_test_data = {
            'secret': 'BASE32ENCODEDTESTSTRINGFORTOTP',
            'valid_code': '123456',
            'backup_codes': ['12345678', '87654321']
        }

        # Set up security headers
        self.client.defaults['HTTP_USER_AGENT'] = 'Test Browser'
        self.client.defaults['REMOTE_ADDR'] = '127.0.0.1'

    def test_register_success(self):
        """Test successful user registration with security validation."""
        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

        # Verify user creation
        user = User.objects.get(email=self.valid_user_data['email'])
        self.assertEqual(user.first_name, self.valid_user_data['first_name'])
        self.assertEqual(user.role, 'participant')

        # Verify password hashing
        self.assertNotEqual(user.password, self.valid_user_data['password'])
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))

    def test_register_validation(self):
        """Test registration input validation and security checks."""
        # Test weak password
        weak_password_data = self.valid_user_data.copy()
        weak_password_data['password'] = 'weak'
        weak_password_data['password_confirm'] = 'weak'

        response = self.client.post(
            self.register_url,
            weak_password_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['details']['fields'])

        # Test email uniqueness
        User.objects.create_user(
            email=self.valid_user_data['email'],
            password='TestPass123!',
            first_name='Existing',
            last_name='User'
        )

        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['details']['fields'])

    @patch('services.user.views.UserViewSet.check_rate_limit')
    def test_register_rate_limit(self, mock_rate_limit):
        """Test registration rate limiting."""
        # Simulate rate limit exceeded
        mock_rate_limit.return_value = False

        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Retry-After', response)

    def test_login_success(self):
        """Test successful login with security validation."""
        # Create test user
        user = User.objects.create_user(
            email=self.valid_user_data['email'],
            password=self.valid_user_data['password'],
            first_name=self.valid_user_data['first_name'],
            last_name=self.valid_user_data['last_name']
        )

        response = self.client.post(
            self.login_url,
            {
                'email': self.valid_user_data['email'],
                'password': self.valid_user_data['password']
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

        # Verify JWT token
        token = response.data['token']
        decoded = jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=['RS256'],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        self.assertEqual(decoded['sub'], str(user.id))

    def test_login_mfa_required(self):
        """Test MFA requirement during login."""
        # Create user with MFA enabled
        user = User.objects.create_user(
            email=self.valid_user_data['email'],
            password=self.valid_user_data['password'],
            first_name=self.valid_user_data['first_name'],
            last_name=self.valid_user_data['last_name']
        )
        user.mfa_enabled = True
        user.mfa_secret = self.mfa_test_data['secret']
        user.save()

        response = self.client.post(
            self.login_url,
            {
                'email': self.valid_user_data['email'],
                'password': self.valid_user_data['password']
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('requires_verification', response.data)
        self.assertTrue(response.data['requires_verification'])
        self.assertNotIn('token', response.data)

    @patch('services.user.views.UserViewSet.detect_suspicious_activity')
    def test_login_suspicious_activity(self, mock_detect):
        """Test suspicious activity detection during login."""
        # Simulate suspicious activity
        mock_detect.return_value = True

        response = self.client.post(
            self.login_url,
            {
                'email': self.valid_user_data['email'],
                'password': self.valid_user_data['password']
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('security_alert', response.data)

    def test_update_profile_security(self):
        """Test profile update with security validation."""
        # Create and authenticate user
        user = User.objects.create_user(
            email=self.valid_user_data['email'],
            password=self.valid_user_data['password'],
            first_name=self.valid_user_data['first_name'],
            last_name=self.valid_user_data['last_name']
        )
        self.client.force_authenticate(user=user)

        # Test profile update with sensitive data
        sensitive_data = self.valid_profile_data.copy()
        sensitive_data['password'] = 'sensitive'
        sensitive_data['token'] = 'sensitive'

        response = self.client.put(
            f'/api/users/{user.id}/update_profile/',
            sensitive_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data['profile'])
        self.assertNotIn('token', response.data['profile'])

    def test_mfa_setup_validation(self):
        """Test MFA setup security validation."""
        # Create and authenticate user
        user = User.objects.create_user(
            email=self.valid_user_data['email'],
            password=self.valid_user_data['password'],
            first_name=self.valid_user_data['first_name'],
            last_name=self.valid_user_data['last_name']
        )
        self.client.force_authenticate(user=user)

        # Test initial MFA setup
        response = self.client.post(
            f'/api/users/{user.id}/setup_mfa/',
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('secret', response.data)
        self.assertIn('qr_code', response.data)

        # Test MFA activation with valid code
        response = self.client.post(
            f'/api/users/{user.id}/setup_mfa/',
            {
                'mfa_secret': response.data['secret'],
                'setup_code': self.mfa_test_data['valid_code']
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('backup_codes', response.data)
        self.assertEqual(len(response.data['backup_codes']), 10)

        # Verify MFA enabled
        user.refresh_from_db()
        self.assertTrue(user.mfa_enabled)
        self.assertIsNotNone(user.mfa_secret)

    def test_mfa_verify_rate_limit(self):
        """Test rate limiting on MFA verification."""
        # Create user with MFA enabled
        user = User.objects.create_user(
            email=self.valid_user_data['email'],
            password=self.valid_user_data['password'],
            first_name=self.valid_user_data['first_name'],
            last_name=self.valid_user_data['last_name']
        )
        user.mfa_enabled = True
        user.mfa_secret = self.mfa_test_data['secret']
        user.save()

        # Test multiple failed attempts
        for _ in range(6):
            response = self.client.post(
                self.mfa_verify_url,
                {
                    'user_id': str(user.id),
                    'token': '000000'
                },
                format='json'
            )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Retry-After', response)

    def tearDown(self):
        """Clean up test environment."""
        cache.clear()
        User.objects.all().delete()