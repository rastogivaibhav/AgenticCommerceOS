"""Salesforce integration helpers."""

from integrations.salesforce.client import (
    execute_salesforce_action,
    load_salesforce_config,
    probe_salesforce,
)

__all__ = [
    "execute_salesforce_action",
    "load_salesforce_config",
    "probe_salesforce",
]
