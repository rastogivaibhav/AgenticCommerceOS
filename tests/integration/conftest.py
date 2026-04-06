import pytest
from fastapi.testclient import TestClient
from apps.ops_api.main import app


@pytest.fixture
def client():
    """Test client for UAT integration tests."""
    return TestClient(app)
