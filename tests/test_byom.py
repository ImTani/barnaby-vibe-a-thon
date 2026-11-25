"""The bring-your-own-model worker, end to end against a real stdio MCP server (tests/fixtures/mcp_fixture.py,
run with runtime/mcp-servers' python), with Pydantic AI's FunctionModel scripted in place of a provider.

  .venv/Scripts/python -m pytest -q tests/test_byom.py
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import shutil
from pathlib import Path

import pytest
from pydantic_ai import ModelMessage, ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from barnaby.config import MCP_RUNTIME_PY, settings
from barnaby.events import bus
from barnaby.policy import approvals
from barnaby.synapse import BuildResult
from barnaby.systems import System, registry
from barnaby.toolkit import continuation
from barnaby.worker_byom import ByomWorker

FIXTURE = Path(__file__).parent / "fixtures" / "mcp_fixture.py"
pytestmark = pytest.mark.skipif(not MCP_RUNTIME_PY.exists(), reason="needs runtime/mcp-servers/.venv")

READ, ORDER, DROP = "GET /api/things/{thing_id}", "POST /api/orders", "DELETE /api/things/{thing_id}"
GROWTH = {f"mcp__barnaby__{t}" for t in ("capabilities", "unlock", "build", "compose", "connect")}


class Script:
    """A model that follows a script, one step per request: a list of (tool, args) calls, or the reply text.
    It keeps what it was shown, so a test can read the tool results and the tools on offer."""

    def __init__(self, *steps):
        self.steps = list(steps)
        self.seen: list[list[ModelMessage]] = []
        self.tools: set[str] = set()
        self.model = FunctionModel(self._respond)

    def _respond(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        self.seen.append(list(messages))
        self.tools = {t.name for t in info.function_tools}
        step = self.steps.pop(0)
        if isinstance(step, str):
            return ModelResponse(parts=[TextPart(step)])
        return ModelResponse(parts=[ToolCallPart(name, args) for name, args in step])

    def results(self, tool: str) -> list[ToolReturnPart]:
        """What the model was told each time it called `tool`, in order."""
        return [p for m in self.seen[-1] if isinstance(m, ModelRequest) for p in m.parts
                if isinstance(p, ToolReturnPart) and p.tool_name == tool]

    def prompts(self, request: int) -> list[str]:
        return [p.content for m in self.seen[request] if isinstance(m, ModelRequest) for p in m.parts
                if isinstance(p, UserPromptPart)]


@pytest.fixture
def shop(tmp_path, monkeypatch) -> System:
    """A connected system whose generated server is the fixture, with one composed skill (the fixture again)."""
    repo = tmp_path / "repo"
    (repo / ".synapse").mkdir(parents=True)
    (repo / "README.md").write_text("Things and orders.", encoding="utf-8")
    eps = [("get", "/api/things/{thing_id}", "read_thing", "One thing."), ("post", "/api/orders", "place_order",
           "Order an item."), ("delete", "/api/things/{thing_id}", "drop_thing", "Delete a thing.")]
    (repo / ".synapse" / "surface_cache.json").write_text(json.dumps({"files": {"routes.py": {"endpoints": [
        {"method": m, "path": p, "suggested_tool_name": t, "handler_qualname": t, "description": d}
        for m, p, t, d in eps]}}}), encoding="utf-8")
    s = System(name="fixture", title="the fixture shop", repo=str(repo), base_url="http://fixture.test",
               exposed=[READ], skills=[{"server": "fixture-k1", "tool": "hand_back", "path": str(FIXTURE),
                                        "description": "Hand a job back. Texts the owner."}])
    s.server_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE, s.server_path)
    monkeypatch.setitem(registry.systems, s.name, s)
    monkeypatch.setattr(settings, "auto_approve", set())
    return s


@pytest.fixture
async def make_worker():
    made: list[ByomWorker] = []

    def make(script: Script) -> ByomWorker:
        made.append(ByomWorker(model=script.model))
        return made[-1]

    yield make
    for w in made:
        await w.close()             # stop the server processes before the test's event loop goes


@contextlib.contextmanager
def heard():
    """Every event emitted inside the block."""
    q = bus.subscribe(replay=0)
    events: list = []
    try:
        yield events
    finally:
        bus.unsubscribe(q)
        while not q.empty():
            events.append(q.get_nowait())


@contextlib.asynccontextmanager
async def person(approve: bool):
    """Someone at the display answering every confirmation card; yields the cards they were shown."""
    q = bus.subscribe(replay=0)
    cards: list[dict] = []

    async def answer():
        while True:
            ev = await q.get()
            if ev.type == "approval.requested":
                cards.append(ev.data)
                approvals.resolve(ev.data["id"], approve)

    task = asyncio.create_task(answer())
    try:
        yield cards
    finally:
        task.cancel()
        bus.unsubscribe(q)


def of(events, type_: str) -> list[dict]:
    return [e.data for e in events if e.type == type_]


async def test_a_read_runs_without_a_card_and_is_reported(shop, make_worker):
    script = Script([("mcp__fixture__read_thing", {"thing_id": 7})], "Thing seven is a widget.")
    w = make_worker(script)
    with heard() as events:
        said = await w.ask("What's thing seven?")

    assert said == "Thing seven is a widget."
    assert {"mcp__fixture__read_thing", "mcp__fixture__place_order", "mcp__fixture-k1__hand_back"} | GROWTH <= script.tools
    assert events[0].type == "turn.start" and events[-1].type == "turn.end"
    assert not of(events, "approval.requested")
    [call] = of(events, "tool.call")
    assert (call["system"], call["tool"], call["input"]) == ("fixture", "read_thing", {"thing_id": 7})
    [result] = of(events, "tool.result")
    assert result["ok"] and result["id"] == call["id"]
    assert "widget 7" in result["preview"] and "http://fixture.test" in result["preview"]   # the config's env arrived
    assert [s["text"] for s in of(events, "say") if s["final"]] == [said]
    assert [r["ok"] for r in of(events, "turn.result")] == [True]
    assert w.calls == [("fixture", "read_thing")] and w.turn == 1 and not w.busy


async def test_the_conversation_and_the_servers_carry_across_turns(shop, make_worker):
    script = Script([("mcp__fixture__read_thing", {"thing_id": 1})], "Thing one is a widget.",
                    [("mcp__fixture__read_thing", {"thing_id": 1})], "Still a widget.")
    w = make_worker(script)
    assert await w.ask("What's thing one?") == "Thing one is a widget."
    assert await w.ask("And now?") == "Still a widget."
    assert script.prompts(2) == ["What's thing one?", "And now?"]
    first, second = (p.content["pid"] for p in script.results("mcp__fixture__read_thing"))
    assert first == second                          # one server process for the session, not one per turn
    assert w.turn == 2 and w.calls == [("fixture", "read_thing")] * 2


async def test_writes_and_skills_wait_for_the_person_one_card_at_a_time(shop, make_worker):
    shop.exposed.append(ORDER)
    script = Script([("mcp__fixture__place_order", {"item": "brake pads", "quantity": 10}),
                     ("mcp__fixture-k1__hand_back", {"job_id": 4481})], "Ordered, and handed back.")
    w = make_worker(script)
    with heard() as events:
        async with person(approve=True) as cards:
            said = await w.ask("Order ten brake pads and hand back job 4481.")

    assert said == "Ordered, and handed back."
    assert [c["tier"] for c in cards] == ["write", "write"]
    assert cards[0]["detail"].startswith(ORDER) and cards[1]["title"] == "Hand a job back"
    order = [e.type for e in events if e.type in ("approval.requested", "approval.resolved", "tool.result")]
    assert order == ["approval.requested", "approval.resolved", "tool.result"] * 2   # one card at a time, results live
    [placed], [handed] = script.results("mcp__fixture__place_order"), script.results("mcp__fixture-k1__hand_back")
    assert placed.outcome == "success" and "brake pads" in json.dumps(placed.content)
    assert handed.outcome == "success" and "4481" in json.dumps(handed.content)
    assert all(r["ok"] for r in of(events, "tool.result"))


async def test_declined_or_forbidden_calls_come_back_as_refusals_the_model_reads(shop, make_worker):
    shop.exposed += [ORDER, DROP]
    script = Script([("mcp__fixture__place_order", {"item": "pads", "quantity": 1}),
                     ("mcp__fixture__drop_thing", {"thing_id": 7}),
                     ("mcp__fixture__hand_back", {"job_id": 1})], "Very good, I'll leave it.")
    w = make_worker(script)
    with heard() as events:
        async with person(approve=False) as cards:
            said = await w.ask("Order pads, delete thing seven, hand back job one.")

    assert said == "Very good, I'll leave it."
    assert len(cards) == 1                                                    # only the write asked anyone
    told = {t: script.results(f"mcp__fixture__{t}")[0] for t in ("place_order", "drop_thing", "hand_back")}
    assert all(p.outcome == "failed" for p in told.values())
    assert told["place_order"].content == "The person declined. Don't retry."
    assert told["drop_thing"].content == f"{DROP} is never allowed."
    assert told["hand_back"].content == "That tool isn't exposed."
    assert [r["ok"] for r in of(events, "tool.result")] == [False, False, False]


async def test_growth_tools_then_restart_and_carry_on_with_the_history(shop, make_worker, monkeypatch):
    async def expose(s, add, discover=False):       # stands in for Synapse rebuilding the server with more endpoints
        s.exposed = list(dict.fromkeys(s.exposed + add))
        return BuildResult(True, s.server_path, 0.1, len(s.exposed), "")

    monkeypatch.setattr(registry, "expose", expose)
    monkeypatch.setattr(settings, "auto_approve", {"grow", "write"})
    script = Script(
        [("mcp__barnaby__capabilities", {"system": "fixture"}),
         ("mcp__barnaby__connect", {"profile": "", "repo": "", "base_url": "", "name": ""}),
         ("mcp__barnaby__unlock", {"system": "nowhere", "endpoint": ORDER, "reason": "r"})],
        [("mcp__fixture__read_thing", {"thing_id": 1}),
         ("mcp__barnaby__unlock", {"system": "fixture", "endpoint": ORDER, "reason": "to order pads"})],
        "I've unlocked ordering.",
        [("mcp__fixture__place_order", {"item": "pads", "quantity": 10}), ("mcp__fixture__read_thing", {"thing_id": 1})],
        "Ordered ten pads.")
    w = make_worker(script)
    with heard() as events:
        said = await w.ask("Order ten pads.")

    assert said == "Ordered ten pads."
    caps = json.loads(script.results("mcp__barnaby__capabilities")[0].content)
    assert [e["key"] for e in caps[0]["unlockable"]] == [ORDER, DROP] and caps[0]["notes"] == "Things and orders."
    assert script.results("mcp__barnaby__connect")[0].content == "Give a known profile, or a repo path and its API URL."
    bad, good = script.results("mcp__barnaby__unlock")
    assert bad.outcome == "failed" and "No system called 'nowhere'" in bad.content      # errors reach the model
    assert good.content.startswith(f"Unlocked {ORDER} (tool mcp__fixture__place_order).")

    # the server was restarted and the turn carried on by itself, with the conversation so far
    assert of(events, "system.reloaded") == [{"system": "fixture"}]
    assert script.prompts(3) == ["Order ten pads.", continuation([f"{ORDER} as tool mcp__fixture__place_order"])]
    assert script.results("mcp__fixture__place_order")[0].outcome == "success"
    before, after = (p.content["pid"] for p in script.results("mcp__fixture__read_thing"))
    assert before != after
    assert [s["text"] for s in of(events, "say") if s["final"]] == ["I've unlocked ordering.", "Ordered ten pads."]
    assert len(of(events, "turn.result")) == 2 and len(of(events, "turn.start")) == len(of(events, "turn.end")) == 1
    assert [e.type for e in events if e.type.startswith("growth.unlock")] == ["growth.unlock.proposed", "growth.unlock.done"]


async def test_without_a_model_the_turn_fails_politely(monkeypatch):
    monkeypatch.setattr(settings, "byom_model", "")
    w = ByomWorker()
    with heard() as events:
        said = await w.ask("Hello?")
    assert said == "I'm terribly sorry, something went wrong on my side."
    assert any("BARNABY_BYOM_MODEL" in log["text"] for log in of(events, "log"))
    assert events[-1].type == "turn.end" and not w.busy


def test_the_backend_setting_picks_the_worker(monkeypatch):
    from barnaby import worker as claude
    from barnaby import worker_byom, workers
    monkeypatch.setattr(settings, "worker_backend", "claude-code")
    assert workers.get_worker() is claude.worker
    monkeypatch.setattr(settings, "worker_backend", "byom")
    assert workers.get_worker() is worker_byom.worker
