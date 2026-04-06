"""Chat message models."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """A single chat message."""

    id: str
    channel_id: str
    user_id: str
    text: str
    timestamp: datetime
    thread_ts: Optional[str] = None
    reactions: Optional[list[str]] = None


class ChatThreadRequest(BaseModel):
    """Request to start or reply to a chat thread."""

    channel_id: str
    text: str
    thread_ts: Optional[str] = None
    user_id: Optional[str] = None


class ChatThreadResponse(BaseModel):
    """Response from chat thread operation."""

    status: str
    message_id: str
    thread_ts: str
    timestamp: datetime
