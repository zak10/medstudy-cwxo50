"""
Pydantic schemas for request/response validation and API documentation in the community service.
Implements comprehensive validation for forums, threads, comments and direct messaging with 
enhanced security and content moderation features.

Version: 1.0.0
"""

from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field, validator, constr

# Content validation constants
MIN_NAME_LENGTH = 5
MAX_NAME_LENGTH = 100
MIN_TITLE_LENGTH = 5
MAX_TITLE_LENGTH = 255
MIN_CONTENT_LENGTH = 10
MAX_CONTENT_LENGTH = 10000

class ForumBase(BaseModel):
    """Base schema for forum data with enhanced validation."""
    name: constr(min_length=MIN_NAME_LENGTH, max_length=MAX_NAME_LENGTH) = Field(
        ...,
        description="Forum display name",
        examples=["Vitamin D Protocol Discussion"]
    )
    description: constr(min_length=MIN_CONTENT_LENGTH, max_length=MAX_CONTENT_LENGTH) = Field(
        ...,
        description="Forum description and purpose"
    )
    is_protocol_specific: bool = Field(
        default=False,
        description="Whether this forum is tied to a specific protocol"
    )
    protocol_id: Optional[UUID] = Field(
        None,
        description="Associated protocol ID if protocol-specific"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the forum is currently active"
    )
    allowed_user_roles: List[str] = Field(
        default=["participant", "protocol_creator", "partner", "admin"],
        description="User roles allowed to participate in this forum"
    )
    moderation_settings: Dict[str, any] = Field(
        default_factory=lambda: {
            "auto_moderation": True,
            "require_approval": False,
            "prohibited_terms": [],
            "max_daily_posts": 50
        },
        description="Forum moderation configuration"
    )

    @validator("name", "description")
    def validate_content(cls, value: str) -> str:
        """
        Validates and sanitizes text content for security.
        
        Args:
            value: Content to validate
            
        Returns:
            Sanitized content string
            
        Raises:
            ValueError: If content fails validation
        """
        from core.utils import sanitize_html
        
        # Sanitize HTML content
        clean_value = sanitize_html(value)
        
        # Check for minimum content after sanitization
        if len(clean_value.strip()) < MIN_NAME_LENGTH:
            raise ValueError("Content too short after sanitization")
            
        return clean_value

    @validator("protocol_id", check_fields=False)
    def validate_protocol_id(cls, value: Optional[UUID], values: Dict) -> Optional[UUID]:
        """
        Validates protocol ID when forum is protocol-specific.
        
        Args:
            value: Protocol UUID to validate
            values: Other field values
            
        Returns:
            Validated protocol ID
            
        Raises:
            ValueError: If protocol validation fails
        """
        if values.get("is_protocol_specific", False):
            if not value:
                raise ValueError("Protocol ID required for protocol-specific forums")
        elif value:
            raise ValueError("Protocol ID not allowed for non-protocol-specific forums")
        return value

class ForumCreate(ForumBase):
    """Schema for forum creation requests."""
    pass

class ForumUpdate(ForumBase):
    """Schema for forum update requests."""
    name: Optional[constr(min_length=MIN_NAME_LENGTH, max_length=MAX_NAME_LENGTH)] = None
    description: Optional[constr(min_length=MIN_CONTENT_LENGTH, max_length=MAX_CONTENT_LENGTH)] = None

class ForumResponse(ForumBase):
    """Schema for forum responses with audit fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ThreadBase(BaseModel):
    """Base schema for discussion threads with validation."""
    title: constr(min_length=MIN_TITLE_LENGTH, max_length=MAX_TITLE_LENGTH) = Field(
        ...,
        description="Thread title"
    )
    content: constr(min_length=MIN_CONTENT_LENGTH, max_length=MAX_CONTENT_LENGTH) = Field(
        ...,
        description="Thread content"
    )
    forum_id: UUID = Field(..., description="Parent forum ID")
    is_pinned: bool = Field(default=False, description="Whether thread is pinned")
    is_locked: bool = Field(default=False, description="Whether thread is locked")

    @validator("title", "content")
    def validate_content(cls, value: str) -> str:
        """Validates and sanitizes thread content."""
        from core.utils import sanitize_html
        return sanitize_html(value)

class ThreadCreate(ThreadBase):
    """Schema for thread creation requests."""
    pass

class ThreadUpdate(ThreadBase):
    """Schema for thread update requests."""
    title: Optional[constr(min_length=MIN_TITLE_LENGTH, max_length=MAX_TITLE_LENGTH)] = None
    content: Optional[constr(min_length=MIN_CONTENT_LENGTH, max_length=MAX_CONTENT_LENGTH)] = None
    forum_id: Optional[UUID] = None

class ThreadResponse(ThreadBase):
    """Schema for thread responses with tracking fields."""
    id: UUID
    author_id: UUID
    view_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CommentBase(BaseModel):
    """Base schema for comments with validation."""
    content: constr(min_length=MIN_CONTENT_LENGTH, max_length=MAX_CONTENT_LENGTH) = Field(
        ...,
        description="Comment content"
    )
    thread_id: UUID = Field(..., description="Parent thread ID")
    parent_comment_id: Optional[UUID] = Field(None, description="Parent comment ID for replies")

    @validator("content")
    def validate_content(cls, value: str) -> str:
        """Validates and sanitizes comment content."""
        from core.utils import sanitize_html
        return sanitize_html(value)

class CommentCreate(CommentBase):
    """Schema for comment creation requests."""
    pass

class CommentUpdate(CommentBase):
    """Schema for comment update requests."""
    content: Optional[constr(min_length=MIN_CONTENT_LENGTH, max_length=MAX_CONTENT_LENGTH)] = None

class CommentResponse(CommentBase):
    """Schema for comment responses with audit fields."""
    id: UUID
    author_id: UUID
    is_edited: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class MessageBase(BaseModel):
    """Base schema for direct messages with validation."""
    content: constr(min_length=MIN_CONTENT_LENGTH, max_length=MAX_CONTENT_LENGTH) = Field(
        ...,
        description="Message content"
    )
    recipient_id: UUID = Field(..., description="Message recipient user ID")

    @validator("content")
    def validate_content(cls, value: str) -> str:
        """Validates and sanitizes message content."""
        from core.utils import sanitize_html
        return sanitize_html(value)

class MessageCreate(MessageBase):
    """Schema for message creation requests."""
    pass

class MessageResponse(MessageBase):
    """Schema for message responses with tracking fields."""
    id: UUID
    sender_id: UUID
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True