"""Turn the last real run in .demo/barnaby/events.jsonl into the display's mock-mode fixture.

  .venv/Scripts/python scripts/dev/export_mock_fixture.py [--out ui/fixtures/demo-run.json]

Takes every event from the last `system.connecting` onwards (one demo_check run), trims bulky payloads,
and adds a `state_before` snapshot (the system's endpoints with only the starter set exposed) so the
display can replay the run with no backend. The replay is a real run, just re-timed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "ui" / "fixtures" / "demo-run.json"))
    a = ap.parse_args()
    lines = (ROOT / ".demo" / "barnaby" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(x) for x in lines if x.strip()]
    start = max(i for i, e in enumerate(events) if e["type"] == "system.connecting")
    run = []
    for e in events[start:]:
        d = e["data"]
        if "preview" in d:
            d["preview"] = d["preview"][:900]
        d.pop("output", None)
        if e["type"] == "approval.auto":                 # demo_check auto-approves; the replay shows real cards
            run.append({**e, "type": "approval.requested"})
            run.append({**e, "type": "approval.resolved", "data": {"id": d["id"], "approved": True}})
            continue
        run.append(e)

    from barnaby.systems import registry
    systems = []
    connected = next(e["data"] for e in run if e["type"] == "system.connected")
    for s in registry.systems.values():
        summ = s.summary()
        grown = {k for e in run if e["type"] == "growth.build.done" for k in e["data"].get("endpoints", [])}
        summ["endpoints"] = [ep for ep in summ["endpoints"] if ep["key"] not in grown]
        for ep in summ["endpoints"]:
            ep["exposed"] = ep["key"] in connected["exposed"]
        summ["exposed"] = list(connected["exposed"])
        systems.append(summ)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"state_before": {"systems": systems}, "events": run}, indent=1), encoding="utf-8")
    print(f"{out}: {len(run)} events, {sum(e['type'] == 'turn.start' for e in run)} turns")
    return 0


if __name__ == "__main__":
    sys.exit(main())
