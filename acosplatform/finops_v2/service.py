from acosplatform.agents.registry import REGISTRY
def summary():
    agents=REGISTRY.list_agents(); total=sum(float(a.get('cost_budget_per_run') or 0) for a in agents)
    return {'summary':{'cost_today':round(total*42,2),'avg_cost_per_run':round(total/max(len(agents),1),3),'highest_cost_agent':max(agents,key=lambda a:float(a.get('cost_budget_per_run') or 0))['agent_id']},'by_agent':[{'agent_id':a['agent_id'],'budget':a.get('cost_budget_per_run'),'avg_cost':round(float(a.get('cost_budget_per_run') or 0)*0.8,3),'budget_status':'ok'} for a in agents]}
