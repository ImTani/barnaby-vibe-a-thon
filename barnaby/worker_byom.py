"""The bring-your-own-model worker: the same Barnaby on any Pydantic AI model.

  BARNABY_WORKER_BACKEND=byom
  BARNABY_BYOM_MODEL=openai:<model> | google-gla:<model> | groq:<model> | ollama:<model> | anthropic:<model>

Same public interface (ask / busy / turn) and the same behaviour as worker.Worker, built from the same parts
(toolkit.py):
- every connected system's MCP server and every composed-skill server runs over stdio as an MCPToolset, its
  tools named mcp__<server>__<tool>, so the shared prompt and the growth tools' texts read the same;
- every call to those tools passes the shared tier gate first; a refusal comes back as a failed tool result
  the model sees (what the Agent SDK's PermissionResultDeny does);
- the growth tools are plain function tools (mcp__barnaby__*) wrapping the very functions the Claude worker serves;
- after a growth step the changed servers are restarted and the turn carries on, history kept;
- the same events go on the bus, so the display and the voice layer can't tell which worker is thinking.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pydantic_ai
from fastmcp.client.transports import StdioTransport
from pydantic_ai import (
    Agent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessage,
    ModelResponse,
    RunContext,
    TextPart,
    Tool,
    ToolFailed,
    UsageLimits,
)
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model
from pydantic_ai.toolsets import AbstractToolset, FunctionToolset, PrefixedToolset, ToolsetTool, WrapperToolset

from .config import STATE, demo_today, settings
from .events import bus
from .toolkit import (
    MAX_CONTINUATIONS,
    SYSTEM_PROMPT,
    GrowthTool,
    WorkerState,
    continuation,
    gate,
    growth_tools,
    system_servers,
)

pydantic_ai.BANNER_ENABLED = False      # Barnaby owns the console (python -m barnaby ask prints every event)


@dataclass
class _Gated(WrapperToolset[Any]):
    """A server's tools behind the shared tier gate: reads pass, writes and skills wait for the person."""

    async def call_tool(self, name: str, tool_args: dict[str, Any], ctx: RunContext[Any],
                        tool: ToolsetTool[Any]) -> Any:
        refusal = await gate(name, tool_args)
        if refusal is not None:
            raise ToolFailed(refusal)       # a failed result the model reads, without spending its retry budget
        return await super().call_tool(name, tool_args, ctx, tool)


def _instructions() -> str:
    return SYSTEM_PROMPT.format(today=demo_today() or "today")


def _cost(messages: list[ModelMessage]) -> float | None:
    """The run's price in USD (genai-prices), or None when the model has no known price (a local one, say)."""
    try:
        return round(float(sum(m.cost().total_price for m in messages if isinstance(m, ModelResponse))), 4)
    except Exception:  # noqa: BLE001 - an unknown price isn't an error
        return None


class ByomWorker(WorkerState):
    def __init__(self, model: Model | str | None = None):
        super().__init__()
        self.model = model or settings.byom_model
        self.history: list[ModelMessage] = []                    # the conversation, carried across turns
        self._servers: dict[str, tuple[dict, MCPToolset]] = {}   # server name -> (its stdio config, its toolset)
        self._agent: Agent | None = None

    # ── Barnaby's own tools (toolkit.py), as plain function tools ──
    def _growth_toolset(self) -> FunctionToolset:
        def as_tool(t: GrowthTool) -> Tool:
            async def run(**args: Any) -> str:
                try:
                    return await t.run(self, args)
                except Exception as e:  # noqa: BLE001 - as in the SDK's in-process server, the model sees the error
                    raise ToolFailed(str(e)) from e
            return Tool.from_schema(run, name=f"mcp__barnaby__{t.name}", description=t.description,
                                    json_schema=t.json_schema())

        return FunctionToolset([as_tool(t) for t in growth_tools()])

    def _ensure_agent(self) -> Agent:
        if self._agent is None:
            if not self.model:
                raise RuntimeError("BARNABY_BYOM_MODEL is empty: set a Pydantic AI model string, e.g. 'openai:<model>'")
            # defer_model_check: a missing provider package or key surfaces on the display as a turn error;
            # retries=3: smaller models get a few goes at a tool's argument schema before the turn fails
            self._agent = Agent(self.model, name="barnaby", instructions=_instructions, retries=3,
                                toolsets=[self._growth_toolset()], defer_model_check=True)
        return self._agent

    # ── MCP servers ──
    async def _sync_servers(self, restart: set[str] | frozenset[str] = frozenset()) -> None:
        """Attach every system and skill server, and restart the ones in `restart` (their code was regenerated)."""
        configs = system_servers()
        for name in list(self._servers):
            cfg, mcp = self._servers[name]
            if name in restart or configs.get(name) != cfg:
                del self._servers[name]
                await mcp.client.close()        # stdio sessions outlive a run, so stop the old process explicitly
        for name, cfg in configs.items():
            if name not in self._servers:
                transport = StdioTransport(cfg["command"], cfg["args"], env=cfg.get("env"), cwd=str(STATE),
                                           log_file=STATE / f"mcp-{name}.log")
                # 'failed': a tool error reaches the model as a failed result, as in the Claude worker
                self._servers[name] = (cfg, MCPToolset(transport, id=name, tool_error_behavior="failed",
                                                       init_timeout=30))

    def _toolsets(self) -> list[AbstractToolset]:
        # PrefixedToolset joins prefix and name with one "_", so "mcp__shop_" yields mcp__shop__<tool>
        return [_Gated(PrefixedToolset(mcp, prefix=f"mcp__{name}_")) for name, (_, mcp) in self._servers.items()]

    async def close(self) -> None:
        for _, mcp in self._servers.values():
            await mcp.client.close()
        self._servers.clear()

    # ── a turn ──
    async def ask(self, text: str) -> str:
        async with self.lock:
            self.busy = True
            self.turn += 1
            turn = self.turn
            bus.emit("turn.start", turn=turn, text=text)
            final = ""
            try:
                agent = self._ensure_agent()
                await self._sync_servers()
                prompt = text
                for _round in range(1 + MAX_CONTINUATIONS):    # the original ask + up to two growth continuations
                    self.reload.clear()
                    self.grown.clear()
                    final = await self._run(agent, prompt, turn)
                    if not self.reload:
                        break
                    await self._sync_servers(restart=self.reload)
                    for name in self.reload:
                        bus.emit("system.reloaded", system=name)
                    if not self.grown:                            # a system connected: he has said what he took on
                        break
                    prompt = continuation(self.grown)
                nudge = self.habit_nudge()                        # a repeated chain: offer to compose it
                if nudge:
                    final = await self._run(agent, nudge, turn) or final
            except Exception as e:  # noqa: BLE001 - surface every failure to the display
                bus.emit("log", level="error", text=f"{type(e).__name__}: {e}")
                final = "I'm terribly sorry, something went wrong on my side."
                bus.emit("say", text=final, final=True)
            finally:
                self.busy = False
                bus.emit("turn.end", turn=turn)
            return final

    async def _run(self, agent: Agent, prompt: str, turn: int) -> str:
        """One agent run, walked node by node so the bus hears it as it hears the Claude worker's stream."""
        said = ""
        t0 = time.perf_counter()
        # one call at a time, in the order the model asked: confirmation cards come one by one, as with Claude Code
        with Agent.parallel_tool_call_execution_mode("sequential"):
            async with agent.iter(prompt, message_history=self.history, toolsets=self._toolsets(),
                                  usage_limits=UsageLimits(request_limit=40)) as run:
                async for node in run:
                    if not Agent.is_call_tools_node(node):      # model requests run as they are; nothing to report
                        continue
                    for part in node.model_response.parts:      # what the model said alongside its tool calls
                        if isinstance(part, TextPart) and part.content.strip():
                            said = part.content.strip()
                            bus.emit("say", turn=turn, text=said, final=False)
                    async with node.stream(run.ctx) as events:  # its tool calls, reported live as each starts and ends
                        async for ev in events:
                            if isinstance(ev, FunctionToolCallEvent):
                                self.note_call(turn, ev.tool_call_id, ev.part.tool_name, ev.part.args_as_dict())
                            elif isinstance(ev, FunctionToolResultEvent):   # refusals and errors: outcome 'failed'
                                self.note_result(turn, ev.tool_call_id, ev.part.outcome == "success", ev.part.content)
                result = run.result
        self.history = result.all_messages()
        bus.emit("turn.result", turn=turn, ok=True, ms=round((time.perf_counter() - t0) * 1000),
                 turns=result.usage.requests, cost=_cost(result.new_messages()))
        if said:
            bus.emit("say", turn=turn, text=said, final=True)
        return said


worker = ByomWorker()
