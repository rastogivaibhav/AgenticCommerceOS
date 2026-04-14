"""Security tests for chat-api auth and Slack signature validation."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.chat_api.main import app
from apps.chat_api.models.chat import ChatMessage


def _sign_slack(secret: str, timestamp: str, body: bytes) -> str:
    base = f"v0:{timestamp}:".encode("utf-8") + body
    digest = hmac.new(secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_workflow_execute_message_requires_bearer():
    client = TestClient(app)
    payload = {
        "message_text": "where is my order ORD-1001",
        "user_id": "U12345",
        "channel_id": "C12345",
        "session_id": "sess-123",
    }
    response = client.post("/api/workflows/execute-message", json=payload)
    assert response.status_code in (401, 403)


def test_workflow_execute_message_accepts_dev_bearer_without_secret(monkeypatch):
    monkeypatch.setenv("OPS_ENVIRONMENT", "dev")
    monkeypatch.delenv("CHAT_JWT_SECRET", raising=False)
    monkeypatch.delenv("OPS_JWT_SECRET", raising=False)

    client = TestClient(app)
    payload = {
        "message_text": "where is my order ORD-1001",
        "user_id": "U12345",
        "channel_id": "C12345",
        "session_id": "sess-123",
    }
    with patch("apps.chat_api.routers.workflows._handler_router.route") as mock_route:
        mock_route.return_value = {"status": "success", "result": "ok", "execution_time_ms": 1}
        response = client.post(
            "/api/workflows/execute-message",
            json=payload,
            headers={"Authorization": "Bearer dev-token"},
        )
    assert response.status_code == 200


def test_chat_message_rejects_missing_slack_signature_when_secret_set(monkeypatch):
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "unit-secret")

    client = TestClient(app)
    payload = {
        "source": "slack",
        "event": {
            "type": "message",
            "user": "U12345",
            "channel": "C12345",
            "text": "hello",
            "ts": "1234567890.123456",
        },
        "user_id": "U12345",
        "channel_id": "C12345",
        "timestamp": "1234567890.123456",
    }

    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 401


def test_chat_message_accepts_valid_slack_signature(monkeypatch):
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "unit-secret")

    payload = {
        "source": "slack",
        "event": {
            "type": "message",
            "user": "U12345",
            "channel": "C12345",
            "text": "hello",
            "ts": "1234567890.123456",
        },
        "user_id": "U12345",
        "channel_id": "C12345",
        "timestamp": "1234567890.123456",
    }
    raw_body = json.dumps(payload).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = _sign_slack("unit-secret", timestamp, raw_body)
    headers = {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
    }

    client = TestClient(app)

    with patch("apps.chat_api.routers.message.get_session_store") as mock_store_factory:
        with patch("apps.chat_api.routers.message.get_slack_adapter") as mock_adapter_factory:
            with patch("apps.chat_api.routers.message.get_handler_router") as mock_router_factory:
                mock_store = MagicMock()
                mock_store.get_session.return_value = None
                mock_store.create_session.return_value = MagicMock(id="sess-123")
                mock_store_factory.return_value = mock_store

                mock_adapter = MagicMock()
                mock_adapter.normalize_event.return_value = ChatMessage(
                    id="msg-123",
                    channel_id="C12345",
                    user_id="U12345",
                    text="hello",
                    timestamp=datetime.now(timezone.utc),
                )
                mock_adapter_factory.return_value = mock_adapter

                mock_router = MagicMock()
                mock_router.route.return_value = {
                    "status": "success",
                    "result": "ok",
                    "execution_time_ms": 10,
                    "workflow_id": "wf_test",
                }
                mock_router_factory.return_value = mock_router

                response = client.post("/api/chat/message", content=raw_body, headers=headers)

    assert response.status_code == 200
