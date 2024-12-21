"""
Core middleware components for the Medical Research Platform.
Implements secure request processing, authentication, logging, and error handling.

Version: 1.0.0
"""

from django.utils.deprecation import MiddlewareMixin  # version: ^4.2.0
from django.http import JsonResponse  # version: ^4.2.0
from django.conf import settings  # version: ^4.2.0
from pythonjsonlogger import jsonlogger  # version: ^2.0.7
from django_ratelimit import RateLimiter  # version: ^3.0.1
import uuid
import time
import logging
import json
import threading
from typing import Optional, Dict, Any, Union

from core.exceptions import BaseAPIException
from core.authentication import JWTAuthentication

# Thread-local storage for request context
request_context = threading.local()

# Configure JSON formatter for structured logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with enhanced security context."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Adds additional security and performance fields to log records."""
        super().add_fields(log_record, record, message_dict)
        log_record.update({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'environment': settings.ENVIRONMENT,
            'request_id': getattr(request_context, 'request_id', None),
            'user_id': getattr(request_context, 'user_id', None)
        })

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging all requests and responses with security context and performance metrics.
    Implements structured JSON logging with sensitive data masking.
    """

    def __init__(self, get_response=None):
        """Initialize logging middleware with security configurations."""
        super().__init__(get_response)
        
        # Configure logger
        self.logger = logging.getLogger('request_logger')
        formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(message)s %(environment)s %(request_id)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Sensitive data patterns for masking
        self.sensitive_fields = {
            'password', 'token', 'secret', 'key', 'authorization',
            'credit_card', 'ssn', 'social_security'
        }

    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Masks sensitive information in request/response data."""
        if not isinstance(data, dict):
            return data
            
        masked_data = data.copy()
        for key, value in data.items():
            if any(field in key.lower() for field in self.sensitive_fields):
                masked_data[key] = '[REDACTED]'
            elif isinstance(value, dict):
                masked_data[key] = self.mask_sensitive_data(value)
        return masked_data

    def process_request(self, request) -> None:
        """
        Processes and logs incoming requests with security context.
        
        Args:
            request: The incoming HTTP request
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request_context.request_id = request_id
        request_context.start_time = time.time()
        
        # Extract request metadata
        meta = {
            'method': request.method,
            'path': request.path,
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'content_length': request.META.get('CONTENT_LENGTH'),
            'query_params': dict(request.GET.items())
        }
        
        # Mask sensitive data
        if request.content_type == 'application/json' and request.body:
            try:
                body = json.loads(request.body)
                meta['body'] = self.mask_sensitive_data(body)
            except json.JSONDecodeError:
                meta['body'] = '[Invalid JSON]'
                
        self.logger.info(
            'Request received',
            extra={
                'request_id': request_id,
                'request_meta': meta
            }
        )

    def process_response(self, request, response) -> JsonResponse:
        """
        Processes and logs responses with performance metrics.
        
        Args:
            request: The HTTP request
            response: The HTTP response
            
        Returns:
            The processed response
        """
        duration = time.time() - getattr(request_context, 'start_time', time.time())
        
        # Extract response metadata
        meta = {
            'status_code': response.status_code,
            'content_type': response.get('Content-Type'),
            'duration_ms': int(duration * 1000)
        }
        
        # Mask sensitive response data
        if hasattr(response, 'data'):
            meta['response_data'] = self.mask_sensitive_data(response.data)
            
        self.logger.info(
            'Response completed',
            extra={
                'request_id': getattr(request_context, 'request_id', None),
                'response_meta': meta
            }
        )
        
        # Cleanup thread local storage
        for attr in ('request_id', 'start_time', 'user_id'):
            try:
                delattr(request_context, attr)
            except AttributeError:
                pass
                
        return response

class JWTAuthMiddleware(MiddlewareMixin):
    """
    Middleware for JWT authentication with rate limiting and role-based access control.
    Implements token validation and security auditing.
    """

    def __init__(self, get_response=None):
        """Initialize authentication middleware with security controls."""
        super().__init__(get_response)
        self.auth_handler = JWTAuthentication()
        self.logger = logging.getLogger('auth_logger')
        
        # Configure rate limiter
        self.rate_limiter = RateLimiter(
            key='ip',
            rate='100/m',
            block=True
        )
        
        # Protected paths requiring authentication
        self.protected_paths = getattr(settings, 'PROTECTED_PATHS', [
            '/api/v1/protocols',
            '/api/v1/data',
            '/api/v1/user'
        ])

    def process_request(self, request) -> Optional[JsonResponse]:
        """
        Validates JWT tokens and enforces access control.
        
        Args:
            request: The HTTP request
            
        Returns:
            JsonResponse if authentication fails, None otherwise
        """
        # Skip authentication for unprotected paths
        if not any(request.path.startswith(path) for path in self.protected_paths):
            return None
            
        try:
            # Apply rate limiting
            self.rate_limiter.validate_request(request)
            
            # Authenticate request
            auth_result = self.auth_handler.authenticate(request)
            if auth_result is None:
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )
                
            user, token = auth_result
            request.user = user
            request_context.user_id = str(user.id)
            
            # Log successful authentication
            self.logger.info(
                'Authentication successful',
                extra={
                    'user_id': str(user.id),
                    'request_id': getattr(request_context, 'request_id', None)
                }
            )
            
        except BaseAPIException as e:
            return JsonResponse(
                e.to_dict(),
                status=e.status_code
            )
            
        except Exception as e:
            self.logger.error(
                f'Authentication error: {str(e)}',
                extra={'request_id': getattr(request_context, 'request_id', None)}
            )
            return JsonResponse(
                {'error': 'Authentication failed'},
                status=500
            )

class ExceptionMiddleware(MiddlewareMixin):
    """
    Middleware for handling exceptions with security classification and error tracking.
    Implements standardized error responses and logging.
    """

    def __init__(self, get_response=None):
        """Initialize exception middleware with error tracking."""
        super().__init__(get_response)
        self.logger = logging.getLogger('error_logger')
        
        # Error classification rules
        self.error_classifications = {
            'ValidationError': {'level': 'WARNING', 'status': 400},
            'AuthenticationError': {'level': 'WARNING', 'status': 401},
            'PermissionError': {'level': 'WARNING', 'status': 403},
            'NotFound': {'level': 'INFO', 'status': 404},
            'Default': {'level': 'ERROR', 'status': 500}
        }

    def process_exception(self, request, exception: Exception) -> JsonResponse:
        """
        Processes exceptions with security context and standardized formatting.
        
        Args:
            request: The HTTP request
            exception: The raised exception
            
        Returns:
            Formatted error response
        """
        # Get error classification
        error_class = type(exception).__name__
        classification = self.error_classifications.get(
            error_class,
            self.error_classifications['Default']
        )
        
        # Format error response
        if isinstance(exception, BaseAPIException):
            error_data = exception.to_dict()
            status_code = exception.status_code
        else:
            error_data = {
                'message': str(exception),
                'error_code': f'ERR-{str(uuid.uuid4())[:8]}',
                'status_code': classification['status']
            }
            status_code = classification['status']
            
        # Log error with context
        self.logger.log(
            getattr(logging, classification['level']),
            f'Request error: {str(exception)}',
            extra={
                'error_data': error_data,
                'request_id': getattr(request_context, 'request_id', None),
                'user_id': getattr(request_context, 'user_id', None)
            }
        )
        
        return JsonResponse(
            error_data,
            status=status_code
        )