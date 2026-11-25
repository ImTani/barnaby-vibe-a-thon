"""End-to-end check of the real demo path (no mocks): one PASS/FAIL line per check, with timing.

  .venv/Scripts/python scripts/demo_check.py [--until N] [--no-reset]

Resets the demo world, connects Theo's repo through Synapse, then drives the story's beats as typed requests
in one conversation, auto-approving the gates (as if Martin clicked), and verifies each outcome against the
shop's own API and git history. Runs on the local Claude Code login (no API key needed).

  1 Arrival   connect: Synapse discovers 23 endpoints, 6 read-only tools exposed
  2 Ask       "which repairs are due tomorrow, short on parts?"  -> answer names the brake-pad shortfall
  3 Unlock    "order ten pairs of those pads"                     -> POST /api/purchase-orders unlocked, PO placed
  4 Build     "who's overloaded this week?"                       -> new report endpoint written, tested, merged, used
  5 Act       "move Dev's two wheel builds to Priya"              -> both jobs reassigned in the 2009 system
  6 Compose   "hand back job 4481, and make it one step"          -> Synapse Custom composes a skill; Barnaby uses it
"""
from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402

from barnaby.config import settings  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ->  {detail}" if detail else ""), flush=True)
    return ok


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--until", type=int, default=6)
    ap.add_argument("--no-reset", action="store_true")
    a = ap.parse_args()
    settings.auto_approve = {"write", "grow", "build"}

    if not a.no_reset:
        from barnaby.systems import registry as old
        for s in list(old.systems.values()):
            old.stop(s)
        state = ROOT / ".demo" / "barnaby" / "systems.json"
        if state.exists():
            state.unlink()
        subprocess.run([sys.executable, str(ROOT / "scripts" / "demo_reset.py")], check=True, capture_output=True)

    # import after the reset so the registry starts empty and "today" is the demo's Monday
    import importlib
    import barnaby.systems as systems_mod
    importlib.reload(systems_mod)
    from barnaby import profiles
    importlib.reload(profiles)
    import barnaby.worker as worker_mod
    worker_mod.registry = systems_mod.registry
    import barnaby.build as build_mod
    build_mod.registry = systems_mod.registry
    registry, worker = systems_mod.registry, worker_mod.worker
    shop_url = "http://127.0.0.1:8101"

    t0 = time.perf_counter()
    said = await worker.ask("Barnaby, this is the shop's system. Look after them for me.")   # Theo, his last week
    shop = registry.systems.get("shop")
    n = len(shop.endpoints()) if shop else 0
    check("1 Arrival: Barnaby connects the shop when introduced", shop is not None, f"{time.perf_counter() - t0:.1f}s: {said[:140]}")
    check("1 Arrival: Synapse discovers 23 endpoints", n == 23, str(n))
    check("1 Arrival: 6 read-only tools exposed", bool(shop) and len(shop.exposed) == 6)
    if a.until < 2:
        return report()

    t0 = time.perf_counter()
    said = await worker.ask("Which repairs are due tomorrow, and are we short on parts for any of them?")
    check("2 Ask: answer names the brake-pad shortfall", "pad" in said.lower() and ("anika" in said.lower() or "brake" in said.lower()),
          f"{time.perf_counter() - t0:.1f}s: {said[:140]}")
    if a.until < 3:
        return report()

    t0 = time.perf_counter()
    said = await worker.ask("Order ten pairs of those brake pads from the usual supplier.")
    pos = httpx.get(f"{shop_url}/api/purchase-orders").json()
    shop = registry.get("shop")
    check("3 Unlock: POST /api/purchase-orders unlocked", "POST /api/purchase-orders" in shop.exposed)
    check("3 Unlock: purchase order placed in the shop", any(p["status"] == "ordered" and "Brake pads" in p["part"] and p["quantity"] == 10 for p in pos),
          f"{time.perf_counter() - t0:.1f}s: {said[:120]}")
    if a.until < 4:
        return report()

    t0 = time.perf_counter()
    said = await worker.ask("Who's overloaded this week?")
    shop = registry.get("shop")
    log = subprocess.run(["git", "log", "-1", "--format=%an: %s"], cwd=shop.repo, capture_output=True, text=True).stdout.strip()
    new = [k for k in shop.exposed if k.startswith("GET /api/reports/")]
    check("4 Build: Barnaby's commit landed in Theo's repo", log.startswith("Barnaby:"), log)
    check("4 Build: new report endpoint exposed as a tool", bool(new), ", ".join(new))
    check("4 Build: answer says Dev is overloaded", "dev" in said.lower(), f"{time.perf_counter() - t0:.1f}s: {said[:160]}")
    if new:
        path = new[0].split(" ", 1)[1]
        path = path.replace("{week}", "today").replace("{week_of}", "today").replace("{day}", "today").replace("{date}", "today")
        try:
            body = httpx.get(shop_url + path, timeout=5).json()
            check("4 Build: report reads exactly 31 h for Dev (README definition)", "31" in str(body) and "31.5" not in str(body), str(body)[:160])
        except Exception as e:  # noqa: BLE001
            check("4 Build: report callable", False, str(e))
    if a.until < 5:
        return report()

    t0 = time.perf_counter()
    said = await worker.ask("Move Dev's two wheel builds to Priya, please.")
    jobs = {j["job_id"]: j for j in httpx.get(f"{shop_url}/api/jobs/open").json()}
    check("5 Act: both wheel builds now with Priya", jobs[4471]["mechanic"] == "Priya" and jobs[4472]["mechanic"] == "Priya",
          f"{time.perf_counter() - t0:.1f}s: {said[:140]}")
    if a.until < 6:
        return report()

    from barnaby import synapse
    if not synapse.has_key():
        check("6 Compose: skipped (no SYNAPSE_API_KEY in .env)", True)
        return report()
    from barnaby.events import bus
    mark = bus.history()[-1].id if bus.history() else 0
    t0 = time.perf_counter()
    said = await worker.ask("Tom's bike is done, job 4481. Hand it back: text him it's ready and mark it ready. "
                            "And make handing back a bike a single step, would you? I do it a dozen times a day.")
    shop = registry.get("shop")
    job = httpx.get(f"{shop_url}/api/jobs/4481").json().get("job", {})
    sent = httpx.get(f"{shop_url}/api/notifications/recent").json()
    used = [e.data.get("tool") for e in bus.history() if e.id > mark and e.type == "tool.call"
            and str(e.data.get("system", "")).startswith("shop-k")]
    check("6 Compose: Synapse Custom composed a skill", bool(shop.skills), ", ".join(k["tool"] for k in shop.skills))
    check("6 Compose: Barnaby used the new skill", bool(used), ", ".join(used))
    check("6 Compose: job 4481 marked ready", job.get("status") == "ready", str(job.get("status")))
    check("6 Compose: Tom was texted", "Tom" in str(sent)[:2000] or "4481" in str(sent)[:2000],
          f"{time.perf_counter() - t0:.1f}s: {said[:140]}")
    return report()


def report() -> int:
    passed = sum(ok for _, ok, _ in RESULTS)
    print(f"\n{passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
