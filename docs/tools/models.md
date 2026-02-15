# Model Introspection Tools

Explore the Odoo schema — list models, inspect fields, and search across models.

## `odoo_model_list`

List all available models (database tables) in Odoo.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `search` | `str` | `null` | Filter by name or description |
| `transient` | `bool` | `false` | Include wizard/transient models |

**Returns:** Model list with technical name, label, and record count.

**Example:** `"List all models related to 'partner'"`

---

## `odoo_model_fields`

Get all fields of a model with types and attributes. This is the source of truth for what fields exist.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name (e.g., `"res.partner"`) |
| `field_type` | `str` | `null` | Filter by type (`"char"`, `"many2one"`, etc.) |
| `search` | `str` | `null` | Filter by field name or label |

**Returns:** Field list with name, type, label, required, readonly, and relation info.

**Example:** `"Show me all many2one fields on res.partner"`

---

## `odoo_model_search_field`

Search for fields across all models or within a specific model. Useful when you know a field exists but aren't sure which model it's on.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `query` | `str` | *required* | Field name or label to search |
| `model` | `str` | `null` | Limit search to a specific model |

**Returns:** Matching fields with model name, field name, type, and label.

**Example:** `"Search for any field named 'vat' across all models"`
