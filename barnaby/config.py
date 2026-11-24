"""Paths and settings. Everything lives inside the repo (delete the folder and nothing remains)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

STATE = ROOT / ".demo" / "barnaby"                 # Barnaby's own state: registry, generated servers, logs
SERVERS = STATE / "servers"                         # generated MCP servers live here, never in the target repo
SYNAPSE_HOME = ROOT / ".cache" / "synapse-home"     # Synapse writes ~/.synapse; we point its home here
SYNAPSE_JS = ROOT / "node_modules" / "@2ndbrainlabs-ai" / "synapse-cli"
MCP_RUNTIME_PY = ROOT / "runtime" / "mcp-servers" / ".venv" / "Scripts" / "python.exe"
LEGACY_PY = ROOT / "runtime" / "legacy" / ".venv" / "Scripts" / "python.exe"
DEMO_TODAY_FILE = ROOT / ".demo" / "today"


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Settings:
    worker_backend: str = field(default_factory=lambda: _env("BARNABY_WORKER_BACKEND", "claude-code"))
    worker_model: str = field(default_factory=lambda: _env("BARNABY_WORKER_MODEL", "claude-opus-5-5"))
    builder_model: str = field(default_factory=lambda: _env("BARNABY_BUILDER_MODEL", "claude-opus-5-5"))
    front_desk_model: str = field(default_factory=lambda: _env("BARNABY_FRONT_DESK_MODEL", "claude-haiku-5-5"))
    api_key_present: bool = field(default_factory=lambda: bool(_env("ANTHROPIC_API_KEY")))
    port: int = field(default_factory=lambda: int(_env("BARNABY_PORT", "8700")))
    # auto-approve tiers for unattended tests: comma list of "write,grow,build"
    auto_approve: set[str] = field(default_factory=lambda: {x for x in _env("BARNABY_AUTO_APPROVE").split(",") if x})

    def worker_env(self) -> dict[str, str]:
        """Env for Agent SDK subprocesses. 'claude-code' strips the API key so the local Claude Code login is used."""
        env = dict(os.environ)
        if self.worker_backend == "claude-code":
            env.pop("ANTHROPIC_API_KEY", None)
        env.setdefault("MCP_TOOL_TIMEOUT", "1800000")   # a Build (write code, test, wait for approval) takes minutes
        return env


settings = Settings()


def demo_today() -> str | None:
    return DEMO_TODAY_FILE.read_text().strip() if DEMO_TODAY_FILE.exists() else None
