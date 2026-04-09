"""ADK integration with a standardized runtime and tool contracts.

Falls back to local logic if Google GenAI API key is not set.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from acosplatform.auth.sanitize import sanitize_user_message
from integrations.adk.runtime import ADKRuntime, RuntimeTool, ToolContract, ToolContractError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"
SUPPORTED_RUNTIME_PROVIDERS = ("google_genai", "local_fallback")
ROADMAP_RUNTIME_PROVIDERS = (
    "crewai",
    "salesforce_agentforce",
    "servicenow_agent",
    "openai_agent",
)

_adk_available = False
_model = None


def _init_adk() -> None:
    global _adk_available, _model
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("No GOOGLE_API_KEY set; ADK running in local fallback mode")
        _adk_available = False
        return

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        _model = client
        _adk_available = True
        logger.info("Google GenAI ADK initialized")
    except Exception as exc:
        logger.warning(f"ADK init failed: {exc}")
        _adk_available = False


_init_adk()


def _skill_recommendation(ctx: dict[str, Any], products: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Recommendation skill that returns product reasoning."""
    message = ctx.get("message", "")
    prefs = ctx.get("preferences", {})

    if _adk_available and _model:
        try:
            prompt = (
                f"You are a shopping assistant. The customer says: '{message}'. "
                f"Their preferences: {json.dumps(prefs)}. "
                f"Available products: {json.dumps((products or [])[:3])}. "
                "Give a brief, friendly recommendation in 2-3 sentences. "
                "Mention specific product names and why they are a good fit."
            )
            response = _model.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
            )
            return {
                "recommendation_text": response.text,
                "source": "adk_genai",
            }
        except Exception as exc:
            logger.warning(f"ADK recommendation skill failed: {exc}")

    if products:
        top = products[0]
        name = top.get("name", "our top pick")
        category = top.get("category", "product")
        return {
            "recommendation_text": (
                f"Based on your interest, I recommend {name}. "
                f"It is one of our best {category} options and aligns well with your preferences."
            ),
            "source": "local_fallback",
        }

    return {
        "recommendation_text": "Check out our latest products across all categories.",
        "source": "local_fallback",
    }


def _skill_explanation(ctx: dict[str, Any], result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Explanation skill for pricing and recommendation rationale."""
    message = sanitize_user_message(ctx.get("message", ""))

    if _adk_available and _model:
        try:
            prompt = (
                f"You are a shopping assistant. The customer asked: '{message}'. "
                f"Here is result context: {json.dumps(result or {}, default=str)[:500]}. "
                "Provide a concise explanation in 2-3 sentences."
            )
            response = _model.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
            )
            return {
                "explanation_text": response.text,
                "source": "adk_genai",
            }
        except Exception as exc:
            logger.warning(f"ADK explanation skill failed: {exc}")

    return {
        "explanation_text": (
            "Results are personalized from your request, with active promotions and loyalty effects applied."
        ),
        "source": "local_fallback",
    }


def _build_runtime(journey_type: str) -> ADKRuntime:
    provider = "google_genai" if _adk_available else "local_fallback"
    runtime = ADKRuntime(
        journey_type=journey_type,
        provider=provider,
        contract_version="adk-tool-v1",
        model_name=DEFAULT_MODEL,
    )

    runtime.register_tool(
        RuntimeTool(
            name="recommendation",
            handler=lambda payload: _skill_recommendation(payload, payload.get("products") or []),
            contract=ToolContract(
                name="recommendation",
                output_required=("recommendation_text", "source"),
                output_types={"recommendation_text": str, "source": str},
            ),
        )
    )
    runtime.register_tool(
        RuntimeTool(
            name="explanation",
            handler=lambda payload: _skill_explanation(payload, payload.get("explanation_context")),
            contract=ToolContract(
                name="explanation",
                output_required=("explanation_text", "source"),
                output_types={"explanation_text": str, "source": str},
            ),
        )
    )
    return runtime


def run_adk(ctx: dict[str, Any], journey_type: str = "discovery") -> dict[str, Any]:
    """Supervisor entrypoint using standardized runtime execution."""
    runtime = _build_runtime(journey_type)
    pipeline_by_journey = {
        "discovery": ["recommendation"],
        "purchase": ["recommendation", "explanation"],
        "service": ["explanation"],
        "post_purchase": ["explanation"],
        "engagement": ["recommendation"],
    }

    runtime_payload = dict(ctx)
    runtime_payload["products"] = ctx.get("recommendations") or ctx.get("products") or []
    if journey_type == "post_purchase":
        runtime_payload["explanation_context"] = {"type": "order_tracking"}

    outputs: dict[str, Any] = {}
    used_tools: list[str] = []
    contract_errors: list[str] = []
    try:
        outputs, used_tools = runtime.run_pipeline(
            pipeline_by_journey.get(journey_type, ["recommendation"]),
            runtime_payload,
        )
    except ToolContractError as exc:
        logger.error(f"ADK tool contract violation: {exc}")
        contract_errors.append(str(exc))

    result = {
        "adk_active": _adk_available,
        "journey_type": journey_type,
        "skills_used": used_tools,
        "runtime": runtime.metadata(),
    }
    if "recommendation" in outputs:
        result["recommendation"] = outputs["recommendation"]
    if "explanation" in outputs:
        result["explanation"] = outputs["explanation"]
    if contract_errors:
        result["contract_errors"] = contract_errors
    return result


def get_runtime_capabilities() -> dict[str, Any]:
    return {
        "supported_providers": list(SUPPORTED_RUNTIME_PROVIDERS),
        "roadmap_providers": list(ROADMAP_RUNTIME_PROVIDERS),
        "default_model": DEFAULT_MODEL,
        "active_provider": "google_genai" if _adk_available else "local_fallback",
        "genai_enabled": _adk_available,
    }
