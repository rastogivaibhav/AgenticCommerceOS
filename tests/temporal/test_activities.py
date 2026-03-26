# tests/temporal/test_activities.py
import pytest
from unittest.mock import patch, MagicMock
from acosplatform.temporal.activities import (
    execute_agent_node,
    execute_integration_node,
    execute_logic_node,
    execute_orchestrator_node,
    NodeInput,
)


@pytest.mark.asyncio
async def test_agent_node_calls_run_adk():
    node = {"id": "a1", "type": "agentNode", "data": {"agentId": "ag_triage", "label": "Triage"}}
    ctx  = {"customer_id": "cust-1", "message": "buy headphones", "tenant_id": "default"}
    with patch("acosplatform.temporal.activities.run_adk") as mock_adk:
        mock_adk.return_value = {"response": "Here are some headphones"}
        result = await execute_agent_node(NodeInput(node=node, ctx=ctx, upstream={}))
    mock_adk.assert_called_once()
    assert "response" in result


@pytest.mark.asyncio
async def test_integration_node_catalog_skill():
    node = {"id": "i1", "type": "integrationNode", "data": {"skillId": "catalog", "label": "Search"}}
    ctx  = {"message": "laptops", "tenant_id": "default"}
    with patch("acosplatform.temporal.activities.catalog") as mock_catalog:
        mock_catalog.search.return_value = {"products": [{"id": "p1"}]}
        result = await execute_integration_node(NodeInput(node=node, ctx=ctx, upstream={}))
    assert "products" in result


@pytest.mark.asyncio
async def test_integration_node_unknown_skill_skips():
    node = {"id": "i2", "type": "integrationNode", "data": {"skillId": "unknown_skill"}}
    ctx  = {}
    result = await execute_integration_node(NodeInput(node=node, ctx=ctx, upstream={}))
    assert result.get("skipped") is True


@pytest.mark.asyncio
async def test_logic_node_passes_context_through():
    node = {"id": "l1", "type": "logicNode", "data": {"logicType": "switch"}}
    ctx  = {"score": 0.9}
    result = await execute_logic_node(NodeInput(node=node, ctx=ctx, upstream={"score": 0.9}))
    assert result.get("score") == 0.9


@pytest.mark.asyncio
async def test_orchestrator_node_returns_dispatch_signal():
    node = {"id": "o1", "type": "orchestratorNode", "data": {"agentId": "", "label": "Orch"}}
    ctx  = {"tenant_id": "default"}
    result = await execute_orchestrator_node(NodeInput(node=node, ctx=ctx, upstream={}))
    assert result.get("orchestrated") is True
