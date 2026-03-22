"""
Unit tests for shopping session management service.

Tests the SessionManager class including:
- Session creation for guest and registered users
- Session retrieval with expiration validation
- Conversation history management
- Cart updates
- Preference management
- Error handling
"""

import logging
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, Column, String, JSON, TIMESTAMP, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.dialects import postgresql

from ops_api.services.shopping_sessions import SessionManager, GUEST_EXPIRY_DAYS

# Create a separate base for testing that uses JSON instead of JSONB
TestBase = declarative_base()


# Create minimal mock models for testing
class MockUser(TestBase):
    """Mock users table for testing shopping models."""
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)


class TestShoppingSession(TestBase):
    """Minimal ShoppingSession model for testing (uses JSON instead of JSONB)."""
    __tablename__ = "shopping_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    conversation_history = Column(JSON, nullable=False, default=list)
    cart_items = Column(JSON, nullable=False, default=list)
    session_preferences = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, default=datetime.utcnow)
    last_activity = Column(TIMESTAMP(timezone=False), nullable=False, default=datetime.utcnow)
    expires_at = Column(TIMESTAMP(timezone=False), nullable=True)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")

    # Disable foreign key constraints for testing
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    # Create test models, not the real ones
    TestBase.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def session_manager_with_db(in_memory_db):
    """Create a SessionManager with database connection."""
    return SessionManager(db=in_memory_db, model_class=TestShoppingSession)


@pytest.fixture
def session_manager_no_db():
    """Create a SessionManager without database (testing mode)."""
    logger = logging.getLogger("test_logger")
    return SessionManager(db=None, logger_instance=logger, model_class=TestShoppingSession)


# =============================================================================
# TEST CREATE SESSION
# =============================================================================


class TestCreateSession:
    """Test session creation functionality."""

    def test_create_guest_session_with_db(self, session_manager_with_db, in_memory_db):
        """Test creating a guest session with 30-day expiry."""
        session = session_manager_with_db.create_session(customer_id=None)

        assert session.session_id is not None
        assert session.customer_id is None
        assert session.conversation_history == []
        assert session.cart_items == []
        assert session.session_preferences == {}
        assert session.created_at is not None
        assert session.last_activity is not None
        assert session.expires_at is not None

        # Verify expiry is approximately 30 days from now
        expected_expiry = datetime.utcnow() + timedelta(days=GUEST_EXPIRY_DAYS)
        time_diff = abs((session.expires_at - expected_expiry).total_seconds())
        assert time_diff < 5  # Allow 5 second tolerance

        # Verify persisted to database
        persisted = in_memory_db.query(TestShoppingSession).filter(
            TestShoppingSession.session_id == session.session_id
        ).first()
        assert persisted is not None
        assert persisted.expires_at is not None

    def test_create_registered_session_with_db(self, session_manager_with_db, in_memory_db):
        """Test creating a registered user session with no expiry."""
        customer_id = uuid4()
        session = session_manager_with_db.create_session(customer_id=customer_id)

        assert session.session_id is not None
        assert session.customer_id == customer_id
        assert session.conversation_history == []
        assert session.cart_items == []
        assert session.session_preferences == {}
        assert session.expires_at is None  # Registered users have no expiry

        # Verify persisted to database
        persisted = in_memory_db.query(TestShoppingSession).filter(
            TestShoppingSession.session_id == session.session_id
        ).first()
        assert persisted is not None
        assert persisted.expires_at is None



# =============================================================================
# TEST GET SESSION
# =============================================================================


class TestGetSession:
    """Test session retrieval functionality."""

    def test_get_session_success(self, session_manager_with_db):
        """Test successfully retrieving an existing session."""
        # Create session
        created = session_manager_with_db.create_session(customer_id=None)

        # Retrieve session
        retrieved = session_manager_with_db.get_session(created.session_id)

        assert retrieved.session_id == created.session_id
        assert retrieved.customer_id == created.customer_id

    def test_get_session_not_found(self, session_manager_with_db):
        """Test retrieving a non-existent session raises ValueError."""
        fake_session_id = uuid4()

        with pytest.raises(ValueError, match="Session not found"):
            session_manager_with_db.get_session(fake_session_id)

    def test_get_session_expired(self, session_manager_with_db, in_memory_db):
        """Test retrieving an expired guest session raises ValueError."""
        # Create guest session
        session = session_manager_with_db.create_session(customer_id=None)

        # Manually expire the session by setting expires_at to the past
        db_session = in_memory_db.query(TestShoppingSession).filter(
            TestShoppingSession.session_id == session.session_id
        ).first()
        db_session.expires_at = datetime.utcnow() - timedelta(days=1)
        in_memory_db.commit()

        # Try to retrieve should raise ValueError
        with pytest.raises(ValueError, match="Session has expired"):
            session_manager_with_db.get_session(session.session_id)

    def test_get_session_registered_no_expiry(self, session_manager_with_db):
        """Test that registered sessions don't expire."""
        customer_id = uuid4()
        session = session_manager_with_db.create_session(customer_id=customer_id)

        # Even if we wait, should be able to retrieve
        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.session_id == session.session_id

    def test_get_session_no_db_raises_error(self, session_manager_no_db):
        """Test that get_session without DB connection raises ValueError."""
        fake_session_id = uuid4()

        with pytest.raises(ValueError, match="Cannot retrieve session without database"):
            session_manager_no_db.get_session(fake_session_id)


# =============================================================================
# TEST ADD MESSAGE
# =============================================================================


class TestAddMessage:
    """Test conversation history management."""

    def test_add_single_message(self, session_manager_with_db):
        """Test adding a single message to conversation history."""
        session = session_manager_with_db.create_session(customer_id=None)

        session_manager_with_db.add_message(
            session.session_id,
            role="user",
            content="What products do you have?"
        )

        # Retrieve and verify
        retrieved = session_manager_with_db.get_session(session.session_id)
        assert len(retrieved.conversation_history) == 1
        assert retrieved.conversation_history[0]["role"] == "user"
        assert retrieved.conversation_history[0]["content"] == "What products do you have?"
        assert "timestamp" in retrieved.conversation_history[0]

    def test_add_multiple_messages(self, session_manager_with_db):
        """Test adding multiple messages to conversation history."""
        session = session_manager_with_db.create_session(customer_id=None)

        # Add user message
        session_manager_with_db.add_message(
            session.session_id,
            role="user",
            content="Do you have laptops?"
        )

        # Add assistant message
        session_manager_with_db.add_message(
            session.session_id,
            role="assistant",
            content="Yes, we have several laptop models available."
        )

        # Add another user message
        session_manager_with_db.add_message(
            session.session_id,
            role="user",
            content="What's the price?"
        )

        # Verify conversation
        retrieved = session_manager_with_db.get_session(session.session_id)
        assert len(retrieved.conversation_history) == 3
        assert retrieved.conversation_history[0]["role"] == "user"
        assert retrieved.conversation_history[1]["role"] == "assistant"
        assert retrieved.conversation_history[2]["role"] == "user"

    def test_message_timestamp_format(self, session_manager_with_db):
        """Test that message timestamps are in ISO8601 format."""
        session = session_manager_with_db.create_session(customer_id=None)

        session_manager_with_db.add_message(
            session.session_id,
            role="user",
            content="Test message"
        )

        retrieved = session_manager_with_db.get_session(session.session_id)
        timestamp = retrieved.conversation_history[0]["timestamp"]

        # Should be ISO8601 format
        assert "T" in timestamp
        assert ":" in timestamp

    def test_add_message_updates_last_activity(self, session_manager_with_db):
        """Test that adding a message updates last_activity timestamp."""
        session = session_manager_with_db.create_session(customer_id=None)
        original_activity = session.last_activity

        # Wait a moment to ensure different timestamp
        import time
        time.sleep(0.1)

        session_manager_with_db.add_message(
            session.session_id,
            role="user",
            content="Test"
        )

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.last_activity > original_activity

    def test_add_message_nonexistent_session(self, session_manager_with_db):
        """Test adding message to non-existent session raises ValueError."""
        fake_session_id = uuid4()

        with pytest.raises(ValueError, match="Session not found"):
            session_manager_with_db.add_message(
                fake_session_id,
                role="user",
                content="Test"
            )

    def test_add_message_expired_session(self, session_manager_with_db, in_memory_db):
        """Test adding message to expired session raises ValueError."""
        session = session_manager_with_db.create_session(customer_id=None)

        # Expire the session
        db_session = in_memory_db.query(TestShoppingSession).filter(
            TestShoppingSession.session_id == session.session_id
        ).first()
        db_session.expires_at = datetime.utcnow() - timedelta(days=1)
        in_memory_db.commit()

        with pytest.raises(ValueError, match="Session has expired"):
            session_manager_with_db.add_message(
                session.session_id,
                role="user",
                content="Test"
            )


# =============================================================================
# TEST UPDATE CART
# =============================================================================


class TestUpdateCart:
    """Test shopping cart management."""

    def test_update_cart_single_item(self, session_manager_with_db):
        """Test updating cart with a single item."""
        session = session_manager_with_db.create_session(customer_id=None)

        cart_items = [
            {
                "product_id": "laptop-001",
                "name": "Dell XPS 15",
                "price": 1299.99,
                "quantity": 1
            }
        ]

        session_manager_with_db.update_cart(session.session_id, cart_items)

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert len(retrieved.cart_items) == 1
        assert retrieved.cart_items[0]["product_id"] == "laptop-001"
        assert retrieved.cart_items[0]["quantity"] == 1

    def test_update_cart_multiple_items(self, session_manager_with_db):
        """Test updating cart with multiple items."""
        session = session_manager_with_db.create_session(customer_id=None)

        cart_items = [
            {
                "product_id": "laptop-001",
                "name": "Dell XPS 15",
                "price": 1299.99,
                "quantity": 1
            },
            {
                "product_id": "mouse-001",
                "name": "Logitech MX Master",
                "price": 99.99,
                "quantity": 2
            }
        ]

        session_manager_with_db.update_cart(session.session_id, cart_items)

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert len(retrieved.cart_items) == 2
        assert retrieved.cart_items[0]["product_id"] == "laptop-001"
        assert retrieved.cart_items[1]["product_id"] == "mouse-001"

    def test_update_cart_empty(self, session_manager_with_db):
        """Test updating cart with empty list."""
        session = session_manager_with_db.create_session(customer_id=None)

        # First add items
        cart_items = [{"product_id": "test", "quantity": 1}]
        session_manager_with_db.update_cart(session.session_id, cart_items)

        # Clear cart
        session_manager_with_db.update_cart(session.session_id, [])

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert len(retrieved.cart_items) == 0

    def test_update_cart_updates_last_activity(self, session_manager_with_db):
        """Test that updating cart updates last_activity."""
        session = session_manager_with_db.create_session(customer_id=None)
        original_activity = session.last_activity

        import time
        time.sleep(0.1)

        session_manager_with_db.update_cart(
            session.session_id,
            [{"product_id": "test", "quantity": 1}]
        )

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.last_activity > original_activity

    def test_update_cart_nonexistent_session(self, session_manager_with_db):
        """Test updating cart for non-existent session raises ValueError."""
        fake_session_id = uuid4()

        with pytest.raises(ValueError, match="Session not found"):
            session_manager_with_db.update_cart(
                fake_session_id,
                [{"product_id": "test"}]
            )

    def test_update_cart_replaces_items(self, session_manager_with_db):
        """Test that update_cart replaces all items, not appends."""
        session = session_manager_with_db.create_session(customer_id=None)

        # Add first set of items
        session_manager_with_db.update_cart(
            session.session_id,
            [{"product_id": "item-1", "quantity": 1}]
        )

        # Update with new items
        session_manager_with_db.update_cart(
            session.session_id,
            [
                {"product_id": "item-2", "quantity": 2},
                {"product_id": "item-3", "quantity": 1}
            ]
        )

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert len(retrieved.cart_items) == 2
        assert retrieved.cart_items[0]["product_id"] == "item-2"
        assert "item-1" not in str(retrieved.cart_items)


# =============================================================================
# TEST UPDATE PREFERENCES
# =============================================================================


class TestUpdatePreferences:
    """Test session preferences management."""

    def test_update_preferences_single(self, session_manager_with_db):
        """Test updating a single preference."""
        session = session_manager_with_db.create_session(customer_id=None)

        preferences = {"theme": "dark"}
        session_manager_with_db.update_preferences(session.session_id, preferences)

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.session_preferences["theme"] == "dark"

    def test_update_preferences_multiple(self, session_manager_with_db):
        """Test updating multiple preferences."""
        session = session_manager_with_db.create_session(customer_id=None)

        preferences = {
            "theme": "dark",
            "language": "en",
            "notifications": True
        }
        session_manager_with_db.update_preferences(session.session_id, preferences)

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.session_preferences["theme"] == "dark"
        assert retrieved.session_preferences["language"] == "en"
        assert retrieved.session_preferences["notifications"] is True

    def test_update_preferences_incremental(self, session_manager_with_db):
        """Test that update_preferences merges with existing preferences."""
        session = session_manager_with_db.create_session(customer_id=None)

        # Set initial preferences
        session_manager_with_db.update_preferences(
            session.session_id,
            {"theme": "dark", "language": "en"}
        )

        # Update with additional preference
        session_manager_with_db.update_preferences(
            session.session_id,
            {"notifications": False}
        )

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.session_preferences["theme"] == "dark"
        assert retrieved.session_preferences["language"] == "en"
        assert retrieved.session_preferences["notifications"] is False

    def test_update_preferences_override(self, session_manager_with_db):
        """Test that update_preferences can override existing values."""
        session = session_manager_with_db.create_session(customer_id=None)

        session_manager_with_db.update_preferences(session.session_id, {"theme": "dark"})
        session_manager_with_db.update_preferences(session.session_id, {"theme": "light"})

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.session_preferences["theme"] == "light"

    def test_update_preferences_updates_last_activity(self, session_manager_with_db):
        """Test that updating preferences updates last_activity."""
        session = session_manager_with_db.create_session(customer_id=None)
        original_activity = session.last_activity

        import time
        time.sleep(0.1)

        session_manager_with_db.update_preferences(
            session.session_id,
            {"theme": "dark"}
        )

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.last_activity > original_activity

    def test_update_preferences_nonexistent_session(self, session_manager_with_db):
        """Test updating preferences for non-existent session raises ValueError."""
        fake_session_id = uuid4()

        with pytest.raises(ValueError, match="Session not found"):
            session_manager_with_db.update_preferences(
                fake_session_id,
                {"theme": "dark"}
            )

    def test_update_preferences_complex_objects(self, session_manager_with_db):
        """Test updating preferences with complex nested objects."""
        session = session_manager_with_db.create_session(customer_id=None)

        preferences = {
            "filters": {
                "price_range": {"min": 100, "max": 1000},
                "categories": ["laptops", "phones"]
            }
        }
        session_manager_with_db.update_preferences(session.session_id, preferences)

        retrieved = session_manager_with_db.get_session(session.session_id)
        assert retrieved.session_preferences["filters"]["price_range"]["min"] == 100
        assert "laptops" in retrieved.session_preferences["filters"]["categories"]


# =============================================================================
# TEST DELETE SESSION
# =============================================================================


class TestDeleteSession:
    """Test session deletion functionality."""

    def test_delete_session_success(self, session_manager_with_db, in_memory_db):
        """Test successfully deleting a session."""
        session = session_manager_with_db.create_session(customer_id=None)
        session_id = session.session_id

        # Verify session exists
        assert in_memory_db.query(TestShoppingSession).filter(
            TestShoppingSession.session_id == session_id
        ).first() is not None

        # Delete session
        session_manager_with_db.delete_session(session_id)

        # Verify session is deleted
        assert in_memory_db.query(TestShoppingSession).filter(
            TestShoppingSession.session_id == session_id
        ).first() is None

    def test_delete_nonexistent_session(self, session_manager_with_db):
        """Test deleting a non-existent session raises ValueError."""
        fake_session_id = uuid4()

        with pytest.raises(ValueError, match="Session not found"):
            session_manager_with_db.delete_session(fake_session_id)

    def test_delete_session_no_db_raises_error(self, session_manager_no_db):
        """Test that delete_session without DB connection raises ValueError."""
        fake_session_id = uuid4()

        with pytest.raises(ValueError, match="Cannot delete session without database"):
            session_manager_no_db.delete_session(fake_session_id)

    def test_delete_expired_session(self, session_manager_with_db, in_memory_db):
        """Test that deleting an expired session raises ValueError."""
        session = session_manager_with_db.create_session(customer_id=None)
        session_id = session.session_id

        # Expire the session
        db_session = in_memory_db.query(TestShoppingSession).filter(
            TestShoppingSession.session_id == session_id
        ).first()
        db_session.expires_at = datetime.utcnow() - timedelta(days=1)
        in_memory_db.commit()

        # Cannot delete an expired session (same validation as get_session)
        with pytest.raises(ValueError, match="Session has expired"):
            session_manager_with_db.delete_session(session_id)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestSessionIntegration:
    """Integration tests combining multiple operations."""

    def test_full_session_lifecycle(self, session_manager_with_db):
        """Test complete session lifecycle: create, add messages, update cart, etc."""
        # 1. Create session
        session = session_manager_with_db.create_session(customer_id=None)
        assert session.session_id is not None

        # 2. Add conversation messages
        session_manager_with_db.add_message(
            session.session_id,
            role="user",
            content="I'm looking for a laptop"
        )
        session_manager_with_db.add_message(
            session.session_id,
            role="assistant",
            content="We have several options available"
        )

        # 3. Update preferences
        session_manager_with_db.update_preferences(
            session.session_id,
            {"budget": 1500, "preferred_brand": "Dell"}
        )

        # 4. Update cart
        session_manager_with_db.update_cart(
            session.session_id,
            [
                {"product_id": "dell-xps-15", "name": "Dell XPS 15", "quantity": 1}
            ]
        )

        # 5. Retrieve and verify full state
        final_session = session_manager_with_db.get_session(session.session_id)
        assert len(final_session.conversation_history) == 2
        assert final_session.session_preferences["budget"] == 1500
        assert len(final_session.cart_items) == 1
        assert final_session.cart_items[0]["product_id"] == "dell-xps-15"

    def test_concurrent_sessions(self, session_manager_with_db):
        """Test managing multiple independent sessions."""
        # Create multiple sessions
        session1 = session_manager_with_db.create_session(customer_id=None)
        session2 = session_manager_with_db.create_session(customer_id=uuid4())
        session3 = session_manager_with_db.create_session(customer_id=None)

        # Add different content to each
        session_manager_with_db.add_message(
            session1.session_id,
            role="user",
            content="Session 1"
        )
        session_manager_with_db.add_message(
            session2.session_id,
            role="user",
            content="Session 2"
        )

        # Verify isolation
        s1 = session_manager_with_db.get_session(session1.session_id)
        s2 = session_manager_with_db.get_session(session2.session_id)
        s3 = session_manager_with_db.get_session(session3.session_id)

        assert len(s1.conversation_history) == 1
        assert len(s2.conversation_history) == 1
        assert len(s3.conversation_history) == 0

    def test_session_state_persistence(self, session_manager_with_db, in_memory_db):
        """Test that session state is properly persisted and retrieved."""
        # Create and populate session
        session = session_manager_with_db.create_session(customer_id=None)

        session_manager_with_db.add_message(
            session.session_id,
            role="user",
            content="Test message"
        )
        session_manager_with_db.update_cart(
            session.session_id,
            [{"product_id": "test", "quantity": 1}]
        )
        session_manager_with_db.update_preferences(
            session.session_id,
            {"color": "blue"}
        )

        # Create new manager with same database and model class
        new_manager = SessionManager(db=in_memory_db, model_class=TestShoppingSession)

        # Verify state is persisted
        retrieved = new_manager.get_session(session.session_id)
        assert len(retrieved.conversation_history) == 1
        assert len(retrieved.cart_items) == 1
        assert retrieved.session_preferences["color"] == "blue"
