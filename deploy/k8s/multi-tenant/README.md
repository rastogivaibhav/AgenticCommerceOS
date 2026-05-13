# Multi-Tenant Network Baseline (Week 7)

This folder contains the starter network isolation baseline for namespace-per-tenant Kubernetes deployment.

## Files
1. `namespace-template.yaml`: tenant namespace manifest template.
2. `networkpolicy-default-deny.yaml`: deny all ingress/egress by default.
3. `networkpolicy-allow-dns.yaml`: permit DNS egress to kube-dns.
4. `networkpolicy-allow-acos-control-plane.yaml`: permit egress to ACOS control-plane services.
5. `peer-authentication-strict.yaml`: Istio strict mTLS policy for tenant namespace.

## Apply Order
1. Create namespace from template.
2. Apply default deny policy.
3. Apply allow-list policies.
4. Apply strict mTLS policy (if Istio enabled).

## Notes
1. Replace `${TENANT_NAMESPACE}` and `${TENANT_ID}` before applying.
2. Confirm labels on control-plane namespaces/pods match policy selectors.
3. This is baseline hardening; service-specific ingress policies should be added per workload.

## Runtime Verification
Use the verification script to produce pass/fail evidence from a real cluster:

```powershell
.\scripts\verify_tenant_network_policy.ps1 -TenantId pilot-a
```

Optional control-plane probe:

```powershell
.\scripts\verify_tenant_network_policy.ps1 -TenantId pilot-a -ControlPlaneProbeHost ops-api.control-plane.svc.cluster.local:8000
```
