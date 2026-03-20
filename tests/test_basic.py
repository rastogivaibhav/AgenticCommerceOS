"""Basic smoke tests."""


def test_ok():
    assert True


def test_imports():
    """Verify all modules can be imported."""
    from acosplatform.plugins import catalog, pricing, promotions, loyalty, checkout, orders, returns
    from acosplatform.journey import context, routing, engine
    from acosplatform.db import connection, repository
    from acosplatform.billing import engine as billing
    from acosplatform.evaluation import scorer
    from acosplatform.personalization import engine as personalization
    from acosplatform.replay import replay_engine
    from acosplatform.tenancy import manager
    from acosplatform.analytics import stream
    from integrations.adk import provider
    from integrations.agentfabric import client
    assert True


def test_catalog_has_20_products():
    from acosplatform.plugins.catalog import PRODUCTS
    assert len(PRODUCTS) == 20


def test_tenancy_has_configs():
    from acosplatform.tenancy.manager import TENANT_CONFIGS
    assert "default" in TENANT_CONFIGS
    assert "eu-store" in TENANT_CONFIGS