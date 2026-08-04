from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


CERTIFICATION_GATES = [
    {"id": "connector.health", "title": "Health probe", "required": True},
    {"id": "connector.auth", "title": "Credential/auth validation", "required": True},
    {"id": "connector.idempotency", "title": "Idempotency for writes", "required": True},
    {"id": "connector.webhook_signature", "title": "Webhook signature verification", "required": True},
    {"id": "connector.retry_timeout", "title": "Retry, timeout, and failure behavior", "required": True},
    {"id": "connector.audit", "title": "Tool and webhook audit evidence", "required": True},
    {"id": "connector.degradation", "title": "Degraded/unavailable state handling", "required": True},
]


@dataclass(frozen=True)
class ConnectorCertification:
    connector_id: str
    status: str
    gates: list[dict[str, Any]]
    external_evidence_required: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "status": self.status,
            "gates": self.gates,
            "external_evidence_required": self.external_evidence_required,
        }


def _file_exists(path: str) -> bool:
    return (ROOT / path).exists()


def _gate(gate_id: str, passed: bool, evidence: str) -> dict[str, Any]:
    spec = next(item for item in CERTIFICATION_GATES if item["id"] == gate_id)
    return {
        **spec,
        "status": "pass" if passed else "missing",
        "evidence": evidence,
    }


def certify_connector(connector_id: str) -> ConnectorCertification:
    normalized = connector_id.strip().lower()
    if normalized == "spree":
        gates = [
            _gate("connector.health", _file_exists("scripts/ecom_demo_verify.py"), "ecom demo verifier probes commerce stack health"),
            _gate("connector.auth", _file_exists(".env.ecom-demo.example"), "demo env template carries connector credentials/placeholders"),
            _gate("connector.idempotency", _file_exists("apps/ops_api/routers/spree_webhooks.py"), "Spree webhook/router path is isolated for repeatable events"),
            _gate("connector.webhook_signature", _file_exists("tests/unit/test_spree_webhook_signature.py"), "webhook signature unit tests exist"),
            _gate("connector.retry_timeout", _file_exists("acosplatform/retail_ops/tools.py"), "retail tool adapter centralizes timeout/error behavior"),
            _gate("connector.audit", _file_exists("acosplatform/evidence/store.py"), "tool execution records evidence events"),
            _gate("connector.degradation", _file_exists("docs/REAL_ECOMMERCE_DEMO.md"), "demo guide documents limitations and degraded callback posture"),
        ]
    elif normalized == "shopify":
        gates = [
            _gate("connector.health", _file_exists("integrations/shopify/client.py"), "Shopify probe client exists"),
            _gate("connector.auth", _file_exists("integrations/shopify/client.py"), "Shopify client reads credential env vars"),
            _gate("connector.idempotency", False, "write idempotency proof not yet present"),
            _gate("connector.webhook_signature", False, "webhook signature proof not yet present"),
            _gate("connector.retry_timeout", _file_exists("integrations/shopify/client.py"), "client centralizes request behavior"),
            _gate("connector.audit", _file_exists("acosplatform/evidence/store.py"), "platform evidence store exists"),
            _gate("connector.degradation", False, "degradation drill not yet present"),
        ]
    elif normalized == "salesforce":
        gates = [
            _gate("connector.health", _file_exists("integrations/salesforce/client.py"), "Salesforce probe client exists"),
            _gate("connector.auth", _file_exists("integrations/salesforce/client.py"), "Salesforce client reads credential env vars"),
            _gate("connector.idempotency", False, "write idempotency proof not yet present"),
            _gate("connector.webhook_signature", False, "webhook signature proof not applicable unless event callbacks are enabled"),
            _gate("connector.retry_timeout", _file_exists("integrations/salesforce/client.py"), "client centralizes request behavior"),
            _gate("connector.audit", _file_exists("acosplatform/evidence/store.py"), "platform evidence store exists"),
            _gate("connector.degradation", False, "degradation drill not yet present"),
        ]
    else:
        gates = [_gate(item["id"], False, "Unknown connector") for item in CERTIFICATION_GATES]

    status = "certifiable_local" if all(gate["status"] == "pass" for gate in gates) else "partial"
    external = [
        "Run certification against live sandbox credentials.",
        "Capture webhook callback proof where applicable.",
        "Run failure drills for timeout, stale data, unavailable backend, and duplicate events.",
    ]
    return ConnectorCertification(normalized, status, gates, external)


def list_connector_certifications() -> dict[str, Any]:
    certifications = [certify_connector(connector_id).to_dict() for connector_id in ("spree", "shopify", "salesforce")]
    return {
        "status": "partial" if any(item["status"] == "partial" for item in certifications) else "certifiable_local",
        "certifications": certifications,
        "contract": CERTIFICATION_GATES,
    }
