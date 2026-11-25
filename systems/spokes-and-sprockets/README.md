# Spokes & Sprockets back office (v2.3)

The shop computer's system. Jobs, customers, parts, ordering, mechanics, invoices.
Written by me (Theo) in 2009 when I was 14 because the old Access database kept corrupting,
and patched ever since. Uncle Martin: this file is for whoever looks after it after me. Sorry in advance.

## Running it

```
pip install -r requirements.txt
python seed.py                    # WIPES the database and puts the demo data back. careful!!
uvicorn app:app --port 8101       # then open http://localhost:8101 on the shop computer
pytest                            # the tests
```

`SPOKES_DB` points at a different database file. `SPOKES_TODAY=YYYY-MM-DD` pretends it's a different day.

## How the shop works (read this bit)

- A **job** is one repair on one bike. Every job has a mechanic, an estimate in **hours** (not minutes!!),
  a due date and a status.
- Job statuses, in order: `booked`, `in progress`, `waiting on parts`, `ready` (fixed, waiting for the
  customer to collect), `collected` (gone home, done). Never delete jobs, mark them collected.
  (The delete endpoint is for mistakes only. Uncle Martin, please don't use it.)
- The **shop week** is Monday to Saturday. Each mechanic has `weekly_capacity_hours`: how many hours
  of jobs they can do in a week. Dev only does 20 because he does Tuesdays at the other shop.
  Ravi and Priya do 30.
- A mechanic's **workload** for a week = the hours of their jobs due that week that aren't `ready` or `collected` yet.
  (There's no report for this yet. It's on the Reports page as "coming soon". It has been coming soon since 2011.)
- **Parts**: every part has a stock level and a reorder level. When stock is at or below the reorder level,
  order more. Jobs list the parts they need in `job_parts`.
- **Never trust the stock count on a Friday.** Saturday's parts get picked on Friday afternoon and nobody
  updates the shelves till Monday. (Priya, if you're reading this: hi, welcome, and sorry.)
- When a bike is ready we **text the customer** (the SMS box reads the `notifications` table), then mark
  the job `ready`. When they pick it up, mark it `collected`, which also updates their last visit.
- Customers who haven't been in for **over a year** should get a "we miss you" text (another report I never wrote).

## The API (for the till and the phone app that never happened)

All JSON, all under `/api/...`. Every route is written with its **full path** in the decorator
(e.g. `@router.get("/api/jobs/open")`), no router prefixes, because the old proxy needed full paths.

- **Errors come back as `{"ok": false, "error": "why"}` with a 200**, not as 4xx codes. The old till
  couldn't handle error codes. Successful writes return `{"ok": true, ...}`.
- Path parameters only (`/api/jobs/due/2024-03-01`), no `?query=strings`. Same reason.
- Request bodies are Pydantic models **defined in the same file as the route that uses them**.
  Use plain `str`/`int`/`float` fields (`str | None = None` for optional ones), and put defaults in the handler.
- The shop logic lives in `services.py`. Routes just call it. Every function there says in its docstring
  what it returns.
- Dates are `YYYY-MM-DD` strings. Money is pounds as a float.

Files:

| File | What's in it |
|---|---|
| `routes_jobs.py` | jobs: open, due on a day, detail, book, change status, reassign, delete |
| `routes_customers.py` | customers, search, texting customers, recent texts |
| `routes_parts.py` | parts, low stock, stock changes, purchase orders |
| `routes_mechanics.py` | the mechanics |
| `routes_money.py` | invoices |
| `routes_reports.py` | reports (today at a glance, takings) - the rest are "coming soon" |
| `services.py` | the actual logic |
| `db.py` | sqlite + the schema |
| `seed.py` | demo data |
| `app.py` | the pages the shop computer shows |
| `tests/` | pytest tests, one per route mostly |

## Adding a new report / endpoint

1. Write the logic as a function in `services.py` with a docstring saying what it returns.
2. Add the route in the right `routes_*.py` file with its full path.
3. Add a test in `tests/` (look at `tests/test_api.py`, it uses a throwaway database).
4. Run `pytest`.

Bye. Look after them. - Theo
