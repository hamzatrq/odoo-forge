# Schema Extension Tools

Create and manage custom fields and models. All custom names must use the `x_` prefix to avoid conflicts with core Odoo fields.

## `odoo_schema_field_create`

Create a new custom field on an existing model. No Python code needed — fields are created via the ORM.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Target model (e.g., `"res.partner"`) |
| `field_name` | `str` | *required* | Field name (**must** start with `x_`) |
| `field_type` | `str` | *required* | Field type (see below) |
| `field_label` | `str` | *required* | Human-readable label |
| `required` | `bool` | `false` | Whether the field is required |
| `selection_options` | `list[list[str]]` | `null` | Options for selection fields |
| `relation_model` | `str` | `null` | Related model (for relational fields) |
| `help_text` | `str` | `null` | Tooltip help text |
| `default_value` | `str` | `null` | Default value |
| `copied` | `bool` | `true` | Copy value when duplicating record |

### Supported Field Types

| Type | Description | Extra Params |
|------|-------------|-------------|
| `char` | Short text | — |
| `text` | Long text | — |
| `integer` | Whole number | — |
| `float` | Decimal number | — |
| `boolean` | True/False | — |
| `date` | Date only | — |
| `datetime` | Date and time | — |
| `selection` | Dropdown | `selection_options` required |
| `many2one` | Link to one record | `relation_model` required |
| `one2many` | Link to many records | `relation_model` required |
| `many2many` | Many-to-many link | `relation_model` required |
| `html` | Rich text/HTML | — |
| `binary` | File upload | — |
| `monetary` | Currency amount | — |

**Example:** `"Add a selection field x_tier to res.partner with options Gold, Silver, Bronze"`

---

## `odoo_schema_field_update`

Update properties of an existing custom field (`x_` prefix only).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name |
| `field_name` | `str` | *required* | Field to update |
| `updates` | `dict` | *required* | Properties to change |

**Example:** `"Make x_tier required on res.partner"`

---

## `odoo_schema_field_delete`

Delete a custom field from a model. Requires confirmation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name |
| `field_name` | `str` | *required* | Field to delete |
| `confirm` | `bool` | `false` | Must be `true` to proceed |

> ⚠️ Permanently removes the field and all its data across all records.

---

## `odoo_schema_model_create`

Create a new custom model (database table). Model name must start with `x_`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model_name` | `str` | *required* | Model name (must start with `x_`) |
| `model_label` | `str` | *required* | Human-readable label |
| `fields` | `list[dict]` | `null` | Fields to create with the model |

**Example:** `"Create a model x_equipment with fields x_name (char), x_serial (char), x_purchase_date (date)"`

---

## `odoo_schema_list_custom`

List all custom (manually created) fields and models in the database.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |

**Returns:** Custom models and custom fields grouped by model.
