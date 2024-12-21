#!/usr/bin/env bash
# Version: 1.0.0
# Django backend services container entrypoint script
# Handles initialization, dependency checks, and service startup

# Strict error handling
set -e
set -o pipefail
set -u

# Source dependency checker
source "$(dirname "$0")/wait-for-it.sh"

# Default environment variables
: "${PYTHONUNBUFFERED:=1}"
: "${DJANGO_SETTINGS_MODULE:=config.settings.production}"
: "${APP_HOME:=/app}"
: "${DEPENDENCY_TIMEOUT:=300}"
: "${RETRY_INTERVAL:=5}"
: "${MAX_RETRIES:=60}"
: "${LOG_LEVEL:=INFO}"

# Service configuration
POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-cache}"
REDIS_PORT="${REDIS_PORT:-6379}"
RABBITMQ_HOST="${RABBITMQ_HOST:-queue}"
RABBITMQ_PORT="${RABBITMQ_PORT:-5672}"

# Process ID storage
SERVICE_PID=""

# Logging function
log() {
    local level="$1"
    shift
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $*" >&2
}

# Cleanup handler
cleanup() {
    log "INFO" "Received shutdown signal - cleaning up..."
    if [ -n "$SERVICE_PID" ]; then
        kill -TERM "$SERVICE_PID" 2>/dev/null || true
        wait "$SERVICE_PID" 2>/dev/null || true
    fi
    log "INFO" "Cleanup completed"
    exit 0
}

# Set up signal traps
trap cleanup SIGTERM SIGINT SIGQUIT EXIT

# Check service dependencies
check_dependencies() {
    log "INFO" "Checking service dependencies..."
    
    # Check PostgreSQL
    if ! wait_for "$POSTGRES_HOST" "$POSTGRES_PORT" "$DEPENDENCY_TIMEOUT"; then
        log "ERROR" "PostgreSQL database is not available"
        return 1
    fi
    
    # Check Redis
    if ! wait_for "$REDIS_HOST" "$REDIS_PORT" "$DEPENDENCY_TIMEOUT"; then
        log "ERROR" "Redis cache is not available"
        return 1
    fi
    
    # Check RabbitMQ
    if ! wait_for "$RABBITMQ_HOST" "$RABBITMQ_PORT" "$DEPENDENCY_TIMEOUT"; then
        log "ERROR" "RabbitMQ message queue is not available"
        return 1
    fi
    
    log "INFO" "All dependencies are available"
    return 0
}

# Initialize Django application
initialize_django() {
    log "INFO" "Initializing Django application..."
    
    # Change to application directory
    cd "$APP_HOME"
    
    # Run database migrations
    log "INFO" "Running database migrations..."
    if ! python manage.py migrate --noinput; then
        log "ERROR" "Database migration failed"
        return 1
    fi
    
    # Collect static files
    log "INFO" "Collecting static files..."
    if ! python manage.py collectstatic --noinput; then
        log "ERROR" "Static file collection failed"
        return 1
    fi
    
    # Create cache tables
    log "INFO" "Creating cache tables..."
    if ! python manage.py createcachetable; then
        log "ERROR" "Cache table creation failed"
        return 1
    }
    
    # Create superuser if credentials are provided
    if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
        log "INFO" "Creating superuser..."
        if ! python manage.py createsuperuser --noinput; then
            log "WARN" "Superuser creation failed - may already exist"
        fi
    fi
    
    log "INFO" "Django initialization completed"
    return 0
}

# Start service based on command
start_service() {
    local command="$1"
    
    case "$command" in
        "api")
            log "INFO" "Starting Django API server..."
            gunicorn config.wsgi:application \
                --bind 0.0.0.0:8000 \
                --workers 4 \
                --threads 2 \
                --worker-class uvicorn.workers.UvicornWorker \
                --worker-tmp-dir /dev/shm \
                --log-level "$LOG_LEVEL" \
                --access-logfile - \
                --error-logfile - \
                --capture-output \
                --enable-stdio-inheritance &
            SERVICE_PID="$!"
            ;;
            
        "celery")
            log "INFO" "Starting Celery worker..."
            celery -A config worker \
                --loglevel="$LOG_LEVEL" \
                --concurrency=4 \
                --max-tasks-per-child=1000 \
                --optimization=fair \
                --pool=prefork &
            SERVICE_PID="$!"
            ;;
            
        *)
            log "ERROR" "Unknown command: $command"
            return 1
            ;;
    esac
    
    # Wait for service process
    wait "$SERVICE_PID"
}

# Main execution
main() {
    local command="${1:-api}"
    
    log "INFO" "Starting entrypoint script for command: $command"
    
    # Check dependencies
    if ! check_dependencies; then
        log "ERROR" "Dependency check failed"
        exit 1
    fi
    
    # Initialize Django
    if ! initialize_django; then
        log "ERROR" "Django initialization failed"
        exit 1
    fi
    
    # Start requested service
    log "INFO" "Starting service: $command"
    start_service "$command"
    
    # Service terminated
    log "INFO" "Service terminated"
    exit 0
}

# Execute main if not sourced
if ! (return 0 2>/dev/null); then
    main "$@"
fi