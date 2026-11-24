# app.py - Spokes & Sprockets back office v2.3
# Theo H. started March 2009, ported from the old access database. run:  uvicorn app:app --port 8101
# The JSON API lives in the routes_*.py files. The pages below are for the shop computer.
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import routes_customers
import routes_jobs
import routes_mechanics
import routes_money
import routes_parts
import routes_reports
import services
from db import init_db, today

HERE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Spokes & Sprockets back office", version="2.3")
for r in (routes_jobs, routes_customers, routes_parts, routes_mechanics, routes_money, routes_reports):
    app.include_router(r.router)

app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(HERE, "templates"))

init_db()


def _page(request, name, active, **ctx):
    return templates.TemplateResponse(request, name, {"active": active, "today": today(), **ctx})


def jobs_page(request: Request):
    jobs = services.list_open_jobs()
    week_start, week_end = services.week_bounds()
    return _page(request, "jobs.html", "jobs", jobs=jobs, stats=services.shop_stats(),
                 week_start=week_start, week_end=week_end, texts=services.recent_notifications(5))


def customers_page(request: Request):
    from db import connect
    con = connect()
    customers = con.execute("SELECT * FROM customers ORDER BY name").fetchall()
    con.close()
    return _page(request, "customers.html", "customers", customers=customers)


def parts_page(request: Request):
    return _page(request, "parts.html", "parts", parts=services.list_parts())


def purchase_orders_page(request: Request):
    return _page(request, "purchase_orders.html", "purchase-orders", orders=services.list_purchase_orders())


def mechanics_page(request: Request):
    return _page(request, "mechanics.html", "mechanics", mechanics=services.list_mechanics())


def invoices_page(request: Request):
    return _page(request, "invoices.html", "invoices", invoices=services.unpaid_invoices())


def reports_page(request: Request):
    return _page(request, "reports.html", "reports", stats=services.shop_stats(), takings=services.takings_on(today()))


# pages (the old site's URLs)
for path, fn in [("/", jobs_page), ("/jobs", jobs_page), ("/customers", customers_page), ("/parts", parts_page),
                 ("/purchase-orders", purchase_orders_page), ("/mechanics", mechanics_page),
                 ("/invoices", invoices_page), ("/reports", reports_page)]:
    app.add_api_route(path, fn, methods=["GET"], include_in_schema=False)
