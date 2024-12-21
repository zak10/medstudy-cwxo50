#!/bin/bash

# Medical Research Platform - Celery Worker Startup Script
# Version: 1.0.0
# Celery Version: 5.3.0
# Description: Production-ready script to initialize and manage Celery workers
# with advanced configuration for data analysis, processing, and notifications

set -e  # Exit on error
set -u  # Exit on undefined variable

# Environment configuration
export DJANGO_SETTINGS_MODULE="config.settings.production"
export PYTHONPATH="/app"  # Docker container Python path

# Celery configuration
export CELERY_BROKER_URL=${CELERY_BROKER_URL:-"amqp://rabbitmq:5672"}
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-"redis://redis:6379/0"}
export CELERY_TASK_ALWAYS_EAGER="False"
export CELERY_TASK_SERIALIZER="json"
export CELERY_RESULT_SERIALIZER="json"
export CELERY_ACCEPT_CONTENT='["json"]'
export CELERY_TIMEZONE="UTC"

# Worker configuration
CELERY_APP="medical_research_platform"
QUEUES="analysis,data_processing,notifications"
CONCURRENCY=${WORKER_CONCURRENCY:-4}
LOG_LEVEL=${LOG_LEVEL:-"INFO"}
TASK_TIME_LIMIT=3600  # 1 hour
TASK_SOFT_TIME_LIMIT=3300  # 55 minutes
MAX_TASKS_PER_CHILD=10000
WORKER_PREFETCH_MULTIPLIER=4

# Health check function
check_services() {
    echo "Checking RabbitMQ connection..."
    timeout 30 bash -c "until nc -z rabbitmq 5672; do sleep 1; done" || {
        echo "Error: RabbitMQ is not accessible"
        exit 1
    }

    echo "Checking Redis connection..."
    timeout 30 bash -c "until nc -z redis 6379; do sleep 1; done" || {
        echo "Error: Redis is not accessible"
        exit 1
    }
}

# Graceful shutdown handler
shutdown() {
    echo "Received shutdown signal - gracefully stopping workers..."
    kill -TERM "$worker_pid" 2>/dev/null
    kill -TERM "$beat_pid" 2>/dev/null
    wait "$worker_pid" 2>/dev/null
    wait "$beat_pid" 2>/dev/null
    exit 0
}

# Trap shutdown signals
trap shutdown SIGTERM SIGINT SIGQUIT

# Main startup function
start_workers() {
    echo "Starting Celery workers for Medical Research Platform..."
    echo "Configuration:"
    echo "- Queues: $QUEUES"
    echo "- Concurrency: $CONCURRENCY"
    echo "- Log Level: $LOG_LEVEL"
    
    # Start Celery worker process
    celery -A $CELERY_APP worker \
        -Q $QUEUES \
        -c $CONCURRENCY \
        -l $LOG_LEVEL \
        --events \
        --time-limit=$TASK_TIME_LIMIT \
        --soft-time-limit=$TASK_SOFT_TIME_LIMIT \
        --max-tasks-per-child=$MAX_TASKS_PER_CHILD \
        --prefetch-multiplier=$WORKER_PREFETCH_MULTIPLIER \
        --without-heartbeat \
        --without-gossip \
        --without-mingle \
        -Ofair \
        --pidfile="/var/run/celery/worker.pid" \
        --logfile="/var/log/celery/worker.log" &
    worker_pid=$!
    
    # Start Celery beat process for scheduled tasks
    celery -A $CELERY_APP beat \
        -l $LOG_LEVEL \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler \
        --pidfile="/var/run/celery/beat.pid" \
        --logfile="/var/log/celery/beat.log" &
    beat_pid=$!
    
    # Monitor worker processes
    while true; do
        if ! kill -0 "$worker_pid" 2>/dev/null || ! kill -0 "$beat_pid" 2>/dev/null; then
            echo "Error: A Celery process has died unexpectedly"
            exit 1
        fi
        sleep 10
    done
}

# Create required directories
mkdir -p /var/run/celery /var/log/celery
chmod 755 /var/run/celery /var/log/celery

# Main execution
echo "Initializing Celery workers for Medical Research Platform..."
check_services
start_workers