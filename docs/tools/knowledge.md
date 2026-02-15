# Knowledge Base Tools

Access OdooForge's built-in knowledge about Odoo modules, workflows, and best practices. The knowledge base provides curated guidance for 8 core modules.

## `odoo_knowledge_module_info`

Get curated knowledge about a module — models, fields, workflows, and customization points.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `module_name` | `str` | *required* | Module name (e.g., `"sale"`, `"crm"`) |

### Covered Modules

| Module | Description |
|--------|-------------|
| `sale` | Sales orders, quotations, pricing |
| `purchase` | Purchase orders, vendor management |
| `stock` | Inventory, warehousing, logistics |
| `account` | Accounting, invoicing, payments |
| `crm` | CRM pipeline, leads, opportunities |
| `project` | Project management, tasks |
| `hr` | Human resources, employees |
| `website` | Website builder, pages |

**Returns:** Module description, key models, common fields, workflows, and customization suggestions.

**Example:** `"Tell me about the CRM module — what models and workflows does it use?"`

---

## `odoo_knowledge_search`

Search the knowledge base for Odoo information by keyword.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | *required* | Search query |

**Returns:** Matching knowledge entries with module, topic, and content.

**Example:** `"Search knowledge for 'invoice workflow'"`

---

## `odoo_knowledge_community_gaps`

Analyze installed modules and suggest missing modules or configurations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |

**Returns:** Gap analysis with recommendations for missing modules, unconfigured features, and best practices.

**Example:** `"Analyze my installation and suggest what's missing"`
