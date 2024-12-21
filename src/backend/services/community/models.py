"""
Database models for community features in the Medical Research Platform.
Implements forum discussions, threads, comments, and direct messaging with 
comprehensive moderation, sanitization, and audit capabilities.

Version: 1.0.0
"""

from django.db import models  # version 4.2
from django.utils import timezone  # version 4.2
import uuid  # version 3.11
import logging

from services.user.models import User
from core.utils import sanitize_html

logger = logging.getLogger(__name__)

class Forum(models.Model):
    """
    Model representing a discussion forum with moderation capabilities.
    Supports both protocol-specific and general discussions.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the forum"
    )
    name = models.CharField(
        max_length=255,
        help_text="Forum display name"
    )
    description = models.TextField(
        help_text="Forum description and purpose"
    )
    is_protocol_specific = models.BooleanField(
        default=False,
        help_text="Whether this forum is tied to a specific protocol"
    )
    protocol_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Associated protocol ID if protocol-specific"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the forum is currently active"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when forum was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when forum was last updated"
    )

    class Meta:
        indexes = [
            models.Index(fields=['is_protocol_specific']),
            models.Index(fields=['protocol_id']),
            models.Index(fields=['created_at'])
        ]
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """
        Custom save method with validation and sanitization.
        """
        if not self.id:
            self.created_at = timezone.now()
        
        self.updated_at = timezone.now()
        
        # Validate protocol_id requirement
        if self.is_protocol_specific and not self.protocol_id:
            raise ValueError("Protocol-specific forums must have a protocol_id")
            
        # Sanitize text content
        self.description = sanitize_html(self.description)
        
        super().save(*args, **kwargs)
        logger.info(f"Saved forum: {self.id}")

class Thread(models.Model):
    """
    Model representing a discussion thread with moderation capabilities.
    Includes view tracking and content sanitization.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    forum = models.ForeignKey(
        Forum,
        on_delete=models.CASCADE,
        related_name='threads'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_threads'
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['forum', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_pinned', '-created_at'])
        ]
        ordering = ['-is_pinned', '-created_at']

    def save(self, *args, **kwargs):
        """
        Custom save method with content sanitization.
        """
        if not self.id:
            self.created_at = timezone.now()
        
        self.updated_at = timezone.now()
        
        # Sanitize content
        self.content = sanitize_html(self.content)
        
        # Validate relationships
        if not self.forum_id or not self.author_id:
            raise ValueError("Thread must have both forum and author")
            
        super().save(*args, **kwargs)
        logger.info(f"Saved thread: {self.id}")

    def increment_view_count(self):
        """
        Atomically increments the thread view count.
        """
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])
        logger.debug(f"Incremented view count for thread: {self.id}")

class Comment(models.Model):
    """
    Model representing a comment with nested reply support.
    Implements edit tracking and content sanitization.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_comments'
    )
    content = models.TextField()
    parent_comment = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['thread', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['parent_comment', '-created_at'])
        ]
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        """
        Custom save method with content sanitization and edit tracking.
        """
        is_new = not self.id
        if is_new:
            self.created_at = timezone.now()
        else:
            self.is_edited = True
            
        self.updated_at = timezone.now()
        
        # Sanitize content
        self.content = sanitize_html(self.content)
        
        # Validate relationships
        if not self.thread_id or not self.author_id:
            raise ValueError("Comment must have both thread and author")
            
        # Validate parent comment belongs to same thread
        if self.parent_comment and self.parent_comment.thread_id != self.thread_id:
            raise ValueError("Parent comment must belong to the same thread")
            
        super().save(*args, **kwargs)
        logger.info(f"Saved comment: {self.id}")

class Message(models.Model):
    """
    Model representing a direct message between users.
    Implements read tracking and content sanitization.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['is_read', '-created_at'])
        ]
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """
        Custom save method with content sanitization.
        """
        if not self.id:
            self.created_at = timezone.now()
            
        # Sanitize content
        self.content = sanitize_html(self.content)
        
        # Validate relationships
        if not self.sender_id or not self.recipient_id:
            raise ValueError("Message must have both sender and recipient")
            
        # Prevent self-messaging
        if self.sender_id == self.recipient_id:
            raise ValueError("Cannot send message to self")
            
        super().save(*args, **kwargs)
        logger.info(f"Saved message: {self.id}")

    def mark_as_read(self):
        """
        Marks the message as read with timestamp.
        """
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
        logger.debug(f"Marked message as read: {self.id}")