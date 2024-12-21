"""
Serializers for community features in the Medical Research Platform.
Implements data validation, transformation, content moderation, and audit trails
for forums, threads, comments and direct messaging.

Version: 1.0.0
"""

from rest_framework import serializers  # version 3.14.0
from rest_framework.exceptions import ValidationError  # version 3.14.0
from django.utils import timezone  # version 4.2
import bleach  # version 6.0.0
import logging

from services.community.models import Forum, Thread, Comment, Message
from services.user.models import User
from core.utils import sanitize_html
from core.exceptions import ValidationException

logger = logging.getLogger(__name__)

class ForumSerializer(serializers.ModelSerializer):
    """
    Serializer for Forum model with enhanced validation and protocol-specific forum handling.
    """
    
    thread_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Forum
        fields = [
            'id', 'name', 'description', 'is_protocol_specific',
            'protocol_id', 'is_active', 'created_at', 'updated_at',
            'thread_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'thread_count']

    def validate_name(self, value):
        """Validates forum name with length and content checks."""
        if len(value) < 5 or len(value) > 100:
            raise ValidationError("Forum name must be between 5 and 100 characters")
            
        # Sanitize name content
        clean_name = sanitize_html(value)
        if clean_name != value:
            raise ValidationError("Forum name contains invalid HTML content")
            
        return clean_name

    def validate_description(self, value):
        """Validates and sanitizes forum description."""
        if len(value) > 5000:
            raise ValidationError("Description cannot exceed 5000 characters")
            
        return sanitize_html(value)

    def validate(self, data):
        """Validates protocol-specific forum settings."""
        if data.get('is_protocol_specific'):
            if not data.get('protocol_id'):
                raise ValidationError({
                    "protocol_id": "Protocol ID is required for protocol-specific forums"
                })
                
        return data

    def create(self, validated_data):
        """Creates forum with audit trail and validation."""
        try:
            # Set timestamps
            validated_data['created_at'] = timezone.now()
            validated_data['updated_at'] = timezone.now()
            
            # Create forum instance
            forum = Forum.objects.create(**validated_data)
            logger.info(f"Created forum: {forum.id}")
            
            return forum
            
        except Exception as e:
            logger.error(f"Error creating forum: {str(e)}")
            raise ValidationException("Failed to create forum", str(e))

class ThreadSerializer(serializers.ModelSerializer):
    """
    Serializer for Thread model with view tracking and content moderation.
    """
    
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Thread
        fields = [
            'id', 'forum', 'author', 'title', 'content',
            'is_pinned', 'is_locked', 'view_count', 'comment_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'view_count', 'comment_count',
            'created_at', 'updated_at'
        ]

    def validate_title(self, value):
        """Validates thread title length and content."""
        if len(value) < 5 or len(value) > 200:
            raise ValidationError("Title must be between 5 and 200 characters")
            
        return sanitize_html(value)

    def validate_content(self, value):
        """Validates and sanitizes thread content."""
        if len(value) < 20 or len(value) > 50000:
            raise ValidationError("Content must be between 20 and 50000 characters")
            
        return sanitize_html(value)

    def create(self, validated_data):
        """Creates thread with author assignment and audit trail."""
        try:
            # Get current user from context
            user = self.context['request'].user
            validated_data['author'] = user
            
            # Set timestamps
            validated_data['created_at'] = timezone.now()
            validated_data['updated_at'] = timezone.now()
            
            # Create thread instance
            thread = Thread.objects.create(**validated_data)
            logger.info(f"Created thread: {thread.id}")
            
            return thread
            
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            raise ValidationException("Failed to create thread", str(e))

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model with nested reply support and edit tracking.
    """
    
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'thread', 'author', 'content', 'parent_comment',
            'is_edited', 'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = [
            'id', 'author', 'is_edited', 'created_at', 'updated_at'
        ]

    def get_replies(self, obj):
        """Retrieves nested replies for the comment."""
        replies = Comment.objects.filter(parent_comment=obj)
        return CommentSerializer(replies, many=True).data

    def validate_content(self, value):
        """Validates and sanitizes comment content."""
        if len(value) < 2 or len(value) > 10000:
            raise ValidationError("Content must be between 2 and 10000 characters")
            
        return sanitize_html(value)

    def validate(self, data):
        """Validates comment relationships and threading."""
        if data.get('parent_comment'):
            if data['parent_comment'].thread != data['thread']:
                raise ValidationError({
                    "parent_comment": "Parent comment must belong to the same thread"
                })
                
        return data

    def create(self, validated_data):
        """Creates comment with author assignment and audit trail."""
        try:
            # Get current user from context
            user = self.context['request'].user
            validated_data['author'] = user
            
            # Set timestamps
            validated_data['created_at'] = timezone.now()
            validated_data['updated_at'] = timezone.now()
            
            # Create comment instance
            comment = Comment.objects.create(**validated_data)
            logger.info(f"Created comment: {comment.id}")
            
            return comment
            
        except Exception as e:
            logger.error(f"Error creating comment: {str(e)}")
            raise ValidationException("Failed to create comment", str(e))

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model with read status tracking and content moderation.
    """
    
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'recipient', 'content',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'sender', 'is_read', 'read_at', 'created_at'
        ]

    def validate_content(self, value):
        """Validates and sanitizes message content."""
        if len(value) < 1 or len(value) > 5000:
            raise ValidationError("Content must be between 1 and 5000 characters")
            
        return sanitize_html(value)

    def validate_recipient(self, value):
        """Validates message recipient."""
        if not isinstance(value, User):
            raise ValidationError("Invalid recipient")
            
        # Prevent self-messaging
        if self.context['request'].user == value:
            raise ValidationError("Cannot send message to self")
            
        return value

    def create(self, validated_data):
        """Creates message with sender assignment and audit trail."""
        try:
            # Get current user from context
            user = self.context['request'].user
            validated_data['sender'] = user
            
            # Set timestamp
            validated_data['created_at'] = timezone.now()
            
            # Create message instance
            message = Message.objects.create(**validated_data)
            logger.info(f"Created message: {message.id}")
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise ValidationException("Failed to create message", str(e))