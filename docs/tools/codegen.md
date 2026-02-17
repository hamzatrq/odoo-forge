# Code Generation

1 tool for generating complete Odoo addon source code.

## Tools

### `odoo_generate_addon`

Generate a complete, installable Odoo addon from model specifications.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `module_name` | string | yes | Module name (must start with `x_`) |
| `models` | list | yes | List of model definitions |
| `description` | string | no | Module description |
| `version` | string | no | Module version (default: `18.0.1.0.0`) |
| `author` | string | no | Module author (default: `OdooForge`) |
| `category` | string | no | Module category (default: `Customizations`) |
| `depends` | list | no | Module dependencies (auto-detected if not specified) |
| `security_groups` | list | no | Custom security group definitions |

**Model Definition Format:**

```json
{
  "name": "x_recipe",
  "description": "Recipe",
  "inherit": ["mail.thread"],
  "fields": [
    {"name": "name", "type": "Char", "required": true, "string": "Name"},
    {"name": "description", "type": "Text", "string": "Description"},
    {"name": "prep_time", "type": "Integer", "string": "Prep Time (min)"},
    {"name": "category_id", "type": "Many2one", "relation": "x_recipe.category", "string": "Category"},
    {"name": "stage", "type": "Selection", "selection": [["draft", "Draft"], ["active", "Active"]], "string": "Stage"}
  ]
}
```

**Returns:**

```json
{
  "module_name": "x_recipe",
  "files": {
    "__manifest__.py": "...",
    "__init__.py": "...",
    "models/__init__.py": "...",
    "models/x_recipe.py": "...",
    "views/x_recipe_views.xml": "...",
    "security/ir.model.access.csv": "..."
  },
  "summary": {
    "models": 1,
    "fields": 5,
    "views": 3,
    "security_groups": 0
  }
}
```

**Generated Files:**

| File | Content |
|------|---------|
| `__manifest__.py` | Module metadata, dependencies, data file references |
| `__init__.py` | Top-level import |
| `models/__init__.py` | Model imports |
| `models/<name>.py` | Python model class with fields |
| `views/<name>_views.xml` | Tree, form, search views + action + menu |
| `security/ir.model.access.csv` | User (CRUD, no delete) + Manager (full) access rules |
| `security/<name>_security.xml` | Security groups (if `security_groups` provided) |

**Features:**

- Auto-detects `mail` dependency when models inherit `mail.thread`
- Generates CamelCase class names from dotted model names
- Adds chatter section to form views when `mail.thread` is inherited
- Creates both user and manager access rules per model
- Supports all field types: Char, Text, Html, Integer, Float, Monetary, Date, Datetime, Boolean, Binary, Selection, Many2one, One2many, Many2many
