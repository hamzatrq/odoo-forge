# Settings & Company Tools

Configure system settings, company details, and manage users.

## `odoo_settings_get`

Get current system settings from `res.config.settings`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `keys` | `list[str]` | `null` | Specific setting keys (null = all) |

**Returns:** Settings dictionary with key-value pairs.

**Example:** `"Get the current website and email settings"`

---

## `odoo_settings_set`

Update system settings and apply them.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `values` | `dict` | *required* | Setting key-value pairs to update |

**Returns:** Update status and applied values.

**Example:** `"Enable multi-currency support in settings"`

---

## `odoo_company_configure`

Configure main company details — name, address, logo, currency, and more.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `updates` | `dict` | *required* | Company fields to update |

Supported fields include `name`, `email`, `phone`, `street`, `city`, `country_id`, `currency_id`, `logo` (base64), `website`, and more.

**Example:** `"Set company name to 'Acme Corp', email to 'info@acme.com', and city to 'San Francisco'"`

---

## `odoo_users_manage`

Manage users — list, create, update, activate, or deactivate.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `action` | `str` | `"list"` | Action: `"list"`, `"create"`, `"update"`, `"activate"`, `"deactivate"` |
| `user_id` | `int` | `null` | User ID (for update/activate/deactivate) |
| `values` | `dict` | `null` | User data (for create/update) |

### Actions

| Action | Description | Required Params |
|--------|-------------|-----------------|
| `list` | List all users | — |
| `create` | Create a new user | `values` (name, login, password) |
| `update` | Update user fields | `user_id`, `values` |
| `activate` | Activate a user | `user_id` |
| `deactivate` | Deactivate a user | `user_id` |

**Example:** `"Create a user with login 'john@acme.com' and name 'John Smith'"`
