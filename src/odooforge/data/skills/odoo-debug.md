---
name: odoo-debug
description: Use when diagnosing Odoo issues — reads logs, maps common errors to fixes, checks module states, with snapshot-based rollback
---

# Odoo Debugger

Diagnose and fix Odoo issues systematically.

## When to Use

- Odoo instance not responding or throwing errors
- Module installation or upgrade fails
- Views or reports not rendering correctly
- Automation or scheduled actions not firing
- Performance issues

## Diagnostic Process

### Step 1: Health Check

Always start here:

```
odoo_diagnostics_health_check(db_name="your_db")
```

This checks Docker, database, auth, modules, and logs in one call.

### Step 2: Read Logs

```
odoo_instance_logs(lines=100, level_filter="ERROR")
odoo_instance_logs(lines=50, grep="your_module_name")
```

### Step 3: Common Error to Fix Mapping

| Error Pattern | Likely Cause | Fix |
|--------------|-------------|-----|
| `Module not found` | Module not in addons path | Check Docker volume mounts, restart |
| `Access Denied` | Wrong credentials or no access | Check `ODOO_ADMIN_USER`, `ODOO_ADMIN_PASSWORD` |
| `relation "table" does not exist` | Missing migration | `odoo_module_install` or `odoo_module_upgrade` |
| `Field "x_field" does not exist` | Custom field deleted | `odoo_schema_field_create` to recreate |
| `View error` / `Invalid XML` | Malformed view customization | `odoo_view_reset` then `odoo_view_modify` |
| `QWeb error` | Report template issue | `odoo_report_reset` then `odoo_report_modify` |
| `RecursionError` | Circular computed fields | Check model inheritance chain |
| `psycopg2.OperationalError` | Database connection issue | Check PostgreSQL, restart instance |
| `Memory limit exceeded` | Large data operation | Increase Docker memory, batch operations |

### Step 4: Module State Checks

```
odoo_module_list_installed(db_name="your_db")
odoo_module_info(db_name="your_db", module_name="problem_module")
```

Module states:
- `installed` — working normally
- `to upgrade` — pending upgrade (restart Odoo to apply)
- `to install` — pending install (restart Odoo to apply)
- `uninstalled` — available but not active
- `uninstallable` — dependencies not met

### Step 5: Data Inspection

```
odoo_record_search(db_name="db", model="ir.module.module", domain=[["state", "=", "to upgrade"]])
odoo_db_run_sql(db_name="db", query="SELECT count(*) FROM ir_attachment WHERE res_model = 'problem.model'")
```

## Recovery Procedures

### Snapshot-Based Rollback

**Always create a snapshot before attempting fixes:**

```
odoo_snapshot_create(db_name="db", name="before_fix", description="Before debugging fix attempt")
```

If the fix makes things worse:
```
odoo_snapshot_restore(db_name="db", snapshot_name="before_fix")
```

### Nuclear Options (Confirm with User First)

These are destructive — always confirm before using:

1. **Module force-reinstall**: Uninstall then reinstall a problematic module
2. **View reset**: `odoo_view_reset` removes all view customizations for a model
3. **Database drop and restore**: `odoo_db_drop` + `odoo_db_restore` from backup
4. **Instance restart**: `odoo_instance_restart` — clears caches and reconnects

### Common Fix Workflows

**Module won't install:**
1. Health check
2. Check logs for dependency errors
3. Install missing dependencies first
4. Retry module install
5. If still failing, check module compatibility with Odoo 18

**View broken after customization:**
1. Snapshot current state
2. `odoo_view_list_customizations` to see what changed
3. `odoo_view_reset` to restore original
4. Re-apply changes carefully with `odoo_view_modify`

**Automation not firing:**
1. `odoo_automation_list` to check automation state
2. Verify trigger conditions match actual data changes
3. Check logs for automation errors
4. `odoo_automation_update` to fix trigger or action

## Key Principles

- **Snapshot first** — always create a snapshot before any fix attempt
- **Read logs** — most Odoo issues are explained in the logs
- **Check module states** — pending upgrades/installs cause many issues
- **Confirm destructive actions** — always ask the user before nuclear options
- **Document the fix** — explain what went wrong and how it was fixed
