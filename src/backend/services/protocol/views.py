"""
Protocol service views for the Medical Research Platform.
Implements secure viewsets for protocol management with enhanced validation,
monitoring, and rate limiting.

Version: 1.0.0
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from ratelimit.decorators import ratelimit
import logging
from typing import Dict, Any

from services.protocol.models import Protocol
from services.protocol.serializers import ProtocolSerializer, ParticipationSerializer
from core.exceptions import ValidationException
from core.utils import sanitize_html

# Configure logger
logger = logging.getLogger(__name__)

class ProtocolViewSet(viewsets.ModelViewSet):
    """
    Enhanced viewset for managing research protocols with comprehensive security,
    validation, and monitoring features.
    """
    
    queryset = Protocol.objects.all()
    serializer_class = ProtocolSerializer
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        """Initialize viewset with security logging and caching configuration."""
        super().__init__(*args, **kwargs)
        self.cache_timeout = 300  # 5 minutes
        self.rate_limit = '100/h'  # 100 requests per hour
        
    @method_decorator(cache_page(300))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        """
        Lists available protocols with caching and filtering.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Filtered list of protocols
        """
        try:
            # Apply filters
            queryset = self.get_queryset()
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
                
            # Apply search
            search_query = request.query_params.get('search')
            if search_query:
                queryset = queryset.filter(title__icontains=search_query)
                
            # Serialize and return
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error listing protocols: {str(e)}")
            raise
    
    @transaction.atomic
    @method_decorator(ratelimit(key='user', rate='100/h'))
    def create(self, request, *args, **kwargs):
        """
        Creates a new protocol with enhanced validation and security checks.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Created protocol data
            
        Raises:
            ValidationException: If validation fails
            PermissionDenied: If user lacks required permissions
        """
        try:
            # Verify creator permissions
            if not request.user.has_role('protocol_creator'):
                raise PermissionDenied("Must be a protocol creator to create protocols")
                
            # Sanitize input data
            data = request.data.copy()
            if 'description' in data:
                data['description'] = sanitize_html(data['description'])
                
            # Validate and create protocol
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            
            # Save with creator
            protocol = serializer.save(creator=request.user)
            
            logger.info(f"Protocol created: {protocol.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationException as e:
            logger.warning(f"Protocol creation validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating protocol: {str(e)}")
            raise
    
    @action(detail=True, methods=['POST'])
    @transaction.atomic
    @method_decorator(ratelimit(key='user', rate='100/h'))
    def enroll(self, request, pk=None):
        """
        Enrolls a participant in a protocol with validation checks.
        
        Args:
            request: HTTP request object
            pk: Protocol ID
            
        Returns:
            Response: Enrollment status
        """
        try:
            protocol = self.get_object()
            
            # Check enrollment eligibility
            if not protocol.status == 'active':
                raise ValidationException("Protocol is not currently active")
                
            # Create participation
            participation_data = {
                'protocol': protocol.id,
                'user': request.user.id
            }
            
            serializer = ParticipationSerializer(data=participation_data)
            serializer.is_valid(raise_exception=True)
            participation = serializer.save()
            
            logger.info(f"User {request.user.id} enrolled in protocol {protocol.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error enrolling in protocol: {str(e)}")
            raise
    
    @action(detail=True, methods=['POST'])
    @transaction.atomic
    @method_decorator(ratelimit(key='user', rate='100/h'))
    def submit_data(self, request, pk=None):
        """
        Submits protocol data with real-time safety checks and validation.
        
        Args:
            request: HTTP request object
            pk: Protocol ID
            
        Returns:
            Response: Submission status
        """
        try:
            protocol = self.get_object()
            
            # Verify participation
            participation = protocol.participations.filter(
                user=request.user,
                status='active'
            ).first()
            
            if not participation:
                raise PermissionDenied("Must be an active participant to submit data")
                
            # Validate data format
            data_point = request.data.copy()
            if not protocol.validate_requirements():
                raise ValidationException("Invalid data format")
                
            # Check safety violations
            violation_found, message, details = protocol.check_safety_violation(data_point)
            if violation_found:
                logger.warning(
                    f"Safety violation in protocol {protocol.id}",
                    extra={'violation_details': details}
                )
                
            # Store data point
            participation.completion_data.update(data_point)
            participation.save()
            
            response_data = {
                'status': 'success',
                'safety_alert': message if violation_found else None,
                'violation_details': details if violation_found else None
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error submitting protocol data: {str(e)}")
            raise
    
    @action(detail=True, methods=['GET'])
    @method_decorator(cache_page(300))
    @method_decorator(vary_on_headers('Authorization'))
    def analytics(self, request, pk=None):
        """
        Retrieves protocol analytics with caching.
        
        Args:
            request: HTTP request object
            pk: Protocol ID
            
        Returns:
            Response: Protocol analytics data
        """
        try:
            protocol = self.get_object()
            
            # Check analytics access permissions
            if not (request.user.has_role('protocol_creator') or 
                   request.user == protocol.creator):
                raise PermissionDenied("Insufficient permissions for analytics access")
                
            # Calculate analytics
            analytics_data = {
                'total_participants': protocol.participations.count(),
                'active_participants': protocol.participations.filter(
                    status='active'
                ).count(),
                'completion_rate': protocol.get_completion_rate(),
                'safety_violations': len(protocol.safety_violation_thresholds or {})
            }
            
            return Response(analytics_data)
            
        except Exception as e:
            logger.error(f"Error retrieving protocol analytics: {str(e)}")
            raise