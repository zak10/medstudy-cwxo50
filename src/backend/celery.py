"""
Celery application configuration for the Medical Research Platform.

Implements distributed task processing with comprehensive monitoring, error handling,
and security controls for data processing, analysis, and notification workloads.
"""

import os
from typing import Any, Dict, Optional, Tuple

from celery import Celery
from celery.signals import (
    task_failure, task_received, task_success, 
    worker_ready, worker_shutdown
)
from kombu import Exchange, Queue
import prometheus_client as prom
import structlog

from config.settings.base import (
    CELERY_TASK_TRACK_STARTED,
    CELERY_TASK_TIME_LIMIT,
    CELERY_ACCEPT_CONTENT,
    CELERY_TASK_SERIALIZER,
    CELERY_RESULT_SERIALIZER
)

# Configure structured logging
logger = structlog.get_logger(__name__)

# Define queue configurations with priorities and TTL
CELERY_QUEUES = {
    'data_processing': {
        'exchange': 'medical_research',
        'routing_key': 'data_processing',
        'queue_arguments': {
            'x-max-priority': 10,
            'x-message-ttl': 3600000,  # 1 hour TTL
            'x-dead-letter-exchange': 'medical_research.dlx',
            'x-dead-letter-routing-key': 'data_processing.dlq'
        }
    },
    'analysis': {
        'exchange': 'medical_research',
        'routing_key': 'analysis',
        'queue_arguments': {
            'x-max-priority': 5,
            'x-message-ttl': 7200000,  # 2 hours TTL
            'x-dead-letter-exchange': 'medical_research.dlx',
            'x-dead-letter-routing-key': 'analysis.dlq'
        }
    },
    'notifications': {
        'exchange': 'medical_research',
        'routing_key': 'notifications',
        'queue_arguments': {
            'x-max-priority': 3,
            'x-message-ttl': 1800000,  # 30 minutes TTL
            'x-dead-letter-exchange': 'medical_research.dlx',
            'x-dead-letter-routing-key': 'notifications.dlq'
        }
    }
}

class MedicalResearchCelery(Celery):
    """
    Custom Celery application class with enhanced monitoring, security,
    and error handling capabilities for medical research workloads.
    """

    def __init__(self) -> None:
        """Initialize the Celery application with comprehensive configuration."""
        super().__init__('medical_research')
        
        # Initialize Prometheus metrics
        self.metrics = {
            'tasks_total': prom.Counter(
                'celery_tasks_total',
                'Total number of Celery tasks processed',
                ['queue', 'status']
            ),
            'task_duration_seconds': prom.Histogram(
                'celery_task_duration_seconds',
                'Task processing duration in seconds',
                ['queue', 'task_type']
            ),
            'queue_size': prom.Gauge(
                'celery_queue_size',
                'Number of tasks in queue',
                ['queue']
            )
        }
        
        # Configure core settings
        self.config_from_object('django.conf:settings', namespace='CELERY')
        self.conf.update(
            task_track_started=CELERY_TASK_TRACK_STARTED,
            task_time_limit=CELERY_TASK_TIME_LIMIT,
            accept_content=CELERY_ACCEPT_CONTENT,
            task_serializer=CELERY_TASK_SERIALIZER,
            result_serializer=CELERY_RESULT_SERIALIZER,
            broker_transport_options={
                'visibility_timeout': 3600,
                'max_retries': 3,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.5,
            },
            task_routes={
                'tasks.data_processing.*': {
                    'queue': 'data_processing',
                    'rate_limit': '100/m',
                    'priority': 8
                },
                'tasks.analysis.*': {
                    'queue': 'analysis',
                    'rate_limit': '50/m',
                    'priority': 5
                },
                'tasks.notifications.*': {
                    'queue': 'notifications',
                    'rate_limit': '200/m',
                    'priority': 3
                }
            },
            task_default_queue='data_processing',
            task_queues=[
                Queue(
                    name,
                    Exchange(config['exchange']),
                    routing_key=config['routing_key'],
                    queue_arguments=config['queue_arguments']
                )
                for name, config in CELERY_QUEUES.items()
            ],
            task_annotations={
                '*': {
                    'rate_limit': '1000/m',
                    'max_retries': 3,
                    'retry_backoff': True,
                    'retry_backoff_max': 600,  # 10 minutes
                    'retry_jitter': True
                }
            }
        )

        # Register signal handlers
        task_received.connect(self._on_task_received)
        task_success.connect(self._on_task_success)
        task_failure.connect(self._on_task_failure)
        worker_ready.connect(self._on_worker_ready)
        worker_shutdown.connect(self._on_worker_shutdown)

    def _on_task_received(self, sender: Any, **kwargs: Dict[str, Any]) -> None:
        """Handle task received signal for monitoring."""
        task_name = sender.name
        queue = sender.request.delivery_info.get('routing_key', 'default')
        
        self.metrics['tasks_total'].labels(queue=queue, status='received').inc()
        self.metrics['queue_size'].labels(queue=queue).inc()
        
        logger.info(
            'task_received',
            task_name=task_name,
            queue=queue,
            correlation_id=sender.request.id
        )

    def _on_task_success(self, sender: Any, **kwargs: Dict[str, Any]) -> None:
        """Handle task success signal for monitoring."""
        task_name = sender.name
        queue = sender.request.delivery_info.get('routing_key', 'default')
        duration = kwargs.get('runtime', 0)
        
        self.metrics['tasks_total'].labels(queue=queue, status='success').inc()
        self.metrics['task_duration_seconds'].labels(
            queue=queue,
            task_type=task_name
        ).observe(duration)
        self.metrics['queue_size'].labels(queue=queue).dec()
        
        logger.info(
            'task_success',
            task_name=task_name,
            queue=queue,
            duration=duration,
            correlation_id=sender.request.id
        )

    def _on_task_failure(
        self,
        sender: Any,
        task_id: str,
        exception: Exception,
        **kwargs: Dict[str, Any]
    ) -> None:
        """Handle task failure signal with error tracking and metrics."""
        task_name = sender.name
        queue = sender.request.delivery_info.get('routing_key', 'default')
        
        self.metrics['tasks_total'].labels(queue=queue, status='failure').inc()
        self.metrics['queue_size'].labels(queue=queue).dec()
        
        logger.error(
            'task_failure',
            task_name=task_name,
            queue=queue,
            error=str(exception),
            correlation_id=task_id,
            exc_info=True
        )

    def _on_worker_ready(self, sender: Any, **kwargs: Dict[str, Any]) -> None:
        """Handle worker ready signal for monitoring."""
        logger.info(
            'worker_ready',
            hostname=sender.hostname,
            pid=os.getpid()
        )

    def _on_worker_shutdown(self, sender: Any, **kwargs: Dict[str, Any]) -> None:
        """Handle worker shutdown signal for monitoring."""
        logger.info(
            'worker_shutdown',
            hostname=sender.hostname,
            pid=os.getpid()
        )

def init_celery() -> MedicalResearchCelery:
    """
    Initialize and configure the Celery application instance.
    
    Returns:
        MedicalResearchCelery: Configured Celery application instance
    """
    app = MedicalResearchCelery()
    app.autodiscover_tasks()
    return app

# Initialize the Celery application
app = init_celery()