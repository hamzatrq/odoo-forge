# QWeb Report Tools

Manage Odoo's QWeb report templates — list reports, inspect templates, modify via XPath, preview, and configure layout.

## `odoo_report_list`

List all available reports, optionally filtered by model.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | `null` | Filter by model (e.g., `"account.move"`) |

**Returns:** Report list with name, technical name, model, and type.

---

## `odoo_report_get_template`

Get the QWeb template XML of a report by its technical name.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `report_name` | `str` | *required* | Technical name (e.g., `"sale.report_saleorder"`) |

**Returns:**

| Key | Type | Description |
|-----|------|-------------|
| `found` | `bool` | Whether the report exists |
| `report` | `dict` | Report metadata |
| `templates` | `list` | QWeb template XML(s) |

**Example:** `"Show me the invoice report template XML"`

---

## `odoo_report_modify`

Modify a QWeb report template using XPath inheritance.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `template_id` | `int` | *required* | Template view ID to inherit from |
| `xpath_specs` | `list[dict]` | *required* | XPath modifications |
| `view_name` | `str` | `null` | Name for the inheriting template |

### XPath Spec Format

```json
[
  {
    "expr": "//div[@class='page']",
    "position": "inside",
    "content": "<p>Custom footer text</p>"
  }
]
```

**Example:** `"Add a custom footer to the invoice report"`

---

## `odoo_report_preview`

Generate a report for specific records (returns metadata, not the PDF).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `report_name` | `str` | *required* | Technical report name |
| `record_ids` | `list[int]` | *required* | Record IDs to generate for |

**Returns:** Generation status, record count, HTML length.

---

## `odoo_report_reset`

Remove a custom report template modification. Requires confirmation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `view_id` | `int` | *required* | Inheriting template view ID |
| `confirm` | `bool` | `false` | Must be `true` to proceed |

---

## `odoo_report_layout_configure`

Configure report layout settings — paper format, company logo, company name.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `paperformat` | `str` | `null` | Paper format: `"A4"`, `"Letter"`, etc. |
| `logo` | `str` | `null` | Base64-encoded logo image |
| `company_name` | `str` | `null` | Company name on reports |

**Example:** `"Set report paper format to A4 and company name to 'Acme Corp'"`
