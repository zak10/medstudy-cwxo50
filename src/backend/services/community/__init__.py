"""
Community service package initializer for the Medical Research Platform.
Exposes models and views for forum discussions, posts, and direct messaging functionality.

This module provides secure, moderated community features including:
- Protocol-specific forums
- Discussion threads and posts
- Direct messaging between users
- Content moderation capabilities

Version: 1.0.0
"""

# Import models for forum discussions and messaging
from services.community.models import (
    Forum,
    Thread as ForumThread,  # Aliased to avoid naming conflicts
    Comment as ForumPost,   # Aliased for clarity
    Message as DirectMessage  # Aliased for clarity
)

# Import views for API endpoints
from services.community.views import (
    ForumViewSet,
    ThreadViewSet as ForumThreadViewSet,  # Aliased to match model naming
)

# Package metadata
__version__ = '1.0.0'
__author__ = 'Medical Research Platform Team'

# Default app configuration
default_app_config = 'services.community.apps.CommunityConfig'

# Expose public models
__all__ = [
    'ForumThread',
    'ForumPost', 
    'DirectMessage',
    'ForumThreadViewSet',
]

# Module initialization logging
import logging
logger = logging.getLogger(__name__)
logger.info('Community service initialized')

def get_version():
    """Returns the current version of the community service package."""
    return __version__

# Validation decorator for content moderation
def require_content_moderation(func):
    """
    Decorator to ensure content passes moderation before saving.
    
    Args:
        func: Function to wrap with moderation check
        
    Returns:
        Wrapped function with content moderation
    """
    from core.utils import sanitize_html
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Apply content sanitization if content is present
        if 'content' in kwargs:
            kwargs['content'] = sanitize_html(kwargs['content'])
        return func(*args, **kwargs)
    return wrapper

# Apply content moderation to model save methods
ForumThread.save = require_content_moderation(ForumThread.save)
ForumPost.save = require_content_moderation(ForumPost.save)

# Configure secure messaging
def init_secure_messaging():
    """
    Initializes secure messaging configuration with encryption.
    """
    if not hasattr(DirectMessage, 'get_decrypted_content'):
        logger.error('DirectMessage model missing required encryption methods')
        raise RuntimeError('Secure messaging not properly configured')
        
    logger.info('Secure messaging initialized')

# Initialize secure messaging on module load
try:
    init_secure_messaging()
except Exception as e:
    logger.error(f'Failed to initialize secure messaging: {str(e)}')
    raise