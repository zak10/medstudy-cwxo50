"""
Comprehensive test suite for protocol service views.
Tests protocol management endpoints, participation functionality, data validation,
and safety checks with extensive coverage.

Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from freezegun import freeze_time
import factory
import json
from typing import Dict, Any

from services.protocol.views import ProtocolViewSet, ParticipationViewSet
from services.protocol.models import Protocol, Participation
from services.user.models import User
from core.exceptions import ValidationException

# Test data constants
VALID_PROTOCOL_DATA = {
    'title': 'Test Protocol',
    'description': 'Test protocol description',
    'requirements': {
        'data_points': [
            {
                'name': 'vitamin_d',
                'type': 'numeric',
                'unit': 'ng/mL',
                'range': {'min': 20, 'max': 80}
            }
        ],
        'frequency': {'type': 'weekly', 'value': 1},
        'duration': 12
    },
    'safety_params': {
        'markers': {
            'vitamin_d': {
                'critical_ranges': {'min': 10, 'max': 100, 'unit': 'ng/mL'},
                'alert_ranges': {'min': 20, 'max': 80, 'unit': 'ng/mL'},
                'intervention_required': True
            }
        },
        'intervention_triggers': [
            {
                'condition': 'below_minimum',
                'action': 'notify_participant',
                'notification_required': True,
                'immediate_action': False
            }
        ]
    },
    'duration_weeks': 12,
    'min_participants': 1,
    'max_participants': 100
}

VALID_DATA_SUBMISSION = {
    'vitamin_d': 45,
    'timestamp': '2023-08-01T10:00:00Z',
    'notes': 'Regular submission'
}

@pytest.mark.django_db
class TestProtocolViewSet:
    """
    Test cases for protocol management endpoints including CRUD operations,
    data validation, and safety checks.
    """
    
    def setup_method(self):
        """Set up test environment with necessary fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='protocol_creator'
        )
        self.client.force_authenticate(user=self.user)
        self.test_protocol = create_test_protocol(self.user)

    def test_list_protocols(self):
        """Test protocol listing with pagination and filtering."""
        # Create additional test protocols
        for i in range(3):
            create_test_protocol(
                self.user,
                {'title': f'Test Protocol {i}', 'status': 'active'}
            )

        url = reverse('protocol-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3
        assert all('id' in protocol for protocol in response.data)

        # Test filtering
        response = self.client.get(url, {'status': 'active'})
        assert all(p['status'] == 'active' for p in response.data)

    def test_create_protocol(self):
        """Test protocol creation with validation."""
        url = reverse('protocol-list')
        response = self.client.post(url, VALID_PROTOCOL_DATA, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == VALID_PROTOCOL_DATA['title']
        assert 'id' in response.data
        
        # Test validation failure
        invalid_data = VALID_PROTOCOL_DATA.copy()
        invalid_data['requirements'] = {}
        response = self.client.post(url, invalid_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_enroll_participant(self):
        """Test protocol enrollment with validation checks."""
        url = reverse('protocol-enroll', kwargs={'pk': self.test_protocol.id})
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['protocol'] == str(self.test_protocol.id)
        assert response.data['status'] == 'enrolled'
        
        # Test duplicate enrollment
        response = self.client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_data(self):
        """Test data submission with safety validation."""
        # Create participation
        participation = Participation.objects.create(
            protocol=self.test_protocol,
            user=self.user,
            status='active'
        )
        
        url = reverse('protocol-submit-data', kwargs={'pk': self.test_protocol.id})
        response = self.client.post(url, VALID_DATA_SUBMISSION, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'status' in response.data
        assert response.data['status'] == 'success'
        
        # Test safety violation
        violation_data = VALID_DATA_SUBMISSION.copy()
        violation_data['vitamin_d'] = 5  # Below critical threshold
        response = self.client.post(url, violation_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['safety_alert'] is not None
        assert 'violation_details' in response.data

    def test_protocol_analytics(self):
        """Test protocol analytics endpoint."""
        # Create participations with different statuses
        for status in ['active', 'completed', 'withdrawn']:
            Participation.objects.create(
                protocol=self.test_protocol,
                user=create_test_protocol(self.user)['creator'],
                status=status
            )
        
        url = reverse('protocol-analytics', kwargs={'pk': self.test_protocol.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_participants' in response.data
        assert 'completion_rate' in response.data
        assert 'active_participants' in response.data

@pytest.mark.django_db
class TestParticipationViewSet:
    """
    Test cases for participation management including enrollment,
    progress tracking, and withdrawal.
    """
    
    def setup_method(self):
        """Set up participation test environment."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='participant@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Participant'
        )
        self.client.force_authenticate(user=self.user)
        self.test_protocol = create_test_protocol(self.user)
        self.test_participation = Participation.objects.create(
            protocol=self.test_protocol,
            user=self.user,
            status='active'
        )

    def test_get_progress(self):
        """Test participation progress tracking."""
        url = reverse('participation-progress', kwargs={'pk': self.test_participation.id})
        
        # Submit some data
        self.test_participation.completion_data = {'vitamin_d': 45}
        self.test_participation.save()
        
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'progress' in response.data
        assert 'remaining_tasks' in response.data
        assert 'compliance_score' in response.data

    def test_withdraw_participation(self):
        """Test participation withdrawal."""
        url = reverse('participation-withdraw', kwargs={'pk': self.test_participation.id})
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'withdrawn'
        
        # Verify can't submit data after withdrawal
        submit_url = reverse('protocol-submit-data', kwargs={'pk': self.test_protocol.id})
        response = self.client.post(submit_url, VALID_DATA_SUBMISSION, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_concurrent_enrollment(self):
        """Test handling of concurrent protocol enrollments."""
        # Create another active protocol
        second_protocol = create_test_protocol(self.user)
        url = reverse('protocol-enroll', kwargs={'pk': second_protocol.id})
        
        # Attempt concurrent enrollment
        response = self.client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'concurrent enrollment' in response.data['message'].lower()

def create_test_protocol(creator: User, custom_fields: Dict[str, Any] = None) -> Protocol:
    """Helper function to create test protocol data."""
    protocol_data = VALID_PROTOCOL_DATA.copy()
    if custom_fields:
        protocol_data.update(custom_fields)
    
    protocol = Protocol.objects.create(
        creator=creator,
        **protocol_data
    )
    return protocol