"""Pure graph traversal and condition evaluation — no I/O, no Temporal SDK."""
from __future__ import annotations


def build_adjacency(edges: list[dict]) -> dict[str, list[str]]:
    """Return {source_id: [target_id, ...]} from an edge list."""
    adj: dict[str, list[str]] = {}
    for edge in edges:
        adj.setdefault(edge["source"], []).append(edge["target"])
    return adj


def find_start_node(nodes: list[dict]) -> dict:
    """Return the single startNode; raise ValueError if absent."""
    for node in nodes:
        if node.get("type") in ("startNode", "triggerNode"):
            return node
    raise ValueError("No startNode found in graph — canvas must have a Start node")


def evaluate_edge_condition(edge_data: dict, ctx: dict) -> bool:
    """
    Return True if the edge should be followed given the current execution context.
    An edge with no condition (or condition=None) is always followed.
    """
    condition = edge_data.get("condition")
    if not condition:
        return True
    field    = condition.get("field", "")
    operator = condition.get("operator", "==")
    value    = condition.get("value", "")
    actual   = ctx.get(field)
    if actual is None:
        return False
    try:
        if operator == "==":           return str(actual) == str(value)
        if operator == "!=":           return str(actual) != str(value)
        if operator == ">":            return float(actual) > float(value)
        if operator == ">=":           return float(actual) >= float(value)
        if operator == "<":            return float(actual) < float(value)
        if operator == "<=":           return float(actual) <= float(value)
        if operator == "contains":     return str(value).lower() in str(actual).lower()
        if operator == "not_contains": return str(value).lower() not in str(actual).lower()
    except (TypeError, ValueError):
        return False
    return True


def next_nodes(
    node_id: str,
    edges: list[dict],
    nodes: list[dict],
    ctx: dict,
) -> list[dict]:
    """Return nodes reachable from node_id whose edge conditions pass."""
    node_map = {n["id"]: n for n in nodes}
    outgoing = [e for e in edges if e["source"] == node_id]
    result = []
    for edge in outgoing:
        if evaluate_edge_condition(edge.get("data", {}), ctx):
            target = node_map.get(edge["target"])
            if target:
                result.append(target)
    return result


def topological_order(graph: dict) -> list[dict]:
    """
    Return nodes in a valid execution order (Kahn's algorithm).
    Raises ValueError if a cycle is detected.
    """
    nodes    = graph["nodes"]
    edges    = graph["edges"]
    node_map = {n["id"]: n for n in nodes}
    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    for edge in edges:
        in_degree[edge["target"]] = in_degree.get(edge["target"], 0) + 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    order: list[dict] = []
    while queue:
        nid = queue.pop(0)
        order.append(node_map[nid])
        for edge in edges:
            if edge["source"] == nid:
                in_degree[edge["target"]] -= 1
                if in_degree[edge["target"]] == 0:
                    queue.append(edge["target"])
    if len(order) != len(nodes):
        raise ValueError("Cycle detected in workflow graph")
    return order
