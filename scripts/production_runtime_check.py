"""Production-runtime static/smoke checker for ACOS.

This script intentionally avoids requiring Docker so it can run in constrained CI
sandboxes, while still verifying that production runtime assets are present and
that the north-star runtime can execute a golden journey.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.orchestration.runtime import run_omnichannel_turn
from acosplatform.tools.registry import list_tools

REQUIRED_FILES = [
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "Dockerfile",
    "Dockerfile.chat_api",
    ".env.production.example",
    "db/schema.sql",
    "db/northstar_schema.sql",
    "alembic.ini",
    "migrations/env.py",
    "migrations/versions/20260511_0001_northstar_runtime_rbac.py",
    "docs/deployment/PRODUCTION_RUNTIME_GUIDE.md",
]

REQUIRED_TOOLS = {
    "catalog.search",
    "inventory.check_stock",
    "pricing.calculate",
    "promotions.find_offers",
    "case.create",
}


def main() -> int:
    missing = [item for item in REQUIRED_FILES if not (ROOT / item).exists()]
    tool_names = {item["name"] for item in list_tools()}
    missing_tools = sorted(REQUIRED_TOOLS - tool_names)
    result = run_omnichannel_turn(
        MessageEnvelope(
            tenant_id="runtime-check",
            channel="web",
            channel_user_id="runtime-user",
            customer_id="runtime-customer",
            text="I need an outfit for a winter wedding under £200, available for pickup near Reading",
        )
    )
    report = {
        "status": "pass" if not missing and not missing_tools and result.get("status") == "success" else "fail",
        "missing_files": missing,
        "missing_tools": missing_tools,
        "golden_journey_status": result.get("status"),
        "participating_agents": [a.get("id") for a in result.get("participating_agents", [])],
        "tool_count": len(result.get("tool_trace", [])),
        "evidence_count": len(result.get("evidence", [])),
        "alembic_migration_present": (ROOT / "migrations" / "versions" / "20260511_0001_northstar_runtime_rbac.py").exists(),
        "redis_fast_path_configurable": "ACOS_REDIS_ENABLED" in (ROOT / ".env.production.example").read_text(encoding="utf-8"),
        "docker_available": os.system("docker --version >/dev/null 2>&1") == 0,
        "note": "Docker runtime is only certified when this script is paired with docker compose up in a Docker-enabled runner.",
    }
    out = ROOT / "docs" / "release" / "production-runtime-check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
