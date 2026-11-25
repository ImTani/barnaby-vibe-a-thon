"""Systems Barnaby looks after: where each repo lives, how to run it, what's exposed, and its process.

The registry is a small JSON file in .demo/barnaby/systems.json. "Connecting" a repo = Synapse discovers its
endpoints, Barnaby exposes a starter set of read-only ones, and the generated MCP server is ready to attach.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

import httpx
import psutil

from . import synapse
from .config import MCP_RUNTIME_PY, SERVERS, STATE
from .events import bus

REGISTRY = STATE / "systems.json"


@dataclass
class System:
    name: str                                   # short id, also the MCP server name (tools: mcp__<name>__<tool>)
    title: str                                  # how Barnaby refers to it ("the shop's back office")
    repo: str                                   # path to the repo Synapse scans
    base_url: str                               # where its HTTP API runs
    start: list[str] = field(default_factory=list)   # command to run it (empty: already running elsewhere)
    env: dict[str, str] = field(default_factory=dict)
    exposed: list[str] = field(default_factory=list)  # endpoint keys exposed as tools ("GET /api/jobs/open")
    denied: list[str] = field(default_factory=list)   # never exposed, whoever asks
    starter: list[str] = field(default_factory=list)  # preferred first exposure (else: read-only endpoints)
    skills: list[dict] = field(default_factory=list)  # composed tools: {server, tool, path, description}
    pid: int | None = None

    @property
    def repo_path(self) -> Path:
        return Path(self.repo)

    @property
    def server_path(self) -> Path:
        return SERVERS / self.name / "server.py"

    def endpoints(self) -> list[synapse.Endpoint]:
        return synapse.surface(self.repo_path)

    def mcp_config(self) -> dict:
        return {"type": "stdio", "command": str(MCP_RUNTIME_PY), "args": [str(self.server_path)],
                "env": {"ENDPOINT_BASE_URL": self.base_url}}

    def skill_configs(self) -> dict[str, dict]:
        """One MCP server per composed skill. Synapse Custom output imports the repo's own modules, so it runs with
        the repo on PYTHONPATH and the system's env (e.g. its database path)."""
        out = {}
        for sk in self.skills:
            out[sk["server"]] = {"type": "stdio", "command": str(MCP_RUNTIME_PY), "args": [sk["path"]],
                                 "env": {"PYTHONPATH": self.repo, **self.env}}
        return out

    def summary(self) -> dict:
        eps = self.endpoints()
        return {"name": self.name, "title": self.title, "repo": self.repo, "base_url": self.base_url,
                "running": self.is_running(), "exposed": self.exposed, "denied": self.denied, "skills": self.skills,
                "endpoints": [e.brief() | {"exposed": e.key in self.exposed, "denied": e.key in self.denied} for e in eps]}

    def is_running(self) -> bool:
        try:
            return httpx.get(self.base_url + "/", timeout=1.0).status_code < 500
        except httpx.HTTPError:
            return False


class Registry:
    def __init__(self):
        self.systems: dict[str, System] = {}
        if REGISTRY.exists():
            for d in json.loads(REGISTRY.read_text(encoding="utf-8")):
                self.systems[d["name"]] = System(**d)

    def save(self) -> None:
        STATE.mkdir(parents=True, exist_ok=True)
        REGISTRY.write_text(json.dumps([asdict(s) for s in self.systems.values()], indent=2), encoding="utf-8")

    def get(self, name: str) -> System:
        if name not in self.systems:
            raise KeyError(f"No system called '{name}'. Connected: {', '.join(self.systems) or 'none'}")
        return self.systems[name]

    # ── processes ──
    async def ensure_running(self, s: System) -> bool:
        if s.is_running():
            return True
        if not s.start:
            return False
        log = open(STATE / f"{s.name}.log", "a", encoding="utf-8")
        proc = subprocess.Popen(s.start, cwd=s.repo, env={**os.environ, **s.env}, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        s.pid = proc.pid
        self.save()
        for _ in range(60):
            await asyncio.sleep(0.25)
            if s.is_running():
                bus.emit("system.started", system=s.name, base_url=s.base_url, pid=proc.pid)
                return True
        return False

    def stop(self, s: System) -> None:
        if s.pid and psutil.pid_exists(s.pid):
            parent = psutil.Process(s.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            psutil.wait_procs([parent], timeout=5)
        s.pid = None
        self.save()

    async def restart(self, s: System) -> bool:
        """Stop and start a system we launched (after Barnaby's code lands). Deterministic on Windows, where
        uvicorn --reload hangs: its reloader stops workers with a console Ctrl-C a windowless process never gets."""
        if not s.start:
            return s.is_running()
        self.stop(s)
        for _ in range(40):                        # wait for the port to free up
            if not s.is_running():
                break
            await asyncio.sleep(0.25)
        ok = await self.ensure_running(s)
        bus.emit("system.restarted", system=s.name, ok=ok)
        return ok

    # ── connect / expose ──
    async def connect(self, s: System, starter_limit: int = 6) -> dict:
        """Discover every endpoint, then expose a starter set (configured, else the first read-only ones)."""
        bus.emit("system.connecting", system=s.name, title=s.title, repo=s.repo)
        self.systems[s.name] = s
        await self.ensure_running(s)
        # first pass: discover everything (Synapse needs a selection to build, so build the read-only set)
        res = await synapse.build(s.name, s.repo_path, endpoints=None)
        eps = s.endpoints()
        if not res.ok or not eps:
            return {"ok": False, "error": "Synapse found no HTTP endpoints in that repo", "output": res.output[-800:]}
        keys = {e.key for e in eps}
        starter = [k for k in s.starter if k in keys] or [e.key for e in eps if e.read_only][:starter_limit]
        res = await synapse.build(s.name, s.repo_path, endpoints=starter)
        s.exposed = starter
        self.save()
        bus.emit("system.connected", system=s.name, title=s.title, discovered=len(eps), exposed=starter,
                 read_only=sum(e.read_only for e in eps), seconds=round(res.seconds, 2))
        return {"ok": res.ok, "discovered": len(eps), "exposed": starter}

    async def compose(self, s: System, description: str) -> synapse.CustomResult:
        """Compose a new skill with Synapse Custom mode and register it as an MCP server for this system."""
        res = await synapse.build_custom(s.name, s.repo_path, description)
        if res.ok:
            s.skills = [k for k in s.skills if k["tool"] != res.tool]
            s.skills.append({"server": f"{s.name}-k{len(s.skills) + 1}", "tool": res.tool, "path": str(res.server),
                             "description": description})
            self.save()
        return res

    async def expose(self, s: System, add: list[str], discover: bool = False) -> synapse.BuildResult:
        """Rebuild the system's MCP server with more endpoints (Unlock, and the last step of Build)."""
        wanted = [k for k in dict.fromkeys(s.exposed + add) if k not in s.denied]
        res = await synapse.build(s.name, s.repo_path, endpoints=wanted, discover=discover)
        if res.ok:
            known = {e.key for e in s.endpoints()}
            s.exposed = [k for k in wanted if k in known]
            self.save()
        return res


registry = Registry()
