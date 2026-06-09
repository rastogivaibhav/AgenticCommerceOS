from __future__ import annotations

from typing import Any


PILOT_KPIS = [
    {"id": "conversion.assisted_journey", "title": "Assisted journey conversion", "unit": "rate"},
    {"id": "support.deflection", "title": "Support deflection", "unit": "rate"},
    {"id": "ops.handling_time", "title": "Average handling time reduction", "unit": "minutes"},
    {"id": "automation.success_rate", "title": "Successful automation rate", "unit": "rate"},
    {"id": "automation.fallback_rate", "title": "Fallback/handoff rate", "unit": "rate"},
    {"id": "cost.per_successful_journey", "title": "Cost per successful journey", "unit": "currency"},
    {"id": "approval.rate", "title": "Human approval rate", "unit": "rate"},
]


def summarize_runs_for_outcomes(runs: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(runs)
    successful = len([run for run in runs if run.get("status") == "success"])
    with_handoff = len([run for run in runs if int(run.get("handoff_count") or 0) > 0])
    tool_calls = sum(int(run.get("tool_count") or 0) for run in runs)
    evidence_events = sum(int(run.get("evidence_count") or 0) for run in runs)
    failed_tools = sum(int(run.get("failed_tool_count") or 0) for run in runs)

    return {
        "pilot_kpis": PILOT_KPIS,
        "sample_size": total,
        "metrics": {
            "successful_automation_rate": round(successful / total, 4) if total else None,
            "fallback_or_handoff_rate": round(with_handoff / total, 4) if total else None,
            "average_tool_calls_per_run": round(tool_calls / total, 2) if total else None,
            "average_evidence_events_per_run": round(evidence_events / total, 2) if total else None,
            "failed_tool_rate": round(failed_tools / tool_calls, 4) if tool_calls else None,
        },
        "measurement_contract": [
            "Attach order/cart/support identifiers to successful journeys.",
            "Join ACOS run IDs to conversion, support, and fulfilment source systems.",
            "Report cost per successful journey from model, connector, and infrastructure usage.",
            "Compare pilot cohorts against a non-ACOS baseline.",
        ],
        "status": "needs_live_pilot_data" if total == 0 else "pilot_sample_available",
    }
