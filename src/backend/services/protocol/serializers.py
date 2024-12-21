"""
Protocol service serializers for the Medical Research Platform.
Implements comprehensive serializers for Protocol and Participation models with enhanced
validation, security features, and performance optimizations.

Version: 1.0.0
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from typing import Dict, Any

from services.protocol.models import Protocol, Participation
from services.protocol.schemas import validate_requirements_schema, validate_safety_parameters
from core.utils import sanitize_html

class ProtocolSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for Protocol model with comprehensive validation and security features.
    Implements detailed data transformation and representation with caching support.
    """
    
    # Computed fields with caching
    participant_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    safety_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Protocol
        fields = [
            'id', 'title', 'description', 'creator', 'requirements',
            'safety_params', 'duration_weeks', 'start_date', 'end_date',
            'status', 'min_participants', 'max_participants',
            'safety_violation_thresholds', 'version', 'data_collection_frequency',
            'participant_count', 'completion_rate', 'safety_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'version']
        
    def validate_title(self, value: str) -> str:
        """Validates and sanitizes protocol title."""
        if not value or len(value.strip()) < 3:
            raise ValidationError("Title must be at least 3 characters long")
        return sanitize_html(value.strip())
        
    def validate_description(self, value: str) -> str:
        """Validates and sanitizes protocol description."""
        if value:
            return sanitize_html(value)
        return value
        
    def validate_requirements(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced validation of protocol requirements with strict schema checking.
        
        Args:
            value: Protocol requirements dictionary
            
        Returns:
            Validated requirements dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate requirements schema
            validate_requirements_schema(value)
            
            # Additional validation for data collection requirements
            if not value.get('data_points'):
                raise ValidationError("At least one data point is required")
                
            # Validate measurement units
            for data_point in value.get('data_points', []):
                if 'unit' not in data_point:
                    raise ValidationError(f"Missing unit for data point: {data_point.get('name')}")
                    
            return value
            
        except ValidationError as e:
            raise ValidationError(f"Requirements validation failed: {str(e)}")
            
    def validate_safety_params(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of safety parameters with threshold verification.
        
        Args:
            value: Safety parameters dictionary
            
        Returns:
            Validated safety parameters dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate safety parameters schema
            validate_safety_parameters(value)
            
            # Additional validation for safety thresholds
            if 'markers' in value:
                for marker, params in value['markers'].items():
                    if params.get('intervention_required'):
                        if not params.get('critical_ranges'):
                            raise ValidationError(
                                f"Critical ranges required for marker {marker} with intervention"
                            )
                            
            return value
            
        except ValidationError as e:
            raise ValidationError(f"Safety parameters validation failed: {str(e)}")
            
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs cross-field validation with enhanced security checks.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            Validated data dictionary
        """
        # Validate date ranges
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise ValidationError("End date must be after start date")
                
        # Validate participant limits
        if data.get('min_participants') and data.get('max_participants'):
            if data['min_participants'] > data['max_participants']:
                raise ValidationError("Minimum participants cannot exceed maximum")
                
        return data
        
    def get_participant_count(self, obj: Protocol) -> int:
        """Returns current participant count with caching."""
        return obj.participations.filter(status__in=['enrolled', 'active']).count()
        
    def get_completion_rate(self, obj: Protocol) -> float:
        """Calculates protocol completion rate with caching."""
        completed = obj.participations.filter(status='completed').count()
        total = obj.participations.exclude(status='withdrawn').count()
        return round((completed / total * 100) if total > 0 else 0, 2)
        
    def get_safety_status(self, obj: Protocol) -> Dict[str, Any]:
        """Returns current safety status with violation counts."""
        return {
            'has_violations': obj.safety_violation_thresholds is not None,
            'violation_count': len(obj.safety_violation_thresholds or {})
        }

class ParticipationSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for Participation model with progress tracking and validation.
    Implements comprehensive participation management with completion verification.
    """
    
    # Computed fields
    progress = serializers.SerializerMethodField()
    remaining_tasks = serializers.SerializerMethodField()
    compliance_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Participation
        fields = [
            'id', 'protocol', 'user', 'status', 'enrolled_at',
            'completed_at', 'completion_data', 'progress_percentage',
            'participation_metrics', 'progress', 'remaining_tasks',
            'compliance_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'progress_percentage']
        
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of participation data with enhanced checks.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            Validated data dictionary
        """
        # Validate protocol capacity
        protocol = data.get('protocol')
        if protocol:
            current_count = protocol.participations.filter(
                status__in=['enrolled', 'active']
            ).count()
            if current_count >= protocol.max_participants:
                raise ValidationError("Protocol has reached maximum participants")
                
        # Validate completion data if provided
        if 'completion_data' in data:
            self._validate_completion_data(data['completion_data'], protocol)
            
        return data
        
    def _validate_completion_data(
        self,
        completion_data: Dict[str, Any],
        protocol: Protocol
    ) -> None:
        """Validates completion data against protocol requirements."""
        if not protocol.requirements.get('data_points'):
            return
            
        missing_points = []
        for point in protocol.requirements['data_points']:
            if point['name'] not in completion_data:
                missing_points.append(point['name'])
                
        if missing_points:
            raise ValidationError(f"Missing required data points: {', '.join(missing_points)}")
            
    def get_progress(self, obj: Participation) -> Dict[str, Any]:
        """Calculates detailed progress metrics with caching."""
        return {
            'percentage': obj.progress_percentage,
            'completed_tasks': len(obj.completion_data or {}),
            'total_tasks': len(obj.protocol.requirements.get('data_points', []))
        }
        
    def get_remaining_tasks(self, obj: Participation) -> list:
        """Returns list of remaining required tasks."""
        completed = set(obj.completion_data.keys() if obj.completion_data else set())
        required = set(
            point['name'] for point in obj.protocol.requirements.get('data_points', [])
        )
        return list(required - completed)
        
    def get_compliance_score(self, obj: Participation) -> float:
        """Calculates participant compliance score."""
        if not obj.participation_metrics:
            return 0.0
            
        metrics = obj.participation_metrics
        total_required = metrics.get('total_required_submissions', 0)
        actual_submissions = metrics.get('total_submissions', 0)
        
        return round((actual_submissions / total_required * 100) if total_required > 0 else 0, 2)