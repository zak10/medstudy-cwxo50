"""
Celery tasks package initialization for the Medical Research Platform.

Exposes key asynchronous task functions for protocol data analysis, data processing,
and notifications. Provides centralized task registration and organization for all
background processing operations.

Version: 1.0.0
Author: Medical Research Platform Team
"""

# Import task functions from submodules
from tasks.analysis import (
    process_protocol_data,
    detect_signals,
    generate_cohort_analysis
)

from tasks.data_processing import (
    process_blood_work,
    process_weekly_checkin,
    normalize_data_point
)

from tasks.notifications import (
    send_email_notification,
    send_protocol_reminder,
    send_data_submission_alert,
    send_safety_notification
)

# Import Celery app instance
from celery import Celery  # version 5.3.0

# Package metadata
__version__ = '1.0.0'
__author__ = 'Medical Research Platform Team'

# Define public API
__all__ = [
    # Analysis tasks
    'process_protocol_data',
    'detect_signals', 
    'generate_cohort_analysis',
    
    # Data processing tasks
    'process_blood_work',
    'process_weekly_checkin',
    'normalize_data_point',
    
    # Notification tasks
    'send_email_notification',
    'send_protocol_reminder',
    'send_data_submission_alert',
    'send_safety_notification'
]

# Register tasks with Celery app
app = Celery('medical_research')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in registered Django apps
app.autodiscover_tasks()