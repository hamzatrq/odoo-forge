"""Generate Python model files for an Odoo addon."""

from __future__ import annotations


def _to_class_name(model_name: str) -> str:
    """Convert a dotted model name to a CamelCase class name.

    Examples:
        'x_recipe' -> 'XRecipe'
        'x_recipe.category' -> 'XRecipeCategory'
    """
    parts = model_name.replace(".", "_").split("_")
    return "".join(part.capitalize() for part in parts)


# Field types that take a positional argument before keyword args
_RELATIONAL_FIELDS = {"Many2one", "One2many", "Many2many"}
_SELECTION_FIELD = "Selection"


def _build_field_line(field: dict) -> str:
    """Build a single field definition line."""
    name = field["name"]
    ftype = field["type"]
    positional_args: list[str] = []
    kwargs: dict[str, str] = {}

    if ftype == _SELECTION_FIELD and "selection" in field:
        positional_args.append(repr(field["selection"]))
    elif ftype == "Many2one" and "relation" in field:
        positional_args.append(repr(field["relation"]))
    elif ftype == "One2many" and "relation" in field:
        positional_args.append(repr(field["relation"]))
        if "inverse_field" in field:
            positional_args.append(repr(field["inverse_field"]))
    elif ftype == "Many2many" and "relation" in field:
        positional_args.append(repr(field["relation"]))

    if "string" in field:
        kwargs["string"] = repr(field["string"])
    if field.get("required"):
        kwargs["required"] = "True"
    if field.get("readonly"):
        kwargs["readonly"] = "True"
    if "help" in field:
        kwargs["help"] = repr(field["help"])
    if "default" in field:
        kwargs["default"] = repr(field["default"])

    all_args = positional_args + [f"{k}={v}" for k, v in kwargs.items()]
    args_str = ", ".join(all_args)
    return f"    {name} = fields.{ftype}({args_str})"


def generate_models(model: dict) -> str:
    """Generate a single model Python file."""
    model_name = model["name"]
    class_name = _to_class_name(model_name)
    description = model.get("description", model_name)
    inherits = model.get("inherit", [])
    model_fields = model.get("fields", [])

    lines = [
        "from odoo import models, fields, api",
        "",
        "",
        f"class {class_name}(models.Model):",
        f'    _name = "{model_name}"',
        f'    _description = "{description}"',
    ]

    if inherits:
        lines.append(f"    _inherit = {inherits!r}")

    lines.append("")

    for field in model_fields:
        lines.append(_build_field_line(field))

    lines.append("")
    return "\n".join(lines)


def generate_models_init(models: list[dict]) -> str:
    """Generate models/__init__.py that imports all model files."""
    lines = []
    for model in models:
        module_name = model["name"].replace(".", "_")
        lines.append(f"from . import {module_name}")
    lines.append("")
    return "\n".join(lines)


def generate_top_init() -> str:
    """Generate the top-level __init__.py that imports the models package."""
    return "from . import models\n"
