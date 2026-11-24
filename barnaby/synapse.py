"""Synapse driver: discover a repo's endpoints, expose a chosen set as an MCP server, rebuild after changes.

Barnaby never edits Synapse's job; he wraps it:
- runs the pinned local CLI (node_modules) non-interactively, with its home redirected into the repo
  (Synapse 0.1.9 otherwise writes ~/.synapse even with telemetry off);
- reads .synapse/surface_cache.json as the capability atlas (every endpoint Synapse discovered);
- moves the generated server out of the target repo into .demo/barnaby/servers/<system>/server.py so the
  repo stays clean (and the Build tier's diffs never include generated files);
- applies a small, disclosed fix-up pass (fixup()) for known 0.1.9 issues.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import ROOT, SERVERS, SYNAPSE_HOME, SYNAPSE_JS
from .events import bus

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


@dataclass
class Endpoint:
    method: str
    path: str
    tool: str                       # Synapse's suggested tool name (the handler name)
    description: str
    payload: dict | None
    file: str
    line: int
    path_params: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"

    @property
    def read_only(self) -> bool:
        return self.method == "GET"

    def brief(self) -> dict:
        return {"key": self.key, "tool": self.tool, "method": self.method, "path": self.path,
                "description": self.description, "read_only": self.read_only,
                "params": self.path_params + list((self.payload or {}).keys())}


@dataclass
class BuildResult:
    ok: bool
    server: Path | None
    seconds: float
    endpoints: int
    output: str


def _env() -> dict[str, str]:
    SYNAPSE_HOME.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "USERPROFILE": str(SYNAPSE_HOME), "HOME": str(SYNAPSE_HOME),
        "SYNAPSE_TELEMETRY": "0",
        # plain local Auto calls no model, but 0.1.9 still checks for a provider key; Ollama needs none
        "SYNAPSE_LLM_PROVIDER": env.get("SYNAPSE_LLM_PROVIDER") or "ollama",
        "NO_COLOR": "1", "FORCE_COLOR": "0",
    })
    return env


async def _run(args: list[str], cwd: Path, timeout: float = 300) -> tuple[int, str]:
    cli = SYNAPSE_JS / "dist" / "index.js"
    proc = await asyncio.create_subprocess_exec(
        "node", str(cli), *args, cwd=str(cwd), env=_env(),
        stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout)
    except TimeoutError:
        proc.kill()
        return 124, "synapse timed out"
    return proc.returncode or 0, ANSI.sub("", out.decode("utf-8", "replace"))


def surface(repo: Path) -> list[Endpoint]:
    """Every endpoint Synapse discovered in the repo (from its surface cache), in file order."""
    cache = repo / ".synapse" / "surface_cache.json"
    if not cache.exists():
        return []
    data = json.loads(cache.read_text(encoding="utf-8"))
    eps: list[Endpoint] = []
    for fname, entry in sorted(data.get("files", {}).items()):
        for e in entry.get("endpoints", []):
            eps.append(Endpoint(
                method=e["method"].upper(), path=e["path"], tool=e.get("suggested_tool_name") or e["handler_qualname"],
                description=(e.get("description") or "").strip(), payload=e.get("payload_example"),
                file=e.get("file_path", fname), line=e.get("start_line", 0),
                path_params=re.findall(r"\{(\w+)\}", e["path"]),
            ))
    return eps


async def build(system: str, repo: Path, endpoints: list[str] | None = None, discover: bool = False) -> BuildResult:
    """Run `synapse build --auto --local` for the given endpoint keys ("GET /api/x"), or all if None.

    Returns the path of the (fixed-up) server under .demo/barnaby/servers/<system>/server.py.
    """
    t0 = time.perf_counter()
    for stale in repo.glob("synapse_auto_server*.py"):          # 0.1.9 writes _2, _3... if the file exists
        stale.unlink()
    had_env_example = (repo / ".env.example").exists()
    args = ["build", "--auto", "--local"]
    args += ["--endpoints", ",".join(endpoints)] if endpoints else ["--all-endpoints"]
    if discover:
        args.append("--discover")
    bus.emit("synapse.run", system=system, args=args)
    code, out = await _run(args, repo)
    generated = repo / "synapse_auto_server.py"
    if not had_env_example and (repo / ".env.example").exists():
        (repo / ".env.example").unlink()                        # Synapse drops one; keep Theo's repo clean
    m = re.search(r"Extracted (\d+) endpoint", out)
    n = int(m.group(1)) if m else len(surface(repo))
    if code != 0 or not generated.exists():
        bus.emit("synapse.failed", system=system, code=code, output=out[-1500:])
        return BuildResult(False, None, time.perf_counter() - t0, n, out)
    dest_dir = SERVERS / system
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "server.py"
    src = generated.read_text(encoding="utf-8")
    shutil.move(str(generated), dest_dir / "server.synapse.py")  # keep Synapse's original output for disclosure
    dest.write_text(fixup(src, surface(repo)), encoding="utf-8")
    secs = time.perf_counter() - t0
    bus.emit("synapse.built", system=system, seconds=round(secs, 2), exposed=len(endpoints or []) or n, discovered=n)
    return BuildResult(True, dest, secs, n, out)


# ── fix-up pass (disclosed in the README): known Synapse 0.1.9 output issues ──

_ERR_RETURN = (
    "    if resp.status_code >= 400:\n"
    "        try:\n"
    "            return {\"ok\": False, \"status_code\": resp.status_code, \"error\": resp.json()}\n"
    "        except ValueError:\n"
    "            return {\"ok\": False, \"status_code\": resp.status_code, \"error\": resp.text[:2000]}\n"
)


def _py_type(example) -> str | None:
    if isinstance(example, bool):
        return "bool"
    if isinstance(example, (int, float)):
        return "float"
    if isinstance(example, str):
        return "str"
    return None


def fixup(source: str, endpoints: list[Endpoint]) -> str:
    """1) error bodies reach the agent instead of a bare 'raise_for_status' exception;
    2) parameters get types and required-ness back (0.1.9 emits every one as `Any = None`):
       path params -> required str; body fields with a typed example -> required; null examples stay optional;
    3) the base URL defaults to the system's configured URL if the env var is missing (set by Barnaby anyway).
    """
    source = source.replace("    resp.raise_for_status()\n", _ERR_RETURN)
    by_tool = {e.tool: e for e in endpoints}

    def retype(m: re.Match) -> str:
        name, params = m.group(1), m.group(2)
        ep = by_tool.get(name)
        if not ep or not params.strip():
            return m.group(0)
        required, optional = [], []
        for p in [p.strip() for p in params.split(",") if p.strip()]:
            pname = p.split(":")[0].strip()
            if pname in ep.path_params:
                required.append(f"{pname}: str | int")     # agents pass ids as numbers; pydantic won't coerce int->str
                continue
            t = _py_type((ep.payload or {}).get(pname))
            if t:
                required.append(f"{pname}: {t}")
            else:
                optional.append(f"{pname}: Any = None")
        return f"def {name}({', '.join(required + optional)}) -> dict:"

    source = re.sub(r"def (\w+)\(([^)]*)\) -> dict:", retype, source)
    return "# Fixed up by Barnaby (see barnaby/synapse.py: fixup). Synapse's original output: server.synapse.py\n" + source
