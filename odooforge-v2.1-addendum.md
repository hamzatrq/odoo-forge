# OdooForge Architecture — V2.1 Addendum

## Addressing Final Audit Gaps

This addendum slots into the V2 blueprint. It adds **12 new tools** (58 → 70 total), modifies 3 existing tools, and adds 2 new utility modules.

---

## 1. SCHEMA EXTENSION TOOLS (New Section 5.13)

### Why This Is Critical

Odoo's external API supports creating custom fields and models dynamically via `ir.model.fields` and `ir.model`. However, there's a catch the reviewer correctly identified: simply creating a record in `ir.model.fields` doesn't make the ORM recognize the column. The field must be created with `state='manual'`, and crucially, you must trigger a **registry reload** afterward (restart the Odoo worker or call `registry.reset()` via the internal API).

In Docker, the cleanest way to force a registry reload is to restart the Odoo service. This takes ~3-5 seconds and is imperceptible in a configuration workflow.

### Custom Field Rules in Odoo

- Custom field names **must** start with `x_` (Odoo enforces this)
- Custom model names **must** start with `x_` 
- Fields must have `state='manual'` to be loaded by the ORM
- Computed fields **cannot** be created via the external API (no Python code execution)
- Relational fields (Many2one, One2many, Many2many) work but require the target model to exist
- After field creation, the Odoo service needs a registry reload (restart worker)

### Tool Specifications

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_schema_field_create                                   │
│ Creates a custom field on an existing Odoo model                 │
│                                                                  │
│ Params:                                                          │
│   db_name: str                                                   │
│   model: str (e.g., "product.template")                          │
│   name: str (must start with "x_", e.g., "x_spiciness_level")   │
│   field_type: "char" | "text" | "integer" | "float" | "boolean" │
│               | "date" | "datetime" | "selection" | "html"      │
│               | "monetary" | "many2one" | "one2many" | "many2many│
│   label: str (human-readable, e.g., "Spiciness Level")          │
│   help_text?: str (tooltip shown on hover)                       │
│   required?: bool (default false)                                │
│   default_value?: str | int | float | bool                      │
│   selection_options?: list of [value, label] pairs               │
│     (required when field_type="selection")                       │
│     e.g., [["1", "Mild"], ["2", "Medium"], ["3", "Hot"],        │
│            ["4", "Very Hot"], ["5", "Nuclear"]]                  │
│   relation?: str (required for many2one/one2many/many2many)      │
│     e.g., "res.partner" for a Many2one to contacts               │
│   relation_field?: str (required for one2many — the inverse)     │
│   groups?: list of group XML IDs (field-level access control)    │
│   copied?: bool (default true — copy field when duplicating)     │
│   add_to_view?: bool (default true — auto-add to form view)     │
│   view_position?: dict (if add_to_view=true):                   │
│     { "after": "field_name" } or { "before": "field_name" }     │
│                                                                  │
│ Returns:                                                         │
│   field_id: int (ir.model.fields record ID)                     │
│   technical_name: str (the x_ prefixed name)                    │
│   added_to_view: bool + view_id if applicable                   │
│   registry_reloaded: bool                                        │
│                                                                  │
│ Internal Steps:                                                  │
│   1. Validate name starts with "x_" (auto-prefix if not)        │
│   2. Validate model exists via Live State Cache                  │
│   3. Check field doesn't already exist                           │
│   4. Create ir.model.fields record with state='manual'          │
│   5. Restart Odoo service (docker compose restart web)           │
│   6. Wait for Odoo to be healthy (poll /web/health)             │
│   7. Verify field exists via fields_get()                        │
│   8. Update Live State Cache                                     │
│   9. If add_to_view=true, call odoo_view_modify internally      │
│      to add the field to the form view at the specified position │
│                                                                  │
│ Example Scenarios:                                               │
│                                                                  │
│ "Track spiciness on products":                                   │
│   model="product.template", name="x_spiciness_level",           │
│   field_type="selection", label="Spiciness Level",              │
│   selection_options=[["1","Mild"],["3","Medium"],["5","Hot"]]    │
│   add_to_view=true, view_position={"after": "categ_id"}         │
│                                                                  │
│ "Add loyalty points to customers":                               │
│   model="res.partner", name="x_loyalty_points",                 │
│   field_type="integer", label="Loyalty Points",                 │
│   default_value=0, add_to_view=true                             │
│                                                                  │
│ "Link products to a supplier region":                            │
│   model="product.template", name="x_supplier_region",           │
│   field_type="char", label="Supplier Region",                   │
│   help_text="Geographic region of the primary supplier"          │
│                                                                  │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_schema_field_update                                   │
│ Modifies properties of an existing custom field                  │
│                                                                  │
│ Params:                                                          │
│   db_name: str                                                   │
│   model: str                                                     │
│   name: str (the x_ field name)                                  │
│   changes: dict — any of:                                        │
│     label?: str (display name)                                   │
│     help_text?: str                                              │
│     required?: bool                                              │
│     default_value?: any                                          │
│     selection_options?: list (for selection fields — REPLACES)   │
│     groups?: list of group XML IDs                               │
│                                                                  │
│ Returns: Status, updated field summary                           │
│ Post-action: Restart Odoo + verify + refresh cache               │
│                                                                  │
│ Notes: Cannot change field_type after creation (Odoo limitation).│
│        Cannot modify non-custom (non x_) fields.                 │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_schema_field_delete                                   │
│ Removes a custom field from a model                              │
│                                                                  │
│ Params:                                                          │
│   db_name: str                                                   │
│   model: str                                                     │
│   name: str (must be x_ field)                                   │
│   confirm: bool (must be true)                                   │
│   auto_snapshot?: bool (default true)                            │
│                                                                  │
│ Returns: Status, data_loss_warning (shows record count that had  │
│          values in this field)                                   │
│                                                                  │
│ Notes: This DELETES the database column and all data in it.      │
│        Auto-removes field from any views that reference it.      │
│        Creates snapshot before deletion by default.              │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_schema_model_create                                   │
│ Creates a new custom model (database table)                      │
│                                                                  │
│ Params:                                                          │
│   db_name: str                                                   │
│   name: str (must start with "x_", e.g., "x_recipe")            │
│   label: str (human-readable, e.g., "Recipe")                   │
│   fields: list of field definitions (same shape as               │
│           odoo_schema_field_create params, minus model)          │
│   create_menu?: bool (default true — creates a menu entry)      │
│   menu_parent?: str (parent menu XML ID, e.g., "stock.menu_     │
│                 stock_root" to put under Inventory)               │
│   create_default_views?: bool (default true — auto-generates    │
│                 form and tree views for the model)                │
│                                                                  │
│ Returns:                                                         │
│   model_id: int (ir.model record ID)                             │
│   technical_name: str                                            │
│   field_ids: list of created field IDs                           │
│   view_ids: list of auto-created view IDs                        │
│   menu_id: int (if create_menu=true)                             │
│                                                                  │
│ Internal Steps:                                                  │
│   1. Create ir.model record with state='manual'                 │
│   2. Create ir.model.fields records for each field               │
│   3. Restart Odoo service                                        │
│   4. Create ir.ui.view records (form + tree) if requested        │
│   5. Create ir.ui.menu + ir.actions.act_window if requested      │
│   6. Create ir.model.access (default: full access for admin,     │
│      read for internal users)                                    │
│   7. Verify everything works                                     │
│                                                                  │
│ Example: "I need a recipe tracking table with name, ingredients, │
│          prep time, and a link to the product it produces"        │
│   name="x_recipe", label="Recipe",                              │
│   fields=[                                                       │
│     {name: "x_name", type: "char", label: "Recipe Name",        │
│      required: true},                                            │
│     {name: "x_ingredients", type: "text", label: "Ingredients"}, │
│     {name: "x_prep_time", type: "integer",                      │
│      label: "Prep Time (min)"},                                  │
│     {name: "x_product_id", type: "many2one",                    │
│      relation: "product.template", label: "Product"}             │
│   ]                                                              │
│                                                                  │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_schema_list_custom                                    │
│ Lists all custom fields and models created by OdooForge/user     │
│                                                                  │
│ Params: db_name, model_filter? (specific model or "all")         │
│ Returns: Custom models with their fields, custom fields on       │
│          standard models, creation dates                         │
│ Annotations: readOnly=true                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Detail

```python
# Creating a custom selection field via XML-RPC
async def create_custom_field(rpc: OdooRPC, docker: OdooDocker,
                              cache: LiveStateCache,
                              model: str, name: str, field_type: str,
                              label: str, **kwargs) -> dict:
    # 1. Get the ir.model ID for the target model
    model_rec = rpc.search_read('ir.model',
        [['model', '=', model]], ['id'], limit=1)
    if not model_rec:
        raise ToolError(f"Model '{model}' not found")

    # 2. Ensure name starts with x_
    if not name.startswith('x_'):
        name = f'x_{name}'

    # 3. Check field doesn't already exist
    existing = rpc.search_read('ir.model.fields',
        [['model', '=', model], ['name', '=', name]], ['id'])
    if existing:
        raise ToolError(f"Field '{name}' already exists on '{model}'")

    # 4. Build field values
    field_vals = {
        'model_id': model_rec[0]['id'],
        'name': name,
        'field_description': label,
        'ttype': field_type,
        'state': 'manual',  # Critical — required for dynamic fields
    }

    if field_type == 'selection' and 'selection_options' in kwargs:
        # Odoo stores selection as a string representation
        field_vals['selection_ids'] = [
            (0, 0, {'value': v, 'name': l, 'sequence': i})
            for i, (v, l) in enumerate(kwargs['selection_options'])
        ]

    if field_type in ('many2one', 'one2many', 'many2many'):
        field_vals['relation'] = kwargs['relation']
        if field_type == 'one2many':
            field_vals['relation_field'] = kwargs['relation_field']

    if 'help_text' in kwargs:
        field_vals['help'] = kwargs['help_text']
    if 'required' in kwargs:
        field_vals['required'] = kwargs['required']

    # 5. Create the field
    field_id = rpc.create('ir.model.fields', field_vals)

    # 6. Restart Odoo to reload the registry
    await docker.restart_service('web')
    await _wait_for_healthy(docker, timeout=30)

    # 7. Verify field exists
    fields = rpc.fields_get(model, attributes=['string', 'type'])
    if name not in fields:
        raise ToolError(f"Field '{name}' was created but not loaded. "
                       f"Registry reload may have failed.")

    # 8. Update cache
    await cache.refresh_model_fields(model)

    # 9. Optionally add to view
    if kwargs.get('add_to_view', True):
        # Use the view_modify logic internally
        position = kwargs.get('view_position', {})
        ...

    return {
        'field_id': field_id,
        'technical_name': name,
        'model': model,
        'type': field_type,
        'label': label,
        'registry_reloaded': True,
        'verified': True,
    }
```

### How Schema + View Tools Work Together

This is the complete flow for "Add spiciness level to products":

```
AI receives: "I need to track spiciness level (1-5) on my products"

Step 1: odoo_schema_field_create(
          model="product.template",
          name="x_spiciness_level",
          field_type="selection",
          label="Spiciness Level",
          selection_options=[["1","Mild"],["2","Medium"],["3","Hot"],
                           ["4","Very Hot"],["5","Nuclear"]],
          add_to_view=true,
          view_position={"after": "categ_id"}
        )
        → Internally:
          1. Creates ir.model.fields record
          2. Restarts Odoo (registry reload)
          3. Verifies field exists via fields_get()
          4. Creates inherited view to show field on form
          5. Verifies view renders correctly
        → Returns: field_id, view_id, confirmed working

Step 2: (optionally) odoo_view_modify(
          model="product.template",
          view_type="tree",
          modifications=[{"action": "add_field",
                         "target": "list_price",
                         "value": "x_spiciness_level",
                         "position": "after"}]
        )
        → Adds the field to the list view too

Done. The field is in the database, on the form, and on the list view.
```

---

## 2. QWEB REPORT TOOLS (Extension to Section 5.8)

### Background

In Odoo, PDF reports (invoices, quotations, delivery slips, receipts) are rendered via QWeb — an XML templating engine. The report layouts are stored in `ir.ui.view` records with `type='qweb'`. They can be modified using the same XPath inheritance mechanism as form/tree views, but with important differences:

- QWeb templates use `<t>` tags, `t-if`, `t-foreach`, `t-esc`, `t-raw` directives
- The "outer layout" (`web.external_layout`) controls header/footer across all reports
- Individual reports (e.g., `account.report_invoice_document`) control the body content
- Breaking a QWeb template means **all PDFs for that report type fail** — higher stakes than form views
- Testing requires rendering the report to HTML or PDF, not just checking if the view loads

### New/Modified Tools

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_report_list                                           │
│ Lists all available report templates                             │
│                                                                  │
│ Params: db_name, model_filter?                                   │
│ Returns: List of reports with:                                   │
│   - name, technical name (report action XML ID)                  │
│   - model (e.g., "account.move" for invoices)                    │
│   - report_type (qweb-pdf, qweb-html)                           │
│   - associated QWeb view IDs                                     │
│   - paper_format                                                 │
│                                                                  │
│ Example output:                                                  │
│   "Invoice" → account.report_invoice, model=account.move         │
│   "Quotation/Order" → sale.report_saleorder, model=sale.order    │
│   "Delivery Slip" → stock.report_deliveryslip                    │
│   "POS Receipt" → point_of_sale.report_receipt                   │
│                                                                  │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_report_get_template                                   │
│ Gets the full QWeb template XML of a specific report             │
│                                                                  │
│ Params: db_name, report_name (XML ID or technical name),         │
│         include_layout? (bool, default true — includes the       │
│           external_layout header/footer wrapper)                  │
│ Returns:                                                         │
│   - Full QWeb XML template (compiled with all inheritance)       │
│   - Annotated field list (which fields are used: object.name,    │
│     object.partner_id.name, etc.)                                │
│   - Template hierarchy (which views inherit from which)          │
│   - Modifiable sections (header, footer, body, address blocks,   │
│     table headers, line items, totals, notes)                    │
│                                                                  │
│ Notes: The AI MUST read this before attempting any report         │
│   modification. QWeb templates are more complex than form views. │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_report_modify                                         │
│ Modifies a report template via QWeb view inheritance             │
│                                                                  │
│ Params: db_name, report_name,                                    │
│   modifications: list of {                                       │
│     action: "hide_element" | "show_element" | "replace_text" |  │
│             "add_field" | "remove_field" | "modify_layout" |    │
│             "change_style" | "add_section" | "custom_xpath",    │
│     target: element description or xpath,                        │
│     value?: replacement content or style,                        │
│     position?: "before" | "after" | "replace" | "inside"        │
│   },                                                             │
│   auto_snapshot?: bool (default true)                            │
│                                                                  │
│ HIGH-LEVEL ACTIONS → QWeb XPath Translation:                     │
│                                                                  │
│ "Hide Tax ID from invoice header":                               │
│   action="hide_element", target="company_vat"                    │
│   → <xpath expr="//span[@t-field='o.company_id.vat']"           │
│           position="attributes">                                 │
│       <attribute name="t-if">False</attribute>                   │
│     </xpath>                                                     │
│                                                                  │
│ "Make logo bigger on invoice":                                   │
│   action="change_style", target="company_logo",                  │
│   value="max-height: 120px; max-width: 250px;"                  │
│   → <xpath expr="//img[hasclass('header-logo')]"                 │
│           position="attributes">                                 │
│       <attribute name="style">max-height:120px;max-width:250px; │
│       </attribute>                                               │
│     </xpath>                                                     │
│                                                                  │
│ "Add bank details to invoice footer":                            │
│   action="add_section", target="footer",                         │
│   value="<div class='text-center'><small>                        │
│     Bank: HBL | Account: 1234-5678 | IBAN: PK...</small></div>" │
│   position="inside"                                              │
│                                                                  │
│ "Show custom spiciness field on POS receipt":                    │
│   action="add_field", target="order_line_details",               │
│   value="x_spiciness_level"                                      │
│                                                                  │
│ Returns: Created view ID, rendered test status                   │
│                                                                  │
│ Post-action:                                                     │
│   1. Renders a test report to HTML (using a sample record)       │
│   2. Checks for rendering errors (QWeb exceptions)               │
│   3. If render fails: auto-reverts (deletes custom view)         │
│   4. Returns a note that user should verify PDF output           │
│                                                                  │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_report_preview                                        │
│ Renders a report to HTML for verification (no PDF generation)    │
│                                                                  │
│ Params: db_name, report_name, record_id? (uses first record if   │
│         not specified)                                            │
│ Returns:                                                         │
│   - success: bool                                                │
│   - html_preview: str (the rendered HTML — truncated if large)   │
│   - errors: list of any QWeb rendering errors                    │
│   - field_values: dict of the data that populated the template   │
│                                                                  │
│ Notes: This is the QWeb equivalent of the form view render test. │
│   The AI should call this after any report modification to verify│
│   the template didn't break. Returns HTML, not PDF, because PDF  │
│   generation requires wkhtmltopdf which may timeout.             │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_report_reset                                          │
│ Removes a report customization                                   │
│ Params: db_name, view_id (the custom QWeb inheritance view)      │
│ Returns: Status                                                  │
│ Annotations: readOnly=false, destructive=true                    │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_report_layout_configure                               │
│ Configures the global report layout (header/footer template)     │
│                                                                  │
│ Params: db_name,                                                 │
│   layout?: "standard" | "boxed" | "clean" | "bold" (Odoo's      │
│           built-in layout options — maps to external_layout_*)   │
│   paper_format?: "A4" | "US Letter" | "custom"                  │
│   company_logo_size?: "small" | "medium" | "large"              │
│   header_content?: dict (what to show/hide in header:            │
│     show_company_name, show_company_address, show_company_vat,   │
│     show_company_phone, show_company_email, show_company_website)│
│   footer_content?: dict (what to show/hide in footer:            │
│     show_company_details, show_bank_details, custom_text)        │
│                                                                  │
│ Returns: Status, applied changes                                 │
│ Notes: This is a higher-level tool that modifies                 │
│   web.external_layout, which affects ALL reports globally.       │
│   More user-friendly than raw XPath on the layout template.      │
│ Annotations: readOnly=false, destructive=false                   │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation: QWeb Verification

```python
async def verify_report_modification(
    rpc: OdooRPC,
    report_name: str,
    custom_view_id: int,
    test_record_id: int | None = None
) -> ReportVerificationResult:
    """
    Renders a report to HTML to verify it doesn't crash.
    If it fails, auto-reverts the modification.
    """
    try:
        # Find a record to render the report for
        if test_record_id is None:
            report = rpc.search_read('ir.actions.report',
                [['report_name', '=', report_name]],
                ['model'], limit=1)
            model = report[0]['model']
            records = rpc.search_read(model, [], ['id'], limit=1)
            if not records:
                return ReportVerificationResult(
                    success=True,
                    warning="No records exist to test render. "
                            "Verify manually after creating data."
                )
            test_record_id = records[0]['id']

        # Attempt to render the report as HTML
        # Uses ir.actions.report._render_qweb_html()
        result = rpc.execute_method(
            'ir.actions.report',
            '_render_qweb_html',
            args=[report_name, [test_record_id]]
        )
        return ReportVerificationResult(
            success=True,
            html_length=len(result[0]) if result else 0,
        )
    except Exception as e:
        # Report rendering broke — revert
        rpc.unlink('ir.ui.view', [custom_view_id])
        return ReportVerificationResult(
            success=False,
            error=str(e),
            auto_reverted=True,
            message=f"Report modification caused render error: {e}. "
                    f"Customization was automatically reverted."
        )
```

### Common Report Modification Patterns

These go into the Knowledge Base (`knowledge/data/report_patterns.json`):

```json
{
  "invoice_hide_tax_id": {
    "report": "account.report_invoice_document",
    "description": "Hide company Tax ID from invoice header",
    "xpath": "//span[@t-field='o.company_id.vat']",
    "action": "set t-if='False'"
  },
  "invoice_add_bank_details": {
    "report": "web.external_layout",
    "description": "Add bank account details to all report footers",
    "xpath": "//div[hasclass('footer')]",
    "action": "append custom content inside"
  },
  "invoice_bigger_logo": {
    "report": "web.external_layout",
    "description": "Increase company logo size on all reports",
    "xpath": "//img[hasclass('header-logo')]",
    "action": "change style attribute"
  },
  "quotation_add_terms": {
    "report": "sale.report_saleorder_document",
    "description": "Add terms and conditions to quotation PDF",
    "xpath": "//div[@id='informations']",
    "action": "add section after"
  },
  "receipt_add_custom_field": {
    "report": "point_of_sale.report_receipt",
    "description": "Show custom product field on POS receipt",
    "note": "POS receipts use a different rendering engine (JS-based). Modifications are more limited."
  }
}
```

---

## 3. NETWORK EXPOSURE TOOLS (New Section 5.14)

### Why This Matters

A restaurant POS is useless if it only runs on `localhost`. The iPad at the counter needs to reach the Odoo instance. This tool provides multiple exposure strategies, from simple LAN access to secure internet tunnels.

```
┌─────────────────────────────────────────────────────────────────┐
│ TOOL: odoo_network_expose                                        │
│ Exposes the local Odoo instance to LAN or internet               │
│                                                                  │
│ Params:                                                          │
│   method: "lan" | "cloudflared" | "tailscale"                    │
│   port?: int (default: 8069 — the Odoo port)                    │
│   subdomain?: str (for cloudflared, e.g., "steamin-erp")        │
│                                                                  │
│ Method Details:                                                  │
│                                                                  │
│ "lan" (simplest — same WiFi network):                            │
│   - Detects the host machine's LAN IP                            │
│   - Verifies Odoo is bound to 0.0.0.0 (not just 127.0.0.1)     │
│   - Returns: http://192.168.x.x:8069                            │
│   - Checks: firewall rules, docker port binding                  │
│   - Limitation: Only works on same WiFi/network                  │
│                                                                  │
│ "cloudflared" (free, secure internet tunnel):                    │
│   - Checks if cloudflared is installed                           │
│   - Runs: cloudflared tunnel --url http://localhost:8069         │
│   - Returns: https://xxx.trycloudflare.com (temporary)           │
│     OR https://steamin-erp.yourdomain.com (if configured)       │
│   - Advantage: HTTPS automatic, no port forwarding               │
│   - Limitation: Requires cloudflared binary installed            │
│                                                                  │
│ "tailscale" (secure mesh VPN):                                   │
│   - Checks if Tailscale is running                               │
│   - Returns: http://machine-name:8069 (via Tailscale network)   │
│   - Advantage: Private, encrypted, persistent                    │
│   - Limitation: All devices need Tailscale installed             │
│                                                                  │
│ Returns:                                                         │
│   url: str (the accessible URL)                                  │
│   method: str (which method was used)                            │
│   instructions: str (what to do on the client device)            │
│   qr_code?: str (URL encoded as QR for mobile scanning)         │
│   warnings: list (security notes, temporary URL notice, etc.)    │
│                                                                  │
│ Post-action:                                                     │
│   - Updates Odoo's web.base.url system parameter to the new URL  │
│     (required for email links, report URLs to work correctly)    │
│   - Tests accessibility from localhost via the public URL         │
│                                                                  │
│ Annotations: readOnly=false, destructive=false                   │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_network_status                                        │
│ Shows current network exposure status                            │
│                                                                  │
│ Params: none                                                     │
│ Returns:                                                         │
│   local_url: str (http://localhost:8069)                         │
│   lan_ip: str (http://192.168.x.x:8069)                         │
│   tunnel_url: str | null (if tunnel is active)                   │
│   tunnel_method: str | null                                      │
│   web_base_url: str (current Odoo web.base.url setting)          │
│ Annotations: readOnly=true                                       │
├─────────────────────────────────────────────────────────────────┤
│ TOOL: odoo_network_stop                                          │
│ Stops any active tunnel and reverts web.base.url                 │
│                                                                  │
│ Params: none                                                     │
│ Returns: Status                                                  │
│ Annotations: readOnly=false, destructive=false                   │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
import subprocess
import socket

class NetworkManager:
    """Manages network exposure for the Odoo instance."""

    def get_lan_ip(self) -> str:
        """Detect the machine's LAN IP address."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()

    async def expose_lan(self, port: int = 8069) -> dict:
        """Expose via LAN — just returns the LAN IP + port."""
        lan_ip = self.get_lan_ip()
        url = f"http://{lan_ip}:{port}"

        # Verify Odoo is accessible on this IP
        # (Docker must bind to 0.0.0.0, not 127.0.0.1)
        ...
        return {
            "url": url,
            "method": "lan",
            "instructions": (
                f"On any device connected to the same WiFi network, "
                f"open a browser and go to {url}\n"
                f"For iPad POS: Open Safari → {url}"
            ),
        }

    async def expose_cloudflared(self, port: int = 8069) -> dict:
        """Start a Cloudflare tunnel."""
        # Check if cloudflared is installed
        result = subprocess.run(["which", "cloudflared"],
                               capture_output=True)
        if result.returncode != 0:
            return {
                "error": "cloudflared not installed",
                "install_instructions": (
                    "Install Cloudflare Tunnel:\n"
                    "  macOS: brew install cloudflared\n"
                    "  Linux: curl -L https://github.com/cloudflare/"
                    "cloudflared/releases/latest/download/"
                    "cloudflared-linux-amd64 -o /usr/local/bin/cloudflared"
                )
            }

        # Start tunnel in background
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # Parse the generated URL from stderr
        ...
```

---

## 4. BINARY / IMAGE HANDLING (Enhancement to Existing Tools)

### Modification to `odoo_record_create` and `odoo_record_update`

Add image handling support to the existing CRUD tools rather than creating separate tools.

```
ENHANCEMENT to odoo_record_create / odoo_record_update:

For fields of type "binary" (e.g., image_1920, image_128, logo):

The "values" dict accepts three formats for binary fields:

1. Base64 string (direct):
   {"image_1920": "/9j/4AAQSkZJRgABAQ..."}  (raw base64)

2. File path (auto-converted):
   {"image_1920": {"file": "/path/to/logo.png"}}
   → Tool reads the file and converts to base64

3. URL (auto-downloaded and converted):
   {"image_1920": {"url": "https://example.com/logo.png"}}
   → Tool downloads the image and converts to base64

The tool detects binary fields via fields_get() (type='binary')
and auto-converts file/url references before sending to XML-RPC.
```

### Implementation in `utils/binary_handler.py` (New)

```python
import base64
import httpx
from pathlib import Path

async def resolve_binary_value(value: Any, field_name: str) -> str:
    """
    Resolves a binary field value to a base64 string.

    Accepts:
    - str: assumed to be raw base64 already
    - dict with "file": reads local file → base64
    - dict with "url": downloads → base64
    """
    if isinstance(value, str):
        # Assume raw base64
        return value

    if isinstance(value, dict):
        if "file" in value:
            path = Path(value["file"])
            if not path.exists():
                raise ToolError(f"File not found: {path}")
            data = path.read_bytes()
            return base64.b64encode(data).decode('utf-8')

        if "url" in value:
            async with httpx.AsyncClient() as client:
                response = await client.get(value["url"], timeout=30)
                response.raise_for_status()
                return base64.b64encode(response.content).decode('utf-8')

    raise ToolError(
        f"Invalid value for binary field '{field_name}'. "
        f"Expected base64 string, {{file: path}}, or {{url: url}}"
    )


async def process_binary_fields(rpc: OdooRPC, model: str,
                                 values: dict) -> dict:
    """
    Pre-processes a values dict, converting any binary field
    values from file/url references to base64.
    """
    fields_info = rpc.fields_get(model, attributes=['type'])
    processed = {}

    for key, val in values.items():
        if key in fields_info and fields_info[key]['type'] == 'binary':
            processed[key] = await resolve_binary_value(val, key)
        else:
            processed[key] = val

    return processed
```

### Usage Example

```
AI receives: "Set up Steamin with this logo" (user provides URL)

odoo_company_configure(
  db_name="steamin",
  name="Steamin - Korean Japanese Fusion Ramen",
  logo={"url": "https://steamin.pk/logo.png"},
  city="Lahore",
  country="Pakistan",
  currency="PKR"
)
→ Tool internally downloads the image, converts to base64,
  writes to res.company.logo field via XML-RPC

AI receives: "Add product images for our ramen bowls"

odoo_record_create(
  db_name="steamin",
  model="product.template",
  values={
    "name": "Tonkotsu Ramen",
    "list_price": 1200.0,
    "categ_id": 5,
    "image_1920": {"file": "/uploads/tonkotsu.jpg"}
  }
)
→ Tool detects image_1920 is a binary field, reads the file,
  converts to base64, sends via XML-RPC
```

---

## 5. UPDATED PROJECT STRUCTURE (Additions Only)

```
src/odooforge/
├── tools/
│   ├── schema.py              # (NEW) Custom field/model creation
│   ├── reports.py             # (NEW) QWeb report modification
│   ├── network.py             # (NEW) LAN/tunnel exposure
│   └── ... (existing)
│
├── utils/
│   ├── binary_handler.py      # (NEW) Image/file → base64 conversion
│   ├── qweb_builder.py        # (NEW) QWeb XPath expression generator
│   └── ... (existing)
│
├── knowledge/data/
│   ├── report_patterns.json   # (NEW) Common report modifications
│   └── ... (existing)
│
└── verification/
    ├── verify_schema.py       # (NEW) Post-field-creation verification
    ├── verify_report.py       # (NEW) QWeb render testing
    └── ... (existing)
```

---

## 6. UPDATED TOOL COUNT

| Category | V2 Count | V2.1 Additions | V2.1 Total |
|---|---|---|---|
| Instance Management | 5 | — | 5 |
| Database Management | 6 | — | 6 |
| Snapshot/Rollback | 4 | — | 4 |
| Module Management | 6 | — | 6 |
| Model Introspection | 3 | — | 3 |
| Record CRUD | 6 | (enhanced with binary handling) | 6 |
| Batch Import | 3 | — | 3 |
| View/UI Customization | 5 | — | 5 |
| **Schema Extension** | — | **+5** | **5** |
| **QWeb Reports** | — | **+5** | **5** |
| Automation | 5 | — | 5 |
| Email Configuration | 4 | — | 4 |
| Settings & Users | 4 | — | 4 |
| Knowledge & Recipes | 6 | — | 6 |
| Diagnostics | 1 | — | 1 |
| **Network Exposure** | — | **+3** | **3** |
| **TOTAL** | **58** | **+13** | **71** |

---

## 7. REVISED DEVELOPMENT PHASES (Impact)

The new tools slot into existing phases with minimal disruption:

**Phase 2 (Module Management)** — Add `odoo_schema_field_create` here since it's a natural extension of model introspection. Schema tools are needed before view tools (you need to create a field before you can add it to a view).

**Phase 3 (View Customization)** — Add QWeb report tools here alongside existing view tools. Same XPath mechanics, different target (QWeb vs form views). Also add network exposure tools since they're needed for POS testing.

**Phase 4 (Import + Email + Knowledge)** — Add binary handling enhancement to existing CRUD tools. Add report patterns to knowledge base.

### Updated Phase Timeline

```
Phase 1 (Week 1-2): Foundation + Core CRUD .................. 14 tools
Phase 2 (Week 2-3): Modules + Snapshots + Schema ........... +17 tools (31)
Phase 3 (Week 3-4): Views + QWeb + Automation + Network .... +18 tools (49)
Phase 4 (Week 4-5): Import + Email + Knowledge + Polish .... +16 tools (65)
Phase 5 (Week 5-6): Recipes + Remaining + Distribution ..... + 6 tools (71)
```

---

## 8. UPDATED END-TO-END EXAMPLE

Adding to the restaurant setup scenario from V2:

```
... (after steps 1-13 from V2 example) ...

14. odoo_schema_field_create(
      model="product.template",
      name="x_spiciness_level",
      field_type="selection",
      label="Spiciness Level",
      selection_options=[["1","Mild"],["2","Medium"],["3","Hot"],
                        ["4","Very Hot"],["5","Nuclear"]],
      add_to_view=true,
      view_position={"after": "categ_id"}
    )
    → Custom field created, Odoo restarted, field verified,
      added to product form view

15. odoo_schema_field_create(
      model="res.partner",
      name="x_loyalty_points",
      field_type="integer",
      label="Loyalty Points",
      default_value=0,
      add_to_view=true
    )
    → Customer loyalty tracking field added

16. odoo_report_get_template(
      db="steamin",
      report_name="account.report_invoice_document"
    )
    → AI reads the invoice template structure

17. odoo_report_layout_configure(
      db="steamin",
      company_logo_size="large",
      footer_content={
        "show_bank_details": true,
        "custom_text": "Thank you for dining at Steamin!"
      }
    )
    → Invoice/receipt branding configured

18. odoo_report_modify(
      db="steamin",
      report_name="account.report_invoice_document",
      modifications=[
        {"action": "hide_element", "target": "company_vat"}
      ]
    )
    → Tax ID removed from invoice header
    → Test render: ✓ successful

19. odoo_network_expose(method="lan")
    → Returns: http://192.168.1.105:8069
    → "Open this URL on your iPad for POS access"
    → web.base.url updated automatically

20. odoo_snapshot_create(db="steamin", name="ready_for_launch")
    → Final checkpoint: everything configured and verified
```

**Result**: A fully operational restaurant ERP with custom fields (spiciness, loyalty points), branded invoices, hidden unnecessary fields, automated purchase review, email configured, accessible on the local network for iPad POS — all through conversation.

---

## 9. FINAL RISK ADDITIONS

| Risk | Mitigation |
|---|---|
| Schema field creation fails silently (ORM doesn't load) | Registry reload via Docker restart + verification via fields_get(). If field not found post-restart, error with clear message. |
| QWeb modification breaks all PDFs for a report type | Auto-render test after every modification. Auto-revert on failure. Snapshot before modification. |
| Network tunnel exposes instance to internet | Clear security warnings. Recommend Tailscale for persistent setups. Auto-set `web.base.url` on tunnel start/stop. |
| User uploads malicious file as "product image" | File size limits. Image type validation (check magic bytes). No executable file types. |
| Custom model creation without security rules | Auto-create `ir.model.access` records with sensible defaults (admin: full, internal users: read). AI prompted to refine permissions. |
