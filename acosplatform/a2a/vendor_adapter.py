from __future__ import annotations
from typing import Any
from acosplatform.v2_store import get_v2_repository

SEED_VENDOR = {
    'vendor_beauty_advisor': {
        'vendor_agent_id': 'vendor_beauty_advisor',
        'name': 'Vendor Beauty Advisor',
        'vendor': 'mock_vendor',
        'endpoint': 'mock://beauty-advisor',
        'allowed_capabilities': ['beauty.advise','shopping.find_products'],
        'allowed_tools': ['catalog.search'],
        'enabled': True,
        'kill_switch': False,
        'evaluation_threshold': 0.88,
        'cost_budget_per_run': 0.04,
        'auth_method': 'mock_signed_request',
    }
}
class VendorAgentRegistry:
    def __init__(self, tenant_id='default'):
        self.tenant_id=tenant_id; self.repo=get_v2_repository(); self._seed()
    def _seed(self):
        if not self.repo.list_json('v2_vendor_agents', self.tenant_id):
            for k,v in SEED_VENDOR.items(): self.repo.upsert_json('v2_vendor_agents', k, v, self.tenant_id)
    def list(self): return self.repo.list_json('v2_vendor_agents', self.tenant_id)
    def register(self, payload:dict[str,Any]):
        vid=payload.get('vendor_agent_id') or payload.get('id') or payload.get('name','vendor_agent').lower().replace(' ','_')
        base={'vendor_agent_id':vid,'enabled':True,'kill_switch':False,'allowed_capabilities':[],'allowed_tools':[],'cost_budget_per_run':0.05, **payload}
        self.repo.upsert_json('v2_vendor_agents', vid, base, self.tenant_id)
        return base
    def kill(self, vendor_agent_id:str, enabled:bool=False):
        agent=self.repo.get_json('v2_vendor_agents', vendor_agent_id, self.tenant_id)
        if not agent: return None
        agent['kill_switch']=not enabled; agent['enabled']=enabled
        self.repo.upsert_json('v2_vendor_agents', vendor_agent_id, agent, self.tenant_id)
        return agent
    def invoke(self, vendor_agent_id:str, message:str):
        agent=self.repo.get_json('v2_vendor_agents', vendor_agent_id, self.tenant_id)
        if not agent or agent.get('kill_switch') or not agent.get('enabled'):
            return {'status':'blocked','reason':'vendor_agent_disabled_or_not_found','vendor_agent_id':vendor_agent_id}
        return {'status':'completed','vendor_agent_id':vendor_agent_id,'response':f"{agent.get('name','Vendor agent')} response for: {message}", 'confidence':0.87}
VENDOR_REGISTRY = VendorAgentRegistry()
