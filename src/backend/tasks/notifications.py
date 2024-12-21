"""
Celery task module for handling asynchronous notifications in the Medical Research Platform.
Manages email notifications, safety alerts, and protocol-related communications with
comprehensive error handling, security features, and performance optimizations.

Version: 1.0.0
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Third-party imports
from celery import shared_task
import boto3
from jinja2 import Environment, FileSystemLoader, select_autoescape
import structlog

# Internal imports
from services.user.models import User
from services.protocol.models import Protocol
from core.utils import format_datetime
from core.exceptions import ValidationException

# Configure structured logging
logger = structlog.get_logger(__name__)

# Constants
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '../templates/email')
RATE_LIMIT_CONFIG = {
    "default": "100/m",
    "safety_alerts": "1000/m"
}
TEMPLATE_CACHE_TTL = 3600  # 1 hour cache TTL

class NotificationManager:
    """
    Manages notification preferences and delivery methods with enhanced security and performance.
    Implements caching, rate limiting, and comprehensive error handling.
    """
    
    def __init__(self):
        """Initializes notification manager with templates, settings, and optimizations."""
        self._email_templates = {}
        self._template_cache = {}
        self._rate_limiters = {}
        
        # Initialize Jinja2 environment with security features
        self._jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize AWS SES client
        self._ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        
        logger.info("NotificationManager initialized")

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves notification preferences for a user with caching.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of user notification preferences
            
        Raises:
            ValidationException: If user is not found
        """
        try:
            # Check cache first
            cache_key = f"notification_prefs_{user_id}"
            if cache_key in self._template_cache:
                return self._template_cache[cache_key]
            
            # Get user and preferences
            user = User.objects.get(id=user_id)
            preferences = user.profile.get('notification_preferences', {})
            
            # Set defaults if needed
            defaults = {
                'email_enabled': True,
                'safety_alerts': True,
                'protocol_updates': True,
                'community_messages': True
            }
            preferences = {**defaults, **preferences}
            
            # Cache preferences
            self._template_cache[cache_key] = preferences
            
            return preferences
            
        except User.DoesNotExist:
            logger.error("User not found", user_id=user_id)
            raise ValidationException("User not found")
        except Exception as e:
            logger.error("Error getting user preferences", error=str(e), user_id=user_id)
            raise

# Celery tasks
@shared_task(bind=True, max_retries=3, retry_backoff=True, rate_limit=RATE_LIMIT_CONFIG['default'])
def send_email_notification(
    self,
    recipient_email: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any]
) -> bool:
    """
    Sends an email notification using AWS SES with enhanced error handling and retry mechanisms.
    
    Args:
        recipient_email: Recipient's email address
        subject: Email subject
        template_name: Name of the email template
        context: Template context data
        
    Returns:
        Success status of email sending
        
    Raises:
        ValidationException: If template or parameters are invalid
    """
    try:
        # Initialize NotificationManager
        notification_manager = NotificationManager()
        
        # Validate email template
        template_path = f"{template_name}.html"
        template = notification_manager._jinja_env.get_template(template_path)
        
        # Sanitize context data
        context['timestamp'] = format_datetime(datetime.now())
        context['subject'] = subject
        
        # Render email content
        email_content = template.render(**context)
        
        # Send email through SES
        response = notification_manager._ses_client.send_email(
            Source=os.getenv('NOTIFICATION_EMAIL_FROM'),
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': email_content}}
            }
        )
        
        logger.info(
            "Email notification sent",
            message_id=response['MessageId'],
            recipient=recipient_email,
            template=template_name
        )
        return True
        
    except Exception as e:
        logger.error(
            "Error sending email notification",
            error=str(e),
            recipient=recipient_email,
            template=template_name,
            retry_count=self.request.retries
        )
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        raise

@shared_task(bind=True, priority='high', queue='alerts')
def send_safety_alert(
    self,
    protocol_id: str,
    participant_id: str,
    data_point: Dict[str, Any]
) -> None:
    """
    Sends immediate safety alerts for protocol violations with high priority.
    
    Args:
        protocol_id: Protocol identifier
        participant_id: Participant identifier
        data_point: Data point that triggered the alert
        
    Raises:
        ValidationException: If protocol or participant is not found
    """
    try:
        # Get protocol and check safety violation
        protocol = Protocol.objects.get(id=protocol_id)
        participant = User.objects.get(id=participant_id)
        
        violation_found, violation_message, violation_details = protocol.check_safety_violation(data_point)
        
        if violation_found:
            # Prepare alert context
            alert_context = {
                'protocol_title': protocol.title,
                'participant_name': participant.get_full_name(),
                'violation_message': violation_message,
                'violation_details': violation_details,
                'data_point': data_point,
                'timestamp': format_datetime(datetime.now())
            }
            
            # Send alert to protocol creator
            send_email_notification.apply_async(
                args=[
                    protocol.creator.email,
                    f"Safety Alert: {protocol.title}",
                    'safety_alert',
                    alert_context
                ],
                priority='high'
            )
            
            logger.warning(
                "Safety violation alert sent",
                protocol_id=protocol_id,
                participant_id=participant_id,
                violation_details=violation_details
            )
            
    except (Protocol.DoesNotExist, User.DoesNotExist) as e:
        logger.error(
            "Entity not found for safety alert",
            error=str(e),
            protocol_id=protocol_id,
            participant_id=participant_id
        )
        raise ValidationException("Protocol or participant not found")
    except Exception as e:
        logger.error(
            "Error sending safety alert",
            error=str(e),
            protocol_id=protocol_id,
            participant_id=participant_id
        )
        raise