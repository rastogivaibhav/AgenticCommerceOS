from acosplatform.agents.registry import REGISTRY
STAGES=['draft','local_test','evaluation','safety_review','business_approval','pilot','production','monitor','retire']
def route_summary():
 return [{'agent_id':a['agent_id'],'agent_name':a['name'],'current_stage':'production' if a.get('status')=='production' else ('pilot' if a.get('status')=='pilot' else 'draft'),'required_evidence':['owner','capabilities','tools','evaluation_score','fallback','approval_record'],'ready_for_production': bool(a.get('owner_team') and a.get('capabilities') and a.get('evaluation_score',0)>0.88)} for a in REGISTRY.list_agents()]
