"""Interactive CLI using InquirerPy for decision-tree prompts.

Walks the user through building a ProviderConfig via prompts,
determines the tier, optionally saves the YAML, and generates the adaptor.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from InquirerPy import inquirer
from InquirerPy.separator import Separator

from anycost_generator.cli.display import (
    console,
    print_banner,
    print_config_summary,
    print_error,
    print_success,
    print_tier_info,
    print_warning,
)
from anycost_generator.config.loader import load_from_dict
from anycost_generator.engine.generator import AdaptorGenerator
from anycost_generator.validation.config_validator import validate_config
from anycost_generator.validation.output_validator import validate_output


# -- Tier descriptions for display ------------------------------------------

TIER_DESCRIPTIONS = {
    "tier1_credit": "Simple credit polling -- poll single endpoint, compute delta, credit-to-USD",
    "tier2_structured": "Structured billing -- multiple endpoints, field mapping, line items",
    "tier3_enterprise": "Enterprise/complex -- CSV processing or nested API, contract pricing, aggregation",
}


def run_interactive(output_dir: str = "./output", save_config: str | None = None):
    """Main interactive flow."""
    print_banner()

    # Step 1: Provider identity
    console.print("\n[bold]Step 1: Provider Identity[/bold]")
    provider_name = inquirer.text(
        message="Provider identifier (lowercase, e.g. 'bfl', 'elevenlabs'):",
        validate=lambda x: len(x) > 0 and x.replace("_", "").replace("-", "").isalnum(),
        invalid_message="Use lowercase alphanumeric characters, underscores, or hyphens",
    ).execute()

    display_name = inquirer.text(
        message="Display name (e.g. 'Black Forest Labs'):",
        validate=lambda x: len(x) > 0,
    ).execute()

    service_type = inquirer.text(
        message="Service type (e.g. 'ai-image-generation', 'logging'):",
        default="cloud",
    ).execute()

    # Step 2: API config
    console.print("\n[bold]Step 2: API Configuration[/bold]")
    base_url = inquirer.text(
        message="API base URL:",
        validate=lambda x: x.startswith("http"),
        invalid_message="URL must start with http:// or https://",
    ).execute()

    auth_method = inquirer.select(
        message="Authentication method:",
        choices=[
            {"name": "API Key (x-api-key header)", "value": "api_key"},
            {"name": "API Key (custom header)", "value": "api_key_header"},
            {"name": "Basic Auth (username:password)", "value": "basic_auth"},
            {"name": "Bearer Token", "value": "bearer_token"},
            {"name": "Bearer JWT", "value": "bearer_jwt"},
            {"name": "OAuth2", "value": "oauth2"},
        ],
    ).execute()

    # Env vars
    env_var_prefix = provider_name.upper().replace("-", "_")
    default_env_var = f"{env_var_prefix}_API_KEY"

    required_env_vars_str = inquirer.text(
        message="Required env vars (comma-separated):",
        default=default_env_var,
    ).execute()
    required_env_vars = [v.strip() for v in required_env_vars_str.split(",") if v.strip()]

    optional_env_vars_str = inquirer.text(
        message="Optional env vars (comma-separated, or leave empty):",
        default="",
    ).execute()
    optional_env_vars = [v.strip() for v in optional_env_vars_str.split(",") if v.strip()]

    # Step 3: Data shape (determines tier)
    console.print("\n[bold]Step 3: Data Shape[/bold]")
    data_shape = inquirer.select(
        message="How does this provider expose billing/usage data?",
        choices=[
            {"name": "Single endpoint returning credit/token balance", "value": "tier1_credit"},
            {"name": "API returning structured billing line items", "value": "tier2_structured"},
            {"name": "CSV file with billing data", "value": "tier3_csv"},
            {"name": "Complex API with nested responses", "value": "tier3_api"},
        ],
    ).execute()

    # Map data shape to tier
    if data_shape == "tier1_credit":
        tier = "tier1_credit"
    elif data_shape == "tier2_structured":
        tier = "tier2_structured"
    else:
        tier = "tier3_enterprise"

    print_tier_info(tier, TIER_DESCRIPTIONS[tier])

    # Step 4: Tier-specific details
    config_data = {
        "provider": {
            "name": provider_name,
            "display_name": display_name,
            "service_type": service_type,
        },
        "api": {
            "base_url": base_url,
            "auth_method": auth_method,
        },
        "auth": {
            "required_env_vars": required_env_vars,
            "optional_env_vars": optional_env_vars,
        },
        "tier": tier,
    }

    console.print(f"\n[bold]Step 4: {TIER_DESCRIPTIONS[tier].split(' -- ')[0]} Details[/bold]")

    if tier == "tier1_credit":
        config_data["credit_config"] = _prompt_credit_config(provider_name)
    elif tier == "tier2_structured":
        config_data["structured_config"] = _prompt_structured_config()
    else:
        config_data["enterprise_config"] = _prompt_enterprise_config(data_shape)

    # Step 5: Review
    console.print("\n[bold]Step 5: Review[/bold]")
    print_config_summary(config_data)

    proceed = inquirer.confirm(message="Generate adaptor with this configuration?", default=True).execute()
    if not proceed:
        print_warning("Generation cancelled.")
        return

    # Validate and generate
    try:
        config = load_from_dict(config_data)
    except Exception as e:
        print_error(f"Config validation failed: {e}")
        sys.exit(1)

    issues = validate_config(config)
    for issue in issues:
        if issue.severity == "warning":
            print_warning(str(issue))
        else:
            print_error(str(issue))

    if any(i.severity == "error" for i in issues):
        sys.exit(1)

    # Optionally save YAML
    if save_config:
        _save_yaml(config_data, save_config)
    else:
        save = inquirer.confirm(message="Save configuration to YAML?", default=False).execute()
        if save:
            path = inquirer.text(
                message="YAML output path:",
                default=f"config/examples/{provider_name}_config.yaml",
            ).execute()
            _save_yaml(config_data, path)

    # Generate
    generator = AdaptorGenerator(config)
    output_path = generator.generate(output_dir)

    # Post-validation
    post_issues = validate_output(output_path, config.provider.name, config.auth.required_env_vars)
    post_errors = [i for i in post_issues if i.severity == "error"]
    if post_errors:
        print_warning("Post-generation validation found issues:")
        for e in post_errors:
            print_error(f"  {e}")
    else:
        print_success("All validation checks passed.")


def _prompt_credit_config(provider_name: str) -> dict:
    """Prompt for tier 1 credit config."""
    credits_endpoint = inquirer.text(
        message="Credits/balance API endpoint (e.g. '/me', '/credits'):",
        default="/credits",
    ).execute()

    credit_to_usd = inquirer.text(
        message="Credit-to-USD conversion rate (e.g. 0.01):",
        default="0.01",
        validate=lambda x: _is_float(x),
        invalid_message="Must be a number",
    ).execute()

    discount_rate = inquirer.text(
        message="Discount rate (0-1, e.g. 0.30 for 30%, or 0 for none):",
        default="0",
        validate=lambda x: _is_float(x),
    ).execute()

    has_pools = inquirer.confirm(message="Does the provider have multiple token/credit pools?", default=False).execute()
    token_pools = []
    if has_pools:
        while True:
            field = inquirer.text(message="Pool field name (or 'done'):").execute()
            if field.lower() == "done":
                break
            label = inquirer.text(message=f"Label for '{field}':").execute()
            token_pools.append({"field": field, "label": label})

    discount_rate_val = float(discount_rate)
    credit_to_usd_val = float(credit_to_usd)
    discounted_rate = credit_to_usd_val * (1 - discount_rate_val) if discount_rate_val > 0 else 0

    return {
        "credits_endpoint": credits_endpoint,
        "credit_to_usd": credit_to_usd_val,
        "discount_rate": discount_rate_val,
        "discounted_rate": round(discounted_rate, 6),
        "token_pools": token_pools,
        "snapshot_file": f"data/{provider_name}_snapshots.csv",
    }


def _prompt_structured_config() -> dict:
    """Prompt for tier 2 structured billing config."""
    root_data_key = inquirer.text(
        message="Root data key in API response (e.g. 'data', 'items'):",
        default="data",
    ).execute()

    line_type_field = inquirer.text(
        message="Field that identifies line item type (e.g. 'line_type', or leave empty):",
        default="",
    ).execute()

    resource_id_template = inquirer.text(
        message="Resource ID template (e.g. 'provider:{type}/{id}', or leave empty):",
        default="",
    ).execute()

    return {
        "root_data_key": root_data_key,
        "line_type_field": line_type_field,
        "resource_id_template": resource_id_template,
    }


def _prompt_enterprise_config(data_shape: str) -> dict:
    """Prompt for tier 3 enterprise config."""
    config: dict = {}

    if data_shape == "tier3_csv":
        console.print("  CSV structure configuration:")
        header_skip = inquirer.text(
            message="Number of header rows to skip:",
            default="0",
            validate=lambda x: x.isdigit(),
        ).execute()

        date_format = inquirer.text(
            message="Date format in CSV (e.g. '%b %Y', '%Y-%m-%d'):",
            default="%b %Y",
        ).execute()

        config["csv_structure"] = {
            "header_rows_to_skip": int(header_skip),
            "date_column": 0,
            "date_format": date_format,
            "cost_categories": {},
        }

        # Collect cost categories
        console.print("  Enter cost category columns (name=column_index):")
        while True:
            cat = inquirer.text(message="Category name (or 'done'):").execute()
            if cat.lower() == "done":
                break
            col = inquirer.text(
                message=f"Column index for '{cat}':",
                validate=lambda x: x.isdigit(),
            ).execute()
            config["csv_structure"]["cost_categories"][cat] = int(col)
    else:
        config["nested_response"] = True

    aggregation = inquirer.select(
        message="Aggregation method:",
        choices=["daily", "monthly", "none"],
        default="daily",
    ).execute()
    config["aggregation_method"] = aggregation

    return config


def _save_yaml(data: dict, path: str):
    """Save config data as YAML."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"Config saved to: {p}")


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False
