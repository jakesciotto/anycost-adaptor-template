"""AdaptorGenerator -- orchestrates config -> rendered output.

Takes a validated ProviderConfig, selects the tier strategy,
renders all templates, copies static files, and creates the
output directory structure.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from anycost_generator.config.schema import ProviderConfig, Tier
from anycost_generator.engine.renderer import create_jinja_env, render_template
from anycost_generator.tiers.base import TierStrategy
from anycost_generator.tiers.tier1_credit import Tier1CreditStrategy
from anycost_generator.tiers.tier2_structured import Tier2StructuredStrategy
from anycost_generator.tiers.tier3_enterprise import Tier3EnterpriseStrategy


_STRATEGY_MAP: dict[Tier, type[TierStrategy]] = {
    Tier.TIER1_CREDIT: Tier1CreditStrategy,
    Tier.TIER2_STRUCTURED: Tier2StructuredStrategy,
    Tier.TIER3_ENTERPRISE: Tier3EnterpriseStrategy,
}


class AdaptorGenerator:
    """Orchestrates adaptor generation from a ProviderConfig."""

    def __init__(self, config: ProviderConfig, templates_dir: Path | None = None):
        self.config = config
        self.env = create_jinja_env(templates_dir)
        self.templates_dir = templates_dir or (
            Path(__file__).resolve().parent.parent.parent / "templates"
        )

        strategy_cls = _STRATEGY_MAP.get(config.tier)
        if strategy_cls is None:
            raise ValueError(f"Unknown tier: {config.tier}")
        self.strategy = strategy_cls(config)

    def generate(self, output_dir: str | Path) -> Path:
        """Generate the adaptor project.

        Args:
            output_dir: Target directory for the generated project.

        Returns:
            Path to the output directory.
        """
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        print(f"Generating {self.config.provider.display_name} adaptor ({self.config.tier.value})...")
        print(f"Output directory: {output.absolute()}")

        # Create directory structure
        for directory in self.strategy.get_directories():
            (output / directory).mkdir(parents=True, exist_ok=True)

        # Build template context
        context = self._build_context()

        # Render templates
        manifest = self.strategy.get_template_manifest()
        for template_path, output_file in manifest:
            self._render_file(template_path, output / output_file, context)

        # Copy static files
        for src_rel, dst_rel in self.strategy.get_static_files():
            self._copy_static(src_rel, output / dst_rel)

        print(f"\nSuccessfully generated {self.config.provider.display_name} adaptor!")
        print(f"\nNext steps:")
        print(f"1. cd {output}")
        print(f"2. cp env/.env.example env/.env")
        print(f"3. Edit env/.env with your {self.config.provider.display_name} credentials")
        print(f"4. pip install .")
        print(f"5. Customize the TODO sections in the generated files")
        print(f"6. python anycost.py test")

        return output

    def _build_context(self) -> dict[str, Any]:
        """Build the full template context from config + tier extras."""
        # Dump the entire config as a dict for template access
        ctx = self.config.model_dump()

        # Add derived properties
        ctx["provider_class_name"] = self.config.provider_class_name
        ctx["provider_upper"] = self.config.provider_upper

        # Add tier-specific context
        ctx.update(self.strategy.get_extra_context())

        return ctx

    def _render_file(self, template_path: str, output_path: Path, context: dict[str, Any]):
        """Render a single template and write to output."""
        try:
            rendered = render_template(self.env, template_path, context)
        except Exception as e:
            print(f"Warning: Failed to render {template_path}: {e}")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)
        print(f"  Generated: {output_path}")

    def _copy_static(self, src_rel: str, dst_path: Path):
        """Copy a static (non-templated) file."""
        src_path = self.templates_dir / src_rel
        if not src_path.exists():
            print(f"  Warning: Static file not found: {src_path}")
            return

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)
        print(f"  Copied: {dst_path}")
