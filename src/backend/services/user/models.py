"""
User models for the Medical Research Platform.

This module defines the core User model and related components for identity management,
authentication, and role-based access control. It implements secure password handling,
profile management, and multi-factor authentication support.

Version: 1.0.0
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils import timezone
import re
import logging

logger = logging.getLogger(__name__)

# Role choices tuple for user role management
ROLE_CHOICES = (
    ('participant', 'Participant'),
    ('protocol_creator', 'Protocol Creator'),
    ('partner', 'Partner'),
    ('admin', 'Administrator')
)

class UserManager(BaseUserManager):
    """
    Custom user manager for creating and managing User instances with enhanced security features.
    Implements secure user creation methods with proper validation and sanitization.
    """
    
    use_in_migrations = True

    def _validate_email(self, email):
        """Validates email format and domain."""
        if not email:
            raise ValueError('Email address is required')
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValueError('Invalid email format')
        
        return self.normalize_email(email)

    def _validate_password(self, password):
        """Validates password complexity requirements."""
        if not password:
            raise ValueError('Password is required')
        
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(char.islower() for char in password):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(char.isdigit() for char in password):
            raise ValueError('Password must contain at least one number')

    def _sanitize_profile(self, profile):
        """Sanitizes profile data for security."""
        if not profile:
            return {}
        
        # Remove any sensitive or disallowed keys
        sanitized = profile.copy()
        sensitive_keys = {'password', 'secret', 'token', 'key'}
        for key in sensitive_keys:
            sanitized.pop(key, None)
        
        return sanitized

    def create_user(self, email, password, first_name, last_name, profile=None):
        """
        Creates and saves a new user instance with enhanced security.
        
        Args:
            email (str): User's email address
            password (str): User's password
            first_name (str): User's first name
            last_name (str): User's last name
            profile (dict, optional): Additional profile data
            
        Returns:
            User: Created and validated user instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            email = self._validate_email(email)
            self._validate_password(password)
            
            user = self.model(
                email=email,
                first_name=first_name,
                last_name=last_name,
                profile=self._sanitize_profile(profile),
                role='participant'  # Default role
            )
            
            user.password = make_password(password)
            user.save(using=self._db)
            
            logger.info(f"Created new user: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    def create_superuser(self, email, password, first_name, last_name):
        """
        Creates and saves a new superuser instance with full privileges.
        
        Args:
            email (str): Superuser's email address
            password (str): Superuser's password
            first_name (str): Superuser's first name
            last_name (str): Superuser's last name
            
        Returns:
            User: Created superuser instance
        """
        user = self.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        user.is_staff = True
        user.is_superuser = True
        user.role = 'admin'
        user.save(using=self._db)
        
        logger.info(f"Created new superuser: {email}")
        return user

class User(AbstractBaseUser, PermissionsMixin):
    """
    Core user model with enhanced security and profile management.
    Implements secure authentication, role-based access, and MFA support.
    """
    
    # Identity fields
    email = models.EmailField(
        verbose_name='Email Address',
        max_length=255,
        unique=True,
        db_index=True
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    # Profile and security
    profile = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='participant'
    )
    
    # MFA configuration
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    mfa_enabled = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at'])
        ]
        
    def get_full_name(self):
        """
        Returns user's full name with proper formatting.
        
        Returns:
            str: Formatted full name
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def has_role(self, role_name):
        """
        Secure role verification method.
        
        Args:
            role_name (str): Role to check
            
        Returns:
            bool: True if user has specified role
            
        Raises:
            ValueError: If role_name is invalid
        """
        if role_name not in dict(ROLE_CHOICES):
            raise ValueError(f"Invalid role: {role_name}")
        
        return self.role == role_name or self.is_superuser
    
    def save(self, *args, **kwargs):
        """
        Enhanced save method with security and audit features.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.pk:
            self.created_at = timezone.now()
        
        self.updated_at = timezone.now()
        self.profile = self.objects._sanitize_profile(self.profile)
        
        if self.role not in dict(ROLE_CHOICES):
            raise ValueError(f"Invalid role: {self.role}")
        
        super().save(*args, **kwargs)
        logger.info(f"Saved user: {self.email}")