# View Management Tools

List, inspect, modify, and reset Odoo views. Modifications use XPath inheritance to create inheriting views, leaving base views untouched.

## `odoo_view_list`

List views, optionally filtered by model or type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | `null` | Filter by model (e.g., `"res.partner"`) |
| `view_type` | `str` | `null` | Filter by type: `form`, `tree`, `kanban`, `search` |

**Returns:** View list with ID, name, model, type, and inheritance info.

---

## `odoo_view_get_arch`

Get the full architecture XML of a view. Specify either `view_id` directly or `model` + `view_type` to get the default view.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `view_id` | `int` | `null` | Specific view ID |
| `model` | `str` | `null` | Model name (with `view_type`) |
| `view_type` | `str` | `"form"` | View type: `form`, `tree`, `kanban`, `search` |

**Returns:** View XML architecture, model, type, and view ID.

**Example:** `"Show me the form view XML for res.partner"`

---

## `odoo_view_modify`

Modify a view using XPath inheritance. Creates a new inheriting view that overlays changes on the parent.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `inherit_view_id` | `int` | *required* | Parent view ID to inherit from |
| `view_name` | `str` | *required* | Name for the new inheriting view |
| `xpath_specs` | `list[dict]` | *required* | XPath modification specs |

### XPath Spec Format

```json
[
  {
    "expr": "//field[@name='email']",
    "position": "after",
    "content": "<field name='x_custom'/>"
  }
]
```

**Positions:** `before`, `after`, `replace`, `inside`, `attributes`

**Example:** `"Add field x_tier after the email field on the partner form view"`

---

## `odoo_view_reset`

Delete a custom inheriting view, reverting the parent to its original state. Requires confirmation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `view_id` | `int` | *required* | Inheriting view ID to delete |
| `confirm` | `bool` | `false` | Must be `true` to proceed |

> Only inheriting views can be reset. Base views cannot be deleted.

---

## `odoo_view_list_customizations`

List all custom (inheriting) views that can be reset.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | `null` | Filter by model |

**Returns:** Custom views with ID, name, parent view, and model.
