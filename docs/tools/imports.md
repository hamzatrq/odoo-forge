# Import Tools

Import data from CSV files into Odoo models. Supports preview, validation, and error handling.

## `odoo_import_preview`

Preview a CSV import — validates field names and shows what would be imported without making changes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Target model (e.g., `"res.partner"`) |
| `csv_data` | `str` | *required* | CSV content as a string |
| `has_header` | `bool` | `true` | Whether CSV has a header row |

**Returns:** Validated fields, sample rows, field mapping, and any warnings.

**Example:** `"Preview this CSV import for res.partner: name,email\nAcme,info@acme.com"`

---

## `odoo_import_execute`

Execute a CSV import into a model. Use `odoo_import_preview` first to validate.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Target model |
| `csv_data` | `str` | *required* | CSV content |
| `has_header` | `bool` | `true` | Whether CSV has a header row |
| `on_error` | `str` | `"stop"` | Error handling: `"stop"` or `"skip"` |

**Returns:** Import status, number of records created, and any errors.

---

## `odoo_import_template`

Generate a CSV template with correct headers for importing into a model.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model to generate template for |
| `include_optional` | `bool` | `false` | Include optional fields |

**Returns:** CSV header string with field names.

**Example:** `"Generate a CSV import template for res.partner with optional fields"`
