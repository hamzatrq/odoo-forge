# Planning Tools

3 tools for AI-driven requirement analysis and solution design.

## Tools

### `odoo_analyze_requirements`

Parse a natural language business description into structured requirements.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `description` | string | yes | Natural language business description |

**Returns:** Structured requirements including detected industry, matched blueprint, recommended modules, custom feature needs, and clarifying questions.

**Example:**
```
"I run a bakery with 3 locations. I need inventory management, point of sale, and employee scheduling."
```

Returns modules like `point_of_sale`, `stock`, `hr`, matched blueprint `retail` or `restaurant`, and flags multi-location setup.

---

### `odoo_design_solution`

Generate a phased implementation plan from analyzed requirements.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `requirements` | dict | yes | Output from `odoo_analyze_requirements` |

**Returns:** Ordered phases with steps — module installation order, configuration steps, custom field creation, automation setup, and verification checkpoints.

---

### `odoo_validate_plan`

Validate an implementation plan against knowledge base rules and best practices.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `plan` | dict | yes | Implementation plan to validate |

**Returns:** Validation results — warnings for naming convention violations, missing dependencies, security gaps, and best practice recommendations.
