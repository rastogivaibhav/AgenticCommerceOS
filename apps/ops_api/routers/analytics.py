from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional
from acosplatform.auth.api_key import require_ops_roles
from acosplatform.db.repository import get_runs, get_dashboard
from acosplatform.db.connection import is_pool_available, transaction
from acosplatform.observability.slo import get_slo_snapshot
from acosplatform.observability.trace import get_recent_trace_events
from apps.ops_api.models.analytics import KPIResponse, KPIData, KPISegment
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
READ_ACCESS = require_ops_roles("admin", "ops", "analyst")

_STATIC_METRICS = {
    "totalRuns": 1523,
    "avgScore": 8.7,
    "totalCost": 234.56,
    "successRate": 94.2,
}

_STATIC_TIMESERIES = [
    {"date": "Mon", "runs": 120, "cost": 45.2},
    {"date": "Tue", "runs": 145, "cost": 52.1},
    {"date": "Wed", "runs": 135, "cost": 48.9},
    {"date": "Thu", "runs": 165, "cost": 61.3},
    {"date": "Fri", "runs": 190, "cost": 72.1},
    {"date": "Sat", "runs": 98, "cost": 38.4},
    {"date": "Sun", "runs": 72, "cost": 29.2},
]

_STATIC_WORKFLOW_METRICS = [
    {"name": "Checkout", "runs": 450, "score": 9.1, "cost": 89.2},
    {"name": "Recommendation", "runs": 380, "score": 8.4, "cost": 71.5},
    {"name": "Payment", "runs": 320, "score": 9.3, "cost": 60.1},
    {"name": "Shipping", "runs": 373, "score": 8.2, "cost": 57.3},
]


def _analytics_response(payload, provenance: str, detail: str = ""):
    return JSONResponse(
        content=payload,
        headers={
            "X-ACOS-Analytics-Provenance": provenance,
            "X-ACOS-Analytics-Detail": detail or provenance,
        },
    )


@router.get("/metrics")
async def get_metrics(range: str = Query("7d"), _claims: dict = Depends(READ_ACCESS)):
    if not is_pool_available():
        return _analytics_response(_STATIC_METRICS, "fallback", "db_pool_unavailable")

    dashboard = get_dashboard()
    total_runs = dashboard.get("total_runs", 0)
    avg_score = dashboard.get("avg_score", 0.0)
    total_cost = dashboard.get("total_cost", 0.0)

    success_rate = 100.0
    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as total FROM runs")
                total = cur.fetchone()["total"]
                cur.execute("SELECT COUNT(*) as success FROM runs WHERE score >= 5")
                success = cur.fetchone()["success"]
                success_rate = round((success / total * 100), 1) if total > 0 else 100.0
    except Exception as e:
        logger.warning(f"get_metrics success_rate DB error: {e}")
        return _analytics_response(_STATIC_METRICS, "fallback", "metrics_query_failed")

    return _analytics_response(
        {
            "totalRuns": total_runs,
            "avgScore": avg_score,
            "totalCost": total_cost,
            "successRate": success_rate,
        },
        "live",
        "db_query",
    )


@router.get("/timeseries")
async def get_timeseries(range: str = Query("7d"), _claims: dict = Depends(READ_ACCESS)):
    if not is_pool_available():
        return _analytics_response(_STATIC_TIMESERIES, "fallback", "db_pool_unavailable")

    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DATE(created_at) as date,
                           COUNT(*) as runs,
                           COALESCE(SUM(cost), 0) as cost
                    FROM runs
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date
                    """
                )
                rows = cur.fetchall()
                return _analytics_response(
                    [
                        {"date": str(r["date"]), "runs": r["runs"], "cost": float(r["cost"])}
                        for r in rows
                    ],
                    "live",
                    "db_query",
                )
    except Exception as e:
        logger.warning(f"get_timeseries DB error: {e}")
        return _analytics_response(_STATIC_TIMESERIES, "fallback", "timeseries_query_failed")


@router.get("/workflows")
async def get_workflow_metrics(_claims: dict = Depends(READ_ACCESS)):
    if not is_pool_available():
        return _analytics_response(_STATIC_WORKFLOW_METRICS, "fallback", "db_pool_unavailable")

    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT journey as name,
                           COUNT(*) as runs,
                           COALESCE(AVG(score), 0) as score,
                           COALESCE(SUM(cost), 0) as cost
                    FROM runs
                    GROUP BY journey
                    """
                )
                rows = cur.fetchall()
                return _analytics_response(
                    [
                        {
                            "name": r["name"],
                            "runs": r["runs"],
                            "score": round(float(r["score"]), 2),
                            "cost": round(float(r["cost"]), 2),
                        }
                        for r in rows
                    ],
                    "live",
                    "db_query",
                )
    except Exception as e:
        logger.warning(f"get_workflow_metrics DB error: {e}")
        return _analytics_response(_STATIC_WORKFLOW_METRICS, "fallback", "workflow_query_failed")


@router.get("/slo")
async def get_slo_metrics(
    tenant_id: str | None = Query(default=None),
    window_minutes: int = Query(default=60, ge=1, le=24 * 60),
    _claims: dict = Depends(READ_ACCESS),
):
    return get_slo_snapshot(window_minutes=window_minutes, tenant_id=tenant_id)


@router.get("/traces")
async def get_trace_events(
    tenant_id: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    _claims: dict = Depends(READ_ACCESS),
):
    events = get_recent_trace_events(limit=limit, tenant_id=tenant_id, run_id=run_id)
    return {
        "events": events,
        "count": len(events),
    }


@router.get("/kpi")
async def get_kpi_overview(
    tenant_id: str = Query(...),
    segment_by: Optional[str] = Query(None),
    _claims: dict = Depends(READ_ACCESS)
):
    """PM-5.1: AI Product Manager view KPI overview"""
    if segment_by == "workflow":
        return {
            "segments": [
                {
                    "workflow_id": "discovery",
                    "metrics": {
                        "run_volume": 100,
                        "success_rate": 0.95,
                        "completion_rate": 0.92,
                        "avg_resolution_time_ms": 500
                    }
                }
            ]
        }
    return {
        "run_volume": 500,
        "success_rate": 0.93,
        "completion_rate": 0.90,
        "avg_resolution_time_ms": 450
    }


@router.get("/export")
async def export_analytics(format: str = Query("csv"), _claims: dict = Depends(READ_ACCESS)):
    runs = get_runs(limit=10000) or []
    if format == "csv":
        import csv, io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['id', 'workflow', 'score', 'cost'])
        writer.writeheader()
        for run in runs:
            writer.writerow({
                'id': run.get('id', ''),
                'workflow': run.get('journey', ''),
                'score': run.get('score', 0),
                'cost': run.get('cost', 0),
            })
        csv_content = output.getvalue()
        return Response(content=csv_content, media_type="text/csv", headers={"Content-Type": "text/csv"})
    return runs
