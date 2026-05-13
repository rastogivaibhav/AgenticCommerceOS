from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from acosplatform.v2_store import get_v2_repository
from acosplatform.agents.registry import REGISTRY
NOW=lambda: datetime.now(timezone.utc).isoformat()
CAPABILITIES=[
 {"capability_id":"shopping.find_products","name":"Find Products","intent_families":["product_discovery","shopping"],"owner":"Digital Commerce","risk_level":"low","evaluation_threshold":0.85},
 {"capability_id":"shopping.compare_products","name":"Compare Products","intent_families":["product_discovery"],"owner":"Digital Commerce","risk_level":"low","evaluation_threshold":0.85},
 {"capability_id":"pricing.explain","name":"Explain Pricing","intent_families":["price_or_promotion"],"owner":"Commercial","risk_level":"low","evaluation_threshold":0.85},
 {"capability_id":"delivery.check","name":"Check Delivery","intent_families":["stock_availability","delivery_issue"],"owner":"Fulfilment","risk_level":"medium","evaluation_threshold":0.88},
 {"capability_id":"order.track","name":"Track Order","intent_families":["order_status","delivery_issue"],"owner":"Fulfilment","risk_level":"medium","evaluation_threshold":0.90},
 {"capability_id":"returns.check_eligibility","name":"Check Return Eligibility","intent_families":["return_or_refund"],"owner":"Customer Service","risk_level":"high","evaluation_threshold":0.92},
 {"capability_id":"returns.create_return","name":"Create Return","intent_families":["return_or_refund"],"owner":"Customer Service","risk_level":"high","evaluation_threshold":0.95},
 {"capability_id":"mattress.recommend","name":"Recommend Mattress","intent_families":["mattress_recommendation","shopping"],"owner":"Home Category","risk_level":"medium","evaluation_threshold":0.88},
 {"capability_id":"nursery.advise","name":"Nursery Advice","intent_families":["nursery_advice"],"owner":"Nursery Category","risk_level":"high","evaluation_threshold":0.90},
 {"capability_id":"gift.recommend","name":"Gift Recommendation","intent_families":["gift_advice"],"owner":"Gifting","risk_level":"low","evaluation_threshold":0.84},
]
class CapabilityRegistry:
 def __init__(self, tenant_id='default'):
  self.tenant_id=tenant_id; self.repo=get_v2_repository(); self._seed_if_empty()
 def _seed_if_empty(self):
  if not self.repo.list_json('v2_capabilities', self.tenant_id):
   for c in CAPABILITIES: self.repo.upsert_json('v2_capabilities', c['capability_id'], dict(c,created_at=NOW()), self.tenant_id)
 def list_capabilities(self):
  agents=REGISTRY.list_agents(); out=[]
  for c in self.repo.list_json('v2_capabilities', self.tenant_id):
   mapped=[a['agent_id'] for a in agents if c['capability_id'] in a.get('capabilities',[])]
   out.append(dict(c, mapped_agents=mapped, coverage_status='covered' if mapped else 'gap'))
  return out
 def upsert(self,payload:dict[str,Any]):
  cid=payload.get('capability_id') or payload.get('id') or payload.get('name','capability').lower().replace(' ','.')
  item={"capability_id":cid,"name":cid,"intent_families":[],"owner":"unassigned","risk_level":"medium","evaluation_threshold":0.85,**payload,"updated_at":NOW()}
  self.repo.upsert_json('v2_capabilities', cid, item, self.tenant_id)
  return item
 def map_agent(self, capability_id:str, agent_id:str):
  self.repo.map_capability(agent_id, capability_id, self.tenant_id)
 def coverage(self):
  caps=self.list_capabilities()
  gaps=[c for c in caps if c.get('coverage_status')=='gap']
  dupes=[c for c in caps if len(c.get('mapped_agents',[]))>1]
  return {"total":len(caps),"covered":len(caps)-len(gaps),"gaps":gaps,"duplicate_capabilities":dupes}
 def resolve(self, text:str, intent: str|None=None):
  lower=(text or '').lower(); caps=[]
  if any(w in lower for w in ['cot','newborn','nursery']): caps += ['nursery.advise']
  if 'mattress' in lower: caps += ['mattress.recommend','shopping.find_products']
  if any(w in lower for w in ['return','refund','previous order']): caps += ['returns.check_eligibility','order.track']
  if any(w in lower for w in ['gift','present']): caps += ['gift.recommend']
  if not caps: caps=['shopping.find_products']
  agents=[]
  for a in REGISTRY.list_agents():
   if any(c in a.get('capabilities',[]) for c in caps) and not a.get('kill_switch'): agents.append(a)
  return {"required_capabilities":list(dict.fromkeys(caps)),"resolved_agents":agents,"coverage":"covered" if agents else "gap"}
CAPABILITY_REGISTRY=CapabilityRegistry()
