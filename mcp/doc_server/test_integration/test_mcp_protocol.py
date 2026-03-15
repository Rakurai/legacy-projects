"""
Test the MCP server over stdio with real JSON-RPC protocol messages.

Sends initialize → initialized → tools/list → tools/call (resolve_entity) → shutdown.
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def main():
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "server.server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(Path(__file__).parent.parent),
    )

    async def send(msg: dict) -> dict | None:
        """Send JSON-RPC message and read response."""
        payload = json.dumps(msg)
        proc.stdin.write(payload.encode() + b"\n")
        await proc.stdin.drain()

        # Read response (may take a moment for initialization)
        try:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=15)
            if line:
                return json.loads(line.decode().strip())
        except asyncio.TimeoutError:
            print(f"  ⏱ Timeout waiting for response to {msg.get('method', 'unknown')}")
        return None

    async def send_notification(msg: dict):
        """Send JSON-RPC notification (no response expected)."""
        payload = json.dumps(msg)
        proc.stdin.write(payload.encode() + b"\n")
        await proc.stdin.drain()

    print("\n=== MCP Server Protocol Test ===\n")

    # 1. Initialize
    print("[1] Sending initialize...")
    resp = await send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "smoke_test", "version": "1.0"},
        }
    })

    if resp and "result" in resp:
        server_info = resp["result"].get("serverInfo", {})
        tools_cap = resp["result"].get("capabilities", {}).get("tools", {})
        print(f"  ✅ Server: {server_info.get('name', '?')} v{server_info.get('version', '?')}")
        print(f"  ✅ Protocol: {resp['result'].get('protocolVersion', '?')}")
    else:
        print(f"  ❌ Initialize failed: {resp}")
        proc.kill()
        return 1

    # 2. Send initialized notification
    print("[2] Sending initialized notification...")
    await send_notification({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    })
    # Small delay to let server process
    await asyncio.sleep(0.5)
    print("  ✅ Sent")

    # 3. List tools
    print("[3] Listing tools...")
    resp = await send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    })

    if resp and "result" in resp:
        tools = resp["result"].get("tools", [])
        tool_names = [t["name"] for t in tools]
        print(f"  ✅ {len(tools)} tools available: {', '.join(tool_names)}")
    else:
        print(f"  ❌ tools/list failed: {resp}")

    # 4. Call resolve_entity
    print("[4] Calling resolve_entity('do_kill')...")
    resp = await send({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "resolve_entity",
            "arguments": {"query": "do_kill"}
        }
    })

    if resp and "result" in resp:
        content = resp["result"].get("content", [])
        if content:
            data = json.loads(content[0].get("text", "{}"))
            status = data.get("resolution_status", "?")
            candidates = data.get("resolution_candidates", 0)
            print(f"  ✅ Status: {status}, Candidates: {candidates}")
            if data.get("candidates"):
                first = data["candidates"][0]
                print(f"     First: {first.get('name')} ({first.get('kind')}) - {first.get('brief', 'no brief')}")
        else:
            print(f"  ❌ Empty content: {resp['result']}")
    else:
        err = resp.get("error", {}) if resp else "no response"
        print(f"  ❌ resolve_entity failed: {err}")

    # 5. Call search
    print("[5] Calling search('combat damage')...")
    resp = await send({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "search",
            "arguments": {"query": "combat damage", "limit": 5}
        }
    })

    if resp and "result" in resp:
        content = resp["result"].get("content", [])
        if content:
            text_val = content[0].get("text", "")
            try:
                data = json.loads(text_val)
                mode = data.get("search_mode", "?")
                count = data.get("result_count", 0)
                print(f"  ✅ Mode: {mode}, Results: {count}")
            except json.JSONDecodeError:
                # If it's an error message, print it
                print(f"  ⚠ Non-JSON response: {text_val[:200]}")
        else:
            print(f"  ❌ Empty content")
    elif resp and "error" in resp:
        print(f"  ❌ search error: {resp['error'].get('message', '?')}")
    else:
        print(f"  ❌ search failed: no response")

    # 6. Call get_callers
    print("[6] Calling get_callers...")
    resp = await send({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "get_callers",
            "arguments": {"entity_id": "fight_8cc_1a84db4297aa2c33f5150d9c0577d74bab", "depth": 1}
        }
    })

    if resp and "result" in resp:
        content = resp["result"].get("content", [])
        if content:
            text_val = content[0].get("text", "")
            try:
                data = json.loads(text_val)
                depths = data.get("callers_by_depth", {})
                total = sum(len(v) for v in depths.values())
                print(f"  ✅ Callers: {total} across {len(depths)} depth levels")
            except json.JSONDecodeError:
                print(f"  ⚠ Non-JSON response: {text_val[:200]}")
        else:
            print(f"  ❌ Empty content")
    elif resp and "error" in resp:
        print(f"  ❌ get_callers error: {resp['error'].get('message', '?')}")
    else:
        print(f"  ❌ get_callers failed: no response")

    # Shutdown
    print("\n[Done] Shutting down server...")
    proc.stdin.close()
    try:
        await asyncio.wait_for(proc.wait(), timeout=5)
        print(f"  ✅ Server exited cleanly (code={proc.returncode})")
    except asyncio.TimeoutError:
        proc.kill()
        print("  ⚠ Server killed after timeout")

    # Read stderr for any errors
    stderr = await proc.stderr.read()
    stderr_text = stderr.decode()
    error_lines = [l for l in stderr_text.split("\n") if "ERROR" in l or "Traceback" in l]
    if error_lines:
        print(f"\n⚠ Server errors:")
        for line in error_lines[:5]:
            print(f"  {line}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
