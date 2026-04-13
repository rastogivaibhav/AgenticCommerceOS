"""Salesforce REST API helpers for workflow connector actions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

_DEFAULT_TIMEOUT_SECONDS = 4.0
_DEFAULT_API_VERSION = "v60.0"


@dataclass(frozen=True)
class SalesforceConfig:
    instance_url: str
    access_token: str
    api_version: str = _DEFAULT_API_VERSION


def load_salesforce_config() -> SalesforceConfig | None:
    instance_url = (os.environ.get("SALESFORCE_INSTANCE_URL") or "").strip().rstrip("/")
    access_token = (os.environ.get("SALESFORCE_ACCESS_TOKEN") or "").strip()
    api_version = (os.environ.get("SALESFORCE_API_VERSION") or _DEFAULT_API_VERSION).strip()
    if not instance_url or not access_token:
        return None
    return SalesforceConfig(
        instance_url=instance_url,
        access_token=access_token,
        api_version=api_version or _DEFAULT_API_VERSION,
    )


def probe_salesforce(
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    config = load_salesforce_config()
    if not config:
        return {"status": "skipped", "configured": False, "reason": "salesforce_not_configured"}

    try:
        response = requests.get(
            f"{config.instance_url}/services/data/{config.api_version}/",
            headers={"Authorization": f"Bearer {config.access_token}"},
            timeout=max(float(timeout_seconds), 0.2),
        )
        if response.status_code >= 400:
            return {
                "status": "error",
                "configured": True,
                "status_code": response.status_code,
                "error": f"Salesforce HTTP {response.status_code}",
            }
        return {
            "status": "ok",
            "configured": True,
            "instance_url": config.instance_url,
            "api_version": config.api_version,
        }
    except (requests.Timeout, requests.ConnectionError) as exc:
        return {
            "status": "error",
            "configured": True,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


def execute_salesforce_action(
    action: str,
    payload: dict[str, Any],
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    config = load_salesforce_config()
    action_key = (action or "").strip().lower()
    if not config:
        return {
            "status": "ok",
            "mode": "sandbox",
            "action": action_key,
            "connector_source": "local_fallback",
            "note": "salesforce_not_configured",
            "result": _salesforce_sandbox_result(action_key, payload),
        }

    try:
        if action_key == "get_contact":
            contact_id = str(payload.get("contact_id") or "").strip()
            if not contact_id:
                return _salesforce_sandbox(action_key, "missing_contact_id", payload)
            result = _salesforce_get(config, f"/sobjects/Contact/{contact_id}", timeout_seconds)
        elif action_key == "get_case":
            case_id = str(payload.get("case_id") or "").strip()
            if not case_id:
                return _salesforce_sandbox(action_key, "missing_case_id", payload)
            result = _salesforce_get(config, f"/sobjects/Case/{case_id}", timeout_seconds)
        elif action_key == "create_case":
            body = {
                "Subject": payload.get("subject") or "Workflow escalation",
                "Description": payload.get("description") or payload.get("message") or "Created by ACOS workflow",
                "Origin": payload.get("origin") or "WhatsApp",
                "Status": payload.get("status") or "New",
            }
            result = _salesforce_post(config, "/sobjects/Case", body, timeout_seconds)
        elif action_key == "update_case":
            case_id = str(payload.get("case_id") or "").strip()
            if not case_id:
                return _salesforce_sandbox(action_key, "missing_case_id", payload)
            body = {key: value for key, value in payload.items() if key in {"Subject", "Description", "Status", "Priority"}}
            result = _salesforce_patch(config, f"/sobjects/Case/{case_id}", body, timeout_seconds)
        else:
            return _salesforce_sandbox(action_key, "unsupported_action", payload)
    except (requests.Timeout, requests.ConnectionError) as exc:
        return _salesforce_sandbox(action_key, f"{exc.__class__.__name__}: {exc}", payload)

    return {
        "status": "ok",
        "mode": "live",
        "action": action_key,
        "connector_source": "salesforce_rest_api",
        "instance_url": config.instance_url,
        "api_version": config.api_version,
        "result": result,
    }


def _salesforce_headers(config: SalesforceConfig) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _salesforce_get(config: SalesforceConfig, path: str, timeout_seconds: float) -> dict[str, Any]:
    response = requests.get(
        f"{config.instance_url}/services/data/{config.api_version}{path}",
        headers=_salesforce_headers(config),
        timeout=max(float(timeout_seconds), 0.2),
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def _salesforce_post(config: SalesforceConfig, path: str, body: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
    response = requests.post(
        f"{config.instance_url}/services/data/{config.api_version}{path}",
        headers=_salesforce_headers(config),
        json=body,
        timeout=max(float(timeout_seconds), 0.2),
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def _salesforce_patch(config: SalesforceConfig, path: str, body: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
    response = requests.patch(
        f"{config.instance_url}/services/data/{config.api_version}{path}",
        headers=_salesforce_headers(config),
        json=body,
        timeout=max(float(timeout_seconds), 0.2),
    )
    response.raise_for_status()
    if response.content:
        return response.json()
    return {"id": path.split("/")[-1], "updated": True}


def _salesforce_sandbox(action: str, reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "mode": "sandbox",
        "action": action,
        "connector_source": "local_fallback",
        "note": reason,
        "result": _salesforce_sandbox_result(action, payload),
    }


def _salesforce_sandbox_result(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action == "get_contact":
        return {
            "Id": payload.get("contact_id") or "003-demo-contact",
            "FirstName": "Demo",
            "LastName": "Customer",
            "Email": "customer@example.com",
            "AccountTier__c": "gold",
        }
    if action in {"create_case", "update_case", "get_case"}:
        return {
            "Id": payload.get("case_id") or "500-demo-case",
            "Subject": payload.get("subject") or "Workflow escalation",
            "Status": payload.get("status") or "New",
            "Priority": payload.get("priority") or "Medium",
        }
    return {"status": "sandbox"}
