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
