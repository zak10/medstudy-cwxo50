# Medical Research Platform

![Build Status](https://github.com/medical-research-platform/backend/workflows/CI/badge.svg)
![Coverage Status](https://img.shields.io/codecov/c/github/medical-research-platform/backend)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![TypeScript: 5.0+](https://img.shields.io/badge/TypeScript-5.0%2B-blue)

A comprehensive platform for democratizing medical research through community-driven observational studies ("unstudies"). This system bridges the gap between individual health experimentation and formal clinical research by providing structured protocols, data collection tools, and analysis capabilities.

## 🎯 Project Overview

The Medical Research Platform enables:
- Standardized protocol management for supplement-based studies
- Structured data collection for blood work, biometrics, and experiences
- Advanced analysis engine for signal detection and pattern recognition
- Moderated community features for participant interaction

### Target Metrics
- 50+ active protocols within first year
- 80% protocol completion rate
- 95% data collection compliance
- 1,000 active participants in 6 months
- 5 verified supplement company partnerships

## 🏗 System Architecture

The platform utilizes a modern, scalable architecture:

- **Frontend**: Vue.js 3.0+ with TypeScript 5.0+
- **Backend**: Django 4.2+ with Python 3.11+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7.0+
- **Message Queue**: RabbitMQ 3.11+
- **Infrastructure**: AWS with Docker 24.0+ and Terraform 1.5+

## 🚀 Getting Started

### Prerequisites

#### Backend Requirements
```bash
Python 3.11+
PostgreSQL 15+
Redis 7.0+
RabbitMQ 3.11+
Docker 24.0+
```

#### Frontend Requirements
```bash
Node.js 18+
pnpm 8.0+
```

#### Infrastructure Tools
```bash
Terraform 1.5+
AWS CLI 2.0+
Docker 24.0+
```

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/medical-research-platform/platform.git
cd platform
```

2. Install backend dependencies:
```bash
poetry install
```

3. Install frontend dependencies:
```bash
pnpm install
```

4. Start development environment:
```bash
docker-compose up -d
```

5. Run migrations:
```bash
poetry run python manage.py migrate
```

6. Start development servers:
```bash
# Backend
poetry run python manage.py runserver

# Frontend
pnpm dev
```

## 💻 Development

### Code Quality Standards

- Python: black (23.0+), isort (5.0+), pylint
- TypeScript: eslint (8.0+), prettier (3.0+)
- Test coverage minimum: 80%
- Documentation: JSDoc/Sphinx for all public interfaces

### Testing

```bash
# Backend tests
poetry run pytest

# Frontend tests
pnpm test
```

## 📦 Deployment

The platform uses GitHub Actions for CI/CD with deployments to AWS:

- Development: Local Docker environment
- Staging: AWS ECS with replicated production setup
- Production: Multi-AZ AWS ECS deployment

Refer to [Deployment Guide](docs/deployment/README.md) for detailed procedures.

## 🤝 Contributing

We welcome contributions! Please see:

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📚 Documentation

- [Technical Documentation](docs/technical/README.md)
- [API Documentation](docs/api/README.md)
- [Deployment Guide](docs/deployment/README.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Quick Links

- [Technical Documentation](docs/technical/README.md)
- [API Documentation](docs/api/README.md)
- [Deployment Guide](docs/deployment/README.md)
- [Security Policy](SECURITY.md)

## 🛡 Security

For security concerns, please review our [Security Policy](SECURITY.md) before submitting a vulnerability report.

## 📧 Contact

For support or inquiries, please open an issue in the repository.