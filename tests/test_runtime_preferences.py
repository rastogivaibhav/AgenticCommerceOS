from fastapi.testclient import TestClient

from apps.ops_api.main import app


client = TestClient(app)
OPS_AUTH = {"Authorization": "Bearer dev-token"}


def test_ops_context_exposes_runtime_controls():
    response = client.get("/api/v1/ops/context", headers=OPS_AUTH)

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "normal"
    assert payload["data_mode"] in {"live", "demo"}
    assert "normal" in payload["mode_options"]
    assert "demo" in payload["mode_options"]
    assert "auto" in payload["runtime_preference_options"]
    assert "local_openai_host" in payload["runtime_preference_options"]
    assert "local_openai_docker" in payload["runtime_preference_options"]


def test_runtime_preferences_accept_docker_local_llm():
    original = client.get("/api/v1/ops/context", headers=OPS_AUTH).json()

    try:
        response = client.patch(
            "/api/v1/runtime/preferences",
            json={
                "platform_mode": "demo",
                "runtime_preference": "local_openai_docker",
            },
            headers=OPS_AUTH,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["context"]["mode"] == "demo"
        assert payload["context"]["runtime_preference"] == "local_openai_docker"
        assert payload["runtime"]["runtime_preference"] == "local_openai_docker"
        assert "local_openai_docker" in payload["runtime"]["providers"]["supported_providers"]
    finally:
        client.patch(
            "/api/v1/runtime/preferences",
            json={
                "platform_mode": original.get("mode", "normal"),
                "runtime_preference": original.get("runtime_preference", "auto"),
            },
            headers=OPS_AUTH,
        )
