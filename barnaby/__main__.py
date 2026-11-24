"""Barnaby command line.

  python -m barnaby serve                         API + display on http://127.0.0.1:8700
  python -m barnaby connect shop                  connect a known system (see profiles.py) and exit
  python -m barnaby ask "question" [--auto write,grow,build]
                                                  run one turn in this process, printing every event
  python -m barnaby state                         what's connected and exposed

Note: don't run `serve` under uvicorn --reload on Windows: the selector event loop can't spawn the
MCP server / Agent SDK subprocesses.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys


def _print_event(ev) -> None:
    d = ev.data
    t = ev.type
    if t == "say":
        if not d.get("final"):
            print(f"  BARNABY  {d['text']}")
    elif t == "tool.call":
        print(f"  call     {d.get('system')}.{d['tool']} {json.dumps(d.get('input'))[:160]}")
    elif t == "tool.result":
        print(f"  result   {'ok ' if d.get('ok') else 'ERR'} {d.get('preview', '')[:160]}")
    elif t.startswith("approval."):
        print(f"  {t:9}{d.get('tier', '')} {d.get('title', '')} {'approved' if d.get('approved') else ''}".rstrip())
    elif t.startswith(("growth.", "synapse.", "system.")):
        print(f"  {t:24} " + json.dumps({k: v for k, v in d.items() if k not in ('diff', 'output')}, default=str)[:180])
    elif t == "turn.result":
        print(f"  done     {d.get('ms')} ms, {d.get('turns')} model turns, ${d.get('cost')}")
    elif t == "log":
        print(f"  {d.get('level', 'log').upper():8} {d.get('text')}")


async def _with_printer(coro):
    from .events import bus
    q = bus.subscribe(replay=0)

    async def printer():
        while True:
            _print_event(await q.get())

    task = asyncio.create_task(printer())
    try:
        return await coro
    finally:
        await asyncio.sleep(0.1)
        task.cancel()


def main() -> int:
    ap = argparse.ArgumentParser(prog="barnaby")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve")
    c = sub.add_parser("connect")
    c.add_argument("profile")
    a = sub.add_parser("ask")
    a.add_argument("text")
    a.add_argument("--auto", default="", help="tiers to auto-approve: write,grow,build")
    sub.add_parser("state")
    args = ap.parse_args()

    if args.cmd == "serve":
        import uvicorn
        from .config import settings
        uvicorn.run("barnaby.server:app", host="127.0.0.1", port=settings.port, log_level="warning")
        return 0

    from .config import settings
    if getattr(args, "auto", ""):
        settings.auto_approve = {x for x in args.auto.split(",") if x}
    from .systems import registry

    if args.cmd == "state":
        for s in registry.systems.values():
            print(json.dumps({k: v for k, v in s.summary().items() if k != "endpoints"}, indent=1))
        return 0
    if args.cmd == "connect":
        from .profiles import PROFILES
        print(asyncio.run(_with_printer(registry.connect(PROFILES[args.profile]()))))
        return 0
    if args.cmd == "ask":
        from .worker import worker

        async def run():
            for s in registry.systems.values():
                await registry.ensure_running(s)
            out = await worker.ask(args.text)
            if worker.client:
                await worker.client.disconnect()
            return out

        print("\nFINAL:", asyncio.run(_with_printer(run())))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
