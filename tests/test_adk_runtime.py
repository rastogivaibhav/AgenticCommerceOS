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

