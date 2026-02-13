"""Tests for adaptor class resolution logic."""

from anycost_generator.config.schema import AdaptorClass
from anycost_generator.classes.resolver import resolve_adaptor_class_from_dict


class TestAdaptorClassResolver:

    def test_explicit_adaptor_class(self):
        assert resolve_adaptor_class_from_dict({"adaptor_class": "class1_credit"}) == AdaptorClass.CLASS1_CREDIT
        assert resolve_adaptor_class_from_dict({"adaptor_class": "class2_structured"}) == AdaptorClass.CLASS2_STRUCTURED
        assert resolve_adaptor_class_from_dict({"adaptor_class": "class3_enterprise"}) == AdaptorClass.CLASS3_ENTERPRISE

    def test_credit_config_detected(self):
        data = {"credit_config": {"credit_to_usd": 0.01}}
        assert resolve_adaptor_class_from_dict(data) == AdaptorClass.CLASS1_CREDIT

    def test_structured_config_detected(self):
        data = {"structured_config": {"root_data_key": "data"}}
        assert resolve_adaptor_class_from_dict(data) == AdaptorClass.CLASS2_STRUCTURED

    def test_enterprise_config_detected(self):
        data = {"enterprise_config": {"nested_response": True}}
        assert resolve_adaptor_class_from_dict(data) == AdaptorClass.CLASS3_ENTERPRISE

    def test_csv_source_format_detected(self):
        data = {"data": {"source_format": "csv"}}
        assert resolve_adaptor_class_from_dict(data) == AdaptorClass.CLASS3_ENTERPRISE

    def test_file_upload_detected(self):
        data = {"data": {"input_method": "file_upload"}}
        assert resolve_adaptor_class_from_dict(data) == AdaptorClass.CLASS3_ENTERPRISE

    def test_legacy_data_structure_with_root_data_key(self):
        data = {"data_structure": {"root_data_key": "data"}}
        assert resolve_adaptor_class_from_dict(data) == AdaptorClass.CLASS2_STRUCTURED

    def test_legacy_data_patterns_csv(self):
        data = {"data_patterns": {"source_format": "csv"}}
        assert resolve_adaptor_class_from_dict(data) == AdaptorClass.CLASS3_ENTERPRISE

    def test_legacy_provider_specific_credit(self):
        data = {
            "provider": {"name": "bfl"},
            "bfl_config": {"credit_to_usd": 0.01},
        }
        assert resolve_adaptor_class_from_dict(data) == AdaptorClass.CLASS1_CREDIT

    def test_default_class1(self):
        assert resolve_adaptor_class_from_dict({}) == AdaptorClass.CLASS1_CREDIT
