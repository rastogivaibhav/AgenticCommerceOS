from integrations.adk import provider as adk_provider
from integrations.adk.provider import run_adk
from integrations.adk.runtime import ADKRuntime, RuntimeTool, ToolContract, ToolContractError


def test_runtime_enforces_output_contract():
    runtime = ADKRuntime(journey_type="discovery", provider="test")
    runtime.register_tool(
        RuntimeTool(
            name="bad_tool",
            handler=lambda _payload: {"source": "x"},
            contract=ToolContract(name="bad_tool", output_required=("result_text",)),
        )
    )
    try:
        runtime.call_tool("bad_tool", {})
        assert False, "expected ToolContractError"
    except ToolContractError:
        assert True


def test_run_adk_discovery_uses_standard_runtime():
    result = run_adk({"message": "show me laptops", "customer_id": "cust-1"}, journey_type="discovery")
    assert "runtime" in result
    assert result["runtime"]["engine"] == "standardized-adk-runtime"
    assert "recommendation" in result
    assert "recommendation" in result["skills_used"]


def test_run_adk_purchase_executes_two_tools():
    result = run_adk({"message": "buy headphones", "customer_id": "cust-2"}, journey_type="purchase")
    assert "recommendation" in result
    assert "explanation" in result
    assert result["skills_used"] == ["recommendation", "explanation"]


def test_run_adk_respects_requested_local_fallback(monkeypatch):
    monkeypatch.setattr(adk_provider, "_adk_available", True)
    monkeypatch.setattr(adk_provider, "_model", object())

    result = run_adk(
        {"message": "show me laptops", "customer_id": "cust-3"},
        journey_type="discovery",
        requested_provider="local_fallback",
        strict_provider=True,
    )

    assert result["runtime"]["provider"] == "local_fallback"
    assert result["recommendation"]["source"] == "local_fallback"


def test_run_adk_reports_unavailable_requested_provider(monkeypatch):
    monkeypatch.setattr(adk_provider, "_adk_available", False)
    monkeypatch.setattr(adk_provider, "_model", None)

    result = run_adk(
        {"message": "track my order", "customer_id": "cust-4"},
        journey_type="post_purchase",
        requested_provider="google_genai",
        strict_provider=True,
    )

    assert result["runtime"]["provider"] == "google_genai"
    assert result["skills_used"] == []
    assert "errors" in result
