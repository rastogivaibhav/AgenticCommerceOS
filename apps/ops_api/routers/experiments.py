from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from acosplatform.auth.api_key import require_ops_token
from acosplatform.db.repository import get_experiments
from acosplatform.evaluation.scorer import run_ab_test
from acosplatform.journey.engine import run_journey

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
def list_experiments():
    return {"experiments": get_experiments()}


@router.post("")
def create_experiment(body: dict, _token: dict = Depends(require_ops_token)):
    name = body["name"]
    payload = {
        "message": body["message"],
        "customer_id": body["customer_id"],
        "tenant_id": body["tenant_id"],
    }
    result = run_ab_test(
        experiment_name=name,
        payload=payload,
        run_func=run_journey,
    )
    return result


@router.get("/{experiment_id}/results")
def get_experiment_results(experiment_id: str):
    try:
        eid = int(experiment_id)
    except ValueError:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    experiments = get_experiments()
    record = next((e for e in experiments if e.get("id") == eid), None)
    if not record:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"experiment": record}
