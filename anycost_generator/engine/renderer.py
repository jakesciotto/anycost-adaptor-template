"""Jinja2 template renderer for the AnyCost Adaptor Generator.

Sets up the Jinja2 environment with:
- StrictUndefined (missing variables raise errors)
- Template search paths for base/, src/, fragments/
- Custom filters and globals
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound


def _get_templates_dir() -> Path:
    """Return the absolute path to the templates/ directory."""
    return Path(__file__).resolve().parent.parent.parent / "templates"


def create_jinja_env(templates_dir: Path | None = None) -> Environment:
    """Create a Jinja2 environment configured for adaptor generation."""
    if templates_dir is None:
        templates_dir = _get_templates_dir()

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Custom filters
    env.filters["quote"] = lambda s: f'"{s}"'
    env.filters["pylist"] = _pylist_filter
    env.filters["indent_lines"] = _indent_lines_filter

    return env


def _pylist_filter(items: list[str], indent: int = 8) -> str:
    """Render a list of strings as a Python list literal."""
    if not items:
        return "[]"
    pad = " " * indent
    entries = [f'{pad}"{item}",' for item in items]
    return "[\n" + "\n".join(entries) + "\n" + " " * (indent - 4) + "]"


def _indent_lines_filter(text: str, spaces: int = 4) -> str:
    """Indent every line of text by the given number of spaces."""
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


def render_template(
    env: Environment,
    template_path: str,
    context: dict[str, Any],
) -> str:
    """Render a single template with the given context.

    Args:
        env: Jinja2 Environment.
        template_path: Path relative to templates/ (e.g. 'base/anycost.py.j2').
        context: Template variables.

    Returns:
        Rendered string.

    Raises:
        TemplateNotFound: If the template file does not exist.
    """
    template = env.get_template(template_path)
    return template.render(**context)
