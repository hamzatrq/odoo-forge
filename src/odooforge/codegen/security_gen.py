"""Generate security files (access CSV and groups XML) for an Odoo addon."""

from __future__ import annotations


def generate_access_csv(
    models: list[dict],
    security_groups: list[dict] | None = None,
) -> str:
    """Generate security/ir.model.access.csv content.

    Creates user (read/write/create) and manager (full) access lines per model.
    """
    lines = ["id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink"]

    for model in models:
        model_technical = model["name"].replace(".", "_")
        lines.append(
            f"access_{model_technical}_user,"
            f"{model['name']}.user,"
            f"model_{model_technical},"
            f"base.group_user,"
            f"1,1,1,0"
        )
        lines.append(
            f"access_{model_technical}_manager,"
            f"{model['name']}.manager,"
            f"model_{model_technical},"
            f"base.group_system,"
            f"1,1,1,1"
        )

    lines.append("")
    return "\n".join(lines)


def generate_security_xml(
    module_name: str,
    security_groups: list[dict],
) -> str:
    """Generate a security XML file with res.groups records."""
    records: list[str] = []

    for group in security_groups:
        group_id = f"{module_name}_group_{group['name']}"
        desc = group.get("description", group["name"])

        implied = ""
        if "implied_group" in group:
            implied = (
                f'\n            <field name="implied_ids" eval="'
                f"[(4, ref('{group['implied_group']}'))]"
                f'"/>'
            )

        records.append(
            f'    <record id="{group_id}" model="res.groups">\n'
            f'        <field name="name">{desc}</field>{implied}\n'
            f"    </record>"
        )

    records_str = "\n\n".join(records)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<odoo>
{records_str}
</odoo>
"""
