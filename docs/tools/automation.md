# Automation Tools

Create and manage automated actions (server actions) and email templates. Automation rules trigger server-side logic on record events.

## `odoo_automation_list`

List all automated actions, optionally filtered by model or trigger type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `model` | `str` | `null` | Filter by target model |
| `trigger` | `str` | `null` | Filter by trigger type |

**Returns:** Automation rules with name, model, trigger, and active status.

---

## `odoo_automation_create`

Create a new automated action rule with a server action.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `name` | `str` | *required* | Rule name |
| `model` | `str` | *required* | Target model (e.g., `"res.partner"`) |
| `trigger` | `str` | *required* | When to fire (see below) |
| `action_type` | `str` | `"code"` | Action type (see below) |
| `code` | `str` | `null` | Python code (for `action_type="code"`) |
| `filter_domain` | `str` | `null` | Domain filter for matching records |
| `trigger_fields` | `list[str]` | `null` | Fields that trigger the rule (for `on_write`) |

### Triggers

| Trigger | Description |
|---------|-------------|
| `on_create` | When a record is created |
| `on_write` | When a record is updated |
| `on_unlink` | When a record is deleted |
| `on_create_or_write` | On create or update |
| `on_time` | Time-based (scheduled) |

### Action Types

| Type | Description |
|------|-------------|
| `code` | Execute Python code |
| `object_write` | Update field values |
| `followers` | Add followers |
| `email` | Send email |
| `sms` | Send SMS |

**Example:** `"Create an automation that uppercases partner names when they're created"`

---

## `odoo_automation_update`

Update an existing automation rule.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `rule_id` | `int` | *required* | Automation rule ID |
| `updates` | `dict` | *required* | Fields to update |

**Example:** `"Disable automation rule 5"`

---

## `odoo_automation_delete`

Delete an automation rule. Requires confirmation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `rule_id` | `int` | *required* | Rule ID to delete |
| `confirm` | `bool` | `false` | Must be `true` to proceed |

---

## `odoo_email_template_create`

Create an email template for use in automations or manual sends.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `name` | `str` | *required* | Template name |
| `model` | `str` | *required* | Target model |
| `subject` | `str` | *required* | Email subject (supports Jinja: `{{ object.name }}`) |
| `body_html` | `str` | *required* | HTML body (supports Jinja) |
| `email_from` | `str` | `null` | Sender address |
| `reply_to` | `str` | `null` | Reply-to address |

**Example:** `"Create a welcome email template for res.partner with subject 'Welcome {{object.name}}'"`
