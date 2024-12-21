# Contributing to Medical Research Platform

## Table of Contents
- [Introduction](#introduction)
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Review Process](#review-process)

## Introduction

Welcome to the Medical Research Platform project! We're excited that you're interested in contributing. This platform aims to democratize medical research through community-driven observational studies while maintaining the highest standards of security, privacy, and compliance.

Before contributing, please note that we handle sensitive medical data and must maintain strict HIPAA compliance. All contributions must adhere to our security and compliance requirements.

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing. We are committed to providing a welcoming and safe environment for all contributors while protecting sensitive medical data and maintaining user privacy.

## Getting Started

### Development Environment Setup

#### Backend Requirements
- Python 3.11+
- pytest 7.4+
- flake8 with security plugins
- mypy (strict mode)
- bandit and safety for security scanning
- hipaa-audit-tool for compliance checks

#### Frontend Requirements
- Node.js 18+
- TypeScript 5.0+
- Jest 29.5+
- ESLint with @typescript-eslint
- Prettier
- npm audit and snyk for security scanning
- wcag-test-tools for accessibility compliance

### Initial Setup Steps
1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/medical-research-platform.git`
3. Install dependencies:
   ```bash
   # Backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Frontend
   cd src/web
   npm install
   ```

## Development Workflow

### Branch Naming Convention
- Feature: `feature/<description>`
- Bugfix: `bugfix/<description>`
- Hotfix: `hotfix/<description>`
- Release: `release/<version>`
- Security: `security/<description>`

### Commit Message Format
```
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance
- security: Security improvements

Example:
feat(auth): implement MFA for protocol creators
```

### Pull Request Process
1. Create a branch following naming conventions
2. Make your changes
3. Run all tests and checks locally
4. Push changes and create a PR
5. Address review feedback
6. Maintain or improve code coverage
7. Ensure all checks pass

## Code Standards

### Backend (Python)
- Follow PEP 8 style guide
- Use type hints with strict mypy checking
- Maximum cyclomatic complexity: 10
- Document all public interfaces
- Handle sensitive data according to HIPAA guidelines

### Frontend (TypeScript)
- Follow ESLint configuration
- Use strict TypeScript checks
- Follow WCAG 2.1 AA accessibility standards
- Implement security best practices for handling PHI
- Document component interfaces

## Testing Requirements

### Coverage Requirements
- Minimum 80% test coverage for all new code
- 100% coverage for security-critical paths
- Integration tests for API endpoints
- End-to-end tests for critical workflows

### Security Testing
- Run security scans before commits:
  ```bash
  # Backend
  bandit -r ./src/backend
  safety check
  
  # Frontend
  npm audit
  snyk test
  ```

### Compliance Testing
- Verify HIPAA compliance:
  ```bash
  # Run compliance checks
  hipaa-audit-tool scan ./src
  
  # Accessibility checks
  npm run test:accessibility
  ```

## Documentation

### Required Documentation
- API documentation for new endpoints
- Security considerations for features
- HIPAA compliance documentation
- Updated README.md when needed
- JSDoc for TypeScript components
- Docstrings for Python functions

### Documentation Style
- Clear and concise language
- Include security implications
- Document data privacy considerations
- Provide usage examples
- Include error handling

## Review Process

### PR Review Requirements
1. Code Quality
   - Passes all automated checks
   - Follows style guidelines
   - Maintains code coverage
   - No security vulnerabilities
   - HIPAA compliant

2. Security Review
   - Data handling review
   - Authentication/authorization check
   - Input validation
   - Error handling
   - Secure communications

3. Compliance Review
   - HIPAA requirements met
   - Privacy considerations
   - Data protection measures
   - Audit trail requirements

### Review Checklist
- [ ] Tests passing (unit, integration, security)
- [ ] Code coverage ≥80%
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Security scan clean
- [ ] HIPAA compliance verified
- [ ] Documentation updated
- [ ] PR description complete
- [ ] Changelog updated
- [ ] Version bumped if needed

Thank you for contributing to the Medical Research Platform! Your efforts help us build a secure and compliant platform for advancing medical research.