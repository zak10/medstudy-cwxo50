"""
Test suite for community service API views.
Tests forum management, thread operations, comments and direct messaging endpoints
with comprehensive coverage for moderation, permissions, and error cases.

Version: 1.0.0
"""

# Third-party imports
import pytest  # version ^7.4.0
from rest_framework.test import APIClient  # version ^3.14.0
from rest_framework import status  # version ^3.14.0
import uuid
from datetime import datetime, timedelta

# Internal imports
from services.community.views import (
    ForumViewSet,
    ThreadViewSet,
    CommentViewSet,
    MessageViewSet
)
from services.community.models import Forum, Thread, Comment, Message
from services.user.models import User
from core.exceptions import ValidationException

@pytest.mark.django_db
class TestForumViewSet:
    """
    Test cases for forum management endpoints including moderation actions.
    """

    def setup_method(self):
        """Set up test data and client."""
        self.client = APIClient()
        
        # Create test users with different roles
        self.participant = User.objects.create_user(
            email="participant@test.com",
            password="Test123!",
            first_name="Test",
            last_name="Participant"
        )
        self.protocol_creator = User.objects.create_user(
            email="creator@test.com",
            password="Test123!",
            first_name="Test",
            last_name="Creator",
            profile={"role": "protocol_creator"}
        )
        
        # Create test protocol
        self.protocol_id = str(uuid.uuid4())

    def test_list_forums(self):
        """Test listing forums with pagination and filtering."""
        # Create test forums
        Forum.objects.create(
            name="General Discussion",
            description="General forum for discussions",
            is_protocol_specific=False
        )
        Forum.objects.create(
            name="Protocol Forum",
            description="Protocol specific forum",
            is_protocol_specific=True,
            protocol_id=self.protocol_id
        )
        
        # Test unauthenticated access
        response = self.client.get("/api/v1/forums/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test authenticated access
        self.client.force_authenticate(user=self.participant)
        response = self.client.get("/api/v1/forums/")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response structure
        data = response.json()
        assert "results" in data
        assert "pagination" in data
        assert len(data["results"]) == 2
        
        # Test protocol filter
        response = self.client.get(f"/api/v1/forums/?protocol_id={self.protocol_id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 1
        
        # Test active filter
        response = self.client.get("/api/v1/forums/?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        assert all(forum["is_active"] for forum in response.json()["results"])

    def test_create_forum(self):
        """Test forum creation with validation."""
        forum_data = {
            "name": "Test Forum",
            "description": "Test forum description",
            "is_protocol_specific": True,
            "protocol_id": self.protocol_id
        }
        
        # Test unauthenticated access
        response = self.client.post("/api/v1/forums/", forum_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test participant access (should be denied)
        self.client.force_authenticate(user=self.participant)
        response = self.client.post("/api/v1/forums/", forum_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test protocol creator access
        self.client.force_authenticate(user=self.protocol_creator)
        response = self.client.post("/api/v1/forums/", forum_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify created forum
        created_forum = response.json()
        assert created_forum["name"] == forum_data["name"]
        assert created_forum["description"] == forum_data["description"]
        assert created_forum["is_protocol_specific"] == forum_data["is_protocol_specific"]
        assert created_forum["protocol_id"] == forum_data["protocol_id"]
        
        # Test validation - missing required fields
        invalid_data = {"name": "Test Forum"}
        response = self.client.post("/api/v1/forums/", invalid_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_forum_moderation(self):
        """Test forum moderation actions."""
        # Create test forum
        forum = Forum.objects.create(
            name="Test Forum",
            description="Test forum description",
            is_protocol_specific=False
        )
        
        # Test unauthenticated access
        response = self.client.post(f"/api/v1/forums/{forum.id}/lock/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test participant access (should be denied)
        self.client.force_authenticate(user=self.participant)
        response = self.client.post(f"/api/v1/forums/{forum.id}/lock/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test protocol creator moderation
        self.client.force_authenticate(user=self.protocol_creator)
        
        # Test lock forum
        response = self.client.post(f"/api/v1/forums/{forum.id}/lock/")
        assert response.status_code == status.HTTP_200_OK
        forum.refresh_from_db()
        assert forum.is_locked is True
        
        # Test unlock forum
        response = self.client.post(f"/api/v1/forums/{forum.id}/unlock/")
        assert response.status_code == status.HTTP_200_OK
        forum.refresh_from_db()
        assert forum.is_locked is False
        
        # Test pin forum
        response = self.client.post(f"/api/v1/forums/{forum.id}/pin/")
        assert response.status_code == status.HTTP_200_OK
        forum.refresh_from_db()
        assert forum.is_pinned is True
        
        # Test unpin forum
        response = self.client.post(f"/api/v1/forums/{forum.id}/unpin/")
        assert response.status_code == status.HTTP_200_OK
        forum.refresh_from_db()
        assert forum.is_pinned is False

@pytest.mark.django_db
class TestThreadViewSet:
    """
    Test cases for thread management endpoints.
    """

    def setup_method(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com",
            password="Test123!",
            first_name="Test",
            last_name="User"
        )
        self.forum = Forum.objects.create(
            name="Test Forum",
            description="Test forum description"
        )

    def test_list_threads(self):
        """Test listing threads with pagination and filtering."""
        # Create test threads
        Thread.objects.create(
            forum=self.forum,
            author=self.user,
            title="Thread 1",
            content="Thread 1 content"
        )
        Thread.objects.create(
            forum=self.forum,
            author=self.user,
            title="Thread 2",
            content="Thread 2 content",
            is_pinned=True
        )
        
        # Test unauthenticated access
        response = self.client.get(f"/api/v1/forums/{self.forum.id}/threads/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test authenticated access
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/v1/forums/{self.forum.id}/threads/")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response structure and ordering (pinned first)
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["is_pinned"] is True

    def test_create_thread(self):
        """Test thread creation with validation."""
        thread_data = {
            "title": "Test Thread",
            "content": "Test thread content"
        }
        
        # Test unauthenticated access
        response = self.client.post(f"/api/v1/forums/{self.forum.id}/threads/", thread_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test authenticated creation
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/v1/forums/{self.forum.id}/threads/", thread_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify created thread
        created_thread = response.json()
        assert created_thread["title"] == thread_data["title"]
        assert created_thread["content"] == thread_data["content"]
        assert created_thread["author"]["id"] == str(self.user.id)
        
        # Test validation - missing required fields
        invalid_data = {"title": "Test Thread"}
        response = self.client.post(f"/api/v1/forums/{self.forum.id}/threads/", invalid_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_thread_moderation(self):
        """Test thread moderation actions."""
        thread = Thread.objects.create(
            forum=self.forum,
            author=self.user,
            title="Test Thread",
            content="Test thread content"
        )
        
        # Test close thread
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/v1/threads/{thread.id}/close/")
        assert response.status_code == status.HTTP_200_OK
        thread.refresh_from_db()
        assert thread.is_locked is True
        
        # Test delete thread
        response = self.client.delete(f"/api/v1/threads/{thread.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Thread.objects.filter(id=thread.id).exists()

@pytest.mark.django_db
class TestCommentViewSet:
    """
    Test cases for comment management endpoints.
    """

    def setup_method(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com",
            password="Test123!",
            first_name="Test",
            last_name="User"
        )
        self.forum = Forum.objects.create(
            name="Test Forum",
            description="Test forum description"
        )
        self.thread = Thread.objects.create(
            forum=self.forum,
            author=self.user,
            title="Test Thread",
            content="Test thread content"
        )

    def test_list_comments(self):
        """Test listing comments with pagination."""
        # Create test comments
        Comment.objects.create(
            thread=self.thread,
            author=self.user,
            content="Comment 1"
        )
        Comment.objects.create(
            thread=self.thread,
            author=self.user,
            content="Comment 2"
        )
        
        # Test authenticated access
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/v1/threads/{self.thread.id}/comments/")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response structure
        data = response.json()
        assert len(data["results"]) == 2
        assert all("content" in comment for comment in data["results"])

    def test_create_comment(self):
        """Test comment creation and replies."""
        comment_data = {
            "content": "Test comment"
        }
        
        # Test authenticated comment creation
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/v1/threads/{self.thread.id}/comments/", comment_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Test reply to comment
        parent_comment = response.json()
        reply_data = {
            "content": "Test reply",
            "parent_comment_id": parent_comment["id"]
        }
        response = self.client.post(f"/api/v1/threads/{self.thread.id}/comments/", reply_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["parent_comment_id"] == parent_comment["id"]

    def test_edit_delete_comment(self):
        """Test comment editing and deletion."""
        comment = Comment.objects.create(
            thread=self.thread,
            author=self.user,
            content="Original content"
        )
        
        # Test edit comment
        self.client.force_authenticate(user=self.user)
        edit_data = {"content": "Edited content"}
        response = self.client.patch(f"/api/v1/comments/{comment.id}/", edit_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["content"] == edit_data["content"]
        assert response.json()["is_edited"] is True
        
        # Test delete comment
        response = self.client.delete(f"/api/v1/comments/{comment.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=comment.id).exists()

@pytest.mark.django_db
class TestMessageViewSet:
    """
    Test cases for direct messaging endpoints.
    """

    def setup_method(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.sender = User.objects.create_user(
            email="sender@test.com",
            password="Test123!",
            first_name="Test",
            last_name="Sender"
        )
        self.recipient = User.objects.create_user(
            email="recipient@test.com",
            password="Test123!",
            first_name="Test",
            last_name="Recipient"
        )

    def test_send_message(self):
        """Test sending direct messages."""
        message_data = {
            "recipient_id": str(self.recipient.id),
            "content": "Test message content"
        }
        
        # Test authenticated message sending
        self.client.force_authenticate(user=self.sender)
        response = self.client.post("/api/v1/messages/", message_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify message data
        created_message = response.json()
        assert created_message["content"] == message_data["content"]
        assert created_message["sender"]["id"] == str(self.sender.id)
        assert created_message["recipient"]["id"] == message_data["recipient_id"]
        assert created_message["is_read"] is False

    def test_list_messages(self):
        """Test listing messages and conversation threads."""
        # Create test messages
        Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            content="Message 1"
        )
        Message.objects.create(
            sender=self.recipient,
            recipient=self.sender,
            content="Message 2"
        )
        
        # Test listing received messages
        self.client.force_authenticate(user=self.recipient)
        response = self.client.get("/api/v1/messages/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 1
        
        # Test conversation thread view
        response = self.client.get(f"/api/v1/messages/thread/{self.sender.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["messages"]) == 2

    def test_message_status(self):
        """Test message read status management."""
        message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            content="Test message"
        )
        
        # Test marking message as read
        self.client.force_authenticate(user=self.recipient)
        response = self.client.post(f"/api/v1/messages/{message.id}/read/")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify read status
        message.refresh_from_db()
        assert message.is_read is True
        assert message.read_at is not None