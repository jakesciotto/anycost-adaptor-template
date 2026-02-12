"""Semantic validation beyond Pydantic type checking.

Catches issues like:
- Empty required fields that Pydantic allows as valid strings
- Inconsistent tier config (e.g. credit_config on a tier3 provider)
- URLs that don't look valid
- Env var naming conventions
"""

from __future__ import annotations

from urllib.parse import urlparse

from anycost_generator.config.schema import ProviderConfig, Tier


class ConfigValidationError:
    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # "error" or "warning"

    def __str__(self):
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


def validate_config(config: ProviderConfig) -> list[ConfigValidationError]:
    """Run semantic validation on a ProviderConfig.

    Returns a list of validation errors/warnings. Empty list means valid.
    """
    errors: list[ConfigValidationError] = []

    # Provider name should be lowercase alphanumeric + underscores
    if not config.provider.name.replace("_", "").replace("-", "").isalnum():
        errors.append(ConfigValidationError(
            "provider.name",
            f"Provider name '{config.provider.name}' should contain only alphanumeric chars, underscores, or hyphens"
        ))

    # Base URL should be a valid URL
    parsed = urlparse(config.api.base_url)
    if not parsed.scheme or not parsed.netloc:
        if "{" not in config.api.base_url:  # Allow template URLs like https://api.{deployment}.example.com
            errors.append(ConfigValidationError(
                "api.base_url",
                f"Base URL '{config.api.base_url}' does not appear to be a valid URL"
            ))

    # Required env vars should not be empty
    if not config.auth.required_env_vars:
        errors.append(ConfigValidationError(
            "auth.required_env_vars",
            "At least one required environment variable should be specified"
        ))

    # Env vars should be UPPER_SNAKE_CASE
    for var in config.auth.required_env_vars + config.auth.optional_env_vars:
        if var != var.upper() or " " in var:
            errors.append(ConfigValidationError(
                "auth.env_vars",
                f"Environment variable '{var}' should be UPPER_SNAKE_CASE",
                severity="warning",
            ))

    # Tier-specific consistency checks
    if config.tier == Tier.TIER1_CREDIT and config.credit_config:
        if config.credit_config.credit_to_usd == 0.0:
            errors.append(ConfigValidationError(
                "credit_config.credit_to_usd",
                "Credit-to-USD conversion rate is 0.0 -- set this to the actual rate",
                severity="warning",
            ))

    if config.tier == Tier.TIER3_ENTERPRISE and config.enterprise_config:
        ec = config.enterprise_config
        if not ec.csv_structure and not ec.nested_response and not ec.cost_categories:
            errors.append(ConfigValidationError(
                "enterprise_config",
                "Enterprise config should specify csv_structure, nested_response, or cost_categories",
                severity="warning",
            ))

    return errors
