"""Reset the demo world: a fresh copy of Theo's 2009 repo with its history and a freshly seeded database.

  .venv/Scripts/python scripts/demo_reset.py [--today YYYY-MM-DD]

- Copies systems/spokes-and-sprockets (the pristine source, tracked in our repo) to .demo/spokes-and-sprockets
  (gitignored). Barnaby only ever touches the copy, so his code changes and worktrees never land in our repo.
- Gives the copy its own git repo with Theo's backdated history (2009 -> last week).
- Stops a shop left running by an earlier session and clears Barnaby's registry + generated servers
  (--keep-barnaby to skip), so Barnaby meets the shop for the first time again.
- Seeds the shop database. "Today" defaults to the Monday of the current week (the story's Monday),
  and is written to .demo/today so every process uses the same date.
"""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "systems" / "spokes-and-sprockets"
DEMO = ROOT / ".demo"
DST = DEMO / "spokes-and-sprockets"
LEGACY_PY = ROOT / "runtime" / "legacy" / ".venv" / "Scripts" / "python.exe"
IGNORE = shutil.ignore_patterns("shop.db", "__pycache__", ".pytest_cache", ".synapse", "synapse_auto_server*.py",
                                "*_server.py", ".env.example", ".git")

THEO = {"GIT_AUTHOR_NAME": "Theo Hartley", "GIT_AUTHOR_EMAIL": "theo@spokesandsprockets.co.uk",
        "GIT_COMMITTER_NAME": "Theo Hartley", "GIT_COMMITTER_EMAIL": "theo@spokesandsprockets.co.uk"}
HISTORY = [  # (date, message, files to add) - the final commit adds everything
    ("2009-03-14T16:20:00", "first version of the shop system!! (bye access database)", ["db.py", "app.py"]),
    ("2009-07-02T21:05:00", "jobs + customers pages, made it look proper", ["routes_jobs.py", "routes_customers.py", "templates", "static"]),
    ("2011-03-19T14:40:00", "parts + ordering from suppliers. reports page (coming soon)", ["routes_parts.py", "routes_reports.py"]),
    ("2014-10-08T19:12:00", "invoices, mechanics, moved logic into services.py", ["routes_money.py", "routes_mechanics.py", "services.py"]),
    ("2019-02-23T11:30:00", "tests!! finally. seed script for the training laptop", ["tests", "seed.py", "pytest.ini", "requirements.txt"]),
]
HANDOVER = "README: notes for whoever looks after it next. bye x"


def _rm_readonly(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def git(*args: str, env: dict | None = None) -> None:
    subprocess.run(["git", *args], cwd=DST, check=True, capture_output=True,
                   env={**os.environ, **(env or {})})


def forget_barnaby(ports=(8101,)) -> None:
    """Barnaby starts from scratch too: stop the shop if an earlier session left it running (by the registry's pid,
    then by whoever still listens on its port), and drop his registry and generated servers. Run this while
    `barnaby serve` is stopped (it keeps the registry in memory)."""
    import json
    import psutil
    state = DEMO / "barnaby"
    pids = set()
    reg = state / "systems.json"
    if reg.exists():
        pids |= {s["pid"] for s in json.loads(reg.read_text(encoding="utf-8")) if s.get("pid")}
    try:
        pids |= {c.pid for c in psutil.net_connections("tcp") if c.laddr and c.laddr.port in ports
                 and c.status == psutil.CONN_LISTEN and c.pid}
    except psutil.AccessDenied:
        pass
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            for child in proc.children(recursive=True):
                child.kill()
            proc.kill()
            proc.wait(5)
        except psutil.Error:
            pass
    reg.unlink(missing_ok=True)
    if (state / "servers").exists():
        shutil.rmtree(state / "servers", onerror=_rm_readonly)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", help="the demo's 'today' (default: Monday of this week)")
    ap.add_argument("--keep-barnaby", action="store_true", help="keep Barnaby's registry and generated servers")
    a = ap.parse_args()
    today = a.today or (date.today() - timedelta(days=date.today().weekday())).isoformat()

    if not a.keep_barnaby:
        forget_barnaby()
    if DST.exists():
        shutil.rmtree(DST, onerror=_rm_readonly)
    for wt in DEMO.glob("worktree-*"):
        shutil.rmtree(wt, onerror=_rm_readonly)
    shutil.copytree(SRC, DST, ignore=IGNORE)
    (DEMO / "today").write_text(today)

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Theo Hartley")
    git("config", "user.email", "theo@spokesandsprockets.co.uk")
    (DST / ".gitignore").write_text("shop.db\n__pycache__/\n.pytest_cache/\n.synapse/\n.env\n")
    for when, msg, files in HISTORY:
        git("add", ".gitignore", *files)
        git("commit", "-q", "-m", msg, env={**THEO, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when})
    last_week = (date.fromisoformat(today) - timedelta(days=4)).isoformat() + "T18:45:00"
    git("add", "-A")
    git("commit", "-q", "-m", HANDOVER, env={**THEO, "GIT_AUTHOR_DATE": last_week, "GIT_COMMITTER_DATE": last_week})

    py = str(LEGACY_PY) if LEGACY_PY.exists() else sys.executable
    out = subprocess.run([py, "seed.py"], cwd=DST, check=True, capture_output=True, text=True,
                         env={**os.environ, "SPOKES_TODAY": today, "SPOKES_DB": str(DST / "shop.db")})
    log = subprocess.run(["git", "log", "--format=%ad  %s", "--date=short"], cwd=DST, capture_output=True, text=True).stdout
    print(f"demo world reset: {DST}\n  today = {today}\n  seed  = {out.stdout.strip()}\n  history:\n" +
          "".join(f"    {line}\n" for line in log.strip().splitlines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
