"""Chat message models."""

from pydantic import BaseModel
from typing import Optional, Any, Dict
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


class ChatMessageRequest(BaseModel):
    """Request to process a chat message through the pipeline."""

    source: str  # e.g., "slack"
    event: Dict[str, Any]  # Platform-specific event data
    user_id: str  # User identifier
    channel_id: str  # Channel identifier
    timestamp: str  # Event timestamp


class ChatMessageResponse(BaseModel):
    """Response from message processing (sync)."""

    status: str  # "success" or "failed"
    result: Optional[str] = None  # Execution result for sync
    execution_time_ms: Optional[int] = None  # Time taken in milliseconds
    request_id: str  # Request tracking ID
    workflow_id: Optional[str] = None  # Workflow that was executed


class AsyncMessageResponse(BaseModel):
    """Response from message processing (async)."""

    status: str  # "queued" or "failed"
    job_id: Optional[str] = None  # Job identifier for polling
    polling_endpoint: Optional[str] = None  # Where to poll status
    result_endpoint: Optional[str] = None  # Where to get final result
    request_id: str  # Request tracking ID
    workflow_id: Optional[str] = None  # Workflow that was enqueued
