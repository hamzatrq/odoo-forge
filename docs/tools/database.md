# Database Management Tools

Create, manage, backup, and restore Odoo databases. Includes raw SQL access.

## `odoo_db_create`

Create a new Odoo database and initialize the base module.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `language` | `str` | `"en_US"` | Default language |
| `country` | `str` | `null` | Country code (e.g., `"US"`) |
| `demo_data` | `bool` | `false` | Load demo/sample data |
| `admin_password` | `str` | `"admin"` | Admin user password |

**Returns:** Database creation status, admin credentials.

**Example:** `"Create a database called myshop with US localization and demo data"`

---

## `odoo_db_list`

List all databases on the Odoo instance.

**Parameters:** None

**Returns:** List of database names.

---

## `odoo_db_backup`

Create a backup of a database using `pg_dump`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database to back up |

**Returns:** Backup file path, size, timestamp.

---

## `odoo_db_restore`

Restore a database from a backup snapshot.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Target database name |
| `backup_name` | `str` | *required* | Backup snapshot name |
| `overwrite` | `bool` | `false` | Replace existing database |

**Returns:** Restore status.

---

## `odoo_db_drop`

Permanently drop a database. Requires confirmation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database to drop |
| `confirm` | `bool` | `false` | Must be `true` to proceed |

> ⚠️ This permanently deletes the database and all its data.

---

## `odoo_db_run_sql`

Execute a raw SQL query against a database.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Target database |
| `query` | `str` | *required* | SQL query string |
| `params` | `list` | `null` | Query parameters (for parameterized queries) |

**Returns:** Rows for `SELECT` queries, execution status for others.

> ⚠️ Bypasses Odoo's ORM — use with caution. Consider using record tools for standard operations.

**Example:** `"Run SQL: SELECT count(*) FROM res_partner WHERE is_company = true"`
