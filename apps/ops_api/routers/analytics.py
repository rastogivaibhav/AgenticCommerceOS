from fastapi import APIRouter, Depends, Query
from acosplatform.auth.api_key import require_ops_token
from acosplatform.db.repository import get_runs

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/metrics")
async def get_metrics(range: str = Query("7d"), _token: dict = Depends(require_ops_token)):
    runs = get_runs(limit=1000)
    return {
        "totalRuns": len(runs),
        "avgScore": 8.7,
        "totalCost": 234.56,
        "successRate": 94.2,
    }

@router.get("/timeseries")
async def get_timeseries(range: str = Query("7d"), _token: dict = Depends(require_ops_token)):
    return [
        {"date": "Mon", "runs": 120, "cost": 45.2},
        {"date": "Tue", "runs": 145, "cost": 52.1},
    ]

@router.get("/workflows")
async def get_workflow_metrics(_token: dict = Depends(require_ops_token)):
    return [
        {"name": "Checkout", "runs": 450, "score": 9.1, "cost": 89.2},
        {"name": "Recommendation", "runs": 380, "score": 8.4, "cost": 71.5},
    ]

@router.get("/export")
async def export_analytics(format: str = Query("csv"), _token: dict = Depends(require_ops_token)):
    runs = get_runs(limit=10000)
    if format == "csv":
        import csv, io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['id', 'workflow', 'score', 'cost'])
        writer.writeheader()
        for run in runs:
            writer.writerow({
                'id': run['id'],
                'workflow': run.get('journey', ''),
                'score': run.get('score', 0),
                'cost': run.get('cost', 0),
            })
        return {"content": output.getvalue()}
    return runs
