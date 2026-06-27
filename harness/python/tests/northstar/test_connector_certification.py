from fastapi.testclient import TestClient

from apps.ops_api.main import app
from acosplatform.connectors.certification import certify_connector


def test_spree_connector_has_local_certification_evidence():
    certification = certify_connector("spree").to_dict()
    assert certification["status"] == "partial"
    assert any(gate["status"] == "pass" for gate in certification["gates"])
    assert certification["external_evidence_required"]


def test_connector_certification_endpoint_lists_partial_live_connectors():
    client = TestClient(app)
    response = client.get("/api/northstar/connector-certifications")
    assert response.status_code == 200
    payload = response.json()
    by_id = {item["connector_id"]: item for item in payload["certifications"]}
    assert by_id["spree"]["status"] == "partial"
    assert by_id["shopify"]["status"] == "partial"
    assert by_id["salesforce"]["status"] == "partial"
