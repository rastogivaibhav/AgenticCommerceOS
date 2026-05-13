"""
ops_api.services.shopping_sessions — Session management service for shopping chatbot.

This module provides the SessionManager class for managing shopping sessions,
including conversation history, cart persistence, and user preferences.

The SessionManager handles:
- Session lifecycle management (creation, retrieval, deletion)
- Guest vs. registered user session expiration rules
- Conversation history persistence
- Cart state management
- User preference tracking
- Database persistence with fallback testing mode
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session as SQLSession
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import flag_modified

from ops_api.models.shopping import ShoppingSession

# Configuration constants
GUEST_EXPIRY_DAYS = 30

# Initialize logger
logger = logging.getLogger(__name__)


class SessionManager:
    """Manages shopping sessions for the shopping chatbot system.

    Handles session creation, retrieval, and updates for both guest and
    registered customers. Implements session expiration for guests and
    persists conversation history, cart items, and preferences.

    Attributes:
        db: SQLAlchemy session for database operations (optional for testing)
        logger: Logger instance for tracking operations
        model_class: Session model class (defaults to ShoppingSession)
    """

    def __init__(self, db: Optional[SQLSession] = None, logger_instance=None, model_class=None):
        """Initialize SessionManager with optional database connection.

        Args:
            db: SQLAlchemy session for database operations. If None, methods
                will return objects but not persist to database (testing mode).
            logger_instance: Optional logger instance. Defaults to module logger.
            model_class: Optional model class to use instead of ShoppingSession.
                         Useful for testing with different model implementations.
        """
        self.db = db
        self.logger = logger_instance or logger
        self.model_class = model_class or ShoppingSession

    def _mark_dirty(self, obj) -> None:
        """Mark a SQLAlchemy object as dirty for JSON field updates.

        SQLAlchemy doesn't automatically track mutations of mutable objects
        like lists and dicts in JSON columns. This helper marks the object
        as needing an update.

        Args:
            obj: The SQLAlchemy object to mark as dirty.
        """
        if self.db is not None and hasattr(obj, '__dict__'):
            flag_modified(obj, 'conversation_history')
            flag_modified(obj, 'cart_items')
            flag_modified(obj, 'session_preferences')

    def create_session(self, customer_id: Optional[UUID] = None) -> ShoppingSession:
        """Create a new shopping session.

        For guest users (customer_id=None), sets expiration to 30 days from now.
        For registered users, no expiration is set (None).

        Args:
            customer_id: Optional UUID of the customer. If None, creates a guest session.

        Returns:
            ShoppingSession: The newly created session object.

        Raises:
            ValueError: If database operation fails (when db is not None).
        """
        try:
            now = datetime.utcnow()
            expires_at = None

            # Set expiration for guest sessions
            if customer_id is None:
                expires_at = now + timedelta(days=GUEST_EXPIRY_DAYS)
                self.logger.info(
                    f"Creating guest session with 30-day expiry: {expires_at}"
                )
            else:
                self.logger.info(
                    f"Creating registered session for customer: {customer_id}"
                )

            # Create session object
            session = self.model_class(
                customer_id=customer_id,
                conversation_history=[],
                cart_items=[],
                session_preferences={},
                created_at=now,
                last_activity=now,
                expires_at=expires_at,
            )

            # Persist to database if connection available
            if self.db is not None:
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)
                self.logger.info(f"Session created and persisted: {session.session_id}")
            else:
                self.logger.debug(
                    "Database not available; session created in memory only"
                )

            return session

        except Exception as e:
            self.logger.error(f"Error creating session: {str(e)}")
            if self.db is not None:
                self.db.rollback()
            raise ValueError(f"Failed to create session: {str(e)}")

    def get_session(self, session_id: UUID) -> ShoppingSession:
        """Retrieve a session by ID with expiration validation.

        Checks if the session has expired for guest users. Raises ValueError
        if session not found or has expired.

        Args:
            session_id: UUID of the session to retrieve.

        Returns:
            ShoppingSession: The retrieved session object.

        Raises:
            ValueError: If session not found, has expired, or database error occurs.
        """
        try:
            if self.db is None:
                raise ValueError("Cannot retrieve session without database connection")

            session = self.db.query(self.model_class).filter(
                self.model_class.session_id == session_id
            ).first()

            if session is None:
                self.logger.warning(f"Session not found: {session_id}")
                raise ValueError(f"Session not found: {session_id}")

            # Check expiration for guest sessions
            if session.expires_at is not None:
                now = datetime.utcnow()
                if session.expires_at < now:
                    self.logger.warning(
                        f"Session has expired: {session_id} (expired at {session.expires_at})"
                    )
                    raise ValueError(f"Session has expired: {session_id}")

            self.logger.debug(f"Session retrieved: {session_id}")
            return session

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving session {session_id}: {str(e)}")
            raise ValueError(f"Failed to retrieve session: {str(e)}")

    def add_message(self, session_id: UUID, role: str, content: str) -> None:
        """Add a message to the conversation history.

        Appends a new message with timestamp to the conversation history
        and updates the session's last_activity timestamp.

        Args:
            session_id: UUID of the session.
            role: Role of the message sender (e.g., 'user', 'assistant').
            content: Content of the message.

        Raises:
            ValueError: If session not found or database operation fails.
        """
        try:
            session = self.get_session(session_id)

            # Create message object with ISO8601 timestamp
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Append to conversation history
            if session.conversation_history is None:
                session.conversation_history = []
            session.conversation_history.append(message)

            # Update last activity
            session.last_activity = datetime.utcnow()

            # Persist to database
            if self.db is not None:
                self._mark_dirty(session)
                self.db.commit()
                self.logger.info(
                    f"Message added to session {session_id} "
                    f"(total messages: {len(session.conversation_history)})"
                )
            else:
                self.logger.debug("Database not available; message stored in memory only")

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error adding message to session {session_id}: {str(e)}"
            )
            if self.db is not None:
                self.db.rollback()
            raise ValueError(f"Failed to add message to session: {str(e)}")

    def update_cart(self, session_id: UUID, cart_items: List[Dict]) -> None:
        """Update the shopping cart items for a session.

        Replaces the entire cart_items list and updates last_activity.

        Args:
            session_id: UUID of the session.
            cart_items: List of cart item dictionaries.

        Raises:
            ValueError: If session not found or database operation fails.
        """
        try:
            session = self.get_session(session_id)

            # Update cart items
            session.cart_items = cart_items if cart_items else []

            # Update last activity
            session.last_activity = datetime.utcnow()

            # Persist to database
            if self.db is not None:
                self._mark_dirty(session)
                self.db.commit()
                self.logger.info(
                    f"Cart updated for session {session_id} "
                    f"(total items: {len(session.cart_items)})"
                )
            else:
                self.logger.debug("Database not available; cart stored in memory only")

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating cart for session {session_id}: {str(e)}")
            if self.db is not None:
                self.db.rollback()
            raise ValueError(f"Failed to update cart: {str(e)}")

    def update_preferences(
        self, session_id: UUID, preferences: Dict
    ) -> None:
        """Update session preferences.

        Updates the session_preferences JSONB field and last_activity timestamp.

        Args:
            session_id: UUID of the session.
            preferences: Dictionary of preference key-value pairs.

        Raises:
            ValueError: If session not found or database operation fails.
        """
        try:
            session = self.get_session(session_id)

            # Update preferences
            if session.session_preferences is None:
                session.session_preferences = {}
            session.session_preferences.update(preferences)

            # Update last activity
            session.last_activity = datetime.utcnow()

            # Persist to database
            if self.db is not None:
                self._mark_dirty(session)
                self.db.commit()
                self.logger.info(
                    f"Preferences updated for session {session_id} "
                    f"(total keys: {len(session.session_preferences)})"
                )
            else:
                self.logger.debug(
                    "Database not available; preferences stored in memory only"
                )

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error updating preferences for session {session_id}: {str(e)}"
            )
            if self.db is not None:
                self.db.rollback()
            raise ValueError(f"Failed to update preferences: {str(e)}")

    def delete_session(self, session_id: UUID) -> None:
        """Delete a session from the database.

        Useful for cleaning up expired guest sessions or user-initiated cleanup.

        Args:
            session_id: UUID of the session to delete.

        Raises:
            ValueError: If session not found or database operation fails.
        """
        try:
            if self.db is None:
                raise ValueError("Cannot delete session without database connection")

            session = self.get_session(session_id)
            self.db.delete(session)
            self.db.commit()
            self.logger.info(f"Session deleted: {session_id}")

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {str(e)}")
            if self.db is not None:
                self.db.rollback()
            raise ValueError(f"Failed to delete session: {str(e)}")
