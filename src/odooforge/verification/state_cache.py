"""Live State Cache — in-memory cache of current Odoo instance state.

Refreshed after every mutating operation so the AI always has current truth.
This is an internal component, not exposed as an MCP tool.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from odooforge.connections.xmlrpc_client import OdooRPC

logger = logging.getLogger(__name__)


class LiveStateCache:
    """In-memory cache of installed modules, model fields, and settings.

    Every mutating tool (install, create, modify) calls refresh methods
    after completion. Tool responses include data from this cache so the
    LLM context always reflects the real instance state.
    """

    def __init__(self, rpc: OdooRPC):
        self.rpc = rpc
        self._installed_modules: dict[str, str] = {}  # name → state
        self._model_fields: dict[str, dict[str, Any]] = {}  # model → fields_get result
        self._available_models: list[str] = []
        self._last_refresh: datetime | None = None

    @property
    def is_initialized(self) -> bool:
        return self._last_refresh is not None

    # ── Refresh methods ─────────────────────────────────────────────

    def refresh_modules(self) -> dict[str, str]:
        """Re-query installed modules from ir_module_module."""
        try:
            modules = self.rpc.search_read(
                "ir.module.module",
                [["state", "=", "installed"]],
                fields=["name", "state", "shortdesc"],
                limit=500,
            )
            self._installed_modules = {m["name"]: m["state"] for m in modules}
            self._last_refresh = datetime.now(timezone.utc)
            logger.debug("Refreshed module cache: %d installed", len(self._installed_modules))
            return self._installed_modules
        except Exception as e:
            logger.warning("Failed to refresh module cache: %s", e)
            return self._installed_modules

    def refresh_model_fields(self, model: str) -> dict[str, Any]:
        """Re-query fields_get for a specific model."""
        try:
            fields = self.rpc.fields_get(model, attributes=["string", "type", "required", "readonly", "relation"])
            self._model_fields[model] = fields
            self._last_refresh = datetime.now(timezone.utc)
            logger.debug("Refreshed fields cache for %s: %d fields", model, len(fields))
            return fields
        except Exception as e:
            logger.warning("Failed to refresh fields for %s: %s", model, e)
            return self._model_fields.get(model, {})

    def refresh_models(self) -> list[str]:
        """Re-query the list of available models."""
        try:
            models = self.rpc.search_read(
                "ir.model",
                [],
                fields=["model"],
                limit=2000,
            )
            self._available_models = [m["model"] for m in models]
            self._last_refresh = datetime.now(timezone.utc)
            return self._available_models
        except Exception as e:
            logger.warning("Failed to refresh models list: %s", e)
            return self._available_models

    def refresh_all(self) -> None:
        """Full refresh — called after major operations like module install."""
        self.refresh_modules()
        self.refresh_models()
        # Don't refresh all model fields — too expensive. Only cached ones.
        for model in list(self._model_fields.keys()):
            self.refresh_model_fields(model)

    # ── Query methods ───────────────────────────────────────────────

    def is_module_installed(self, module_name: str) -> bool:
        """Check if a module is installed."""
        return module_name in self._installed_modules

    def is_field_valid(self, model: str, field_name: str) -> bool:
        """Check if a field exists on a model. Uses cache, falls back to live query."""
        if model in self._model_fields:
            return field_name in self._model_fields[model]
        # Not cached — fetch live
        fields = self.refresh_model_fields(model)
        return field_name in fields

    def get_model_fields(self, model: str) -> dict[str, Any] | None:
        """Get cached fields for a model, or None if not cached."""
        return self._model_fields.get(model)

    def validate_fields(self, model: str, field_names: list[str]) -> list[str]:
        """Validate a list of field names against a model. Returns invalid ones."""
        if model not in self._model_fields:
            self.refresh_model_fields(model)

        fields = self._model_fields.get(model, {})
        if not fields:
            return []  # Can't validate — model might not exist yet

        return [f for f in field_names if f not in fields and f != "id"]

    def get_installed_modules(self) -> dict[str, str]:
        """Get the cached installed modules dict."""
        return dict(self._installed_modules)
