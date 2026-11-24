"""Phase 0 smoke test: can the core's MCP client drive a Synapse-generated server?

Starts sandbox/smoke_app (FastAPI) on 127.0.0.1:8765, launches its synapse_auto_server.py under the
pinned mcp==1.30 runtime venv over stdio, then lists and calls every tool through the FastMCP 4 client
(the one Pydantic AI's MCPToolset wraps). Prints one PASS/FAIL/NOTE line per check.

Run from the repo root:  .venv/Scripts/python scripts/smoke/smoke_mcp.py
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "sandbox" / "smoke_app"
SERVER = APP_DIR / "synapse_auto_server.py"
RUNTIME_PY = ROOT / "runtime" / "mcp-servers" / ".venv" / "Scripts" / "python.exe"
CORE_PY = ROOT / ".venv" / "Scripts" / "python.exe"
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"


def line(status: str, what: str, detail: str = "") -> None:
    print(f"[{status:4}] {what}" + (f"  ->  {detail}" if detail else ""), flush=True)


def start_app() -> subprocess.Popen:
    proc = subprocess.Popen(
        [str(CORE_PY), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            httpx.get(f"{BASE}/items", timeout=0.5)
            return proc
        except httpx.HTTPError:
            time.sleep(0.2)
    proc.kill()
    raise SystemExit("smoke app did not start")


def text_of(result) -> str:
    """Best-effort readable form of a CallToolResult."""
    data = getattr(result, "data", None)
    if data is not None:
        return json.dumps(data, default=str)[:200]
    parts = [getattr(c, "text", str(c)) for c in (getattr(result, "content", None) or [])]
    return " ".join(parts)[:200]


async def main() -> int:
    app = start_app()
    failures = 0
    try:
        transport = StdioTransport(
            command=str(RUNTIME_PY), args=[str(SERVER)], env={"ENDPOINT_BASE_URL": BASE}, cwd=str(APP_DIR),
        )
        t0 = time.perf_counter()
        async with Client(transport) as client:
            line("PASS", "connect + initialize (FastMCP 4 client <-> mcp 1.30 server)", f"{(time.perf_counter() - t0) * 1000:.0f} ms")
            tools = await client.list_tools()
            names = sorted(t.name for t in tools)
            line("PASS", "list_tools", ", ".join(names))
            for t in tools:
                props = (t.inputSchema or {}).get("properties", {})
                req = (t.inputSchema or {}).get("required", [])
                line("NOTE", f"schema {t.name}", f"params={list(props)} required={req} types={[p.get('type', 'any') for p in props.values()]}")

            async def call(name: str, args: dict, expect: str):
                nonlocal failures
                try:
                    r = await client.call_tool(name, args, raise_on_error=False)
                    err = bool(getattr(r, "is_error", False))
                    line("FAIL" if err and expect == "ok" else "PASS" if not err else "NOTE",
                         f"call {name}({args}) expecting {expect}", ("ERROR: " if err else "") + text_of(r))
                    if err and expect == "ok":
                        failures += 1
                except Exception as e:  # noqa: BLE001 - smoke test: report everything
                    failures += 1
                    line("FAIL", f"call {name}({args})", f"{type(e).__name__}: {e}"[:200])

            await call("list_items", {}, "ok")                     # returns a JSON list but the tool is annotated -> dict
            await call("get_item", {"item_id": 1}, "ok")
            await call("search", {}, "error (query param dropped)")
            await call("create_order", {"item_id": 1, "quantity": 2, "supplier": "Shimano", "note": "rush"}, "ok")
            await call("fail", {}, "error (is the 409 reason visible?)")
            await call("ping", {}, "error (prefix /v2 dropped)")
    finally:
        app.terminate()
    print("\nRESULT:", "PASS" if failures == 0 else f"{failures} unexpected failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
