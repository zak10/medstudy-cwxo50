"""
Test suite for notification tasks in the Medical Research Platform.
Tests email notifications, safety alerts, and protocol-related communications
with comprehensive validation and security checks.

Version: 1.0.0
"""

import pytest
from unittest.mock import patch, Mock, call
from freezegun import freeze_time
from datetime import datetime, timedelta
import json

# Internal imports
from tasks.notifications import (
    send_email_notification,
    send_safety_alert,
    send_protocol_reminder,
    send_completion_notification,
    NotificationManager
)
from services.user.models import User
from core.exceptions import ValidationException

# Test constants
TEST_EMAIL_TEMPLATE = "test_notification.html"
TEST_USER_DATA = {
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
}
SAFETY_THRESHOLD_CONFIG = {
    "critical": 90,
    "warning": 70,
    "notice": 50
}

@pytest.fixture
def mock_ses_client():
    """Fixture for mocked AWS SES client."""
    with patch('boto3.client') as mock_client:
        mock_ses = Mock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        mock_client.return_value = mock_ses
        yield mock_ses

@pytest.fixture
def mock_notification_manager():
    """Fixture for mocked NotificationManager."""
    with patch('tasks.notifications.NotificationManager') as mock_nm:
        manager = Mock()
        manager._jinja_env.get_template.return_value.render.return_value = "Test email content"
        mock_nm.return_value = manager
        yield manager

@pytest.fixture
def test_user(db):
    """Fixture for test user creation."""
    return User.objects.create(
        email=TEST_USER_DATA["email"],
        first_name=TEST_USER_DATA["first_name"],
        last_name=TEST_USER_DATA["last_name"]
    )

@pytest.mark.django_db
class TestEmailNotifications:
    """Test cases for email notification functionality."""

    def test_send_email_notification_success(self, mock_ses_client, mock_notification_manager, test_user):
        """Tests successful email notification sending."""
        # Test data
        subject = "Test Notification"
        context = {
            "user_name": test_user.get_full_name(),
            "action_required": "Please verify your email"
        }

        # Execute task
        result = send_email_notification(
            recipient_email=test_user.email,
            subject=subject,
            template_name=TEST_EMAIL_TEMPLATE,
            context=context
        )

        # Verify email was sent
        assert result is True
        mock_ses_client.send_email.assert_called_once()
        call_args = mock_ses_client.send_email.call_args[1]
        assert call_args["Destination"]["ToAddresses"] == [test_user.email]
        assert call_args["Message"]["Subject"]["Data"] == subject

    def test_send_email_notification_retry(self, mock_ses_client, mock_notification_manager):
        """Tests email notification retry mechanism."""
        # Configure mock to fail initially
        mock_ses_client.send_email.side_effect = [
            Exception("Temporary failure"),
            {'MessageId': 'test-retry-id'}
        ]

        with pytest.raises(Exception):
            send_email_notification(
                recipient_email=TEST_USER_DATA["email"],
                subject="Retry Test",
                template_name=TEST_EMAIL_TEMPLATE,
                context={}
            )

        # Verify retry attempt
        assert mock_ses_client.send_email.call_count == 1

    @freeze_time("2024-01-01 12:00:00")
    def test_email_template_rendering(self, mock_notification_manager):
        """Tests email template rendering with context validation."""
        template_context = {
            "user_name": "Test User",
            "timestamp": datetime.now().isoformat(),
            "action_url": "https://example.com/verify"
        }

        # Render template
        mock_notification_manager._jinja_env.get_template.return_value.render.assert_not_called()
        
        send_email_notification(
            recipient_email=TEST_USER_DATA["email"],
            subject="Template Test",
            template_name=TEST_EMAIL_TEMPLATE,
            context=template_context
        )

        # Verify template rendering
        mock_notification_manager._jinja_env.get_template.assert_called_with(f"{TEST_EMAIL_TEMPLATE}.html")
        mock_notification_manager._jinja_env.get_template.return_value.render.assert_called_once()
        render_context = mock_notification_manager._jinja_env.get_template.return_value.render.call_args[1]
        assert all(key in render_context for key in template_context.keys())

@pytest.mark.django_db
class TestSafetyAlerts:
    """Test cases for safety alert notifications."""

    def test_send_safety_alert_critical(self, mock_notification_manager, test_user):
        """Tests critical safety alert notification."""
        # Test data
        protocol_id = "test-protocol-123"
        data_point = {
            "blood_pressure_systolic": 180,
            "timestamp": datetime.now().isoformat()
        }

        # Send alert
        send_safety_alert(
            protocol_id=protocol_id,
            participant_id=test_user.id,
            data_point=data_point
        )

        # Verify high-priority notification
        mock_notification_manager._ses_client.send_email.assert_called_once()
        call_args = mock_notification_manager._ses_client.send_email.call_args[1]
        assert "Safety Alert" in call_args["Message"]["Subject"]["Data"]

    def test_safety_alert_threshold_validation(self, mock_notification_manager):
        """Tests safety threshold validation logic."""
        data_points = [
            {"heart_rate": 95},  # Above warning
            {"heart_rate": 75},  # Normal
            {"heart_rate": 45},  # Below warning
        ]

        for data_point in data_points:
            send_safety_alert(
                protocol_id="test-protocol",
                participant_id="test-participant",
                data_point=data_point
            )

        # Verify alert frequency matches thresholds
        assert mock_notification_manager._ses_client.send_email.call_count == 2

@pytest.mark.django_db
class TestProtocolNotifications:
    """Test cases for protocol-related notifications."""

    def test_send_protocol_reminder(self, mock_notification_manager, test_user):
        """Tests protocol reminder notifications."""
        reminder_data = {
            "protocol_id": "test-protocol",
            "action_required": "Weekly check-in",
            "due_date": (datetime.now() + timedelta(days=1)).isoformat()
        }

        send_protocol_reminder(
            user_id=test_user.id,
            reminder_data=reminder_data
        )

        # Verify reminder email
        mock_notification_manager._ses_client.send_email.assert_called_once()
        call_args = mock_notification_manager._ses_client.send_email.call_args[1]
        assert "Reminder" in call_args["Message"]["Subject"]["Data"]

    def test_send_completion_notification(self, mock_notification_manager, test_user):
        """Tests protocol completion notifications."""
        completion_data = {
            "protocol_id": "test-protocol",
            "completion_date": datetime.now().isoformat(),
            "summary": {
                "data_points_submitted": 12,
                "completion_percentage": 100
            }
        }

        send_completion_notification(
            user_id=test_user.id,
            completion_data=completion_data
        )

        # Verify completion email
        mock_notification_manager._ses_client.send_email.assert_called_once()
        call_args = mock_notification_manager._ses_client.send_email.call_args[1]
        assert "Completion" in call_args["Message"]["Subject"]["Data"]

@pytest.mark.django_db
class TestNotificationPreferences:
    """Test cases for notification preference management."""

    def test_get_user_preferences(self, test_user):
        """Tests retrieval of user notification preferences."""
        manager = NotificationManager()
        
        # Test default preferences
        preferences = manager.get_user_preferences(test_user.id)
        assert preferences["email_enabled"] is True
        assert preferences["safety_alerts"] is True

    def test_invalid_user_preferences(self):
        """Tests handling of invalid user preferences."""
        manager = NotificationManager()
        
        with pytest.raises(ValidationException):
            manager.get_user_preferences("non-existent-user")

def test_notification_rate_limiting(mock_notification_manager):
    """Tests notification rate limiting functionality."""
    # Send multiple notifications rapidly
    for _ in range(5):
        send_email_notification(
            recipient_email=TEST_USER_DATA["email"],
            subject="Rate Limit Test",
            template_name=TEST_EMAIL_TEMPLATE,
            context={}
        )

    # Verify rate limiting
    assert mock_notification_manager._ses_client.send_email.call_count <= 3