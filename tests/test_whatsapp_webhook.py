from fastapi.testclient import TestClient

from apps.ops_api.main import app


client = TestClient(app)
OPS_AUTH = {"Authorization": "Bearer dev-token"}


def test_whatsapp_webhook_verifies_against_binding_metadata(monkeypatch):
    monkeypatch.setattr(
        "apps.ops_api.main.get_channel_bindings",
        lambda: [
            {
                "id": "whatsapp-eu",
                "type": "whatsapp",
                "metadata": {
                    "verify_token": "binding-token",
                    "access_token": "access-token",
                    "phone_number_id": "123456789",
                },
            }
        ],
    )

    response = client.get(
        "/api/v1/connectors/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "binding-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


def test_whatsapp_webhook_resolves_binding_and_parses_text(monkeypatch):
    captured = []

    monkeypatch.setattr(
        "apps.ops_api.main.get_channel_bindings",
        lambda: [
            {
                "id": "whatsapp-uk",
                "type": "whatsapp",
                "tenant_id": "tenant-uk",
                "environment": "prod",
                "metadata": {"phone_number_id": "222"},
            },
            {
                "id": "whatsapp-us",
                "type": "whatsapp",
                "tenant_id": "tenant-us",
                "environment": "staging",
                "metadata": {"phone_number_id": "999"},
            },
        ],
    )
    monkeypatch.setattr(
        "apps.ops_api.main.ingest_channel_message",
        lambda **kwargs: captured.append(kwargs) or {"status": "dispatched"},
    )
    monkeypatch.setattr("apps.ops_api.main.save_audit_event", lambda *args, **kwargs: None)

    response = client.post(
        "/api/v1/connectors/whatsapp/webhook",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {
                                    "phone_number_id": "999",
                                    "display_phone_number": "+1 555 000 1111",
                                },
                                "contacts": [
                                    {
                                        "wa_id": "447700900001",
                                        "profile": {"name": "Ava Morgan"},
                                    }
                                ],
                                "messages": [
                                    {
                                        "id": "wamid-1",
                                        "from": "447700900001",
                                        "type": "text",
                                        "text": {"body": "Where is my order ORD-1001?"},
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        },
    )

    assert response.status_code == 200
    assert captured == [
        {
            "channel_binding_id": "whatsapp-us",
            "sender_external_id": "whatsapp:+447700900001",
            "display_name": "Ava Morgan",
            "message": "Where is my order ORD-1001?",
            "tenant_id": "tenant-us",
            "environment": "staging",
        }
    ]
    processed = response.json()["processed"]
    assert processed[0]["binding_id"] == "whatsapp-us"
    assert processed[0]["tenant_id"] == "tenant-us"
    assert processed[0]["status"] == "dispatched"


def test_whatsapp_webhook_parses_interactive_reply(monkeypatch):
    captured = []

    monkeypatch.setattr(
        "apps.ops_api.main.get_channel_bindings",
        lambda: [
            {
                "id": "whatsapp-support",
                "type": "whatsapp",
                "tenant_id": "default",
                "environment": "dev",
                "metadata": {"phone_number_id": "123"},
            }
        ],
    )
    monkeypatch.setattr(
        "apps.ops_api.main.ingest_channel_message",
        lambda **kwargs: captured.append(kwargs) or {"status": "dispatched"},
    )
    monkeypatch.setattr("apps.ops_api.main.save_audit_event", lambda *args, **kwargs: None)

    response = client.post(
        "/api/v1/connectors/whatsapp/webhook",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "123"},
                                "contacts": [
                                    {
                                        "wa_id": "15551230000",
                                        "profile": {"name": "Sam Lee"},
                                    }
                                ],
                                "messages": [
                                    {
                                        "id": "wamid-2",
                                        "from": "15551230000",
                                        "type": "interactive",
                                        "interactive": {
                                            "button_reply": {
                                                "id": "route_return",
                                                "title": "Return item",
                                            }
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        },
    )

    assert response.status_code == 200
    assert captured[0]["message"] == "Return item | route_return"


def test_whatsapp_webhook_ignores_unsupported_message_without_text(monkeypatch):
    monkeypatch.setattr(
        "apps.ops_api.main.get_channel_bindings",
        lambda: [
            {
                "id": "whatsapp-support",
                "type": "whatsapp",
                "tenant_id": "default",
                "environment": "dev",
                "metadata": {"phone_number_id": "123"},
            }
        ],
    )
    monkeypatch.setattr("apps.ops_api.main.save_audit_event", lambda *args, **kwargs: None)

    response = client.post(
        "/api/v1/connectors/whatsapp/webhook",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "123"},
                                "messages": [
                                    {
                                        "id": "wamid-3",
                                        "from": "15551230000",
                                        "type": "image",
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ignored"] == 1
    assert body["processed"][0]["status"] == "ignored"
    assert body["processed"][0]["reason"] == "unsupported_or_empty_message"


def test_whatsapp_channel_test_uses_default_recipient(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "apps.ops_api.main.get_channel_binding",
        lambda binding_id: {
            "id": binding_id,
            "type": "whatsapp",
            "metadata": {
                "default_recipient": "+447700900999",
                "access_token": "token",
                "phone_number_id": "123",
                "verify_token": "verify",
            },
        },
    )
    monkeypatch.setattr(
        "apps.ops_api.main.execute_whatsapp_action",
        lambda action, payload, **kwargs: captured.update({"action": action, "payload": payload}) or {"mode": "live"},
    )

    response = client.post(
        "/api/v1/channels/whatsapp-support/test",
        headers=OPS_AUTH,
        json={"text": "ACOS channel test", "recipient": ""},
    )

    assert response.status_code == 200
    assert captured["action"] == "send_message"
    assert captured["payload"]["to"] == "+447700900999"
