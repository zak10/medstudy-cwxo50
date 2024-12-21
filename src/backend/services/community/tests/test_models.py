"""
Test suite for community service models including forums, threads, comments, and direct messaging.
Tests validation, moderation, and protocol-specific constraints.

Version: 1.0.0
"""

# Third-party imports
import pytest  # version ^7.4.0
from freezegun import freeze_time  # version ^1.2.0
from django.utils import timezone  # version 4.2
from django.contrib.auth.models import User  # version 4.2

# Internal imports
from services.community.models import Forum, Thread, Comment, Message

# Mark all tests to use the database
pytestmark = pytest.mark.django_db

class TestForum:
    """Test cases for Forum model functionality."""

    def test_forum_creation(self, mocker):
        """Test basic forum creation with validation."""
        # Create test user
        user = User.objects.create(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

        # Create forum with valid data
        forum = Forum.objects.create(
            name="Test Forum",
            description="A test forum for unit testing",
            is_protocol_specific=False,
            created_at=timezone.now()
        )

        assert forum.id is not None
        assert forum.name == "Test Forum"
        assert forum.description == "A test forum for unit testing"
        assert forum.is_protocol_specific is False
        assert forum.protocol_id is None
        assert forum.is_active is True

    def test_protocol_specific_forum(self):
        """Test protocol-specific forum validation."""
        # Test forum creation with protocol ID
        protocol_id = "550e8400-e29b-41d4-a716-446655440000"
        forum = Forum.objects.create(
            name="Protocol Forum",
            description="Forum for specific protocol",
            is_protocol_specific=True,
            protocol_id=protocol_id
        )

        assert forum.protocol_id == protocol_id
        assert forum.is_protocol_specific is True

        # Test validation error when protocol_id is missing
        with pytest.raises(ValueError) as exc_info:
            Forum.objects.create(
                name="Invalid Forum",
                description="Missing protocol ID",
                is_protocol_specific=True
            )
        assert "Protocol-specific forums must have a protocol_id" in str(exc_info.value)

    def test_forum_content_sanitization(self):
        """Test HTML sanitization in forum description."""
        unsafe_description = """
        <p>Safe content</p>
        <script>alert('unsafe')</script>
        <a href="safe.com" onclick="unsafe()">Link</a>
        """

        forum = Forum.objects.create(
            name="Test Forum",
            description=unsafe_description
        )

        # Verify unsafe content is removed
        assert "<script>" not in forum.description
        assert "onclick" not in forum.description
        assert "<p>Safe content</p>" in forum.description
        assert '<a href="safe.com">Link</a>' in forum.description

class TestThread:
    """Test cases for Thread model functionality."""

    @pytest.fixture
    def test_forum(self):
        """Fixture to create test forum."""
        return Forum.objects.create(
            name="Test Forum",
            description="Test forum description"
        )

    @pytest.fixture
    def test_user(self):
        """Fixture to create test user."""
        return User.objects.create(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

    def test_thread_creation(self, test_forum, test_user):
        """Test basic thread creation and validation."""
        thread = Thread.objects.create(
            forum=test_forum,
            author=test_user,
            title="Test Thread",
            content="Thread content"
        )

        assert thread.id is not None
        assert thread.title == "Test Thread"
        assert thread.content == "Thread content"
        assert thread.view_count == 0
        assert thread.is_pinned is False
        assert thread.is_locked is False

    def test_thread_view_count(self, test_forum, test_user):
        """Test thread view count incrementation."""
        thread = Thread.objects.create(
            forum=test_forum,
            author=test_user,
            title="Test Thread",
            content="Content"
        )

        initial_count = thread.view_count
        thread.increment_view_count()
        thread.refresh_from_db()
        
        assert thread.view_count == initial_count + 1

    @freeze_time("2023-01-01 12:00:00")
    def test_thread_timestamps(self, test_forum, test_user):
        """Test thread timestamp handling."""
        thread = Thread.objects.create(
            forum=test_forum,
            author=test_user,
            title="Test Thread",
            content="Content"
        )

        assert thread.created_at == timezone.now()
        
        with freeze_time("2023-01-01 13:00:00"):
            thread.content = "Updated content"
            thread.save()
            assert thread.updated_at == timezone.now()

class TestComment:
    """Test cases for Comment model functionality."""

    @pytest.fixture
    def test_thread(self, test_forum, test_user):
        """Fixture to create test thread."""
        return Thread.objects.create(
            forum=test_forum,
            author=test_user,
            title="Test Thread",
            content="Thread content"
        )

    def test_comment_creation(self, test_thread, test_user):
        """Test basic comment creation."""
        comment = Comment.objects.create(
            thread=test_thread,
            author=test_user,
            content="Test comment"
        )

        assert comment.id is not None
        assert comment.content == "Test comment"
        assert comment.is_edited is False
        assert comment.parent_comment is None

    def test_nested_comments(self, test_thread, test_user):
        """Test nested comment functionality."""
        parent_comment = Comment.objects.create(
            thread=test_thread,
            author=test_user,
            content="Parent comment"
        )

        reply = Comment.objects.create(
            thread=test_thread,
            author=test_user,
            content="Reply comment",
            parent_comment=parent_comment
        )

        assert reply.parent_comment == parent_comment
        
        # Test validation of parent comment from different thread
        other_thread = Thread.objects.create(
            forum=test_thread.forum,
            author=test_user,
            title="Other Thread",
            content="Content"
        )

        with pytest.raises(ValueError) as exc_info:
            Comment.objects.create(
                thread=other_thread,
                author=test_user,
                content="Invalid reply",
                parent_comment=parent_comment
            )
        assert "Parent comment must belong to the same thread" in str(exc_info.value)

class TestMessage:
    """Test cases for Message model functionality."""

    @pytest.fixture
    def test_sender(self):
        """Fixture to create test sender."""
        return User.objects.create(
            email="sender@example.com",
            first_name="Sender",
            last_name="User"
        )

    @pytest.fixture
    def test_recipient(self):
        """Fixture to create test recipient."""
        return User.objects.create(
            email="recipient@example.com",
            first_name="Recipient",
            last_name="User"
        )

    def test_message_creation(self, test_sender, test_recipient):
        """Test basic message creation."""
        message = Message.objects.create(
            sender=test_sender,
            recipient=test_recipient,
            content="Test message"
        )

        assert message.id is not None
        assert message.content == "Test message"
        assert message.is_read is False
        assert message.read_at is None

    def test_message_read_status(self, test_sender, test_recipient):
        """Test message read status functionality."""
        message = Message.objects.create(
            sender=test_sender,
            recipient=test_recipient,
            content="Test message"
        )

        assert message.is_read is False
        assert message.read_at is None

        message.mark_as_read()
        message.refresh_from_db()

        assert message.is_read is True
        assert message.read_at is not None

    def test_self_messaging_prevention(self, test_sender):
        """Test prevention of sending messages to self."""
        with pytest.raises(ValueError) as exc_info:
            Message.objects.create(
                sender=test_sender,
                recipient=test_sender,
                content="Self message"
            )
        assert "Cannot send message to self" in str(exc_info.value)