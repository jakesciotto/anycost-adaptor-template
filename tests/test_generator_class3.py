"""End-to-end generation tests for Class 3 (enterprise)."""

import ast
from pathlib import Path

import pytest

from anycost_generator.config.loader import load_from_yaml
from anycost_generator.engine.generator import AdaptorGenerator
from anycost_generator.validation.output_validator import validate_output


class TestClass3Generation:

    def test_generate_from_fixture(self, complex_class3_path, tmp_output):
        config = load_from_yaml(complex_class3_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        assert (output / "src" / "testenterprise_config.py").exists()
        assert (output / "src" / "testenterprise_client.py").exists()
        assert (output / "src" / "testenterprise_transform.py").exists()
        assert (output / "src" / "testenterprise_anycost_adaptor.py").exists()

    def test_python_files_valid_syntax(self, complex_class3_path, tmp_output):
        config = load_from_yaml(complex_class3_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        for py_file in output.rglob("*.py"):
            source = py_file.read_text()
            ast.parse(source)

    def test_no_unresolved_placeholders(self, complex_class3_path, tmp_output):
        config = load_from_yaml(complex_class3_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        issues = validate_output(output, "testenterprise", ["TESTENTERPRISE_TOKEN"])
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"Validation errors: {[str(e) for e in errors]}"

    def test_csv_processing_in_client(self, complex_class3_path, tmp_output):
        config = load_from_yaml(complex_class3_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        client_code = (output / "src" / "testenterprise_client.py").read_text()
        assert "process_csv_file" in client_code

    def test_cost_categories_in_transform(self, complex_class3_path, tmp_output):
        config = load_from_yaml(complex_class3_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        transform_code = (output / "src" / "testenterprise_transform.py").read_text()
        assert "compute" in transform_code
        assert "storage" in transform_code

    def test_fixed_costs_in_transform(self, complex_class3_path, tmp_output):
        config = load_from_yaml(complex_class3_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        transform_code = (output / "src" / "testenterprise_transform.py").read_text()
        assert "support_plan" in transform_code
        assert "5000" in transform_code

    def test_generate_heroku_example(self, examples_dir, tmp_output):
        path = examples_dir / "heroku_config.yaml"
        if not path.exists():
            pytest.skip("Heroku example config not found")
        config = load_from_yaml(path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        issues = validate_output(output, "heroku", ["HEROKU_API_TOKEN", "HEROKU_ENTERPRISE_ACCOUNT_ID"])
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_generate_splunk_csv_example(self, examples_dir, tmp_output):
        path = examples_dir / "splunk_config.yaml"
        if not path.exists():
            pytest.skip("Splunk example config not found")
        config = load_from_yaml(path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        issues = validate_output(output, "splunk", ["SPLUNK_API_KEY"])
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0
