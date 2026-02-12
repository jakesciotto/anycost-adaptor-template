"""Tests for the Jinja2 renderer."""

import pytest
from jinja2 import TemplateNotFound

from anycost_generator.engine.renderer import create_jinja_env, render_template


class TestRenderer:

    def test_create_env(self):
        env = create_jinja_env()
        assert env is not None
        assert env.undefined.__name__ == "StrictUndefined"

    def test_render_simple_template(self, tmp_path):
        """Test rendering a simple template from a custom dir."""
        (tmp_path / "test.txt.j2").write_text("Hello {{ name }}!")
        env = create_jinja_env(tmp_path)
        result = render_template(env, "test.txt.j2", {"name": "World"})
        assert result == "Hello World!"

    def test_strict_undefined_raises(self, tmp_path):
        (tmp_path / "test.txt.j2").write_text("Hello {{ missing_var }}!")
        env = create_jinja_env(tmp_path)
        with pytest.raises(Exception):
            render_template(env, "test.txt.j2", {})

    def test_template_not_found(self):
        env = create_jinja_env()
        with pytest.raises(TemplateNotFound):
            render_template(env, "nonexistent.j2", {})

    def test_quote_filter(self, tmp_path):
        (tmp_path / "test.j2").write_text("{{ value | quote }}")
        env = create_jinja_env(tmp_path)
        result = render_template(env, "test.j2", {"value": "hello"})
        assert result == '"hello"'

    def test_pylist_filter(self, tmp_path):
        (tmp_path / "test.j2").write_text("{{ items | pylist }}")
        env = create_jinja_env(tmp_path)
        result = render_template(env, "test.j2", {"items": ["a", "b"]})
        assert '"a"' in result
        assert '"b"' in result

    def test_base_templates_exist(self):
        """Verify all base templates can be loaded."""
        env = create_jinja_env()
        for name in ["base/anycost.py.j2", "base/pyproject.toml.j2", "base/env_example.j2",
                      "base/readme.md.j2", "base/gitignore.j2"]:
            template = env.get_template(name)
            assert template is not None

    def test_src_templates_exist(self):
        """Verify all src templates can be loaded."""
        env = create_jinja_env()
        for name in ["src/provider_config.py.j2", "src/provider_client.py.j2",
                      "src/provider_transform.py.j2", "src/provider_anycost_adaptor.py.j2"]:
            template = env.get_template(name)
            assert template is not None
