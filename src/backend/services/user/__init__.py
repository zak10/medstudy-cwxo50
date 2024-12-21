"""
User Service Module for Medical Research Platform.

This module initializes and exports core user management components including the User model
and UserManager for identity management, authentication, and profile handling.

Version: 1.0.0
"""

# Version information
__version__ = '1.0.0'

# Import core user management components
from services.user.models import User, UserManager

# Export core components
__all__ = [
    'User',
    'UserManager'
]

# Module level docstrings for exported components
User.__doc__ = """
Core user model for authentication and profile management.

This class provides comprehensive user management functionality including:
- Secure authentication with Argon2id password hashing
- Profile management with data sanitization
- Role-based access control
- Multi-factor authentication support
- Audit logging

Key methods:
- save(): Enhanced save method with security and audit features
- get_full_name(): Returns formatted full name
- enable_mfa(): Configures multi-factor authentication
"""

UserManager.__doc__ = """
User management class for secure user operations.

This class handles user creation and management with:
- Secure password validation and hashing
- Email validation and normalization
- Profile data sanitization
- Role management
- Audit logging

Key methods:
- create_user(): Creates standard user accounts
- create_superuser(): Creates administrative users
"""