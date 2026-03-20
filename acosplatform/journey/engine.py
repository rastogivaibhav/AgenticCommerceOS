"""Journey engine – full orchestration of commerce journeys through plugin chains."""

import uuid
import logging

from acosplatform.journey.context import build_context
from acosplatform.journey.routing import route
from acosplatform.plugins import catalog, pricing, promotions, loyalty, checkout, orders, returns
from integrations.adk.provider import run_adk
from integrations.agentfabric.client import start_trace, log_event, policy_check
from acosplatform.personalization.engine import personalize
from acosplatform.evaluation.scorer import score
from acosplatform.billing.engine import compute_cost
from acosplatform.db.repository import save_run, save_event
from acosplatform.analytics.stream import push
from acosplatform.workflows.service import resolve_execution_workflow

logger = logging.getLogger(__name__)


def run_journey(payload):
    """Execute a full commerce journey based on the incoming payload."""
    run_id = "run-" + uuid.uuid4().hex[:8]
    environment_id = payload.get("environment_id", "dev")

    # Build enriched context
    ctx = build_context(payload)
    journey_type = route(ctx)
    workflow = resolve_execution_workflow(ctx["tenant_id"], journey_type, environment=environment_id) or {}

    # Start tracing
    trace_id = start_trace(run_id, ctx)
    log_event(trace_id, "journey_started", {"journey": journey_type, "customer_id": ctx["customer_id"]})

    # Execute journey-specific plugin chain
    result = _execute_journey(journey_type, ctx, run_id, trace_id)

    # ADK agent enrichment
    adk_result = run_adk({**ctx, **result}, journey_type)
    result["agent"] = adk_result

    # Personalize
    result = personalize(ctx, result)

    # Policy check before finalizing
    policy = policy_check(trace_id, ctx, result)
    result["policy"] = policy

    # Compute cost
    run_cost = compute_cost(run_id, ctx, result)
    result["cost"] = run_cost

    # Attach workflow identity before scoring and persistence
    result["workflow"] = {
        "workflow_id": workflow.get("workflow_id"),
        "workflow_version": workflow.get("version"),
        "environment_id": environment_id,
    }

    # Score quality after policy and cost are available
    quality_score = score(result, journey_type)
    result["quality_score"] = quality_score

    # Persist
    save_run(
        run_id=run_id,
        tenant_id=ctx["tenant_id"],
        customer_id=ctx["customer_id"],
        journey=journey_type,
        input_data={"message": ctx["message"], "customer_id": ctx["customer_id"], "tenant_id": ctx["tenant_id"]},
        output_data=result,
        cost=run_cost.get("total_cost", 0),
        score=quality_score.get("overall", 0),
        workflow_id=workflow.get("workflow_id"),
        workflow_version=workflow.get("version"),
        environment_id=environment_id,
    )
    save_event(run_id, "journey_completed", {"journey": journey_type})

    # Analytics
    push({
        "run_id": run_id,
        "journey": journey_type,
        "customer_id": ctx["customer_id"],
        "tenant_id": ctx["tenant_id"],
    })

    log_event(trace_id, "journey_completed", {"journey": journey_type})

    return {
        "run_id": run_id,
        "journey": journey_type,
        "workflow": {
            "workflow_id": workflow.get("workflow_id"),
            "workflow_version": workflow.get("version"),
            "environment_id": environment_id,
        },
        "result": result,
    }


def _execute_journey(journey_type, ctx, run_id, trace_id):
    """Execute the appropriate plugin chain for the journey type."""
    handlers = {
        "discovery": _journey_discovery,
        "purchase": _journey_purchase,
        "post_purchase": _journey_post_purchase,
        "service": _journey_service,
        "engagement": _journey_engagement,
    }
    handler = handlers.get(journey_type, _journey_discovery)
    return handler(ctx, run_id, trace_id)


def _journey_discovery(ctx, run_id, trace_id):
    """Discovery journey: recommend products based on preferences."""
    log_event(trace_id, "discovery_started", {})

    # Get recommendations
    recs = catalog.recommend(ctx)
    products = recs.get("recommendations", [])

    # Price them
    price_ctx = {"products": products, "tenant_config": ctx.get("tenant_config")}
    priced = pricing.run(price_ctx)
    products = priced.get("products", [])

    # Apply promotions
    promo_ctx = {"products": products, "tenant_config": ctx.get("tenant_config")}
    promoted = promotions.run(promo_ctx)

    # Loyalty status
    loyalty_status = loyalty.get_status(ctx["customer_id"])

    log_event(trace_id, "discovery_completed", {"product_count": len(products)})

    return {
        "recommendations": promoted.get("products", []),
        "total_products": promoted.get("products", []).__len__(),
        "promo_savings_available": promoted.get("total_savings", 0),
        "active_promos": promoted.get("active_seasonal_promos", []),
        "loyalty": loyalty_status,
    }


def _journey_purchase(ctx, run_id, trace_id):
    """Purchase journey: pricing, promos, loyalty, checkout."""
    log_event(trace_id, "purchase_started", {})

    # Search/browse catalog
    query = ctx.get("query", ctx.get("message", ""))
    category = ctx.get("category")
    if category:
        catalog_result = catalog.get_by_category(category)
    else:
        catalog_result = catalog.search(query)

    products = catalog_result.get("products", [])[:5]  # Top 5

    # Price
    priced = pricing.run({"products": products, "tenant_config": ctx.get("tenant_config")})
    products = priced.get("products", [])

    # Promos
    promoted = promotions.run({"products": products, "tenant_config": ctx.get("tenant_config")})
    products = promoted.get("products", [])
    promo_savings = promoted.get("total_savings", 0)

    # Loyalty
    subtotal = sum(p.get("promo_price", p.get("price", 0)) for p in products)
    loyalty_result = loyalty.run({
        "customer_id": ctx["customer_id"],
        "subtotal": subtotal,
        "points_to_redeem": ctx.get("points_to_redeem", 0),
    })

    # Checkout
    cart = checkout.run({
        "products": products,
        "promo_savings": promo_savings,
        "loyalty": loyalty_result,
        "tenant_config": ctx.get("tenant_config"),
        "customer_id": ctx["customer_id"],
    })

    log_event(trace_id, "purchase_completed", {"cart_id": cart.get("cart_id")})

    return {
        "products": products,
        "promotions": {
            "savings": promo_savings,
            "applied": promoted.get("applied_promos", []),
        },
        "loyalty": loyalty_result,
        "cart": cart,
    }


def _journey_post_purchase(ctx, run_id, trace_id):
    """Post-purchase journey: order tracking."""
    log_event(trace_id, "post_purchase_started", {})

    order_id = ctx.get("order_id")
    customer_id = ctx["customer_id"]

    if order_id:
        tracking = orders.track(order_id)
    else:
        order_history = orders.run({"customer_id": customer_id})
        tracking = order_history

    log_event(trace_id, "post_purchase_completed", {})

    return {
        "order_info": tracking,
        "customer_id": customer_id,
    }


def _journey_service(ctx, run_id, trace_id):
    """Service journey: returns and refunds."""
    log_event(trace_id, "service_started", {})

    order_id = ctx.get("order_id")
    message = ctx.get("message", "").lower()

    result = {}

    if order_id or "return" in message or "refund" in message:
        # Try to extract order_id from message if not provided
        if not order_id:
            # Check customer's orders
            order_history = orders.run({"customer_id": ctx["customer_id"]})
            customer_orders = order_history.get("orders", [])
            if customer_orders:
                order_id = customer_orders[0]["order_id"]

        if order_id:
            return_result = returns.run({
                "order_id": order_id,
                "reason": ctx.get("message", "Customer request"),
                "condition": ctx.get("condition", "opened"),
            })
            result["return"] = return_result
        else:
            result["return"] = {"success": False, "error": "No orders found for this customer"}
    else:
        # General service inquiry
        order_history = orders.run({"customer_id": ctx["customer_id"]})
        result["orders"] = order_history

    log_event(trace_id, "service_completed", {})

    return result


def _journey_engagement(ctx, run_id, trace_id):
    """Engagement journey: feedback, referrals."""
    log_event(trace_id, "engagement_started", {})

    message = ctx.get("message", "").lower()
    customer_id = ctx["customer_id"]

    result = {"customer_id": customer_id}

    if "refer" in message or "referral" in message:
        referral_code = f"REF-{customer_id.upper()}-{uuid.uuid4().hex[:4].upper()}"
        result["referral"] = {
            "code": referral_code,
            "reward": "10% off next purchase for you and your friend",
            "share_link": f"https://shop.example.com/ref/{referral_code}",
        }
        # Bonus loyalty points for referral
        loyalty.add_points(customer_id, 50)
        result["loyalty_bonus"] = {"points_added": 50, "reason": "referral_generated"}

    if "feedback" in message or "review" in message or "rate" in message:
        result["feedback"] = {
            "status": "feedback_recorded",
            "message": "Thank you for your feedback! You've earned 25 loyalty points.",
        }
        loyalty.add_points(customer_id, 25)
        result["loyalty_bonus"] = result.get("loyalty_bonus", {})
        result["loyalty_bonus"]["points_added"] = result["loyalty_bonus"].get("points_added", 0) + 25
        result["loyalty_bonus"]["reason"] = result["loyalty_bonus"].get("reason", "") + " feedback_submitted"

    if not result.get("referral") and not result.get("feedback"):
        result["engagement"] = {
            "message": "How can we help you today? You can leave feedback, write a review, or refer a friend!",
            "options": ["leave_feedback", "write_review", "refer_friend", "view_loyalty"],
        }
        result["loyalty"] = loyalty.get_status(customer_id)

    log_event(trace_id, "engagement_completed", {})

    return result
