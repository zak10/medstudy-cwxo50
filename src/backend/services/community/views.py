"""
API views for community features in the Medical Research Platform.
Implements forum management, thread operations, and moderation capabilities
with enhanced security controls and performance optimization.

Version: 1.0.0
"""

from rest_framework.views import APIView  # version ^3.14.0
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.pagination import CursorPagination
from rest_framework import status
from django.core.cache import cache  # version ^4.2.0
from django.db import transaction
from django_audit_logger import AuditLogger  # version ^1.0.0
import logging

from services.community.models import Forum, Thread
from core.exceptions import ValidationException
from core.utils import sanitize_html

# Configure logger
logger = logging.getLogger(__name__)

# Cache configuration
FORUM_CACHE_TTL = 300  # 5 minutes
THREAD_CACHE_TTL = 300  # 5 minutes

class CommunityPagination(CursorPagination):
    """
    Cursor-based pagination for community content with performance optimization.
    """
    page_size = 20
    ordering = '-created_at'
    max_page_size = 100

class ParticipantPermission(IsAuthenticated):
    """
    Permission class to verify active participant status.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_active and request.user.has_role('participant')

class ForumViewSet(APIView):
    """
    API view for managing forums with caching and moderation support.
    Implements CRUD operations with security controls and audit logging.
    """
    
    permission_classes = [ParticipantPermission]
    throttle_classes = [UserRateThrottle]
    pagination_class = CommunityPagination
    audit_logger = AuditLogger('community')

    def get_cache_key(self, **kwargs):
        """
        Generates cache key for forum data.
        """
        base_key = 'forum'
        if kwargs:
            params = '-'.join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            return f"{base_key}:{params}"
        return base_key

    def list(self, request):
        """
        Lists forums with caching and filtering support.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Paginated list of forums
        """
        try:
            # Extract filter parameters
            protocol_id = request.query_params.get('protocol_id')
            is_active = request.query_params.get('is_active', 'true').lower() == 'true'
            
            # Generate cache key
            cache_key = self.get_cache_key(
                protocol_id=protocol_id,
                is_active=is_active,
                page=request.query_params.get('cursor', '')
            )
            
            # Check cache
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for forums: {cache_key}")
                return Response(cached_data)
            
            # Build queryset with filters
            queryset = Forum.objects.all()
            if protocol_id:
                queryset = queryset.filter(protocol_id=protocol_id)
            queryset = queryset.filter(is_active=is_active)
            
            # Apply pagination
            paginator = self.pagination_class()
            paginated_forums = paginator.paginate_queryset(queryset, request)
            
            # Prepare response data
            response_data = {
                'results': [
                    {
                        'id': str(forum.id),
                        'name': forum.name,
                        'description': forum.description,
                        'is_protocol_specific': forum.is_protocol_specific,
                        'protocol_id': str(forum.protocol_id) if forum.protocol_id else None,
                        'is_active': forum.is_active,
                        'created_at': forum.created_at.isoformat(),
                        'updated_at': forum.updated_at.isoformat()
                    }
                    for forum in paginated_forums
                ],
                'pagination': {
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link()
                }
            }
            
            # Cache the response
            cache.set(cache_key, response_data, FORUM_CACHE_TTL)
            logger.info("Forums retrieved successfully")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error listing forums: {str(e)}")
            raise ValidationException("Failed to retrieve forums", details={'error': str(e)})

    @transaction.atomic
    def create(self, request):
        """
        Creates a new forum with content moderation.
        
        Args:
            request: HTTP request object with forum data
            
        Returns:
            Response: Created forum data
        """
        try:
            # Validate request data
            required_fields = ['name', 'description']
            for field in required_fields:
                if field not in request.data:
                    raise ValidationException(f"Missing required field: {field}")
            
            # Sanitize content
            description = sanitize_html(request.data['description'])
            
            # Create forum instance
            forum = Forum(
                name=request.data['name'],
                description=description,
                is_protocol_specific=request.data.get('is_protocol_specific', False),
                protocol_id=request.data.get('protocol_id'),
                is_active=True
            )
            
            # Validate and save
            forum.save()
            
            # Audit logging
            self.audit_logger.log_action(
                user=request.user,
                action='forum_created',
                resource_id=str(forum.id),
                details={
                    'name': forum.name,
                    'is_protocol_specific': forum.is_protocol_specific
                }
            )
            
            # Invalidate cache
            cache.delete(self.get_cache_key())
            
            # Prepare response
            response_data = {
                'id': str(forum.id),
                'name': forum.name,
                'description': forum.description,
                'is_protocol_specific': forum.is_protocol_specific,
                'protocol_id': str(forum.protocol_id) if forum.protocol_id else None,
                'is_active': forum.is_active,
                'created_at': forum.created_at.isoformat(),
                'updated_at': forum.updated_at.isoformat()
            }
            
            logger.info(f"Forum created successfully: {forum.id}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValidationException as ve:
            logger.warning(f"Validation error creating forum: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error creating forum: {str(e)}")
            raise ValidationException("Failed to create forum", details={'error': str(e)})

class ThreadViewSet(APIView):
    """
    API view for managing forum threads with view tracking and moderation.
    Implements CRUD operations with security controls and performance optimization.
    """
    
    permission_classes = [ParticipantPermission]
    throttle_classes = [UserRateThrottle]
    pagination_class = CommunityPagination
    audit_logger = AuditLogger('community')

    def get_cache_key(self, forum_id, **kwargs):
        """
        Generates cache key for thread data.
        """
        base_key = f'thread:forum:{forum_id}'
        if kwargs:
            params = '-'.join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            return f"{base_key}:{params}"
        return base_key

    def list(self, request, forum_id):
        """
        Lists threads for a forum with caching support.
        
        Args:
            request: HTTP request object
            forum_id: UUID of the forum
            
        Returns:
            Response: Paginated list of threads
        """
        try:
            # Generate cache key
            cache_key = self.get_cache_key(
                forum_id,
                page=request.query_params.get('cursor', '')
            )
            
            # Check cache
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for threads: {cache_key}")
                return Response(cached_data)
            
            # Get forum and validate
            try:
                forum = Forum.objects.get(id=forum_id, is_active=True)
            except Forum.DoesNotExist:
                raise ValidationException("Forum not found")
            
            # Build queryset
            queryset = Thread.objects.filter(forum=forum)
            
            # Apply pagination
            paginator = self.pagination_class()
            paginated_threads = paginator.paginate_queryset(queryset, request)
            
            # Prepare response data
            response_data = {
                'results': [
                    {
                        'id': str(thread.id),
                        'title': thread.title,
                        'content': thread.content,
                        'author': {
                            'id': str(thread.author.id),
                            'name': thread.author.get_full_name()
                        },
                        'is_pinned': thread.is_pinned,
                        'is_locked': thread.is_locked,
                        'view_count': thread.view_count,
                        'created_at': thread.created_at.isoformat(),
                        'updated_at': thread.updated_at.isoformat()
                    }
                    for thread in paginated_threads
                ],
                'pagination': {
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link()
                }
            }
            
            # Cache the response
            cache.set(cache_key, response_data, THREAD_CACHE_TTL)
            logger.info(f"Threads retrieved successfully for forum: {forum_id}")
            
            return Response(response_data)
            
        except ValidationException as ve:
            logger.warning(f"Validation error listing threads: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error listing threads: {str(e)}")
            raise ValidationException("Failed to retrieve threads", details={'error': str(e)})