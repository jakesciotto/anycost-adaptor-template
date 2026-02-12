"""Base tier strategy ABC.

Each tier strategy determines which templates to render and what
extra context they need.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from anycost_generator.config.schema import ProviderConfig


class TierStrategy(ABC):
    """Abstract base for tier-specific generation strategies."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def get_template_manifest(self) -> list[tuple[str, str]]:
        """Return list of (template_path, output_path) tuples.

        template_path is relative to templates/ dir.
        output_path is relative to the output root.
        """

    @abstractmethod
    def get_extra_context(self) -> dict[str, Any]:
        """Return tier-specific extra template context variables."""

    def get_base_templates(self) -> list[tuple[str, str]]:
        """Templates shared by all tiers."""
        name = self.config.provider.name
        return [
            ("base/anycost.py.j2", "anycost.py"),
            ("base/pyproject.toml.j2", "pyproject.toml"),
            ("base/env_example.j2", "env/.env.example"),
            ("base/readme.md.j2", "README.md"),
            ("base/gitignore.j2", ".gitignore"),
        ]

    def get_src_templates(self) -> list[tuple[str, str]]:
        """Source templates rendered with provider name substitution."""
        name = self.config.provider.name
        return [
            ("src/provider_config.py.j2", f"src/{name}_config.py"),
            ("src/provider_client.py.j2", f"src/{name}_client.py"),
            ("src/provider_transform.py.j2", f"src/{name}_transform.py"),
            ("src/provider_anycost_adaptor.py.j2", f"src/{name}_anycost_adaptor.py"),
        ]

    def get_static_files(self) -> list[tuple[str, str]]:
        """Static files to copy verbatim."""
        return [
            ("static/cloudzero.py", "src/cloudzero.py"),
        ]

    def get_directories(self) -> list[str]:
        """Directories to create in the output."""
        return ["env", "input", "output", "tests", "src", "state"]
