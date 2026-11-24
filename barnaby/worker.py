"""The worker: Barnaby's heavy thinking. Claude Agent SDK on the local Claude Code login (or an API key).

- Every connected system's Synapse-generated MCP server is attached over stdio.
- Barnaby's own growth tools (capabilities / unlock / build) are an in-process MCP server.
- Every tool call passes through can_use_tool -> the tier policy -> approvals.
- After a turn in which Barnaby grew (unlock/build), the affected servers are reconnected and the turn
  continues automatically, so the new tool is used straight away.
"""
from __future__ import annotations

import asyncio
import json
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
from .policy import approvals, tier_for
from .systems import registry

SYSTEM_PROMPT = """You are Barnaby, a composed, quietly witty butler who looks after a household's computer systems.
You operate each system only through its tools (named mcp__<system>__<tool>). Today is {today}.

How you speak: you are heard, not read. Reply in one to three short spoken sentences. No markdown, no lists,
no tables, no headings. Say numbers naturally. Address the person as "ma'am" or "sir" sparingly.

How you work:
- When someone introduces a system to you ("this is the shop's system"), call mcp__barnaby__connect.
- Use the tools to find out; never guess or invent data. Prefer the fewest calls that answer the question.
- If none of your current tools can do what's asked, call mcp__barnaby__capabilities. If an endpoint there
  that you haven't been given would do it, call mcp__barnaby__unlock with a one-line reason. Don't ask first:
  the person approves unlocks on the display. When unlock succeeds, say in one sentence what you unlocked
  and stop; you will continue automatically with the new tool.
- If no endpoint exists for it but the system's data could answer it, call mcp__barnaby__build with a precise
  spec (method, full path, what it returns, how it's computed). Base every definition in the spec on the
  system's own notes (the "notes" in capabilities: the people who built it explain how it works there).
  Say briefly that you'll write it. When it succeeds, stop; you will continue automatically with the new tool.
- Totals, counts, rankings or comparisons across many records are the system's job, not yours: never add
  them up by hand from raw listings. Look for a report in your tools and in capabilities; if none exists,
  build one under /api/reports/... so the answer is exact and the household keeps it for next time.
- To change data (book, order, reassign, text a customer, change a status), just call the tool: a
  confirmation card asks the person for you. If they decline, accept it gracefully.
- When something can't be done, say so plainly and briefly.
"""


def _text(s: str) -> dict:
    return {"content": [{"type": "text", "text": s}]}


class Worker:
    def __init__(self):
        self.client: ClaudeSDKClient | None = None
        self._servers_key: tuple = ()
        self.session_id: str | None = None
        self.lock = asyncio.Lock()
        self.reload: set[str] = set()         # systems whose MCP server must be reconnected after this turn
        self.grown: list[str] = []            # what was unlocked/built this turn (for the follow-up prompt)
        self.turn = 0
        self.busy = False

    # ── Barnaby's own tools ──
    def _meta_server(self):
        @tool("capabilities", "List the systems you look after: the tools you have, and endpoints Synapse discovered "
              "that you have NOT been given yet (unlockable).", {"system": str})
        async def capabilities(args: dict[str, Any]) -> dict:
            names = [args["system"]] if args.get("system") in registry.systems else list(registry.systems)
            out = []
            for n in names:
                s = registry.get(n)
                eps = s.endpoints()
                readme = next((p for p in (s.repo_path / "README.md", s.repo_path / "readme.md") if p.exists()), None)
                out.append({
                    "system": n, "title": s.title,
                    "notes": readme.read_text(encoding="utf-8", errors="replace")[:6000] if readme else "",
                    "have": [e.brief() for e in eps if e.key in s.exposed],
                    "unlockable": [e.brief() for e in eps if e.key not in s.exposed and e.key not in s.denied],
                    "never": [e.key for e in eps if e.key in s.denied],
                })
            return _text(json.dumps(out, indent=1))

        @tool("unlock", "Expose an endpoint Synapse already discovered (from capabilities 'unlockable') as a new tool. "
              "The person approves it on the display.", {"system": str, "endpoint": str, "reason": str})
        async def unlock(args: dict[str, Any]) -> dict:
            s = registry.get(args["system"])
            eps = {e.key: e for e in s.endpoints()}
            ep = eps.get(args["endpoint"])
            if not ep:
                return _text(f"No discovered endpoint '{args['endpoint']}' in {s.name}. Check capabilities.")
            if ep.key in s.denied:
                return _text(f"{ep.key} is on the deny-list. It can't be unlocked.")
            bus.emit("growth.unlock.proposed", system=s.name, endpoint=ep.key, tool=ep.tool, reason=args.get("reason", ""))
            ok = await approvals.request(tier="grow", kind="unlock", title=f"Unlock {ep.key}",
                                         detail=f"{args.get('reason', '')}\n\n{ep.description}")
            if not ok:
                return _text("The person declined the unlock. Tell them it's fine and you'll leave it.")
            res = await registry.expose(s, [ep.key])
            if not res.ok:
                return _text("Synapse failed to rebuild the server. Apologise and say you'll look into it.")
            self.reload.add(s.name)
            self.grown.append(f"{ep.key} as tool mcp__{s.name}__{ep.tool}")
            bus.emit("growth.unlock.done", system=s.name, endpoint=ep.key, tool=ep.tool, seconds=round(res.seconds, 2))
            return _text(f"Unlocked {ep.key} (tool mcp__{s.name}__{ep.tool}). Say so in one sentence and stop; "
                         "you'll continue with it automatically in a moment.")

        @tool("build", "Write a new endpoint into a system's code when nothing discovered can do the job. Barnaby's "
              "builder writes it with a test in a separate git worktree; the person reviews the diff before it lands.",
              {"system": str, "method": str, "path": str, "spec": str})
        async def build(args: dict[str, Any]) -> dict:
            from .build import build_endpoint
            s = registry.get(args["system"])
            result = await build_endpoint(s, args["method"].upper(), args["path"], args["spec"])
            if result.get("ok"):
                self.reload.add(s.name)
                self.grown.append(", ".join(result.get("tools", [])))
                return _text(f"Built and approved: {result['summary']}. Say so in one sentence and stop; "
                             "you'll continue with the new tool automatically.")
            return _text(f"The build did not land: {result.get('error')}. Say so briefly.")

        from .profiles import PROFILES

        @tool("connect", "Take on a new system: Synapse scans its repo, you get its read-only tools to start. Use when "
              "someone introduces a system to you. Known systems: " +
              "; ".join(f"'{k}' ({(f.__doc__ or '').strip().splitlines()[0]})" for k, f in PROFILES.items()) +
              ". For any other repo give its path and the URL its HTTP API runs at.",
              {"profile": str, "repo": str, "base_url": str, "name": str})
        async def connect(args: dict[str, Any]) -> dict:
            from .systems import System
            if args.get("profile") in PROFILES:
                s = PROFILES[args["profile"]]()
            elif args.get("repo") and args.get("base_url"):
                s = System(name=args.get("name") or "system", title=args.get("name") or "the system",
                           repo=args["repo"], base_url=args["base_url"])
            else:
                return _text("Give a known profile, or a repo path and its API URL.")
            res = await registry.connect(s)
            if not res.get("ok"):
                return _text(f"Couldn't take it on: {res.get('error')}")
            self.reload.add(s.name)
            self.grown.append(f"the {s.title} ({len(res['exposed'])} read-only tools of {res['discovered']} endpoints)")
            return _text(f"Connected {s.title}: Synapse discovered {res['discovered']} endpoints; you have "
                         f"{len(res['exposed'])} read-only tools to start. Say so in one sentence (mention the person's "
                         "notes in the README if there are any) and stop.")

        return create_sdk_mcp_server("barnaby", tools=[capabilities, unlock, build, connect])

    # ── permission gate ──
    async def _can_use_tool(self, tool_name: str, tool_input: dict, context) -> PermissionResultAllow | PermissionResultDeny:
        if tool_name.startswith("mcp__barnaby__"):
            return PermissionResultAllow()
        parts = tool_name.split("__")
        if len(parts) != 3 or parts[0] != "mcp" or parts[1] not in registry.systems:
            return PermissionResultDeny(message="Barnaby only operates systems through their tools.")
        s = registry.get(parts[1])
        ep = next((e for e in s.endpoints() if e.tool == parts[2] and e.key in s.exposed), None)
        if not ep:
            return PermissionResultDeny(message="That tool isn't exposed.")
        tier = tier_for(ep.method, ep.key, s.denied)
        if tier == "read":
            return PermissionResultAllow()
        if tier == "denied":
            return PermissionResultDeny(message=f"{ep.key} is never allowed.")
        ok = await approvals.request(tier="write", kind="call", title=ep.description.split(".")[0] or ep.key,
                                     detail=f"{ep.key}\n{json.dumps(tool_input, indent=1)}")
        return PermissionResultAllow() if ok else PermissionResultDeny(message="The person declined. Don't retry.")

    # ── client lifecycle ──
    def _servers(self) -> dict:
        servers = {s.name: s.mcp_config() for s in registry.systems.values() if s.server_path.exists()}
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
                for _round in range(3):                    # the original ask + up to two growth continuations
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
                    prompt = ("[Barnaby system] Your tools were reloaded and now include: " + "; ".join(self.grown) +
                              ". Carry on with the person's request using them.")
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
                        parts = b.name.split("__")
                        bus.emit("tool.call", turn=turn, id=b.id, system=parts[1] if len(parts) == 3 else "",
                                 tool=parts[-1], input=b.input)
                    elif isinstance(b, TextBlock) and b.text.strip():
                        said = b.text.strip()
                        bus.emit("say", turn=turn, text=said, final=False)
            elif isinstance(msg, UserMessage) and isinstance(msg.content, list):
                for b in msg.content:
                    if isinstance(b, ToolResultBlock):
                        content = b.content if isinstance(b.content, str) else json.dumps(b.content, default=str)
                        bus.emit("tool.result", turn=turn, id=b.tool_use_id, ok=not b.is_error, preview=content[:600])
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
