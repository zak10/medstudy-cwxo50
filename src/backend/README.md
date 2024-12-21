# Medical Research Platform Backend

## Overview

The Medical Research Platform backend is a HIPAA-compliant, microservices-based system built to support community-driven medical research. The platform leverages Django 4.2 for its core services, implementing a secure and scalable architecture designed for handling sensitive medical data.

### Key Features
- Microservices architecture with Django
- HIPAA-compliant data handling
- Comprehensive security controls
- Scalable infrastructure design
- Real-time data processing capabilities

### Technology Stack
- Python 3.11+
- Django 4.2
- PostgreSQL 15
- Redis 7.0
- RabbitMQ 3.11
- Kong API Gateway 3.4

## Prerequisites

Ensure your development environment meets the following requirements:

- Python 3.11 or higher with venv support
- Docker 24.0+ and Docker Compose v2
- Make 4.0+ for automation scripts
- Git 2.40+
- Minimum 16GB RAM
- 50GB available storage

## Development Setup

### 1. Clone the Repository
```bash
git clone git@github.com:org/medical-research-platform.git
cd src/backend
```

### 2. Environment Configuration
```bash
cp .env.example .env
```

Update `.env` with appropriate values:
```ini
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_DEBUG=True
DATABASE_URL=postgresql://postgres:postgres@db:5432/medical_research?sslmode=require
REDIS_URL=rediss://cache:6379/0
RABBITMQ_URL=amqps://guest:guest@queue:5672/
AWS_S3_BUCKET=medical-research-files
JWT_SECRET_KEY=generate-secure-key-here
```

### 3. Start Development Environment
```bash
make setup-dev
docker-compose -f docker-compose.dev.yml up --build
```

### 4. Verify Installation
Services should be available at:
- API Gateway: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- API Documentation: http://localhost:8000/api/docs

## Testing

### Running Tests
```bash
# Run full test suite
make test

# Run security scans
make security-scan

# Generate coverage report
make coverage-report
```

### Testing Requirements
- Minimum 80% test coverage
- All critical paths must be tested
- Integration tests for service interactions
- Performance testing for critical endpoints
- Security scanning for vulnerabilities

## Code Quality

### Standards
- Strict adherence to PEP 8
- Type hints required for all functions
- Docstrings following Google style
- Maximum cyclomatic complexity of 10
- No critical or high security vulnerabilities

### Automated Checks
```bash
# Run all quality checks
make quality-check

# Run individual checks
make lint
make type-check
make security-audit
```

## API Documentation

### Authentication
- JWT-based authentication
- Access tokens expire after 1 hour
- Refresh tokens expire after 7 days
- MFA required for elevated permissions

### Rate Limiting
- 100 requests per minute per IP
- 1000 requests per hour per user
- Burst allowance of 200 requests

### Versioning
- URI versioning (e.g., /api/v1/)
- Semantic versioning for APIs
- Deprecation notices 3 months in advance

## Deployment

### Production Deployment
```bash
# Build production images
make build

# Security verification
make security-check

# Blue/Green deployment
make deploy-blue
make health-check
make switch-traffic
make verify-deployment
```

### Environment Configuration
- Production settings module
- SSL/TLS enforcement
- HIPAA compliance mode
- Enhanced logging
- Performance monitoring

### Health Checks
- Database connectivity
- Redis availability
- Message queue status
- API endpoint health
- Resource utilization

### Backup Procedures
- Automated daily backups
- Point-in-time recovery
- 30-day retention
- Monthly archive storage
- Quarterly recovery testing

## Service Architecture

### Components
1. API Gateway (Kong 3.4)
   - Rate limiting
   - JWT validation
   - SSL termination
   - Request routing

2. API Service (Django 4.2)
   - Gunicorn with 4 workers
   - Gevent worker class
   - Memory limits
   - Health monitoring

3. Celery Workers (Celery 5.3)
   - Auto-scaling configuration
   - Dead letter queues
   - Task monitoring
   - Resource limits

4. Database (PostgreSQL 15)
   - Multi-AZ deployment
   - Automated backups
   - Point-in-time recovery
   - Connection pooling

5. Cache (Redis 7)
   - Cluster mode enabled
   - SSL/TLS encryption
   - Automatic failover
   - Memory policies

6. Message Queue (RabbitMQ 3.11)
   - Quorum queues
   - SSL enabled
   - Monitoring integration
   - High availability

## Troubleshooting

### Common Issues
1. Database Connection Errors
   - Verify PostgreSQL service is running
   - Check connection string in .env
   - Validate SSL certificates

2. Redis Connection Issues
   - Confirm Redis service status
   - Verify SSL configuration
   - Check memory availability

3. Worker Processing Delays
   - Monitor queue lengths
   - Check worker logs
   - Verify resource allocation

### Support
- GitHub Issues for bug reports
- Technical documentation in /docs
- Slack channel for urgent issues
- Weekly office hours for Q&A

## Contributing

### Development Workflow
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request
6. Pass code review
7. Merge to main

### Code Review Requirements
- Two approvals required
- All tests passing
- Coverage maintained
- Security scan passed
- Documentation updated