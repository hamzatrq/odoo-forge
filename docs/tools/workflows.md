# Workflow Tools

4 tools for generating multi-step operation plans. Workflow tools return ordered step lists — the AI assistant executes each step using core tools.

## Tools

### `odoo_setup_business`

Generate a complete business deployment plan from a blueprint.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `db_name` | string | yes | Target database |
| `blueprint_name` | string | yes | Industry blueprint (e.g., `restaurant`, `ecommerce`, `manufacturing`) |
| `company_name` | string | no | Company name |
| `dry_run` | boolean | no | Preview steps without execution (default: true) |

**Returns:** Ordered steps: snapshot → company config → module install → settings → custom fields → automations → health check.

---

### `odoo_create_feature`

Generate a custom feature creation plan with fields, views, and optional automation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `db_name` | string | yes | Target database |
| `model` | string | yes | Target model (e.g., `res.partner`) |
| `feature_name` | string | yes | Human-readable feature name |
| `fields` | list | yes | List of field definitions |
| `automation` | dict | no | Optional automation rule |

**Returns:** Ordered steps: snapshot → create fields → modify form view → modify tree view → optional automation → verify.

---

### `odoo_create_dashboard`

Generate a dashboard creation plan with action windows and menus.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `db_name` | string | yes | Target database |
| `name` | string | yes | Dashboard name |
| `metrics` | list | yes | List of metric definitions (model, domain, label) |

**Returns:** Ordered steps: snapshot → create action windows → create parent menu → child menu items → health check.

---

### `odoo_setup_integration`

Generate an integration setup plan for email, payment, or shipping.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `db_name` | string | yes | Target database |
| `integration_type` | string | yes | One of: `email`, `payment`, `shipping` |
| `config` | dict | yes | Type-specific configuration |

**Returns:** Type-specific ordered steps for setting up the integration.
