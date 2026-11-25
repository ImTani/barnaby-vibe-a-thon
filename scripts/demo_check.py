"""End-to-end check of the real demo path (no mocks): one PASS/FAIL line per check, with timing.

  .venv/Scripts/python scripts/demo_check.py [--until N] [--no-reset]

Resets the demo world, connects Theo's repo through Synapse, then drives the story's beats as typed requests
in one conversation, in the film's order, auto-approving the gates (as if Martin clicked), and verifies each outcome
against the shop's own API and git history. Runs on the local Claude Code login (no API key needed).

  1 Arrival   connect: Synapse discovers 23 endpoints, 6 read-only tools exposed
  2 Ask       "which repairs are due tomorrow, short on parts?"  -> answer names the brake-pad shortfall
  3 Unlock    "order ten pairs of those pads"                     -> POST /api/purchase-orders unlocked, PO placed
  4 Compose   scene 5: Sofia's, Kwame's and Jana's bikes handed back (texted, marked ready), then Tom's 4481
              "and make it one step"                              -> Synapse Custom composes a skill; Barnaby uses it
  5 Build     "who's overloaded this week?"                       -> new report endpoint written, tested, merged, used;
                                                                     after the hand-backs it reads Dev's 31 h
  6 Act       "move Dev's two wheel builds to Priya"              -> both jobs reassigned in the 2009 system
  Speech      everything Barnaby said, across the run             -> none of the machine's words (toolkit.JARGON)
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
HEARD = None                    # the run's events (a bus subscription), for what Barnaby said aloud


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
    global HEARD
    from barnaby.events import bus
    HEARD = bus.subscribe(replay=0)

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

    # scene 5, Monday afternoon: Martin hands back finished bikes. Barnaby texts each customer and marks it ready (the
    # keys for texting and marking ready are asked for on the first), three times the long way, then Tom's in one step.
    t0 = time.perf_counter()
    for ask in ["Barnaby, Sofia's bike's done, job 4475. Text her it's ready to collect and mark it ready.",
                "Kwame's bike's done too, job 4490. Text him it's ready to collect and mark it ready.",
                "And Jana's, job 4488. Text her it's ready to collect and mark it ready."]:
        await worker.ask(ask)
    from barnaby import synapse
    from barnaby.events import bus
    tom = "Tom's bike is done, job 4481. Hand it back: text him it's ready and mark it ready."
    if synapse.has_key():
        mark = bus.history()[-1].id if bus.history() else 0
        said = await worker.ask(tom + " And make handing back a bike a single step, would you? I do it a dozen times a day.")
        shop = registry.get("shop")
        used = [e.data.get("tool") for e in bus.history() if e.id > mark and e.type == "tool.call"
                and str(e.data.get("system", "")).startswith("shop-k")]
        check("4 Compose: Synapse Custom composed a skill", bool(shop.skills), ", ".join(k["tool"] for k in shop.skills))
        check("4 Compose: Barnaby used the new skill", bool(used), ", ".join(used))
    else:
        said = await worker.ask(tom)
        check("4 Compose: skipped (no SYNAPSE_API_KEY in .env)", True)
    back = {i: httpx.get(f"{shop_url}/api/jobs/{i}").json().get("job", {}).get("status") for i in (4475, 4490, 4488, 4481)}
    day = (ROOT / ".demo" / "today").read_text().strip()     # texts sent this run (the seeded ones are all older)
    texted = {n["customer"].split()[0] for n in httpx.get(f"{shop_url}/api/notifications/recent").json() if n["sent_at"] >= day}
    check("4 Compose: all four bikes handed back are marked ready", set(back.values()) == {"ready"}, str(back))
    check("4 Compose: Sofia, Kwame, Jana and Tom were texted", {"Sofia", "Kwame", "Jana", "Tom"} <= texted,
          f"{time.perf_counter() - t0:.1f}s: {said[:140]}")
    if a.until < 5:
        return report()

    t0 = time.perf_counter()
    said = await worker.ask("Who's overloaded this week?")
    shop = registry.get("shop")
    log = subprocess.run(["git", "log", "-1", "--format=%an: %s"], cwd=shop.repo, capture_output=True, text=True).stdout.strip()
    new = [k for k in shop.exposed if k.startswith("GET /api/reports/")]
    check("5 Build: Barnaby's commit landed in Theo's repo", log.startswith("Barnaby:"), log)
    check("5 Build: new report endpoint exposed as a tool", bool(new), ", ".join(new))
    check("5 Build: answer says Dev is overloaded", "dev" in said.lower(), f"{time.perf_counter() - t0:.1f}s: {said[:160]}")
    if new:
        path = new[0].split(" ", 1)[1]
        path = path.replace("{week}", "today").replace("{week_of}", "today").replace("{day}", "today").replace("{date}", "today")
        try:
            body = httpx.get(shop_url + path, timeout=5).json()
            check("5 Build: report reads exactly 31 h for Dev after the hand-backs (README definition)", "31" in str(body) and "31.5" not in str(body), str(body)[:160])
        except Exception as e:  # noqa: BLE001
            check("5 Build: report callable", False, str(e))
    if a.until < 6:
        return report()

    t0 = time.perf_counter()
    said = await worker.ask("Move Dev's two wheel builds to Priya, please.")
    jobs = {j["job_id"]: j for j in httpx.get(f"{shop_url}/api/jobs/open").json()}
    check("6 Act: both wheel builds now with Priya", jobs[4471]["mechanic"] == "Priya" and jobs[4472]["mechanic"] == "Priya",
          f"{time.perf_counter() - t0:.1f}s: {said[:140]}")
    return report()


def speech_check() -> None:
    """Everything Barnaby said this run (each `say`, spoken or final) is in the household's words, unless the
    person used the word first."""
    from barnaby.toolkit import jargon
    said: list[str] = []
    theirs, slips = "", []
    while HEARD is not None and not HEARD.empty():
        ev = HEARD.get_nowait()
        if ev.type == "turn.start" and not ev.data.get("text", "").startswith("[Barnaby system]"):
            theirs += " " + ev.data["text"]
        elif ev.type == "say" and ev.data.get("text") and ev.data["text"] not in said:
            said.append(t := ev.data["text"])
            if words := jargon(t, theirs):
                slips.append(f"{', '.join(words)} in \"{t[:100]}\"")
    check("Speech: no endpoint/API/tool/MCP/server/deploy/merge/diff/worktree/Synapse in anything Barnaby said",
          bool(said) and not slips, "; ".join(slips) if slips else f"{len(said)} lines, all plain")


def report() -> int:
    speech_check()
    passed = sum(ok for _, ok, _ in RESULTS)
    print(f"\n{passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


async def run() -> int:
    try:
        return await main()
    finally:                                   # close the agent's subprocesses cleanly (else Windows prints noise)
        import barnaby.worker as worker_mod
        await worker_mod.worker.close()


if __name__ == "__main__":
    code = asyncio.run(run())
    sys.exit(code)
