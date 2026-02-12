"""Tier 3: Enterprise / complex strategy.

Providers with CSV processing, nested API responses, contract pricing,
and aggregation (Heroku, Splunk).
"""

from __future__ import annotations

from typing import Any

from anycost_generator.tiers.base import TierStrategy


class Tier3EnterpriseStrategy(TierStrategy):

    def get_template_manifest(self) -> list[tuple[str, str]]:
        return self.get_base_templates() + self.get_src_templates()

    def get_extra_context(self) -> dict[str, Any]:
        ec = self.config.enterprise_config
        if ec is None:
            return {}
        return {
            "enterprise_config": ec,
        }
