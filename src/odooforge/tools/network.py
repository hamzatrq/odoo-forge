"""Network tools — expose Odoo via tunneling for external access."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Track active tunnel processes
_active_tunnels: dict[str, asyncio.subprocess.Process] = {}


async def odoo_network_expose(
    port: int = 8069,
    method: str = "ssh",
    subdomain: str | None = None,
) -> dict[str, Any]:
    """Expose the local Odoo instance to the internet via a tunnel.

    Useful for testing webhooks, sharing demos, or remote access.

    Args:
        port: Local port to expose (default: 8069).
        method: Tunneling method — "ssh" (localhost.run) or "cloudflared".
        subdomain: Optional preferred subdomain (availability not guaranteed).
    """
    global _active_tunnels

    if str(port) in _active_tunnels:
        return {
            "status": "already_running",
            "message": f"A tunnel is already active on port {port}. Use odoo_network_status to check.",
        }

    try:
        if method == "ssh":
            cmd = ["ssh", "-R", f"80:localhost:{port}", "nokey@localhost.run"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait briefly for the URL to appear
            url = None
            try:
                async with asyncio.timeout(10):
                    while True:
                        line = await process.stdout.readline()
                        if not line:
                            break
                        decoded = line.decode().strip()
                        if "https://" in decoded:
                            url = decoded.split("https://")[1].split()[0]
                            url = f"https://{url}"
                            break
            except asyncio.TimeoutError:
                pass

            _active_tunnels[str(port)] = process

            return {
                "status": "exposed",
                "url": url or "Tunnel starting... check odoo_network_status for URL.",
                "port": port,
                "method": method,
                "message": f"Odoo exposed at {url or 'starting...'}",
            }

        elif method == "cloudflared":
            cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]
            if subdomain:
                cmd.extend(["--hostname", subdomain])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            url = None
            try:
                async with asyncio.timeout(15):
                    while True:
                        line = await process.stderr.readline()
                        if not line:
                            break
                        decoded = line.decode().strip()
                        if "https://" in decoded and "trycloudflare" in decoded:
                            url = "https://" + decoded.split("https://")[1].split()[0]
                            break
            except asyncio.TimeoutError:
                pass

            _active_tunnels[str(port)] = process

            return {
                "status": "exposed",
                "url": url or "Tunnel starting...",
                "port": port,
                "method": method,
                "message": f"Odoo exposed via Cloudflare at {url or 'starting...'}",
            }

        else:
            return {
                "status": "error",
                "message": f"Unsupported method '{method}'. Use 'ssh' or 'cloudflared'.",
            }

    except FileNotFoundError as e:
        return {
            "status": "error",
            "message": f"Required tool not found: {e}",
            "suggestion": f"Install {'openssh' if method == 'ssh' else 'cloudflared'} first.",
        }


async def odoo_network_status() -> dict[str, Any]:
    """Check the status of active network tunnels."""
    global _active_tunnels

    tunnels = []
    for port, process in list(_active_tunnels.items()):
        if process.returncode is not None:
            # Process has exited
            del _active_tunnels[port]
            continue

        tunnels.append({
            "port": int(port),
            "pid": process.pid,
            "status": "running",
        })

    return {
        "tunnels": tunnels,
        "count": len(tunnels),
        "message": f"{len(tunnels)} active tunnel(s)." if tunnels else "No active tunnels.",
    }


async def odoo_network_stop(
    port: int | None = None,
) -> dict[str, Any]:
    """Stop network tunnels.

    Args:
        port: Specific port to stop. If omitted, stops all tunnels.
    """
    global _active_tunnels

    if port:
        key = str(port)
        if key not in _active_tunnels:
            return {"status": "error", "message": f"No tunnel running on port {port}."}
        _active_tunnels[key].terminate()
        del _active_tunnels[key]
        return {"status": "stopped", "port": port, "message": f"Tunnel on port {port} stopped."}

    # Stop all
    count = len(_active_tunnels)
    for key, process in list(_active_tunnels.items()):
        process.terminate()
    _active_tunnels.clear()

    return {
        "status": "stopped",
        "count": count,
        "message": f"Stopped {count} tunnel(s).",
    }
