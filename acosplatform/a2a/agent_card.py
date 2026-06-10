from acosplatform.agents.registry import REGISTRY

def list_agent_cards():
    return [REGISTRY.agent_card(a['agent_id']) for a in REGISTRY.list_agents()]
