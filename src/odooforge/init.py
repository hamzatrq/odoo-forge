"""OdooForge workspace initializer — ``odooforge init``."""

from __future__ import annotations

import importlib.resources
import shutil
from pathlib import Path

# ── Result tracking ───────────────────────────────────────────────

Result = tuple[str, str]  # (relative_path, "created" | "skipped" | "updated")

# ── Templates ─────────────────────────────────────────────────────

_CLAUDE_MD = """\
# OdooForge Workspace

This project uses [OdooForge](https://github.com/hamzatrq/odoo-forge) — an AI-First ERP Configuration Engine for Odoo 18.

## Quick Start

```bash
# Start Odoo + PostgreSQL
cd docker && docker compose up -d

# Run OdooForge MCP server
odooforge
```

## Updating

After upgrading OdooForge, update workspace files to the latest version:

```bash
pip install --upgrade odooforge
odooforge init --update
```

Your `.env` is never overwritten.

## Environment

- Edit `.env` with your connection details
- Default Odoo URL: http://localhost:8069
- Default credentials: admin / admin

## OdooForge Tools

OdooForge exposes 79 MCP tools across these categories:

| Category | Examples |
|----------|----------|
| **Instance** | `odoo_instance_start`, `odoo_instance_restart`, `odoo_instance_logs` |
| **Database** | `odoo_db_create`, `odoo_db_list`, `odoo_db_run_sql` |
| **Modules** | `odoo_module_install`, `odoo_module_upgrade`, `odoo_module_list_installed` |
| **Schema** | `odoo_model_list`, `odoo_model_fields`, `odoo_schema_field_create` |
| **Records** | `odoo_record_search`, `odoo_record_create`, `odoo_record_write` |
| **Views** | `odoo_view_list`, `odoo_view_modify`, `odoo_view_reset` |
| **Snapshots** | `odoo_snapshot_create`, `odoo_snapshot_restore`, `odoo_snapshot_list` |
| **Planning** | `odoo_analyze_requirements`, `odoo_design_solution`, `odoo_validate_plan` |
| **Workflows** | `odoo_setup_business`, `odoo_create_feature`, `odoo_create_dashboard` |
| **Code Gen** | `odoo_generate_addon` |
| **Diagnostics** | `odoo_diagnostics_health_check` |

## Skills

The `skills/` directory contains Claude Code skills for guided workflows:
- **odoo-brainstorm** — Explore Odoo customization ideas
- **odoo-architect** — Design data models with best practices
- **odoo-debug** — Diagnose and fix Odoo issues

## Custom Addons

Place custom Odoo modules in the `addons/` directory. They are automatically
mounted into the Docker container at `/mnt/extra-addons`.
"""

_CURSOR_MCP_JSON = """\
{
  "mcpServers": {
    "odooforge": {
      "command": "uvx",
      "args": ["odooforge"]
    }
  }
}
"""

_WINDSURF_MCP_JSON = """\
{
  "mcpServers": {
    "odooforge": {
      "command": "uvx",
      "args": ["odooforge"]
    }
  }
}
"""

_GITIGNORE = """\
# OdooForge
.env
__pycache__/
*.pyc
addons/*/
!addons/.keep
docker/snapshots/
"""


# ── Helpers ───────────────────────────────────────────────────────

def _pkg_data() -> Path:
    """Return the path to the bundled ``data/`` directory."""
    return importlib.resources.files("odooforge") / "data"  # type: ignore[return-value]


def _write_file(path: Path, content: str, results: list[Result], *, update: bool = False) -> None:
    """Write *content* to *path*, optionally overwriting if *update* is set."""
    rel = str(path)
    if path.exists():
        if update:
            path.write_text(content)
            results.append((rel, "updated"))
        else:
            results.append((rel, "skipped"))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    results.append((rel, "created"))


def _copy_file(src: Path, dst: Path, results: list[Result], *, update: bool = False) -> None:
    """Copy *src* to *dst*, optionally overwriting if *update* is set."""
    rel = str(dst)
    if dst.exists():
        if update:
            shutil.copy2(src, dst)
            results.append((rel, "updated"))
        else:
            results.append((rel, "skipped"))
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    results.append((rel, "created"))


# ── Section builders ──────────────────────────────────────────────

def _copy_skills(target: Path, results: list[Result], *, update: bool = False) -> None:
    skills_src = _pkg_data() / "skills"
    for name in ("odoo-brainstorm.md", "odoo-architect.md", "odoo-debug.md"):
        _copy_file(skills_src / name, target / "skills" / name, results, update=update)


def _create_claude_md(target: Path, results: list[Result], *, update: bool = False) -> None:
    _write_file(target / "CLAUDE.md", _CLAUDE_MD, results, update=update)


def _create_mcp_configs(target: Path, results: list[Result], *, update: bool = False) -> None:
    _write_file(target / ".cursor" / "mcp.json", _CURSOR_MCP_JSON, results, update=update)
    _write_file(target / ".windsurf" / "mcp.json", _WINDSURF_MCP_JSON, results, update=update)


def _copy_env(target: Path, results: list[Result]) -> None:
    # Never overwrite .env — it contains user credentials.
    _copy_file(_pkg_data() / ".env.example", target / ".env", results, update=False)


def _copy_docker(target: Path, results: list[Result], *, update: bool = False) -> None:
    data = _pkg_data()
    _copy_file(data / "docker-compose.yml", target / "docker" / "docker-compose.yml", results, update=update)
    _copy_file(data / "odoo.conf", target / "docker" / "odoo.conf", results, update=update)


def _create_addons_dir(target: Path, results: list[Result]) -> None:
    keep = target / "addons" / ".keep"
    if keep.exists():
        results.append((str(keep), "skipped"))
        return
    keep.parent.mkdir(parents=True, exist_ok=True)
    keep.write_text("")
    results.append((str(keep), "created"))


def _create_gitignore(target: Path, results: list[Result], *, update: bool = False) -> None:
    gi = target / ".gitignore"
    marker = "# OdooForge"
    if gi.exists():
        existing = gi.read_text()
        if marker in existing:
            if update:
                # Replace the OdooForge section in-place
                import re
                replaced = re.sub(
                    r"# OdooForge\n(?:.*\n)*?(?=\n[^ \t#]|\n*$|\Z)",
                    _GITIGNORE,
                    existing,
                )
                gi.write_text(replaced)
                results.append((str(gi), "updated"))
            else:
                results.append((str(gi), "skipped"))
            return
        # Append OdooForge section
        gi.write_text(existing.rstrip() + "\n\n" + _GITIGNORE)
        results.append((str(gi), "created"))
    else:
        gi.write_text(_GITIGNORE)
        results.append((str(gi), "created"))


# ── Summary ───────────────────────────────────────────────────────

def _print_summary(target: Path, results: list[Result]) -> None:
    created = [(p, s) for p, s in results if s == "created"]
    updated = [(p, s) for p, s in results if s == "updated"]
    skipped = [(p, s) for p, s in results if s == "skipped"]

    print(f"\nOdooForge workspace initialized in {target.resolve()}\n")
    if created:
        print(f"  Created {len(created)} file(s):")
        for p, _ in created:
            print(f"    + {p}")
    if updated:
        print(f"  Updated {len(updated)} file(s):")
        for p, _ in updated:
            print(f"    ~ {p}")
    if skipped:
        print(f"  Skipped {len(skipped)} file(s) (already exist):")
        for p, _ in skipped:
            print(f"    - {p}")
    print(
        "\nNext steps:\n"
        "  1. Edit .env with your Odoo connection details\n"
        "  2. cd docker && docker compose up -d\n"
        "  3. Start coding with your AI editor!\n"
    )


# ── Main ──────────────────────────────────────────────────────────

def run_init(target: Path | None = None, *, update: bool = False) -> list[Result]:
    """Initialize the current directory as an OdooForge workspace.

    When *update* is ``True``, template files are overwritten with the
    latest versions from the package.  ``.env`` is never overwritten.

    Returns the list of ``(path, status)`` results for testing.
    """
    target = target or Path(".")
    results: list[Result] = []

    _copy_skills(target, results, update=update)
    _create_claude_md(target, results, update=update)
    _create_mcp_configs(target, results, update=update)
    _copy_env(target, results)  # always update=False
    _copy_docker(target, results, update=update)
    _create_addons_dir(target, results)
    _create_gitignore(target, results, update=update)
    _print_summary(target, results)

    return results
