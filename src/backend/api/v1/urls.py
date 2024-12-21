"""
URL routing configuration for v1 of the Medical Research Platform API.
Implements secure endpoint routing with rate limiting and monitoring.

Version: 1.0.0
"""

from django.urls import path, include  # v4.2.0
from django_ninja import NinjaAPI  # v0.22.0
from django.views.decorators.http import require_http_methods  # v4.2.0
from django_ratelimit.middleware import RateLimitMiddleware  # v3.0.0

from api.v1.views import api_router

# API configuration with security settings
api = NinjaAPI(
    title="Medical Research Platform API",
    version="1.0",
    description="API for community-driven medical research platform",
    docs_url="/api/v1/docs",
    csrf=True,
    auth=["jwt"],
    urls_namespace="api_v1"
)

# Rate limiting configuration per endpoint category
RATE_LIMIT_CONFIG = {
    "auth": "100/hour",  # Authentication endpoints
    "protocols": "1000/hour",  # Protocol operations
    "data": "5000/hour",  # Data submission
    "analysis": "500/hour",  # Analysis operations
    "community": "2000/hour"  # Community features
}

# Health check patterns
health_patterns = [
    path("", api_router.health_check, name="health_check"),
    path("metrics/", api_router.metrics, name="metrics"),
]

# Authentication patterns with rate limiting
auth_patterns = [
    path(
        "register/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["auth"])(api_router.register_user),
        name="register"
    ),
    path(
        "login/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["auth"])(api_router.login_user),
        name="login"
    ),
    path(
        "refresh/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["auth"])(api_router.refresh_token),
        name="refresh_token"
    ),
]

# Protocol management patterns
protocol_patterns = [
    path(
        "",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["protocols"])(api_router.create_protocol),
        name="create_protocol"
    ),
    path(
        "<uuid:id>/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["protocols"])(api_router.get_protocol),
        name="get_protocol"
    ),
    path(
        "<uuid:id>/enroll/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["protocols"])(api_router.enroll_protocol),
        name="enroll_protocol"
    ),
]

# Data collection patterns
data_patterns = [
    path(
        "",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["data"])(api_router.submit_data_point),
        name="submit_data"
    ),
    path(
        "<uuid:id>/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["data"])(api_router.get_data_point),
        name="get_data_point"
    ),
    path(
        "validate/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["data"])(api_router.validate_data),
        name="validate_data"
    ),
]

# Analysis patterns
analysis_patterns = [
    path(
        "<uuid:protocol_id>/results/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["analysis"])(api_router.get_protocol_results),
        name="protocol_results"
    ),
    path(
        "<uuid:protocol_id>/trends/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["analysis"])(api_router.get_protocol_trends),
        name="protocol_trends"
    ),
]

# Community patterns
community_patterns = [
    path(
        "forums/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["community"])(api_router.list_forums),
        name="list_forums"
    ),
    path(
        "forums/<uuid:id>/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["community"])(api_router.forum_detail),
        name="forum_detail"
    ),
    path(
        "messages/",
        RateLimitMiddleware(RATE_LIMIT_CONFIG["community"])(api_router.list_messages),
        name="list_messages"
    ),
]

# Main URL patterns with versioning
app_name = "api_v1"
urlpatterns = [
    # Health monitoring endpoints
    path("health/", include((health_patterns, "health"))),
    
    # Core API endpoints with rate limiting
    path("auth/", include((auth_patterns, "auth"))),
    path("protocols/", include((protocol_patterns, "protocols"))),
    path("data-points/", include((data_patterns, "data"))),
    path("analysis/", include((analysis_patterns, "analysis"))),
    path("community/", include((community_patterns, "community"))),
]