"""
Django migrations package initialization for the analysis service.

This package manages database schema migrations for analysis service models including
AnalysisResult and SignalDetection. It supports time-based partitioning and maintains
version control of schema changes while ensuring zero-downtime deployments.

Migration Configuration:
- App Label: analysis
- DB Table Prefix: analysis_
- Default Auto Field: BigAutoField
- Partitioning: Time-based (Monthly) on recorded_at
- Zero Downtime: Required
- Rollback: Supported
- Backup: Required before migrations

Development Guidelines:
- Squash migrations when exceeding 10 migrations
- Maintain backward compatibility
- Test migrations in staging environment
- Peer review required for all migrations
"""

# This file intentionally left empty to mark the directory as a Python package.
# Django's migration system will automatically discover and manage migrations
# in this directory.

default_app_config = 'services.analysis.apps.AnalysisConfig'