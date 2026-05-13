from acosplatform.capabilities.registry import CAPABILITY_REGISTRY

def route(message: str):
    return CAPABILITY_REGISTRY.resolve(message)
