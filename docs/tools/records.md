# Record CRUD Tools

Create, read, update, and delete records in any Odoo model. This is the primary data manipulation interface.

## `odoo_record_search`

Search for records in any Odoo model with domain filters, field selection, and pagination.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name (e.g., `"res.partner"`) |
| `domain` | `list` | `null` | Domain filter (e.g., `[["is_company", "=", true]]`) |
| `fields` | `list[str]` | `null` | Fields to return (null = all) |
| `limit` | `int` | `20` | Max records to return |
| `offset` | `int` | `0` | Pagination offset |
| `order` | `str` | `null` | Sort order (e.g., `"name asc"`) |

**Returns:** Matching records, total count, pagination info.

**Example:** `"Find all companies in res.partner sorted by name"`

---

## `odoo_record_read`

Read specific records by ID.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name |
| `ids` | `list[int]` | *required* | Record IDs to read |
| `fields` | `list[str]` | `null` | Fields to return (null = all) |

---

## `odoo_record_create`

Create one or more records. Field names are validated against the live schema.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name |
| `values` | `dict \| list[dict]` | *required* | Field values (single dict or list for batch) |

**Returns:** Created record ID(s).

**Example:** `"Create a contact: name 'Acme Corp', email 'info@acme.com', is_company true"`

---

## `odoo_record_update`

Update existing records. Field names are validated before writing.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name |
| `ids` | `list[int]` | *required* | Record IDs to update |
| `values` | `dict` | *required* | Fields to update |

**Example:** `"Update partner ID 5: set phone to '+1-555-0100'"`

---

## `odoo_record_delete`

Delete records permanently. Requires confirmation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name |
| `ids` | `list[int]` | *required* | Record IDs to delete |
| `confirm` | `bool` | `false` | Must be `true` to proceed |

> ⚠️ Deletion cannot be undone. Create a snapshot first.

---

## `odoo_record_execute`

Execute any method on any model. This is a generic escape hatch for methods not covered by other tools.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | *required* | Model name |
| `method` | `str` | *required* | Method name |
| `args` | `list` | `null` | Positional arguments |
| `kwargs` | `dict` | `null` | Keyword arguments |

**Example:** `"Execute 'action_confirm' on sale.order for IDs [1, 2, 3]"`
