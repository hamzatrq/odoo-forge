# Diagnostics Tools

Run comprehensive health checks to verify your Odoo instance is properly configured and running.

## `odoo_diagnostics_health_check`

Run a 7-point health check covering Docker, database, authentication, modules, PostgreSQL, logs, and version.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_name` | `str` | *required* | Database name to check |

### Checks Performed

| Check | What It Verifies |
|-------|-----------------|
| **Docker** | Containers running and healthy |
| **Database** | Database exists and is accessible |
| **Authentication** | Admin login via XML-RPC succeeds |
| **Modules** | Base module is installed, no broken modules |
| **PostgreSQL** | Direct PG connection works |
| **Logs** | Scans for recent ERROR-level log entries |
| **Version** | Detects Odoo version |

**Returns:**

| Key | Type | Description |
|-----|------|-------------|
| `overall` | `str` | `"healthy"`, `"degraded"`, or `"unhealthy"` |
| `checks` | `list` | Per-check results with status and details |
| `errors` | `list` | Any detected errors or warnings |
| `odoo_version` | `str` | Detected Odoo version |

**Example:** `"Run a health check on my Odoo instance"`

### Interpreting Results

- **healthy** — All checks pass. System is fully operational.
- **degraded** — Some non-critical checks failed (e.g., log errors found). System works but needs attention.
- **unhealthy** — Critical checks failed (Docker down, auth failed). Immediate action needed.
