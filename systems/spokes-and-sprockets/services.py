# services.py - the actual shop logic. the routes just call these.
# Theo H. If you change a return shape, update the docstring, future-me will thank you.
from datetime import date, datetime

from db import connect, today

JOB_STATUSES = ["booked", "in progress", "waiting on parts", "ready", "collected"]
OPEN_STATUSES = ("booked", "in progress", "waiting on parts", "ready")

_JOB_SELECT = """
SELECT j.id AS job_id, j.work, j.estimate_hours, j.status, j.due_date, j.notes,
       c.id AS customer_id, c.name AS customer, c.phone AS customer_phone,
       b.make || ' ' || b.model AS bike,
       m.id AS mechanic_id, m.name AS mechanic
FROM jobs j
JOIN customers c ON c.id = j.customer_id
LEFT JOIN bikes b ON b.id = j.bike_id
LEFT JOIN mechanics m ON m.id = j.mechanic_id
"""


def _now():
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def list_open_jobs():
    """Every job that hasn't been collected yet, soonest due first.

    Returns a list of dicts: {job_id, work, estimate_hours, status, due_date, notes,
    customer_id, customer, customer_phone, bike, mechanic_id, mechanic}.
    """
    con = connect()
    rows = con.execute(_JOB_SELECT + " WHERE j.status != 'collected' ORDER BY j.due_date, j.id").fetchall()
    con.close()
    return rows


def jobs_due_on(day):
    """Jobs due on one day (YYYY-MM-DD), excluding collected ones. Same dict shape as list_open_jobs."""
    con = connect()
    rows = con.execute(_JOB_SELECT + " WHERE j.due_date = ? AND j.status != 'collected' ORDER BY j.id", (day,)).fetchall()
    con.close()
    return rows


def get_job(job_id):
    """One job with the parts it needs.

    Returns {ok: True, job: {...same keys as list_open_jobs...}, parts: [{part_id, sku, name, qty_needed, in_stock}]}
    or {ok: False, error: "..."} if there's no such job.
    """
    con = connect()
    job = con.execute(_JOB_SELECT + " WHERE j.id = ?", (job_id,)).fetchone()
    if not job:
        con.close()
        return {"ok": False, "error": f"No job #{job_id}"}
    parts = con.execute(
        """SELECT p.id AS part_id, p.sku, p.name, jp.qty AS qty_needed, p.stock AS in_stock
           FROM job_parts jp JOIN parts p ON p.id = jp.part_id WHERE jp.job_id = ?""",
        (job_id,),
    ).fetchall()
    con.close()
    return {"ok": True, "job": job, "parts": parts}


def set_job_status(job_id, status):
    """Move a job to a new status (booked, in progress, waiting on parts, ready, collected).

    Returns {ok: True, job_id, old_status, new_status} or {ok: False, error}.
    """
    if status not in JOB_STATUSES:
        return {"ok": False, "error": f"Unknown status '{status}'. Use one of: {', '.join(JOB_STATUSES)}"}
    con = connect()
    row = con.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        con.close()
        return {"ok": False, "error": f"No job #{job_id}"}
    con.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    if status == "collected":
        con.execute(
            "UPDATE customers SET last_visit = ? WHERE id = (SELECT customer_id FROM jobs WHERE id = ?)",
            (today(), job_id),
        )
    con.commit()
    con.close()
    return {"ok": True, "job_id": job_id, "old_status": row["status"], "new_status": status}


def assign_job(job_id, mechanic_name):
    """Give a job to a different mechanic, by the mechanic's first name (e.g. "Priya").

    Returns {ok: True, job_id, from_mechanic, to_mechanic} or {ok: False, error}.
    """
    con = connect()
    mech = con.execute("SELECT id, name FROM mechanics WHERE lower(name) = lower(?)", (mechanic_name.strip(),)).fetchone()
    job = con.execute(
        "SELECT j.id, m.name AS mechanic FROM jobs j LEFT JOIN mechanics m ON m.id = j.mechanic_id WHERE j.id = ?",
        (job_id,),
    ).fetchone()
    if not mech:
        con.close()
        return {"ok": False, "error": f"No mechanic called '{mechanic_name}'"}
    if not job:
        con.close()
        return {"ok": False, "error": f"No job #{job_id}"}
    con.execute("UPDATE jobs SET mechanic_id = ? WHERE id = ?", (mech["id"], job_id))
    con.commit()
    con.close()
    return {"ok": True, "job_id": job_id, "from_mechanic": job["mechanic"], "to_mechanic": mech["name"]}


def book_job(customer_id, work, estimate_hours, due_date, mechanic_name="", bike_id=None):
    """Book a new repair job. Returns {ok: True, job_id} or {ok: False, error}."""
    con = connect()
    if not con.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone():
        con.close()
        return {"ok": False, "error": f"No customer #{customer_id}"}
    mech_id = None
    if mechanic_name:
        mech = con.execute("SELECT id FROM mechanics WHERE lower(name) = lower(?)", (mechanic_name,)).fetchone()
        mech_id = mech["id"] if mech else None
    cur = con.execute(
        "INSERT INTO jobs (customer_id, bike_id, mechanic_id, work, estimate_hours, status, due_date, created) VALUES (?,?,?,?,?,?,?,?)",
        (customer_id, bike_id, mech_id, work, estimate_hours, "booked", due_date, _now()),
    )
    con.commit()
    job_id = cur.lastrowid
    con.close()
    return {"ok": True, "job_id": job_id}


def get_customer(customer_id):
    """One customer with their bikes and their last 5 jobs.

    Returns {ok: True, customer: {id, name, phone, email, joined, last_visit}, bikes: [...], recent_jobs: [...]}
    or {ok: False, error}.
    """
    con = connect()
    cust = con.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not cust:
        con.close()
        return {"ok": False, "error": f"No customer #{customer_id}"}
    bikes = con.execute("SELECT id, make, model, colour FROM bikes WHERE customer_id = ?", (customer_id,)).fetchall()
    jobs = con.execute(
        "SELECT id AS job_id, work, status, due_date FROM jobs WHERE customer_id = ? ORDER BY due_date DESC LIMIT 5",
        (customer_id,),
    ).fetchall()
    con.close()
    return {"ok": True, "customer": cust, "bikes": bikes, "recent_jobs": jobs}


def search_customers(name):
    """Customers whose name contains the given text (case-insensitive). Returns a list of {id, name, phone, last_visit}."""
    con = connect()
    rows = con.execute(
        "SELECT id, name, phone, last_visit FROM customers WHERE lower(name) LIKE ? ORDER BY name",
        (f"%{name.lower()}%",),
    ).fetchall()
    con.close()
    return rows


def add_customer(name, phone="", email=""):
    """Add a customer. Returns {ok: True, customer_id}."""
    con = connect()
    cur = con.execute(
        "INSERT INTO customers (name, phone, email, joined, last_visit) VALUES (?,?,?,?,?)",
        (name, phone, email, today(), today()),
    )
    con.commit()
    cid = cur.lastrowid
    con.close()
    return {"ok": True, "customer_id": cid}


def notify_customer(customer_id, message, channel="sms", job_id=None):
    """Send a customer a text (or email). The shop's SMS box just logs it here and the phone sends it.

    Returns {ok: True, notification_id, to, channel, message} or {ok: False, error}.
    """
    con = connect()
    cust = con.execute("SELECT name, phone, email FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not cust:
        con.close()
        return {"ok": False, "error": f"No customer #{customer_id}"}
    cur = con.execute(
        "INSERT INTO notifications (customer_id, job_id, channel, message, sent_at) VALUES (?,?,?,?,?)",
        (customer_id, job_id, channel, message, _now()),
    )
    con.commit()
    nid = cur.lastrowid
    con.close()
    to = cust["phone"] if channel == "sms" else cust["email"]
    return {"ok": True, "notification_id": nid, "to": f"{cust['name']} <{to}>", "channel": channel, "message": message}


def recent_notifications(limit=15):
    """The most recent texts/emails sent. Returns a list of {id, customer, channel, message, sent_at, job_id}."""
    con = connect()
    rows = con.execute(
        """SELECT n.id, c.name AS customer, n.channel, n.message, n.sent_at, n.job_id
           FROM notifications n JOIN customers c ON c.id = n.customer_id ORDER BY n.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    con.close()
    return rows


def list_parts():
    """Every part in stock. Returns a list of {id, sku, name, stock, reorder_level, supplier, unit_cost}."""
    con = connect()
    rows = con.execute("SELECT * FROM parts ORDER BY name").fetchall()
    con.close()
    return rows


def low_stock_parts():
    """Parts at or below their reorder level. Same dict shape as list_parts."""
    con = connect()
    rows = con.execute("SELECT * FROM parts WHERE stock <= reorder_level ORDER BY stock").fetchall()
    con.close()
    return rows


def adjust_stock(part_id, change, reason):
    """Add (positive) or remove (negative) stock for a part. Returns {ok: True, part_id, old_stock, new_stock} or {ok: False, error}."""
    con = connect()
    part = con.execute("SELECT stock FROM parts WHERE id = ?", (part_id,)).fetchone()
    if not part:
        con.close()
        return {"ok": False, "error": f"No part #{part_id}"}
    new = part["stock"] + change
    if new < 0:
        con.close()
        return {"ok": False, "error": f"Only {part['stock']} in stock, can't remove {-change}"}
    con.execute("UPDATE parts SET stock = ? WHERE id = ?", (new, part_id))
    con.commit()
    con.close()
    return {"ok": True, "part_id": part_id, "old_stock": part["stock"], "new_stock": new, "reason": reason}


def create_purchase_order(part_id, quantity, supplier=""):
    """Order more of a part from a supplier (defaults to the part's usual supplier).

    Returns {ok: True, purchase_order_id, part, quantity, supplier, status} or {ok: False, error}.
    """
    if quantity <= 0:
        return {"ok": False, "error": "Quantity has to be at least 1"}
    con = connect()
    part = con.execute("SELECT name, supplier FROM parts WHERE id = ?", (part_id,)).fetchone()
    if not part:
        con.close()
        return {"ok": False, "error": f"No part #{part_id}"}
    supplier = supplier or part["supplier"]
    cur = con.execute(
        "INSERT INTO purchase_orders (part_id, quantity, supplier, status, created) VALUES (?,?,?,?,?)",
        (part_id, quantity, supplier, "ordered", _now()),
    )
    con.commit()
    po_id = cur.lastrowid
    con.close()
    return {"ok": True, "purchase_order_id": po_id, "part": part["name"], "quantity": quantity, "supplier": supplier, "status": "ordered"}


def list_purchase_orders():
    """All purchase orders, newest first. Returns a list of {id, part, quantity, supplier, status, created}."""
    con = connect()
    rows = con.execute(
        """SELECT po.id, p.name AS part, po.quantity, po.supplier, po.status, po.created
           FROM purchase_orders po JOIN parts p ON p.id = po.part_id ORDER BY po.id DESC"""
    ).fetchall()
    con.close()
    return rows


def receive_purchase_order(po_id):
    """Mark an order as delivered and add the stock. Returns {ok: True, purchase_order_id, part, new_stock} or {ok: False, error}."""
    con = connect()
    po = con.execute("SELECT * FROM purchase_orders WHERE id = ?", (po_id,)).fetchone()
    if not po:
        con.close()
        return {"ok": False, "error": f"No purchase order #{po_id}"}
    if po["status"] == "received":
        con.close()
        return {"ok": False, "error": f"Purchase order #{po_id} was already received"}
    con.execute("UPDATE purchase_orders SET status = 'received' WHERE id = ?", (po_id,))
    con.execute("UPDATE parts SET stock = stock + ? WHERE id = ?", (po["quantity"], po["part_id"]))
    part = con.execute("SELECT name, stock FROM parts WHERE id = ?", (po["part_id"],)).fetchone()
    con.commit()
    con.close()
    return {"ok": True, "purchase_order_id": po_id, "part": part["name"], "new_stock": part["stock"]}


def list_mechanics():
    """The mechanics. Returns a list of {id, name, weekly_capacity_hours, started}.

    weekly_capacity_hours is how many hours of jobs they can do Mon-Sat.
    """
    con = connect()
    rows = con.execute("SELECT * FROM mechanics ORDER BY id").fetchall()
    con.close()
    return rows


def unpaid_invoices():
    """Invoices not paid yet. Returns a list of {id, job_id, customer, amount, created}."""
    con = connect()
    rows = con.execute(
        """SELECT i.id, i.job_id, c.name AS customer, i.amount, i.created
           FROM invoices i JOIN jobs j ON j.id = i.job_id JOIN customers c ON c.id = j.customer_id
           WHERE i.paid = 0 ORDER BY i.created"""
    ).fetchall()
    con.close()
    return rows


def create_invoice(job_id, amount):
    """Raise an invoice for a job. Returns {ok: True, invoice_id, job_id, amount} or {ok: False, error}."""
    con = connect()
    if not con.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone():
        con.close()
        return {"ok": False, "error": f"No job #{job_id}"}
    cur = con.execute("INSERT INTO invoices (job_id, amount, paid, created) VALUES (?,?,0,?)", (job_id, amount, _now()))
    con.commit()
    iid = cur.lastrowid
    con.close()
    return {"ok": True, "invoice_id": iid, "job_id": job_id, "amount": amount}


def takings_on(day):
    """Money from paid invoices raised on a day (YYYY-MM-DD). Returns {day, invoices, total}."""
    con = connect()
    row = con.execute(
        "SELECT count(*) AS invoices, coalesce(sum(amount), 0) AS total FROM invoices WHERE paid = 1 AND substr(created, 1, 10) = ?",
        (day,),
    ).fetchone()
    con.close()
    return {"day": day, "invoices": row["invoices"], "total": round(row["total"], 2)}


def shop_stats():
    """Today at a glance. Returns {today, open_jobs, due_today, ready_to_collect, low_stock_parts, unpaid_invoices}."""
    t = today()
    con = connect()
    stats = {
        "today": t,
        "open_jobs": con.execute("SELECT count(*) AS n FROM jobs WHERE status != 'collected'").fetchone()["n"],
        "due_today": con.execute("SELECT count(*) AS n FROM jobs WHERE due_date = ? AND status != 'collected'", (t,)).fetchone()["n"],
        "ready_to_collect": con.execute("SELECT count(*) AS n FROM jobs WHERE status = 'ready'").fetchone()["n"],
        "low_stock_parts": con.execute("SELECT count(*) AS n FROM parts WHERE stock <= reorder_level").fetchone()["n"],
        "unpaid_invoices": con.execute("SELECT count(*) AS n FROM invoices WHERE paid = 0").fetchone()["n"],
    }
    con.close()
    return stats


def week_bounds(day=None):
    """Monday and Saturday (YYYY-MM-DD) of the shop week containing `day` (default today)."""
    d = date.fromisoformat(day or today())
    monday = date.fromordinal(d.toordinal() - d.weekday())
    saturday = date.fromordinal(monday.toordinal() + 5)
    return monday.isoformat(), saturday.isoformat()
