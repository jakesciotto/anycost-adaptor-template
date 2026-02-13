"""End-to-end generation tests for Class 1 (credit polling)."""

import ast
from pathlib import Path

import pytest

from anycost_generator.config.loader import load_from_yaml
from anycost_generator.engine.generator import AdaptorGenerator
from anycost_generator.validation.output_validator import validate_output


class TestClass1Generation:

    def test_generate_from_fixture(self, minimal_class1_path, tmp_output):
        config = load_from_yaml(minimal_class1_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        # All expected files exist
        assert (output / "anycost.py").exists()
        assert (output / "pyproject.toml").exists()
        assert (output / "README.md").exists()
        assert (output / ".gitignore").exists()
        assert (output / "env" / ".env.example").exists()
        assert (output / "src" / "testprovider_config.py").exists()
        assert (output / "src" / "testprovider_client.py").exists()
        assert (output / "src" / "testprovider_transform.py").exists()
        assert (output / "src" / "testprovider_anycost_adaptor.py").exists()
        assert (output / "src" / "cloudzero.py").exists()

    def test_python_files_valid_syntax(self, minimal_class1_path, tmp_output):
        config = load_from_yaml(minimal_class1_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        for py_file in output.rglob("*.py"):
            source = py_file.read_text()
            ast.parse(source)  # Raises SyntaxError if invalid

    def test_no_unresolved_placeholders(self, minimal_class1_path, tmp_output):
        config = load_from_yaml(minimal_class1_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        issues = validate_output(output, "testprovider", ["TEST_API_KEY"])
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"Validation errors: {[str(e) for e in errors]}"

    def test_env_example_contains_required_vars(self, minimal_class1_path, tmp_output):
        config = load_from_yaml(minimal_class1_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        env_content = (output / "env" / ".env.example").read_text()
        assert "TEST_API_KEY" in env_content
        assert "CLOUDZERO_API_KEY" in env_content

    def test_pyproject_has_provider_name(self, minimal_class1_path, tmp_output):
        config = load_from_yaml(minimal_class1_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        pyproject = (output / "pyproject.toml").read_text()
        assert "testprovider-anycost-adaptor" in pyproject

    def test_generate_bfl_example(self, examples_dir, tmp_output):
        bfl_path = examples_dir / "bfl_config.yaml"
        if not bfl_path.exists():
            pytest.skip("BFL example config not found")
        config = load_from_yaml(bfl_path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        issues = validate_output(output, "bfl", ["BFL_API_KEY"])
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_generate_leonardo_example(self, examples_dir, tmp_output):
        path = examples_dir / "leonardo_config.yaml"
        if not path.exists():
            pytest.skip("Leonardo example config not found")
        config = load_from_yaml(path)
        gen = AdaptorGenerator(config)
        output = gen.generate(tmp_output)

        # Leonardo has multi-pool credits, verify the client references them
        client_code = (output / "src" / "leonardo_client.py").read_text()
        assert "apiSubscriptionTokens" in client_code.lower() or "apisubscriptiontokens" in client_code
