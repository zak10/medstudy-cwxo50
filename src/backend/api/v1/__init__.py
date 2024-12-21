"""
API v1 package initialization for the Medical Research Platform.
Configures the Django Ninja API router with comprehensive security, monitoring,
and validation features.

Version: 1.0.0
"""

import os
import logging
from typing import Dict, Any

from django_ninja import NinjaAPI  # v0.22.0
from prometheus_client import Counter, Histogram, start_http_server  # v0.16.0
import sentry_sdk  # v1.28.1
from django_ninja_jwt import JWTAuthMiddleware  # v0.10.0
from django_ninja_throttling import RateLimitMiddleware  # v0.1.0

from api.v1.views import api_router
from api.v1.urls import urlpatterns

# Configure logging
logger = logging.getLogger(__name__)

# Initialize API with security settings
api = NinjaAPI(
    title='Medical Research Platform API',
    version='1.0.0',
    urls_namespace='api_v1',
    auth=JWTAuthMiddleware(),
    docs_url='/docs',
    openapi_url='/openapi.json',
    middleware=[RateLimitMiddleware(rate='100/m')],
    csrf=True
)

# Prometheus metrics configuration
PROMETHEUS_METRICS = {
    'http_requests_total': Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    ),
    'http_request_duration_seconds': Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint']
    ),
    'data_validation_errors_total': Counter(
        'data_validation_errors_total',
        'Total data validation errors',
        ['endpoint', 'error_type']
    )
}

# Sentry configuration for error tracking
SENTRY_CONFIG = {
    'dsn': os.getenv('SENTRY_DSN'),
    'traces_sample_rate': 0.1,
    'profiles_sample_rate': 0.1,
    'environment': os.getenv('ENVIRONMENT', 'production'),
    'release': '1.0.0'
}

def init_monitoring() -> None:
    """
    Initializes monitoring systems including Prometheus and Sentry.
    Configures metrics collection and error tracking.
    """
    try:
        # Initialize Sentry SDK
        sentry_sdk.init(**SENTRY_CONFIG)
        
        # Start Prometheus metrics server
        start_http_server(port=9090)
        
        logger.info("Monitoring systems initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize monitoring: {str(e)}", exc_info=True)
        raise

@api.get("/health")
def health_check() -> Dict[str, Any]:
    """
    API health check endpoint with enhanced monitoring.
    
    Returns:
        Dict containing health status and metrics
    """
    try:
        health_metrics = {
            'status': 'healthy',
            'version': api.version,
            'metrics': {
                'requests_total': PROMETHEUS_METRICS['http_requests_total']._value.sum(),
                'avg_response_time': PROMETHEUS_METRICS['http_request_duration_seconds']._sum.sum()
            }
        }
        
        # Record health check in metrics
        PROMETHEUS_METRICS['http_requests_total'].labels(
            method='GET',
            endpoint='/health',
            status=200
        ).inc()
        
        return health_metrics
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

# Initialize monitoring on module load
init_monitoring()

# Register API routes
api.router = api_router

# Export package components
__all__ = [
    'api',
    'api_router',
    'urlpatterns',
    'PROMETHEUS_METRICS',
    'health_check'
]