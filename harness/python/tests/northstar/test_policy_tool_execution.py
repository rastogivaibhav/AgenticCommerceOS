from acosplatform.policy.tool_policy import classify_tool, evaluate_tool_policy
from acosplatform.tools.executor import execute_tool


def test_tool_policy_classifies_commerce_risk_levels():
    assert classify_tool("catalog.search") == "low"
    assert classify_tool("cart.add_item") == "medium"
    assert classify_tool("payments.create") == "high"
    assert classify_tool("unknown.tool") == "unknown"


def test_high_risk_tool_requires_approval_when_policy_enforcement_enabled(monkeypatch):
    monkeypatch.setenv("ACOS_POLICY_ENFORCEMENT", "1")
    decision = evaluate_tool_policy("returns.create_return", {"order_id": "ORD-1001"})
    assert decision.verdict == "require_approval"
    trace = execute_tool("returns.create_return", {"order_id": "ORD-1001"}, context={"tenant_id": "policy-test"})
    assert trace["status"] == "blocked"
    assert trace["policy_verdict"] == "require_approval"


def test_high_risk_tool_executes_with_explicit_policy_approval(monkeypatch):
    monkeypatch.setenv("ACOS_POLICY_ENFORCEMENT", "1")
    trace = execute_tool(
        "returns.create_return",
        {"order_id": "ORD-1001"},
        context={"tenant_id": "policy-test", "policy_approved": True},
    )
    assert trace["status"] == "success"
    assert trace["policy_verdict"] == "allow"
    assert trace["risk_level"] == "high"
