# tests for the API. each test gets a freshly seeded throwaway database (see conftest.py).
# "today" is fixed to Monday 2026-11-23, so "tomorrow" is 2026-11-24.


def test_open_jobs(client):
    jobs = client.get("/api/jobs/open").json()
    assert len(jobs) == 22
    assert {"job_id", "mechanic", "estimate_hours", "status", "due_date", "customer"} <= set(jobs[0])


def test_jobs_due_tomorrow(client):
    jobs = client.get("/api/jobs/due/2026-11-24").json()
    assert sorted(j["job_id"] for j in jobs) == [4471, 4475, 4478, 4485, 4490]


def test_jobs_due_today_word(client):
    jobs = client.get("/api/jobs/due/today").json()
    assert all(j["due_date"] == "2026-11-23" for j in jobs)


def test_job_detail_has_parts(client):
    body = client.get("/api/jobs/4478").json()
    assert body["ok"] is True
    pads = [p for p in body["parts"] if p["sku"] == "BP-SH-RES"][0]
    assert pads["qty_needed"] == 2 and pads["in_stock"] == 1


def test_job_detail_missing(client):
    assert client.get("/api/jobs/999").json() == {"ok": False, "error": "No job #999"}


def test_set_status(client):
    r = client.post("/api/jobs/4460/status", json={"status": "collected"}).json()
    assert r == {"ok": True, "job_id": 4460, "old_status": "ready", "new_status": "collected"}


def test_set_status_rejects_unknown(client):
    assert client.post("/api/jobs/4460/status", json={"status": "finished"}).json()["ok"] is False


def test_assign(client):
    r = client.post("/api/jobs/4471/assign", json={"mechanic": "Priya"}).json()
    assert r == {"ok": True, "job_id": 4471, "from_mechanic": "Dev", "to_mechanic": "Priya"}


def test_book_job_defaults(client):
    r = client.post("/api/jobs", json={"customer_id": 1, "work": "Puncture", "estimate_hours": 0.5,
                                       "due_date": None, "mechanic": None, "bike_id": None}).json()
    assert r["ok"] is True
    assert client.get(f"/api/jobs/{r['job_id']}").json()["job"]["due_date"] == "2026-11-23"


def test_customer_search_and_detail(client):
    found = client.get("/api/customers/search/okafor").json()
    assert found[0]["name"] == "Rachel Okafor"
    detail = client.get(f"/api/customers/{found[0]['id']}").json()
    assert detail["ok"] is True and detail["bikes"][0]["make"] == "Genesis"


def test_notify_defaults_to_sms(client):
    r = client.post("/api/customers/1/notify", json={"message": "Your bike is ready", "channel": None, "job_id": None}).json()
    assert r["ok"] is True and r["channel"] == "sms"
    assert client.get("/api/notifications/recent").json()[0]["message"] == "Your bike is ready"


def test_parts_low(client):
    low = {p["sku"] for p in client.get("/api/parts/low").json()}
    assert {"BP-SH-RES", "TUB-700-25", "SPK-DT-292", "CAS-11-32"} <= low


def test_purchase_order_and_receive(client):
    po = client.post("/api/purchase-orders", json={"part_id": 1, "quantity": 10, "supplier": None}).json()
    assert po["ok"] is True and po["supplier"] == "Madison"
    rec = client.post(f"/api/purchase-orders/{po['purchase_order_id']}/receive").json()
    assert rec == {"ok": True, "purchase_order_id": po["purchase_order_id"], "part": "Brake pads (Shimano resin, pair)", "new_stock": 11}


def test_adjust_stock_cannot_go_negative(client):
    assert client.post("/api/parts/4/adjust", json={"change": -1, "reason": None}).json()["ok"] is False


def test_mechanics(client):
    names = [m["name"] for m in client.get("/api/mechanics").json()]
    assert names == ["Dev", "Ravi", "Priya"]


def test_invoices(client):
    assert len(client.get("/api/invoices/unpaid").json()) == 3
    assert client.post("/api/invoices", json={"job_id": 4460, "amount": 49.99}).json()["ok"] is True


def test_reports(client):
    stats = client.get("/api/reports/today").json()
    assert stats["ready_to_collect"] == 4 and stats["today"] == "2026-11-23"
    takings = client.get("/api/reports/takings/today").json()
    assert takings == {"day": "2026-11-23", "invoices": 2, "total": 83.0}


def test_cancel_job(client):
    assert client.delete("/api/jobs/4492").json()["ok"] is True
    assert client.get("/api/jobs/4492").json()["ok"] is False


def test_pages_render(client):
    for path in ["/", "/customers", "/parts", "/purchase-orders", "/mechanics", "/invoices", "/reports"]:
        r = client.get(path)
        assert r.status_code == 200 and "Spokes &amp; Sprockets" in r.text
