# Project-local isolation for bash (Git Bash). Source before any uv/pip/npm/model work:  source scripts/env.sh
# Mirrors scripts/env.ps1. This machine exports UV_CACHE_DIR / PIP_CACHE_DIR / HF_HOME globally
# (X:\Caches\*), and env vars beat config files, so this override is required, not optional.
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BARNABY_ROOT="$(cd "$_here/.." && (pwd -W 2>/dev/null || pwd))"
export BARNABY_ROOT
export UV_CACHE_DIR="$BARNABY_ROOT/.cache/uv"
export PIP_CACHE_DIR="$BARNABY_ROOT/.cache/pip"
export npm_config_cache="$BARNABY_ROOT/.cache/npm"
export XDG_CACHE_HOME="$BARNABY_ROOT/.cache/xdg"
export HF_HOME="$BARNABY_ROOT/models/hf"
export BARNABY_MODELS="$BARNABY_ROOT/models"
export UV_PYTHON_DOWNLOADS=never
export SYNAPSE_TELEMETRY=0
mkdir -p "$UV_CACHE_DIR" "$PIP_CACHE_DIR" "$npm_config_cache" "$HF_HOME"
unset _here
