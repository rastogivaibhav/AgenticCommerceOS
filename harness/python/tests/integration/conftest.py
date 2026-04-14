import pytest
from fastapi.testclient import TestClient
from apps.ops_api.main import app
from acosplatform.auth.api_key import require_ops_token


@pytest.fixture
def client():
    """Test client for UAT integration tests."""
    app.dependency_overrides[require_ops_token] = lambda: {
        "sub": "uat-integration-user",
        "role": "admin",
        "roles": ["admin", "editor", "viewer", "analyst", "ops"],
    }
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
