#!/usr/bin/env python3
"""
Verify OdooForge Release

This script tests the installed `odooforge` package by running it as a subprocess
and communicating via MCP stdio protocol.

Usage:
    pip install odooforge
    python3 scripts/verify_release.py
"""

import sys
import os
import json
import subprocess
import threading
import time
import shutil

def verify_release():
    # Check if odooforge is available in path (via uvx or pip)
    executable = shutil.which("odooforge")
    cmd = ["odooforge"]
    
    if not executable:
        # Try uvx if odooforge not in path
        if shutil.which("uvx"):
            cmd = ["uvx", "odooforge"]
        else:
            print("❌ 'odooforge' command not found. Please install via 'pip install odooforge'")
            sys.exit(1)

    # Debug: Check installed version
    try:
        from importlib.metadata import version
        v = version("odooforge")
        print(f"📦 Installed OdooForge version: {v}")
    except Exception:
        print("⚠️ Could not determine installed version")

    print(f"🚀 Launching OdooForge via: {' '.join(cmd)}")
    

    
    # NOTE: We do not inject DOCKER_COMPOSE_PATH here to verify 
    # that the installed package can find its own bundled docker-compose.yml (v0.1.2+)

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1
    )

    # Helper to send JSON-RPC message
    def send_request(method, params=None, id=1):
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": id
        }
        json_str = json.dumps(msg)
        print(f"-> Sending {method}...")
        process.stdin.write(json_str + "\n")
        process.stdin.flush()

    # Read stdout in loop
    def read_response():
        while True:
            line = process.stdout.readline()
            if not line:
                break
            try:
                data = json.loads(line)
                if "result" in data:
                    return data["result"]
                if "error" in data:
                    print(f"❌ Error: {data['error']}")
                    return None
            except json.JSONDecodeError:
                pass
        return None

    # 1. Initialize
    send_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "verify_script", "version": "1.0"}
    }, id=1)
    
    init_result = read_response()
    if not init_result:
        print("❌ Failed to receive initialize response")
        sys.exit(1)
        
    server_info = init_result.get("serverInfo", {})
    print(f"✅ Connected to {server_info.get('name')} v{server_info.get('version')}")

    # 2. List Tools
    send_request("tools/list", {}, id=2)
    tools_result = read_response()
    
    if not tools_result or "tools" not in tools_result:
        print("❌ Failed to list tools")
        sys.exit(1)
        
    tools = tools_result["tools"]
    tool_names = [t["name"] for t in tools]
    print(f"✅ Found {len(tools)} tools")
    
    # 3. Verify core tools exist
    required_tools = [
        "odoo_instance_start",
        "odoo_db_create",
        "odoo_record_search",
        "odoo_diagnostics_health_check"
    ]
    
    missing = [t for t in required_tools if t not in tool_names]
    
    if missing:
        print(f"❌ Missing required tools: {missing}")
        sys.exit(1)
        
    print("✅ Core basic tools verified")
    
    # Terminate
    process.terminate()
    print("\n✨ Release verification PASSED!")

if __name__ == "__main__":
    verify_release()
