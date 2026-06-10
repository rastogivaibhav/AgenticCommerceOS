from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from acosplatform.v2_store import get_v2_repository

NOW=lambda: datetime.now(timezone.utc).isoformat()

SEED_AGENTS: list[dict[str, Any]] = [
    {"agent_id":"shopping_agent","name":"Shopping Agent","description":"Finds, researches, compares and evaluates products for customer needs.","owner_team":"Digital Commerce","business_owner":"shopping-product-owner","technical_owner":"ai-platform","vendor_stack":"internal","status":"production","risk_level":"medium","supported_channels":["web","app","store_partner","contact_centre"],"capabilities":["shopping.find_products","shopping.compare_products","pricing.explain"],"tools":["catalog.search","catalog.get_product","catalog.compare_products","pricing.calculate","promotions.find_offers"],"tone_profile":"john_lewis_customer_direct","evaluation_score":0.91,"cost_budget_per_run":0.05,"fallback":"handoff_to_partner"},
    {"agent_id":"wismo_agent","name":"Where Is My Order Agent","description":"Tracks orders and investigates delivery issues.","owner_team":"Fulfilment","business_owner":"fulfilment-lead","technical_owner":"ai-platform","vendor_stack":"internal","status":"production","risk_level":"medium","supported_channels":["web","app","store_partner","contact_centre"],"capabilities":["order.track","order.investigate_delay"],"tools":["order.lookup","order.history","order.track","case.create"],"tone_profile":"john_lewis_policy_sensitive","evaluation_score":0.93,"cost_budget_per_run":0.04,"fallback":"contact_centre_handoff"},
    {"agent_id":"returns_agent","name":"Returns Agent","description":"Checks returns eligibility and supports return creation.","owner_team":"Customer Service","business_owner":"returns-policy-owner","technical_owner":"ai-platform","vendor_stack":"internal","status":"production","risk_level":"high","supported_channels":["web","app","store_partner","contact_centre"],"capabilities":["returns.check_eligibility","returns.create_return"],"tools":["order.lookup","returns.check_eligibility","returns.create_return","case.create"],"tone_profile":"john_lewis_policy_sensitive","evaluation_score":0.94,"cost_budget_per_run":0.06,"fallback":"human_approval"},
    {"agent_id":"mattress_recommender","name":"Mattress Recommender","description":"Recommends mattresses based on sleep style, budget, size, comfort and delivery needs.","owner_team":"Home Category","business_owner":"home-category-lead","technical_owner":"ai-platform","vendor_stack":"internal","status":"production","risk_level":"medium","supported_channels":["web","app","store_partner","contact_centre"],"capabilities":["mattress.recommend","shopping.compare_products","delivery.check"],"tools":["catalog.search","catalog.compare_products","inventory.check_stock","pricing.calculate"],"tone_profile":"john_lewis_premium_advisor","evaluation_score":0.91,"cost_budget_per_run":0.05,"fallback":"shopping_agent"},
    {"agent_id":"nursery_advisor","name":"Nursery Advisor","description":"Advises on nursery products with safety-aware wording and customer context.","owner_team":"Nursery Category","business_owner":"nursery-category-lead","technical_owner":"ai-platform","vendor_stack":"internal","status":"pilot","risk_level":"high","supported_channels":["web","app","store_partner","contact_centre"],"capabilities":["nursery.advise"],"tools":["catalog.search","inventory.check_stock","case.create"],"tone_profile":"john_lewis_policy_sensitive","evaluation_score":0.89,"cost_budget_per_run":0.07,"fallback":"human_handoff"},
    {"agent_id":"gift_advisor","name":"Gift Advisor","description":"Suggests gifts based on occasion, recipient and budget.","owner_team":"Gifting","business_owner":"gifting-lead","technical_owner":"ai-platform","vendor_stack":"internal","status":"draft","risk_level":"low","supported_channels":["web","app","store_partner"],"capabilities":["gift.recommend","shopping.find_products"],"tools":["catalog.search","pricing.calculate","promotions.find_offers"],"tone_profile":"john_lewis_customer_direct","evaluation_score":0.82,"cost_budget_per_run":0.05,"fallback":"shopping_agent"},
]

class AgentRegistry:
    def __init__(self, tenant_id: str='default'):
        self.tenant_id=tenant_id
        self.repo=get_v2_repository()
        self._seed_if_empty()
    def _seed_if_empty(self):
        if self.repo.list_json('v2_agents', self.tenant_id):
            return
        for a in SEED_AGENTS:
            payload=dict(a, created_at=NOW(), updated_at=NOW(), version='1.0.0')
            self.repo.upsert_json('v2_agents', payload['agent_id'], payload, self.tenant_id, payload.get('status'))
            self.repo.set_route_stage(payload['agent_id'], 'production' if payload['status']=='production' else payload['status'], {'seeded': True, 'evaluation_score': payload.get('evaluation_score')}, self.tenant_id)
            for c in payload.get('capabilities',[]):
                self.repo.map_capability(payload['agent_id'], c, self.tenant_id)
    def list_agents(self, status: str|None=None):
        vals=self.repo.list_json('v2_agents', self.tenant_id)
        if status: vals=[a for a in vals if a.get('status')==status]
        return vals
    def get_agent(self, agent_id: str): return self.repo.get_json('v2_agents', agent_id, self.tenant_id)
    def upsert_agent(self, payload: dict[str, Any]):
        aid=payload.get('agent_id') or payload.get('id') or payload.get('name','agent').lower().replace(' ','_')
        base={"agent_id": aid, "name": aid.replace('_',' ').title(), "status":"draft", "risk_level":"medium", "supported_channels":["web"], "capabilities":[], "tools":[], "vendor_stack":"internal", "evaluation_score":0.0, "created_at":NOW(), "fallback":"human_handoff"}
        existing=self.get_agent(aid) or {}
        base.update(existing); base.update(payload); base['agent_id']=aid; base['updated_at']=NOW()
        self.repo.upsert_json('v2_agents', aid, base, self.tenant_id, base.get('status'))
        for c in base.get('capabilities',[]): self.repo.map_capability(aid,c,self.tenant_id)
        return base
    def agent_card(self, agent_id: str):
        a=self.get_agent(agent_id)
        if not a: return None
        return {"agent_id":a['agent_id'],"name":a['name'],"description":a.get('description'),"service_endpoint":f"/api/v2/a2a/agents/{a['agent_id']}","skills":[{"skill_id":c,"description":c.replace('.',' '),"input_schema_ref":f"schema://{c}/input","output_schema_ref":f"schema://{c}/output"} for c in a.get('capabilities',[])],"capabilities":{"streaming":False,"long_running_tasks":True,"human_handoff":True},"supported_channels":a.get('supported_channels',[]),"risk_level":a.get('risk_level'),"vendor_stack":a.get('vendor_stack'),"auth":{"type":"acos_api_key"},"status":a.get('status'),"owner_team":a.get('owner_team'),"kill_switch": bool(a.get('kill_switch', False))}
    def create_version(self, agent_id: str, payload: dict[str,Any]):
        agent=self.get_agent(agent_id)
        if not agent: return None
        version=payload.get('version') or f"v{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        record={"version_id":"av_"+uuid4().hex[:12],"agent_id":agent_id,"version":version,"status":"draft","payload":payload,"created_at":NOW()}
        self.repo.insert_task({"task_id":record['version_id'],"tenant_id":self.tenant_id,"agent_id":agent_id,"capability_id":"agent.version","status":"created","request":payload,"response":record})
        return record
    def promote(self, agent_id: str, target_stage='production'):
        agent=self.get_agent(agent_id)
        if not agent: return {"status":"rejected","reason":"agent_not_found"}
        missing=[]
        for field in ['owner_team','capabilities','supported_channels','tools','risk_level','fallback']:
            if not agent.get(field): missing.append(field)
        if float(agent.get('evaluation_score') or 0) < 0.85: missing.append('evaluation_score>=0.85')
        if missing:
            return {"status":"rejected","agent_id":agent_id,"missing":missing,"stage":"blocked"}
        agent['status']='production' if target_stage=='production' else target_stage
        agent['updated_at']=NOW()
        self.repo.upsert_json('v2_agents', agent_id, agent, self.tenant_id, agent['status'])
        self.repo.set_route_stage(agent_id, agent['status'], {"approved": True, "gate_checks":"passed"}, self.tenant_id)
        return {"status":"promoted","agent":agent,"stage":agent['status']}
    def retire(self, agent_id: str):
        agent=self.get_agent(agent_id)
        if not agent: return None
        agent['status']='retired'; agent['updated_at']=NOW()
        self.repo.upsert_json('v2_agents', agent_id, agent, self.tenant_id, 'retired')
        self.repo.set_route_stage(agent_id, 'retired', {"retired": True}, self.tenant_id)
        return agent
REGISTRY=AgentRegistry()
