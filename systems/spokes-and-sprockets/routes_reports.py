# routes_reports.py - reports. the reports page was meant to have loads of these. it has two. Theo H, 2011
from fastapi import APIRouter

import services
from db import today

router = APIRouter()


@router.get("/api/reports/today")
def today_at_a_glance():
    """Today at a glance: open jobs, jobs due today, bikes ready to collect, low-stock parts, unpaid invoices."""
    return services.shop_stats()


@router.get("/api/reports/takings/{day}")
def takings(day: str):
    """Money taken (paid invoices) on a day. day is YYYY-MM-DD, or the word 'today'."""
    if day == "today":
        day = today()
    return services.takings_on(day)
