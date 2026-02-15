# Tool Reference

OdooForge provides **71 MCP tools** across **16 categories**. Each tool is documented with its parameters, return values, and usage examples.

## Quick Reference

| Category | Tools | Description | Docs |
|----------|-------|-------------|------|
| [Instance](instance.md) | 5 | Start, stop, restart, status, logs | Docker lifecycle |
| [Database](database.md) | 6 | Create, list, backup, restore, drop, SQL | Database management |
| [Records](records.md) | 6 | Search, read, create, update, delete, execute | ORM operations |
| [Snapshots](snapshots.md) | 4 | Create, list, restore, delete | Backup & restore |
| [Modules](modules.md) | 6 | List, info, install, upgrade, uninstall | Module lifecycle |
| [Models](models.md) | 3 | List, fields, search | Schema introspection |
| [Schema](schema.md) | 5 | Field create/update/delete, model create, list | Custom extensions |
| [Views](views.md) | 5 | List, get XML, modify, reset, customizations | View inheritance |
| [Reports](reports.md) | 6 | List, template, modify, preview, reset, layout | QWeb reports |
| [Automation](automation.md) | 5 | Rules, email templates | Automated actions |
| [Network](network.md) | 3 | Expose, status, stop | Tunnel management |
| [Import](imports.md) | 3 | Preview, execute, template | CSV import |
| [Email](email.md) | 4 | SMTP, IMAP, test, DNS | Mail configuration |
| [Settings](settings.md) | 4 | System, company, users | Configuration |
| [Knowledge](knowledge.md) | 3 | Module info, search, gaps | Built-in guidance |
| [Recipes](recipes.md) | 2 | List, execute | Industry setup |
| [Diagnostics](diagnostics.md) | 1 | Health check | System diagnostics |

## Common Patterns

### Response Format

All tools return a `dict` with at minimum a `status` key:

```json
{
  "status": "created",
  "id": 42,
  "message": "Record created successfully."
}
```

Error responses:

```json
{
  "status": "error",
  "message": "Model 'res.invalid' not found."
}
```

### Confirmation Guards

Destructive operations require `confirm=true`:

```
"Delete the record" → status: "cancelled", message: "Set confirm=true to proceed."
"Delete the record, confirm" → status: "deleted"
```

### Pagination

List tools support `limit` and `offset`:

```json
{
  "status": "ok",
  "records": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### Database Parameter

Most tools require `db_name` to specify which database to operate on. The AI assistant will typically use the default database from configuration.
