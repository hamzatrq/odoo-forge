"""Docker Compose wrapper for Odoo infrastructure management."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Timeout for Docker commands (seconds)
_CMD_TIMEOUT = 120
_HEALTH_TIMEOUT = 60


async def _run(cmd: list[str], cwd: str | None = None, timeout: int = _CMD_TIMEOUT) -> tuple[int, str, str]:
    """Run a subprocess command and return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(cmd)}")

    return proc.returncode, stdout.decode(errors="replace"), stderr.decode(errors="replace")


class DockerError(Exception):
    """Raised when a Docker operation fails."""


class OdooDocker:
    """Docker Compose wrapper for Odoo infrastructure management."""

    def __init__(self, compose_path: str):
        self.compose_dir = Path(compose_path)
        self.compose_file = self.compose_dir / "docker-compose.yml"
        self._snapshots_dir = self.compose_dir / "snapshots"

        if not self.compose_file.exists():
            raise DockerError(
                f"docker-compose.yml not found at {self.compose_file}. "
                f"Set DOCKER_COMPOSE_PATH to the directory containing docker-compose.yml."
            )

    def _compose_cmd(self, *args: str) -> list[str]:
        """Build a docker compose command list."""
        return ["docker", "compose", "-f", str(self.compose_file), *args]

    # ── Lifecycle ───────────────────────────────────────────────────

    async def up(self, detach: bool = True) -> dict[str, Any]:
        """Start the Odoo Docker environment."""
        cmd = self._compose_cmd("up")
        if detach:
            cmd.append("-d")
        cmd.append("--wait")

        rc, stdout, stderr = await _run(cmd, cwd=str(self.compose_dir), timeout=180)
        if rc != 0:
            raise DockerError(f"docker compose up failed:\n{stderr}")

        return {
            "status": "running",
            "message": "Odoo environment started",
            "output": stdout.strip(),
        }

    async def down(self, remove_volumes: bool = False) -> dict[str, Any]:
        """Stop the Odoo Docker environment."""
        cmd = self._compose_cmd("down")
        if remove_volumes:
            cmd.append("-v")

        rc, stdout, stderr = await _run(cmd, cwd=str(self.compose_dir))
        if rc != 0:
            raise DockerError(f"docker compose down failed:\n{stderr}")

        return {
            "status": "stopped",
            "volumes_removed": remove_volumes,
            "output": stdout.strip(),
        }

    async def restart_service(self, service: str = "web") -> dict[str, Any]:
        """Restart a specific service (default: Odoo web)."""
        rc, stdout, stderr = await _run(
            self._compose_cmd("restart", service),
            cwd=str(self.compose_dir),
        )
        if rc != 0:
            raise DockerError(f"Restart of '{service}' failed:\n{stderr}")

        return {"status": "restarted", "service": service}

    async def status(self) -> dict[str, Any]:
        """Get container states, ports, health status."""
        rc, stdout, stderr = await _run(
            self._compose_cmd("ps", "--format", "json"),
            cwd=str(self.compose_dir),
        )
        if rc != 0:
            raise DockerError(f"docker compose ps failed:\n{stderr}")

        containers = []
        for line in stdout.strip().splitlines():
            line = line.strip()
            if line:
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        return {
            "running": len(containers) > 0,
            "containers": containers,
        }

    async def logs(
        self,
        service: str = "web",
        lines: int = 100,
        since: str | None = None,
        grep: str | None = None,
    ) -> str:
        """Retrieve container logs."""
        cmd = self._compose_cmd("logs", service, f"--tail={lines}", "--no-color")
        if since:
            cmd.extend(["--since", since])

        rc, stdout, stderr = await _run(cmd, cwd=str(self.compose_dir))

        log_output = stdout or stderr

        if grep and log_output:
            import re
            pattern = re.compile(grep, re.IGNORECASE)
            log_output = "\n".join(
                line for line in log_output.splitlines() if pattern.search(line)
            )

        return log_output

    async def exec_in_container(
        self, service: str, command: str, timeout: int = _CMD_TIMEOUT
    ) -> str:
        """Execute a command inside a running container."""
        cmd = self._compose_cmd("exec", "-T", service, "bash", "-c", command)

        rc, stdout, stderr = await _run(cmd, cwd=str(self.compose_dir), timeout=timeout)
        if rc != 0:
            raise DockerError(
                f"exec in '{service}' failed (exit {rc}):\n{stderr or stdout}"
            )
        return stdout

    # ── Module management via CLI ───────────────────────────────────

    async def install_module_via_cli(self, db: str, modules: list[str]) -> str:
        """Install modules using Odoo CLI (more reliable than XML-RPC for large modules)."""
        module_list = ",".join(modules)
        cmd = self._compose_cmd(
            "exec", "-T", "web",
            "odoo", "-d", db, "-i", module_list, "--stop-after-init",
        )

        rc, stdout, stderr = await _run(
            cmd, cwd=str(self.compose_dir), timeout=300,
        )

        output = stderr or stdout  # Odoo logs to stderr
        if rc != 0:
            raise DockerError(
                f"Module install failed for [{module_list}] on '{db}':\n{output[-2000:]}"
            )
        return output

    async def upgrade_module_via_cli(self, db: str, modules: list[str]) -> str:
        """Upgrade modules using Odoo CLI."""
        module_list = ",".join(modules)
        cmd = self._compose_cmd(
            "exec", "-T", "web",
            "odoo", "-d", db, "-u", module_list, "--stop-after-init",
        )

        rc, stdout, stderr = await _run(
            cmd, cwd=str(self.compose_dir), timeout=300,
        )

        output = stderr or stdout
        if rc != 0:
            raise DockerError(
                f"Module upgrade failed for [{module_list}] on '{db}':\n{output[-2000:]}"
            )
        return output

    # ── Snapshot operations ─────────────────────────────────────────

    async def create_snapshot(self, db: str, name: str, description: str = "") -> dict[str, Any]:
        """Create a database snapshot via pg_dump in the postgres container."""
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)

        dump_file = f"{name}.dump"
        container_path = f"/tmp/{dump_file}"

        # pg_dump inside the container
        await self.exec_in_container(
            "db",
            f"pg_dump -U odoo -Fc {db} -f {container_path}",
            timeout=300,
        )

        # Copy dump out of container
        local_path = self._snapshots_dir / dump_file
        rc, stdout, stderr = await _run(
            ["docker", "compose", "-f", str(self.compose_file),
             "cp", f"db:{container_path}", str(local_path)],
            cwd=str(self.compose_dir),
        )
        if rc != 0:
            raise DockerError(f"Failed to copy snapshot: {stderr}")

        # Clean up temp file in container
        await self.exec_in_container("db", f"rm -f {container_path}")

        # Write manifest
        manifest = {
            "name": name,
            "database": db,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dump_file": dump_file,
            "size_bytes": local_path.stat().st_size if local_path.exists() else 0,
        }
        manifest_path = self._snapshots_dir / f"{name}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        return manifest

    async def restore_snapshot(self, db: str, name: str) -> dict[str, Any]:
        """Restore a database from a snapshot."""
        dump_path = self._snapshots_dir / f"{name}.dump"
        if not dump_path.exists():
            raise DockerError(f"Snapshot '{name}' not found at {dump_path}")

        container_path = f"/tmp/{name}.dump"

        # Copy dump into container
        rc, _, stderr = await _run(
            ["docker", "compose", "-f", str(self.compose_file),
             "cp", str(dump_path), f"db:{container_path}"],
            cwd=str(self.compose_dir),
        )
        if rc != 0:
            raise DockerError(f"Failed to copy snapshot to container: {stderr}")

        # Drop and recreate the database
        await self.exec_in_container(
            "db",
            f"psql -U odoo -d postgres -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{db}' AND pid <> pg_backend_pid();\"",
        )
        await self.exec_in_container("db", f"dropdb -U odoo --if-exists {db}")
        await self.exec_in_container("db", f"createdb -U odoo {db}")

        # Restore
        await self.exec_in_container(
            "db",
            f"pg_restore -U odoo -d {db} --no-owner {container_path}",
            timeout=300,
        )

        # Clean up
        await self.exec_in_container("db", f"rm -f {container_path}")

        # Restart Odoo to pick up restored state
        await self.restart_service("web")

        return {
            "status": "restored",
            "database": db,
            "snapshot": name,
        }

    async def list_snapshots(self, db: str | None = None) -> list[dict]:
        """List available snapshots from the manifests directory."""
        if not self._snapshots_dir.exists():
            return []

        snapshots = []
        for manifest_file in sorted(self._snapshots_dir.glob("*.json")):
            try:
                manifest = json.loads(manifest_file.read_text())
                if db is None or manifest.get("database") == db:
                    snapshots.append(manifest)
            except (json.JSONDecodeError, OSError):
                continue

        return snapshots

    async def delete_snapshot(self, name: str) -> dict[str, Any]:
        """Delete a snapshot from disk."""
        dump_path = self._snapshots_dir / f"{name}.dump"
        manifest_path = self._snapshots_dir / f"{name}.json"

        freed = 0
        if dump_path.exists():
            freed = dump_path.stat().st_size
            dump_path.unlink()
        if manifest_path.exists():
            manifest_path.unlink()

        return {"status": "deleted", "name": name, "freed_bytes": freed}

    # ── Health ──────────────────────────────────────────────────────

    async def wait_for_healthy(self, timeout: int = _HEALTH_TIMEOUT) -> bool:
        """Poll until the Odoo web service is healthy."""
        import httpx

        start = asyncio.get_event_loop().time()
        url = "http://localhost:8069/web/health"

        while (asyncio.get_event_loop().time() - start) < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=5)
                    if resp.status_code == 200:
                        return True
            except (httpx.ConnectError, httpx.ReadTimeout, OSError):
                pass
            await asyncio.sleep(2)

        raise DockerError(f"Odoo did not become healthy within {timeout}s")
