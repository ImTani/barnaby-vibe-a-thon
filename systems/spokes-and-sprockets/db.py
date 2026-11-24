# db.py - database stuff for the shop system
# Theo H, March 2009. sqlite because the old access file kept corrupting.
import os
import sqlite3
from datetime import date

DB_PATH = os.environ.get("SPOKES_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    joined TEXT,
    last_visit TEXT
);
CREATE TABLE IF NOT EXISTS bikes (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    make TEXT, model TEXT, colour TEXT
);
CREATE TABLE IF NOT EXISTS mechanics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    weekly_capacity_hours REAL NOT NULL,
    started TEXT
);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    bike_id INTEGER REFERENCES bikes(id),
    mechanic_id INTEGER REFERENCES mechanics(id),
    work TEXT NOT NULL,
    estimate_hours REAL NOT NULL,
    status TEXT NOT NULL,
    due_date TEXT NOT NULL,
    created TEXT NOT NULL,
    notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY,
    sku TEXT UNIQUE,
    name TEXT NOT NULL,
    stock INTEGER NOT NULL,
    reorder_level INTEGER NOT NULL,
    supplier TEXT,
    unit_cost REAL
);
CREATE TABLE IF NOT EXISTS job_parts (
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    part_id INTEGER NOT NULL REFERENCES parts(id),
    qty INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY,
    part_id INTEGER NOT NULL REFERENCES parts(id),
    quantity INTEGER NOT NULL,
    supplier TEXT NOT NULL,
    status TEXT NOT NULL,
    created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    job_id INTEGER,
    channel TEXT NOT NULL,
    message TEXT NOT NULL,
    sent_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    amount REAL NOT NULL,
    paid INTEGER NOT NULL DEFAULT 0,
    created TEXT NOT NULL
);
"""


def connect():
    """Open the shop database. Rows come back as dicts."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = lambda cur, row: {col[0]: row[i] for i, col in enumerate(cur.description)}
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    con = connect()
    con.executescript(SCHEMA)
    con.commit()
    con.close()


def today():
    """Today's date as YYYY-MM-DD. SPOKES_TODAY overrides it (used for demos)."""
    return os.environ.get("SPOKES_TODAY") or date.today().isoformat()
