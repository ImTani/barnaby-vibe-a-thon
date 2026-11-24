"""Voice end-to-end test, no human needed: a WAV (the question, then 30 s of silence so Chrome's looping fake mic asks only once) plays into headless Chrome's fake microphone, goes over WebRTC to
the Pipecat bot, is transcribed (sherpa by default), reaches Barnaby, and Barnaby's answer is spoken by Kokoro.

  .venv/Scripts/python scripts/smoke/voice_e2e.py [--wav .demo/voice-samples/owner-question.wav] [--seconds 60]

Starts Barnaby's server (:8700) and the voice bot (:7860) if they aren't running, opens the display in
hands-free mode with the WAV as the mic, then checks the event log for: a turn whose text came from speech,
and something Barnaby said in reply. Prints PASS/FAIL lines.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
EVENTS = ROOT / ".demo" / "barnaby" / "events.jsonl"


def up(url: str) -> bool:
    try:
        return httpx.get(url, timeout=1).status_code < 500
    except httpx.HTTPError:
        return False


def wait(url: str, secs: float = 60) -> bool:
    end = time.time() + secs
    while time.time() < end:
        if up(url):
            return True
        time.sleep(0.5)
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=str(ROOT / ".demo" / "voice-samples" / "owner-question.wav"))
    ap.add_argument("--seconds", type=int, default=60)
    a = ap.parse_args()
    procs = []
    logs = ROOT / ".demo" / "barnaby" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    if not up("http://127.0.0.1:8700/api/state"):
        procs.append(subprocess.Popen([str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "barnaby", "serve"], cwd=ROOT,
                                      stdout=open(logs / "core.log", "a"), stderr=subprocess.STDOUT))
    if not up("http://127.0.0.1:7860/"):
        procs.append(subprocess.Popen([str(ROOT / "runtime" / "voice" / ".venv" / "Scripts" / "python.exe"), "voice/bot.py",
                                       "-t", "webrtc", "--port", "7860"], cwd=ROOT,
                                      stdout=open(logs / "voice.log", "a"), stderr=subprocess.STDOUT))
    ok_core, ok_voice = wait("http://127.0.0.1:8700/api/state"), wait("http://127.0.0.1:7860/", 90)
    print(f"[{'PASS' if ok_core else 'FAIL'}] Barnaby server up")
    print(f"[{'PASS' if ok_voice else 'FAIL'}] voice bot up")
    if not (ok_core and ok_voice):
        for p in procs:
            p.terminate()
        return 1

    t0 = time.time()
    profile = tempfile.mkdtemp(prefix="voice-e2e-")
    chrome = subprocess.Popen([CHROME, "--headless=new", "--no-first-run", f"--user-data-dir={profile}",
                               "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                               f"--use-file-for-fake-audio-capture={a.wav}", "--autoplay-policy=no-user-gesture-required",
                               "http://127.0.0.1:8700/?handsfree=1"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    heard, said = None, []
    try:
        end = time.time() + a.seconds
        while time.time() < end and not (heard and said):
            time.sleep(2)
            for line in EVENTS.read_text(encoding="utf-8").splitlines():
                ev = json.loads(line)
                if ev["ts"] < t0:
                    continue
                if ev["type"] == "turn.start" and not heard:
                    heard = ev["data"]["text"]
                if ev["type"] == "say" and not ev["data"].get("final") and heard:
                    said.append(ev["data"]["text"])
    finally:
        chrome.terminate()
        time.sleep(1)
        shutil.rmtree(profile, ignore_errors=True)
        for p in procs:
            p.terminate()
    print(f"[{'PASS' if heard else 'FAIL'}] speech reached Barnaby as a turn  ->  {heard!r} ({time.time() - t0:.0f}s)")
    print(f"[{'PASS' if said else 'FAIL'}] Barnaby answered (spoken by the bot)  ->  {(said or [''])[0][:160]!r}")
    return 0 if heard and said else 1


if __name__ == "__main__":
    sys.exit(main())
