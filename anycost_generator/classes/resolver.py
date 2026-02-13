"""Adaptor class resolver -- determines the complexity class from a ProviderConfig.

The adaptor class is already resolved by the Pydantic model_validator on ProviderConfig,
but this module provides a standalone function for use cases where you want to
determine the adaptor class from raw data before full validation.
"""

from __future__ import annotations

from typing import Any

from anycost_generator.config.schema import AdaptorClass


def resolve_adaptor_class_from_dict(data: dict[str, Any]) -> AdaptorClass:
    """Determine adaptor class from a raw config dict.

    Priority:
    1. Explicit 'adaptor_class' key
    2. Presence of enterprise_config or csv_structure -> class3
    3. Presence of structured_config or root_data_key hints -> class2
    4. Presence of credit_config or credit-related keys -> class1
    5. Default -> class1
    """
    # Explicit adaptor class
    explicit = data.get("adaptor_class")
    if explicit:
        return AdaptorClass(explicit)

    # Check for enterprise indicators
    if data.get("enterprise_config"):
        return AdaptorClass.CLASS3_ENTERPRISE

    # Check for CSV source format
    data_section = data.get("data", {})
    if data_section.get("source_format") == "csv" or data_section.get("input_method") == "file_upload":
        return AdaptorClass.CLASS3_ENTERPRISE

    # Check for reference-pattern configs (legacy format)
    if "data_structure" in data or "data_patterns" in data:
        # If it has csv_structure or CSV mentions, it's class3
        patterns = data.get("data_patterns", {})
        if patterns.get("source_format") == "csv":
            return AdaptorClass.CLASS3_ENTERPRISE

        # If it has root_data_key, line_type_field, etc. it's class2
        structure = data.get("data_structure", {})
        if structure.get("root_data_key") or structure.get("line_type_field"):
            return AdaptorClass.CLASS2_STRUCTURED

    # Check for structured config
    if data.get("structured_config"):
        return AdaptorClass.CLASS2_STRUCTURED

    # Check for credit-style config
    if data.get("credit_config"):
        return AdaptorClass.CLASS1_CREDIT

    # Check provider-specific config sections
    provider_name = data.get("provider", {}).get("name", "")
    legacy_key = f"{provider_name}_config"
    if legacy_key in data:
        legacy = data[legacy_key]
        if any(k in legacy for k in ("credit_to_usd", "credits_endpoint", "token_pools")):
            return AdaptorClass.CLASS1_CREDIT

    return AdaptorClass.CLASS1_CREDIT
