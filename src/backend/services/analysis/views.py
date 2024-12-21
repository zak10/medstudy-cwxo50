"""
API views for the analysis service handling protocol data analysis, statistical computations,
pattern detection and visualization endpoints with enhanced security and caching.

Version: 1.0.0
"""

from rest_framework.views import APIView  # version ^3.14.0
from rest_framework.response import Response  # version ^3.14.0
from rest_framework.decorators import action, cache_control  # version ^3.14.0
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
import logging
from typing import Dict, Any, Optional

from services.analysis.models import AnalysisResult
from services.analysis.schemas import (
    StatisticalSummarySchema,
    PatternDetectionSchema,
    VisualizationConfigSchema,
    AnalysisRequestSchema
)
from services.protocol.models import Protocol
from services.data.models import DataPoint
from core.exceptions import ValidationException
from core.utils import format_datetime

# Configure logger
logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL = 3600  # 1 hour
CACHE_KEY_PREFIX = 'analysis'

class AnalysisViewSet(APIView):
    """
    Enhanced ViewSet for handling protocol analysis operations with caching and security.
    Implements comprehensive data analysis, pattern detection, and visualization endpoints.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def __init__(self, *args, **kwargs):
        """Initialize analysis viewset with security and caching configuration."""
        super().__init__(*args, **kwargs)
        self.cache_timeout = CACHE_TTL
        
    @transaction.atomic
    @action(methods=['post'], detail=False)
    @cache_control(private=True)
    def create_analysis(self, request) -> Response:
        """
        Initiates protocol data analysis with enhanced validation and progress tracking.
        
        Args:
            request: HTTP request with analysis parameters
            
        Returns:
            Response with analysis task status
            
        Raises:
            ValidationException: If request validation fails
        """
        try:
            # Validate request data
            schema = AnalysisRequestSchema(**request.data)
            
            # Get protocol and validate access
            protocol = Protocol.objects.get(id=schema.protocol_id)
            if not request.user.has_role('protocol_creator') and protocol.creator != request.user:
                raise ValidationException("Unauthorized to analyze this protocol")
            
            # Get data points with optimization
            data_points = DataPoint.objects.filter(
                protocol=protocol,
                status='validated'
            ).select_related('user').order_by('recorded_at')
            
            if not data_points:
                raise ValidationException("No validated data points available for analysis")
            
            # Initialize analysis result
            analysis_result = AnalysisResult.objects.create(
                protocol=protocol,
                status='processing'
            )
            
            # Compute statistics
            if schema.analysis_options.get('compute_statistics', True):
                statistical_summary = analysis_result.compute_statistics(data_points)
                analysis_result.statistical_summary = statistical_summary
            
            # Detect patterns
            if schema.analysis_options.get('detect_patterns', True):
                patterns = analysis_result.detect_patterns(
                    data_points,
                    confidence_threshold=schema.confidence_threshold
                )
                analysis_result.patterns_detected = patterns
            
            # Generate visualizations
            if schema.analysis_options.get('generate_visualizations', True):
                visualizations = analysis_result.generate_visualizations(
                    analysis_result.statistical_summary,
                    analysis_result.patterns_detected
                )
                analysis_result.visualizations = visualizations
            
            # Update status and save
            analysis_result.status = 'completed'
            analysis_result.save()
            
            # Clear related caches
            cache_key = f"{CACHE_KEY_PREFIX}:protocol:{protocol.id}"
            cache.delete(cache_key)
            
            return Response({
                'id': str(analysis_result.id),
                'status': 'completed',
                'created_at': format_datetime(analysis_result.created_at)
            })
            
        except Protocol.DoesNotExist:
            raise ValidationException("Protocol not found")
        except Exception as e:
            logger.error(f"Analysis creation failed: {str(e)}")
            raise ValidationException("Analysis creation failed")
    
    @action(methods=['get'], detail=True)
    @cache_control(public=True, max_age=CACHE_TTL)
    def get_analysis_results(self, request, protocol_id: str) -> Response:
        """
        Retrieves analysis results with caching and pagination.
        
        Args:
            request: HTTP request
            protocol_id: UUID of the protocol
            
        Returns:
            Paginated analysis results
            
        Raises:
            ValidationException: If validation fails
        """
        try:
            # Check cache
            cache_key = f"{CACHE_KEY_PREFIX}:protocol:{protocol_id}"
            cached_results = cache.get(cache_key)
            
            if cached_results:
                return Response(cached_results)
            
            # Get protocol and validate access
            protocol = Protocol.objects.get(id=protocol_id)
            if not request.user.has_role('protocol_creator') and protocol.creator != request.user:
                raise ValidationException("Unauthorized to view analysis results")
            
            # Get analysis results with optimization
            analysis_results = AnalysisResult.objects.filter(
                protocol=protocol,
                status='completed'
            ).order_by('-created_at')
            
            # Paginate results
            paginator = PageNumberPagination()
            paginator.page_size = 10
            paginated_results = paginator.paginate_queryset(analysis_results, request)
            
            # Format response
            results = []
            for result in paginated_results:
                results.append({
                    'id': str(result.id),
                    'statistical_summary': result.statistical_summary,
                    'patterns_detected': result.patterns_detected,
                    'visualizations': result.visualizations,
                    'created_at': format_datetime(result.created_at)
                })
            
            response_data = {
                'count': analysis_results.count(),
                'results': results
            }
            
            # Cache results
            cache.set(cache_key, response_data, CACHE_TTL)
            
            return Response(response_data)
            
        except Protocol.DoesNotExist:
            raise ValidationException("Protocol not found")
        except Exception as e:
            logger.error(f"Error retrieving analysis results: {str(e)}")
            raise ValidationException("Failed to retrieve analysis results")
    
    @action(methods=['get'], detail=True)
    @cache_control(public=True, max_age=CACHE_TTL)
    def get_visualizations(self, request, analysis_id: str) -> Response:
        """
        Retrieves visualization configurations with caching.
        
        Args:
            request: HTTP request
            analysis_id: UUID of the analysis result
            
        Returns:
            Visualization configurations
            
        Raises:
            ValidationException: If validation fails
        """
        try:
            # Check cache
            cache_key = f"{CACHE_KEY_PREFIX}:visualizations:{analysis_id}"
            cached_viz = cache.get(cache_key)
            
            if cached_viz:
                return Response(cached_viz)
            
            # Get analysis result and validate access
            analysis_result = AnalysisResult.objects.select_related('protocol').get(id=analysis_id)
            if not request.user.has_role('protocol_creator') and analysis_result.protocol.creator != request.user:
                raise ValidationException("Unauthorized to view visualizations")
            
            # Validate visualization configurations
            schema = VisualizationConfigSchema(data=analysis_result.visualizations)
            
            response_data = {
                'visualizations': analysis_result.visualizations,
                'generated_at': format_datetime(analysis_result.created_at)
            }
            
            # Cache visualizations
            cache.set(cache_key, response_data, CACHE_TTL)
            
            return Response(response_data)
            
        except AnalysisResult.DoesNotExist:
            raise ValidationException("Analysis result not found")
        except Exception as e:
            logger.error(f"Error retrieving visualizations: {str(e)}")
            raise ValidationException("Failed to retrieve visualizations")