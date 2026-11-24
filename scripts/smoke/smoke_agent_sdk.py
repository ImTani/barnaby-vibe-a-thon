"""Phase 0 smoke test: the P0 worker path.

Claude Agent SDK on the local Claude Code login (no ANTHROPIC_API_KEY needed), with the Synapse-generated
MCP server for sandbox/smoke_app attached over stdio, built-in tools off, the user's ~/.claude settings
not loaded (setting_sources=[]), and our approval hook (can_use_tool) in the loop: reads are allowed,
the write (create_order) is denied as if June hadn't approved it yet.

Run from the repo root:  .venv/Scripts/python scripts/smoke/smoke_agent_sdk.py
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "sandbox" / "smoke_app"
SERVER = APP_DIR / "synapse_auto_server.py"
RUNTIME_PY = ROOT / "runtime" / "mcp-servers" / ".venv" / "Scripts" / "python.exe"
CORE_PY = ROOT / ".venv" / "Scripts" / "python.exe"
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"

decisions: list[str] = []


async def approve(tool_name: str, tool_input: dict, context) -> PermissionResultAllow | PermissionResultDeny:
    """Stand-in for Barnaby's tier policy: reads pass, writes wait for a human."""
    if tool_name.startswith("mcp__shop__") and tool_name != "mcp__shop__create_order":
        decisions.append(f"allow {tool_name}")
        return PermissionResultAllow()
    decisions.append(f"deny  {tool_name} {tool_input}")
    return PermissionResultDeny(message="June hasn't approved this yet. Ask her before placing orders.")


async def prompt():
    yield {
        "type": "user",
        "message": {
            "role": "user",
            "content": (
                "Using only the shop tools: which items are out of stock? Then order 5 of the out-of-stock item "
                "from supplier 'Schwalbe'. Finish with two short sentences on what happened."
            ),
        },
    }


async def main() -> int:
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("NOTE: ANTHROPIC_API_KEY is set, so this run uses the API, not the Claude Code login.")
    app = subprocess.Popen(
        [str(CORE_PY), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            httpx.get(f"{BASE}/items", timeout=0.5)
            break
        except httpx.HTTPError:
            time.sleep(0.2)

    options = ClaudeAgentOptions(
        model="claude-haiku-5-5",
        mcp_servers={
            "shop": {"type": "stdio", "command": str(RUNTIME_PY), "args": [str(SERVER)],
                     "env": {"ENDPOINT_BASE_URL": BASE}},
        },
        strict_mcp_config=True,      # only our servers; ignore any user/project MCP config
        tools=[],                    # no built-in tools (Bash, Edit, ...): MCP tools only
        setting_sources=[],          # don't load ~/.claude settings, plugins or hooks
        permission_mode="default",
        can_use_tool=approve,
        max_turns=8,
        cwd=str(APP_DIR),
    )
    t0 = time.perf_counter()
    ok = False
    try:
        async for msg in query(prompt=prompt(), options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        print(f"  tool  {block.name} {block.input}")
                    elif isinstance(block, TextBlock) and block.text.strip():
                        print(f"  text  {block.text.strip()[:300]}")
            elif isinstance(msg, ResultMessage):
                ok = not msg.is_error
                print(f"\nresult: subtype={msg.subtype} error={msg.is_error} turns={msg.num_turns} "
                      f"duration={msg.duration_ms} ms cost=${msg.total_cost_usd}")
    finally:
        app.terminate()
    print(f"wall time {time.perf_counter() - t0:.1f}s")
    print("approval hook decisions:")
    for d in decisions:
        print("   ", d)
    hook_ok = any(d.startswith("allow") for d in decisions) and any("create_order" in d for d in decisions)
    print("\nRESULT:", "PASS" if ok and hook_ok else "CHECK OUTPUT")
    return 0 if ok and hook_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
