# Configuration

OdooForge reads configuration from environment variables. Use a `.env` file or set them in your shell.

## Environment Variables

### Odoo Connection

| Variable | Default | Description |
|----------|---------|-------------|
| `ODOO_URL` | `http://localhost:8069` | Odoo instance URL |
| `ODOO_MASTER_PASSWORD` | `admin` | Odoo master/admin password (for DB operations) |
| `ODOO_DEFAULT_DB` | *(empty)* | Default database name |
| `ODOO_ADMIN_USER` | `admin` | Admin username for XML-RPC authentication |
| `ODOO_ADMIN_PASSWORD` | `admin` | Admin password for XML-RPC authentication |

### PostgreSQL Direct Connection

Used for raw SQL queries, backups, and diagnostics.

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `odoo` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `odoo` | PostgreSQL password |

### Docker

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCKER_COMPOSE_PATH` | *(auto-detected)* | Path to docker/ directory. Auto-resolves to `<project_root>/docker` |

### Snapshots

| Variable | Default | Description |
|----------|---------|-------------|
| `ODOOFORGE_SNAPSHOTS_DIR` | `<docker_path>/snapshots` | Directory for database snapshot storage |

## MCP Client Configuration

When running via MCP clients (Claude Desktop, Cursor), explicitly pass environment variables in the configuration JSON. **This is required because `uvx` runs in an isolated environment and may not read your local `.env` file.**

### Example `mcp.json`

```json
{
  "mcpServers": {
    "odooforge": {
      "command": "uvx",
      "args": ["odooforge"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DEFAULT_DB": "odoo",
        "ODOO_ADMIN_USER": "admin",
        "ODOO_ADMIN_PASSWORD": "admin",
        "ODOO_MASTER_PASSWORD": "admin",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "odoo",
        "POSTGRES_PASSWORD": "odoo"
      }
    }
  }
}
```

## .env File

Copy the provided template:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
# Odoo Connection
ODOO_URL=http://localhost:8069
ODOO_MASTER_PASSWORD=admin
ODOO_DEFAULT_DB=mydb
ODOO_ADMIN_USER=admin
ODOO_ADMIN_PASSWORD=admin

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=odoo
POSTGRES_PASSWORD=odoo
```

## Docker Compose Setup

The included `docker/docker-compose.yml` provides:

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `web` | `odoo:18` | `8069` | Odoo application server |
| `db` | `postgres:17` | `5432` | PostgreSQL database |

### Starting

```bash
docker compose -f docker/docker-compose.yml up -d
```

### Stopping

```bash
docker compose -f docker/docker-compose.yml down
```

### Stopping with data removal

```bash
docker compose -f docker/docker-compose.yml down -v
```

> ⚠️ The `-v` flag removes all persistent volumes — **this deletes all Odoo data**.

### Health Checks

Both services include health checks:
- **Odoo**: HTTP check on `/web/health` (every 15s, 30s start period)
- **PostgreSQL**: `pg_isready` check (every 10s)

### Custom Addons

Place custom Odoo addons in `docker/addons/`. They are mounted at `/mnt/extra-addons` inside the container.

### Odoo Configuration

The file `docker/odoo.conf` is mounted read-only into the container. Default settings:

```ini
[options]
addons_path = /mnt/extra-addons
data_dir = /var/lib/odoo
```

## Remote Odoo Instances

OdooForge can connect to any Odoo 18 instance, not just Docker:

```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_ADMIN_USER=your_user
ODOO_ADMIN_PASSWORD=your_password
```

When connecting remotely, Docker-dependent features (instance management, snapshots) won't be available, but all ORM-based tools (records, modules, schema, views, etc.) work normally.
