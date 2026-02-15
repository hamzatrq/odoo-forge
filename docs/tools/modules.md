# Module Management Tools

Install, upgrade, and manage Odoo modules with dependency resolution and post-install verification.

## `odoo_module_list_available`

List all modules available for installation, optionally filtered by category.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `category` | `str` | `null` | Filter by category name |

**Returns:** Module list with name, state, summary, and category.

---

## `odoo_module_list_installed`

List all currently installed modules.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |

**Returns:** Installed modules with name, version, and summary.

---

## `odoo_module_info`

Get detailed information about a specific module including dependencies and description.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `module_name` | `str` | *required* | Technical module name (e.g., `"sale"`) |

**Returns:**

| Key | Type | Description |
|-----|------|-------------|
| `found` | `bool` | Whether the module exists |
| `name` | `str` | Technical name |
| `shortdesc` | `str` | Human-readable name |
| `state` | `str` | `installed`, `uninstalled`, etc. |
| `dependencies` | `list` | Required module dependencies |

---

## `odoo_module_install`

Install one or more Odoo modules with automatic dependency resolution. Includes post-install verification.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `modules` | `list[str]` | *required* | Module names to install |

**Returns:** Installation status per module, verification results.

> **Tip:** Create a snapshot before installing modules.

**Example:** `"Install the sales, crm, and inventory modules"`

---

## `odoo_module_upgrade`

Upgrade (update) installed modules to apply code changes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `modules` | `list[str]` | *required* | Module names to upgrade |

---

## `odoo_module_uninstall`

Uninstall a module. Requires confirmation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `module_name` | `str` | *required* | Module to uninstall |
| `confirm` | `bool` | `false` | Must be `true` to proceed |

> ⚠️ May delete data created by the module. Create a snapshot first!

**Example:** `"Uninstall the website module, I confirm"`
