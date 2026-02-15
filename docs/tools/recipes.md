# Recipe Tools

Execute pre-built industry setup recipes that install modules, configure settings, and create initial data.

> See [Industry Recipes](../recipes.md) for detailed recipe descriptions.

## `odoo_recipe_list`

List all available industry setup recipes.

**Parameters:** None

**Returns:** Recipe list with ID, name, description, modules, and step count.

Available recipes: `restaurant`, `ecommerce`, `manufacturing`, `services`, `retail`

---

## `odoo_recipe_execute`

Execute an industry recipe to set up an Odoo instance.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name |
| `recipe_id` | `str` | *required* | Recipe ID (e.g., `"restaurant"`) |
| `dry_run` | `bool` | `true` | Preview without making changes |

### Dry Run Mode (default)

Returns what would be installed and configured without making any changes. **Always preview first.**

### Execute Mode

When `dry_run=false`, the recipe:
1. Installs required modules (skips already-installed)
2. Creates initial data records (categories, stages, work centers, etc.)
3. Returns execution results per step

**Returns:** Step-by-step results and post-setup guidance.

> **Tip:** Create a snapshot before executing: `"Create a snapshot called pre-recipe"`

**Example:** `"Run the ecommerce recipe in dry-run mode, then execute it"`
