# routes_jobs.py - repair jobs. Theo H.
# NOTE: errors come back as {"ok": false, "error": "..."} with a 200. it's how the old site did it, sorry.
from fastapi import APIRouter
from pydantic import BaseModel

import services
from db import today

router = APIRouter()


class BookJobIn(BaseModel):
    customer_id: int
    work: str
    estimate_hours: float
    due_date: str | None = None
    mechanic: str | None = None
    bike_id: int | None = None


class StatusIn(BaseModel):
    status: str


class AssignIn(BaseModel):
    mechanic: str


@router.get("/api/jobs/open")
def open_jobs():
    """All repair jobs that haven't been collected yet, soonest due first, with customer, bike, mechanic, estimated hours and status."""
    return services.list_open_jobs()


@router.get("/api/jobs/due/{day}")
def jobs_due(day: str):
    """Repair jobs due on a given day. day is YYYY-MM-DD, or the word 'today'."""
    if day == "today":
        day = today()
    return services.jobs_due_on(day)


@router.get("/api/jobs/{job_id}")
def job_detail(job_id: int):
    """One repair job, including the parts it needs and how many of each are in stock."""
    return services.get_job(job_id)


@router.post("/api/jobs")
def book_job(body: BookJobIn):
    """Book a new repair job for a customer. due_date is YYYY-MM-DD (defaults to today); mechanic is a first name."""
    return services.book_job(body.customer_id, body.work, body.estimate_hours, body.due_date or today(),
                             body.mechanic or "", body.bike_id)


@router.post("/api/jobs/{job_id}/status")
def update_status(job_id: int, body: StatusIn):
    """Change a job's status: booked, in progress, waiting on parts, ready, or collected."""
    return services.set_job_status(job_id, body.status)


@router.post("/api/jobs/{job_id}/assign")
def assign(job_id: int, body: AssignIn):
    """Give a job to a different mechanic, by first name (e.g. Priya)."""
    return services.assign_job(job_id, body.mechanic)


@router.delete("/api/jobs/{job_id}")
def cancel_job(job_id: int):
    """Cancel and delete a job completely. Careful!! there is no undo."""
    from db import connect
    con = connect()
    con.execute("DELETE FROM job_parts WHERE job_id = ?", (job_id,))
    cur = con.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    con.commit()
    con.close()
    if cur.rowcount == 0:
        return {"ok": False, "error": f"No job #{job_id}"}
    return {"ok": True, "job_id": job_id, "deleted": True}
