"""Build tier: Barnaby writes the endpoint nobody wrote.

1. A git worktree of the system's repo on a new branch (the live repo is untouched until approval).
2. The builder (Claude Agent SDK, local Claude Code login) follows the repo's own README conventions:
   logic in services.py, route with its full path, a test, then runs pytest. Tools are limited to the
   worktree; the only shell command it may run is pytest. ~/.claude settings/plugins never load.
3. We re-run the tests ourselves, then explain the change in the household's words (what it does, what it reads,
   what it changes, the checks, that it can be undone), aloud and on the card, with the diff folded behind it.
   Code lands only after a person has had that explanation and clicks.
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
  Fix anything that fails. Finish when all tests pass.

When all tests pass, reply with one sentence describing what you added (it becomes the commit message), then these
four lines for the system's owner, who is not a programmer. Plain words only: no code, file, route, endpoint, API,
function or test talk.
NAME: a short name for what you added, as the owner would say it (e.g. "a weekly workload report")
DOES: one sentence starting "It " that says what it lets them see or do
READS: a short phrase naming the records it looks at (e.g. "the jobs and the mechanics' hours")
CHANGES: "nothing" if it only looks, else a short phrase naming the records it changes
"""

_PLAIN = re.compile(r"^[\s*_>-]*(NAME|DOES|READS|CHANGES)[*_]*\s*:[*_]*\s*(.+?)\s*$", re.MULTILINE)


def plain_parts(reply: str) -> tuple[dict[str, str], str]:
    """The builder's four plain lines (name, does, reads, changes), and the rest of its reply (the commit message)."""
    parts = {k.lower(): v.strip().strip("\"“”`*_ ") for k, v in _PLAIN.findall(reply)}
    for k in ("name", "reads", "changes"):
        if k in parts:
            parts[k] = parts[k].rstrip(".")
    return parts, _PLAIN.sub("", reply).strip()


def _passed(test_line: str) -> int | None:
    m = re.search(r"(\d+) passed", test_line or "")
    return int(m.group(1)) if m else None


def _lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s[1:2].islower() else s       # "A weekly report" -> "a weekly…"; "QR codes" stays


def explain(*, title: str, method: str, path: str, parts: dict[str, str], before: int | None, after: int | None,
            who: str = "") -> dict[str, str]:
    """What Barnaby tells the person before a code change lands, in the household's words: the card's title, its
    summary (what it does, what it reads, what it changes, the checks, that it can be undone) and the spoken line."""
    name = _lower_first(parts.get("name") or ("a new report" if "/report" in path else "a new feature"))
    reads = parts.get("reads") or "the system's records"
    changes = parts.get("changes") or ("nothing" if method == "GET" else "some of its records")
    looks_only = changes.lower().strip(" .") in ("nothing", "none", "nothing at all")
    does = parts.get("does") or f"It adds {name} to {title}."
    owner = f"{who}'s" if who else "The system's own"                  # whose checks they are
    if before and after and after >= before:
        new = after - before
        checks = (f"{owner} {before} checks still pass" +
                  (", and so does the new one." if new == 1 else f", and so do the {new} new ones." if new else "."))
    elif after:
        checks = f"All {after} checks pass."
    else:
        checks = "The checks pass."
    effect = (f"It only reads {reads}, and changes nothing." if looks_only else
              f"It reads {reads}, and changes {changes}.")
    summary = "\n".join([does if does.endswith((".", "!", "?")) else does + ".", effect, checks,
                         "If you change your mind, it can be undone."])
    said = ((f"I've made {name}, which only reads {reads} and changes nothing. " if looks_only else
             f"I've made {name}; it reads {reads} and changes {changes}. ") +
            f"{owner} checks all still pass, it can be undone, and it's on your display to approve.")
    return {"name": name, "title": f"Add {name} to {title}", "summary": summary, "said": said}


def _author(repo: Path) -> str:
    """First name of whoever last worked on the repo, Barnaby aside ("Theo"), or "" if there's no telling."""
    names = [n.strip() for n in _git(repo, "log", "-30", "--format=%an", check=False).splitlines()]
    who = next((n for n in names if n and n.lower() != "barnaby"), "")
    return who.split()[0] if who else ""


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
        _, baseline = await asyncio.to_thread(_pytest, wt)         # how many checks the system had before
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

        # explain before changing anything: the card leads with plain words, and Barnaby says them aloud
        parts, summary = plain_parts(summary)
        plain = explain(title=s.title, method=method, path=path, parts=parts, before=_passed(baseline),
                        after=_passed(test_line), who=_author(repo))
        bus.emit("growth.build.explained", system=s.name, name=plain["name"], summary=plain["summary"])
        bus.emit("say", text=plain["said"], final=False)
        ok = await approvals.request(tier="build", kind="build", title=plain["title"], detail=plain["summary"],
                                     technical=f"{method} {path} in {s.title}, on branch {branch}\n{summary}\n"
                                               f"Tests: {test_line}", diff=diff)
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
        return {"ok": res.ok and bool(added), "name": plain["name"], "summary": plain["summary"], "tools": tools,
                "error": None if added else "Synapse did not discover the new endpoint"}
    except Exception as e:  # noqa: BLE001
        bus.emit("log", level="error", text=f"build failed: {type(e).__name__}: {e}")
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        _git(repo, "worktree", "remove", "--force", str(wt), check=False)
        if wt.exists():
            _rm(wt)
        _git(repo, "branch", "-D", branch, check=False)
