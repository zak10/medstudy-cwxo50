"""
API views for managing data collection in the Medical Research Platform.
Implements secure endpoints for blood work results, biometrics, and participant check-ins
with comprehensive validation, error handling, and audit logging.

Version: 1.0.0
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from django.db import transaction
from django.core.cache import cache
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from services.data.models import DataPoint, BloodWorkResult, CheckIn
from services.data.schemas import DataPointSchema, BloodWorkSchema, WeeklyCheckInSchema
from core.exceptions import ValidationException
from core.utils import sanitize_html, generate_unique_id
from core.decorators import rate_limit, audit_log

# Configure logger
logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = 'data_point'

class DataPointView(APIView):
    """
    Enhanced API view for managing data point operations with comprehensive validation,
    security controls, and monitoring capabilities.
    """
    
    permission_classes = [IsAuthenticated]
    schema_class = DataPointSchema

    @method_decorator(rate_limit(rate='100/hour'))
    @method_decorator(audit_log)
    def post(self, request) -> Response:
        """
        Creates a new data point with enhanced validation and security measures.
        
        Args:
            request: HTTP request object containing data point information
            
        Returns:
            Response: Created data point or error details
            
        Raises:
            ValidationException: If data validation fails
        """
        try:
            # Validate request data using schema
            data = request.data.copy()
            data['user'] = request.user.id
            
            schema = self.schema_class(**data)
            validated_data = schema.dict()
            
            # Verify protocol enrollment
            if not request.user.protocol_participations.filter(
                protocol_id=validated_data['protocol_id'],
                status='active'
            ).exists():
                raise ValidationException("User not enrolled in protocol")
            
            # Create data point with transaction management
            with transaction.atomic():
                # Initialize data point
                data_point = DataPoint(
                    user=request.user,
                    protocol_id=validated_data['protocol_id'],
                    type=validated_data['type'],
                    data=validated_data['data'],
                    recorded_at=validated_data.get('recorded_at', datetime.now())
                )
                
                # Process type-specific data
                if data_point.type == 'blood_work':
                    blood_work_schema = BloodWorkSchema(**validated_data['data'])
                    blood_work_data = blood_work_schema.dict()
                    
                    # Create blood work result
                    blood_work = BloodWorkResult(
                        data_point=data_point,
                        lab_name=blood_work_data['lab_name'],
                        test_date=blood_work_data['test_date'],
                        test_results=blood_work_data['markers'],
                        file_hash=blood_work_data['file_hash']
                    )
                    blood_work.save()
                    
                elif data_point.type == 'check_in':
                    check_in_schema = WeeklyCheckInSchema(**validated_data['data'])
                    check_in_data = check_in_schema.dict()
                    
                    # Create check-in record
                    check_in = CheckIn(
                        data_point=data_point,
                        energy_level=check_in_data['energy_level'],
                        sleep_quality=check_in_data['sleep_quality'],
                        side_effects=sanitize_html(check_in_data.get('side_effects', '')),
                        additional_notes=check_in_data.get('additional_notes', {})
                    )
                    check_in.save()
                
                # Save data point with encryption
                data_point.save()
                
                # Invalidate relevant caches
                cache_key = f"{CACHE_PREFIX}:user:{request.user.id}"
                cache.delete(cache_key)
                
                logger.info(
                    f"Created data point: {data_point.id}",
                    extra={
                        "user_id": request.user.id,
                        "protocol_id": data_point.protocol_id,
                        "type": data_point.type
                    }
                )
                
                return Response(
                    {
                        "message": "Data point created successfully",
                        "data_point_id": str(data_point.id),
                        "type": data_point.type,
                        "recorded_at": data_point.recorded_at.isoformat()
                    },
                    status=status.HTTP_201_CREATED
                )
                
        except ValidationException as e:
            logger.warning(
                "Validation error creating data point",
                extra={"error": str(e), "user_id": request.user.id}
            )
            return Response(e.to_dict(), status=e.status_code)
            
        except Exception as e:
            logger.error(
                "Error creating data point",
                extra={"error": str(e), "user_id": request.user.id},
                exc_info=True
            )
            return Response(
                {"message": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @method_decorator(rate_limit(rate='100/hour'))
    def get(self, request) -> Response:
        """
        Retrieves paginated data points with caching and filtering.
        
        Args:
            request: HTTP request object with optional query parameters
            
        Returns:
            Response: Paginated list of data points
        """
        try:
            # Check cache first
            cache_key = f"{CACHE_PREFIX}:user:{request.user.id}"
            cached_response = cache.get(cache_key)
            
            if cached_response:
                return Response(cached_response)
            
            # Process query parameters
            protocol_id = request.query_params.get('protocol_id')
            data_type = request.query_params.get('type')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            # Build query
            queryset = DataPoint.objects.filter(user=request.user)
            
            if protocol_id:
                queryset = queryset.filter(protocol_id=protocol_id)
            if data_type:
                queryset = queryset.filter(type=data_type)
            if start_date:
                queryset = queryset.filter(recorded_at__gte=start_date)
            if end_date:
                queryset = queryset.filter(recorded_at__lte=end_date)
                
            # Apply pagination
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 10)), 100)
            start = (page - 1) * page_size
            end = start + page_size
            
            # Get paginated results
            total_count = queryset.count()
            data_points = queryset.order_by('-recorded_at')[start:end]
            
            # Format response
            response_data = {
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "results": [
                    {
                        "id": str(dp.id),
                        "type": dp.type,
                        "recorded_at": dp.recorded_at.isoformat(),
                        "protocol_id": str(dp.protocol_id),
                        "data": dp.data
                    }
                    for dp in data_points
                ]
            }
            
            # Cache response
            cache.set(cache_key, response_data, CACHE_TTL)
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(
                "Error retrieving data points",
                extra={"error": str(e), "user_id": request.user.id},
                exc_info=True
            )
            return Response(
                {"message": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )