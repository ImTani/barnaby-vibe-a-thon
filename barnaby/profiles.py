"""Known systems for the demo world. Any other repo can be connected through the API with the same fields."""
from __future__ import annotations

from .config import LEGACY_PY, ROOT, demo_today
from .systems import System

SHOP_REPO = ROOT / ".demo" / "spokes-and-sprockets"


def shop() -> System:
    """Spokes & Sprockets: Theo's 2009 back office (the copy made by scripts/demo_reset.py)."""
    today = demo_today() or ""
    return System(
        name="shop",
        title="the shop's back office",
        repo=str(SHOP_REPO),
        base_url="http://127.0.0.1:8101",
        start=[str(LEGACY_PY), "-m", "uvicorn", "app:app", "--port", "8101"],   # no --reload: Barnaby restarts it
        env={"SPOKES_TODAY": today, "SPOKES_DB": str(SHOP_REPO / "shop.db")} if today else {"SPOKES_DB": str(SHOP_REPO / "shop.db")},
        starter=[
            "GET /api/jobs/open", "GET /api/jobs/due/{day}", "GET /api/jobs/{job_id}",
            "GET /api/parts/low", "GET /api/customers/search/{name}", "GET /api/mechanics",
        ],
        denied=["DELETE /api/jobs/{job_id}"],
    )


PROFILES = {"shop": shop}
