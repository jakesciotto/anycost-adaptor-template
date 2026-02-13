"""Tests for the Pydantic config schema and loader."""

import pytest

from anycost_generator.config.schema import (
    AuthMethod,
    CreditConfig,
    ProviderConfig,
    AdaptorClass,
)
from anycost_generator.config.loader import load_from_dict, load_from_yaml


class TestProviderConfig:

    def test_minimal_config(self):
        config = load_from_dict({
            "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
            "api": {"base_url": "https://api.test.com", "auth_method": "api_key"},
            "auth": {"required_env_vars": ["TEST_KEY"]},
        })
        assert config.provider.name == "test"
        assert config.adaptor_class == AdaptorClass.CLASS1_CREDIT
        assert config.credit_config is not None

    def test_adaptor_class_auto_detection_credit(self):
        config = load_from_dict({
            "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
            "api": {"base_url": "https://api.test.com", "auth_method": "api_key"},
            "auth": {"required_env_vars": ["TEST_KEY"]},
            "credit_config": {"credit_to_usd": 0.01},
        })
        assert config.adaptor_class == AdaptorClass.CLASS1_CREDIT

    def test_adaptor_class_auto_detection_structured(self):
        config = load_from_dict({
            "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
            "api": {"base_url": "https://api.test.com", "auth_method": "basic_auth"},
            "auth": {"required_env_vars": ["TEST_KEY", "TEST_SECRET"]},
            "structured_config": {"root_data_key": "data"},
        })
        assert config.adaptor_class == AdaptorClass.CLASS2_STRUCTURED

    def test_adaptor_class_auto_detection_enterprise(self):
        config = load_from_dict({
            "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
            "api": {"base_url": "https://api.test.com", "auth_method": "bearer_token"},
            "auth": {"required_env_vars": ["TEST_TOKEN"]},
            "enterprise_config": {"nested_response": True},
        })
        assert config.adaptor_class == AdaptorClass.CLASS3_ENTERPRISE

    def test_explicit_adaptor_class_override(self):
        config = load_from_dict({
            "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
            "api": {"base_url": "https://api.test.com", "auth_method": "api_key"},
            "auth": {"required_env_vars": ["TEST_KEY"]},
            "adaptor_class": "class2_structured",
        })
        assert config.adaptor_class == AdaptorClass.CLASS2_STRUCTURED

    def test_derived_properties(self):
        config = load_from_dict({
            "provider": {"name": "my_provider", "display_name": "My Provider", "service_type": "cloud"},
            "api": {"base_url": "https://api.test.com", "auth_method": "api_key"},
            "auth": {"required_env_vars": ["MY_KEY"]},
        })
        assert config.provider_class_name == "MyProvider"
        assert config.provider_upper == "MY_PROVIDER"

    def test_auth_methods(self):
        for method in ["api_key", "api_key_header", "basic_auth", "bearer_token", "bearer_jwt", "oauth2"]:
            config = load_from_dict({
                "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
                "api": {"base_url": "https://api.test.com", "auth_method": method},
                "auth": {"required_env_vars": ["TEST_KEY"]},
            })
            assert config.api.auth_method == AuthMethod(method)

    def test_invalid_auth_method(self):
        with pytest.raises(Exception):
            load_from_dict({
                "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
                "api": {"base_url": "https://api.test.com", "auth_method": "invalid"},
                "auth": {"required_env_vars": ["TEST_KEY"]},
            })


class TestLoadFromYaml:

    def test_load_minimal_class1(self, minimal_class1_path):
        config = load_from_yaml(minimal_class1_path)
        assert config.provider.name == "testprovider"
        assert config.adaptor_class == AdaptorClass.CLASS1_CREDIT
        assert config.credit_config.credit_to_usd == 0.01

    def test_load_full_class2(self, full_class2_path):
        config = load_from_yaml(full_class2_path)
        assert config.provider.name == "testbilling"
        assert config.adaptor_class == AdaptorClass.CLASS2_STRUCTURED
        assert config.structured_config.root_data_key == "data"

    def test_load_complex_class3(self, complex_class3_path):
        config = load_from_yaml(complex_class3_path)
        assert config.provider.name == "testenterprise"
        assert config.adaptor_class == AdaptorClass.CLASS3_ENTERPRISE
        assert config.enterprise_config.csv_structure is not None
        assert config.enterprise_config.csv_structure.header_rows_to_skip == 2


class TestLegacyConfigNormalization:

    def test_slash_keyed_cbf_mapping(self):
        config = load_from_dict({
            "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
            "api": {"base_url": "https://api.test.com", "auth_method": "api_key"},
            "auth": {"required_env_vars": ["TEST_KEY"]},
            "cbf_mapping": {
                "time/usage_start": "snapshot_timestamp",
                "cost/cost": "credits * 0.01",
            },
        })
        assert config.cbf_mapping.time_usage_start == "snapshot_timestamp"
        assert config.cbf_mapping.cost_cost == "credits * 0.01"

    def test_legacy_provider_specific_config(self):
        """Test that bfl_config key gets mapped to credit_config."""
        config = load_from_dict({
            "provider": {"name": "bfl", "display_name": "BFL", "service_type": "ai"},
            "api": {"base_url": "https://api.bfl.ai", "auth_method": "api_key"},
            "auth": {"required_env_vars": ["BFL_API_KEY"]},
            "bfl_config": {"credit_to_usd": 0.01, "credits_endpoint": "/me"},
        })
        assert config.adaptor_class == AdaptorClass.CLASS1_CREDIT
        assert config.credit_config.credit_to_usd == 0.01

    def test_top_level_endpoints_moved_to_api(self):
        config = load_from_dict({
            "provider": {"name": "test", "display_name": "Test", "service_type": "testing"},
            "api": {"base_url": "https://api.test.com", "auth_method": "api_key"},
            "auth": {"required_env_vars": ["TEST_KEY"]},
            "endpoints": {"me": "/me", "usage": "/usage"},
        })
        assert config.api.endpoints == {"me": "/me", "usage": "/usage"}
