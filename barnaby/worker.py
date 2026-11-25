"""The worker: Barnaby's heavy thinking. Claude Agent SDK on the local Claude Code login (or an API key).

- Every connected system's Synapse-generated MCP server is attached over stdio.
- Barnaby's own growth tools (capabilities / unlock / build) are an in-process MCP server.
- Every tool call passes through can_use_tool -> the tier policy -> approvals.
- After a turn in which Barnaby grew (unlock/build), the affected servers are reconnected and the turn
  continues automatically, so the new tool is used straight away.

The prompt, the tier gate and the growth tools live in toolkit.py, shared with the any-model worker (worker_byom.py).
"""
from __future__ import annotations

from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    tool,
)

from .config import STATE, demo_today, settings
from .events import bus
from .toolkit import (
    MAX_CONTINUATIONS,
    SYSTEM_PROMPT,
    GrowthTool,
    WorkerState,
    continuation,
    gate,
    growth_tools,
    system_servers,
)


def _text(s: str) -> dict:
    return {"content": [{"type": "text", "text": s}]}


class Worker(WorkerState):
    def __init__(self):
        super().__init__()
        self.client: ClaudeSDKClient | None = None
        self._servers_key: tuple = ()
        self.session_id: str | None = None

    # ── Barnaby's own tools (toolkit.py), as an in-process MCP server ──
    def _meta_server(self):
        def sdk_tool(t: GrowthTool):
            async def handler(args: dict[str, Any]) -> dict:
                return _text(await t.run(self, args))
            return tool(t.name, t.description, dict.fromkeys(t.params, str))(handler)

        return create_sdk_mcp_server("barnaby", tools=[sdk_tool(t) for t in growth_tools()])

    # ── permission gate: the shared tier policy ──
    async def _can_use_tool(self, tool_name: str, tool_input: dict, context) -> PermissionResultAllow | PermissionResultDeny:
        refusal = await gate(tool_name, tool_input)
        return PermissionResultAllow() if refusal is None else PermissionResultDeny(message=refusal)

    # ── client lifecycle ──
    def _servers(self) -> dict:
        servers = system_servers()
        servers["barnaby"] = self._meta
        return servers

    async def _ensure_client(self) -> ClaudeSDKClient:
        if not hasattr(self, "_meta"):
            self._meta = self._meta_server()
        servers = self._servers()
        key = tuple(sorted(servers))
        if self.client and key == self._servers_key:
            return self.client
        if self.client:
            await self.client.disconnect()
        opts = ClaudeAgentOptions(
            model=settings.worker_model,
            system_prompt=SYSTEM_PROMPT.format(today=demo_today() or "today"),
            mcp_servers=servers, strict_mcp_config=True,
            tools=[], setting_sources=[], permission_mode="default", can_use_tool=self._can_use_tool,
            env=settings.worker_env(), cwd=str(STATE), max_turns=40, effort="medium",
            resume=self.session_id,
        )
        self.client = ClaudeSDKClient(opts)
        await self.client.connect()
        self._servers_key = key
        return self.client

    async def close(self) -> None:
        if self.client:
            await self.client.disconnect()

    # ── a turn ──
    async def ask(self, text: str) -> str:
        async with self.lock:
            self.busy = True
            self.turn += 1
            turn = self.turn
            bus.emit("turn.start", turn=turn, text=text)
            final = ""
            try:
                client = await self._ensure_client()
                prompt = text
                for _round in range(1 + MAX_CONTINUATIONS):    # the original ask + up to two growth continuations
                    self.reload.clear()
                    self.grown.clear()
                    await client.query(prompt)
                    final = await self._drain(client, turn)
                    if not self.reload:
                        break
                    old_key = self._servers_key
                    client = await self._ensure_client()          # a newly connected system: new client, same session
                    for name in self.reload:
                        if self._servers_key == old_key:
                            await client.reconnect_mcp_server(name)
                        bus.emit("system.reloaded", system=name)
                    prompt = continuation(self.grown)
            except Exception as e:  # noqa: BLE001 - surface every failure to the display
                bus.emit("log", level="error", text=f"{type(e).__name__}: {e}")
                final = "I'm terribly sorry, something went wrong on my side."
                bus.emit("say", text=final, final=True)
            finally:
                self.busy = False
                bus.emit("turn.end", turn=turn)
            return final

    async def _drain(self, client: ClaudeSDKClient, turn: int) -> str:
        said = ""
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for b in msg.content:
                    if isinstance(b, ToolUseBlock):
                        self.note_call(turn, b.id, b.name, b.input)
                    elif isinstance(b, TextBlock) and b.text.strip():
                        said = b.text.strip()
                        bus.emit("say", turn=turn, text=said, final=False)
            elif isinstance(msg, UserMessage) and isinstance(msg.content, list):
                for b in msg.content:
                    if isinstance(b, ToolResultBlock):
                        self.note_result(turn, b.tool_use_id, not b.is_error, b.content)
            elif isinstance(msg, SystemMessage) and getattr(msg, "subtype", "") == "init":
                self.session_id = (msg.data or {}).get("session_id", self.session_id)
            elif isinstance(msg, ResultMessage):
                self.session_id = msg.session_id or self.session_id
                bus.emit("turn.result", turn=turn, ok=not msg.is_error, ms=msg.duration_ms, turns=msg.num_turns,
                         cost=msg.total_cost_usd)
        if said:
            bus.emit("say", turn=turn, text=said, final=True)
        return said


worker = Worker()
