"""Week-7 network baseline asset checks."""

from pathlib import Path


def test_network_policy_assets_exist():
    root = Path(__file__).resolve().parents[1]
    required = [
        root / "deploy" / "k8s" / "multi-tenant" / "namespace-template.yaml",
        root / "deploy" / "k8s" / "multi-tenant" / "networkpolicy-default-deny.yaml",
        root / "deploy" / "k8s" / "multi-tenant" / "networkpolicy-allow-dns.yaml",
        root / "deploy" / "k8s" / "multi-tenant" / "networkpolicy-allow-acos-control-plane.yaml",
        root / "deploy" / "k8s" / "multi-tenant" / "peer-authentication-strict.yaml",
        root / "scripts" / "verify_tenant_network_policy.ps1",
    ]
    for path in required:
        assert path.exists(), f"missing expected asset: {path}"


def test_default_deny_policy_is_present():
    root = Path(__file__).resolve().parents[1]
    content = (root / "deploy" / "k8s" / "multi-tenant" / "networkpolicy-default-deny.yaml").read_text(
        encoding="utf-8"
    )
    assert "kind: NetworkPolicy" in content
    assert "name: default-deny-all" in content
    assert "Ingress" in content
    assert "Egress" in content
