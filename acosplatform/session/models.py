# acosplatform/session/models.py
"""
Data models for session store.

Defines ChatSession, ChatMessage, MessageRole, and SessionStatus
for multi-turn conversation management.
"""

from enum import Enum
from datetime import datetime, UTC
from typing import Optional, Any, Dict, List
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    """Message role types in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    """Session lifecycle states."""

    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ChatMessage(BaseModel):
    """
    A single message in a conversation.

    Attributes:
        role: Who sent the message (user, assistant, or system)
        content: The message text content
        timestamp: When the message was created
    """

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(use_enum_values=False)


class ChatSession(BaseModel):
    """
    A session for managing multi-turn conversations.

    Attributes:
        id: Unique session identifier (format: sess_<uuid>)
        user_id: The user associated with this session
        status: Current session state (active, closed, or archived)
        messages: List of messages in conversation history
        context: Dictionary of user context (preferences, cart, etc)
        created_at: When the session was created
        closed_at: When the session was closed (optional)
        archived_at: When the session was archived (optional)
    """

    id: str = Field(default_factory=lambda: f"sess_{uuid4()}")
    user_id: str
    status: SessionStatus = SessionStatus.ACTIVE
    messages: List[ChatMessage] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    closed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=False)
