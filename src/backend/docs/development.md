# Medical Research Platform - Backend Development Guide

Version: 1.0.0  
Last Updated: 2024-01-20  
Maintainers: Backend Team  
Repository: Medical Research Platform

## Table of Contents
- [Development Environment Setup](#development-environment-setup)
  - [Prerequisites](#prerequisites)
  - [Initial Setup](#initial-setup)
  - [Development Services](#development-services)
- [Development Workflow](#development-workflow)
  - [Code Quality Standards](#code-quality-standards)
  - [Testing Requirements](#testing-requirements)
  - [Git Workflow](#git-workflow)
- [Security Standards](#security-standards)
- [Troubleshooting](#troubleshooting)

## Development Environment Setup

### Prerequisites

Ensure you have the following tools installed on your development machine:

| Tool | Version | Installation Guide |
|------|---------|-------------------|
| Docker | 24.0+ | [Docker Installation](https://docs.docker.com/get-docker/) |
| Docker Compose | 2.20+ | Included with Docker Desktop |
| Python | 3.11+ | [Python Downloads](https://www.python.org/downloads/) |
| Poetry | 1.5+ | `curl -sSL https://install.python-poetry.org \| python3 -` |
| Git | 2.40+ | [Git Installation](https://git-scm.com/downloads) |
| Node.js | 18+ | [Node.js Downloads](https://nodejs.org/) |
| VS Code | Latest | [VS Code Download](https://code.visualstudio.com/) |

#### Recommended VS Code Extensions
- Python
- Docker
- GitLens
- Python Type Hint
- markdownlint

### Initial Setup

1. Clone the repository and set up environment:
```bash
git clone git@github.com:org/medical-research-platform.git
cd medical-research-platform/src/backend
cp .env.example .env
```

2. Install Python dependencies:
```bash
poetry install
poetry shell
```

3. Start development services:
```bash
docker compose -f docker-compose.dev.yml up -d
```

4. Run database migrations:
```bash
poetry run python manage.py migrate
```

5. Load initial test data:
```bash
poetry run python manage.py loaddata initial_data
```

6. Configure pre-commit hooks:
```bash
poetry run pre-commit install
```

7. Generate development SSL certificates:
```bash
./scripts/generate-ssl-certs.sh
```

### Development Services

The development environment includes the following services:

| Service | Purpose | Access |
|---------|----------|---------|
| Django API | Backend API service | http://localhost:8000 |
| PostgreSQL | Primary database | localhost:5432 |
| Redis | Caching and sessions | localhost:6379 |
| RabbitMQ | Message broker | localhost:5672 (AMQP)<br>http://localhost:15672 (Management) |
| Mailhog | Email testing | http://localhost:8025 |
| MinIO | S3-compatible storage | http://localhost:9000 (API)<br>http://localhost:9001 (Console) |

## Development Workflow

### Code Quality Standards

All code must meet the following quality standards:

#### Code Formatting
```toml
# pyproject.toml configuration
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
```

#### Type Checking
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

#### Testing Configuration
```toml
[tool.pytest]
minversion = "7.0"
addopts = "-ra -q --cov=app --cov-report=term-missing"
testpaths = ["tests"]
```

### Testing Requirements

- Minimum 80% code coverage required for all modules
- Test organization:
  ```
  tests/
  ├── unit/
  │   ├── test_models.py
  │   ├── test_services.py
  │   └── test_utils.py
  ├── integration/
  │   ├── test_api.py
  │   └── test_workflows.py
  └── conftest.py
  ```

### Git Workflow

#### Branch Naming
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Production fixes

#### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add user authentication endpoint
fix: correct database connection timeout
docs: update API documentation
test: add integration tests for protocol service
```

#### Pull Request Process
1. Create branch from `develop`
2. Implement changes with tests
3. Pass all CI checks
4. Obtain code review approval
5. Squash and merge to `develop`

## Security Standards

### Development Security Controls

1. Environment Variables
```bash
# Required in .env file
DATABASE_URL=postgresql://user:password@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
SECRET_KEY=development-secret-key-change-in-production
```

2. Data Encryption
- Use `cryptography` package for encryption
- Store encryption keys in AWS KMS in production
- Use environment-specific keys for development

3. Access Controls
- Implement RBAC using Django permissions
- Use JWT tokens for API authentication
- Enable CORS only for approved origins

4. Vulnerability Management
- Regular dependency updates with `poetry update`
- Security scanning with `bandit`
- OWASP dependency check in CI pipeline

## Troubleshooting

### Common Issues

1. Docker Services
```bash
# Reset development environment
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
```

2. Database
```bash
# Reset database
poetry run python manage.py reset_db
poetry run python manage.py migrate
poetry run python manage.py loaddata initial_data
```

3. Dependencies
```bash
# Clean and reinstall dependencies
poetry env remove python
poetry install
```

### Getting Help

- Check the [Backend Team Wiki](https://wiki.example.com/backend)
- Join #backend-dev on Slack
- Create an issue in GitHub repository
- Contact the Backend Team Lead

---

For additional documentation, please refer to:
- [API Documentation](../api/README.md)
- [Database Schema](../db/README.md)
- [Deployment Guide](./deployment.md)