"""
Comprehensive test suite for data processing tasks in the Medical Research Platform.
Implements thorough testing of data processing, validation, security, and performance.

Version: 1.0.0
"""

# Standard library imports
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest  # version 7.4+
from faker import Faker  # version 18.13
from freezegun import freeze_time  # version 1.2

# Internal imports
from tasks.data_processing import (
    process_bloodwork_data,
    process_checkin_data,
    prepare_analysis_data,
    validate_data_point
)
from services.data.models import DataPoint, BloodworkResult
from core.exceptions import ValidationException

# Initialize Faker for generating test data
fake = Faker()

@pytest.fixture
def mock_s3():
    """Fixture for mocking S3 interactions with security validation."""
    with patch('boto3.client') as mock_client:
        s3_mock = MagicMock()
        mock_client.return_value = s3_mock
        yield s3_mock

@pytest.fixture
def mock_data_point():
    """Fixture for creating test data points with proper validation."""
    def _create_data_point(data_type: str = 'blood_work', status: str = 'pending') -> DataPoint:
        return DataPoint.objects.create(
            protocol_id=fake.uuid4(),
            user_id=fake.uuid4(),
            type=data_type,
            data={},
            recorded_at=datetime.now(),
            status=status
        )
    return _create_data_point

@pytest.fixture
def mock_bloodwork_file(tmp_path):
    """Fixture for creating mock blood work files with security checks."""
    def _create_file(file_type: str = 'csv') -> str:
        file_path = tmp_path / f"test_bloodwork.{file_type}"
        test_data = {
            'cholesterol': fake.random_int(150, 300),
            'glucose': fake.random_int(70, 120),
            'thyroid_stimulating_hormone': fake.random_float(0.4, 4.0)
        }
        
        if file_type == 'csv':
            content = "parameter,value\n"
            for key, value in test_data.items():
                content += f"{key},{value}\n"
        else:
            content = json.dumps(test_data)
            
        file_path.write_text(content)
        return str(file_path)
    return _create_file

class TestDataProcessing:
    """
    Comprehensive test suite for data processing tasks with security,
    performance, and validation testing.
    """
    
    def setup_method(self):
        """Set up test environment with security and monitoring configuration."""
        self.faker = Faker()
        self.performance_threshold = 5.0  # seconds
        
    @pytest.mark.django_db
    @patch('boto3.client')
    @pytest.mark.timeout(5)
    @freeze_time('2024-01-01')
    def test_process_bloodwork_data_success(
        self,
        mock_s3_client,
        mock_data_point,
        mock_bloodwork_file
    ):
        """Test successful blood work data processing with security validation."""
        # Arrange
        data_point = mock_data_point('blood_work')
        file_path = mock_bloodwork_file('csv')
        
        # Configure S3 mock with security checks
        s3_mock = MagicMock()
        mock_s3_client.return_value = s3_mock
        
        # Act
        result = process_bloodwork_data(str(data_point.id), file_path)
        
        # Assert
        assert result is not None
        assert 'cholesterol' in result
        assert 'glucose' in result
        assert 'thyroid_stimulating_hormone' in result
        
        # Verify security measures
        s3_mock.upload_fileobj.assert_called_once()
        upload_args = s3_mock.upload_fileobj.call_args[1]
        assert upload_args['ExtraArgs']['ServerSideEncryption'] == 'AES256'
        
        # Verify data point updates
        data_point.refresh_from_db()
        assert data_point.status == 'validated'
        assert len(data_point.audit_trail) > 0
        
    @pytest.mark.django_db
    @pytest.mark.security
    def test_process_bloodwork_data_security(
        self,
        mock_data_point,
        mock_bloodwork_file
    ):
        """Test blood work data security measures and validation."""
        # Arrange
        data_point = mock_data_point('blood_work')
        file_path = mock_bloodwork_file('csv')
        
        # Test file type validation
        with pytest.raises(ValidationException) as exc_info:
            process_bloodwork_data(str(data_point.id), 'invalid.exe')
        assert 'Unsupported file format' in str(exc_info.value)
        
        # Test data sanitization
        malicious_file = mock_bloodwork_file('csv')
        with open(malicious_file, 'w') as f:
            f.write('parameter,value\nmalicious","=cmd.exe\n')
            
        with pytest.raises(ValidationException):
            process_bloodwork_data(str(data_point.id), malicious_file)
            
    @pytest.mark.django_db
    @pytest.mark.timeout(5)
    def test_process_checkin_data_success(self, mock_data_point):
        """Test successful check-in data processing with validation."""
        # Arrange
        data_point = mock_data_point('check_in')
        checkin_data = {
            'energy_level': fake.random_int(1, 5),
            'sleep_quality': fake.random_int(1, 5),
            'side_effects': fake.text(max_nb_chars=200),
            'compliance': True
        }
        
        # Act
        result = process_checkin_data(str(data_point.id), checkin_data)
        
        # Assert
        assert result is not None
        assert all(key in result for key in checkin_data.keys())
        
        # Verify data encryption
        data_point.refresh_from_db()
        assert 'side_effects' in data_point.encryption_metadata['encrypted_fields']
        
    @pytest.mark.django_db
    def test_process_checkin_data_validation(self, mock_data_point):
        """Test check-in data validation and error handling."""
        # Arrange
        data_point = mock_data_point('check_in')
        
        # Test invalid energy level
        invalid_data = {'energy_level': 10}  # Out of range
        with pytest.raises(ValidationException) as exc_info:
            process_checkin_data(str(data_point.id), invalid_data)
        assert 'Invalid energy level' in str(exc_info.value)
        
        # Test missing required fields
        with pytest.raises(ValidationException) as exc_info:
            process_checkin_data(str(data_point.id), {})
        assert 'Missing required fields' in str(exc_info.value)
        
    @pytest.mark.django_db
    @pytest.mark.timeout(10)
    def test_prepare_analysis_data_success(self, mock_data_point):
        """Test successful analysis data preparation with performance monitoring."""
        # Arrange
        protocol_id = fake.uuid4()
        data_points = []
        
        # Create test data points
        for _ in range(5):
            dp = mock_data_point('blood_work')
            dp.protocol_id = protocol_id
            dp.status = 'validated'
            dp.save()
            data_points.append(dp)
            
        # Act
        result = prepare_analysis_data(protocol_id)
        
        # Assert
        assert result is not None
        assert 'blood_work' in result
        assert len(result['blood_work']) == 5
        
        # Verify data structure
        for data in result['blood_work']:
            assert isinstance(data, dict)
            assert all(key in data for key in ['recorded_at', 'values'])
            
    @pytest.mark.django_db
    @pytest.mark.parametrize('data_type', ['blood_work', 'check_in', 'biometric'])
    def test_validate_data_point(self, mock_data_point, data_type):
        """Test comprehensive data point validation for different types."""
        # Arrange
        data_point = mock_data_point(data_type)
        test_data = self._generate_test_data(data_type)
        
        # Act
        result = validate_data_point(str(data_point.id), test_data)
        
        # Assert
        assert result['is_valid'] is True
        assert 'validation_details' in result
        
        # Verify audit logging
        data_point.refresh_from_db()
        assert len(data_point.audit_trail) > 0
        assert data_point.audit_trail[-1]['action'] == 'validation'
        
    def _generate_test_data(self, data_type: str) -> Dict[str, Any]:
        """Helper method to generate type-specific test data."""
        if data_type == 'blood_work':
            return {
                'cholesterol': fake.random_int(150, 300),
                'glucose': fake.random_int(70, 120),
                'thyroid_stimulating_hormone': fake.random_float(0.4, 4.0)
            }
        elif data_type == 'check_in':
            return {
                'energy_level': fake.random_int(1, 5),
                'sleep_quality': fake.random_int(1, 5),
                'side_effects': fake.text(max_nb_chars=200),
                'compliance': fake.boolean()
            }
        else:  # biometric
            return {
                'weight': fake.random_int(50, 100),
                'blood_pressure_systolic': fake.random_int(90, 140),
                'blood_pressure_diastolic': fake.random_int(60, 90),
                'heart_rate': fake.random_int(60, 100)
            }