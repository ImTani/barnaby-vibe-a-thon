"""Phase 0 smoke test: is Tani's sherpa-onnx streaming STT server reachable, and what does it send back?

Protocol (from sherpa-onnx online-websocket-server source): binary frames of float32 little-endian mono
PCM at 16 kHz, then the text frame "Done"; the server replies with JSON per decode step and "Done!" at the end.
Sends one second of silence, so it's harmless.

Run from the repo root:  .venv/Scripts/python scripts/smoke/smoke_sherpa.py [ws://host:port]
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time

import numpy as np
import websockets

URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SHERPA_WS_URL", "ws://192.168.1.68:6007")


async def main() -> int:
    t0 = time.perf_counter()
    try:
        async with websockets.connect(URL, open_timeout=5, max_size=None) as ws:
            print(f"[PASS] connected to {URL} in {(time.perf_counter() - t0) * 1000:.0f} ms")
            silence = np.zeros(16000, dtype="<f4")
            for chunk in np.array_split(silence, 10):          # ten 100 ms frames
                await ws.send(chunk.tobytes())
            await ws.send("Done")
            replies = 0
            async for raw in ws:
                if raw == "Done!":
                    break
                replies += 1
                msg = json.loads(raw)
                if replies == 1:
                    print(f"[NOTE] first reply keys: {sorted(msg)}")
            print(f"[PASS] {replies} JSON replies, then 'Done!' ({(time.perf_counter() - t0) * 1000:.0f} ms total)")
            return 0
    except Exception as e:  # noqa: BLE001 - smoke test: report everything
        print(f"[FAIL] {URL}: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
