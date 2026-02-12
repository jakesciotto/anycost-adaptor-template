"""Tier 2: Structured billing strategy.

Providers with multiple endpoints and structured billing line items
(ElevenLabs, Confluent, SumoLogic).
"""

from __future__ import annotations

from typing import Any

from anycost_generator.tiers.base import TierStrategy


class Tier2StructuredStrategy(TierStrategy):

    def get_template_manifest(self) -> list[tuple[str, str]]:
        return self.get_base_templates() + self.get_src_templates()

    def get_extra_context(self) -> dict[str, Any]:
        sc = self.config.structured_config
        if sc is None:
            return {}
        return {
            "structured_config": sc,
        }
