"""ADK integration with a standardized runtime and tool contracts.

Falls back to local logic if Google GenAI API key is not set.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

from acosplatform.auth.sanitize import sanitize_user_message
from integrations.adk.runtime import ADKRuntime, RuntimeTool, ToolContract, ToolContractError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"
SUPPORTED_RUNTIME_PROVIDERS = (
    "google_genai",
    "local_openai_host",
    "local_openai_docker",
    "local_fallback",
)
RUNTIME_PREFERENCE_OPTIONS = ("auto", *SUPPORTED_RUNTIME_PROVIDERS)
ROADMAP_RUNTIME_PROVIDERS = (
    "crewai",
    "salesforce_agentforce",
    "servicenow_agent",
    "openai_agent",
)

_adk_available = False
_model = None


def _normalize_provider_name(value: str | None, *, allow_auto: bool = False) -> str:
    normalized = (value or "").strip().lower()
    aliases = {
        "google adk": "google_genai",
        "google_genai": "google_genai",
        "lmstudio": "local_openai_host",
        "lmstudio_local": "local_openai_host",
        "lmstudio_host": "local_openai_host",
        "local_openai_host": "local_openai_host",
        "local llm": "local_openai_host",
        "local_llm": "local_openai_host",
        "docker llm": "local_openai_docker",
        "docker_llm": "local_openai_docker",
        "lmstudio_docker": "local_openai_docker",
        "local_openai_docker": "local_openai_docker",
        "local fallback": "local_fallback",
        "local_fallback": "local_fallback",
    }
    if allow_auto and normalized in {"", "auto"}:
        return "auto"
    return aliases.get(normalized, normalized)

def _openai_profile_config(provider: str) -> dict[str, Any]:
    normalized = _normalize_provider_name(provider)
    if normalized == "local_openai_docker":
        configured_base_url = (
            os.environ.get("DOCKER_OPENAI_BASE_URL")
            or os.environ.get("LMSTUDIO_DOCKER_BASE_URL")
            or ""
        ).rstrip("/")
        configured_model = (
            os.environ.get("DOCKER_OPENAI_MODEL")
            or os.environ.get("LMSTUDIO_DOCKER_MODEL")
            or os.environ.get("LOCAL_OPENAI_MODEL")
            or os.environ.get("LMSTUDIO_MODEL")
            or ""
        ).strip()
        return {
            "provider": "local_openai_docker",
            "label": "Docker local LLM",
            "configured_base_url": configured_base_url,
            "configured_model": configured_model,
            "base_candidates": [configured_base_url] if configured_base_url else [
                "http://host.docker.internal:1234/v1",
                "http://llm:1234/v1",
            ],
        }

    configured_base_url = (
        os.environ.get("LOCAL_OPENAI_BASE_URL")
        or os.environ.get("LMSTUDIO_BASE_URL")
        or ""
    ).rstrip("/")
    configured_model = (
        os.environ.get("LOCAL_OPENAI_MODEL")
        or os.environ.get("LMSTUDIO_MODEL")
        or ""
    ).strip()
    return {
        "provider": "local_openai_host",
        "label": "Host local LLM",
        "configured_base_url": configured_base_url,
        "configured_model": configured_model,
        "base_candidates": [configured_base_url] if configured_base_url else [
            "http://localhost:1234/v1",
            "http://127.0.0.1:1234/v1",
        ],
    }


def _runtime_preference_default() -> str:
    return _normalize_provider_name(os.environ.get("ACOS_RUNTIME_PREFERENCE"), allow_auto=True)


def _probe_openai_compatible(
    provider: str,
    timeout_seconds: float = 1.5,
) -> tuple[bool, str | None, str | None]:
    profile = _openai_profile_config(provider)
    for base_url in profile["base_candidates"]:
        try:
            response = requests.get(
                f"{base_url}/models",
                timeout=max(float(timeout_seconds), 0.2),
            )
            response.raise_for_status()
            payload = response.json() if response.content else {}
            data = payload.get("data") if isinstance(payload, dict) else []
            if isinstance(data, list) and data:
                candidate = data[0] or {}
                return True, candidate.get("id") or profile["configured_model"] or None, base_url
            return True, profile["configured_model"] or None, base_url
        except Exception:
            continue
    return False, None, None


def _openai_compatible_generate(
    prompt: str,
    provider: str,
    *,
    timeout_seconds: float = 10.0,
) -> str:
    profile = _openai_profile_config(provider)
    available, detected_model, _ = _probe_openai_compatible(provider, timeout_seconds=2.0)
    if not available:
        raise RuntimeError(f"{profile['label']} server is unavailable")

    model_name = profile["configured_model"] or detected_model
    if not model_name:
        raise RuntimeError(f"{profile['label']} server has no loaded model")

    last_error = None
    for base_url in profile["base_candidates"]:
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
                timeout=max(float(timeout_seconds), 0.5),
            )
            response.raise_for_status()
            payload = response.json() if response.content else {}
            choices = payload.get("choices") if isinstance(payload, dict) else []
            if not isinstance(choices, list) or not choices:
                raise RuntimeError("LM Studio response did not include choices")
            message = (choices[0] or {}).get("message") or {}
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError(f"{profile['label']} returned an empty response")
            return content
        except Exception as exc:
            last_error = exc
    raise RuntimeError(str(last_error) if last_error else f"{profile['label']} server is unavailable")


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


def _resolve_provider(
    requested_provider: str | None = None,
    *,
    strict_provider: bool = False,
) -> tuple[str, list[str]]:
    if requested_provider == "google_genai":
        if _adk_available and _model:
            return "google_genai", []
        if strict_provider:
            return (
                "google_genai",
                [
                    "Configured runtime provider 'google_genai' is unavailable. "
                    "Set GOOGLE_API_KEY or GEMINI_API_KEY to enable the Agent SDK runtime."
                ],
            )
        return "local_fallback", []

    normalized_request = _normalize_provider_name(
        requested_provider or _runtime_preference_default(),
        allow_auto=True,
    )

    if normalized_request == "local_fallback":
        return "local_fallback", []

    if normalized_request in {"", "auto"}:
        if _adk_available and _model:
            return "google_genai", []
        host_available, _, _ = _probe_openai_compatible("local_openai_host")
        if host_available:
            return "local_openai_host", []
        docker_available, _, _ = _probe_openai_compatible("local_openai_docker")
        if docker_available:
            return "local_openai_docker", []
        return "local_fallback", []

    if normalized_request in {"local_openai_host", "local_openai_docker"}:
        available, _, _ = _probe_openai_compatible(normalized_request)
        if available:
            return normalized_request, []
        if strict_provider:
            label = _openai_profile_config(normalized_request)["label"]
            return (
                normalized_request,
                [
                    f"Configured runtime provider '{normalized_request}' is unavailable. "
                    f"Start the {label.lower()} endpoint and load a model before retrying."
                ],
            )
        return "local_fallback", []

    return ("google_genai", []) if _adk_available and _model else ("local_fallback", [])


def _should_use_genai(ctx: dict[str, Any]) -> bool:
    return ctx.get("__runtime_provider") == "google_genai" and _adk_available and _model is not None


def _should_use_openai_local(ctx: dict[str, Any]) -> bool:
    return ctx.get("__runtime_provider") in {"local_openai_host", "local_openai_docker"}


def _skill_recommendation(ctx: dict[str, Any], products: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Recommendation skill that returns product reasoning."""
    message = ctx.get("message", "")
    prefs = ctx.get("preferences", {})

    if _should_use_genai(ctx):
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

    if _should_use_openai_local(ctx):
        try:
            prompt = (
                f"You are a shopping assistant. The customer says: '{message}'. "
                f"Their preferences: {json.dumps(prefs)}. "
                f"Available products: {json.dumps((products or [])[:3])}. "
                "Give a brief, friendly recommendation in 2-3 sentences. "
                "Mention specific product names and why they are a good fit."
            )
            return {
                "recommendation_text": _openai_compatible_generate(prompt, ctx.get("__runtime_provider")),
                "source": ctx.get("__runtime_provider") or "local_openai_host",
            }
        except Exception as exc:
            logger.warning(f"Local OpenAI recommendation skill failed: {exc}")

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

    if _should_use_genai(ctx):
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

    if _should_use_openai_local(ctx):
        try:
            prompt = (
                f"You are a shopping assistant. The customer asked: '{message}'. "
                f"Here is result context: {json.dumps(result or {}, default=str)[:500]}. "
                "Provide a concise explanation in 2-3 sentences."
            )
            return {
                "explanation_text": _openai_compatible_generate(prompt, ctx.get("__runtime_provider")),
                "source": ctx.get("__runtime_provider") or "local_openai_host",
            }
        except Exception as exc:
            logger.warning(f"Local OpenAI explanation skill failed: {exc}")

    return {
        "explanation_text": (
            "Results are personalized from your request, with active promotions and loyalty effects applied."
        ),
        "source": "local_fallback",
    }


def _build_runtime(journey_type: str, provider: str) -> ADKRuntime:
    model_name = DEFAULT_MODEL
    if provider in {"local_openai_host", "local_openai_docker"}:
        available, detected_model, _ = _probe_openai_compatible(provider)
        profile = _openai_profile_config(provider)
        model_name = profile["configured_model"] or detected_model or (
            "local-llm" if available else profile["label"].lower().replace(" ", "-")
        )
    runtime = ADKRuntime(
        journey_type=journey_type,
        provider=provider,
        contract_version="adk-tool-v1",
        model_name=model_name,
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


def run_adk(
    ctx: dict[str, Any],
    journey_type: str = "discovery",
    *,
    requested_provider: str | None = None,
    strict_provider: bool = False,
) -> dict[str, Any]:
    """Supervisor entrypoint using standardized runtime execution."""
    resolved_provider, runtime_errors = _resolve_provider(
        requested_provider,
        strict_provider=strict_provider,
    )
    runtime = _build_runtime(journey_type, resolved_provider)
    pipeline_by_journey = {
        "discovery": ["recommendation"],
        "purchase": ["recommendation", "explanation"],
        "service": ["explanation"],
        "post_purchase": ["explanation"],
        "engagement": ["recommendation"],
    }

    runtime_payload = dict(ctx)
    runtime_payload["__runtime_provider"] = resolved_provider
    runtime_payload["products"] = ctx.get("recommendations") or ctx.get("products") or []
    if journey_type == "post_purchase":
        runtime_payload["explanation_context"] = {"type": "order_tracking"}

    outputs: dict[str, Any] = {}
    used_tools: list[str] = []
    contract_errors: list[str] = []
    if not runtime_errors:
        try:
            outputs, used_tools = runtime.run_pipeline(
                pipeline_by_journey.get(journey_type, ["recommendation"]),
                runtime_payload,
            )
        except ToolContractError as exc:
            logger.error(f"ADK tool contract violation: {exc}")
            contract_errors.append(str(exc))

    result = {
        "adk_active": resolved_provider == "google_genai" and _adk_available,
        "journey_type": journey_type,
        "skills_used": used_tools,
        "runtime": runtime.metadata(),
        "tool_trace": list(ctx.get("tool_trace") or []),
    }
    if "recommendation" in outputs:
        result["recommendation"] = outputs["recommendation"]
    if "explanation" in outputs:
        result["explanation"] = outputs["explanation"]
    if runtime_errors:
        result["errors"] = runtime_errors
    if contract_errors:
        result["contract_errors"] = contract_errors
    return result


def get_runtime_capabilities() -> dict[str, Any]:
    preferred_provider = _runtime_preference_default()
    host_enabled, host_model, host_base_url = _probe_openai_compatible("local_openai_host")
    docker_enabled, docker_model, docker_base_url = _probe_openai_compatible("local_openai_docker")
    resolved_preferred, _ = _resolve_provider(preferred_provider, strict_provider=False)
    host_profile = _openai_profile_config("local_openai_host")
    docker_profile = _openai_profile_config("local_openai_docker")
    return {
        "supported_providers": list(SUPPORTED_RUNTIME_PROVIDERS),
        "runtime_preference_options": list(RUNTIME_PREFERENCE_OPTIONS),
        "roadmap_providers": list(ROADMAP_RUNTIME_PROVIDERS),
        "default_model": DEFAULT_MODEL,
        "active_provider": (
            "google_genai"
            if _adk_available
            else ("local_openai_host" if host_enabled else ("local_openai_docker" if docker_enabled else "local_fallback"))
        ),
        "preferred_provider": preferred_provider,
        "preferred_provider_resolved": resolved_preferred,
        "genai_enabled": _adk_available,
        "local_openai_profiles": {
            "local_openai_host": {
                "label": host_profile["label"],
                "available": host_enabled,
                "base_url": host_base_url or host_profile["base_candidates"][0],
                "configured_base_url": host_profile["configured_base_url"] or None,
                "model": host_profile["configured_model"] or host_model,
            },
            "local_openai_docker": {
                "label": docker_profile["label"],
                "available": docker_enabled,
                "base_url": docker_base_url or docker_profile["base_candidates"][0],
                "configured_base_url": docker_profile["configured_base_url"] or None,
                "model": docker_profile["configured_model"] or docker_model,
            },
        },
        "lmstudio_enabled": host_enabled or docker_enabled,
        "lmstudio_base_url": host_base_url or docker_base_url or host_profile["base_candidates"][0],
        "lmstudio_model": host_profile["configured_model"] or host_model or docker_profile["configured_model"] or docker_model,
    }
