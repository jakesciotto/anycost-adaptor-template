"""Tests for tier resolution logic."""

from anycost_generator.config.schema import Tier
from anycost_generator.tiers.resolver import resolve_tier_from_dict


class TestTierResolver:

    def test_explicit_tier(self):
        assert resolve_tier_from_dict({"tier": "tier1_credit"}) == Tier.TIER1_CREDIT
        assert resolve_tier_from_dict({"tier": "tier2_structured"}) == Tier.TIER2_STRUCTURED
        assert resolve_tier_from_dict({"tier": "tier3_enterprise"}) == Tier.TIER3_ENTERPRISE

    def test_credit_config_detected(self):
        data = {"credit_config": {"credit_to_usd": 0.01}}
        assert resolve_tier_from_dict(data) == Tier.TIER1_CREDIT

    def test_structured_config_detected(self):
        data = {"structured_config": {"root_data_key": "data"}}
        assert resolve_tier_from_dict(data) == Tier.TIER2_STRUCTURED

    def test_enterprise_config_detected(self):
        data = {"enterprise_config": {"nested_response": True}}
        assert resolve_tier_from_dict(data) == Tier.TIER3_ENTERPRISE

    def test_csv_source_format_detected(self):
        data = {"data": {"source_format": "csv"}}
        assert resolve_tier_from_dict(data) == Tier.TIER3_ENTERPRISE

    def test_file_upload_detected(self):
        data = {"data": {"input_method": "file_upload"}}
        assert resolve_tier_from_dict(data) == Tier.TIER3_ENTERPRISE

    def test_legacy_data_structure_with_root_data_key(self):
        data = {"data_structure": {"root_data_key": "data"}}
        assert resolve_tier_from_dict(data) == Tier.TIER2_STRUCTURED

    def test_legacy_data_patterns_csv(self):
        data = {"data_patterns": {"source_format": "csv"}}
        assert resolve_tier_from_dict(data) == Tier.TIER3_ENTERPRISE

    def test_legacy_provider_specific_credit(self):
        data = {
            "provider": {"name": "bfl"},
            "bfl_config": {"credit_to_usd": 0.01},
        }
        assert resolve_tier_from_dict(data) == Tier.TIER1_CREDIT

    def test_default_tier1(self):
        assert resolve_tier_from_dict({}) == Tier.TIER1_CREDIT
