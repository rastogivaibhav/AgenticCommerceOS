"""Message router stub for chat operations."""

from fastapi import APIRouter, Depends, HTTPException
from apps.chat_api.models.chat import ChatThreadRequest, ChatThreadResponse
from datetime import datetime

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("/send", response_model=ChatThreadResponse)
def send_message(
    payload: ChatThreadRequest,
) -> ChatThreadResponse:
    """Send a message or reply to a thread.

    Stub implementation.
    """
    return ChatThreadResponse(
        status="success",
        message_id="msg_stub_" + payload.channel_id,
        thread_ts=payload.thread_ts or "1234567890.000001",
        timestamp=datetime.now(),
    )


@router.get("/{message_id}")
def get_message(message_id: str):
    """Retrieve a specific message.

    Stub implementation.
    """
    return {"status": "success", "message": {"id": message_id, "text": "Stub message"}}
