"""Prometheus metrics for ACOS."""

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

journey_requests_total = Counter(
    "acos_journey_requests_total",
    "Total journey requests",
    ["journey_type", "tenant_id", "status"],
)

journey_duration_seconds = Histogram(
    "acos_journey_duration_seconds",
    "Journey execution time in seconds",
    ["journey_type", "tenant_id"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

journey_cost_dollars = Histogram(
    "acos_journey_cost_dollars",
    "Cost per journey run in USD",
    ["journey_type", "tenant_id"],
    buckets=[0.0001, 0.001, 0.01, 0.05, 0.10, 0.50, 1.0],
)

api_errors_total = Counter(
    "acos_api_errors_total",
    "Total API errors by type",
    ["error_type", "endpoint"],
)

active_tenants = Gauge(
    "acos_active_tenants",
    "Number of tenants with activity in the last hour",
)

loyalty_points_redeemed_total = Counter(
    "acos_loyalty_points_redeemed_total",
    "Total loyalty points redeemed",
    ["tenant_id"],
)

tenant_limit_rejections_total = Counter(
    "acos_tenant_limit_rejections_total",
    "Total tenant traffic-control rejections",
    ["tenant_id", "limit_type"],
)


def metrics_endpoint():
    """Prometheus scrape endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def record_journey(
    journey_type: str,
    tenant_id: str,
    duration: float,
    cost: float,
    success: bool,
    points_redeemed: int = 0,
):
    """Record metrics for a completed journey."""
    status = "success" if success else "error"
    journey_requests_total.labels(
        journey_type=journey_type,
        tenant_id=tenant_id,
        status=status,
    ).inc()
    journey_duration_seconds.labels(
        journey_type=journey_type,
        tenant_id=tenant_id,
    ).observe(max(duration, 0))
    if cost > 0:
        journey_cost_dollars.labels(
            journey_type=journey_type,
            tenant_id=tenant_id,
        ).observe(cost)
    if points_redeemed > 0:
        loyalty_points_redeemed_total.labels(tenant_id=tenant_id).inc(points_redeemed)


def record_api_error(error_type: str, endpoint: str):
    api_errors_total.labels(error_type=error_type, endpoint=endpoint).inc()


def record_tenant_limit_rejection(tenant_id: str, limit_type: str) -> None:
    tenant_limit_rejections_total.labels(tenant_id=tenant_id, limit_type=limit_type).inc()
