from acosplatform.agents.registry import REGISTRY
POLICIES=[
 {'id':'pii_minimisation','name':'PII minimisation','status':'active','risk':'high'},
 {'id':'returns_approval','name':'High-value refund approval','status':'active','risk':'high'},
 {'id':'nursery_safety_boundaries','name':'Nursery safety wording boundaries','status':'active','risk':'high'},
 {'id':'vendor_agent_allowlist','name':'Vendor agent capability allowlist','status':'active','risk':'medium'},
 {'id':'cost_budget','name':'Per-run cost budget','status':'active','risk':'medium'},
]
def guardrails():
    return {'policies':POLICIES,'recent_decisions':[{'policy':'nursery_safety_boundaries','verdict':'allow_with_safe_wording'}, {'policy':'returns_approval','verdict':'requires_human_for_refund_creation'}, {'policy':'cost_budget','verdict':'allow'}]}
def enforce_promotion_gate(agent_id):
    agent=REGISTRY.get_agent(agent_id)
    if not agent: return {'allowed':False,'missing':['agent']}
    missing=[]
    for f in ['owner_team','capabilities','supported_channels','tools','risk_level','fallback']:
        if not agent.get(f): missing.append(f)
    if float(agent.get('evaluation_score') or 0) < 0.85: missing.append('evaluation_score')
    return {'allowed':not missing,'missing':missing}
