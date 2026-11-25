"""Which worker does the thinking. BARNABY_WORKER_BACKEND=byom runs Barnaby on any Pydantic AI model
(BARNABY_BYOM_MODEL); anything else ("claude-code", the default, or "api") is the Claude Agent SDK worker.

Both expose ask(text) -> str, busy, turn and close(), and emit the same events.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .config import settings

if TYPE_CHECKING:
    from .worker import Worker
    from .worker_byom import ByomWorker


def get_worker() -> Worker | ByomWorker:
    # imported on demand, so each backend loads only its own framework
    if settings.worker_backend == "byom":
        from .worker_byom import worker
    else:
        from .worker import worker
    return worker
