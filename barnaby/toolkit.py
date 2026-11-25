"""What every worker shares, whichever model does the thinking: the system prompt, the tier gate in front of
every system and skill tool call, Barnaby's own growth tools, and the turn bookkeeping (what grew, habits).

Both workers name tools mcp__<server>__<tool> (the Claude Agent SDK's MCP convention; the Pydantic AI worker
prefixes its MCP tools the same way), so the prompt and every text below read the same whichever worker runs.
"""
from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
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

Whom you speak to: the household, not a developer. These rules are firm.
- Speak their language. Never say endpoint, API, tool, MCP, server, deploy, merge, diff, worktree or Synapse to
  the person unless they use the word first. Those words are for your calls, never for what you say aloud.
- Describe abilities as what the system can do, and name who built it if the notes say: "I can look up jobs,
  parts and customers", "Theo built the system a way to order from suppliers", never "six read-only tools".
- Ask before you take on a new ability, in plain words. Explain before you change anything: what it will do,
  and to whom or what.

How you work:
- When someone introduces a system to you ("this is the shop's system"), call mcp__barnaby__connect.
- Use the tools to find out; never guess or invent data. Prefer the fewest calls that answer the question.
- If none of your current tools can do what's asked, call mcp__barnaby__capabilities. If an endpoint there that
  you haven't been given would do it, ask and unlock in the same reply: first say, in one or two short sentences,
  that you can't do it yourself yet but the system can, and ask to take it on (for example "I can't order parts
  myself yet, but Theo built the system a way to. Shall I take that on?"); then call mcp__barnaby__unlock with a
  plain `ability` (what it will let you do, in the household's words, e.g. "order parts from your suppliers")
  and a plain one-line reason. Don't wait for an answer in words: the card on the display is their answer.
  When unlock succeeds, say in a few words that you can do it now, and stop; you will continue automatically.
- If no endpoint exists for it but the system's data could answer it, call mcp__barnaby__build with a precise
  spec (method, full path, what it returns, how it's computed). Base every definition in the spec on the
  system's own notes (the "notes" in capabilities: the people who built it explain how it works there).
  First say in one short sentence that the system can't tell you that yet and you'll make it a way to. The
  person is told what you made before it's added. When it succeeds, say in a few words that it's in place, and
  stop; you will continue automatically.
- Totals, counts, rankings or comparisons across many records are the system's job, not yours: never add
  them up by hand from raw listings. Look for a report in your tools and in capabilities; if none exists,
  build one under /api/reports/... so the answer is exact and the household keeps it for next time.
- To change data (book, order, reassign, text a customer, change a status), say in one short sentence what
  you're about to do and ask, e.g. "Ten pairs from Madison, shall I?", then call the tool in the same reply: a
  confirmation card puts your question to the person, and their yes there is the answer. Never stop to wait for
  a spoken yes instead of calling it. If they decline, accept it gracefully.
- If capabilities shows a habit (the same chain of calls repeated), or the person asks for something to become one
  step, offer to make it a single skill; when they agree (or asked), call mcp__barnaby__compose with a one-sentence
  description of the whole job and a short plain name for it (e.g. "Hand back a bike in one step"). Prefer an
  existing skill over the long chain whenever one fits.
- When something can't be done, say so plainly and briefly.
"""

# Words that belong in Barnaby's calls, never in what he says to the household (the prompt's rule, and what
# scripts/demo_check.py listens for across a whole run).
JARGON = ("endpoint", "API", "tool", "MCP", "server", "deploy", "merge", "diff", "worktree", "Synapse")
JARGON_RE = re.compile(r"\b(?:" + "|".join([*JARGON, *(j[:-1] + "ing" for j in JARGON if j.endswith("e"))]) +
                       r")(?:s|d|ed|ing)?\b", re.IGNORECASE)        # "tools", "merged", "merging", "APIs" too


def _root(word: str) -> str:
    """The JARGON entry a heard word comes from: "merging" -> "merge", "APIs" -> "API"."""
    return next(j for j in JARGON if word.lower().startswith(j.lower().removesuffix("e")))


def jargon(text: str, theirs: str = "") -> list[str]:
    """The machine's words in something Barnaby said ("tools", "merged", "Synapse"), in order. Words the person
    used first (anywhere in `theirs`, what they've said so far) are theirs to hear back, as the prompt allows."""
    used = {_root(w) for w in JARGON_RE.findall(theirs)}
    return [m.group(0) for m in JARGON_RE.finditer(text) if _root(m.group(0)) not in used]

MAX_CONTINUATIONS = 2       # after a growth step the turn carries on by itself, at most this many times


def continuation(grown: list[str]) -> str:
    """The follow-up prompt after a growth step, once the reloaded tools are attached."""
    return ("[Barnaby system] Your tools were reloaded and now include: " + "; ".join(grown) +
            ". Carry on with the person's request using them, in the household's words.")


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


# ── cards in the household's words ──
def plain_action(description: str) -> str:
    """The plain gist of an endpoint's description: its first clause, without asides or parameter notes.
    "Give a job to a different mechanic, by first name (e.g. Priya)." -> "Give a job to a different mechanic"."""
    text = re.sub(r"\s*\([^)]*\)", "", description or "").strip()
    first = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return re.split(r"\s*[,:;]\s*", first, maxsplit=1)[0].strip().rstrip(".!?")


def _plain_value(v: Any) -> str:
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    v = str(v)
    return v if len(v) <= 48 else v[:45].rstrip() + "…"


_QUANTITY = ("quantity", "qty", "count")
_WITH = ("supplier", "vendor")
_TO = ("mechanic", "assignee", "to", "status")
_QUOTED = ("message", "text", "note", "body")
_NAMES = ("name", "title", "full_name", "label")
_PRICES = ("unit_cost", "unit_price", "price", "cost")

# What the person has just seen: the results of this session's recent calls, newest last, as (tool, parsed result).
# A card names what an id points at from them ("Brake pads (Shimano resin, pair)", not "part 1"): Barnaby has just
# looked it up, so it's the thing the person is deciding about. Nothing seen, and the card says "part 1" as before.
SEEN: list[tuple[str, Any]] = []


def note_seen(tool: str, content: Any) -> None:
    SEEN.append((tool, content))
    del SEEN[:-12]


def _records(x: Any, depth: int = 0):
    """Every dict in a call's result, however it came back (MCP text blocks holding JSON, wrappers, lists)."""
    if depth > 6:
        return
    if isinstance(x, str):
        s = x.strip()
        if s[:1] in ("{", "["):
            try:
                yield from _records(json.loads(s), depth + 1)
            except ValueError:
                pass
    elif isinstance(x, dict):
        yield x
        for v in x.values():
            yield from _records(v, depth + 1)
    elif isinstance(x, list):
        for v in x:
            yield from _records(v, depth + 1)


def known_as(word: str, ident: Any) -> dict[str, Any] | None:
    """The newest record seen for `<word> <ident>`, as {"name": ..., "price": ...}: a record carrying
    "<word>_id": ident and "<word>" (or "<word>_name"), or one with "id": ident from a call about <word>s."""
    def same(a: Any) -> bool:                 # 1 == "1": ids come back as numbers or strings
        return a is not None and not isinstance(a, bool) and str(a) == str(ident)

    for tool, content in reversed(SEEN):
        about = word.replace(" ", "_") in tool.lower()
        for r in _records(content):
            name = None
            if same(r.get(f"{word}_id")):
                name = r.get(word) or r.get(f"{word}_name")
            elif about and same(r.get("id")):
                name = next((r[k] for k in _NAMES if isinstance(r.get(k), str) and r[k].strip()), None)
            if isinstance(name, str) and name.strip():
                price = next((r[k] for k in _PRICES if isinstance(r.get(k), (int, float)) and r[k] > 0), None)
                return {"name": name.strip(), "price": price}
    return None


def _money(v: float) -> str:
    return f"{v:,.2f}"


def plain_cost(args: dict[str, Any]) -> str:
    """What an order comes to, when the thing ordered has a price on record: "6.50 each, 65.00 in all"."""
    qty = next((args[k] for k in _QUANTITY if isinstance(args.get(k), (int, float))), None)
    for k, v in args.items():
        if k.endswith("_id") and qty:
            rec = known_as(k.removesuffix("_id").replace("_", " "), v)
            if rec and rec["price"]:
                return f"{_money(rec['price'])} each, {_money(rec['price'] * qty)} in all"
    return ""


def plain_args(args: dict[str, Any]) -> str:
    """A call's key arguments as a person would say them:
    {"part_id": 1, "quantity": 10, "supplier": "Madison"} -> "10 × part 1 with Madison", or, once Barnaby has
    looked the part up, "10 × Brake pads (Shimano resin, pair) with Madison";
    {"job_id": 4471, "mechanic": "Priya"} -> "job 4471 to Priya"."""
    args = {k: v for k, v in (args or {}).items() if v not in (None, "") and not isinstance(v, (dict, list))}
    qty = next((args.pop(k) for k in _QUANTITY if k in args), None)
    nouns = [k for k in args if k not in (*_WITH, *_TO, *_QUOTED)]
    counted = next((k for k in nouns if k.endswith("_id")), nouns[0] if nouns else None)   # what the quantity counts
    out: list[str] = [] if qty is None or counted else [f"quantity {_plain_value(qty)}"]
    for k, v in args.items():
        val = _plain_value(v)
        if k in _WITH:
            out.append(f"with {val}")
        elif k in _TO:
            out.append(f"to {val}")
        elif k in _QUOTED:
            out.append(f"“{val}”")
        else:                                 # "part 1", "estimate hours 2"; words speak for themselves: "Full service"
            word = k.removesuffix("_id").replace("_", " ")
            item = val if isinstance(v, str) and not k.endswith("_id") else f"{word} {val}"
            rec = known_as(word, v) if k.endswith("_id") else None
            if rec:                           # ...and a record seen names it: "Brake pads (Shimano resin, pair)"
                item = _plain_value(rec["name"]) if word not in ("job", "invoice", "order") else f"{item} ({_plain_value(rec['name'])})"
            out.append(f"{_plain_value(qty)} × {item}" if k == counted and qty is not None else item)
    said = ""
    for item in out:                          # "with …" and "to …" follow what they qualify; the rest take commas
        said += (" " if item.startswith(("with ", "to ")) else ", ") + item if said else item
    return said


def call_title(action: str, args: dict[str, Any]) -> str:
    """A write card's title: what will happen, then to what. "Order more of a part from a supplier: 10 × part 1"."""
    what = plain_args(args)
    return f"{action}: {what}" if what else action


def _technical(name: str, tool_input: dict) -> str:
    return f"{name}\n{json.dumps(tool_input, indent=1)}"


def asked() -> str:
    """What Barnaby has just said to the person about this call ("Ten pairs from Madison, shall I?"), for its card:
    the words of the reply that makes the call, or "" if that reply said nothing. Only the reply's own tool calls may
    stand between: a result, another card or a new turn means those words were about something else."""
    for ev in reversed(bus.history()):
        if ev.type == "say" and not ev.data.get("final"):
            return ev.data.get("text", "")
        if ev.type != "tool.call":
            return ""
    return ""


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
        ok = await approvals.request(tier="write", kind="call", title=call_title(skill_name(k), tool_input),
                                     detail=asked(),
                                     technical=_technical(f"{k['tool']} (a skill composed for {s.title})", tool_input))
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
    cost = plain_cost(tool_input or {})
    ok = await approvals.request(tier="write", kind="call", title=call_title(plain_action(ep.description) or ep.key,
                                                                             tool_input),
                                 detail=asked(), technical=_technical(f"{ep.key} (tool {ep.tool})", tool_input),
                                 facts=[["Cost", cost]] if cost else None)
    return None if ok else DECLINED


# ── turn bookkeeping ──
class WorkerState:
    """What both workers keep between and during turns: one turn at a time, what grew this round (so the
    servers can be restarted and the turn continued), and the session's call history (for habits)."""

    def __init__(self):
        self.lock = asyncio.Lock()
        self.reload: set[str] = set()         # servers whose MCP process must be restarted after this round
        self.grown: list[str] = []            # what was unlocked/built/composed this round (for the follow-up prompt;
                                              # a connect reloads without one: his reply already said what he took on)
        self.calls: list[tuple[str, str]] = []  # (system, tool) of every system call this session, for habits
        self.offered: set[tuple[str, str]] = set()  # (system, chain) habits Barnaby has already offered to compose
        self.tools: dict[str, str] = {}       # call id -> tool name, until its result comes back
        self.turn = 0
        self.busy = False

    def note_call(self, turn: int, call_id: str, name: str, tool_input: Any) -> None:
        parts = name.split("__")
        bus.emit("tool.call", turn=turn, id=call_id, system=parts[1] if len(parts) == 3 else "",
                 tool=parts[-1], input=tool_input)
        self.tools[call_id] = parts[-1]
        if len(parts) == 3 and parts[1] in _registry().systems:
            self.calls = (self.calls + [(parts[1], parts[2])])[-300:]

    def note_result(self, turn: int, call_id: str, ok: bool, content: Any) -> None:
        tool = self.tools.pop(call_id, "")
        if ok:
            note_seen(tool, content)              # so the next card can name what it's about
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


    def habit_nudge(self, min_times: int = 3) -> str | None:
        """After a turn: if a chain of calls has now repeated `min_times` times on a system, the follow-up prompt that
        has Barnaby offer to fuse it into one skill (Compose). Each chain is offered once per session; once composed,
        the skill replaces the chain, so it stops repeating."""
        for name in list(_registry().systems):
            for h in self.habits(name, min_times):
                if (name, h["chain"]) in self.offered:
                    continue
                self.offered.add((name, h["chain"]))
                return (f"[Barnaby system] Habit noticed on {name}: this session you've run {h['chain']} "
                        f"{h['times']} times. In one short spoken sentence, in the household's words (the job, not "
                        "the calls), offer to make that a single step (say how many times you've done it). Don't "
                        "call compose unless the person agrees.")
        return None


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
            "skills": [{"tool": f"mcp__{k['server']}__{k['tool']}", "name": skill_name(k), "does": k["description"]}
                       for k in s.skills],
            "habits": w.habits(n),
        })
    return json.dumps(out, indent=1)


def ability(text: str, description: str = "") -> str:
    """What an unlock lets Barnaby do, to finish "Let Barnaby …": the model's plain words, else the endpoint's gist.
    "Let Barnaby order parts from your suppliers." -> "order parts from your suppliers"."""
    t = re.sub(r"^\s*(?:let barnaby|to)\s+", "", (text or "").strip(), flags=re.IGNORECASE).rstrip(" .!?")
    t = t or plain_action(description)
    return t[:1].lower() + t[1:] if t[1:2].islower() else t


async def unlock(w: WorkerState, args: dict[str, Any]) -> str:
    registry = _registry()
    s = registry.get(args["system"])
    eps = {e.key: e for e in s.endpoints()}
    ep = eps.get(args["endpoint"])
    if not ep:
        return f"No discovered endpoint '{args['endpoint']}' in {s.name}. Check capabilities."
    if ep.key in s.denied:
        return f"{ep.key} is on the deny-list. It can't be unlocked."
    able = ability(args.get("ability", ""), ep.description) or ep.key
    bus.emit("growth.unlock.proposed", system=s.name, endpoint=ep.key, tool=ep.tool, reason=args.get("reason", ""),
             ability=able)
    ok = await approvals.request(tier="grow", kind="unlock", title=f"Let Barnaby {able}",
                                 detail=args.get("reason", "").strip(),
                                 technical=f"{ep.key} (tool {ep.tool}) in {s.title}\n{ep.description}")
    if not ok:
        return "The person declined. Tell them that's quite all right, and you'll leave it."
    res = await registry.expose(s, [ep.key])
    if not res.ok:
        return "Synapse failed to rebuild the server. Apologise in plain words and say you'll look into it."
    w.reload.add(s.name)
    w.grown.append(f"{ep.key} as tool mcp__{s.name}__{ep.tool}")
    bus.emit("growth.unlock.done", system=s.name, endpoint=ep.key, tool=ep.tool, seconds=round(res.seconds, 2))
    return (f"Unlocked {ep.key} (tool mcp__{s.name}__{ep.tool}): you can now {able}. Say in a few plain words that "
            "you can do it now, and stop; you'll continue with it automatically in a moment.")


async def build(w: WorkerState, args: dict[str, Any]) -> str:
    from .build import build_endpoint
    s = _registry().get(args["system"])
    result = await build_endpoint(s, args["method"].upper(), args["path"], args["spec"])
    if result.get("ok"):
        w.reload.add(s.name)
        w.grown.append(", ".join(result.get("tools", [])))
        return (f"Added {result['name']}, with the person's approval ({', '.join(result.get('tools', []))}). They "
                "have already heard what it does. Say in a few plain words that it's in place, and stop; you'll "
                "continue with it automatically.")
    return f"The build did not land: {result.get('error')}. Say so briefly, in plain words."


def skill_name(k: dict) -> str:
    """A composed skill as the household knows it ("Hand back a bike in one step")."""
    return k.get("name") or plain_action(k.get("description", "")) or k.get("tool", "a new skill")


async def compose(w: WorkerState, args: dict[str, Any]) -> str:
    registry = _registry()
    s = registry.get(args["system"])
    desc = args["description"].strip()
    name = (args.get("name") or "").strip().rstrip(".") or plain_action(desc) or "One step for a job done often"
    name = name[:1].upper() + name[1:]
    bus.emit("growth.compose.proposed", system=s.name, description=desc, name=name)
    ok = await approvals.request(tier="grow", kind="compose", title=name,
                                 detail=f"One step instead of several, made from things {s.title} already does.",
                                 technical=f"Synapse Custom mode composes {s.title}'s own functions into one tool:\n"
                                           f"{desc}")
    if not ok:
        return "The person declined. Say that's quite all right."
    res = await registry.compose(s, desc, name=name)
    if not res.ok:
        return f"Synapse couldn't compose it: {res.output[-300:]}. Say so briefly, in plain words."
    sk = s.skills[-1]
    w.reload.add(sk["server"])
    w.grown.append(f"the skill mcp__{sk['server']}__{sk['tool']} ({desc})")
    bus.emit("growth.compose.done", system=s.name, tool=sk["tool"], server=sk["server"], name=name,
             seconds=round(res.seconds, 1))
    return (f"Composed {sk['tool']} (tool mcp__{sk['server']}__{sk['tool']}): {name}. Say in a few plain words that "
            "it's one step now, and stop; you'll continue with it automatically.")


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
    w.reload.add(s.name)        # its tools attach for what comes next; nothing grew mid-request, so no carry-on
    return (f"Connected {s.title}. Its code can do {res['discovered']} things; to start you may use the "
            f"{len(res['exposed'])} that only look things up, and you'll ask before taking on any of the rest. In "
            "one or two plain sentences, tell the person you've taken it on and what you can look into for them now "
            "(mention the notes its builder left, if there are any), and stop.")


@dataclass(frozen=True)
class GrowthTool:
    name: str                                   # the model sees mcp__barnaby__<name>
    description: str
    params: tuple[str, ...]                     # required strings
    run: Callable[[WorkerState, dict[str, Any]], Awaitable[str]]
    optional: tuple[str, ...] = ()              # optional strings
    hints: dict[str, str] = field(default_factory=dict)     # what a parameter is for, where its name doesn't say

    def json_schema(self) -> dict:
        """Every parameter a string, `params` required. Both workers hand this to their framework as it is."""
        props = {p: {"type": "string"} | ({"description": self.hints[p]} if p in self.hints else {})
                 for p in self.params + self.optional}
        return {"type": "object", "properties": props, "required": list(self.params)}


def growth_tools() -> list[GrowthTool]:
    # Built on demand: connect's description lists the known profiles.
    from .profiles import PROFILES
    return [
        GrowthTool("capabilities", "List the systems you look after: the tools you have, and endpoints Synapse "
                   "discovered that you have NOT been given yet (unlockable).", ("system",), capabilities),
        GrowthTool("unlock", "Expose an endpoint Synapse already discovered (from capabilities 'unlockable') as a new "
                   "tool. The person approves it on the display; ask them in plain words in the same reply.",
                   ("system", "endpoint", "reason"), unlock, optional=("ability",), hints={
                       "ability": "What it will let you do, in the household's words, to finish 'Let Barnaby ...', "
                                  "e.g. 'order parts from your suppliers'.",
                       "reason": "One plain line for the person: why you need it now."}),
        GrowthTool("build", "Write a new endpoint into a system's code when nothing discovered can do the job. "
                   "Barnaby's builder writes it with a test in a separate git worktree; the person is told in plain "
                   "words what it does (the change itself is there if they want it) before it lands.",
                   ("system", "method", "path", "spec"), build),
        GrowthTool("compose", "Fuse a chain of steps you keep repeating into ONE new tool, using Synapse Custom mode: "
                   "it composes the system's own internal functions. Describe the whole job in one sentence (inputs, "
                   "what it does, what it returns). The person approves it on the display.",
                   ("system", "description"), compose, optional=("name",), hints={
                       "name": "A short plain name for the person, e.g. 'Hand back a bike in one step'."}),
        GrowthTool("connect", "Take on a new system: Synapse scans its repo, you get its read-only tools to start. Use "
                   "when someone introduces a system to you. Known systems: " +
                   "; ".join(f"'{k}' ({(f.__doc__ or '').strip().splitlines()[0]})" for k, f in PROFILES.items()) +
                   ". For any other repo give its path and the URL its HTTP API runs at.",
                   ("profile", "repo", "base_url", "name"), connect),
    ]
