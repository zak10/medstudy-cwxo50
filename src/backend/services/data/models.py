"""
Data models for the Medical Research Platform.

This module defines core models for managing research data collection, including blood work results,
check-ins, biometrics, and participant experiences with enhanced security and validation features.

Version: 1.0.0
"""

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
import uuid
import logging
import json

from services.protocol.models import Protocol
from core.utils import hash_file, sanitize_html
from core.exceptions import ValidationException
from cryptography.fernet import Fernet
import boto3

# Configure logger
logger = logging.getLogger(__name__)

# Data point status choices
DATA_POINT_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('validated', 'Validated'),
    ('rejected', 'Rejected'),
    ('archived', 'Archived')
)

# Data point types
DATA_POINT_TYPES = (
    ('blood_work', 'Blood Work'),
    ('check_in', 'Weekly Check-in'),
    ('biometric', 'Biometric Measurement'),
    ('experience', 'Experience Report')
)

@python_2_unicode_compatible
class DataPoint(models.Model):
    """
    Core model for storing all types of protocol data points with enhanced security.
    Implements comprehensive data validation, encryption, and audit logging.
    """
    
    # Identity and relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.PROTECT,
        related_name='data_points'
    )
    user = models.ForeignKey(
        'user.User',
        on_delete=models.PROTECT,
        related_name='data_points'
    )
    
    # Data fields
    type = models.CharField(
        max_length=20,
        choices=DATA_POINT_TYPES,
        db_index=True
    )
    data = models.JSONField()
    recorded_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=DATA_POINT_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Security and audit
    audit_trail = models.JSONField(default=list)
    encryption_metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['type', 'status']),
            models.Index(fields=['recorded_at']),
            models.Index(fields=['created_at'])
        ]
        
    def __str__(self):
        return f"{self.type} - {self.user.email} - {self.recorded_at}"

    def encrypt_sensitive_data(self) -> dict:
        """
        Encrypts sensitive fields based on data classification.
        
        Returns:
            dict: Encrypted data with metadata
            
        Raises:
            ValidationException: If encryption fails
        """
        try:
            # Get data classification from protocol
            classification = self.protocol.get_data_classification()
            
            # Initialize encryption
            key = Fernet.generate_key()
            fernet = Fernet(key)
            
            # Identify and encrypt sensitive fields
            encrypted_data = self.data.copy()
            sensitive_fields = []
            
            for field, value in self.data.items():
                if field in classification.get('sensitive_fields', []):
                    encrypted_value = fernet.encrypt(json.dumps(value).encode())
                    encrypted_data[field] = encrypted_value.decode()
                    sensitive_fields.append(field)
            
            # Update encryption metadata
            self.encryption_metadata = {
                'encrypted_fields': sensitive_fields,
                'encryption_key': key.decode(),
                'encryption_date': timezone.now().isoformat(),
                'encryption_version': '1.0'
            }
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Encryption error for data point {self.id}: {str(e)}")
            raise ValidationException("Failed to encrypt sensitive data")

    def save(self, *args, **kwargs):
        """
        Enhanced save method with validation, encryption, and audit logging.
        
        Raises:
            ValidationException: If validation fails
        """
        try:
            # Validate data against protocol requirements
            if not self.protocol.validate_requirements():
                raise ValidationException("Invalid protocol requirements")
            
            # Set timestamps
            if not self.pk:
                self.created_at = timezone.now()
            self.updated_at = timezone.now()
            
            # Encrypt sensitive data
            self.data = self.encrypt_sensitive_data()
            
            # Generate audit entry
            audit_entry = {
                'timestamp': timezone.now().isoformat(),
                'action': 'update' if self.pk else 'create',
                'status': self.status,
                'user_id': str(self.user.id)
            }
            self.audit_trail.append(audit_entry)
            
            super().save(*args, **kwargs)
            logger.info(f"Saved data point: {self.id}")
            
        except Exception as e:
            logger.error(f"Error saving data point: {str(e)}")
            raise

@python_2_unicode_compatible
class BloodworkResult(models.Model):
    """
    Model for storing blood test results with enhanced security and verification.
    Implements secure file handling and lab result validation.
    """
    
    # Identity and relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data_point = models.OneToOneField(
        DataPoint,
        on_delete=models.PROTECT,
        related_name='bloodwork_result'
    )
    
    # Result data
    report_file = models.FileField(upload_to='bloodwork_reports/%Y/%m/')
    lab_name = models.CharField(max_length=255)
    test_date = models.DateField()
    file_hash = models.CharField(max_length=64)
    test_results = models.JSONField()
    lab_verification_code = models.CharField(max_length=50)
    
    # Security metadata
    security_metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['test_date']),
            models.Index(fields=['lab_name']),
            models.Index(fields=['created_at'])
        ]
        
    def __str__(self):
        return f"Blood Work - {self.lab_name} - {self.test_date}"

    def save(self, *args, **kwargs):
        """
        Enhanced save method with secure file handling and validation.
        
        Raises:
            ValidationException: If validation fails
        """
        try:
            # Validate lab verification
            if not self.lab_verification_code:
                raise ValidationException("Lab verification code required")
            
            # Process file upload
            if self.report_file:
                # Generate file hash
                self.file_hash = hash_file(self.report_file)
                
                # Upload to S3 with encryption
                s3 = boto3.client('s3')
                s3.upload_fileobj(
                    self.report_file,
                    'bloodwork-reports',
                    f"{self.id}/{self.report_file.name}",
                    ExtraArgs={'ServerSideEncryption': 'AES256'}
                )
            
            # Update security metadata
            self.security_metadata = {
                'file_hash': self.file_hash,
                'upload_date': timezone.now().isoformat(),
                'verification_status': 'verified',
                'retention_period': '7_years'
            }
            
            # Set timestamps
            if not self.pk:
                self.created_at = timezone.now()
            self.updated_at = timezone.now()
            
            super().save(*args, **kwargs)
            logger.info(f"Saved blood work result: {self.id}")
            
        except Exception as e:
            logger.error(f"Error saving blood work result: {str(e)}")
            raise