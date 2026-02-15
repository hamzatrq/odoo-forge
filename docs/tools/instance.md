# Instance Management Tools

Manage the Odoo Docker environment — start, stop, restart, check status, and read logs.

> **Requires:** Docker and Docker Compose

## `odoo_instance_start`

Start the Odoo Docker environment (Odoo + PostgreSQL). Brings up both containers and waits for Odoo to be healthy.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | `int` | `8069` | Port to expose Odoo on |

**Returns:** Container status, ports, and health check result.

**Example:** `"Start the Odoo instance on port 8069"`

---

## `odoo_instance_stop`

Stop the running Odoo Docker environment.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `remove_volumes` | `bool` | `false` | Also erase all data (⚠️ destructive) |

**Returns:** Stop confirmation.

> ⚠️ Setting `remove_volumes=true` permanently deletes all Odoo data.

**Example:** `"Stop the Odoo instance"`

---

## `odoo_instance_restart`

Restart the Odoo web service (not PostgreSQL). Useful after configuration changes or to reload the module registry.

**Parameters:** None

**Returns:** Restart confirmation.

**Example:** `"Restart Odoo to pick up the config changes"`

---

## `odoo_instance_status`

Returns health status of all containers, exposed ports, and Odoo version.

**Parameters:** None

**Returns:**

| Key | Type | Description |
|-----|------|-------------|
| `containers` | `list` | Container name, status, health |
| `odoo_version` | `str` | Detected Odoo version |
| `ports` | `dict` | Exposed port mappings |

**Example:** `"What's the status of my Odoo instance?"`

---

## `odoo_instance_logs`

Retrieve Odoo server logs with optional filtering.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lines` | `int` | `100` | Number of log lines to return |
| `level_filter` | `str` | `null` | Filter by level: `ERROR`, `WARNING`, `INFO` |
| `since` | `str` | `null` | Time filter (e.g., `"1h"`, `"30m"`) |
| `grep` | `str` | `null` | Regex pattern to filter lines |

**Returns:** Filtered log lines.

**Example:** `"Show me the last 50 error logs from the past hour"`
