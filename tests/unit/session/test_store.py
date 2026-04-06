"""
Unit tests for session store.

Tests the SessionStore class including:
- Session creation with unique IDs
- Conversation history management (adding messages)
- User context storage
- Session lifecycle: active -> closed -> archived
- Redis caching with 24-hour TTL
- Session retrieval and message retrieval
"""

import pytest
from datetime import datetime, UTC
from uuid import uuid4
import fakeredis

from acosplatform.session.models import ChatSession, ChatMessage, MessageRole, SessionStatus
from acosplatform.session.store import SessionStore


@pytest.fixture
def redis_client():
    """Create a fake Redis client for testing."""
    return fakeredis.FakeStrictRedis()


@pytest.fixture
def session_store(redis_client):
    """Create a SessionStore instance with fake Redis."""
    store = SessionStore(redis_client=redis_client)
    return store


class TestSessionStore:
    """Tests for SessionStore."""

    def test_create_session_returns_session_with_unique_id(self, session_store):
        """Test that create_session returns a ChatSession with a unique ID."""
        user_id = "user-123"
        session = session_store.create_session(user_id=user_id)

        assert isinstance(session, ChatSession)
        assert session.id is not None
        assert session.id.startswith("sess_")
        assert session.user_id == user_id
        assert session.status == SessionStatus.ACTIVE
        assert session.created_at is not None
        assert session.messages == []
        assert session.context == {}

    def test_create_session_generates_different_ids(self, session_store):
        """Test that multiple create_session calls generate unique IDs."""
        session1 = session_store.create_session(user_id="user-1")
        session2 = session_store.create_session(user_id="user-2")

        assert session1.id != session2.id

    def test_get_session_returns_created_session(self, session_store):
        """Test that get_session retrieves a previously created session."""
        user_id = "user-123"
        created_session = session_store.create_session(user_id=user_id)

        retrieved_session = session_store.get_session(created_session.id)

        assert retrieved_session is not None
        assert retrieved_session.id == created_session.id
        assert retrieved_session.user_id == user_id
        assert retrieved_session.status == SessionStatus.ACTIVE

    def test_get_session_returns_none_for_nonexistent_session(self, session_store):
        """Test that get_session returns None for non-existent session."""
        result = session_store.get_session("sess_nonexistent")
        assert result is None

    def test_add_message_to_session(self, session_store):
        """Test that add_message adds a message to session history."""
        session = session_store.create_session(user_id="user-123")

        message = session_store.add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content="Hello, assistant!"
        )

        assert isinstance(message, ChatMessage)
        assert message.role == MessageRole.USER
        assert message.content == "Hello, assistant!"
        assert message.timestamp is not None

        # Verify message is in session
        retrieved_session = session_store.get_session(session.id)
        assert len(retrieved_session.messages) == 1
        assert retrieved_session.messages[0].role == MessageRole.USER
        assert retrieved_session.messages[0].content == "Hello, assistant!"

    def test_add_multiple_messages_to_session(self, session_store):
        """Test that multiple messages can be added to a session."""
        session = session_store.create_session(user_id="user-123")

        msg1 = session_store.add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content="First message"
        )
        msg2 = session_store.add_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content="First response"
        )
        msg3 = session_store.add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content="Second message"
        )

        retrieved_session = session_store.get_session(session.id)
        assert len(retrieved_session.messages) == 3
        assert retrieved_session.messages[0].content == "First message"
        assert retrieved_session.messages[1].content == "First response"
        assert retrieved_session.messages[2].content == "Second message"

    def test_add_message_to_nonexistent_session_returns_none(self, session_store):
        """Test that add_message returns None if session doesn't exist."""
        result = session_store.add_message(
            session_id="sess_nonexistent",
            role=MessageRole.USER,
            content="Message"
        )
        assert result is None

    def test_update_context_stores_user_data(self, session_store):
        """Test that update_context stores user context data."""
        session = session_store.create_session(user_id="user-123")

        context_data = {
            "preferences": {"theme": "dark"},
            "cart": {"items": ["item1", "item2"]},
            "last_action": "checkout"
        }

        result = session_store.update_context(session.id, context_data)
        assert result is True

        # Verify context is stored
        retrieved_session = session_store.get_session(session.id)
        assert retrieved_session.context == context_data

    def test_update_context_merges_with_existing_context(self, session_store):
        """Test that update_context merges with existing context."""
        session = session_store.create_session(user_id="user-123")

        # First update
        session_store.update_context(session.id, {"key1": "value1", "key2": "value2"})

        # Second update should merge
        session_store.update_context(session.id, {"key2": "updated_value2", "key3": "value3"})

        retrieved_session = session_store.get_session(session.id)
        assert retrieved_session.context["key1"] == "value1"
        assert retrieved_session.context["key2"] == "updated_value2"
        assert retrieved_session.context["key3"] == "value3"

    def test_update_context_for_nonexistent_session_returns_false(self, session_store):
        """Test that update_context returns False for non-existent session."""
        result = session_store.update_context(
            "sess_nonexistent",
            {"key": "value"}
        )
        assert result is False

    def test_close_session_updates_status(self, session_store):
        """Test that close_session updates session status to CLOSED."""
        session = session_store.create_session(user_id="user-123")

        # Add some messages
        session_store.add_message(session.id, MessageRole.USER, "Hello")
        session_store.add_message(session.id, MessageRole.ASSISTANT, "Hi there")

        # Close session
        result = session_store.close_session(session.id)
        assert result is True

        retrieved_session = session_store.get_session(session.id)
        assert retrieved_session.status == SessionStatus.CLOSED
        assert retrieved_session.closed_at is not None

    def test_close_session_for_nonexistent_session_returns_false(self, session_store):
        """Test that close_session returns False for non-existent session."""
        result = session_store.close_session("sess_nonexistent")
        assert result is False

    def test_archive_session_updates_status(self, session_store):
        """Test that archive_session updates session status to ARCHIVED."""
        session = session_store.create_session(user_id="user-123")

        # Close first
        session_store.close_session(session.id)

        # Then archive
        result = session_store.archive_session(session.id)
        assert result is True

        retrieved_session = session_store.get_session(session.id)
        assert retrieved_session.status == SessionStatus.ARCHIVED
        assert retrieved_session.archived_at is not None

    def test_archive_session_for_nonexistent_session_returns_false(self, session_store):
        """Test that archive_session returns False for non-existent session."""
        result = session_store.archive_session("sess_nonexistent")
        assert result is False

    def test_session_ttl_is_24_hours(self, session_store):
        """Test that sessions are cached with 24-hour TTL."""
        session = session_store.create_session(user_id="user-123")

        # Verify the session exists
        assert session_store.get_session(session.id) is not None

        # Check that TTL is set correctly (should be around 86400 seconds = 24 hours)
        assert session_store.SESSION_TTL == 86400  # 24 hours in seconds

    def test_session_lifecycle_active_to_closed_to_archived(self, session_store):
        """Test full session lifecycle: ACTIVE -> CLOSED -> ARCHIVED."""
        session = session_store.create_session(user_id="user-123")

        # Initial state
        assert session_store.get_session(session.id).status == SessionStatus.ACTIVE

        # Add some conversation
        session_store.add_message(session.id, MessageRole.USER, "What is 2+2?")
        session_store.add_message(session.id, MessageRole.ASSISTANT, "2+2 equals 4")

        # Update context
        session_store.update_context(session.id, {"math_level": "basic"})

        # Close session
        session_store.close_session(session.id)
        retrieved = session_store.get_session(session.id)
        assert retrieved.status == SessionStatus.CLOSED
        assert len(retrieved.messages) == 2
        assert retrieved.context["math_level"] == "basic"

        # Archive session
        session_store.archive_session(session.id)
        retrieved = session_store.get_session(session.id)
        assert retrieved.status == SessionStatus.ARCHIVED

    def test_message_role_enum(self):
        """Test that MessageRole enum has all expected values."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_session_status_enum(self):
        """Test that SessionStatus enum has all expected values."""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.CLOSED.value == "closed"
        assert SessionStatus.ARCHIVED.value == "archived"

    def test_create_session_with_initial_context(self, session_store):
        """Test that create_session can accept initial context."""
        initial_context = {"preferences": {"lang": "en"}}
        session = session_store.create_session(
            user_id="user-123",
            initial_context=initial_context
        )

        assert session.context == initial_context

        retrieved = session_store.get_session(session.id)
        assert retrieved.context == initial_context

    def test_get_messages_for_session(self, session_store):
        """Test that get_messages retrieves all messages for a session."""
        session = session_store.create_session(user_id="user-123")

        session_store.add_message(session.id, MessageRole.USER, "Hello")
        session_store.add_message(session.id, MessageRole.ASSISTANT, "Hi")
        session_store.add_message(session.id, MessageRole.USER, "How are you?")

        messages = session_store.get_messages(session.id)

        assert len(messages) == 3
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi"
        assert messages[2].content == "How are you?"

    def test_get_messages_for_nonexistent_session_returns_empty_list(self, session_store):
        """Test that get_messages returns empty list for non-existent session."""
        messages = session_store.get_messages("sess_nonexistent")
        assert messages == []
