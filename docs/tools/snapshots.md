# Snapshot Tools

Create and manage database snapshots for backup and recovery. Use snapshots before risky operations like module installs or schema changes.

## `odoo_snapshot_create`

Create a named snapshot (backup) of a database.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database to snapshot |
| `name` | `str` | *required* | Snapshot name (e.g., `"pre-install"`) |
| `description` | `str` | `""` | Optional description |

**Returns:** Snapshot name, file path, size, timestamp.

**Example:** `"Create a snapshot called 'before-sales-install' for database myshop"`

---

## `odoo_snapshot_list`

List all available snapshots, optionally filtered by database.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | `null` | Filter by database (null = all) |

**Returns:** List of snapshots with name, database, size, and creation date.

---

## `odoo_snapshot_restore`

Restore a database from a previously created snapshot.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Target database name |
| `snapshot_name` | `str` | *required* | Snapshot to restore from |

> ⚠️ This replaces the current database contents entirely.

**Example:** `"Restore myshop from the 'before-sales-install' snapshot"`

---

## `odoo_snapshot_delete`

Delete a snapshot from disk to free space.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Snapshot name to delete |

**Returns:** Deletion confirmation and freed disk space.
