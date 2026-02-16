"""OdooForge Knowledge Base — structured Odoo domain knowledge."""

from __future__ import annotations

from typing import Any


class KnowledgeBase:
    """Central loader for all Odoo domain knowledge.

    Lazy-imports each knowledge sub-module on first instantiation to keep
    import cost low when the knowledge layer is not needed.
    """

    def __init__(self) -> None:
        from odooforge.knowledge.modules import MODULES
        from odooforge.knowledge.dictionary import DICTIONARY
        from odooforge.knowledge.patterns import PATTERNS
        from odooforge.knowledge.best_practices import BEST_PRACTICES
        from odooforge.knowledge.blueprints import BLUEPRINTS

        self._modules = MODULES
        self._dictionary = DICTIONARY
        self._patterns = PATTERNS
        self._best_practices = BEST_PRACTICES
        self._blueprints = BLUEPRINTS

    # ── Module catalog ────────────────────────────────────────────

    def get_modules(self) -> dict[str, Any]:
        """Return the full module knowledge catalog."""
        return self._modules

    # ── Business-to-Odoo dictionary ───────────────────────────────

    def get_dictionary(self) -> dict[str, Any]:
        """Return business-term-to-Odoo-model mappings."""
        return self._dictionary

    # ── Customization patterns ────────────────────────────────────

    def get_patterns(self) -> dict[str, Any]:
        """Return data-model customization patterns."""
        return self._patterns

    # ── Best practices ────────────────────────────────────────────

    def get_best_practices(self) -> dict[str, Any]:
        """Return Odoo convention / best-practice rules."""
        return self._best_practices

    # ── Industry blueprints ───────────────────────────────────────

    def list_blueprints(self) -> list[str]:
        """Return available blueprint IDs."""
        return list(self._blueprints.keys())

    def get_blueprint(self, blueprint_id: str) -> dict[str, Any] | None:
        """Return a single blueprint by ID, or None if not found."""
        return self._blueprints.get(blueprint_id)
