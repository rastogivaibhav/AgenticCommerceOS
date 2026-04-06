# apps/ops_api/models/analytics.py
from pydantic import BaseModel
from typing import List, Dict, Optional


class KPIData(BaseModel):
    run_volume: int
    success_rate: float
    completion_rate: float
    avg_resolution_time_ms: int


class KPISegment(BaseModel):
    workflow_id: str
    metrics: KPIData


class KPIResponse(BaseModel):
    segments: Optional[List[KPISegment]] = None
    data: Optional[KPIData] = None
