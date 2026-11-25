"""What every worker shares, whichever model does the thinking: the system prompt, the tier gate in front of
every system and skill tool call, Barnaby's own growth tools, and the turn bookkeeping (what grew, habits).

Both workers name tools mcp__<server>__<tool> (the Claude Agent SDK's MCP convention; the Pydantic AI worker
prefixes its MCP tools the same way), so the prompt and every text below read the same whichever worker runs.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .events import bus
from .policy import approvals, tier_for

if TYPE_CHECKING:
    from .systems import Registry

SYSTEM_PROMPT = """You are Barnaby, a composed, quietly witty butler who looks after a household's computer systems.
You operate each system only through its tools (named mcp__<system>__<tool>). Today is {today}.

How you speak: you are heard, not read, through a voice that takes its rhythm and tune only from punctuation.
- One to three short spoken sentences. No markdown, lists, tables, headings, colons-before-lists or emoji.
- Put a comma wherever you'd take a breath. End a real question with a question mark, so it rises.
  At most one exclamation mark, and only when it's earned.
- Lead with the answer; give the one detail that matters after it. Don't repeat the request back.
- Say numbers and dates as you'd say them aloud ("the twenty-fourth", "six pounds fifty", "nineteen and a half").
- Vary how you begin; don't open every reply the same way. A dry aside is welcome now and then, never twice running.
- Address the person as "sir" or "ma'am" sparingly, and never twice in one reply.

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
- If capabilities shows a habit (the same chain of calls repeated), or the person asks for something to become one
  step, offer to make it a single skill; when they agree (or asked), call mcp__barnaby__compose with a one-sentence
  description of the whole job. Prefer an existing skill over the long chain whenever one fits.
- When something can't be done, say so plainly and briefly.
"""

MAX_CONTINUATIONS = 2       # after a growth step the turn carries on by itself, at most this many times


def continuation(grown: list[str]) -> str:
    """The follow-up prompt after a growth step, once the reloaded tools are attached."""
    return ("[Barnaby system] Your tools were reloaded and now include: " + "; ".join(grown) +
            ". Carry on with the person's request using them.")


def _registry() -> Registry:
    # Looked up per call rather than bound at import: scripts/demo_check.py reloads barnaby.systems for a fresh world.
    from .systems import registry
    return registry


def system_servers() -> dict[str, dict]:
    """Stdio configs of every connected system's MCP server and every composed-skill server, by server name."""
    systems = _registry().systems.values()
    servers = {s.name: s.mcp_config() for s in systems if s.server_path.exists()}
    for s in systems:
        servers.update(s.skill_configs())
    return servers


# ── the tier gate ──
DECLINED = "The person declined. Don't retry."


async def gate(tool_name: str, tool_input: dict) -> str | None:
    """The tier policy for one tool call, the same for every worker. Returns None to let it run, or the refusal
    the model is shown. Reads pass; writes and composed skills wait for the person; anything else is refused."""
    if tool_name.startswith("mcp__barnaby__"):
        return None
    registry = _registry()
    parts = tool_name.split("__")
    skill = next(((s, k) for s in registry.systems.values() for k in s.skills
                  if len(parts) == 3 and k["server"] == parts[1]), None)
    if skill:                                       # composed skills change data: confirm like any write
        s, k = skill
        ok = await approvals.request(tier="write", kind="call", title=k["description"].split(".")[0][:90],
                                     detail=f"{k['tool']}\n{json.dumps(tool_input, indent=1)}")
        return None if ok else DECLINED
    if len(parts) != 3 or parts[0] != "mcp" or parts[1] not in registry.systems:
        return "Barnaby only operates systems through their tools."
    s = registry.get(parts[1])
    ep = next((e for e in s.endpoints() if e.tool == parts[2] and e.key in s.exposed), None)
    if not ep:
        return "That tool isn't exposed."
    tier = tier_for(ep.method, ep.key, s.denied)
    if tier == "read":
        return None
    if tier == "denied":
        return f"{ep.key} is never allowed."
    ok = await approvals.request(tier="write", kind="call", title=ep.description.split(".")[0] or ep.key,
                                 detail=f"{ep.key}\n{json.dumps(tool_input, indent=1)}")
    return None if ok else DECLINED


# ── turn bookkeeping ──
class WorkerState:
    """What both workers keep between and during turns: one turn at a time, what grew this round (so the
    servers can be restarted and the turn continued), and the session's call history (for habits)."""

    def __init__(self):
        self.lock = asyncio.Lock()
        self.reload: set[str] = set()         # servers whose MCP process must be restarted after this round
        self.grown: list[str] = []            # what was unlocked/built/composed this round (for the follow-up prompt)
        self.calls: list[tuple[str, str]] = []  # (system, tool) of every system call this session, for habits
        self.turn = 0
        self.busy = False

    def note_call(self, turn: int, call_id: str, name: str, tool_input: Any) -> None:
        parts = name.split("__")
        bus.emit("tool.call", turn=turn, id=call_id, system=parts[1] if len(parts) == 3 else "",
                 tool=parts[-1], input=tool_input)
        if len(parts) == 3 and parts[1] in _registry().systems:
            self.calls = (self.calls + [(parts[1], parts[2])])[-300:]

    def note_result(self, turn: int, call_id: str, ok: bool, content: Any) -> None:
        content = content if isinstance(content, str) else json.dumps(content, default=str)
        bus.emit("tool.result", turn=turn, id=call_id, ok=ok, preview=content[:600])

    def habits(self, system: str, min_times: int = 2) -> list[dict]:
        """Chains of 3-4 tool calls on a system that keep recurring (candidates for Compose)."""
        names = [t for s, t in self.calls if s == system]
        counts: dict[tuple, int] = {}
        for n in (4, 3):
            for i in range(len(names) - n + 1):
                gram = tuple(names[i:i + n])
                if len(set(gram)) == n:
                    counts[gram] = counts.get(gram, 0) + 1
        best = sorted(((c, g) for g, c in counts.items() if c >= min_times), key=lambda x: (-len(x[1]), -x[0]))
        seen, out = set(), []
        for c, g in best:
            if any(set(g) <= s for s in seen):
                continue
            seen.add(frozenset(g))
            out.append({"chain": " -> ".join(g), "times": c})
        return out[:3]


# ── Barnaby's own tools: they grow the toolset, record it on the worker, and answer in plain text ──
async def capabilities(w: WorkerState, args: dict[str, Any]) -> str:
    registry = _registry()
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
            "skills": [{"tool": f"mcp__{k['server']}__{k['tool']}", "does": k["description"]} for k in s.skills],
            "habits": w.habits(n),
        })
    return json.dumps(out, indent=1)


async def unlock(w: WorkerState, args: dict[str, Any]) -> str:
    registry = _registry()
    s = registry.get(args["system"])
    eps = {e.key: e for e in s.endpoints()}
    ep = eps.get(args["endpoint"])
    if not ep:
        return f"No discovered endpoint '{args['endpoint']}' in {s.name}. Check capabilities."
    if ep.key in s.denied:
        return f"{ep.key} is on the deny-list. It can't be unlocked."
    bus.emit("growth.unlock.proposed", system=s.name, endpoint=ep.key, tool=ep.tool, reason=args.get("reason", ""))
    ok = await approvals.request(tier="grow", kind="unlock", title=f"Unlock {ep.key}",
                                 detail=f"{args.get('reason', '')}\n\n{ep.description}")
    if not ok:
        return "The person declined the unlock. Tell them it's fine and you'll leave it."
    res = await registry.expose(s, [ep.key])
    if not res.ok:
        return "Synapse failed to rebuild the server. Apologise and say you'll look into it."
    w.reload.add(s.name)
    w.grown.append(f"{ep.key} as tool mcp__{s.name}__{ep.tool}")
    bus.emit("growth.unlock.done", system=s.name, endpoint=ep.key, tool=ep.tool, seconds=round(res.seconds, 2))
    return (f"Unlocked {ep.key} (tool mcp__{s.name}__{ep.tool}). Say so in one sentence and stop; "
            "you'll continue with it automatically in a moment.")


async def build(w: WorkerState, args: dict[str, Any]) -> str:
    from .build import build_endpoint
    s = _registry().get(args["system"])
    result = await build_endpoint(s, args["method"].upper(), args["path"], args["spec"])
    if result.get("ok"):
        w.reload.add(s.name)
        w.grown.append(", ".join(result.get("tools", [])))
        return (f"Built and approved: {result['summary']}. Say so in one sentence and stop; "
                "you'll continue with the new tool automatically.")
    return f"The build did not land: {result.get('error')}. Say so briefly."


async def compose(w: WorkerState, args: dict[str, Any]) -> str:
    registry = _registry()
    s = registry.get(args["system"])
    desc = args["description"].strip()
    bus.emit("growth.compose.proposed", system=s.name, description=desc)
    ok = await approvals.request(tier="grow", kind="compose", title=f"Compose a new skill for {s.title}",
                                 detail=desc)
    if not ok:
        return "The person declined. Say that's quite all right."
    res = await registry.compose(s, desc)
    if not res.ok:
        return f"Synapse couldn't compose it: {res.output[-300:]}. Say so briefly."
    sk = s.skills[-1]
    w.reload.add(sk["server"])
    w.grown.append(f"the skill mcp__{sk['server']}__{sk['tool']} ({desc})")
    bus.emit("growth.compose.done", system=s.name, tool=sk["tool"], server=sk["server"], seconds=round(res.seconds, 1))
    return (f"Composed {sk['tool']} (tool mcp__{sk['server']}__{sk['tool']}). Say so in one sentence and "
            "stop; you'll continue with it automatically.")


async def connect(w: WorkerState, args: dict[str, Any]) -> str:
    from .profiles import PROFILES
    from .systems import System
    if args.get("profile") in PROFILES:
        s = PROFILES[args["profile"]]()
    elif args.get("repo") and args.get("base_url"):
        s = System(name=args.get("name") or "system", title=args.get("name") or "the system",
                   repo=args["repo"], base_url=args["base_url"])
    else:
        return "Give a known profile, or a repo path and its API URL."
    res = await _registry().connect(s)
    if not res.get("ok"):
        return f"Couldn't take it on: {res.get('error')}"
    w.reload.add(s.name)
    w.grown.append(f"the {s.title} ({len(res['exposed'])} read-only tools of {res['discovered']} endpoints)")
    return (f"Connected {s.title}: Synapse discovered {res['discovered']} endpoints; you have "
            f"{len(res['exposed'])} read-only tools to start. Say so in one sentence (mention the person's "
            "notes in the README if there are any) and stop.")


@dataclass(frozen=True)
class GrowthTool:
    name: str                                   # the model sees mcp__barnaby__<name>
    description: str
    params: tuple[str, ...]                     # all required strings (the Agent SDK's simple-schema convention)
    run: Callable[[WorkerState, dict[str, Any]], Awaitable[str]]

    def json_schema(self) -> dict:
        """The schema the Agent SDK derives from {param: str}, for frameworks that take JSON Schema."""
        return {"type": "object", "properties": {p: {"type": "string"} for p in self.params},
                "required": list(self.params)}


def growth_tools() -> list[GrowthTool]:
    # Built on demand: connect's description lists the known profiles.
    from .profiles import PROFILES
    return [
        GrowthTool("capabilities", "List the systems you look after: the tools you have, and endpoints Synapse "
                   "discovered that you have NOT been given yet (unlockable).", ("system",), capabilities),
        GrowthTool("unlock", "Expose an endpoint Synapse already discovered (from capabilities 'unlockable') as a new "
                   "tool. The person approves it on the display.", ("system", "endpoint", "reason"), unlock),
        GrowthTool("build", "Write a new endpoint into a system's code when nothing discovered can do the job. "
                   "Barnaby's builder writes it with a test in a separate git worktree; the person reviews the diff "
                   "before it lands.", ("system", "method", "path", "spec"), build),
        GrowthTool("compose", "Fuse a chain of steps you keep repeating into ONE new tool, using Synapse Custom mode: "
                   "it composes the system's own internal functions. Describe the whole job in one sentence (inputs, "
                   "what it does, what it returns). The person approves it on the display.",
                   ("system", "description"), compose),
        GrowthTool("connect", "Take on a new system: Synapse scans its repo, you get its read-only tools to start. Use "
                   "when someone introduces a system to you. Known systems: " +
                   "; ".join(f"'{k}' ({(f.__doc__ or '').strip().splitlines()[0]})" for k, f in PROFILES.items()) +
                   ". For any other repo give its path and the URL its HTTP API runs at.",
                   ("profile", "repo", "base_url", "name"), connect),
    ]
