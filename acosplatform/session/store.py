# acosplatform/session/store.py
"""
Session store for managing multi-turn conversation state.

Provides Redis-backed session storage with 24-hour TTL for managing
conversation history, user context, and session lifecycle.
"""

import json
import logging
from datetime import datetime, UTC
from typing import Optional, Any, Dict, List

import redis

from .models import ChatSession, ChatMessage, MessageRole, SessionStatus

logger = logging.getLogger(__name__)


class SessionStore:
    """
    Store for managing chat sessions.

    Uses Redis for fast access and caching, with 24-hour TTL.
    Handles session creation, message management, context storage,
    and session lifecycle (active -> closed -> archived).
    """

    # Session TTL in seconds (24 hours)
    SESSION_TTL = 86400

    # Redis key prefixes
    SESSION_PREFIX = "session:"
    MESSAGES_PREFIX = "session_messages:"

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize SessionStore.

        Args:
            redis_client: Redis client instance. If None, creates a new connection
                         to localhost:6379/0
        """
        if redis_client is None:
            self.redis = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
            )
        else:
            self.redis = redis_client

    def create_session(
        self,
        user_id: str,
        initial_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> ChatSession:
        """
        Create a new session for a user.

        Args:
            user_id: The user identifier
            initial_context: Optional initial context data for the session
            session_id: Optional session identifier. If provided, will be used instead of auto-generated ID.
                       Expected format: "user_id:channel_id"

        Returns:
            Created ChatSession object in ACTIVE status
        """
        # If session_id is provided, use it; otherwise create a new one with auto-generated ID
        if session_id:
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                status=SessionStatus.ACTIVE,
                context=initial_context or {},
            )
        else:
            session = ChatSession(
                user_id=user_id,
                status=SessionStatus.ACTIVE,
                context=initial_context or {},
            )

        # Store session data in Redis
        session_key = f"{self.SESSION_PREFIX}{session.id}"
        session_json = session.model_dump_json()
        self.redis.setex(session_key, self.SESSION_TTL, session_json)

        logger.info(
            f"Created session {session.id} for user {user_id}",
            extra={"session_id": session.id, "user_id": user_id},
        )

        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Retrieve a session by ID.

        Args:
            session_id: The session identifier

        Returns:
            ChatSession object if found, None otherwise
        """
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_json = self.redis.get(session_key)

        if session_json is None:
            logger.debug(f"Session {session_id} not found")
            return None

        try:
            # Handle both bytes and str (for Redis vs fakeredis)
            if isinstance(session_json, bytes):
                session_json = session_json.decode("utf-8")
            session_data = json.loads(session_json)
            return ChatSession(**session_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to deserialize session {session_id}: {e}")
            return None

    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
    ) -> Optional[ChatMessage]:
        """
        Add a message to a session's conversation history.

        Args:
            session_id: The session identifier
            role: The message role (user, assistant, or system)
            content: The message content

        Returns:
            Created ChatMessage if successful, None if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            logger.warning(f"Cannot add message: session {session_id} not found")
            return None

        # Create message
        message = ChatMessage(role=role, content=content)

        # Add to session's messages
        session.messages.append(message)

        # Update session in Redis
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_json = session.model_dump_json()
        self.redis.setex(session_key, self.SESSION_TTL, session_json)

        logger.debug(
            f"Added {role.value} message to session {session_id}",
            extra={"session_id": session_id, "role": role.value},
        )

        return message

    def update_context(
        self,
        session_id: str,
        context_data: Dict[str, Any],
    ) -> bool:
        """
        Update the user context for a session.

        Context data is merged with existing context (updates, doesn't replace).

        Args:
            session_id: The session identifier
            context_data: Context data to merge into the session

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            logger.warning(f"Cannot update context: session {session_id} not found")
            return False

        # Merge context (new data overrides existing)
        session.context.update(context_data)

        # Update session in Redis
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_json = session.model_dump_json()
        self.redis.setex(session_key, self.SESSION_TTL, session_json)

        logger.debug(
            f"Updated context for session {session_id}",
            extra={"session_id": session_id},
        )

        return True

    def close_session(self, session_id: str) -> bool:
        """
        Close a session (transition from ACTIVE to CLOSED).

        Args:
            session_id: The session identifier

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            logger.warning(f"Cannot close session: session {session_id} not found")
            return False

        session.status = SessionStatus.CLOSED
        session.closed_at = datetime.now(UTC)

        # Update session in Redis
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_json = session.model_dump_json()
        self.redis.setex(session_key, self.SESSION_TTL, session_json)

        logger.info(
            f"Closed session {session_id}",
            extra={"session_id": session_id},
        )

        return True

    def archive_session(self, session_id: str) -> bool:
        """
        Archive a session (transition from CLOSED to ARCHIVED).

        Args:
            session_id: The session identifier

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            logger.warning(f"Cannot archive session: session {session_id} not found")
            return False

        session.status = SessionStatus.ARCHIVED
        session.archived_at = datetime.now(UTC)

        # Update session in Redis
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_json = session.model_dump_json()
        self.redis.setex(session_key, self.SESSION_TTL, session_json)

        logger.info(
            f"Archived session {session_id}",
            extra={"session_id": session_id},
        )

        return True

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """
        Retrieve all messages for a session.

        Args:
            session_id: The session identifier

        Returns:
            List of ChatMessage objects, empty list if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            logger.debug(f"Session {session_id} not found, returning empty messages")
            return []

        return session.messages
