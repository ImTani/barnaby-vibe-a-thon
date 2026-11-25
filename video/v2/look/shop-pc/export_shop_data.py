"""Export the REAL shop system's seeded data for the shop-PC look-dev pages.

    .venv/Scripts/python video/v2/look/shop-pc/export_shop_data.py

Seeds a throwaway database (system temp dir, deleted afterwards) with systems/spokes-and-sprockets/seed.py, with
"today" pinned to Monday 2026-11-23 as in the recorded run (video/data.js), and reads it back through Theo's own
services.py. Writes shop-data.js next to this file. Nothing in systems/ is modified.

The film's other states (Thursday night's Back Office tab, PO #3, the four bikes handed back on Monday afternoon, the
16:16 workload report, the two wheel builds moving to Priya, Tuesday morning) are derived here from the same data with
Theo's own functions, in the film's order, so the pages never show a number the real app wouldn't.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHOP = ROOT / "systems" / "spokes-and-sprockets"
TODAY = "2026-11-23"


JOB_KEYS = ("job_id", "mechanic", "work", "customer", "bike", "estimate_hours", "due_date", "status")
THURSDAY, THURSDAY_NOW = "2026-11-19", "2026-11-19 21:47:00"     # scene 1: Theo's last evening at the desk
TUESDAY = "2026-11-24"                                           # scene 7: Priya's first morning
HAND_BACK = [4475, 4490, 4488, 4481]                             # scene 5, in order: Sofia, Kwame, Jana, Tom's Brompton


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="shop-pc-data-")
    os.environ["SPOKES_DB"] = str(Path(tmp) / "shop.db")
    os.environ["SPOKES_TODAY"] = TODAY
    sys.path.insert(0, str(SHOP))
    import db  # noqa: E402  (Theo's modules, imported after the env is set)
    import seed  # noqa: E402
    import services  # noqa: E402

    def workload(week_start, week_end):
        """The workload report Barnaby wrote (same SQL as the approved diff in video/data.js)."""
        con = db.connect()
        rows = con.execute(
            """SELECT m.id AS mechanic_id, m.name, m.weekly_capacity_hours,
                      coalesce(sum(j.estimate_hours), 0) AS workload_hours, count(j.id) AS job_count
               FROM mechanics m
               LEFT JOIN jobs j ON j.mechanic_id = m.id AND j.due_date BETWEEN ? AND ?
                               AND j.status NOT IN ('ready', 'collected')
               GROUP BY m.id ORDER BY m.id""",
            (week_start, week_end),
        ).fetchall()
        con.close()
        for r in rows:
            r["spare_hours"] = round(r["weekly_capacity_hours"] - r["workload_hours"], 2)
            r["overloaded"] = r["workload_hours"] > r["weekly_capacity_hours"]
        rows.sort(key=lambda r: r["spare_hours"])
        return rows

    def day_view(day):
        """Theo's Jobs page as the shop would print it on `day` (the env's today is set to it while reading)."""
        os.environ["SPOKES_TODAY"] = day
        try:
            week_start, week_end = services.week_bounds()
            return {"today": day, "week_start": week_start, "week_end": week_end, "stats": services.shop_stats(),
                    "jobs": [{k: j[k] for k in JOB_KEYS} for j in services.list_open_jobs()],
                    "texts": services.recent_notifications(5)}
        finally:
            os.environ["SPOKES_TODAY"] = TODAY

    try:
        # Monday 23 Nov, morning: the seed as it is (08:52 and the 09:04 order)
        seed.seed()
        week_start, week_end = services.week_bounds()
        data = {
            "today": TODAY,
            "week_start": week_start,
            "week_end": week_end,
            "stats": services.shop_stats(),
            "jobs": [{k: j[k] for k in JOB_KEYS} for j in services.list_open_jobs()],
            "texts": services.recent_notifications(5),
            "parts": services.list_parts(),
            "purchase_orders": services.list_purchase_orders(),
            "mechanics": services.list_mechanics(),
            "invoices": services.unpaid_invoices(),
            "takings": services.takings_on(TODAY),
            # what the real run did next (video/data.js turns 2 and 4)
            "new_po": {"id": 3, "part": "Brake pads (Shimano resin, pair)", "quantity": 10, "supplier": "Madison",
                       "status": "ordered", "created": f"{TODAY} 09:04:12"},
            "reassigned": {"to": "Priya", "jobs": [4471, 4472]},
        }

        # Thursday 19 Nov, 21:47 (the Back Office tab among the nine): the same shop four days earlier. Nothing created
        # after 21:47 exists yet (Monday's two collected jobs were booked on Saturday), and none of the bikes that are
        # ready on Monday morning was ready yet: they were still booked.
        con = db.connect()
        later = "SELECT id FROM jobs WHERE created > ?"
        con.execute(f"DELETE FROM job_parts WHERE job_id IN ({later})", (THURSDAY_NOW,))
        con.execute(f"DELETE FROM invoices WHERE job_id IN ({later})", (THURSDAY_NOW,))
        con.execute("DELETE FROM jobs WHERE created > ?", (THURSDAY_NOW,))
        con.execute("DELETE FROM notifications WHERE sent_at > ?", (THURSDAY_NOW,))
        con.execute("DELETE FROM purchase_orders WHERE created > ?", (THURSDAY_NOW,))
        con.execute("UPDATE jobs SET status = 'booked' WHERE status = 'ready'")
        con.commit()
        con.close()
        thursday = day_view(THURSDAY)

        # Monday afternoon (script scene 5), from the seed again: Martin hands back four finished bikes and Barnaby marks
        # each one ready (Theo's set_job_status), in the script's order. The counters after each one come from Theo's
        # shop_stats, so the 16:08-16:21 pages show what the real app would: stats[i] = after the first i+1. (Barnaby's
        # texts to them aren't exported: the page's one texts table would show them on Monday morning too.)
        seed.seed()
        after = []
        for job_id in HAND_BACK:
            assert services.set_job_status(job_id, "ready")["ok"], job_id
            after.append(services.shop_stats())
        data["handed_back"] = {"status": "ready", "jobs": HAND_BACK, "stats": after}
        # 16:16: the report is built after the hand-backs (Tom's Brompton no longer counts), so Dev carries 31 hours
        data["workload"] = {"week_start": week_start, "week_end": week_end, "mechanics": workload(week_start, week_end)}

        # Tuesday 24 Nov, 08:34: the wheel builds went to Priya at 16:21, and the four bikes handed back were collected
        # on Monday evening, before close. Ready to collect is the four that were ready on Monday morning.
        for job_id in data["reassigned"]["jobs"]:
            assert services.assign_job(job_id, data["reassigned"]["to"])["ok"], job_id
        for job_id in HAND_BACK:
            assert services.set_job_status(job_id, "collected")["ok"], job_id
        data["after_reassign"] = workload(week_start, week_end)
        tuesday = day_view(TUESDAY)
        data["days"] = {THURSDAY: thursday, TUESDAY: tuesday}
    finally:
        try:
            os.remove(os.environ["SPOKES_DB"])
            os.rmdir(tmp)
        except OSError:
            pass
    out = HERE / "shop-data.js"
    out.write_text("/* GENERATED by export_shop_data.py from the real shop system's seed (today = Mon 2026-11-23).\n"
                   " * Do not edit by hand; re-run the script. */\nwindow.SHOP = " + json.dumps(data, indent=1) + ";\n",
                   encoding="utf-8")
    hours = lambda rows: [(r["name"], r["workload_hours"], r["job_count"]) for r in rows]  # noqa: E731
    print(f"{out}: {len(data['jobs'])} open jobs, {len(data['parts'])} parts, {len(data['purchase_orders'])} POs; "
          f"16:16 workload {hours(data['workload']['mechanics'])}, after 16:21 {hours(data['after_reassign'])}; "
          + "; ".join(f"{d}: {len(v['jobs'])} open, ready {v['stats']['ready_to_collect']}, due {v['stats']['due_today']}"
                      for d, v in data["days"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
