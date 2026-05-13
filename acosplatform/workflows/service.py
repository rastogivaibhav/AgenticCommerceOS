"""Workflow registry services and default seed data for ACOS."""

import logging
import re
from typing import Any, Optional

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

DEMO_WORKFLOW_ID = "wf-order-support-demo"

DEFAULT_WORKFLOWS = [
    {
        "tenant_id": "default",
        "workflow_id": DEMO_WORKFLOW_ID,
        "name": "Order Support Assistant",
        "family": "service",
        "description": "Resolve inbound order questions with Shopify, Salesforce, WhatsApp, and governed escalation.",
        "is_demo": True,
    },
    {
        "tenant_id": "default",
        "workflow_id": "wf-discovery",
        "name": "Discovery Concierge",
        "family": "discovery",
        "description": "AI-assisted product discovery and recommendation",
    },
    {
        "tenant_id": "default",
        "workflow_id": "wf-purchase",
        "name": "Purchase Guide",
        "family": "purchase",
        "description": "Price, promotion, loyalty, and checkout support",
    },
    {
        "tenant_id": "default",
        "workflow_id": "wf-post-purchase",
        "name": "Post Purchase Tracker",
        "family": "post_purchase",
        "description": "Order status and fulfillment support",
    },
    {
        "tenant_id": "default",
        "workflow_id": "wf-service",
        "name": "Service Recovery",
        "family": "service",
        "description": "Returns, service, and exception handling",
    },
    {
        "tenant_id": "default",
        "workflow_id": "wf-engagement",
        "name": "Engagement Loop",
        "family": "engagement",
        "description": "Feedback, loyalty, and referral engagement",
    },
]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workflow"


def _blank_workflow_graph(family: str) -> dict[str, Any]:
    trigger_label = {
        "discovery": "Web Intake",
        "purchase": "Cart Event",
        "post_purchase": "Order Update",
        "service": "Support Request",
        "engagement": "Campaign Trigger",
    }.get(family, "Workflow Trigger")
    return {
        "nodes": [
            {
                "id": "trigger-1",
                "type": "triggerNode",
                "position": {"x": 260, "y": 80},
                "data": {
                    "label": trigger_label,
                    "channel": "api",
                    "triggerType": "manual",
                    "bindingId": "",
                    "mode": "demo",
                },
            },
            {
                "id": "agent-1",
                "type": "agentNode",
                "position": {"x": 260, "y": 230},
                "data": {
                    "label": "Primary Agent",
                    "agentId": "ag_support_l1",
                    "mode": "demo",
                },
            },
            {
                "id": "end-1",
                "type": "endNode",
                "position": {"x": 260, "y": 380},
                "data": {
                    "label": "Resolved",
                    "outcomeType": "success",
                },
            },
        ],
        "edges": [
            {
                "id": "edge-trigger-agent",
                "source": "trigger-1",
                "target": "agent-1",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
            {
                "id": "edge-agent-end",
                "source": "agent-1",
                "target": "end-1",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
        ],
    }


def _order_support_demo_graph() -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": "trigger-whatsapp",
                "type": "triggerNode",
                "position": {"x": 260, "y": 40},
                "data": {
                    "label": "WhatsApp Inbound",
                    "channel": "whatsapp",
                    "triggerType": "inbound_message",
                    "bindingId": "whatsapp-support",
                    "sampleMessage": "Where is my order ORD-1001?",
                    "mode": "sandbox",
                },
            },
            {
                "id": "connector-shopify",
                "type": "connectorNode",
                "position": {"x": 80, "y": 200},
                "data": {
                    "label": "Shopify Order Lookup",
                    "connectorType": "shopify",
                    "bindingId": "shopify-primary",
                    "action": "get_order",
                    "config": {"order_id": "{{trigger.order_id}}"},
                    "mode": "live_or_sandbox",
                },
            },
            {
                "id": "connector-salesforce",
                "type": "connectorNode",
                "position": {"x": 440, "y": 200},
                "data": {
                    "label": "Salesforce Customer Context",
                    "connectorType": "salesforce",
                    "bindingId": "salesforce-support",
                    "action": "get_contact",
                    "config": {"contact_key": "{{trigger.customer_phone}}"},
                    "mode": "sandbox",
                },
            },
            {
                "id": "agent-order-support",
                "type": "agentNode",
                "position": {"x": 260, "y": 350},
                "data": {
                    "label": "Order Support Agent",
                    "agentId": "ag_support_l1",
                    "mode": "live_or_demo",
                },
            },
            {
                "id": "decision-resolution",
                "type": "decisionNode",
                "position": {"x": 260, "y": 500},
                "data": {
                    "label": "Can Resolve Automatically?",
                    "logicType": "decision",
                    "routingRule": "order_found && confidence >= 0.7",
                },
            },
            {
                "id": "connector-whatsapp",
                "type": "connectorNode",
                "position": {"x": 70, "y": 670},
                "data": {
                    "label": "WhatsApp Reply",
                    "connectorType": "whatsapp",
                    "bindingId": "whatsapp-support",
                    "action": "send_message",
                    "config": {"template": "order_status_update"},
                    "mode": "sandbox",
                },
            },
            {
                "id": "human-escalation",
                "type": "humanNode",
                "position": {"x": 450, "y": 670},
                "data": {
                    "label": "Escalate to Service Desk",
                    "queue": "tier-2-order-support",
                    "bindingId": "salesforce-support",
                    "action": "create_case",
                    "mode": "sandbox",
                },
            },
            {
                "id": "end-resolved",
                "type": "endNode",
                "position": {"x": 70, "y": 830},
                "data": {
                    "label": "Customer Updated",
                    "outcomeType": "success",
                },
            },
            {
                "id": "end-escalated",
                "type": "endNode",
                "position": {"x": 450, "y": 830},
                "data": {
                    "label": "Escalated",
                    "outcomeType": "escalated",
                },
            },
        ],
        "edges": [
            {
                "id": "edge-trigger-shopify",
                "source": "trigger-whatsapp",
                "target": "connector-shopify",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
            {
                "id": "edge-trigger-salesforce",
                "source": "trigger-whatsapp",
                "target": "connector-salesforce",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
            {
                "id": "edge-shopify-agent",
                "source": "connector-shopify",
                "target": "agent-order-support",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
            {
                "id": "edge-salesforce-agent",
                "source": "connector-salesforce",
                "target": "agent-order-support",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
            {
                "id": "edge-agent-decision",
                "source": "agent-order-support",
                "target": "decision-resolution",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
            {
                "id": "edge-decision-reply",
                "source": "decision-resolution",
                "target": "connector-whatsapp",
                "type": "conditionEdge",
                "animated": False,
                "data": {"label": "yes"},
            },
            {
                "id": "edge-decision-escalation",
                "source": "decision-resolution",
                "target": "human-escalation",
                "type": "conditionEdge",
                "animated": False,
                "data": {"label": "no"},
            },
            {
                "id": "edge-reply-end",
                "source": "connector-whatsapp",
                "target": "end-resolved",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
            {
                "id": "edge-human-end",
                "source": "human-escalation",
                "target": "end-escalated",
                "type": "conditionEdge",
                "animated": False,
                "data": {},
            },
        ],
    }


def _seed_step_definitions(workflow_id: str, family: str) -> list[dict[str, Any]]:
    if workflow_id == DEMO_WORKFLOW_ID:
        return [_order_support_demo_graph()]
    return [_blank_workflow_graph(family)]


def ensure_default_workflow_registry(environment: str = "dev") -> None:
    existing = {workflow["id"] for workflow in get_workflows(tenant_id="default")}
    for item in DEFAULT_WORKFLOWS:
        tenant_id = item["tenant_id"]
        workflow_id = item["workflow_id"]
        name = item["name"]
        family = item["family"]
        description = item["description"]
        if workflow_id in existing:
            continue
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
            step_definitions=_seed_step_definitions(workflow_id, family),
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
                "is_demo": workflow["id"] == DEMO_WORKFLOW_ID,
                "recommended_entrypoint": workflow["id"] == DEMO_WORKFLOW_ID,
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
            "is_demo": workflow["id"] == DEMO_WORKFLOW_ID,
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
        step_definitions=_seed_step_definitions(workflow_id, payload.workflow_family),
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
        step_definitions=payload.step_definitions or _seed_step_definitions(workflow_id, workflow["workflow_family"]),
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


def resolve_execution_workflow(
    tenant_id: str,
    workflow_family: str,
    environment: str = "dev",
    preferred_workflow_id: Optional[str] = None,
):
    if preferred_workflow_id:
        preferred_workflow = get_workflow(preferred_workflow_id)
        if (
            preferred_workflow
            and preferred_workflow.get("workflow_family") == workflow_family
            and preferred_workflow.get("tenant_id") in {tenant_id, "default"}
        ):
            preferred_promotions = get_workflow_promotions(
                workflow_id=preferred_workflow_id,
                environment=environment,
            )
            active_promotion = next(
                (promotion for promotion in preferred_promotions if promotion.get("is_active")),
                None,
            )
            if active_promotion:
                return {
                    "workflow_id": preferred_workflow["id"],
                    "name": preferred_workflow["name"],
                    "workflow_family": preferred_workflow["workflow_family"],
                    "version": active_promotion.get("version"),
                    "lifecycle_state": "active",
                    "resolution": "preferred_active",
                }

            preferred_versions = get_workflow_versions(preferred_workflow_id)
            if preferred_versions:
                latest_version = preferred_versions[-1]
                return {
                    "workflow_id": preferred_workflow["id"],
                    "name": preferred_workflow["name"],
                    "workflow_family": preferred_workflow["workflow_family"],
                    "version": latest_version.get("version"),
                    "lifecycle_state": latest_version.get("lifecycle_state", "draft"),
                    "resolution": "preferred_latest",
                }

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
