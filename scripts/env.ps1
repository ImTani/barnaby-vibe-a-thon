# Project-local isolation for PowerShell. Dot-source before any uv/pip/npm/model work:  . .\scripts\env.ps1
# This machine exports UV_CACHE_DIR / PIP_CACHE_DIR / HF_HOME globally (X:\Caches\*), and env vars
# beat config files, so this override is required, not optional. Delete the repo and nothing remains.
$root = Split-Path -Parent $PSScriptRoot
$env:BARNABY_ROOT        = $root
$env:UV_CACHE_DIR        = Join-Path $root ".cache\uv"
$env:PIP_CACHE_DIR       = Join-Path $root ".cache\pip"
$env:npm_config_cache    = Join-Path $root ".cache\npm"
$env:XDG_CACHE_HOME      = Join-Path $root ".cache\xdg"
$env:HF_HOME             = Join-Path $root "models\hf"
$env:BARNABY_MODELS      = Join-Path $root "models"
$env:UV_PYTHON_DOWNLOADS = "never"
$env:SYNAPSE_TELEMETRY   = "0"
$env:IMPECCABLE_HOME     = Join-Path $root ".cache\impeccable"   # impeccable skill engine (else ~/.impeccable)
$env:BLENDER_USER_RESOURCES  = Join-Path $root ".cache\blender"  # Blender user dirs (else %APPDATA%)
$env:BLENDER_USER_CONFIG     = Join-Path $root ".cache\blender\config"
$env:BLENDER_USER_SCRIPTS    = Join-Path $root ".cache\blender\scripts"
$env:BLENDER_USER_DATAFILES  = Join-Path $root ".cache\blender\datafiles"
$env:BLENDER_USER_EXTENSIONS = Join-Path $root ".cache\blender\extensions"
foreach ($d in $env:UV_CACHE_DIR, $env:PIP_CACHE_DIR, $env:npm_config_cache, $env:HF_HOME, $env:IMPECCABLE_HOME, $env:BLENDER_USER_CONFIG) {
  New-Item -ItemType Directory -Force $d | Out-Null
}
