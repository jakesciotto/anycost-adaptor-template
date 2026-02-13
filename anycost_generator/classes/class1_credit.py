"""Class 1: Credit polling strategy.

Simple credit-based providers (BFL, Runware, Leonardo, Luma).
Poll a single endpoint, compute delta, convert credits to USD.
"""

from __future__ import annotations

from typing import Any

from anycost_generator.classes.base import AdaptorClassStrategy


class Class1CreditStrategy(AdaptorClassStrategy):

    def get_template_manifest(self) -> list[tuple[str, str]]:
        return self.get_base_templates() + self.get_src_templates()

    def get_extra_context(self) -> dict[str, Any]:
        cc = self.config.credit_config
        if cc is None:
            return {}
        return {
            "credit_config": cc,
        }
