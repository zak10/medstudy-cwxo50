"""
Protocol service package initializer for the Medical Research Platform.

This module exposes core protocol models and views for managing research protocols and participant
enrollment with comprehensive validation, safety checks, and progress tracking capabilities.

Version: 1.0.0
"""

# Import core protocol models with validation and safety features
from services.protocol.models import (
    Protocol,
    Participation,
    PROTOCOL_STATUS_CHOICES,
    PARTICIPATION_STATUS_CHOICES
)

# Import protocol management views with security and monitoring
from services.protocol.views import (
    ProtocolViewSet,
    ParticipationViewSet
)

# Package metadata
__version__ = '1.0.0'

# Export core models and views
__all__ = [
    # Models
    'Protocol',
    'Participation',
    'PROTOCOL_STATUS_CHOICES',
    'PARTICIPATION_STATUS_CHOICES',
    
    # ViewSets
    'ProtocolViewSet',
    'ParticipationViewSet',
]

# Protocol model exports
Protocol.validate_requirements = Protocol.validate_requirements
Protocol.check_safety_violation = Protocol.check_safety_violation
Protocol.track_compliance = Protocol.track_compliance
Protocol.validate_timeline = Protocol.validate_timeline

# Participation model exports
Participation.calculate_progress = Participation.calculate_progress
Participation.check_completion = Participation.check_completion
Participation.calculate_metrics = Participation.calculate_metrics
Participation.validate_enrollment = Participation.validate_enrollment

# Protocol ViewSet exports
ProtocolViewSet.create = ProtocolViewSet.create
ProtocolViewSet.update = ProtocolViewSet.update
ProtocolViewSet.list = ProtocolViewSet.list
ProtocolViewSet.validate_safety = ProtocolViewSet.validate_safety
ProtocolViewSet.check_compliance = ProtocolViewSet.check_compliance

# Participation ViewSet exports
ParticipationViewSet.enroll = ParticipationViewSet.enroll
ParticipationViewSet.withdraw = ParticipationViewSet.withdraw
ParticipationViewSet.get_progress = ParticipationViewSet.get_progress
ParticipationViewSet.validate_enrollment = ParticipationViewSet.validate_enrollment
ParticipationViewSet.track_metrics = ParticipationViewSet.track_metrics