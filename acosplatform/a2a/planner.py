def build_plan(required_capabilities, agents):
    return {'mode':'sequential_agents','steps':[{'type':'agent_call','agent':a['agent_id'],'capabilities':[c for c in a.get('capabilities',[]) if c in required_capabilities]} for a in agents] + [{'type':'response_merge'}]}
