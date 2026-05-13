from fastapi.testclient import TestClient

from apps.ops_api.main import app


client = TestClient(app)
OPS_AUTH = {"Authorization": "Bearer dev-token"}


def test_metrics_header_marks_fallback(monkeypatch):
    monkeypatch.setattr("apps.ops_api.routers.analytics.is_pool_available", lambda: False)

    response = client.get("/api/analytics/metrics", headers=OPS_AUTH)

    assert response.status_code == 200
    assert response.headers["X-ACOS-Analytics-Provenance"] == "fallback"
    assert response.headers["X-ACOS-Analytics-Detail"] == "db_pool_unavailable"


def test_workflow_header_marks_live(monkeypatch):
    class _Cursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query):
            self.query = query

        def fetchall(self):
            return [{"name": "service", "runs": 3, "score": 8.5, "cost": 12.25}]

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return _Cursor()

    monkeypatch.setattr("apps.ops_api.routers.analytics.is_pool_available", lambda: True)
    monkeypatch.setattr("apps.ops_api.routers.analytics.transaction", lambda: _Conn())

    response = client.get("/api/analytics/workflows", headers=OPS_AUTH)

    assert response.status_code == 200
    assert response.headers["X-ACOS-Analytics-Provenance"] == "live"
    assert response.headers["X-ACOS-Analytics-Detail"] == "db_query"
    assert response.json()[0]["name"] == "service"
