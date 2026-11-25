# seed.py - put the shop's data back to a known state.  python seed.py
# Theo H. dates are relative to "today" (db.today(), which SPOKES_TODAY can override) so it never goes stale.
import os
from datetime import date, timedelta

import db

CUSTOMERS = [
    # name, phone, email, joined, last_visit (days ago)
    ("Rachel Okafor", "07700 900101", "rachel.okafor@example.co.uk", "2011-05-14", 3),
    ("Magnus Lindqvist", "07700 900102", "magnus.l@example.co.uk", "2016-08-02", 6),
    ("Anika Banerjee", "07700 900103", "anika.b@example.co.uk", "2014-03-21", 2),
    ("Tom Whitfield", "07700 900104", "tom.whitfield@example.co.uk", "2009-06-30", 1),
    ("Piotr Kowalski", "07700 900105", "p.kowalski@example.co.uk", "2018-01-11", 9),
    ("Funmi Adeyemi", "07700 900106", "funmi.a@example.co.uk", "2020-04-04", 4),
    ("Claire Moreau", "07700 900107", "claire.moreau@example.co.uk", "2022-09-17", 5),
    ("Thanh Nguyen", "07700 900108", "thanh.nguyen@example.co.uk", "2013-02-08", 8),
    ("Luca Rossi", "07700 900109", "luca.rossi@example.co.uk", "2017-07-23", 12),
    ("Sofia Ferreira", "07700 900110", "sofia.f@example.co.uk", "2015-10-05", 7),
    ("Aoife O'Brien", "07700 900111", "aoife.obrien@example.co.uk", "2019-03-15", 10),
    ("Karim Haddad", "07700 900112", "karim.h@example.co.uk", "2021-11-28", 1),
    ("Yuki Tanaka", "07700 900113", "yuki.tanaka@example.co.uk", "2012-04-19", 14),
    ("Jana Novak", "07700 900114", "jana.novak@example.co.uk", "2023-02-02", 11),
    ("Arthur Pemberton", "07700 900115", "a.pemberton@example.co.uk", "1998-05-01", 20),
    ("Kwame Mensah", "07700 900116", "kwame.m@example.co.uk", "2016-06-06", 3),
    ("Zara Ali", "07700 900117", "zara.ali@example.co.uk", "2024-08-30", 0),
    ("Sean Brennan", "07700 900118", "sean.brennan@example.co.uk", "2010-12-12", 15),
    ("Gareth Hughes", "07700 900119", "gareth.hughes@example.co.uk", "2008-09-09", 6),
    ("Marisol Delgado", "07700 900120", "marisol.d@example.co.uk", "2019-05-25", 5),
    ("Niamh Fitzgerald", "07700 900121", "niamh.fitz@example.co.uk", "2014-07-07", 4),
    ("Chidi Okonkwo", "07700 900122", "chidi.o@example.co.uk", "2018-10-10", 2),
    # haven't been in for over a year
    ("Douglas Fairbairn", "07700 900123", "d.fairbairn@example.co.uk", "2007-04-12", 540),
    ("Helen Marsh", "07700 900124", "helen.marsh@example.co.uk", "2012-08-08", 430),
    ("Ibrahim Yusuf", "07700 900125", "ibrahim.y@example.co.uk", "2016-02-14", 700),
    ("Greta Lindholm", "07700 900126", "greta.l@example.co.uk", "2019-09-19", 395),
    ("Patrick Doyle", "07700 900127", "patrick.doyle@example.co.uk", "2005-03-03", 1100),
    ("Mei Chen", "07700 900128", "mei.chen@example.co.uk", "2020-06-01", 460),
]

BIKES = {  # customer name -> (make, model, colour)
    "Rachel Okafor": ("Genesis", "Croix de Fer", "green"), "Magnus Lindqvist": ("Bianchi", "Infinito", "celeste"),
    "Anika Banerjee": ("Trek", "FX 3", "black"), "Tom Whitfield": ("Brompton", "C Line", "orange"),
    "Piotr Kowalski": ("Specialized", "Allez", "red"), "Funmi Adeyemi": ("Cannondale", "Topstone", "grey"),
    "Claire Moreau": ("Riese & Muller", "Charger4", "blue"), "Thanh Nguyen": ("Surly", "Long Haul Trucker", "olive"),
    "Luca Rossi": ("Colnago", "C64", "white"), "Sofia Ferreira": ("Giant", "Defy", "teal"),
    "Aoife O'Brien": ("Ribble", "CGR", "purple"), "Karim Haddad": ("Santa Cruz", "Stigmata", "yellow"),
    "Yuki Tanaka": ("Kona", "Rove", "sand"), "Jana Novak": ("Canyon", "Grail", "black"),
    "Arthur Pemberton": ("Raleigh", "Record Ace (1978)", "flamboyant red"), "Kwame Mensah": ("Boardman", "SLR", "silver"),
    "Zara Ali": ("Pinnacle", "Lithium", "blue"), "Sean Brennan": ("Dawes", "Galaxy", "maroon"),
    "Gareth Hughes": ("Orbea", "Orca", "black"), "Marisol Delgado": ("Cube", "Attain", "grey"),
    "Niamh Fitzgerald": ("Marin", "Muirwoods", "green"), "Chidi Okonkwo": ("Merida", "Scultura", "red"),
}

MECHANICS = [("Dev", 20, "2015-04-01"), ("Ravi", 30, "2019-09-02"), ("Priya", 30, None)]  # Priya starts "today"

PARTS = [
    # sku, name, stock, reorder_level, supplier, unit_cost
    ("BP-SH-RES", "Brake pads (Shimano resin, pair)", 1, 4, "Madison", 6.50),
    ("SPK-DT-292", "Spokes DT Swiss 292mm (each)", 40, 64, "Upgrade Bikes", 0.85),
    ("RIM-DT-R460", "Rim DT Swiss R460 700c", 2, 2, "Upgrade Bikes", 42.00),
    ("TUB-700-25", "Inner tube 700x25c", 0, 10, "Schwalbe UK", 4.20),
    ("CHN-KMC-X11", "Chain KMC X11", 5, 3, "Madison", 22.00),
    ("CAS-11-32", "Cassette 11-32 (11 speed)", 1, 2, "Madison", 38.00),
    ("CAB-SH-GEAR", "Gear cable set", 12, 5, "Madison", 9.50),
    ("TAPE-BAR-BLK", "Bar tape (black)", 7, 4, "Fizik", 14.00),
    ("BB-SH-HT2", "Bottom bracket Shimano HT2", 3, 2, "Madison", 26.00),
    ("FLD-DOT51", "Brake fluid DOT 5.1 (500ml)", 2, 2, "Madison", 8.00),
    ("HDS-FSA-118", "Headset FSA 1-1/8in", 4, 2, "Madison", 31.00),
    ("TYR-GP5K-28", "Tyre Continental GP5000 28c", 6, 4, "Continental UK", 52.00),
]

# job id, customer, mechanic, work, hours, status, due (days from today), [(part sku, qty)]
JOBS = [
    # Dev: 31.0 hours booked this week against a 20 hour week
    (4471, "Rachel Okafor", "Dev", "Wheel build (front, 32 hole)", 6.0, "booked", 1, [("SPK-DT-292", 32), ("RIM-DT-R460", 1)]),
    (4472, "Magnus Lindqvist", "Dev", "Wheel build (rear, 32 hole)", 5.5, "booked", 2, [("SPK-DT-292", 32), ("RIM-DT-R460", 1)]),
    (4478, "Anika Banerjee", "Dev", "Brake bleed + new pads", 1.5, "booked", 1, [("BP-SH-RES", 2), ("FLD-DOT51", 1)]),
    (4481, "Tom Whitfield", "Dev", "Full service", 3.0, "in progress", 0, []),
    (4482, "Piotr Kowalski", "Dev", "Full service", 3.0, "booked", 3, []),
    (4483, "Funmi Adeyemi", "Dev", "Drivetrain overhaul (chain + cassette)", 4.5, "booked", 2, [("CHN-KMC-X11", 1), ("CAS-11-32", 1)]),
    (4484, "Claire Moreau", "Dev", "E-bike diagnostics (motor cutting out)", 3.5, "booked", 3, []),
    (4485, "Thanh Nguyen", "Dev", "Headset replacement", 1.0, "booked", 1, [("HDS-FSA-118", 1)]),
    (4487, "Luca Rossi", "Dev", "Gear tune, new cables + bar tape", 3.0, "booked", 4, [("CAB-SH-GEAR", 1), ("TAPE-BAR-BLK", 1)]),
    # Ravi: 22.0 hours against 30
    (4475, "Sofia Ferreira", "Ravi", "Full service", 3.0, "booked", 1, []),
    (4476, "Aoife O'Brien", "Ravi", "Full service", 3.0, "booked", 2, []),
    (4479, "Karim Haddad", "Ravi", "Tubeless setup", 1.5, "in progress", 0, []),
    (4480, "Yuki Tanaka", "Ravi", "Headset swap", 2.0, "booked", 4, [("HDS-FSA-118", 1)]),
    (4488, "Jana Novak", "Ravi", "Suspension fork service", 4.0, "booked", 3, []),
    (4489, "Arthur Pemberton", "Ravi", "Full restoration (1978 Raleigh)", 6.0, "waiting on parts", 4, []),
    (4490, "Kwame Mensah", "Ravi", "Bottom bracket replacement", 1.5, "booked", 1, [("BB-SH-HT2", 1)]),
    (4491, "Zara Ali", "Ravi", "Puncture repair + new tube", 0.5, "booked", 0, [("TUB-700-25", 1)]),
    (4492, "Sean Brennan", "Ravi", "Cable replacement", 0.5, "booked", 2, []),
    # done, waiting to be collected
    (4460, "Gareth Hughes", "Ravi", "Full service", 3.0, "ready", -1, []),
    (4462, "Marisol Delgado", "Dev", "New chain + cassette", 1.0, "ready", -1, []),
    (4465, "Niamh Fitzgerald", "Ravi", "Brake pads", 0.5, "ready", 0, []),
    (4468, "Chidi Okonkwo", "Dev", "Wheel true", 0.5, "ready", 0, []),
]

HISTORY = [  # collected jobs: customer, work, days ago, amount, paid
    ("Douglas Fairbairn", "Full service", 540, 49.99, 1), ("Helen Marsh", "New tyres", 430, 104.00, 1),
    ("Ibrahim Yusuf", "Puncture repair", 700, 12.00, 1), ("Greta Lindholm", "Brake service", 395, 35.00, 1),
    ("Patrick Doyle", "Full service", 1100, 39.99, 1), ("Mei Chen", "Gear tune", 460, 25.00, 1),
    ("Tom Whitfield", "Puncture repair", 30, 12.00, 1), ("Rachel Okafor", "Full service", 200, 49.99, 1),
    ("Gareth Hughes", "Wheel true", 90, 18.00, 0), ("Luca Rossi", "Bar tape", 60, 28.00, 0),
    ("Karim Haddad", "Brake pads", 0, 19.00, 1), ("Sofia Ferreira", "Tyre fitting", 0, 64.00, 1),
    ("Aoife O'Brien", "Full service", 120, 49.99, 0),
]


def seed():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.init_db()
    t = date.fromisoformat(db.today())
    d = lambda n: (t + timedelta(days=n)).isoformat()  # noqa: E731
    con = db.connect()
    cust_ids, bike_ids = {}, {}
    for name, phone, email, joined, ago in CUSTOMERS:
        cur = con.execute("INSERT INTO customers (name, phone, email, joined, last_visit) VALUES (?,?,?,?,?)",
                          (name, phone, email, joined, d(-ago)))
        cust_ids[name] = cur.lastrowid
        if name in BIKES:
            make, model, colour = BIKES[name]
            bike_ids[name] = con.execute("INSERT INTO bikes (customer_id, make, model, colour) VALUES (?,?,?,?)",
                                         (cust_ids[name], make, model, colour)).lastrowid
    mech_ids = {}
    for name, cap, started in MECHANICS:
        mech_ids[name] = con.execute("INSERT INTO mechanics (name, weekly_capacity_hours, started) VALUES (?,?,?)",
                                     (name, cap, started or d(0))).lastrowid
    part_ids = {}
    for sku, name, stock, reorder, supplier, cost in PARTS:
        part_ids[sku] = con.execute(
            "INSERT INTO parts (sku, name, stock, reorder_level, supplier, unit_cost) VALUES (?,?,?,?,?,?)",
            (sku, name, stock, reorder, supplier, cost)).lastrowid
    for job_id, cust, mech, work, hours, status, due, parts in JOBS:
        con.execute("INSERT INTO jobs (id, customer_id, bike_id, mechanic_id, work, estimate_hours, status, due_date, created) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (job_id, cust_ids[cust], bike_ids.get(cust), mech_ids[mech], work, hours, status, d(due), d(min(due, 0) - 5)))
        for sku, qty in parts:
            con.execute("INSERT INTO job_parts (job_id, part_id, qty) VALUES (?,?,?)", (job_id, part_ids[sku], qty))
    next_id = 4300
    for cust, work, ago, amount, paid in HISTORY:
        next_id += 1
        con.execute("INSERT INTO jobs (id, customer_id, bike_id, mechanic_id, work, estimate_hours, status, due_date, created) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (next_id, cust_ids[cust], bike_ids.get(cust), mech_ids["Ravi"], work, 1.0, "collected", d(-ago), d(-ago - 2)))
        con.execute("INSERT INTO invoices (job_id, amount, paid, created) VALUES (?,?,?,?)",
                    (next_id, amount, paid, d(-ago) + " 16:30:00"))
    for part, qty, supplier, ago in [("CHN-KMC-X11", 10, "Madison", 21), ("TYR-GP5K-28", 8, "Continental UK", 14)]:
        con.execute("INSERT INTO purchase_orders (part_id, quantity, supplier, status, created) VALUES (?,?,?,?,?)",
                    (part_ids[part], qty, supplier, "received", d(-ago) + " 10:15:00"))
    for cust, msg, ago in [("Tom Whitfield", "Hi Tom, your Brompton is ready to collect. Spokes & Sprockets", 30),
                           ("Rachel Okafor", "Hi Rachel, your rims have arrived, wheel build booked for next week. S&S", 4)]:
        con.execute("INSERT INTO notifications (customer_id, job_id, channel, message, sent_at) VALUES (?,?,?,?,?)",
                    (cust_ids[cust], None, "sms", msg, d(-ago) + " 11:02:00"))
    con.commit()
    con.close()
    return {"db": db.DB_PATH, "today": d(0), "customers": len(CUSTOMERS), "jobs": len(JOBS) + len(HISTORY)}


if __name__ == "__main__":
    print(seed())
