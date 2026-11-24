"""Screenshot a page with the installed Chrome (headless, throwaway profile in the system temp dir).

  .venv/Scripts/python scripts/dev/screenshot.py URL OUT.png [--size 1440,1000] [--serve "CMD" --cwd DIR --env K=V ...]

--serve starts a server first (e.g. the shop app), waits until URL answers, screenshots, then stops it.
Used to eyeball UI changes during unattended work. Nothing is installed; no global state is touched.
"""
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--size", default="1440,1000")
    ap.add_argument("--serve")
    ap.add_argument("--cwd")
    ap.add_argument("--env", action="append", default=[])
    ap.add_argument("--budget", type=int, default=3000, help="virtual time budget in ms")
    a = ap.parse_args()

    server = None
    if a.serve:
        env = {**os.environ, **dict(kv.split("=", 1) for kv in a.env)}
        cmd = shlex.split(a.serve, posix=False)
        if Path(cmd[0]).exists():          # a relative interpreter path means relative to *our* cwd, not --cwd
            cmd[0] = str(Path(cmd[0]).resolve())
        server = subprocess.Popen(cmd, cwd=a.cwd, env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                if httpx.get(a.url, timeout=1).status_code < 500:
                    break
            except httpx.HTTPError:
                time.sleep(0.3)
        else:
            server.kill()
            print("server did not come up", file=sys.stderr)
            return 1
    profile = tempfile.mkdtemp(prefix="shot-profile-")
    try:
        out = str(Path(a.out).resolve())
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                        "--force-prefers-reduced-motion", f"--user-data-dir={profile}",
                        f"--virtual-time-budget={a.budget}", f"--window-size={a.size}", f"--screenshot={out}", a.url],
                       capture_output=True, timeout=120)
        print(out if Path(out).exists() else "screenshot failed")
    finally:
        if server:
            server.terminate()
        shutil.rmtree(profile, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
