"""Message router for chat operations with full pipeline integration."""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from apps.chat_api.models.chat import (
    ChatThreadRequest,
    ChatThreadResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    AsyncMessageResponse,
)
from apps.chat_api.adapters.slack import SlackAdapter
from apps.chat_api.security import require_chat_token, verify_slack_signature
from apps.chat_api.handlers.router import HandlerRouter
from acosplatform.session.store import SessionStore
from acosplatform.job_queue.service import JobQueueService
from datetime import datetime

router = APIRouter(tags=["messages"])

logger = logging.getLogger(__name__)

# Initialize services
_session_store = None
_job_queue_service = None
_handler_router = None
_slack_adapter = None


def get_session_store() -> SessionStore:
    """Get or initialize SessionStore."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store


def get_job_queue_service() -> JobQueueService:
    """Get or initialize JobQueueService."""
    global _job_queue_service
    if _job_queue_service is None:
        _job_queue_service = JobQueueService()
    return _job_queue_service


def get_handler_router() -> HandlerRouter:
    """Get or initialize HandlerRouter."""
    global _handler_router
    if _handler_router is None:
        session_store = get_session_store()
        job_queue_service = get_job_queue_service()
        _handler_router = HandlerRouter(
            session_store=session_store,
            job_queue_service=job_queue_service,
        )
    return _handler_router


def get_slack_adapter():
    """Get or initialize SlackAdapter."""
    global _slack_adapter
    if _slack_adapter is None:
        # In production, this would use a real Slack client
        from apps.chat_api.config import config

        try:
            from slack_bolt import App

            if config.slack.is_configured():
                slack_app = App(
                    token=config.slack.bot_token,
                    signing_secret=config.slack.signing_secret,
                )
                _slack_adapter = SlackAdapter(slack_client=slack_app.client)
            else:
                # Create mock adapter for testing
                _slack_adapter = SlackAdapter(slack_client=None)
        except ImportError:
            # slack_bolt not available, create mock adapter
            logger.debug("slack_bolt not available, using mock adapter")
            _slack_adapter = SlackAdapter(slack_client=None)

    return _slack_adapter


@router.post("/api/chat/message")
async def process_message(payload: ChatMessageRequest, request: Request):
    """Process a chat message through the full execution pipeline.

    Flow:
    1. Validate source (currently only "slack" supported)
    2. Normalize message using SlackAdapter
    3. Get or create session using SessionStore
    4. Route to appropriate handler using HandlerRouter
    5. Return response based on handler result

    Request body:
    {
        "source": "slack",
        "event": { /* Slack event JSON */ },
        "user_id": "U12345",
        "channel_id": "C12345",
        "timestamp": "1234567890.123456"
    }

    Response (sync):
    {
        "status": "success",
        "result": "Your balance is £1,250",
        "execution_time_ms": 245,
        "request_id": "req-..."
    }

    Response (async):
    {
        "status": "queued",
        "job_id": "job-abc123",
        "polling_endpoint": "/api/jobs/job-abc123/status"
    }
    """
    request_id = f"req-{str(uuid.uuid4())[:8]}"

    try:
        logger.info(
            f"Processing message from {payload.user_id} in {payload.channel_id}",
            extra={
                "request_id": request_id,
                "user_id": payload.user_id,
                "channel_id": payload.channel_id,
                "source": payload.source,
            },
        )

        # Step 1: Validate source
        if payload.source != "slack":
            logger.error(
                f"Invalid source: {payload.source}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported message source: {payload.source}. Currently only 'slack' is supported.",
            )

        # Step 2: Validate Slack request signature before processing the event.
        verify_slack_signature(request=request, raw_body=await request.body())

        # Step 3: Normalize message using SlackAdapter
        try:
            adapter = get_slack_adapter()
            normalized_message = adapter.normalize_event(payload.event)
        except ValueError as e:
            logger.error(
                f"Failed to normalize Slack event: {str(e)}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Slack event: {str(e)}",
            )

        # Step 4: Get or create session
        session_store = get_session_store()
        session_id = f"{payload.user_id}:{payload.channel_id}"

        session = session_store.get_session(session_id)
        if session is None:
            # Create new session with the spec-compliant session_id format
            # SessionStore will use this as the key
            session = session_store.create_session(
                session_id=session_id,
                user_id=payload.user_id,
                initial_context={
                    "channel_id": payload.channel_id,
                    "tenant_id": "default",
                },
            )

            logger.debug(
                f"Created new session {session_id} for user {payload.user_id}",
                extra={"request_id": request_id, "session_id": session_id},
            )
        else:
            logger.debug(
                f"Using existing session {session_id}",
                extra={"request_id": request_id, "session_id": session_id},
            )

        # Step 5: Route to appropriate handler
        router_instance = get_handler_router()
        handler_result = router_instance.route(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Step 6: Return response based on handler result
        if handler_result.get("status") == "success":
            logger.info(
                f"Sync execution completed",
                extra={
                    "request_id": request_id,
                    "session_id": session_id,
                    "execution_time_ms": handler_result.get("execution_time_ms"),
                },
            )

            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ChatMessageResponse(
                    status="success",
                    result=handler_result.get("result"),
                    execution_time_ms=handler_result.get("execution_time_ms"),
                    request_id=request_id,
                    workflow_id=handler_result.get("workflow_id"),
                ).model_dump(),
            )

        elif handler_result.get("status") == "queued":
            logger.info(
                f"Async job queued",
                extra={
                    "request_id": request_id,
                    "session_id": session_id,
                    "job_id": handler_result.get("job_id"),
                },
            )

            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=AsyncMessageResponse(
                    status="queued",
                    job_id=handler_result.get("job_id"),
                    polling_endpoint=handler_result.get("polling_endpoint"),
                    result_endpoint=handler_result.get("result_endpoint"),
                    request_id=request_id,
                    workflow_id=handler_result.get("workflow_id"),
                ).model_dump(),
            )

        elif handler_result.get("status") == "failed":
            logger.error(
                f"Handler execution failed: {handler_result.get('error')}",
                extra={
                    "request_id": request_id,
                    "session_id": session_id,
                    "error": handler_result.get("error"),
                },
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=handler_result.get("error", "Execution failed"),
            )

        else:
            logger.error(
                f"Unknown handler status: {handler_result.get('status')}",
                extra={"request_id": request_id},
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unknown handler response",
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error processing message: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/api/messages/send", response_model=ChatThreadResponse, dependencies=[Depends(require_chat_token)])
def send_message(
    payload: ChatThreadRequest,
) -> ChatThreadResponse:
    """Send a message or reply to a thread.

    Stub implementation for backwards compatibility.
    """
    return ChatThreadResponse(
        status="success",
        message_id="msg_stub_" + payload.channel_id,
        thread_ts=payload.thread_ts or "1234567890.000001",
        timestamp=datetime.now(),
    )


@router.get("/api/messages/{message_id}", dependencies=[Depends(require_chat_token)])
def get_message(message_id: str):
    """Retrieve a specific message.

    Stub implementation for backwards compatibility.
    """
    return {"status": "success", "message": {"id": message_id, "text": "Stub message"}}
