from fastapi import APIRouter, Depends
from acosplatform.auth.api_key import require_ops_token
import uuid

router = APIRouter(prefix="/experiments", tags=["experiments"])

@router.post("")
async def create_experiment(experiment: dict, _token: dict = Depends(require_ops_token)):
    return {
        "id": str(uuid.uuid4()),
        "name": experiment.get("name"),
        "status": "running",
        "createdAt": "2026-03-22T00:00:00Z"
    }

@router.get("/{experiment_id}/results")
async def get_results(experiment_id: str, _token: dict = Depends(require_ops_token)):
    # Return mock results
    return [
        {"variant": "a", "score": 8.5, "cost": 10.5},
        {"variant": "b", "score": 9.1, "cost": 11.2},
    ]

@router.post("/{experiment_id}/run")
async def run_experiment(experiment_id: str, variant: dict, _token: dict = Depends(require_ops_token)):
    return {"experiment_id": experiment_id, "status": "running"}
