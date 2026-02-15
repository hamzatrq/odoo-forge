"""Tests for Docker client with mocked subprocess calls."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from odooforge.connections.docker_client import OdooDocker, DockerError


@pytest.fixture
def tmp_compose(tmp_path):
    """Create a temporary docker-compose.yml for testing."""
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services:\n  web:\n    image: odoo:18\n")
    return tmp_path


@pytest.fixture
def docker(tmp_compose):
    return OdooDocker(str(tmp_compose))


class TestInit:
    def test_valid_path(self, tmp_compose):
        d = OdooDocker(str(tmp_compose))
        assert d.compose_file.exists()

    def test_missing_compose_file(self, tmp_path):
        with pytest.raises(DockerError, match="not found"):
            OdooDocker(str(tmp_path))


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_up_success(self, docker):
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "Started", "")
            result = await docker.up()
            assert result["status"] == "running"
            # Verify docker compose command was built correctly
            cmd = mock_run.call_args[0][0]
            assert "docker" in cmd
            assert "compose" in cmd
            assert "up" in cmd

    @pytest.mark.asyncio
    async def test_up_failure(self, docker):
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (1, "", "Error starting containers")
            with pytest.raises(DockerError, match="failed"):
                await docker.up()

    @pytest.mark.asyncio
    async def test_down_success(self, docker):
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "Stopped", "")
            result = await docker.down()
            assert result["status"] == "stopped"
            assert result["volumes_removed"] is False

    @pytest.mark.asyncio
    async def test_down_with_volumes(self, docker):
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")
            result = await docker.down(remove_volumes=True)
            assert result["volumes_removed"] is True
            cmd = mock_run.call_args[0][0]
            assert "-v" in cmd

    @pytest.mark.asyncio
    async def test_restart_success(self, docker):
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")
            result = await docker.restart_service("web")
            assert result["status"] == "restarted"
            assert result["service"] == "web"


class TestStatus:
    @pytest.mark.asyncio
    async def test_status_running(self, docker):
        container_json = json.dumps({"Name": "web", "State": "running"})
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, container_json, "")
            result = await docker.status()
            assert result["running"] is True
            assert len(result["containers"]) == 1

    @pytest.mark.asyncio
    async def test_status_not_running(self, docker):
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "", "")
            result = await docker.status()
            assert result["running"] is False


class TestLogs:
    @pytest.mark.asyncio
    async def test_logs(self, docker):
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "2024-01-01 INFO startup\n2024-01-01 ERROR oops\n", "")
            logs = await docker.logs(lines=50)
            assert "startup" in logs
            assert "oops" in logs

    @pytest.mark.asyncio
    async def test_logs_with_grep(self, docker):
        with patch("odooforge.connections.docker_client._run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (0, "INFO startup\nERROR oops\nINFO done\n", "")
            logs = await docker.logs(grep="ERROR")
            assert "oops" in logs
            assert "startup" not in logs


class TestSnapshots:
    @pytest.mark.asyncio
    async def test_list_empty(self, docker):
        result = await docker.list_snapshots()
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, docker):
        result = await docker.delete_snapshot("nope")
        assert result["status"] == "deleted"
        assert result["freed_bytes"] == 0

    @pytest.mark.asyncio
    async def test_list_with_manifests(self, docker):
        snap_dir = docker._snapshots_dir
        snap_dir.mkdir(parents=True, exist_ok=True)
        manifest = {"name": "snap1", "database": "testdb", "created_at": "2024-01-01"}
        (snap_dir / "snap1.json").write_text(json.dumps(manifest))

        result = await docker.list_snapshots()
        assert len(result) == 1
        assert result[0]["name"] == "snap1"

    @pytest.mark.asyncio
    async def test_list_filtered_by_db(self, docker):
        snap_dir = docker._snapshots_dir
        snap_dir.mkdir(parents=True, exist_ok=True)
        (snap_dir / "s1.json").write_text(json.dumps({"name": "s1", "database": "db1"}))
        (snap_dir / "s2.json").write_text(json.dumps({"name": "s2", "database": "db2"}))

        result = await docker.list_snapshots(db="db1")
        assert len(result) == 1
        assert result[0]["name"] == "s1"
