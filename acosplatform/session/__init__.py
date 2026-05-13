"""
Session module for managing multi-turn conversations.

Provides Redis-backed session storage with conversation history,
user context management, and session lifecycle handling.
"""

from .models import ChatSession, ChatMessage, MessageRole, SessionStatus
from .store import SessionStore

__all__ = [
    "ChatSession",
    "ChatMessage",
    "MessageRole",
    "SessionStatus",
    "SessionStore",
]
