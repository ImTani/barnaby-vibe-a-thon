# MCP setup

Barnaby has no hand-written tools for the systems he looks after. Every system tool is an MCP server that **Synapse
generates from the system's own code**, and Barnaby grows by asking Synapse for more. This page lists the servers, how
they're built and attached, and how to use the same servers from Claude Code, Claude Desktop or Cursor.

## The servers

| Server (MCP name) | What it is | Built by | Runs in |
|---|---|---|---|
| `<system>` (e.g. `shop`) | One passthrough HTTP tool per exposed endpoint of the system | `synapse build --auto --local --endpoints "…"` | `runtime/mcp-servers/.venv` (`mcp==1.30`), stdio |
| `<system>-k<N>` (e.g. `shop-k1`) | One composed skill: several of the system's internal functions fused into one tool | `synapse build --custom -q "…"` (hosted Custom mode) | same runtime, stdio, with the repo on `PYTHONPATH` |
| `barnaby` | Barnaby's growth tools: `capabilities`, `unlock`, `compose`, `build`, `connect` | hand-written ([`barnaby/worker.py`](../barnaby/worker.py)) | in-process (Claude Agent SDK `create_sdk_mcp_server`) |

Tools are addressed as `mcp__<server>__<tool>`, for example `mcp__shop__jobs_due` or
`mcp__shop-k1__hand_back_finished_bike`.

Where they live (all generated files stay out of the target repo, so its diffs stay clean):

```
.demo/barnaby/
  systems.json                         the registry: each system's repo, base URL, exposed endpoints, deny-list, skills
  servers/shop/server.py               Synapse's server after Barnaby's fix-up pass (what actually runs)
  servers/shop/server.synapse.py       Synapse's original output, kept for audit
  servers/shop/skills/<tool>_server.py composed skills (Synapse Custom output, unmodified)
<repo>/.synapse/surface_cache.json     Synapse's discovery atlas: every endpoint it found (Barnaby's map)
```

## How Barnaby drives Synapse

All calls go through [`barnaby/synapse.py`](../barnaby/synapse.py). It runs the pinned local CLI
(`node_modules/@2ndbrainlabs-ai/synapse-cli`, 0.1.9) with `HOME`/`USERPROFILE` redirected to `.cache/synapse-home`
(Synapse otherwise writes `~/.synapse`), `SYNAPSE_TELEMETRY=0`, and no stdin.

| Moment | Command (run in the target repo) | Then |
|---|---|---|
| **Connect** | `synapse build --auto --local --all-endpoints`, then `--endpoints "<starter set>"` | read `.synapse/surface_cache.json`; expose the read-only starters |
| **Unlock** | `synapse build --auto --local --endpoints "<exposed>,<new>"` (0.3–0.5 s) | reconnect the `<system>` server; the turn continues with the new tool |
| **Compose** | `synapse init` (once per repo), then `synapse build --custom -q "<one-sentence job>"` (16–40 s) | register `<system>-k<N>`; the turn continues with the skill |
| **Build** | after Barnaby's code is merged and the system restarted: `synapse build --auto --local --endpoints "…,<new>" --discover` | the new endpoint appears in the atlas and as a tool |

After every Auto build Barnaby applies a small, disclosed fix-up pass (`fixup()`), for issues we confirmed in
Synapse 0.1.9:

```diff
-def create_purchase_order(part_id: Any = None, quantity: Any = None, supplier: Any = None) -> dict:
+def create_purchase_order(part_id: float, quantity: float, supplier: Any = None) -> dict:
     ...
     resp = requests.post(url, headers=headers, json=payload)
-    resp.raise_for_status()
+    if resp.status_code >= 400:
+        try:
+            return {"ok": False, "status_code": resp.status_code, "error": resp.json()}
+        except ValueError:
+            return {"ok": False, "status_code": resp.status_code, "error": resp.text[:2000]}
```

1. Types and required flags come back (Synapse emits every parameter as `Any = None`). Path parameters become
   `str | int`, body fields take the type of their example, and fields with a null example stay optional.
2. Error bodies reach the agent instead of a bare exception, so Barnaby can say *why* something failed.

## How the worker attaches them

[`barnaby/worker.py`](../barnaby/worker.py) builds the Claude Agent SDK options from the registry:

```python
ClaudeAgentOptions(
    mcp_servers={
        "shop":    {"type": "stdio", "command": "runtime/mcp-servers/.venv/Scripts/python",
                    "args": [".demo/barnaby/servers/shop/server.py"],
                    "env": {"ENDPOINT_BASE_URL": "http://127.0.0.1:8101"}},
        "shop-k1": {"type": "stdio", "command": "runtime/mcp-servers/.venv/Scripts/python",
                    "args": [".demo/barnaby/servers/shop/skills/hand_back_finished_bike_server.py"],
                    "env": {"PYTHONPATH": ".demo/spokes-and-sprockets", "SPOKES_DB": "…/shop.db"}},
        "barnaby": <in-process SDK server>,
    },
    strict_mcp_config=True, tools=[],            # MCP tools only: no shell, no files
    setting_sources=[],                           # never load the user's ~/.claude settings or plugins
    can_use_tool=worker._can_use_tool,            # every call -> tier policy -> approvals
)
```

- `can_use_tool` maps each call to a tier: reads pass; writes and composed skills raise a confirmation card; Unlock and
  Compose raise a one-click "grow" card; Build raises a card with the full diff. Deny-listed endpoints never pass.
- When a growth step changes a server, the worker reconnects it (`reconnect_mcp_server`), or starts a new client on
  the same session when the set of servers changes (a new system or a new skill), and continues the turn.

## Use the same servers from your own MCP client

The generated servers are ordinary stdio MCP servers. With the system running (for the shop:
`python scripts/demo_reset.py`, then `python -m barnaby connect shop`), add them to any client. Use absolute paths.

**Claude Code**

```bash
claude mcp add shop --env ENDPOINT_BASE_URL=http://127.0.0.1:8101 -- \
  X:/DevProjects/vibe-a-thon/runtime/mcp-servers/.venv/Scripts/python.exe \
  X:/DevProjects/vibe-a-thon/.demo/barnaby/servers/shop/server.py
```

**Claude Desktop / Cursor** (`claude_desktop_config.json` / `.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "shop": {
      "command": "X:/DevProjects/vibe-a-thon/runtime/mcp-servers/.venv/Scripts/python.exe",
      "args": ["X:/DevProjects/vibe-a-thon/.demo/barnaby/servers/shop/server.py"],
      "env": { "ENDPOINT_BASE_URL": "http://127.0.0.1:8101" }
    },
    "shop-k1": {
      "command": "X:/DevProjects/vibe-a-thon/runtime/mcp-servers/.venv/Scripts/python.exe",
      "args": ["X:/DevProjects/vibe-a-thon/.demo/barnaby/servers/shop/skills/hand_back_finished_bike_server.py"],
      "env": {
        "PYTHONPATH": "X:/DevProjects/vibe-a-thon/.demo/spokes-and-sprockets",
        "SPOKES_DB": "X:/DevProjects/vibe-a-thon/.demo/spokes-and-sprockets/shop.db"
      }
    }
  }
}
```

You get the tools Barnaby has grown so far, but not his approvals, voice, or growth. Those live in Barnaby's own
loop, which is the point of the project.

## Connect your own repo

Barnaby works on any repo Synapse can scan (Python FastAPI/Flask/aiohttp and Node routes; see the pitfalls in the
[README](../README.md#synapse-019-issues-we-hit-and-the-disclosed-fix-up-pass)). Start its HTTP API, then:

- on the display: *Connect a repo*, with the repo path and the API's URL; or
- by voice or text: *"Barnaby, this is our inventory service, in D:/code/inventory, running on port 9000."*

For Compose, put a free Synapse key in `.env` as `SYNAPSE_API_KEY` (hosted Custom mode). Everything else runs locally
with no account.
