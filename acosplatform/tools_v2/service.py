from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from acosplatform.v2_store import get_v2_repository
NOW=lambda: datetime.now(timezone.utc).isoformat()
SEED_TOOLS=[
 {'tool_id':'catalog.search','name':'Product Search','protocol':'MCP/REST','owner':'Digital Commerce','risk_level':'low','allowed_agents':['shopping_agent','mattress_recommender','nursery_advisor','gift_advisor'],'allowed_channels':['web','app','store_partner','contact_centre'],'cost_class':'low','data_classification':'public','approval_required':False,'status':'active'},
 {'tool_id':'inventory.check_stock','name':'Stock Check','protocol':'REST','owner':'Fulfilment','risk_level':'low','allowed_agents':['shopping_agent','mattress_recommender','nursery_advisor'],'allowed_channels':['web','app','store_partner','contact_centre'],'cost_class':'low','data_classification':'internal','approval_required':False,'status':'active'},
 {'tool_id':'order.lookup','name':'Order Lookup','protocol':'REST','owner':'Fulfilment','risk_level':'medium','allowed_agents':['wismo_agent','returns_agent'],'allowed_channels':['web','app','store_partner','contact_centre'],'cost_class':'medium','data_classification':'customer','approval_required':False,'status':'active'},
 {'tool_id':'returns.create_return','name':'Create Return','protocol':'REST','owner':'Customer Service','risk_level':'high','allowed_agents':['returns_agent'],'allowed_channels':['web','app','contact_centre'],'cost_class':'medium','data_classification':'customer','approval_required':True,'status':'active'},
]
SEED_MCP=[{'server_id':'retail_tool_gateway','name':'Retail Tool Gateway','transport':'streamable_http','endpoint':'/mcp','status':'active','allowed_tools':[t['tool_id'] for t in SEED_TOOLS]}]
class ToolRegistry:
 def __init__(self, tenant_id='default'):
  self.tenant_id=tenant_id; self.repo=get_v2_repository(); self.seed()
 def seed(self):
  if not self.repo.list_json('v2_tools', self.tenant_id):
   for t in SEED_TOOLS: self.repo.upsert_json('v2_tools', t['tool_id'], t, self.tenant_id, t['status'])
  if not self.repo.list_json('v2_mcp_servers', self.tenant_id):
   for s in SEED_MCP: self.repo.upsert_json('v2_mcp_servers', s['server_id'], s, self.tenant_id, s['status'])
 def list_tools(self): return self.repo.list_json('v2_tools', self.tenant_id)
 def upsert_tool(self,payload:dict[str,Any]):
  tid=payload.get('tool_id') or payload.get('id') or payload.get('name','tool').lower().replace(' ','.')
  item={'tool_id':tid,'status':'active','risk_level':'medium','allowed_agents':[],**payload,'updated_at':NOW()}
  return self.repo.upsert_json('v2_tools', tid, item, self.tenant_id, item['status'])
 def list_mcp_servers(self): return self.repo.list_json('v2_mcp_servers', self.tenant_id)
 def upsert_mcp_server(self,payload):
  sid=payload.get('server_id') or payload.get('id') or payload.get('name','mcp_server').lower().replace(' ','_')
  item={'server_id':sid,'transport':'streamable_http','status':'active',**payload,'updated_at':NOW()}
  return self.repo.upsert_json('v2_mcp_servers', sid, item, self.tenant_id, item['status'])
TOOLS=ToolRegistry()
