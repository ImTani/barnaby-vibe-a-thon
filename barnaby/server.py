"""Barnaby's API + event stream. The display (and later the voice front desk) talk to this.

  GET  /api/state                 systems, exposed/discovered endpoints, pending approvals, busy flag
  POST /api/ask        {text}     start a turn (returns immediately; watch /api/events)
  POST /api/approvals/{id} {approved, via}
  POST /api/connect    {profile} | {name, title, repo, base_url, start?, env?, starter?, denied?}
  GET  /api/events                Server-Sent Events: every event (see events.py)
"""
from __future__ import annotations

import asyncio
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .config import ROOT
from .events import bus
from .policy import approvals
from .profiles import PROFILES
from .systems import System, registry
from .worker import worker

UI = ROOT / "ui"
app = FastAPI(title="Barnaby")


class AskIn(BaseModel):
    text: str


class ApprovalIn(BaseModel):
    approved: bool
    via: str = "click"


class ConnectIn(BaseModel):
    profile: str | None = None
    name: str | None = None
    title: str | None = None
    repo: str | None = None
    base_url: str | None = None
    start: list[str] = []
    env: dict[str, str] = {}
    starter: list[str] = []
    denied: list[str] = []


@app.get("/api/state")
def state():
    return {"busy": worker.busy, "systems": [s.summary() for s in registry.systems.values()],
            "approvals": approvals.summary()}


@app.post("/api/ask")
async def ask(body: AskIn):
    if worker.busy:
        return JSONResponse({"ok": False, "error": "busy"}, status_code=409)
    asyncio.create_task(worker.ask(body.text))
    return {"ok": True}


@app.post("/api/approvals/{pid}")
def resolve(pid: str, body: ApprovalIn):
    return {"ok": approvals.resolve(pid, body.approved, body.via)}


@app.post("/api/connect")
async def connect(body: ConnectIn):
    if body.profile:
        s = PROFILES[body.profile]()
    else:
        s = System(name=body.name, title=body.title or body.name, repo=body.repo, base_url=body.base_url,
                   start=body.start, env=body.env, starter=body.starter, denied=body.denied)
    asyncio.create_task(registry.connect(s))
    return {"ok": True, "system": s.name}


@app.get("/api/events")
async def events(request: Request):
    q = bus.subscribe()

    async def gen():
        try:
            while not await request.is_disconnected():
                try:
                    ev = await asyncio.wait_for(q.get(), 15)
                    yield {"event": "message", "id": str(ev.id), "data": ev.json()}
                except TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            bus.unsubscribe(q)

    return EventSourceResponse(gen())


VOICE = os.environ.get("BARNABY_VOICE_URL", "http://127.0.0.1:7860")


@app.post("/api/voice/offer")
async def voice_offer(request: Request):
    """Same-origin proxy for the voice bot's WebRTC offer (Pipecat SmallWebRTC on :7860)."""
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{VOICE}/api/offer", content=await request.body(), headers={"Content-Type": "application/json"})
    return JSONResponse(r.json(), status_code=r.status_code)


@app.patch("/api/voice/offer")
async def voice_ice(request: Request):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.patch(f"{VOICE}/api/offer", content=await request.body(), headers={"Content-Type": "application/json"})
    return JSONResponse(r.json(), status_code=r.status_code)


if UI.exists():
    app.mount("/ui", StaticFiles(directory=UI), name="ui")


@app.get("/")
def index():
    page = UI / "index.html"
    return FileResponse(page) if page.exists() else JSONResponse({"barnaby": "running", "ui": "not built yet"})
