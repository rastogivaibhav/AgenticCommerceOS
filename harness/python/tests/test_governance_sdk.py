from acosplatform.governance.sdk import DefaultGovernanceSDK, log_governance_decision


def test_admin_authorize_allows_write_action():
    sdk = DefaultGovernanceSDK(persist_decisions=False)
    decision = sdk.authorize(
        action="workflow.promote",
        subject={"sub": "u1", "role": "admin"},
        resource="/workflows/w1",
        tenant_id="default",
    )
    assert decision.allowed is True


def test_analyst_authorize_blocks_mutation():
    sdk = DefaultGovernanceSDK(persist_decisions=False)
    decision = sdk.authorize(
        action="workflow.promote",
        subject={"sub": "u2", "role": "analyst"},
        resource="/workflows/w1",
        tenant_id="default",
    )
    assert decision.allowed is False
    assert decision.reason == "analyst_read_only"


def test_analyst_can_call_read_tool_only():
    sdk = DefaultGovernanceSDK(persist_decisions=False)
    allow = sdk.can_call_tool(
        tool_name="search.catalog",
        subject={"sub": "u3", "roles": ["analyst"]},
        tenant_id="default",
    )
    deny = sdk.can_call_tool(
        tool_name="write.order_refund",
        subject={"sub": "u3", "roles": ["analyst"]},
        tenant_id="default",
    )
    assert allow.allowed is True
    assert deny.allowed is False


def test_analyst_sensitive_context_access_blocked():
    sdk = DefaultGovernanceSDK(persist_decisions=False)
    decision = sdk.can_access_context(
        context_key="customer.payment_token",
        subject={"sub": "u4", "role": "analyst"},
        tenant_id="default",
        access="read",
    )
    assert decision.allowed is False
    assert decision.reason == "analyst_sensitive_context_blocked"


def test_decision_logging_fallback(monkeypatch):
    monkeypatch.setattr("acosplatform.governance.sdk.is_pool_available", lambda: False)
    record = log_governance_decision(
        tenant_id="default",
        subject="u5",
        action="read.workflow",
        resource="/workflows/w1",
        decision="allow",
        reason="unit-test",
        policy_source="pytest",
        obligations=[],
        context={"suite": "governance"},
    )
    assert record["decision"] == "allow"
    assert record["tenant_id"] == "default"


def test_opa_override_can_deny(monkeypatch):
    class _FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"result": {"allow": False, "reason": "opa_policy_denied"}}

    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: _FakeResponse())

    sdk = DefaultGovernanceSDK(
        persist_decisions=False,
        use_opa=True,
        opa_url="http://opa:8181",
        opa_package="acos/governance",
    )
    decision = sdk.authorize(
        action="read.workflow",
        subject={"sub": "u6", "role": "admin"},
        resource="/workflows/w1",
        tenant_id="default",
    )
    assert decision.allowed is False
    assert decision.reason == "opa_policy_denied"
    assert decision.policy_source == "opa:acos/governance"


def test_opa_unavailable_falls_back_to_local():
    sdk = DefaultGovernanceSDK(
        persist_decisions=False,
        use_opa=True,
        opa_url="http://127.0.0.1:1",
        opa_package="acos/governance",
        opa_timeout_seconds=0.01,
    )
    decision = sdk.can_call_tool(
        tool_name="search.catalog",
        subject={"sub": "u7", "roles": ["analyst"]},
        tenant_id="default",
    )
    assert decision.allowed is True
    assert decision.reason == "analyst_read_tool_access"
