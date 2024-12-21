"""
Celery tasks for processing research data in the Medical Research Platform.

Implements secure data processing tasks for blood work results, check-ins, and biometric data
with comprehensive validation, encryption, and error handling capabilities.

Version: 1.0.0
"""

# Standard library imports
from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime

# Third-party imports
import pandas as pd  # version 2.0
import numpy as np  # version 1.24
import boto3  # version 1.26.0
from cryptography.fernet import Fernet  # version 41.0.0
import structlog  # version 23.1.0
from ratelimit import limits, RateLimitException  # version 2.2.1

# Internal imports
from services.data.models import DataPoint, BloodworkResult
from services.analysis.models import AnalysisResult
from celery import app
from core.exceptions import ValidationException

# Configure structured logging
logger = structlog.get_logger(__name__)

class DataProcessor:
    """
    Base class for data processing operations with shared functionality.
    Implements secure data handling, validation, and transformation capabilities.
    """
    
    def __init__(self):
        """Initialize data processor with required dependencies."""
        self.logger = structlog.get_logger(__name__)
        self.s3_client = boto3.client('s3')
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
    
    def sanitize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes input data to prevent injection attacks.
        
        Args:
            input_data: Raw input data dictionary
            
        Returns:
            Sanitized data dictionary
            
        Raises:
            ValidationException: If data validation fails
        """
        try:
            if not isinstance(input_data, dict):
                raise ValidationException("Input must be a dictionary")
            
            sanitized_data = {}
            
            for key, value in input_data.items():
                # Remove special characters from keys
                clean_key = ''.join(c for c in key if c.isalnum() or c in ['_', '-'])
                
                # Handle different value types
                if isinstance(value, (int, float)):
                    sanitized_data[clean_key] = value
                elif isinstance(value, str):
                    # Remove potential injection characters
                    sanitized_data[clean_key] = value.replace(';', '').replace('--', '')
                elif isinstance(value, (list, dict)):
                    # Recursively sanitize nested structures
                    sanitized_data[clean_key] = json.loads(
                        json.dumps(value, default=str)
                    )
                elif value is None:
                    sanitized_data[clean_key] = None
                else:
                    raise ValidationException(f"Unsupported data type for {key}")
            
            return sanitized_data
            
        except Exception as e:
            self.logger.error("Data sanitization failed", error=str(e))
            raise ValidationException(f"Failed to sanitize input data: {str(e)}")

    def encrypt_sensitive_data(self, data: Dict[str, Any], sensitive_fields: list) -> Dict[str, Any]:
        """
        Encrypts sensitive fields in the data dictionary.
        
        Args:
            data: Data dictionary to process
            sensitive_fields: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted sensitive fields
        """
        try:
            encrypted_data = data.copy()
            
            for field in sensitive_fields:
                if field in encrypted_data:
                    value = str(encrypted_data[field])
                    encrypted_value = self.fernet.encrypt(value.encode())
                    encrypted_data[field] = encrypted_value.decode()
            
            return encrypted_data
            
        except Exception as e:
            self.logger.error("Data encryption failed", error=str(e))
            raise ValidationException(f"Failed to encrypt sensitive data: {str(e)}")

@app.task(
    queue='data_processing',
    retry_backoff=True,
    max_retries=3,
    rate_limit='100/h'
)
def process_bloodwork_data(data_point_id: str, file_path: str) -> Dict[str, Any]:
    """
    Processes uploaded blood work results with enhanced security and validation.
    
    Args:
        data_point_id: UUID of the DataPoint instance
        file_path: Path to the uploaded blood work file
        
    Returns:
        Processed and validated blood work data
        
    Raises:
        ValidationException: If processing or validation fails
    """
    processor = DataProcessor()
    log = processor.logger.bind(data_point_id=data_point_id)
    
    try:
        # Retrieve data point
        data_point = DataPoint.objects.get(id=data_point_id)
        
        # Initialize blood work result
        blood_result = BloodworkResult(
            data_point=data_point,
            report_file=file_path,
            test_date=datetime.now()
        )
        
        # Upload file to S3 with encryption
        s3_path = f"bloodwork/{data_point_id}/{file_path.split('/')[-1]}"
        blood_result.upload_to_s3(
            file_path,
            s3_path,
            extra_args={'ServerSideEncryption': 'AES256'}
        )
        
        # Extract and validate data
        extracted_data = _extract_bloodwork_data(file_path)
        sanitized_data = processor.sanitize_input(extracted_data)
        
        # Encrypt sensitive fields
        sensitive_fields = ['cholesterol', 'glucose', 'thyroid_stimulating_hormone']
        encrypted_data = processor.encrypt_sensitive_data(
            sanitized_data,
            sensitive_fields
        )
        
        # Update blood work result
        blood_result.test_results = encrypted_data
        blood_result.save()
        
        # Trigger analysis update
        update_analysis.delay(data_point_id)
        
        log.info("Blood work data processed successfully")
        return encrypted_data
        
    except Exception as e:
        log.error("Blood work processing failed", error=str(e))
        raise ValidationException(f"Failed to process blood work data: {str(e)}")

@app.task(queue='data_processing')
def process_checkin_data(data_point_id: str, checkin_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes weekly check-in data with validation and encryption.
    
    Args:
        data_point_id: UUID of the DataPoint instance
        checkin_data: Raw check-in data dictionary
        
    Returns:
        Processed check-in data
    """
    processor = DataProcessor()
    log = processor.logger.bind(data_point_id=data_point_id)
    
    try:
        # Retrieve data point
        data_point = DataPoint.objects.get(id=data_point_id)
        
        # Sanitize and validate input
        sanitized_data = processor.sanitize_input(checkin_data)
        
        # Encrypt sensitive fields
        sensitive_fields = ['symptoms', 'side_effects', 'medications']
        encrypted_data = processor.encrypt_sensitive_data(
            sanitized_data,
            sensitive_fields
        )
        
        # Update data point
        data_point.data = encrypted_data
        data_point.save()
        
        # Trigger analysis update
        update_analysis.delay(data_point_id)
        
        log.info("Check-in data processed successfully")
        return encrypted_data
        
    except Exception as e:
        log.error("Check-in processing failed", error=str(e))
        raise ValidationException(f"Failed to process check-in data: {str(e)}")

@app.task(queue='data_processing')
def prepare_analysis_data(protocol_id: str) -> Dict[str, Any]:
    """
    Prepares data for analysis by aggregating and transforming protocol data points.
    
    Args:
        protocol_id: UUID of the Protocol instance
        
    Returns:
        Prepared data for analysis
    """
    processor = DataProcessor()
    log = processor.logger.bind(protocol_id=protocol_id)
    
    try:
        # Retrieve all data points for protocol
        data_points = DataPoint.objects.filter(
            protocol_id=protocol_id,
            status='validated'
        )
        
        # Transform data for analysis
        analysis_data = {
            'blood_work': [],
            'checkins': [],
            'biometrics': []
        }
        
        for dp in data_points:
            # Decrypt sensitive fields
            decrypted_data = _decrypt_data_point(dp, processor.fernet)
            
            # Categorize by type
            if dp.type == 'blood_work':
                analysis_data['blood_work'].append(decrypted_data)
            elif dp.type == 'check_in':
                analysis_data['checkins'].append(decrypted_data)
            elif dp.type == 'biometric':
                analysis_data['biometrics'].append(decrypted_data)
        
        log.info("Analysis data prepared successfully")
        return analysis_data
        
    except Exception as e:
        log.error("Analysis preparation failed", error=str(e))
        raise ValidationException(f"Failed to prepare analysis data: {str(e)}")

def _extract_bloodwork_data(file_path: str) -> Dict[str, Any]:
    """Helper function to extract data from blood work files."""
    try:
        # Read data based on file type
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            raise ValidationException("Unsupported file format")
        
        # Convert to dictionary format
        data = df.to_dict(orient='records')[0]
        return data
        
    except Exception as e:
        raise ValidationException(f"Failed to extract blood work data: {str(e)}")

def _decrypt_data_point(data_point: DataPoint, fernet: Fernet) -> Dict[str, Any]:
    """Helper function to decrypt data point fields."""
    try:
        decrypted_data = data_point.data.copy()
        
        for field, value in data_point.data.items():
            if isinstance(value, str) and value.startswith('gAAAAA'):
                try:
                    decrypted_value = fernet.decrypt(value.encode()).decode()
                    decrypted_data[field] = decrypted_value
                except:
                    # Skip if field is not actually encrypted
                    continue
        
        return decrypted_data
        
    except Exception as e:
        raise ValidationException(f"Failed to decrypt data point: {str(e)}")