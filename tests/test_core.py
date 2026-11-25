"""Fast unit tests for Barnaby's core (no Synapse, no model, no network).

  .venv/Scripts/python -m pytest -q
The end-to-end path (real Synapse, real agent, real shop) is scripts/demo_check.py.
"""
from __future__ import annotations

import asyncio
import json

from barnaby import synapse
from barnaby.config import settings
from barnaby.policy import Approvals, tier_for
from barnaby.synapse import Endpoint, fixup, surface
from barnaby.worker import Worker

# A trimmed piece of real Synapse 0.1.9 local-auto output (two tools).
SYNAPSE_OUT = '''from mcp.server.fastmcp import FastMCP
mcp = FastMCP("spokes-and-sprockets")


@mcp.tool(name="job_detail", description="One job.")
def job_detail(job_id: Any = None) -> dict:
    url = f"{os.environ["ENDPOINT_BASE_URL"]}/api/jobs/{job_id}"
    headers = {}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


@mcp.tool(name="create_purchase_order", description="Order a part.")
def create_purchase_order(part_id: Any = None, quantity: Any = None, supplier: Any = None) -> dict:
    url = f"{os.environ["ENDPOINT_BASE_URL"]}/api/purchase-orders"
    headers = {}
    payload = {"part_id": part_id, "quantity": quantity, "supplier": supplier}
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()
'''

ENDPOINTS = [
    Endpoint("GET", "/api/jobs/{job_id}", "job_detail", "One job.", None, "routes_jobs.py", 40, ["job_id"]),
    Endpoint("POST", "/api/purchase-orders", "create_purchase_order", "Order a part.",
             {"part_id": 1, "quantity": 10, "supplier": None}, "routes_parts.py", 30),
]


# ── fix-up pass ──
def test_fixup_restores_types_and_required_params():
    out = fixup(SYNAPSE_OUT, ENDPOINTS)
    assert "def job_detail(job_id: str | int) -> dict:" in out                 # path param: required
    assert "def create_purchase_order(part_id: float, quantity: float, supplier: Any = None) -> dict:" in out
    assert "Any = None" not in out.split("def create_purchase_order")[0]          # nothing else left untyped


def test_fixup_returns_error_bodies_instead_of_raising():
    out = fixup(SYNAPSE_OUT, ENDPOINTS)
    assert "raise_for_status" not in out
    assert out.count('"status_code": resp.status_code, "error": resp.json()') == 2
    assert out.startswith("# Fixed up by Barnaby")


def test_fixup_leaves_unknown_tools_alone():
    src = "def mystery(x: Any = None) -> dict:\n    return {}\n"
    assert fixup(src, ENDPOINTS).endswith(src)


# ── the discovery atlas ──
def test_surface_reads_synapse_cache(tmp_path):
    (tmp_path / ".synapse").mkdir()
    (tmp_path / ".synapse" / "surface_cache.json").write_text(json.dumps({"files": {
        "routes_jobs.py": {"endpoints": [
            {"method": "get", "path": "/api/jobs/{job_id}", "suggested_tool_name": "job_detail",
             "handler_qualname": "job_detail", "description": " One job. ", "start_line": 40},
            {"method": "delete", "path": "/api/jobs/{job_id}", "handler_qualname": "delete_job"},
        ]}}}), encoding="utf-8")
    eps = surface(tmp_path)
    assert [e.key for e in eps] == ["GET /api/jobs/{job_id}", "DELETE /api/jobs/{job_id}"]
    assert eps[0].read_only and not eps[1].read_only
    assert eps[0].path_params == ["job_id"] and eps[0].description == "One job."
    assert eps[1].tool == "delete_job"                                        # falls back to the handler name


def test_surface_without_cache_is_empty(tmp_path):
    assert surface(tmp_path) == []


def test_compose_needs_a_key(monkeypatch, tmp_path):
    monkeypatch.delenv("SYNAPSE_API_KEY", raising=False)
    res = asyncio.run(synapse.build_custom("shop", tmp_path, "hand back a bike"))
    assert not res.ok and "SYNAPSE_API_KEY" in res.output


# ── approval tiers ──
def test_tiers():
    assert tier_for("GET", "GET /api/jobs/open", []) == "read"
    assert tier_for("POST", "POST /api/purchase-orders", []) == "write"
    assert tier_for("PATCH", "PATCH /api/jobs/1", []) == "write"
    assert tier_for("DELETE", "DELETE /api/jobs/{job_id}", []) == "denied"
    assert tier_for("POST", "POST /api/refunds", ["POST /api/refunds"]) == "denied"


def test_auto_approval_only_for_configured_tiers(monkeypatch):
    monkeypatch.setattr(settings, "auto_approve", {"write"})
    ap = Approvals()

    async def run():
        assert await ap.request(tier="write", kind="call", title="Order pads") is True
        pending = asyncio.create_task(ap.request(tier="build", kind="build", title="Add a report", timeout=5))
        await asyncio.sleep(0.05)
        assert not pending.done()                                            # build waits for a person
        pid = next(iter(ap.pending))
        assert ap.resolve(pid, True, via="voice") is False                   # code changes: never by voice alone
        ap.resolve(pid, False)
        assert await pending is False
    asyncio.run(run())


# ── habits (Compose candidates) ──
def test_habits_find_a_repeated_chain():
    w = Worker()
    chain = ["job_detail", "customer_detail", "notify", "update_status"]
    w.calls = [("shop", t) for t in ["open_jobs"] + chain + ["parts_low"] + chain + chain]
    hs = w.habits("shop")
    assert hs[0] == {"chain": " -> ".join(chain), "times": 3}
    assert all(h["chain"] != " -> ".join(chain[:3]) for h in hs)             # sub-chains aren't repeated as habits


def test_habits_ignore_other_systems_and_one_offs():
    w = Worker()
    w.calls = [("quorum", "a"), ("quorum", "b"), ("quorum", "c")] * 3 + [("shop", "x"), ("shop", "y"), ("shop", "z")]
    assert w.habits("shop") == []
    assert w.habits("quorum")[0]["times"] >= 2


def test_habit_nudge_offers_each_chain_once(monkeypatch):
    from barnaby import toolkit

    class Reg:
        systems = {"shop": object()}
    monkeypatch.setattr(toolkit, "_registry", lambda: Reg())
    w = Worker()
    chain = ["job_detail", "customer_detail", "notify", "update_status"]
    w.calls = [("shop", t) for t in chain * 2]
    assert w.habit_nudge() is None                                           # twice isn't a habit yet
    w.calls += [("shop", t) for t in chain]
    nudge = w.habit_nudge()
    assert nudge and "job_detail -> customer_detail -> notify -> update_status" in nudge and "3 times" in nudge
    assert w.habit_nudge() is None                                           # offered once per session


# ── the household's words: cards, the build explanation, and what Barnaby may say ──
SHOP = [   # real descriptions from Theo's shop (Synapse's surface cache)
    Endpoint("POST", "/api/purchase-orders", "create_purchase_order",
             "Order more of a part from a supplier. supplier defaults to the part's usual one.",
             {"part_id": 0, "quantity": 0, "supplier": None}, "routes_parts.py", 30),
    Endpoint("POST", "/api/jobs/{job_id}/assign", "assign",
             "Give a job to a different mechanic, by first name (e.g. Priya).", {"mechanic": ""}, "routes_jobs.py", 80,
             ["job_id"]),
    Endpoint("GET", "/api/jobs/open", "open_jobs", "All repair jobs that haven't been collected yet.", None,
             "routes_jobs.py", 10),
]


class Cards:
    """Stands in for the approvals desk: keeps every card it's shown, and answers each with `answer`."""

    def __init__(self, answer: bool = False):
        self.shown: list[dict] = []
        self.answer = answer

    async def request(self, **card) -> bool:
        self.shown.append(card)
        return self.answer


def shop_world(monkeypatch, exposed=("POST /api/purchase-orders", "GET /api/jobs/open"), skills=()):
    from types import SimpleNamespace

    from barnaby import toolkit
    s = SimpleNamespace(name="shop", title="the shop's back office", exposed=list(exposed), denied=[],
                        skills=list(skills), endpoints=lambda: SHOP)
    reg = SimpleNamespace(systems={"shop": s}, get=lambda name: s)
    cards = Cards()
    monkeypatch.setattr(toolkit, "_registry", lambda: reg)
    monkeypatch.setattr(toolkit, "approvals", cards)
    monkeypatch.setattr(toolkit, "SEEN", [])                  # nothing looked up yet
    return s, cards


def test_plain_titles_from_the_endpoint_and_its_arguments():
    from barnaby.toolkit import call_title, plain_action, plain_args
    order, assign, _ = (plain_action(e.description) for e in SHOP)
    assert order == "Order more of a part from a supplier"                     # first clause, no parameter notes
    assert assign == "Give a job to a different mechanic"                      # no asides, no "by first name"
    assert plain_args({"part_id": 1, "quantity": 10, "supplier": "Madison"}) == "10 × part 1 with Madison"
    assert plain_args({"part_id": 1, "quantity": 10.0}) == "10 × part 1"
    assert call_title(assign, {"job_id": 4471, "mechanic": "Priya"}) == f"{assign}: job 4471 to Priya"
    assert plain_args({"job_id": 4481, "status": "ready"}) == "job 4481 to ready"
    assert plain_args({"quantity": 3, "item": "pads"}) == "3 × pads" and call_title("Tidy up", {}) == "Tidy up"


def test_write_cards_lead_in_plain_words_with_the_key_tucked_away(monkeypatch):
    from barnaby.toolkit import DECLINED, gate
    _, cards = shop_world(monkeypatch)
    args = {"part_id": 1, "quantity": 10, "supplier": "Madison"}
    assert asyncio.run(gate("mcp__shop__open_jobs", {})) is None and not cards.shown      # reads ask nobody
    assert asyncio.run(gate("mcp__shop__create_purchase_order", args)) == DECLINED
    [card] = cards.shown
    assert card["title"] == "Order more of a part from a supplier: 10 × part 1 with Madison"
    assert card["technical"].startswith("POST /api/purchase-orders") and '"supplier": "Madison"' in card["technical"]
    assert card["facts"] is None                                                       # no price on record: no cost


def test_write_cards_name_what_barnaby_just_looked_up_and_what_it_costs(monkeypatch):
    from barnaby import toolkit
    from barnaby.toolkit import WorkerState, gate
    _, cards = shop_world(monkeypatch)
    w = WorkerState()
    parts = [{"id": 1, "sku": "BP-SH-RES", "name": "Brake pads (Shimano resin, pair)", "stock": 1, "unit_cost": 6.5},
             {"id": 2, "sku": "CH-KMC-X11", "name": "Chain KMC X11", "stock": 4, "unit_cost": 21.0}]
    w.note_call(1, "c1", "mcp__shop__parts_low_api_parts_low_get", {})
    w.note_result(1, "c1", True, [{"type": "text", "text": json.dumps(parts)}])        # as an MCP result comes back
    asyncio.run(gate("mcp__shop__create_purchase_order", {"part_id": 1, "quantity": 10, "supplier": "Madison"}))
    [card] = cards.shown
    assert card["title"] == "Order more of a part from a supplier: 10 × Brake pads (Shimano resin, pair) with Madison"
    assert card["facts"] == [["Cost", "6.50 each, 65.00 in all"]]
    assert toolkit.known_as("job", 1) is None              # an id in a call about parts names a part, never a job
    w.note_call(1, "c2", "mcp__shop__parts_api_parts_get", {})
    w.note_result(1, "c2", False, "boom")                  # a failed call names nothing
    assert toolkit.known_as("part", "2") == {"name": "Chain KMC X11", "price": 21.0}  # ids as numbers or strings


def test_write_cards_carry_the_question_barnaby_just_asked_and_no_older_words(monkeypatch):
    from barnaby.events import bus
    from barnaby.toolkit import gate
    _, cards = shop_world(monkeypatch)
    args = {"part_id": 1, "quantity": 10}
    bus.emit("say", turn=1, text="Ten pairs from Madison, shall I?", final=False)      # the reply that makes the call
    bus.emit("tool.call", turn=1, id="c1", system="shop", tool="create_purchase_order", input=args)
    asyncio.run(gate("mcp__shop__create_purchase_order", args))
    bus.emit("tool.result", turn=1, id="c1", ok=True, preview="{}")                  # a later call, no new words
    asyncio.run(gate("mcp__shop__create_purchase_order", args))
    bus.emit("say", turn=1, text="Ordered.", final=True)                             # a finished reply's words
    asyncio.run(gate("mcp__shop__create_purchase_order", args))
    assert [c["detail"] for c in cards.shown] == ["Ten pairs from Madison, shall I?", "", ""]


def test_unlock_card_asks_in_the_households_words(monkeypatch):
    from barnaby.toolkit import ability, unlock
    _, cards = shop_world(monkeypatch, exposed=["GET /api/jobs/open"])
    said = asyncio.run(unlock(Worker(), {"system": "shop", "endpoint": "POST /api/purchase-orders",
                                         "reason": "So I can order Anika's brake pads.",
                                         "ability": "Let Barnaby order parts from your suppliers."}))
    assert "declined" in said
    [card] = cards.shown
    assert card["title"] == "Let Barnaby order parts from your suppliers"
    assert card["detail"] == "So I can order Anika's brake pads."
    assert card["technical"].startswith("POST /api/purchase-orders (tool create_purchase_order)")
    assert ability("", SHOP[1].description) == "give a job to a different mechanic"     # no ability: the gist
    assert ability("QR codes for bikes") == "QR codes for bikes"                       # acronyms keep their case


def test_compose_card_names_the_skill_plainly_and_its_calls_use_that_name(monkeypatch):
    from barnaby.toolkit import compose, gate
    skill = {"server": "shop-k1", "tool": "hand_back_finished_bike", "path": "x.py",
             "name": "Hand back a bike in one step",
             "description": "Hand back a finished bike: given a job_id, text the customer and mark the job ready."}
    _, cards = shop_world(monkeypatch, skills=[skill])
    asyncio.run(compose(Worker(), {"system": "shop", "description": skill["description"],
                                   "name": "hand back a bike in one step"}))
    asyncio.run(gate("mcp__shop-k1__hand_back_finished_bike", {"job_id": 4481}))
    made, used = cards.shown
    assert made["title"] == "Hand back a bike in one step" and "Synapse" not in made["title"] + made["detail"]
    assert skill["description"] in made["technical"]
    assert used["title"] == "Hand back a bike in one step: job 4481" and used["technical"].startswith(skill["tool"])


def test_growth_tool_schemas_keep_the_plain_names_optional():
    from barnaby.toolkit import growth_tools
    tools = {t.name: t.json_schema() for t in growth_tools()}
    assert "ability" in tools["unlock"]["properties"] and "ability" not in tools["unlock"]["required"]
    assert "name" in tools["compose"]["properties"] and "name" not in tools["compose"]["required"]
    assert tools["unlock"]["required"] == ["system", "endpoint", "reason"]


def test_approval_events_carry_the_technical_detail_separately(monkeypatch):
    from barnaby.events import bus
    monkeypatch.setattr(settings, "auto_approve", {"write"})
    ap, q = Approvals(), bus.subscribe(replay=0)

    async def run():
        assert await ap.request(tier="write", kind="call", title="Order more of a part: 10 × part 1",
                                technical="POST /api/purchase-orders") is True
        pending = asyncio.create_task(ap.request(tier="grow", kind="unlock", title="Let Barnaby order parts",
                                                 detail="For Anika's pads.", technical="POST /api/purchase-orders"))
        await asyncio.sleep(0.05)
        [card] = ap.summary()
        assert (card["title"], card["detail"], card["technical"]) == ("Let Barnaby order parts", "For Anika's pads.",
                                                                     "POST /api/purchase-orders")
        ap.resolve(card["id"], False)
        await pending
    try:
        asyncio.run(run())
    finally:
        bus.unsubscribe(q)
    events = {}
    while not q.empty():
        ev = q.get_nowait()
        events.setdefault(ev.type, ev.data)
    assert events["approval.auto"]["technical"] == "POST /api/purchase-orders"
    assert events["approval.requested"]["title"] == "Let Barnaby order parts"


def test_build_explanation_is_plain_and_complete():
    from barnaby.build import explain, plain_parts
    from barnaby.toolkit import jargon
    reply = ("Added GET /api/reports/workload/{day}: services.mechanic_workload plus four tests in tests/test_api.py.\n"
             "**NAME:** a weekly workload report\n"
             "DOES: It shows how many hours of work each mechanic has this week against what they can take on.\n"
             "READS: the jobs and the mechanics' hours.\n"
             "CHANGES: nothing\n")
    parts, commit = plain_parts(reply)
    assert parts["name"] == "a weekly workload report" and parts["reads"] == "the jobs and the mechanics' hours"
    assert commit.startswith("Added GET /api/reports/workload/{day}") and "NAME" not in commit
    plain = explain(title="the shop's back office", method="GET", path="/api/reports/workload/{day}", parts=parts,
                    before=19, after=23, who="Theo")
    assert plain["title"] == "Add a weekly workload report to the shop's back office"
    summary = plain["summary"]
    assert summary.startswith("It shows how many hours") and "changes nothing" in summary
    assert "Theo's 19 checks still pass, and so do the 4 new ones." in summary and "can be undone" in summary
    said = plain["said"]
    assert said.startswith("I've made a weekly workload report") and "undone" in said
    assert said.count(". ") + 1 <= 2                                          # one or two spoken sentences
    assert not jargon(plain["title"] + summary + said)
    # the builder said nothing plain: still an honest, plain card
    bare = explain(title="the shop's back office", method="POST", path="/api/jobs/merge", parts={}, before=None,
                   after=21)
    assert "All 21 checks pass." in bare["summary"] and "changes some of its records" in bare["summary"]
    assert not jargon(bare["title"] + bare["summary"] + bare["said"])


def test_jargon_is_heard_as_whole_words_in_any_form():
    from barnaby.toolkit import jargon
    assert jargon("Synapse found 23 endpoints; I have six read-only tools and merged the diff via the API.") == [
        "Synapse", "endpoints", "tools", "merged", "diff", "API"]
    assert jargon("Priya's new toolroll, and a quick merging of jobs on the servers") == ["merging", "servers"]
    assert jargon("I can't order parts myself yet, but Theo built the system a way to. Shall I take that on?") == []
    # unless the person speaks that way first (Theo might): their words are theirs to hear back, in any form
    assert jargon("I've merged it and added two endpoints.", theirs="Add an endpoint, then merge it.") == []
    assert jargon("Merged, and the API is up.", theirs="merging is fine") == ["API"]
