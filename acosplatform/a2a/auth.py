def can_invoke_agent(actor_roles, agent):
    return not agent.get('kill_switch')
