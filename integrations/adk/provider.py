"""ADK integration – supervisor agent with recommendation and explanation skills.

Falls back to local logic if Google GenAI API key is not set.
"""

import os
import logging
import json

from acosplatform.auth.sanitize import sanitize_user_message

logger = logging.getLogger(__name__)

_adk_available = False
_model = None


def _init_adk():
    global _adk_available, _model
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("No GOOGLE_API_KEY set – ADK running in local-fallback mode")
        _adk_available = False
        return

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        _model = client
        _adk_available = True
        logger.info("Google GenAI ADK initialized")
    except Exception as e:
        logger.warning(f"ADK init failed: {e}")
        _adk_available = False


_init_adk()


# ── Skills ────────────────────────────────────────────────────────────────────

def _skill_recommendation(ctx, products=None):
    """Recommendation skill – generates product recommendation reasoning."""
    message = ctx.get("message", "")
    prefs = ctx.get("preferences", {})

    if _adk_available and _model:
        try:
            prompt = (
                f"You are a shopping assistant. The customer says: '{message}'. "
                f"Their preferences: {json.dumps(prefs)}. "
                f"Available products: {json.dumps(products[:3] if products else [])}. "
                f"Give a brief, friendly recommendation in 2-3 sentences. "
                f"Mention specific product names and why they'd be a good fit."
            )
            response = _model.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return {
                "recommendation_text": response.text,
                "source": "adk_genai",
            }
        except Exception as e:
            logger.warning(f"ADK recommendation skill failed: {e}")

    # Local fallback
    if products:
        top = products[0] if products else {}
        name = top.get("name", "our top pick")
        category = top.get("category", "product")
        return {
            "recommendation_text": (
                f"Based on your interest, I'd recommend the {name}. "
                f"It's one of our best {category} items and matches your preferences perfectly. "
                f"Great value at the current promotional price!"
            ),
            "source": "local_fallback",
        }

    return {
        "recommendation_text": "Check out our latest products across all categories!",
        "source": "local_fallback",
    }


def _skill_explanation(ctx, result=None):
    """Explanation skill – explains pricing, promos, or decisions."""
    message = sanitize_user_message(ctx.get("message", ""))

    if _adk_available and _model:
        try:
            prompt = (
                f"You are a shopping assistant. The customer asked: '{message}'. "
                f"Here is the result data: {json.dumps(result or {}, default=str)[:500]}. "
                f"Provide a brief, clear explanation in 2-3 sentences about the pricing, "
                f"discounts, or recommendation shown."
            )
            response = _model.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return {
                "explanation_text": response.text,
                "source": "adk_genai",
            }
        except Exception as e:
            logger.warning(f"ADK explanation skill failed: {e}")

    # Local fallback
    return {
        "explanation_text": (
            "Your results include personalized recommendations based on your preferences, "
            "with the best available promotions automatically applied. "
            "Loyalty points are factored into your final pricing."
        ),
        "source": "local_fallback",
    }


# ── Supervisor ────────────────────────────────────────────────────────────────

def run_adk(ctx, journey_type="discovery"):
    """Supervisor agent – routes to appropriate skill based on journey type.

    Acts as an orchestrator that picks the right skill(s) for the journey.
    """
    result = {
        "adk_active": _adk_available,
        "journey_type": journey_type,
        "skills_used": [],
    }

    products = ctx.get("recommendations") or ctx.get("products") or []

    if journey_type in ("discovery", "purchase"):
        rec = _skill_recommendation(ctx, products)
        result["recommendation"] = rec
        result["skills_used"].append("recommendation")

    if journey_type in ("purchase", "service"):
        expl = _skill_explanation(ctx)
        result["explanation"] = expl
        result["skills_used"].append("explanation")

    if journey_type == "post_purchase":
        expl = _skill_explanation(ctx, {"type": "order_tracking"})
        result["explanation"] = expl
        result["skills_used"].append("explanation")

    if journey_type == "engagement":
        rec = _skill_recommendation(ctx, products)
        result["recommendation"] = rec
        result["skills_used"].append("recommendation")

    return result
