"""Unified Pydantic config schema for AnyCost Adaptor Generator.

All config paths (YAML file or interactive CLI dict) converge here.
The tier is either explicitly set or auto-detected from which optional
tier-specific section is present.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Tier(str, Enum):
    TIER1_CREDIT = "tier1_credit"
    TIER2_STRUCTURED = "tier2_structured"
    TIER3_ENTERPRISE = "tier3_enterprise"


class AuthMethod(str, Enum):
    API_KEY = "api_key"
    API_KEY_HEADER = "api_key_header"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    BEARER_JWT = "bearer_jwt"
    OAUTH2 = "oauth2"


class SourceFormat(str, Enum):
    JSON = "json"
    CSV = "csv"


class InputMethod(str, Enum):
    API = "api"
    FILE_UPLOAD = "file_upload"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class ProviderInfo(BaseModel):
    name: str = Field(..., description="Lowercase provider identifier (e.g. 'bfl')")
    display_name: str = Field(..., description="Human-readable name (e.g. 'Black Forest Labs')")
    service_type: str = Field(..., description="Category (e.g. 'ai-image-generation')")


class ApiConfig(BaseModel):
    base_url: str = Field(..., description="API base URL")
    auth_method: AuthMethod = Field(..., description="Authentication method")
    rate_limit: int = Field(default=10, description="Requests per second")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    endpoints: dict[str, str] = Field(default_factory=dict, description="Named endpoints (e.g. {'me': '/me'})")


class AuthConfig(BaseModel):
    required_env_vars: list[str] = Field(..., description="Required environment variables")
    optional_env_vars: list[str] = Field(default_factory=list, description="Optional environment variables")


class DataConfig(BaseModel):
    source_format: SourceFormat = Field(default=SourceFormat.JSON)
    input_method: InputMethod = Field(default=InputMethod.API)
    time_field: str = Field(default="timestamp")
    cost_field: str = Field(default="cost")
    resource_field: str = Field(default="resource_id")


class CbfMapping(BaseModel):
    """CloudZero Common Billing Format field mappings.

    Field names follow the CBF spec at:
    https://docs.cloudzero.com/docs/anycost-common-bill-format-cbf
    """
    # Required
    cost_cost: str = Field(default="cost")
    time_usage_start: str = Field(default="snapshot_timestamp")

    # Required when tags are present
    resource_id: str = Field(default="")

    # Recommended
    resource_account: str = Field(default="default")
    lineitem_type: str = Field(default="Usage")
    resource_service: str = Field(default="")
    usage_amount: str = Field(default="")
    usage_units: str = Field(default="")

    # Optional -- dimensions
    bill_invoice_id: str = Field(default="")
    lineitem_description: str = Field(default="")
    lineitem_cloud_provider: str = Field(default="")
    resource_region: str = Field(default="global")
    resource_usage_family: str = Field(default="")
    action_operation: str = Field(default="")
    action_usage_type: str = Field(default="")

    # Optional -- cost variants
    cost_discounted_cost: str = Field(default="")
    cost_amortized_cost: str = Field(default="")
    cost_discounted_amortized_cost: str = Field(default="")
    cost_on_demand_cost: str = Field(default="")

    # Optional -- Kubernetes
    k8s_cluster: str = Field(default="")
    k8s_namespace: str = Field(default="")
    k8s_deployment: str = Field(default="")
    k8s_labels: str = Field(default="")

    # Optional -- custom resource tags (resource/tag:<key>)
    # Keys are tag names, values are expressions to extract the tag value.
    resource_tags: dict[str, str] = Field(
        default_factory=dict,
        description="Custom resource tags emitted as resource/tag:<key> columns",
    )


# ---------------------------------------------------------------------------
# Tier-specific optional sections
# ---------------------------------------------------------------------------

class TokenPool(BaseModel):
    field: str
    label: str


class CreditConfig(BaseModel):
    """Tier 1: credit-based polling."""
    credits_endpoint: str = Field(default="")
    credit_to_usd: float = Field(default=0.0, description="Dollars per credit")
    discount_rate: float = Field(default=0.0, description="Discount percentage (0-1)")
    discounted_rate: float = Field(default=0.0, description="Post-discount rate per credit")
    token_pools: list[TokenPool] = Field(default_factory=list)
    contract_value_usd: float = Field(default=0)
    contract_start: str = Field(default="")
    snapshot_file: str = Field(default="state/snapshots.csv")
    model_pricing: dict[str, float] = Field(default_factory=dict)


class FieldMappings(BaseModel):
    cost: dict[str, str] = Field(default_factory=dict)
    date: dict[str, str] = Field(default_factory=dict)
    resource: dict[str, str] = Field(default_factory=dict)
    usage: dict[str, str] = Field(default_factory=dict)


class StructuredConfig(BaseModel):
    """Tier 2: structured billing API with multiple endpoints/line items."""
    root_data_key: str = Field(default="data")
    line_type_field: str = Field(default="")
    field_mappings: FieldMappings = Field(default_factory=FieldMappings)
    tags: list[str] = Field(default_factory=list)
    resource_id_template: str = Field(default="")


class CsvStructure(BaseModel):
    header_rows_to_skip: int = Field(default=0)
    date_column: int = Field(default=0)
    date_format: str = Field(default="%b %Y")
    cost_categories: dict[str, int] = Field(default_factory=dict)


class PricingRule(BaseModel):
    name: str
    contracted_count: int = Field(default=0)
    below_contracted_price: float = Field(default=0.0)
    above_contracted_price: float = Field(default=0.0)
    cumulative_tracking: bool = Field(default=False)


class FixedCost(BaseModel):
    name: str
    monthly_amount: float = Field(default=0.0)
    valid_until: str = Field(default="")
    resource_id: str = Field(default="")


class EnterpriseConfig(BaseModel):
    """Tier 3: CSV processing or complex nested API with contract pricing."""
    csv_structure: Optional[CsvStructure] = None
    nested_response: bool = Field(default=False)
    pricing_rules: list[PricingRule] = Field(default_factory=list)
    fixed_costs: list[FixedCost] = Field(default_factory=list)
    cost_categories: list[str] = Field(default_factory=list)
    aggregation_method: str = Field(default="daily")
    resource_id_templates: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level config
# ---------------------------------------------------------------------------

class ProviderConfig(BaseModel):
    """Top-level unified config. Both YAML and interactive CLI produce this."""
    provider: ProviderInfo
    api: ApiConfig
    auth: AuthConfig
    data: DataConfig = Field(default_factory=DataConfig)
    cbf_mapping: CbfMapping = Field(default_factory=CbfMapping)
    dependencies: list[str] = Field(
        default_factory=lambda: ["requests>=2.28.0", "python-dotenv>=0.19.0"]
    )

    # Tier -- explicit or auto-detected
    tier: Optional[Tier] = Field(default=None, description="Explicit tier override")

    # Tier-specific sections (exactly one should be present, or tier is set explicitly)
    credit_config: Optional[CreditConfig] = None
    structured_config: Optional[StructuredConfig] = None
    enterprise_config: Optional[EnterpriseConfig] = None

    @model_validator(mode="after")
    def resolve_tier(self) -> "ProviderConfig":
        """Auto-detect tier from which optional section is present."""
        if self.tier is not None:
            return self

        if self.credit_config is not None:
            self.tier = Tier.TIER1_CREDIT
        elif self.structured_config is not None:
            self.tier = Tier.TIER2_STRUCTURED
        elif self.enterprise_config is not None:
            self.tier = Tier.TIER3_ENTERPRISE
        else:
            # Default to tier1 if no tier-specific config is present
            self.tier = Tier.TIER1_CREDIT
            self.credit_config = CreditConfig()

        return self

    # -- Derived helpers used by templates --------------------------------

    @property
    def provider_class_name(self) -> str:
        return "".join(word.capitalize() for word in self.provider.name.split("_"))

    @property
    def provider_upper(self) -> str:
        return self.provider.name.upper().replace("-", "_")
