from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any
import os
from acosplatform.capabilities.registry import CAPABILITY_REGISTRY
from acosplatform.agents.registry import REGISTRY
from acosplatform.v2_store import get_v2_repository
from acosplatform.a2a.response_merge import merge_responses
from acosplatform.a2a.vendor_adapter import VENDOR_REGISTRY
NOW=lambda: datetime.now(timezone.utc).isoformat()
repo=get_v2_repository()
CHANNEL_MODES={
 'customer_direct': {'label':'Customer direct','visibility':'customer_safe','include_advisor_notes':False},
 'store_partner_assist': {'label':'Store Partner assist','visibility':'partner_assist','include_advisor_notes':True},
 'contact_centre_assist': {'label':'Contact centre assist','visibility':'case_safe','include_advisor_notes':True},
 'internal_ops': {'label':'Internal ops','visibility':'diagnostic','include_advisor_notes':True},
}
TONE_PROFILES=[
 {'id':'john_lewis_customer_direct','name':'Helpful customer direct','rules':['warm','clear','no internal details']},
 {'id':'john_lewis_partner_assist','name':'Partner assist','rules':['advisor notes','questions to ask','confidence']},
 {'id':'john_lewis_policy_sensitive','name':'Policy sensitive','rules':['accurate boundaries','safe wording','escalate uncertainty']},
 {'id':'john_lewis_premium_advisor','name':'Premium advisor','rules':['expert','reassuring','comparative rationale']},
 {'id':'john_lewis_apology_recovery','name':'Apology recovery','rules':['empathetic','ownership','next best action']},
]
POLICY_BUDGET_PER_RUN=0.50

def _agent_response(agent:dict[str,Any], message:str, mode:str):
 aid=agent['agent_id']
 if aid=='nursery_advisor': text='Nursery Advisor: for a newborn, prioritise a firm, flat cot mattress with breathable washable cover and correct cot-bed fit.'
 elif aid=='mattress_recommender': text='Mattress Recommender: select cot mattresses under £250, compare firmness, safety fit and delivery availability.'
 elif aid=='returns_agent': text='Returns Agent: check the previous nursery order against return window, condition and proof-of-purchase policy before creating a return.'
 elif aid=='wismo_agent': text='WISMO Agent: use order history to verify delivery status and identify any delay or return dependency.'
 elif aid=='shopping_agent': text='Shopping Agent: search and compare suitable nursery mattresses and options within the stated budget.'
 else: text=f"{agent['name']}: search and compare suitable products based on the customer need."
 if mode.endswith('partner_assist'):
  text += ' Partner note: ask the customer about cot size, delivery postcode, and whether packaging is unopened.'
 return {"agent_id":aid,"agent_name":agent['name'],"status":"completed","response":text,"confidence":agent.get('evaluation_score',0.85),"artifacts":[{"type":"summary","text":text}]}

def _policy_check(agent, tool_count, tenant_id):
    cost=float(agent.get('cost_budget_per_run') or 0.05) + tool_count*0.002
    if cost > POLICY_BUDGET_PER_RUN:
        return {'verdict':'deny','policy_id':'cost_budget','cost':cost}
    if agent.get('risk_level') == 'high' and 'returns.create_return' in agent.get('tools',[]):
        return {'verdict':'allow_with_human_approval','policy_id':'high_risk_action','cost':cost}
    return {'verdict':'allow','policy_id':'standard_agent_invocation','cost':cost}

def invoke_a2a(message: str, tenant_id='default', customer_id='demo-customer', channel='web', actor_type='customer', channel_mode='customer_direct', vendor_agent_id: str|None=None):
 resolved=CAPABILITY_REGISTRY.resolve(message)
 agents=resolved['resolved_agents']
 desired=['nursery_advisor','mattress_recommender','shopping_agent','wismo_agent','returns_agent','gift_advisor']
 ordered=[]
 for aid in desired:
  a=REGISTRY.get_agent(aid)
  if a and a in agents: ordered.append(a)
 for a in agents:
  if a not in ordered: ordered.append(a)
 trace_id='a2a_'+uuid4().hex[:12]
 steps=[]; responses=[]; tasks=[]; policy_decisions=[]; total_cost=0.0
 tools=[]
 for tool in ['catalog.search','inventory.check_stock','order.lookup','returns.check_eligibility']:
  if ('return' in message.lower() or tool not in ['order.lookup','returns.check_eligibility']):
   tools.append({'tool':tool,'status':'success','protocol':'mcp_or_rest','latency_ms':42+len(tools)*11,'policy_verdict':'allow'})
 for seq,a in enumerate(ordered, start=1):
  pol=_policy_check(a, len(tools), tenant_id); total_cost += pol['cost']; policy_decisions.append({'agent_id':a['agent_id'], **pol})
  if pol['verdict']=='deny':
   steps.append({'sequence':seq,'type':'agent_blocked','agent_id':a['agent_id'],'policy':pol,'status':'blocked','timestamp':NOW()}); continue
  task_id='task_'+uuid4().hex[:10]
  task={'task_id':task_id,'trace_id':trace_id,'tenant_id':tenant_id,'agent_id':a['agent_id'],'capability_id':next((c for c in a.get('capabilities',[]) if c in resolved['required_capabilities']), a.get('capabilities',['agent'])[0]),'status':'started','request':{'message':message,'channel_mode':channel_mode}}
  repo.insert_task(task)
  steps.append({'sequence':seq,'type':'agent_call','agent_id':a['agent_id'],'agent_name':a['name'],'task_id':task_id,'status':'started','timestamp':NOW()})
  resp=_agent_response(a,message,channel_mode); responses.append(resp)
  task['status']='completed'; task['response']=resp; repo.insert_task(task); tasks.append(task)
  steps.append({'sequence':seq,'type':'agent_response','agent_id':a['agent_id'],'task_id':task_id,'status':'completed','response_preview':resp['response'][:180],'timestamp':NOW()})
 if vendor_agent_id:
  vresp=VENDOR_REGISTRY.invoke(vendor_agent_id, message)
  steps.append({'sequence':len(steps)+1,'type':'vendor_agent_call','vendor_agent_id':vendor_agent_id,'status':vresp.get('status'),'timestamp':NOW()})
  if vresp.get('status')=='completed': responses.append({'agent_id':vendor_agent_id,'agent_name':vendor_agent_id,'response':vresp['response'],'status':'completed','confidence':vresp.get('confidence')})
 final=merge_responses(responses,channel_mode)
 trace={'trace_id':trace_id,'tenant_id':tenant_id,'customer_id':customer_id,'channel':channel,'actor_type':actor_type,'channel_mode':channel_mode,'message':message,'required_capabilities':resolved['required_capabilities'],'agents':[{'agent_id':a['agent_id'],'name':a['name']} for a in ordered],'tasks':[{'task_id':t['task_id'],'agent_id':t['agent_id'],'status':t['status']} for t in tasks],'steps':steps,'tool_trace':tools,'policy_decisions':policy_decisions,'memory_access':[{'scope':'journey_memory','subject_id':customer_id,'verdict':'allow','purpose':'orchestrate customer journey'}],'final_response':final,'cost_estimate':round(total_cost+0.002*len(tools),3),'status':'success','created_at':NOW()}
 repo.insert_trace(trace)
 return trace

def list_traces(tenant_id='default', limit=50): return repo.list_traces(tenant_id, limit)
def get_trace(trace_id): return repo.get_trace(trace_id, 'default') or repo.get_trace(trace_id, os.getenv('ACOS_TENANT','default'))
def list_tasks(tenant_id='default'): return repo.list_tasks(tenant_id)
def get_task(task_id, tenant_id='default'): return repo.get_task(task_id, tenant_id)
