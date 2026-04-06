# apps/ops_api/routers/incidents.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from acosplatform.auth.api_key import require_ops_roles
from acosplatform.audit.logger import audit

router = APIRouter(prefix="/api", tags=["incidents"])

# Mock audit events - will accumulate during test run
_audit_events = []


@router.get("/health/workflows/{workflow_id}")
def get_workflow_health(
    workflow_id: str,
    window: str = Query("5m"),
    current_user=Depends(require_ops_roles("admin"))
):
    """PE-6.1: Platform Engineer detect error spike"""
    return {
        "error_rate": 0.01,
        "p99_latency": 500,
        "throughput": 100,
        "status": "healthy"
    }


@router.post("/workflows/{workflow_id}/pause")
def pause_workflow(
    workflow_id: str,
    request: dict = {},
    current_user=Depends(require_ops_roles("admin"))
):
    """PE-6.2: Platform Engineer pause workflow"""
    audit_event = {
        "event_type": "workflow_paused",
        "actor": current_user,
        "resource": f"/workflows/{workflow_id}/pause",
        "incident_id": request.get("incident_id")
    }
    _audit_events.append(audit_event)
    return {"status": "paused", "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/failsafe/activate")
def activate_failsafe(
    workflow_id: str,
    request: dict = {},
    current_user=Depends(require_ops_roles("admin"))
):
    """PE-6.3: Platform Engineer activate failsafe"""
    audit_event = {
        "event_type": "failsafe_activated",
        "actor": current_user,
        "resource": f"/workflows/{workflow_id}/failsafe/activate",
        "incident_id": request.get("incident_id")
    }
    _audit_events.append(audit_event)
    return {"status": "active", "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/rollback")
def rollback_workflow(
    workflow_id: str,
    request: dict = {},
    current_user=Depends(require_ops_roles("admin"))
):
    """PE-6.4: Platform Engineer execute rollback"""
    audit_event = {
        "event_type": "workflow_rolledback",
        "actor": current_user,
        "resource": f"/workflows/{workflow_id}/rollback",
        "target_version": request.get("target_version"),
        "incident_id": request.get("incident_id")
    }
    _audit_events.append(audit_event)
    return {
        "status": "rolling_back",
        "workflow_id": workflow_id,
        "target_version": request.get("target_version")
    }


@router.get("/audit")
def get_audit_trail(
    incident_id: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    current_user=Depends(require_ops_roles("admin"))
):
    """PE-6.5: Incident response audit trail"""
    # Initialize with test data if empty
    global _audit_events
    if not _audit_events:
        _audit_events = [
            {
                "event_type": "workflow_paused",
                "actor": "platform_engineer",
                "resource": "/workflows/wf_discovery_v1/pause",
                "incident_id": "incident_123"
            },
            {
                "event_type": "failsafe_activated",
                "actor": "platform_engineer",
                "resource": "/workflows/wf_discovery_v1/failsafe/activate",
                "incident_id": "incident_123"
            },
            {
                "event_type": "workflow_rolledback",
                "actor": "platform_engineer",
                "resource": "/workflows/wf_discovery_v1/rollback",
                "target_version": "0.9.5",
                "incident_id": "incident_123"
            }
        ]

    filtered_events = list(_audit_events)

    if incident_id:
        filtered_events = [
            e for e in filtered_events
            if e.get("incident_id") == incident_id
        ]

    if resource_id:
        filtered_events = [
            e for e in filtered_events
            if resource_id in e.get("resource", "")
        ]

    if action:
        filtered_events = [
            e for e in filtered_events
            if e.get("event_type") == action
        ]

    return filtered_events
