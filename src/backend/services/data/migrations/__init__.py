"""
Django migrations package for the data service.

This package manages database schema migrations for data models including:
- DataPoint
- BloodWorkResult 
- WeeklyCheckIn

Key Features:
- Atomic transactions for safe schema updates
- Reversible migrations for rollback capability
- Zero-downtime migration support
- Data preservation during schema changes
- Dependency tracking with user and protocol services

Migration Dependencies:
- services.user: Required for DataPoint foreign key to User model
- services.protocol: Required for DataPoint foreign key to Protocol model

Version: 1.0.0
"""

# Package is intentionally empty as per Django migrations convention
# Django will automatically discover and manage migrations in this package

# Migration configuration is handled through Django settings and model Meta classes
# See ../models.py for model-specific migration configurations