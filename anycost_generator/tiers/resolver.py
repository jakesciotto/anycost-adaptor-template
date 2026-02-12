"""Tier resolver -- determines the complexity tier from a ProviderConfig.

The tier is already resolved by the Pydantic model_validator on ProviderConfig,
but this module provides a standalone function for use cases where you want to
determine the tier from raw data before full validation.
"""

from __future__ import annotations

from typing import Any

from anycost_generator.config.schema import Tier


def resolve_tier_from_dict(data: dict[str, Any]) -> Tier:
    """Determine tier from a raw config dict.

    Priority:
    1. Explicit 'tier' key
    2. Presence of enterprise_config or csv_structure -> tier3
    3. Presence of structured_config or root_data_key hints -> tier2
    4. Presence of credit_config or credit-related keys -> tier1
    5. Default -> tier1
    """
    # Explicit tier
    explicit = data.get("tier")
    if explicit:
        return Tier(explicit)

    # Check for enterprise indicators
    if data.get("enterprise_config"):
        return Tier.TIER3_ENTERPRISE

    # Check for CSV source format
    data_section = data.get("data", {})
    if data_section.get("source_format") == "csv" or data_section.get("input_method") == "file_upload":
        return Tier.TIER3_ENTERPRISE

    # Check for reference-pattern configs (legacy format)
    if "data_structure" in data or "data_patterns" in data:
        # If it has csv_structure or CSV mentions, it's tier3
        patterns = data.get("data_patterns", {})
        if patterns.get("source_format") == "csv":
            return Tier.TIER3_ENTERPRISE

        # If it has root_data_key, line_type_field, etc. it's tier2
        structure = data.get("data_structure", {})
        if structure.get("root_data_key") or structure.get("line_type_field"):
            return Tier.TIER2_STRUCTURED

    # Check for structured config
    if data.get("structured_config"):
        return Tier.TIER2_STRUCTURED

    # Check for credit-style config
    if data.get("credit_config"):
        return Tier.TIER1_CREDIT

    # Check provider-specific config sections
    provider_name = data.get("provider", {}).get("name", "")
    legacy_key = f"{provider_name}_config"
    if legacy_key in data:
        legacy = data[legacy_key]
        if any(k in legacy for k in ("credit_to_usd", "credits_endpoint", "token_pools")):
            return Tier.TIER1_CREDIT

    return Tier.TIER1_CREDIT
