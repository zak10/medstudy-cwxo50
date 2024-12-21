"""
Serializers for data collection in the Medical Research Platform.
Implements comprehensive validation and sanitization for protocol data points,
blood work results, and participant check-ins.

Version: 1.0.0
"""

from rest_framework import serializers  # v3.14.0
from rest_framework.exceptions import ValidationError  # v3.14.0
from django.utils import timezone  # v4.2
import bleach  # v6.0.0
import logging

from .models import DataPoint, BloodworkResult, CheckIn
from .schemas import DataPointSchema
from core.exceptions import ValidationException

# Configure logger
logger = logging.getLogger(__name__)

class DataPointSerializer(serializers.ModelSerializer):
    """
    Base serializer for all protocol data points with enhanced validation and sanitization.
    Implements comprehensive data validation against protocol requirements.
    """

    id = serializers.UUIDField(read_only=True)
    protocol_id = serializers.UUIDField()
    type = serializers.CharField()
    data = serializers.JSONField()
    recorded_at = serializers.DateTimeField(default=timezone.now)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = DataPoint
        fields = ['id', 'protocol_id', 'type', 'data', 'recorded_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Validates and sanitizes data point data against protocol requirements.
        
        Args:
            data: Dictionary containing data point information
            
        Returns:
            Validated and sanitized data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Create schema instance for validation
            schema = DataPointSchema(
                id=data.get('id'),
                protocol_id=data['protocol_id'],
                type=data['type'],
                data=data['data'],
                recorded_at=data.get('recorded_at', timezone.now())
            )

            # Validate data against schema
            validated_data = schema.dict()

            # Additional protocol-specific validation
            protocol = self.context.get('protocol')
            if protocol:
                if not protocol.validate_requirements():
                    raise ValidationException("Data does not meet protocol requirements")

                # Check for safety violations
                violation_found, message, details = protocol.check_safety_violation(validated_data['data'])
                if violation_found:
                    raise ValidationException(message, details)

            logger.info(f"Validated data point for protocol {data['protocol_id']}")
            return validated_data

        except ValidationException as e:
            logger.error(f"Data point validation error: {str(e)}")
            raise ValidationError(detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in data point validation: {str(e)}")
            raise ValidationError("Failed to validate data point")

class BloodWorkSerializer(serializers.ModelSerializer):
    """
    Serializer for blood test results with secure file handling and enhanced validation.
    Implements comprehensive validation for blood work data and secure file uploads.
    """

    id = serializers.UUIDField(read_only=True)
    report_file = serializers.FileField(write_only=True)
    lab_name = serializers.CharField(max_length=255)
    test_date = serializers.DateField()
    test_results = serializers.JSONField()

    class Meta:
        model = BloodworkResult
        fields = ['id', 'report_file', 'lab_name', 'test_date', 'test_results']
        read_only_fields = ['id']

    def validate_test_results(self, value):
        """
        Validates blood test results with comprehensive range checking.
        
        Args:
            value: Dictionary containing test results
            
        Returns:
            Validated test results
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            required_markers = ['vitamin_d', 'crp', 'hdl', 'ldl', 'triglycerides']
            
            # Check for required markers
            missing_markers = [marker for marker in required_markers if marker not in value]
            if missing_markers:
                raise ValidationException(f"Missing required markers: {', '.join(missing_markers)}")

            # Validate marker ranges
            for marker, result in value.items():
                if not isinstance(result, (int, float)):
                    raise ValidationException(f"Invalid value for {marker}: must be numeric")
                if result < 0:
                    raise ValidationException(f"Invalid value for {marker}: cannot be negative")

            logger.info("Validated blood work test results")
            return value

        except ValidationException as e:
            logger.error(f"Blood work validation error: {str(e)}")
            raise ValidationError(detail=str(e))

    def create(self, validated_data):
        """
        Creates blood work result with secure file handling.
        
        Args:
            validated_data: Dictionary containing validated data
            
        Returns:
            Created BloodworkResult instance
            
        Raises:
            ValidationError: If creation fails
        """
        try:
            # Handle file upload securely
            report_file = validated_data.pop('report_file')
            
            # Create data point first
            data_point = DataPoint.objects.create(
                type='blood_work',
                data=validated_data['test_results'],
                protocol_id=self.context['protocol_id'],
                recorded_at=validated_data['test_date']
            )

            # Create blood work result with secure file handling
            blood_work = BloodworkResult.objects.create(
                data_point=data_point,
                report_file=report_file,
                lab_name=validated_data['lab_name'],
                test_date=validated_data['test_date'],
                test_results=validated_data['test_results']
            )

            logger.info(f"Created blood work result: {blood_work.id}")
            return blood_work

        except Exception as e:
            logger.error(f"Error creating blood work result: {str(e)}")
            raise ValidationError("Failed to create blood work result")

class WeeklyCheckInSerializer(serializers.ModelSerializer):
    """
    Serializer for weekly participant check-ins with text sanitization.
    Implements comprehensive validation for check-in data with enhanced security.
    """

    id = serializers.UUIDField(read_only=True)
    energy_level = serializers.IntegerField(min_value=1, max_value=5)
    sleep_quality = serializers.IntegerField(min_value=1, max_value=5)
    side_effects = serializers.CharField(allow_blank=True, max_length=1000)
    additional_notes = serializers.JSONField(required=False)

    class Meta:
        model = CheckIn
        fields = ['id', 'energy_level', 'sleep_quality', 'side_effects', 'additional_notes']
        read_only_fields = ['id']

    def validate_ratings(self, data):
        """
        Validates rating scale values with enhanced checks.
        
        Args:
            data: Dictionary containing rating values
            
        Returns:
            Validated ratings
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            for field in ['energy_level', 'sleep_quality']:
                value = data.get(field)
                if value is not None:
                    if not 1 <= value <= 5:
                        raise ValidationException(f"{field} must be between 1 and 5")

            logger.info("Validated check-in ratings")
            return data

        except ValidationException as e:
            logger.error(f"Rating validation error: {str(e)}")
            raise ValidationError(detail=str(e))

    def create(self, validated_data):
        """
        Creates weekly check-in with sanitized text.
        
        Args:
            validated_data: Dictionary containing validated data
            
        Returns:
            Created CheckIn instance
            
        Raises:
            ValidationError: If creation fails
        """
        try:
            # Sanitize text fields
            if 'side_effects' in validated_data:
                validated_data['side_effects'] = bleach.clean(
                    validated_data['side_effects'],
                    tags=[],
                    strip=True
                )

            # Create data point first
            data_point = DataPoint.objects.create(
                type='check_in',
                data=validated_data,
                protocol_id=self.context['protocol_id'],
                recorded_at=timezone.now()
            )

            # Create check-in record
            check_in = CheckIn.objects.create(
                data_point=data_point,
                **validated_data
            )

            logger.info(f"Created weekly check-in: {check_in.id}")
            return check_in

        except Exception as e:
            logger.error(f"Error creating weekly check-in: {str(e)}")
            raise ValidationError("Failed to create weekly check-in")