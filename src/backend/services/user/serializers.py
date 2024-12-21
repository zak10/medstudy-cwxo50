"""
User serializers for the Medical Research Platform.

This module implements Django REST Framework serializers for user-related models,
handling data serialization, validation and transformation with a focus on security
and data integrity.

Version: 1.0.0
"""

from rest_framework import serializers  # v3.14.0
from rest_framework.exceptions import ValidationError  # v3.14.0
from django.contrib.auth.hashers import make_password  # v4.2.0
import pyotp  # v2.8.0
import re
import logging
from services.user.models import User, ROLE_CHOICES

logger = logging.getLogger(__name__)

# Security constants
PASSWORD_MIN_LENGTH = 12
PASSWORD_REGEX = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{12,}$'
MFA_CODE_LENGTH = 6
MFA_VALIDATION_WINDOW = 30

class BaseUserSerializer(serializers.ModelSerializer):
    """
    Base serializer for common user fields with enhanced validation.
    Implements core field validation and security measures.
    """
    
    email = serializers.EmailField(
        max_length=255,
        required=True,
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please provide a valid email address.'
        }
    )
    
    first_name = serializers.CharField(
        max_length=150,
        required=True,
        error_messages={'required': 'First name is required.'}
    )
    
    last_name = serializers.CharField(
        max_length=150,
        required=True,
        error_messages={'required': 'Last name is required.'}
    )
    
    role = serializers.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        error_messages={'invalid_choice': 'Invalid role selection.'}
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role']

    def validate_role(self, role):
        """
        Validates user role against allowed choices with enhanced security.
        
        Args:
            role (str): Role to validate
            
        Returns:
            str: Validated role value
            
        Raises:
            ValidationError: If role is invalid or unauthorized
        """
        try:
            if role not in dict(ROLE_CHOICES):
                raise ValidationError('Invalid role selection.')
            
            # Additional role-specific validation logic
            if role in ['admin', 'protocol_creator'] and not self.context.get('is_admin', False):
                raise ValidationError('Unauthorized role assignment.')
            
            logger.info(f"Role validation successful: {role}")
            return role
            
        except Exception as e:
            logger.error(f"Role validation failed: {str(e)}")
            raise ValidationError(str(e))

class UserRegistrationSerializer(BaseUserSerializer):
    """
    Serializer for user registration with comprehensive security validation.
    Implements secure password handling and data sanitization.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'Password is required.'}
    )
    
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'Password confirmation is required.'}
    )
    
    profile = serializers.JSONField(
        required=False,
        default=dict
    )

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ['password', 'password_confirm', 'profile']

    def validate(self, data):
        """
        Comprehensive validation of registration data with security checks.
        
        Args:
            data (dict): Registration data to validate
            
        Returns:
            dict: Validated and sanitized data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Password validation
            if data['password'] != data['password_confirm']:
                raise ValidationError({'password_confirm': 'Passwords do not match.'})
            
            if len(data['password']) < PASSWORD_MIN_LENGTH:
                raise ValidationError({
                    'password': f'Password must be at least {PASSWORD_MIN_LENGTH} characters long.'
                })
            
            if not re.match(PASSWORD_REGEX, data['password']):
                raise ValidationError({
                    'password': 'Password must contain uppercase, lowercase, number and special character.'
                })
            
            # Email uniqueness check (case-insensitive)
            email = data['email'].lower()
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError({'email': 'This email address is already registered.'})
            
            # Profile data sanitization
            if 'profile' in data:
                sensitive_keys = {'password', 'secret', 'token', 'key'}
                data['profile'] = {
                    k: v for k, v in data['profile'].items() 
                    if k not in sensitive_keys
                }
            
            logger.info(f"Registration validation successful for email: {email}")
            return data
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Registration validation failed: {str(e)}")
            raise ValidationError('Registration validation failed.')

    def create(self, validated_data):
        """
        Creates new user with secure password handling.
        
        Args:
            validated_data (dict): Validated registration data
            
        Returns:
            User: Created user instance
        """
        try:
            validated_data.pop('password_confirm')
            password = validated_data.pop('password')
            
            user = User.objects.create(
                **validated_data,
                password=make_password(password)
            )
            
            logger.info(f"User created successfully: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise ValidationError('Failed to create user account.')

class UserProfileSerializer(BaseUserSerializer):
    """
    Serializer for user profile updates with secure data handling.
    Implements profile data validation and sanitization.
    """
    
    profile = serializers.JSONField(required=False)
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ['profile', 'profile_image']

    def update(self, instance, validated_data):
        """
        Updates user profile with security measures.
        
        Args:
            instance (User): User instance to update
            validated_data (dict): Validated update data
            
        Returns:
            User: Updated user instance
        """
        try:
            # Handle profile updates
            if 'profile' in validated_data:
                current_profile = instance.profile.copy()
                current_profile.update(validated_data.pop('profile', {}))
                instance.profile = current_profile
            
            # Handle profile image
            if 'profile_image' in validated_data:
                old_image = instance.profile.get('profile_image')
                if old_image:
                    # Clean up old image logic here
                    pass
                
                instance.profile['profile_image'] = validated_data.pop('profile_image')
            
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            instance.save()
            logger.info(f"Profile updated successfully for user: {instance.email}")
            return instance
            
        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            raise ValidationError('Failed to update profile.')

class MFASetupSerializer(serializers.Serializer):
    """
    Serializer for MFA setup with secure TOTP handling.
    Implements MFA configuration and validation.
    """
    
    mfa_secret = serializers.CharField(
        write_only=True,
        required=True,
        max_length=32
    )
    
    setup_code = serializers.CharField(
        write_only=True,
        required=True,
        min_length=MFA_CODE_LENGTH,
        max_length=MFA_CODE_LENGTH
    )

    def validate_setup_code(self, setup_code):
        """
        Validates MFA setup verification code with security checks.
        
        Args:
            setup_code (str): TOTP verification code
            
        Returns:
            str: Validated setup code
            
        Raises:
            ValidationError: If code validation fails
        """
        try:
            if not setup_code.isdigit() or len(setup_code) != MFA_CODE_LENGTH:
                raise ValidationError('Invalid verification code format.')
            
            secret = self.initial_data.get('mfa_secret')
            if not secret:
                raise ValidationError('MFA secret is required.')
            
            totp = pyotp.TOTP(secret)
            if not totp.verify(setup_code, valid_window=MFA_VALIDATION_WINDOW):
                raise ValidationError('Invalid verification code.')
            
            logger.info("MFA setup code validation successful")
            return setup_code
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"MFA setup validation failed: {str(e)}")
            raise ValidationError('MFA setup validation failed.')