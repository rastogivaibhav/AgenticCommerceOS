"""Workflow registry services and default seed data for ACOS."""

import logging
import re
from typing import Optional

from acosplatform.audit.logger import audit
from acosplatform.db.repository import (
    get_active_workflow_version,
    get_audit_events,
    get_runs_by_workflow,
    get_workflow,
    get_workflow_promotions,
    get_workflow_version,
    get_workflow_versions,
    get_workflows,
    save_audit_event,
    save_workflow,
    save_workflow_promotion,
    save_workflow_version,
)

logger = logging.getLogger(__name__)

DEFAULT_WORKFLOWS = [
    ("default", "wf-discovery", "Discovery Concierge", "discovery", "AI-assisted product discovery and recommendation"),
    ("default", "wf-purchase", "Purchase Guide", "purchase", "Price, promotion, loyalty, and checkout support"),
    ("default", "wf-post-purchase", "Post Purchase Tracker", "post_purchase", "Order status and fulfillment support"),
    ("default", "wf-service", "Service Recovery", "service", "Returns, service, and exception handling"),
    ("default", "wf-engagement", "Engagement Loop", "engagement", "Feedback, loyalty, and referral engagement"),
]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workflow"


def ensure_default_workflow_registry(environment: str = "dev") -> None:
    existing = get_workflows(tenant_id="default")
    if existing:
        return
    for tenant_id, workflow_id, name, family, description in DEFAULT_WORKFLOWS:
        save_workflow(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            name=name,
            workflow_family=family,
            description=description,
            business_owner="acos-team",
            status="active",
        )
        save_workflow_version(
            workflow_id=workflow_id,
            version="v1",
            change_summary="Seeded initial workflow version",
            validation_status="approved",
            lifecycle_state="approved",
            created_by="system",
            step_definitions=[{"step": "orchestrate", "family": family}],
            approved_by="system",
        )
        save_workflow_promotion(
            workflow_id=workflow_id,
            version="v1",
            source_environment=None,
            target_environment=environment,
            requested_by="system",
            approved_by="system",
            note="Seeded default active workflow",
        )
        _write_audit(
            actor="system",
            action="workflow.seeded",
            resource_type="workflow",
            resource_id=workflow_id,
            tenant_id=tenant_id,
            environment_id=environment,
            payload={"version": "v1", "workflow_family": family},
        )


def list_workflows_with_state(tenant_id: Optional[str] = None, environment: str = "dev"):
    workflows = get_workflows(tenant_id=tenant_id)
    promotions = get_workflow_promotions(environment=environment)
    active_lookup = {(p["workflow_id"], p["target_environment"]): p for p in promotions if p.get("is_active")}
    result = []
    for workflow in workflows:
        versions = get_workflow_versions(workflow["id"])
        active_promotion = active_lookup.get((workflow["id"], environment))
        result.append(
            {
                **workflow,
                "version_count": len(versions),
                "active_version": active_promotion.get("version") if active_promotion else None,
                "active_environment": environment if active_promotion else None,
                "last_promoted_at": active_promotion.get("promoted_at") if active_promotion else None,
            }
        )
    return result


def get_workflow_detail(workflow_id: str, environment: str = "dev"):
    workflow = get_workflow(workflow_id)
    if not workflow:
        return None
    versions = get_workflow_versions(workflow_id)
    promotions = get_workflow_promotions(workflow_id=workflow_id)
    audits = get_audit_events(resource_type="workflow", resource_id=workflow_id, limit=100)
    runs = get_runs_by_workflow(workflow_id, limit=25)
    active_version = None
    for promotion in promotions:
        if promotion.get("target_environment") == environment and promotion.get("is_active"):
            active_version = promotion.get("version")
            break
    return {
        "workflow": {
            **workflow,
            "active_version": active_version,
            "environment": environment,
        },
        "versions": versions,
        "promotions": promotions,
        "audits": audits,
        "runs": runs,
    }


def create_workflow_draft(payload, actor: str, environment: str = "dev"):
    workflow_id = f"wf-{_slugify(payload.tenant_id)}-{_slugify(payload.name)}"
    existing = get_workflow(workflow_id)
    if existing:
        raise ValueError(f"Workflow '{workflow_id}' already exists")
    workflow = save_workflow(
        workflow_id=workflow_id,
        tenant_id=payload.tenant_id,
        name=payload.name,
        workflow_family=payload.workflow_family,
        description=payload.description,
        business_owner=payload.business_owner,
        status="draft",
    )
    version = save_workflow_version(
        workflow_id=workflow_id,
        version="v1",
        change_summary=payload.change_summary,
        validation_status="draft",
        lifecycle_state="draft",
        created_by=actor,
        step_definitions=[{"step": "draft", "family": payload.workflow_family}],
    )
    _write_audit(
        actor=actor,
        action="workflow.created",
        resource_type="workflow",
        resource_id=workflow_id,
        tenant_id=payload.tenant_id,
        environment_id=environment,
        payload={"version": version["version"], "workflow_family": payload.workflow_family},
    )
    return {"workflow": workflow, "version": version}


def create_workflow_version(workflow_id: str, payload, actor: str, environment: str = "dev"):
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise ValueError("Workflow not found")
    versions = get_workflow_versions(workflow_id)
    next_version = f"v{len(versions) + 1}"
    approved_by = actor if payload.validation_status == "approved" else None
    version = save_workflow_version(
        workflow_id=workflow_id,
        version=next_version,
        change_summary=payload.change_summary,
        validation_status=payload.validation_status,
        lifecycle_state=payload.validation_status,
        created_by=actor,
        step_definitions=payload.step_definitions or [{"step": "draft", "family": workflow["workflow_family"], "version": next_version}],
        agent_bindings=payload.agent_bindings,
        input_schema=payload.input_schema,
        approved_by=approved_by,
    )
    _write_audit(
        actor=actor,
        action="workflow.version_created",
        resource_type="workflow",
        resource_id=workflow_id,
        tenant_id=workflow["tenant_id"],
        environment_id=environment,
        payload={"version": version["version"], "validation_status": payload.validation_status},
    )
    return version


def approve_workflow_version(
    workflow_id: str,
    version: str,
    actor: str,
    environment: str = "dev",
    approval_note: str = "",
):
    workflow = get_workflow(workflow_id)
    workflow_version = get_workflow_version(workflow_id, version)
    if not workflow or not workflow_version:
        raise ValueError("Workflow version not found")

    if workflow_version.get("validation_status") == "approved":
        return {"version": workflow_version, "already_approved": True}

    approved = save_workflow_version(
        workflow_id=workflow_id,
        version=version,
        change_summary=workflow_version.get("change_summary") or "Approved workflow version",
        validation_status="approved",
        lifecycle_state="approved",
        created_by=workflow_version.get("created_by", actor),
        input_schema=workflow_version.get("input_schema"),
        output_schema=workflow_version.get("output_schema"),
        step_definitions=workflow_version.get("step_definitions"),
        agent_bindings=workflow_version.get("agent_bindings"),
        policy_bindings=workflow_version.get("policy_bindings"),
        approved_by=actor,
    )
    _write_audit(
        actor=actor,
        action="workflow.version_approved",
        resource_type="workflow",
        resource_id=workflow_id,
        tenant_id=workflow["tenant_id"],
        environment_id=environment,
        payload={"version": version, "approval_note": approval_note},
    )
    return {"version": approved, "already_approved": False}


def promote_workflow_version(
    workflow_id: str,
    version: str,
    target_environment: str,
    actor: str,
    approval_note: str = "",
    source_environment: Optional[str] = None,
):
    workflow = get_workflow(workflow_id)
    workflow_version = get_workflow_version(workflow_id, version)
    if not workflow or not workflow_version:
        raise ValueError("Workflow version not found")
    if workflow_version.get("validation_status") != "approved":
        raise RuntimeError("Only approved workflow versions can be promoted")
    promotion = save_workflow_promotion(
        workflow_id=workflow_id,
        version=version,
        source_environment=source_environment,
        target_environment=target_environment,
        requested_by=actor,
        approved_by=actor,
        note=approval_note or f"Promoted to {target_environment}",
    )
    updated_version = save_workflow_version(
        workflow_id=workflow_id,
        version=version,
        change_summary=workflow_version["change_summary"],
        validation_status="approved",
        lifecycle_state="active",
        created_by=workflow_version.get("created_by", actor),
        input_schema=workflow_version.get("input_schema"),
        output_schema=workflow_version.get("output_schema"),
        step_definitions=workflow_version.get("step_definitions"),
        agent_bindings=workflow_version.get("agent_bindings"),
        policy_bindings=workflow_version.get("policy_bindings"),
        approved_by=actor,
    )
    save_workflow(
        workflow_id=workflow["id"],
        tenant_id=workflow["tenant_id"],
        name=workflow["name"],
        workflow_family=workflow["workflow_family"],
        description=workflow.get("description", ""),
        business_owner=workflow.get("business_owner", "acos-team"),
        status="active",
    )
    _write_audit(
        actor=actor,
        action="workflow.promoted",
        resource_type="workflow",
        resource_id=workflow_id,
        tenant_id=workflow["tenant_id"],
        environment_id=target_environment,
        payload={"version": version, "source_environment": source_environment, "target_environment": target_environment},
    )
    return {"promotion": promotion, "version": updated_version}


def rollback_workflow_version(
    workflow_id: str,
    target_environment: str,
    actor: str,
    to_version: Optional[str] = None,
    reason: str = "",
):
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise ValueError("Workflow not found")

    promotions = get_workflow_promotions(workflow_id=workflow_id, environment=target_environment)
    active = next((p for p in promotions if p.get("is_active")), None)
    if not active:
        raise RuntimeError("No active promotion exists to roll back")

    current_version = active.get("version")
    rollback_version = to_version

    if rollback_version:
        candidate = get_workflow_version(workflow_id, rollback_version)
        if not candidate:
            raise ValueError("Rollback target version not found")
        if candidate.get("validation_status") != "approved":
            raise RuntimeError("Rollback target must be an approved version")
    else:
        candidate = next(
            (p for p in promotions if p.get("version") != current_version),
            None,
        )
        if not candidate:
            raise RuntimeError("No previous version available for rollback")
        rollback_version = candidate["version"]

    promotion = save_workflow_promotion(
        workflow_id=workflow_id,
        version=rollback_version,
        source_environment=target_environment,
        target_environment=target_environment,
        requested_by=actor,
        approved_by=actor,
        note=reason or f"Rollback from {current_version} to {rollback_version}",
        status="rolled_back",
    )
    updated_version = save_workflow_version(
        workflow_id=workflow_id,
        version=rollback_version,
        change_summary=f"Rollback activation ({target_environment})",
        validation_status="approved",
        lifecycle_state="active",
        created_by=actor,
        approved_by=actor,
    )

    _write_audit(
        actor=actor,
        action="workflow.rolled_back",
        resource_type="workflow",
        resource_id=workflow_id,
        tenant_id=workflow["tenant_id"],
        environment_id=target_environment,
        payload={
            "from_version": current_version,
            "to_version": rollback_version,
            "target_environment": target_environment,
            "reason": reason,
        },
    )
    return {
        "rollback": promotion,
        "version": updated_version,
        "from_version": current_version,
        "to_version": rollback_version,
    }


def archive_workflow(
    workflow_id: str,
    actor: str,
    environment: str = "dev",
    reason: str = "",
):
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise ValueError("Workflow not found")

    archived = save_workflow(
        workflow_id=workflow["id"],
        tenant_id=workflow["tenant_id"],
        name=workflow["name"],
        workflow_family=workflow["workflow_family"],
        description=workflow.get("description", ""),
        business_owner=workflow.get("business_owner", "acos-team"),
        status="archived",
    )
    _write_audit(
        actor=actor,
        action="workflow.archived",
        resource_type="workflow",
        resource_id=workflow_id,
        tenant_id=workflow["tenant_id"],
        environment_id=environment,
        payload={"reason": reason, "status": "archived"},
    )
    return {"workflow": archived, "status": "archived"}


def resolve_execution_workflow(tenant_id: str, workflow_family: str, environment: str = "dev"):
    active = get_active_workflow_version(workflow_family, tenant_id=tenant_id, environment=environment)
    if active:
        return active
    # fall back to the default tenant registry if a tenant-specific active version is not defined
    return get_active_workflow_version(workflow_family, tenant_id="default", environment=environment)


def _write_audit(actor, action, resource_type, resource_id, tenant_id, environment_id, payload):
    entry = audit(
        event_type=action,
        actor=actor,
        resource=resource_id,
        outcome="success",
        resource_type=resource_type,
        tenant_id=tenant_id,
        environment_id=environment_id,
        payload=payload,
    )
    save_audit_event(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=tenant_id,
        environment_id=environment_id,
        payload=entry,
    )
