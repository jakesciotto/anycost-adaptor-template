"""End-to-end generation tests for Tier 2 (structured billing)."""

import ast
from pathlib import Path

import pytest

from anycost_generator.config.loader import load_from_yaml
from anycost_generator.engine.generator import AdaptorGenerator
from anycost_generator.validation.output_validator import validate_output


class TestTier2Generation:

    def test_generate_from_fixture(self, full_tier2_path, tmp_output):
        config = load_from_yaml(full_tier2_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        assert (output / "src" / "testbilling_config.py").exists()
        assert (output / "src" / "testbilling_client.py").exists()
        assert (output / "src" / "testbilling_transform.py").exists()
        assert (output / "src" / "testbilling_anycost_adaptor.py").exists()

    def test_python_files_valid_syntax(self, full_tier2_path, tmp_output):
        config = load_from_yaml(full_tier2_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        for py_file in output.rglob("*.py"):
            source = py_file.read_text()
            ast.parse(source)

    def test_no_unresolved_placeholders(self, full_tier2_path, tmp_output):
        config = load_from_yaml(full_tier2_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        issues = validate_output(output, "testbilling", ["TESTBILLING_ACCESS_KEY", "TESTBILLING_SECRET_KEY"])
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"Validation errors: {[str(e) for e in errors]}"

    def test_basic_auth_in_config(self, full_tier2_path, tmp_output):
        config = load_from_yaml(full_tier2_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        config_code = (output / "src" / "testbilling_config.py").read_text()
        assert "Basic" in config_code or "base64" in config_code

    def test_fetch_billing_data_method(self, full_tier2_path, tmp_output):
        config = load_from_yaml(full_tier2_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        client_code = (output / "src" / "testbilling_client.py").read_text()
        assert "fetch_billing_data" in client_code

    def test_generate_confluent_example(self, examples_dir, tmp_output):
        path = examples_dir / "confluent_config.yaml"
        if not path.exists():
            pytest.skip("Confluent example config not found")
        config = load_from_yaml(path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        issues = validate_output(output, "confluent", ["CONFLUENT_API_KEY", "CONFLUENT_API_SECRET"])
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0
