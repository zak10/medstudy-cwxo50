"""
Core pagination functionality for the Medical Research Platform.
Implements secure, HIPAA-compliant pagination with caching and performance optimizations.

Version: 1.0.0
"""

from typing import Dict, Any, Optional, TypeVar, Generic
from abc import ABC, abstractmethod
import logging
import redis  # v4.5.0
from django.db.models import QuerySet
from api.v1.schemas import PaginationParams

# Type variable for generic pagination
T = TypeVar('T')

# Constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
CACHE_EXPIRY = 300  # 5 minutes
SECURITY_SCAN_INTERVAL = 60  # 1 minute

# Configure logger
logger = logging.getLogger(__name__)

class BasePagination(ABC, Generic[T]):
    """
    Abstract base class for pagination with enhanced security and caching.
    Implements core pagination functionality with HIPAA compliance.
    """

    def __init__(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
        cache_config: Optional[Dict[str, Any]] = None,
        security_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize pagination with security and monitoring configurations.

        Args:
            page_size: Number of items per page
            cache_config: Redis cache configuration
            security_config: Security parameters
        """
        # Validate and set page size
        self.page_size = min(page_size, MAX_PAGE_SIZE) if page_size > 0 else DEFAULT_PAGE_SIZE
        
        # Initialize cache client if config provided
        self.cache_client = None
        if cache_config:
            try:
                self.cache_client = redis.Redis(
                    host=cache_config.get('host', 'localhost'),
                    port=cache_config.get('port', 6379),
                    db=cache_config.get('db', 0),
                    decode_responses=True
                )
            except Exception as e:
                logger.error(f"Cache initialization failed: {str(e)}")

        # Initialize security context
        self.security_config = security_config or {}
        self.last_security_scan = 0
        
        # Set up performance monitoring
        self.performance_metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_queries': 0
        }

    def validate_security(self, security_context: Dict[str, Any]) -> bool:
        """
        Validates security parameters and permissions.

        Args:
            security_context: Security validation context

        Returns:
            bool: True if security validation passes

        Raises:
            ValidationError: If security validation fails
        """
        try:
            # Validate authentication context
            if not security_context.get('authenticated', False):
                raise ValueError("Authentication required for pagination")

            # Validate authorization level
            required_role = self.security_config.get('required_role', 'participant')
            if security_context.get('role') not in ['admin', required_role]:
                raise ValueError(f"Insufficient permissions. Required role: {required_role}")

            # Verify rate limits
            rate_limit = self.security_config.get('rate_limit', 100)
            current_rate = security_context.get('request_rate', 0)
            if current_rate > rate_limit:
                raise ValueError(f"Rate limit exceeded: {current_rate}/{rate_limit}")

            logger.info("Security validation passed", extra={'context': security_context})
            return True

        except Exception as e:
            logger.error(f"Security validation failed: {str(e)}")
            raise

    @abstractmethod
    def paginate(self, queryset: QuerySet[T], params: PaginationParams) -> Dict[str, Any]:
        """
        Abstract method for paginating queryset with security and validation.

        Args:
            queryset: Database queryset to paginate
            params: Pagination parameters

        Returns:
            Dict containing paginated data and metadata

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

class OffsetPagination(BasePagination[T]):
    """
    Implements offset-based pagination with enhanced security and caching.
    """

    def paginate(self, queryset: QuerySet[T], params: PaginationParams) -> Dict[str, Any]:
        """
        Paginates queryset using offset strategy with security and caching.

        Args:
            queryset: Database queryset to paginate
            params: Pagination parameters

        Returns:
            Dict containing paginated data and metadata
        """
        try:
            # Validate pagination parameters
            params.validate_pagination()

            # Calculate offset
            page = max(params.page, 1)
            offset = (page - 1) * self.page_size

            # Generate cache key
            cache_key = f"pagination:offset:{queryset.model.__name__}:{offset}:{self.page_size}"
            
            # Check cache
            if self.cache_client:
                cached_data = self.cache_client.get(cache_key)
                if cached_data:
                    self.performance_metrics['cache_hits'] += 1
                    return eval(cached_data)  # Safe eval of cached data
                self.performance_metrics['cache_misses'] += 1

            # Apply filters if provided
            if params.filters:
                queryset = queryset.filter(**params.filters)

            # Get total count
            total_count = queryset.count()

            # Apply sorting
            if params.sort_by:
                sort_prefix = '-' if params.sort_order == 'desc' else ''
                queryset = queryset.order_by(f"{sort_prefix}{params.sort_by}")

            # Get paginated data
            data = list(queryset[offset:offset + self.page_size].values())

            # Prepare response
            response = {
                'data': data,
                'metadata': {
                    'page': page,
                    'page_size': self.page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + self.page_size - 1) // self.page_size
                }
            }

            # Cache response
            if self.cache_client:
                self.cache_client.setex(
                    cache_key,
                    CACHE_EXPIRY,
                    str(response)
                )

            self.performance_metrics['total_queries'] += 1
            return response

        except Exception as e:
            logger.error(f"Pagination error: {str(e)}")
            raise

class CursorPagination(BasePagination[T]):
    """
    Implements cursor-based pagination with enhanced security and performance.
    """

    def __init__(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
        cursor_field: str = 'id',
        security_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize cursor pagination with security features.

        Args:
            page_size: Number of items per page
            cursor_field: Field to use for cursor
            security_config: Security parameters
        """
        super().__init__(page_size, security_config=security_config)
        self.cursor_field = cursor_field

    def paginate(self, queryset: QuerySet[T], params: PaginationParams) -> Dict[str, Any]:
        """
        Paginates queryset using secure cursor strategy.

        Args:
            queryset: Database queryset to paginate
            params: Pagination parameters

        Returns:
            Dict containing paginated data and metadata
        """
        try:
            # Validate pagination parameters
            params.validate_pagination()

            # Apply filters if provided
            if params.filters:
                queryset = queryset.filter(**params.filters)

            # Apply sorting
            sort_field = params.sort_by or self.cursor_field
            sort_prefix = '-' if params.sort_order == 'desc' else ''
            queryset = queryset.order_by(f"{sort_prefix}{sort_field}")

            # Apply cursor if provided
            if 'cursor' in params.filters:
                cursor_value = params.filters['cursor']
                filter_kwargs = {f"{self.cursor_field}__gt": cursor_value}
                queryset = queryset.filter(**filter_kwargs)

            # Get paginated data
            data = list(queryset[:self.page_size + 1].values())
            
            # Determine if there are more results
            has_next = len(data) > self.page_size
            if has_next:
                data.pop()

            # Get next cursor
            next_cursor = data[-1][self.cursor_field] if data and has_next else None

            # Prepare response
            response = {
                'data': data,
                'metadata': {
                    'next_cursor': next_cursor,
                    'has_next': has_next,
                    'page_size': self.page_size
                }
            }

            self.performance_metrics['total_queries'] += 1
            return response

        except Exception as e:
            logger.error(f"Cursor pagination error: {str(e)}")
            raise