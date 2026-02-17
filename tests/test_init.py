"""Tests for ``odooforge init`` workspace initializer."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from odooforge.init import run_init


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """Return a fresh temporary directory to use as target."""
    return tmp_path


# ── File creation tests ──────────────────────────────────────────


def test_creates_all_expected_files(workspace: Path) -> None:
    results = run_init(workspace)
    created = {p for p, s in results if s == "created"}

    expected = {
        str(workspace / "skills" / "odoo-brainstorm.md"),
        str(workspace / "skills" / "odoo-architect.md"),
        str(workspace / "skills" / "odoo-debug.md"),
        str(workspace / "CLAUDE.md"),
        str(workspace / ".cursor" / "mcp.json"),
        str(workspace / ".windsurf" / "mcp.json"),
        str(workspace / ".env"),
        str(workspace / "docker" / "docker-compose.yml"),
        str(workspace / "docker" / "odoo.conf"),
        str(workspace / "addons" / ".keep"),
        str(workspace / ".gitignore"),
    }

    assert created == expected
    # Every file exists on disk
    for path in expected:
        assert Path(path).exists(), f"{path} was not created on disk"


def test_skill_files_have_content(workspace: Path) -> None:
    run_init(workspace)
    for name in ("odoo-brainstorm.md", "odoo-architect.md", "odoo-debug.md"):
        content = (workspace / "skills" / name).read_text()
        assert len(content) > 100, f"{name} seems too short"
        assert "---" in content  # frontmatter present


def test_claude_md_content(workspace: Path) -> None:
    run_init(workspace)
    content = (workspace / "CLAUDE.md").read_text()
    assert "OdooForge" in content
    assert "odoo_instance_start" in content


def test_mcp_configs_valid_json(workspace: Path) -> None:
    import json

    run_init(workspace)
    for editor in (".cursor", ".windsurf"):
        data = json.loads((workspace / editor / "mcp.json").read_text())
        assert "mcpServers" in data
        assert "odooforge" in data["mcpServers"]


def test_env_file_has_odoo_url(workspace: Path) -> None:
    run_init(workspace)
    content = (workspace / ".env").read_text()
    assert "ODOO_URL" in content


def test_docker_files_created(workspace: Path) -> None:
    run_init(workspace)
    assert (workspace / "docker" / "docker-compose.yml").exists()
    assert (workspace / "docker" / "odoo.conf").exists()


def test_addons_keep_exists(workspace: Path) -> None:
    run_init(workspace)
    assert (workspace / "addons" / ".keep").exists()


def test_gitignore_has_odooforge_section(workspace: Path) -> None:
    run_init(workspace)
    content = (workspace / ".gitignore").read_text()
    assert "# OdooForge" in content
    assert ".env" in content


# ── Skip behavior ────────────────────────────────────────────────


def test_skip_existing_files(workspace: Path) -> None:
    """Running init twice should skip all files on the second run."""
    run_init(workspace)
    results = run_init(workspace)

    statuses = {s for _, s in results}
    assert statuses == {"skipped"}, f"Expected all skipped, got: {results}"


def test_skip_preserves_existing_content(workspace: Path) -> None:
    """Existing files should not be overwritten."""
    (workspace / "CLAUDE.md").write_text("my custom content")
    run_init(workspace)
    assert (workspace / "CLAUDE.md").read_text() == "my custom content"


# ── Gitignore append logic ───────────────────────────────────────


def test_gitignore_appends_to_existing(workspace: Path) -> None:
    """If .gitignore exists without OdooForge section, append it."""
    (workspace / ".gitignore").write_text("node_modules/\n")
    run_init(workspace)
    content = (workspace / ".gitignore").read_text()
    assert "node_modules/" in content  # original preserved
    assert "# OdooForge" in content  # section appended


def test_gitignore_skips_if_section_exists(workspace: Path) -> None:
    """If .gitignore already has OdooForge section, skip it."""
    (workspace / ".gitignore").write_text("# OdooForge\n.env\n")
    results = run_init(workspace)
    gi_results = [(p, s) for p, s in results if ".gitignore" in p]
    assert gi_results[0][1] == "skipped"


# ── CLI dispatcher ───────────────────────────────────────────────


def test_cli_dispatches_init() -> None:
    """``odooforge init`` should call run_init."""
    from odooforge.cli import main

    with patch.object(sys, "argv", ["odooforge", "init"]), \
         patch("odooforge.init.run_init") as mock_run:
        main()
        mock_run.assert_called_once()


def test_cli_help_flag(capsys: pytest.CaptureFixture[str]) -> None:
    from odooforge.cli import main

    with patch.object(sys, "argv", ["odooforge", "-h"]):
        main()
    captured = capsys.readouterr()
    assert "init" in captured.out
    assert "Usage" in captured.out


# ── Return value ─────────────────────────────────────────────────


def test_run_init_returns_results(workspace: Path) -> None:
    results = run_init(workspace)
    assert len(results) == 11  # total files
    assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
