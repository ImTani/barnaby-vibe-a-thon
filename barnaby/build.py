"""Build tier: Barnaby writes the endpoint nobody wrote.

1. A git worktree of the system's repo on a new branch (the live repo is untouched until approval).
2. The builder (Claude Agent SDK, local Claude Code login) follows the repo's own README conventions:
   logic in services.py, route with its full path, a test, then runs pytest. Tools are limited to the
   worktree; the only shell command it may run is pytest. ~/.claude settings/plugins never load.
3. We re-run the tests ourselves and show the diff. Code lands only after a human reads it and clicks.
4. Merge (fast-forward) into the repo -> the app reloads -> `synapse build --discover` exposes the new endpoint.
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import stat
import subprocess
import time
from pathlib import Path

import httpx
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, ToolUseBlock, query

from .config import LEGACY_PY, settings
from .events import bus
from .policy import approvals
from .systems import System, registry

BUILDER_PROMPT = """You are Barnaby's builder. You add one HTTP endpoint to the repo in the current directory.

Task: add `{method} {path}`.
What it must do: {spec}

Rules:
- Read README.md first and follow its conventions exactly (where logic lives, route style, error style, tests).
- Where README.md defines a term the task uses (e.g. what counts towards something), the README's definition
  wins over the task text. If they conflict, follow the README and say so in your final sentence.
- Keep the change minimal: one service function, one route, and tests for it. Don't touch unrelated code.
- The route's decorator must use the full path, and any request body model must be in the same file as the route.
- Write a docstring on the route describing what it returns: it becomes the tool description.
- Run the tests with exactly: python -m pytest -q
  Fix anything that fails. Finish when all tests pass, then reply with one sentence describing what you added.
"""


def _git(repo: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def _rm(path: Path) -> None:
    def onerr(func, p, _):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onerror=onerr)


def _pytest(cwd: Path) -> tuple[bool, str]:
    py = str(LEGACY_PY) if LEGACY_PY.exists() else "python"
    r = subprocess.run([py, "-m", "pytest", "-q"], cwd=cwd, capture_output=True, text=True, timeout=300)
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    return r.returncode == 0, tail[-1]


async def build_endpoint(s: System, method: str, path: str, spec: str) -> dict:
    repo = s.repo_path
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")[-40:] or "endpoint"
    stamp = time.strftime("%H%M%S")
    branch = f"barnaby/{slug}-{stamp}"
    wt = repo.parent / f"worktree-{slug}-{stamp}"
    before = {e.key for e in s.endpoints()}
    bus.emit("growth.build.started", system=s.name, method=method, path=path, spec=spec, branch=branch)
    _git(repo, "worktree", "add", "-q", "-b", branch, str(wt))
    try:
        env = settings.worker_env()
        env["PATH"] = str(LEGACY_PY.parent) + os.pathsep + env.get("PATH", "")
        env.pop("SPOKES_DB", None)
        opts = ClaudeAgentOptions(
            model=settings.builder_model, cwd=str(wt), env=env,
            tools=["Read", "Glob", "Grep", "Edit", "Write", "Bash"],
            allowed_tools=["Read", "Glob", "Grep", "Edit(/**)", "Write(/**)", "Bash(python -m pytest*)"],
            permission_mode="dontAsk", setting_sources=[], max_turns=40, effort="high",
        )
        t0 = time.perf_counter()
        summary = ""
        async for msg in query(prompt=BUILDER_PROMPT.format(method=method, path=path, spec=spec), options=opts):
            if isinstance(msg, AssistantMessage):
                for b in msg.content:
                    if isinstance(b, ToolUseBlock):
                        target = str(b.input.get("file_path") or b.input.get("command") or b.input.get("pattern") or "")
                        for prefix in (str(wt) + os.sep, str(wt).replace("\\", "/") + "/", str(wt)):
                            target = target.replace(prefix, "")     # show repo-relative paths, not the worktree's
                        bus.emit("growth.build.step", system=s.name, tool=b.name, target=target[-120:])
                    elif isinstance(b, TextBlock) and b.text.strip():
                        summary = b.text.strip()
            elif isinstance(msg, ResultMessage):
                bus.emit("growth.build.written", system=s.name, seconds=round(time.perf_counter() - t0, 1),
                         turns=msg.num_turns, ok=not msg.is_error)

        _git(wt, "add", "-A")
        diff = _git(wt, "diff", "--cached", "HEAD")
        if not diff.strip():
            return {"ok": False, "error": "the builder made no changes"}
        passed, test_line = await asyncio.to_thread(_pytest, wt)
        bus.emit("growth.build.tested", system=s.name, passed=passed, result=test_line)
        if not passed:
            return {"ok": False, "error": f"tests failed ({test_line})"}

        ok = await approvals.request(tier="build", kind="build", title=f"Add {method} {path} to {s.title}",
                                     detail=f"{summary}\nTests: {test_line}", diff=diff)
        if not ok:
            bus.emit("growth.build.declined", system=s.name, path=path)
            return {"ok": False, "error": "the person declined the change"}

        _git(wt, "-c", "user.name=Barnaby", "-c", "user.email=barnaby@localhost", "commit", "-q",
             "-m", f"Add {method} {path} (written by Barnaby, approved)\n\n{summary}")
        _git(repo, "merge", "--ff-only", "-q", branch)
        bus.emit("growth.build.merged", system=s.name, branch=branch)

        # restart the app so the merged code is live (uvicorn --reload hangs on Windows; see systems.restart),
        # then wait until it actually serves the new route (FastAPI apps list it in /openapi.json)
        await registry.restart(s)
        template = re.sub(r"\{\w+\}", "{x}", path)
        for _ in range(40):
            try:
                spec_paths = httpx.get(s.base_url + "/openapi.json", timeout=1).json().get("paths", {})
                if any(re.sub(r"\{\w+\}", "{x}", p) == template for p in spec_paths):
                    break
            except (httpx.HTTPError, ValueError):
                pass
            await asyncio.sleep(0.25)

        res = await registry.expose(s, [f"{method} {path}"], discover=True)
        added = [e for e in s.endpoints() if e.key not in before]
        if added and not all(e.key in s.exposed for e in added):
            res = await registry.expose(s, [e.key for e in added])
        tools = [f"mcp__{s.name}__{e.tool}" for e in added]
        bus.emit("growth.build.done", system=s.name, endpoints=[e.key for e in added], tools=tools, ok=res.ok)
        return {"ok": res.ok and bool(added), "summary": summary or f"{method} {path}", "tools": tools,
                "error": None if added else "Synapse did not discover the new endpoint"}
    except Exception as e:  # noqa: BLE001
        bus.emit("log", level="error", text=f"build failed: {type(e).__name__}: {e}")
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        _git(repo, "worktree", "remove", "--force", str(wt), check=False)
        if wt.exists():
            _rm(wt)
        _git(repo, "branch", "-D", branch, check=False)
