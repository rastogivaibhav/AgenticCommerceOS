"""Check whether the local workspace is ready for a real WhatsApp Cloud validation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from acosplatform.db.repository import get_channel_bindings
from integrations.whatsapp.client import probe_whatsapp_cloud


REQUIRED_ENV_VARS = [
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_VERIFY_TOKEN",
]


def _binding_summary(binding: dict) -> dict:
    metadata = binding.get("metadata") or {}
    return {
        "id": binding.get("id"),
        "tenant_id": binding.get("tenant_id"),
        "environment": binding.get("environment"),
        "has_access_token": bool(str(metadata.get("access_token") or "").strip()),
        "has_phone_number_id": bool(str(metadata.get("phone_number_id") or "").strip()),
        "has_verify_token": bool(str(metadata.get("verify_token") or "").strip()),
        "has_default_recipient": bool(str(metadata.get("default_recipient") or "").strip()),
        "has_start_chat_number": bool(str(metadata.get("start_chat_number") or "").strip()),
    }


def main() -> int:
    env_status = {
        name: bool((os.environ.get(name) or "").strip())
        for name in REQUIRED_ENV_VARS
    }
    bindings = [binding for binding in get_channel_bindings() if binding.get("type") == "whatsapp"]
    summaries = [_binding_summary(binding) for binding in bindings]

    ready_binding = next(
        (
            binding
            for binding in bindings
            if all(
                bool(str((binding.get("metadata") or {}).get(field) or "").strip())
                for field in ("access_token", "phone_number_id", "verify_token")
            )
        ),
        None,
    )

    result = {
        "environment_ready": all(env_status.values()),
        "environment": env_status,
        "binding_count": len(bindings),
        "bindings": summaries,
    }

    if ready_binding:
        result["probe"] = probe_whatsapp_cloud(config_override=ready_binding.get("metadata") or {})
        result["live_validation_ready"] = bool(
            summaries[[binding.get("id") for binding in bindings].index(ready_binding.get("id"))]["has_default_recipient"]
        )
    else:
        result["probe"] = None
        result["live_validation_ready"] = False

    print(json.dumps(result, indent=2))
    return 0 if result["live_validation_ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
