"""OdooForge CLI — dispatcher for MCP server and workspace commands."""

from __future__ import annotations

import logging
import sys


def main() -> None:
    """CLI entry point: ``odooforge`` runs the MCP server, ``odooforge init`` initializes a workspace."""
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        from odooforge.init import run_init

        run_init()
    elif len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        _print_usage()
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )
        from odooforge.server import mcp

        mcp.run()


def _print_usage() -> None:
    print(
        "Usage: odooforge [command]\n"
        "\n"
        "Commands:\n"
        "  (none)    Start the OdooForge MCP server\n"
        "  init      Initialize current directory as an OdooForge workspace\n"
        "  -h        Show this help message\n"
    )


if __name__ == "__main__":
    main()
