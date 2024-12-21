"""
Root package initializer for the Medical Research Platform services module.

This module exposes core functionality from all service submodules including user management,
protocol handling, data collection, analysis, and community features. Implements strict
validation, security controls, and type safety while maintaining clean interfaces.

Version: 1.0.0
"""

# Import core service components
from services.analysis import (
    AnalysisResult,
    SignalDetection
)

from services.community import (
    ForumThread,
    ForumPost,
    DirectMessage,
    ForumThreadViewSet,
    ForumPostViewSet,
    DirectMessageViewSet
)

from services.data import (
    DataPoint,
    BloodWorkResult,
    WeeklyCheckIn,
    DataPointViewSet,
    BloodWorkViewSet,
    WeeklyCheckInViewSet
)

from services.protocol import (
    Protocol,
    Participation,
    ProtocolViewSet,
    ParticipationViewSet
)

from services.user import (
    User,
    UserManager
)

# Package metadata
__version__ = '1.0.0'

# Define public API
__all__ = [
    # Analysis components
    'AnalysisResult',
    'SignalDetection',
    
    # Community components
    'ForumThread',
    'ForumPost', 
    'DirectMessage',
    'ForumThreadViewSet',
    'ForumPostViewSet',
    'DirectMessageViewSet',
    
    # Data collection components
    'DataPoint',
    'BloodWorkResult',
    'WeeklyCheckIn',
    'DataPointViewSet',
    'BloodWorkViewSet',
    'WeeklyCheckInViewSet',
    
    # Protocol components
    'Protocol',
    'Participation',
    'ProtocolViewSet',
    'ParticipationViewSet',
    
    # User components
    'User',
    'UserManager'
]

# Module initialization logging
import logging
logger = logging.getLogger(__name__)

def init_services():
    """
    Initializes all service components with validation checks.
    
    Raises:
        ImportError: If required components are missing
        RuntimeError: If service initialization fails
    """
    try:
        # Verify core analysis capabilities
        required_analysis_methods = [
            getattr(AnalysisResult, 'compute_statistics'),
            getattr(AnalysisResult, 'detect_patterns'),
            getattr(SignalDetection, 'calculate_confidence')
        ]
        
        # Verify community features
        required_community_methods = [
            getattr(ForumThread, 'save'),
            getattr(DirectMessage, 'encrypt_content')
        ]
        
        # Verify data collection features
        required_data_methods = [
            getattr(DataPoint, 'validate_data'),
            getattr(BloodWorkResult, 'save')
        ]
        
        # Verify protocol management
        required_protocol_methods = [
            getattr(Protocol, 'validate_requirements'),
            getattr(Participation, 'calculate_progress')
        ]
        
        # Verify user management
        required_user_methods = [
            getattr(User, 'enable_mfa'),
            getattr(UserManager, 'create_user')
        ]
        
        logger.info("All service components initialized successfully")
        
    except AttributeError as e:
        logger.error(f"Service initialization failed: {str(e)}")
        raise ImportError("Required service methods not found")
        
    except Exception as e:
        logger.error(f"Unexpected error during service initialization: {str(e)}")
        raise RuntimeError("Service initialization failed")

# Initialize services on module load
init_services()