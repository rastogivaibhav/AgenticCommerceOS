# tests/temporal/test_graph_walker.py
import pytest
from acosplatform.temporal.graph_walker import (
    build_adjacency,
    find_start_node,
    evaluate_edge_condition,
    topological_order,
    next_nodes,
)

SIMPLE_GRAPH = {
    "nodes": [
        {"id": "s1", "type": "startNode", "data": {"triggerType": "manual"}},
        {"id": "a1", "type": "agentNode",  "data": {"agentId": "ag_triage", "label": "Triage"}},
        {"id": "e1", "type": "endNode",    "data": {"outcomeType": "success"}},
    ],
    "edges": [
        {"id": "es", "source": "s1", "target": "a1", "data": {}},
        {"id": "ea", "source": "a1", "target": "e1", "data": {}},
    ],
}

BRANCH_GRAPH = {
    "nodes": [
        {"id": "s1", "type": "startNode",       "data": {}},
        {"id": "o1", "type": "orchestratorNode", "data": {}},
        {"id": "a1", "type": "agentNode",        "data": {}},
        {"id": "a2", "type": "agentNode",        "data": {}},
        {"id": "e1", "type": "endNode",          "data": {}},
    ],
    "edges": [
        {"id": "e1", "source": "s1", "target": "o1", "data": {}},
        {"id": "e2", "source": "o1", "target": "a1",
         "data": {"condition": {"field": "score", "operator": ">", "value": "0.8"}}},
        {"id": "e3", "source": "o1", "target": "a2",
         "data": {"condition": {"field": "score", "operator": "<=", "value": "0.8"}}},
        {"id": "e4", "source": "a1", "target": "e1", "data": {}},
        {"id": "e5", "source": "a2", "target": "e1", "data": {}},
    ],
}

def test_build_adjacency_simple():
    adj = build_adjacency(SIMPLE_GRAPH["edges"])
    assert adj["s1"] == ["a1"]
    assert adj["a1"] == ["e1"]

def test_find_start_node():
    node = find_start_node(SIMPLE_GRAPH["nodes"])
    assert node["id"] == "s1"

def test_find_start_node_missing_raises():
    with pytest.raises(ValueError, match="No startNode"):
        find_start_node([{"id": "x", "type": "agentNode", "data": {}}])

def test_evaluate_edge_condition_no_condition():
    assert evaluate_edge_condition({}, {}) is True
    assert evaluate_edge_condition({"condition": None}, {}) is True

def test_evaluate_edge_condition_eq():
    cond = {"condition": {"field": "status", "operator": "==", "value": "placed"}}
    assert evaluate_edge_condition(cond, {"status": "placed"}) is True
    assert evaluate_edge_condition(cond, {"status": "pending"}) is False

def test_evaluate_edge_condition_gt():
    cond = {"condition": {"field": "score", "operator": ">", "value": "0.8"}}
    assert evaluate_edge_condition(cond, {"score": 0.9}) is True
    assert evaluate_edge_condition(cond, {"score": 0.5}) is False

def test_evaluate_edge_condition_contains():
    cond = {"condition": {"field": "message", "operator": "contains", "value": "refund"}}
    assert evaluate_edge_condition(cond, {"message": "I want a refund"}) is True
    assert evaluate_edge_condition(cond, {"message": "show me laptops"}) is False

def test_topological_order_simple():
    order = topological_order(SIMPLE_GRAPH)
    ids = [n["id"] for n in order]
    assert ids.index("s1") < ids.index("a1") < ids.index("e1")

def test_next_nodes_with_condition():
    ctx = {"score": 0.9}
    nxt = next_nodes("o1", BRANCH_GRAPH["edges"], BRANCH_GRAPH["nodes"], ctx)
    assert len(nxt) == 1
    assert nxt[0]["id"] == "a1"

def test_next_nodes_no_condition_returns_all():
    ctx = {}
    nxt = next_nodes("s1", SIMPLE_GRAPH["edges"], SIMPLE_GRAPH["nodes"], ctx)
    assert nxt[0]["id"] == "a1"
