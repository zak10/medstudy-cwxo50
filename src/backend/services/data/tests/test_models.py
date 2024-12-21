"""
Unit tests for data service models ensuring data quality, security, and protocol compliance.
Tests DataPoint, BloodworkResult, and CheckIn models with comprehensive validation.

Version: 1.0.0
"""

from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from freezegun import freeze_time  # version: 1.2

from services.data.models import DataPoint, BloodworkResult, CheckIn
from services.protocol.models import Protocol
from services.user.models import User

class DataPointTest(TestCase):
    """
    Test cases for DataPoint model with comprehensive validation and security checks.
    """
    
    def setUp(self):
        """Set up test environment with required data."""
        # Create test user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User"
        )
        
        # Create test protocol with requirements
        self.protocol = Protocol.objects.create(
            title="Test Protocol",
            creator=self.user,
            requirements={
                "data_points": [
                    {
                        "name": "vitamin_d",
                        "type": "number",
                        "unit": "ng/mL",
                        "range": {"min": 20, "max": 80}
                    }
                ],
                "frequency": {"type": "weekly", "value": 1},
                "duration": 12
            },
            safety_params={
                "vitamin_d": {"min": 10, "max": 100}
            },
            duration_weeks=12,
            max_participants=100
        )
        
        # Initialize valid test data
        self.valid_data = {
            "vitamin_d": 45.5,
            "collection_date": timezone.now().isoformat(),
            "notes": "Normal test results"
        }

    def test_create_data_point(self):
        """Test creating a valid data point with all required fields."""
        data_point = DataPoint.objects.create(
            protocol=self.protocol,
            user=self.user,
            type="blood_work",
            data=self.valid_data,
            recorded_at=timezone.now(),
            status="pending"
        )
        
        # Verify basic fields
        self.assertIsNotNone(data_point.id)
        self.assertEqual(data_point.protocol, self.protocol)
        self.assertEqual(data_point.user, self.user)
        self.assertEqual(data_point.type, "blood_work")
        self.assertEqual(data_point.status, "pending")
        
        # Verify data content
        self.assertEqual(data_point.data["vitamin_d"], 45.5)
        self.assertIn("collection_date", data_point.data)
        self.assertIn("notes", data_point.data)
        
        # Verify audit trail
        self.assertEqual(len(data_point.audit_trail), 1)
        self.assertEqual(data_point.audit_trail[0]["action"], "create")
        
        # Verify encryption metadata
        self.assertIn("encrypted_fields", data_point.encryption_metadata)
        self.assertIn("encryption_version", data_point.encryption_metadata)

    @freeze_time("2024-01-01 12:00:00")
    def test_data_validation(self):
        """Test comprehensive data validation against protocol requirements."""
        # Test invalid value range
        invalid_data = self.valid_data.copy()
        invalid_data["vitamin_d"] = 150  # Above max range
        
        with self.assertRaises(ValidationException) as context:
            DataPoint.objects.create(
                protocol=self.protocol,
                user=self.user,
                type="blood_work",
                data=invalid_data,
                recorded_at=timezone.now()
            )
        self.assertIn("value exceeds maximum", str(context.exception))
        
        # Test missing required field
        invalid_data = self.valid_data.copy()
        del invalid_data["vitamin_d"]
        
        with self.assertRaises(ValidationException) as context:
            DataPoint.objects.create(
                protocol=self.protocol,
                user=self.user,
                type="blood_work",
                data=invalid_data,
                recorded_at=timezone.now()
            )
        self.assertIn("required field missing", str(context.exception))
        
        # Test invalid data type
        invalid_data = self.valid_data.copy()
        invalid_data["vitamin_d"] = "not_a_number"
        
        with self.assertRaises(ValidationException) as context:
            DataPoint.objects.create(
                protocol=self.protocol,
                user=self.user,
                type="blood_work",
                data=invalid_data,
                recorded_at=timezone.now()
            )
        self.assertIn("invalid data type", str(context.exception))

    def test_security_validation(self):
        """Test security validation features including encryption and audit logging."""
        data_point = DataPoint.objects.create(
            protocol=self.protocol,
            user=self.user,
            type="blood_work",
            data=self.valid_data,
            recorded_at=timezone.now()
        )
        
        # Test data encryption
        self.assertNotEqual(
            data_point.data["notes"],
            self.valid_data["notes"],
            "Sensitive data should be encrypted"
        )
        
        # Test audit trail
        data_point.status = "validated"
        data_point.save()
        
        self.assertEqual(len(data_point.audit_trail), 2)
        self.assertEqual(data_point.audit_trail[-1]["action"], "update")
        self.assertEqual(data_point.audit_trail[-1]["status"], "validated")

class BloodworkResultTest(TestCase):
    """
    Test cases for BloodworkResult model with enhanced security and file handling.
    """
    
    def setUp(self):
        """Set up test environment for blood work testing."""
        # Create test data point
        self.data_point = DataPoint.objects.create(
            protocol=Protocol.objects.create(
                title="Test Protocol",
                creator=User.objects.create_user(
                    email="test@example.com",
                    password="TestPass123!",
                    first_name="Test",
                    last_name="User"
                ),
                requirements={"data_points": []},
                duration_weeks=12,
                max_participants=100
            ),
            user=User.objects.get(email="test@example.com"),
            type="blood_work",
            data={},
            recorded_at=timezone.now()
        )
        
        # Create test file
        self.test_file_content = b"Test blood work report content"
        self.test_file = SimpleUploadedFile(
            "test_report.pdf",
            self.test_file_content,
            content_type="application/pdf"
        )

    @patch('boto3.client')
    def test_upload_to_s3(self, mock_s3):
        """Test secure file upload to S3 with proper encryption and validation."""
        # Configure mock S3 client
        mock_s3_client = mock_s3.return_value
        mock_s3_client.upload_fileobj.return_value = None
        
        # Create blood work result
        result = BloodworkResult.objects.create(
            data_point=self.data_point,
            report_file=self.test_file,
            lab_name="Test Lab",
            test_date=timezone.now().date(),
            test_results={"vitamin_d": 45.5},
            lab_verification_code="TEST123"
        )
        
        # Verify S3 upload
        mock_s3_client.upload_fileobj.assert_called_once()
        call_args = mock_s3_client.upload_fileobj.call_args
        self.assertIn('ServerSideEncryption', call_args[1]['ExtraArgs'])
        
        # Verify file hash
        self.assertIsNotNone(result.file_hash)
        self.assertEqual(len(result.file_hash), 64)  # SHA-256 hash length
        
        # Verify security metadata
        self.assertIn('file_hash', result.security_metadata)
        self.assertIn('upload_date', result.security_metadata)
        self.assertEqual(
            result.security_metadata['verification_status'],
            'verified'
        )

    def test_file_validation(self):
        """Test comprehensive file validation including size and type checks."""
        # Test invalid file type
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"Invalid file type",
            content_type="text/plain"
        )
        
        with self.assertRaises(ValidationException) as context:
            BloodworkResult.objects.create(
                data_point=self.data_point,
                report_file=invalid_file,
                lab_name="Test Lab",
                test_date=timezone.now().date(),
                test_results={"vitamin_d": 45.5},
                lab_verification_code="TEST123"
            )
        self.assertIn("invalid file type", str(context.exception))
        
        # Test file size limit
        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (10 * 1024 * 1024),  # 10MB file
            content_type="application/pdf"
        )
        
        with self.assertRaises(ValidationException) as context:
            BloodworkResult.objects.create(
                data_point=self.data_point,
                report_file=large_file,
                lab_name="Test Lab",
                test_date=timezone.now().date(),
                test_results={"vitamin_d": 45.5},
                lab_verification_code="TEST123"
            )
        self.assertIn("file size exceeds limit", str(context.exception))

class CheckInTest(TestCase):
    """
    Test cases for CheckIn model with enhanced validation and sanitization.
    """
    
    def setUp(self):
        """Set up test environment for check-in testing."""
        # Create test data point
        self.data_point = DataPoint.objects.create(
            protocol=Protocol.objects.create(
                title="Test Protocol",
                creator=User.objects.create_user(
                    email="test@example.com",
                    password="TestPass123!",
                    first_name="Test",
                    last_name="User"
                ),
                requirements={"data_points": []},
                duration_weeks=12,
                max_participants=100
            ),
            user=User.objects.get(email="test@example.com"),
            type="check_in",
            data={},
            recorded_at=timezone.now()
        )
        
        # Initialize valid test data
        self.valid_data = {
            "energy_level": 4,
            "sleep_quality": 3,
            "side_effects": None,
            "notes": "Feeling good today"
        }

    def test_rating_validation(self):
        """Test comprehensive rating validation for check-in data."""
        # Test invalid rating range
        invalid_data = self.valid_data.copy()
        invalid_data["energy_level"] = 6  # Above max range
        
        with self.assertRaises(ValidationException) as context:
            CheckIn.objects.create(
                data_point=self.data_point,
                ratings=invalid_data
            )
        self.assertIn("rating out of range", str(context.exception))
        
        # Test missing required rating
        invalid_data = self.valid_data.copy()
        del invalid_data["energy_level"]
        
        with self.assertRaises(ValidationException) as context:
            CheckIn.objects.create(
                data_point=self.data_point,
                ratings=invalid_data
            )
        self.assertIn("required rating missing", str(context.exception))

    def test_notes_handling(self):
        """Test secure notes handling with proper sanitization."""
        # Test HTML sanitization
        data_with_html = self.valid_data.copy()
        data_with_html["notes"] = "<script>alert('xss')</script>Normal note"
        
        check_in = CheckIn.objects.create(
            data_point=self.data_point,
            ratings=data_with_html
        )
        
        self.assertNotIn("<script>", check_in.ratings["notes"])
        self.assertIn("Normal note", check_in.ratings["notes"])
        
        # Test notes length limit
        data_with_long_note = self.valid_data.copy()
        data_with_long_note["notes"] = "x" * 1001  # Exceed 1000 char limit
        
        with self.assertRaises(ValidationException) as context:
            CheckIn.objects.create(
                data_point=self.data_point,
                ratings=data_with_long_note
            )
        self.assertIn("notes exceed maximum length", str(context.exception))