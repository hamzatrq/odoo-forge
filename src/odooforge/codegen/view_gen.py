"""Generate XML view files for an Odoo addon."""

from __future__ import annotations

# Field types that are typically shown in tree/list views
_TREE_FIELD_TYPES = {
    "Char", "Text", "Integer", "Float", "Boolean", "Date", "Datetime",
    "Selection", "Many2one", "Monetary",
}

# Field types searchable in search views
_SEARCH_FIELD_TYPES = {
    "Char", "Text", "Selection", "Many2one", "Date", "Datetime",
}


def _xml_escape(text: str) -> str:
    """Escape special XML characters."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_views(model: dict) -> str:
    """Generate a complete views XML file for a model.

    Includes tree, form, search views, an action, and a menu item.
    """
    model_name = model["name"]
    model_technical = model_name.replace(".", "_")
    description = model.get("description", model_name)
    inherits = model.get("inherit", [])
    model_fields = model.get("fields", [])
    has_chatter = "mail.thread" in inherits or "mail.activity.mixin" in inherits

    # Determine which fields go into each view
    tree_fields = [f for f in model_fields if f.get("type") in _TREE_FIELD_TYPES]
    search_fields = [f for f in model_fields if f.get("type") in _SEARCH_FIELD_TYPES]
    form_fields = model_fields  # all fields in form

    # -- Tree View --
    tree_field_lines = "\n".join(
        f'                <field name="{f["name"]}"/>' for f in tree_fields
    )

    # -- Form View --
    form_field_lines = "\n".join(
        f'                        <field name="{f["name"]}"/>' for f in form_fields
    )

    chatter_section = ""
    if has_chatter:
        chatter_section = (
            "\n                <div class=\"oe_chatter\">"
            "\n                    <field name=\"message_follower_ids\"/>"
            "\n                    <field name=\"activity_ids\"/>"
            "\n                    <field name=\"message_ids\"/>"
            "\n                </div>"
        )

    # -- Search View --
    search_field_lines = "\n".join(
        f'                <field name="{f["name"]}"/>' for f in search_fields
    )

    # Pluralize description for menu/action name
    action_name = _xml_escape(description + "s" if not description.endswith("s") else description)
    escaped_desc = _xml_escape(description)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <!-- Tree View -->
    <record id="{model_technical}_view_tree" model="ir.ui.view">
        <field name="name">{model_name}.view.tree</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <tree>
{tree_field_lines}
            </tree>
        </field>
    </record>

    <!-- Form View -->
    <record id="{model_technical}_view_form" model="ir.ui.view">
        <field name="name">{model_name}.view.form</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
{form_field_lines}
                    </group>
                </sheet>{chatter_section}
            </form>
        </field>
    </record>

    <!-- Search View -->
    <record id="{model_technical}_view_search" model="ir.ui.view">
        <field name="name">{model_name}.view.search</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <search>
{search_field_lines}
            </search>
        </field>
    </record>

    <!-- Action -->
    <record id="{model_technical}_action" model="ir.actions.act_window">
        <field name="name">{action_name}</field>
        <field name="res_model">{model_name}</field>
        <field name="view_mode">tree,form</field>
    </record>

    <!-- Menu -->
    <menuitem id="{model_technical}_menu_root" name="{action_name}" action="{model_technical}_action"/>
</odoo>
"""
    return xml
