"""
Test suite for core middleware components including request logging, JWT authentication,
and exception handling middleware with comprehensive security and compliance testing.

Version: 1.0.0
"""

import pytest  # version: ^7.4.0
from unittest.mock import Mock, patch, MagicMock  # version: ^4.0.0
from django.http import JsonResponse  # version: ^4.2.0
from django.test import RequestFactory  # version: ^4.2.0
import json
import time
import jwt
from datetime import datetime, timedelta

from core.middleware import RequestLoggingMiddleware, JWTAuthMiddleware, ExceptionMiddleware
from core.exceptions import BaseAPIException
from services.user.models import User

class TestRequestLoggingMiddleware:
    """Test cases for request logging middleware with security and compliance features."""

    @pytest.fixture
    def setup(self):
        """Set up test environment with security context."""
        self.factory = RequestFactory()
        self.middleware = RequestLoggingMiddleware()
        self.logger_mock = Mock()
        self.middleware.logger = self.logger_mock

    def test_process_request_logging(self, setup):
        """Test request logging with security headers and PII masking."""
        # Create test request with sensitive data
        request = self.factory.post(
            '/api/v1/user',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'secret123',
                'credit_card': '4111-1111-1111-1111'
            }),
            content_type='application/json'
        )
        request.META['HTTP_X_FORWARDED_FOR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'

        # Process request
        self.middleware.process_request(request)

        # Verify logging call
        self.logger_mock.info.assert_called_once()
        log_call = self.logger_mock.info.call_args[1]['extra']
        
        # Verify request ID generation
        assert 'request_id' in log_call
        assert isinstance(log_call['request_id'], str)
        
        # Verify PII masking
        request_meta = log_call['request_meta']
        assert request_meta['body']['password'] == '[REDACTED]'
        assert request_meta['body']['credit_card'] == '[REDACTED]'
        assert request_meta['body']['email'] == 'test@example.com'  # Email not masked

    def test_sensitive_data_masking(self, setup):
        """Test comprehensive PII/PHI data masking patterns."""
        sensitive_data = {
            'password': 'secret123',
            'token': 'abc123',
            'credit_card_number': '4111-1111-1111-1111',
            'ssn': '123-45-6789',
            'api_key': 'key123',
            'safe_field': 'visible data',
            'nested': {
                'secret_key': 'hidden',
                'public_key': 'visible'
            }
        }

        masked_data = self.middleware.mask_sensitive_data(sensitive_data)

        # Verify masking patterns
        assert masked_data['password'] == '[REDACTED]'
        assert masked_data['token'] == '[REDACTED]'
        assert masked_data['credit_card_number'] == '[REDACTED]'
        assert masked_data['ssn'] == '[REDACTED]'
        assert masked_data['api_key'] == '[REDACTED]'
        assert masked_data['safe_field'] == 'visible data'
        assert masked_data['nested']['secret_key'] == '[REDACTED]'
        assert masked_data['nested']['public_key'] == 'visible'

    def test_performance_metrics(self, setup):
        """Test performance logging and metrics collection."""
        request = self.factory.get('/api/v1/protocols')
        response = JsonResponse({'status': 'success'})

        # Add artificial delay
        time.sleep(0.1)
        
        # Process response
        processed_response = self.middleware.process_response(request, response)

        # Verify metrics logging
        log_call = self.logger_mock.info.call_args[1]['extra']
        response_meta = log_call['response_meta']
        
        # Verify timing metrics
        assert 'duration_ms' in response_meta
        assert response_meta['duration_ms'] >= 100  # At least 100ms
        assert response_meta['status_code'] == 200
        assert response_meta['content_type'] == 'application/json'


class TestJWTAuthMiddleware:
    """Test cases for JWT authentication middleware with security features."""

    @pytest.fixture
    def setup(self):
        """Set up test environment with JWT context."""
        self.factory = RequestFactory()
        self.middleware = JWTAuthMiddleware()
        self.user = Mock(spec=User)
        self.user.id = '123'
        self.user.is_active = True

    @patch('core.middleware.JWTAuthentication.authenticate')
    def test_expired_token_handling(self, mock_authenticate, setup):
        """Test handling of expired JWT tokens."""
        # Create request with expired token
        request = self.factory.get('/api/v1/protocols')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer expired.token.here'

        # Mock authentication failure
        mock_authenticate.side_effect = BaseAPIException(
            message="Token has expired",
            details={"token_status": "expired"},
            status_code=401
        )

        # Process request
        response = self.middleware.process_request(request)

        # Verify response
        assert response.status_code == 401
        response_data = json.loads(response.content)
        assert response_data['message'] == 'Token has expired'
        assert response_data['details']['token_status'] == 'expired'

    @patch('django_ratelimit.decorators.RateLimiter.validate_request')
    def test_rate_limit_exceeded(self, mock_validate, setup):
        """Test rate limiting functionality."""
        # Create test request
        request = self.factory.get('/api/v1/protocols')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer valid.token.here'

        # Mock rate limit exceeded
        mock_validate.side_effect = BaseAPIException(
            message="Rate limit exceeded",
            details={"retry_after": "60 seconds"},
            status_code=429
        )

        # Process request
        response = self.middleware.process_request(request)

        # Verify rate limit response
        assert response.status_code == 429
        response_data = json.loads(response.content)
        assert response_data['message'] == 'Rate limit exceeded'
        assert response_data['details']['retry_after'] == '60 seconds'

    @patch('core.middleware.JWTAuthentication.authenticate')
    def test_role_based_access(self, mock_authenticate, setup):
        """Test RBAC validation in JWT processing."""
        # Create request with role-specific token
        request = self.factory.get('/api/v1/protocols')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer token.with.roles'

        # Mock successful authentication with roles
        self.user.role = 'protocol_creator'
        mock_authenticate.return_value = (self.user, 'valid.token')

        # Process request
        response = self.middleware.process_request(request)

        # Verify successful authentication
        assert response is None  # No response means success
        assert hasattr(request, 'user')
        assert request.user.role == 'protocol_creator'


class TestExceptionMiddleware:
    """Test cases for exception handling middleware."""

    @pytest.fixture
    def setup(self):
        """Set up test environment for exception handling."""
        self.factory = RequestFactory()
        self.middleware = ExceptionMiddleware()

    def test_api_exception_handling(self, setup):
        """Test handling of BaseAPIException with security context."""
        request = self.factory.get('/api/v1/protocols')
        exception = BaseAPIException(
            message="Test error",
            details={"error_type": "validation"},
            status_code=400
        )

        # Process exception
        response = self.middleware.process_exception(request, exception)

        # Verify response
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data['message'] == 'Test error'
        assert response_data['details']['error_type'] == 'validation'
        assert 'error_code' in response_data

    def test_security_exception_classification(self, setup):
        """Test security-related exception classification."""
        request = self.factory.get('/api/v1/protocols')
        
        # Test different security exceptions
        security_exceptions = {
            'AuthenticationError': 401,
            'PermissionError': 403,
            'ValidationError': 400
        }

        for error_type, status_code in security_exceptions.items():
            exception = type(error_type, (Exception,), {})()
            response = self.middleware.process_exception(request, exception)
            
            assert response.status_code == status_code
            response_data = json.loads(response.content)
            assert 'error_code' in response_data