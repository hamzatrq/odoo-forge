"""Environment and configuration management for OdooForge."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class OdooForgeConfig:
    """Immutable configuration loaded from environment variables."""

    # Odoo connection
    odoo_url: str = "http://localhost:8069"
    odoo_master_password: str = "admin"
    odoo_default_db: str = ""
    odoo_admin_user: str = "admin"
    odoo_admin_password: str = "admin"

    # PostgreSQL direct connection
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "odoo"
    postgres_password: str = "odoo"

    # Docker
    docker_compose_path: str = ""

    # Snapshots
    snapshots_dir: str = ""

    @classmethod
    def from_env(cls) -> OdooForgeConfig:
        """Load configuration from environment variables with sensible defaults."""
        load_dotenv()

        # Resolve docker compose path — default to <project_root>/docker
        compose_path = os.getenv("DOCKER_COMPOSE_PATH", "")
        if not compose_path:
            # 1. Try package data (pip install)
            package_root = Path(__file__).resolve().parent
            data_compose = package_root / "data" / "docker-compose.yml"
            
            if data_compose.exists():
                compose_path = str(data_compose)
            else:
                # 2. Try source root (dev mode)
                project_root = package_root.parent.parent
                dev_compose = project_root / "docker" / "docker-compose.yml"
                if dev_compose.exists():
                    compose_path = str(dev_compose)

        snapshots_dir = os.getenv("ODOOFORGE_SNAPSHOTS_DIR", "")
        if not snapshots_dir and compose_path:
            snapshots_dir = str(Path(compose_path) / "snapshots")

        return cls(
            odoo_url=os.getenv("ODOO_URL", "http://localhost:8069"),
            odoo_master_password=os.getenv("ODOO_MASTER_PASSWORD", "admin"),
            odoo_default_db=os.getenv("ODOO_DEFAULT_DB", ""),
            odoo_admin_user=os.getenv("ODOO_ADMIN_USER", "admin"),
            odoo_admin_password=os.getenv("ODOO_ADMIN_PASSWORD", "admin"),
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_user=os.getenv("POSTGRES_USER", "odoo"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", "odoo"),
            docker_compose_path=compose_path,
            snapshots_dir=snapshots_dir,
        )


# Module-level singleton — initialized lazily
_config: OdooForgeConfig | None = None


def get_config() -> OdooForgeConfig:
    """Get the global configuration instance (lazy-initialized)."""
    global _config
    if _config is None:
        _config = OdooForgeConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset the config singleton (useful for testing)."""
    global _config
    _config = None
