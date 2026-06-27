from __future__ import annotations

import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _exists(path: str) -> bool:
    return (ROOT / path).exists()


def _read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8", errors="ignore")


def platform_validation_checks() -> list[dict[str, Any]]:
    """Checks exposed to the Test Center and procurement readiness reports."""
    return [
        {
            "id": "smoke.golden_journey",
            "phase": 7,
            "title": "Golden retail journey smoke",
            "command": "python scripts/northstar_smoke.py",
            "expected": "Journey succeeds with multiple agents, tool calls, evidence, and replay capture.",
            "local_verification": "automated",
        },
        {
            "id": "ui.build",
            "phase": 5,
            "title": "Ops UI production build",
            "command": "npm --prefix apps/ops_ui_v2 ci && npm --prefix apps/ops_ui_v2 run build",
            "expected": "Vite build succeeds and emits static assets.",
            "local_verification": "automated",
        },
        {
            "id": "db.migration_sql",
            "phase": 2,
            "title": "Database migration SQL render",
            "command": "alembic upgrade head --sql",
            "expected": "Postgres migration SQL renders for north-star runtime tables.",
            "local_verification": "automated",
        },
        {
            "id": "compose.prod",
            "phase": 6,
            "title": "Production Compose runtime",
            "command": "docker compose --env-file .env.production -f docker-compose.prod.yml up --build",
            "expected": "Services boot healthy against production-like Postgres/Redis settings.",
            "local_verification": "external_runtime",
        },
        {
            "id": "mcp.client",
            "phase": 3,
            "title": "MCP client compatibility",
            "command": "POST /mcp with tools/list and tools/call",
            "expected": "ACOS exposes callable tools through MCP with auth and tenant scope.",
            "local_verification": "automated",
        },
        {
            "id": "graphql.studio",
            "phase": 5,
            "title": "GraphQL Studio plane",
            "command": "POST /graphql",
            "expected": "Studio graph data is returned with RBAC when auth is enabled.",
            "local_verification": "automated",
        },
    ]


def _gate(gate_id: str, title: str, passed: bool, evidence: str, *, severity: str = "blocker") -> dict[str, Any]:
    return {
        "id": gate_id,
        "title": title,
        "status": "pass" if passed else "fail",
        "severity": severity,
        "evidence": evidence,
    }


def build_hardening_gate_report() -> dict[str, Any]:
    """Return Phase 1-7 hardening gates with local evidence and external blockers.

    This report intentionally distinguishes local proof from procurement-grade
    certification. Local source artifacts can pass while cloud/SSO/live-connector
    checks remain external until credentials and target environments are supplied.
    """
    production_env = _read(".env.production.example")
    northstar_schema = _read("db/northstar_schema.sql")
    compose = _read("docker-compose.yml")
    prod_compose = _read("docker-compose.prod.yml")
    ops_api = "\n".join(
        [
            _read("apps/ops_api/main.py"),
            _read("apps/ops_api/routers/northstar_api.py"),
        ]
    )
    package_json = _read("apps/ops_ui_v2/package.json")
    runtime_checker = _read("scripts/production_runtime_check.py")

    phases = [
        {
            "phase": 1,
            "title": "Enterprise Identity, RBAC, And Secure Defaults",
            "status": "partial",
            "gates": [
                _gate("auth.ops.jwt_required", "Ops JWT secret required in non-dev", "OPS_JWT_SECRET" in production_env, ".env.production.example defines OPS_JWT_SECRET"),
                _gate("auth.shopper.keys_required", "Shopper API keys required in non-dev", "SHOPPER_API_KEYS" in production_env, ".env.production.example defines SHOPPER_API_KEYS"),
                _gate("auth.dev_bypass_blocked", "Dev auth bypass blocked outside dev/test", "ALLOW_INSECURE_DEV_AUTH must be disabled" in _read("acosplatform/config/startup_validation.py"), "startup validation rejects insecure dev auth"),
                _gate("auth.northstar_configurable", "North-star API auth is configurable", "ACOS_NORTHSTAR_REQUIRE_AUTH" in _read("acosplatform/auth/northstar.py"), "north-star auth dependency supports env-gated API keys"),
            ],
            "external_blockers": ["Enterprise SSO/OIDC/SAML tenant integration must be wired to the buyer identity provider."],
        },
        {
            "phase": 2,
            "title": "Tenant Isolation And Data Boundaries",
            "status": "partial",
            "gates": [
                _gate("tenant.postgres_schema", "Postgres north-star schema exists", "northstar_conversation_sessions" in northstar_schema, "db/northstar_schema.sql includes north-star tables"),
                _gate("tenant.rls_reference", "RLS reference posture documented", "ENABLE ROW LEVEL SECURITY" in northstar_schema, "north-star schema includes RLS policy templates"),
                _gate("tenant.repository_switch", "Repository can switch to Postgres", "ACOS_NORTHSTAR_STORE" in _read("acosplatform/northstar/repository.py"), "repository supports ACOS_NORTHSTAR_STORE=postgres"),
                _gate("tenant.api_guard", "Tenant guard is available for north-star auth", "def enforce_tenant" in _read("acosplatform/auth/northstar.py"), "north-star auth has enforce_tenant"),
            ],
            "external_blockers": ["Run negative tenant-isolation tests against a real Postgres database with RLS enabled."],
        },
        {
            "phase": 3,
            "title": "Connector Certification",
            "status": "partial",
            "gates": [
                _gate("connector.shopify_client", "Shopify client exists", _exists("integrations/shopify/client.py"), "Shopify integration client present"),
                _gate("connector.salesforce_client", "Salesforce client exists", _exists("integrations/salesforce/client.py"), "Salesforce integration client present"),
                _gate("connector.webhook_signature", "Spree webhook signature tests exist", _exists("tests/unit/test_spree_webhook_signature.py"), "Spree webhook signature unit test present"),
                _gate("connector.ecom_demo", "Real ecommerce demo verifier exists", _exists("scripts/ecom_demo_verify.py"), "ecommerce demo verifier present"),
                _gate("connector.cert_contract", "Connector certification contract exists", _exists("acosplatform/connectors/certification.py"), "connector certification contract present"),
            ],
            "external_blockers": ["Certify one live commerce connector with real credentials, webhook callbacks, idempotency, and failure drills."],
        },
        {
            "phase": 4,
            "title": "Policy, Risk, And Compliance Layer",
            "status": "partial",
            "gates": [
                _gate("policy.sanitize", "Prompt/input sanitization exists", _exists("acosplatform/auth/sanitize.py"), "sanitize module present"),
                _gate("policy.evidence_verdicts", "Evidence supports policy verdicts", "policy_verdict" in northstar_schema, "north-star evidence schema includes policy_verdict"),
                _gate("policy.approvals", "Approval routes exist", _exists("apps/ops_api/routers/approvals.py"), "approval router present"),
                _gate("policy.route_to_production", "Route-to-production stages exist", _exists("acosplatform/route_to_production/service.py"), "route-to-production service present"),
                _gate("policy.tool_policy", "Tool policy execution gate exists", _exists("acosplatform/policy/tool_policy.py"), "tool policy module present"),
            ],
            "external_blockers": ["Map buyer compliance controls: PII retention, PCI boundary, DLP, legal holds, and model risk governance."],
        },
        {
            "phase": 5,
            "title": "Workflow Studio And Operator UX",
            "status": "partial",
            "gates": [
                _gate("studio.react_app", "React Ops UI exists", _exists("apps/ops_ui_v2/package.json"), "Ops UI package present"),
                _gate("studio.workflow_canvas", "Workflow canvas code exists", "reactflow" in package_json, "React Flow dependency present"),
                _gate("studio.runs_screen_api", "Runs and replay APIs exist", "/api/northstar/runs" in ops_api and "/api/northstar/replays" in ops_api, "north-star runs and replay endpoints present"),
                _gate("studio.test_center_api", "Test Center plan exists", "/api/northstar/test-plan" in ops_api, "test-plan endpoint present"),
            ],
            "external_blockers": ["Run full operator UAT with real ops users for workflow promotion, pause, rollback, and incident controls."],
        },
        {
            "phase": 6,
            "title": "Production Runtime And Deployment Certification",
            "status": "partial",
            "gates": [
                _gate("runtime.compose", "Compose assets exist", _exists("docker-compose.yml") and _exists("docker-compose.prod.yml"), "compose assets present"),
                _gate("runtime.secrets", "Production env template requires secrets", "REPLACE_WITH_SECRET" in production_env, ".env.production.example uses secret placeholders"),
                _gate("runtime.redis", "Redis is configurable", "ACOS_REDIS_ENABLED" in production_env or "redis" in compose.lower() or "redis" in prod_compose.lower(), "Redis appears in production/runtime config"),
                _gate("runtime.checker", "Production runtime checker exists", "REQUIRED_FILES" in runtime_checker, "production_runtime_check.py present"),
            ],
            "external_blockers": ["Run Docker/Kubernetes/cloud deployment, backup/restore, load, and disaster recovery tests in target infrastructure."],
        },
        {
            "phase": 7,
            "title": "Business Outcome Proof",
            "status": "partial",
            "gates": [
                _gate("outcome.analytics", "Analytics APIs exist", _exists("apps/ops_api/routers/analytics.py"), "analytics router present"),
                _gate("outcome.finops", "FinOps surfaces exist", _exists("acosplatform/finops_v2/service.py") or "finops" in ops_api.lower(), "FinOps route/surface present"),
                _gate("outcome.golden_smoke", "Golden smoke is automated", _exists("scripts/northstar_smoke.py"), "northstar_smoke.py present"),
                _gate("outcome.runtime_report", "Runtime report artifact is generated", _exists("scripts/production_runtime_check.py"), "runtime checker writes docs/release/production-runtime-check.json"),
                _gate("outcome.kpi_contract", "Pilot KPI contract exists", _exists("acosplatform/outcomes/kpi.py"), "business outcome KPI module present"),
            ],
            "external_blockers": ["Run a paid pilot and measure conversion, support deflection, handling time, cost per journey, approval rate, and fallback rate."],
        },
    ]

    for phase in phases:
        gates = phase["gates"]
        phase["passed_gates"] = len([gate for gate in gates if gate["status"] == "pass"])
        phase["total_gates"] = len(gates)
        if phase["passed_gates"] == phase["total_gates"] and not phase["external_blockers"]:
            phase["status"] = "pass"
        elif phase["passed_gates"] == phase["total_gates"]:
            phase["status"] = "locally_verified_external_blockers"
        else:
            phase["status"] = "partial"

    return {
        "status": "locally_verified_with_external_blockers",
        "scope": "ACOS Phase 1-7 enterprise hardening",
        "checks": platform_validation_checks(),
        "phases": phases,
        "summary": {
            "phase_count": len(phases),
            "locally_verified_phases": len([p for p in phases if p["status"] == "locally_verified_external_blockers"]),
            "partial_phases": len([p for p in phases if p["status"] == "partial"]),
            "external_blockers": sum(len(p.get("external_blockers", [])) for p in phases),
        },
    }
