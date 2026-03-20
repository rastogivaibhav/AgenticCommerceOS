"""Evaluation engine – quality scoring and A/B testing."""

import random
import logging
from datetime import datetime

from acosplatform.db.repository import save_experiment, get_experiments

logger = logging.getLogger(__name__)


def score(result, journey_type="discovery"):
    """Score the quality of a journey result.

    Scoring criteria:
    - Recommendation relevance (0-3): based on personalization
    - Price competitiveness (0-3): based on discounts applied
    - Journey completeness (0-4): based on data completeness

    Returns dict with individual scores and overall (0-10).
    """
    # Recommendation relevance
    relevance = 0
    personalization = result.get("personalization", {})
    if personalization.get("is_personalized"):
        relevance += 2
    recs = result.get("recommendations", [])
    if recs and len(recs) >= 3:
        relevance += 1

    # Price competitiveness
    price_score = 0
    promo = result.get("promotions", {})
    savings = promo.get("savings", 0) if isinstance(promo, dict) else 0
    if savings > 0:
        price_score += 1
    if savings > 10:
        price_score += 1
    loyalty = result.get("loyalty", {})
    if loyalty.get("tier") in ("Silver", "Gold", "Platinum"):
        price_score += 1

    # Journey completeness
    completeness = 0
    if result.get("agent", {}).get("skills_used"):
        completeness += 1
    if result.get("policy", {}).get("allowed"):
        completeness += 1
    if result.get("cost", {}).get("total_cost") is not None:
        completeness += 1

    # Journey-type specific completeness
    if journey_type == "discovery" and recs:
        completeness += 1
    elif journey_type == "purchase" and result.get("cart"):
        completeness += 1
    elif journey_type == "post_purchase" and result.get("order_info"):
        completeness += 1
    elif journey_type == "service" and result.get("return"):
        completeness += 1
    elif journey_type == "engagement" and (result.get("referral") or result.get("feedback") or result.get("engagement")):
        completeness += 1

    overall = min(relevance + price_score + completeness, 10)

    return {
        "relevance": relevance,
        "price_competitiveness": price_score,
        "completeness": completeness,
        "overall": overall,
        "max_score": 10,
        "journey_type": journey_type,
    }


# ── A/B Testing ───────────────────────────────────────────────────────────────

_active_experiments = {}


def assign_variant(experiment_name):
    """Assign a variant (A or B) for an experiment. 50/50 split."""
    return random.choice(["A", "B"])


def run_ab_test(experiment_name, payload, run_func):
    """Run an A/B test by executing the journey twice with different configs.

    In real production, this would only run one variant per user.
    For evaluation purposes, we run both and compare.
    """
    # Variant A: default config
    variant_a_payload = dict(payload)
    variant_a_payload["_variant"] = "A"
    result_a = run_func(variant_a_payload)

    # Variant B: modified config (e.g., different promo rates)
    variant_b_payload = dict(payload)
    variant_b_payload["_variant"] = "B"
    variant_b_payload["_boost_promos"] = True
    result_b = run_func(variant_b_payload)

    score_a = result_a.get("result", {}).get("quality_score", {}).get("overall", 0)
    score_b = result_b.get("result", {}).get("quality_score", {}).get("overall", 0)

    winner = "A" if score_a >= score_b else "B"

    experiment = save_experiment(
        name=experiment_name,
        variant_a={"score": score_a, "run_id": result_a.get("run_id")},
        variant_b={"score": score_b, "run_id": result_b.get("run_id")},
        winner=winner,
    )

    return {
        "experiment": experiment_name,
        "variant_a": {"score": score_a, "run_id": result_a.get("run_id")},
        "variant_b": {"score": score_b, "run_id": result_b.get("run_id")},
        "winner": winner,
        "experiment_id": experiment.get("id"),
    }


def get_experiment_results():
    """Get all experiment results."""
    return get_experiments()
