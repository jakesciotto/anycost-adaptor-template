"""Load ProviderConfig from YAML file or dict.

Both input paths (YAML file and interactive CLI dict) converge here,
producing a validated ProviderConfig.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from anycost_generator.config.schema import ProviderConfig


def _normalize_cbf_mapping(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert slash-keyed cbf_mapping (e.g. 'time/usage_start') to flat keys."""
    if not raw:
        return {}
    out: dict[str, Any] = {}
    for key, value in raw.items():
        flat_key = key.replace("/", "_")
        out[flat_key] = value
    return out


def _normalize_legacy_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Reshape a legacy YAML config into the unified schema.

    Handles:
    - cbf_mapping with slash keys -> flat keys
    - Provider-specific *_config sections -> credit_config / structured_config / enterprise_config
    - Reference-pattern configs (provider_template_example) -> best-effort mapping
    """
    data = dict(raw)

    # Normalize cbf_mapping keys
    if "cbf_mapping" in data:
        data["cbf_mapping"] = _normalize_cbf_mapping(data["cbf_mapping"])

    # Map provider-specific config sections to class-generic names
    provider_name = data.get("provider", {}).get("name", "")
    legacy_key = f"{provider_name}_config"
    if legacy_key in data and "credit_config" not in data:
        legacy = data.pop(legacy_key)
        # Detect whether this is credit-style config
        if any(k in legacy for k in ("credit_to_usd", "credits_endpoint", "token_pools")):
            data["credit_config"] = legacy

    # Move top-level 'endpoints' into api.endpoints
    if "endpoints" in data and "api" in data:
        data["api"]["endpoints"] = data.pop("endpoints")

    return data


def load_from_yaml(path: str | Path) -> ProviderConfig:
    """Load and validate a ProviderConfig from a YAML file."""
    path = Path(path)
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"Empty config file: {path}")

    normalized = _normalize_legacy_config(raw)
    return ProviderConfig.model_validate(normalized)


def load_from_dict(data: dict[str, Any]) -> ProviderConfig:
    """Load and validate a ProviderConfig from a dict (e.g. interactive CLI)."""
    normalized = _normalize_legacy_config(data)
    return ProviderConfig.model_validate(normalized)
