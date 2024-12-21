"""
Protocol models for the Medical Research Platform.

This module defines the core Protocol model and related models for managing research protocols,
including protocol requirements, safety parameters, and enrollment management with enhanced
validation and security features.

Version: 1.0.0
"""

from django.db import models
from django.utils import timezone
import uuid
import jsonschema
import logging

from services.user.models import User
from core.utils import generate_unique_id, sanitize_html
from core.exceptions import ValidationException

# Configure logger
logger = logging.getLogger(__name__)

# Protocol status choices
PROTOCOL_STATUS_CHOICES = (
    ('draft', 'Draft'),
    ('active', 'Active'),
    ('paused', 'Paused'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled')
)

# Participation status choices
PARTICIPATION_STATUS_CHOICES = (
    ('enrolled', 'Enrolled'),
    ('active', 'Active'),
    ('completed', 'Completed'),
    ('withdrawn', 'Withdrawn')
)

class Protocol(models.Model):
    """
    Enhanced core model for research protocols with advanced validation and security features.
    Implements comprehensive protocol management with safety controls and audit logging.
    """
    
    # Identity and metadata
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    creator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_protocols'
    )
    
    # Protocol configuration
    requirements = models.JSONField(default=dict)
    safety_params = models.JSONField(default=dict)
    duration_weeks = models.IntegerField()
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PROTOCOL_STATUS_CHOICES,
        default='draft'
    )
    
    # Participation limits
    min_participants = models.IntegerField(default=1)
    max_participants = models.IntegerField()
    
    # Enhanced safety features
    safety_violation_thresholds = models.JSONField(default=dict)
    version = models.CharField(max_length=10, default='1.0.0')
    data_collection_frequency = models.JSONField(default=dict)
    
    # Audit trail
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    audit_log = models.JSONField(default=list)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['start_date', 'end_date'])
        ]
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def save(self, *args, **kwargs):
        """
        Enhanced save method with comprehensive validation and security checks.
        
        Raises:
            ValidationException: If validation fails
        """
        try:
            # Sanitize HTML content
            self.description = sanitize_html(self.description)
            
            # Validate requirements schema
            if not self.validate_requirements():
                raise ValidationException("Invalid protocol requirements")
            
            # Validate timeline consistency
            if self.start_date and self.end_date and self.start_date >= self.end_date:
                raise ValidationException("End date must be after start date")
            
            # Update audit log
            audit_entry = {
                'timestamp': timezone.now().isoformat(),
                'version': self.version,
                'status': self.status,
                'action': 'update' if self.pk else 'create'
            }
            self.audit_log.append(audit_entry)
            
            # Set timestamps
            if not self.pk:
                self.created_at = timezone.now()
            self.updated_at = timezone.now()
            
            super().save(*args, **kwargs)
            logger.info(f"Saved protocol: {self.id}")
            
        except Exception as e:
            logger.error(f"Error saving protocol: {str(e)}")
            raise
    
    def validate_requirements(self) -> bool:
        """
        Enhanced validation of protocol requirements with strict schema checking.
        
        Returns:
            bool: True if requirements are valid
            
        Raises:
            ValidationException: If requirements are invalid
        """
        try:
            # Define requirements schema
            schema = {
                "type": "object",
                "required": ["data_points", "frequency", "duration"],
                "properties": {
                    "data_points": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "type", "unit"],
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "unit": {"type": "string"},
                                "range": {
                                    "type": "object",
                                    "properties": {
                                        "min": {"type": "number"},
                                        "max": {"type": "number"}
                                    }
                                }
                            }
                        }
                    },
                    "frequency": {
                        "type": "object",
                        "required": ["type", "value"],
                        "properties": {
                            "type": {"type": "string"},
                            "value": {"type": "number"}
                        }
                    },
                    "duration": {"type": "number", "minimum": 1}
                }
            }
            
            jsonschema.validate(self.requirements, schema)
            return True
            
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Requirements validation error: {str(e)}")
            return False
    
    def check_safety_violation(self, data_point: dict) -> tuple:
        """
        Enhanced safety parameter violation detection with detailed reporting.
        
        Args:
            data_point: Dictionary containing measurement data
            
        Returns:
            tuple: (violation_found, violation_message, violation_details)
        """
        try:
            violation_found = False
            violation_message = ""
            violation_details = {}
            
            # Check against safety thresholds
            for param, threshold in self.safety_violation_thresholds.items():
                if param in data_point:
                    value = data_point[param]
                    
                    # Check minimum threshold
                    if 'min' in threshold and value < threshold['min']:
                        violation_found = True
                        violation_details[param] = {
                            'type': 'below_minimum',
                            'value': value,
                            'threshold': threshold['min']
                        }
                    
                    # Check maximum threshold
                    if 'max' in threshold and value > threshold['max']:
                        violation_found = True
                        violation_details[param] = {
                            'type': 'above_maximum',
                            'value': value,
                            'threshold': threshold['max']
                        }
            
            if violation_found:
                violation_message = "Safety parameter violation detected"
                logger.warning(
                    f"Safety violation in protocol {self.id}",
                    extra={'violation_details': violation_details}
                )
            
            return violation_found, violation_message, violation_details
            
        except Exception as e:
            logger.error(f"Error checking safety violation: {str(e)}")
            raise

class Participation(models.Model):
    """
    Enhanced model for protocol enrollment with advanced tracking and validation.
    Implements comprehensive participation management and progress tracking.
    """
    
    # Identity and relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.PROTECT,
        related_name='participations'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='protocol_participations'
    )
    
    # Status and progress
    status = models.CharField(
        max_length=20,
        choices=PARTICIPATION_STATUS_CHOICES,
        default='enrolled'
    )
    enrolled_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_data = models.JSONField(default=dict)
    progress_percentage = models.FloatField(default=0.0)
    
    # Enhanced tracking
    participation_metrics = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    audit_log = models.JSONField(default=list)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['enrolled_at']),
            models.Index(fields=['progress_percentage'])
        ]
        unique_together = ['protocol', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.protocol.title}"
    
    def save(self, *args, **kwargs):
        """
        Enhanced save method with enrollment validation and progress tracking.
        
        Raises:
            ValidationException: If validation fails
        """
        try:
            # Check protocol capacity
            if not self.pk:
                current_participants = self.protocol.participations.count()
                if current_participants >= self.protocol.max_participants:
                    raise ValidationException("Protocol has reached maximum participants")
            
            # Update audit log
            audit_entry = {
                'timestamp': timezone.now().isoformat(),
                'status': self.status,
                'progress': self.progress_percentage,
                'action': 'update' if self.pk else 'enroll'
            }
            self.audit_log.append(audit_entry)
            
            # Set timestamps
            if not self.pk:
                self.created_at = timezone.now()
            self.updated_at = timezone.now()
            
            super().save(*args, **kwargs)
            logger.info(f"Saved participation: {self.id}")
            
        except Exception as e:
            logger.error(f"Error saving participation: {str(e)}")
            raise
    
    def check_completion(self) -> dict:
        """
        Enhanced completion status checking with detailed reporting.
        
        Returns:
            dict: Detailed completion status and metrics
        """
        try:
            completion_status = {
                'completed': False,
                'progress': self.progress_percentage,
                'missing_requirements': [],
                'completed_requirements': []
            }
            
            # Check each protocol requirement
            for requirement in self.protocol.requirements.get('data_points', []):
                requirement_name = requirement['name']
                if requirement_name in self.completion_data:
                    completion_status['completed_requirements'].append(requirement_name)
                else:
                    completion_status['missing_requirements'].append(requirement_name)
            
            # Calculate completion
            total_requirements = len(self.protocol.requirements.get('data_points', []))
            completed_count = len(completion_status['completed_requirements'])
            
            if total_requirements > 0:
                completion_status['progress'] = (completed_count / total_requirements) * 100
                completion_status['completed'] = completed_count == total_requirements
            
            # Update progress percentage
            if self.progress_percentage != completion_status['progress']:
                self.progress_percentage = completion_status['progress']
                self.save()
            
            return completion_status
            
        except Exception as e:
            logger.error(f"Error checking completion status: {str(e)}")
            raise