from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from acosplatform.agents.registry import REGISTRY
from acosplatform.v2_store import get_v2_repository
NOW=lambda: datetime.now(timezone.utc).isoformat()

def list_evaluations():
    return [{'agent_id':a['agent_id'],'agent_name':a['name'],'score':a.get('evaluation_score',0),'threshold':0.85 if a.get('risk_level')!='high' else 0.90,'status':'pass' if a.get('evaluation_score',0)>= (0.90 if a.get('risk_level')=='high' else 0.85) else 'needs_work','dimensions':{'brand_tone':0.9,'tool_use':0.88,'policy_compliance':0.92}} for a in REGISTRY.list_agents()]
def split_recommendations():
    return [{'source_agent':'shopping_agent','recommended_specialist':'beauty_advisor','reason':'category performance lag in beauty/cosmetics test set','confidence':0.72}]
def run_evaluation(agent_id='shopping_agent', tenant_id='default'):
    a=REGISTRY.get_agent(agent_id) or {}
    score=float(a.get('evaluation_score') or 0.80)
    threshold=0.90 if a.get('risk_level')=='high' else 0.85
    run={'run_id':'eval_'+uuid4().hex[:10],'tenant_id':tenant_id,'agent_id':agent_id,'score':score,'threshold':threshold,'status':'pass' if score>=threshold else 'fail','created_at':NOW(),'cases_run':12,'failures':[] if score>=threshold else ['score_below_threshold']}
    return get_v2_repository().insert_eval_run(run)
def list_evaluation_runs(tenant_id='default'):
    rows=get_v2_repository().list_eval_runs(tenant_id)
    return rows or [run_evaluation('mattress_recommender', tenant_id)]
def get_evaluation_run(run_id, tenant_id='default'):
    return get_v2_repository().get_eval_run(run_id, tenant_id)
