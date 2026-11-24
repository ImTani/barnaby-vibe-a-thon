import os
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

# a throwaway database and a fixed "today" (a Monday) so tests never depend on the real date
_tmp = tempfile.mkdtemp(prefix="spokes-test-")
os.environ["SPOKES_DB"] = os.path.join(_tmp, "test.db")
os.environ["SPOKES_TODAY"] = "2026-11-23"


@pytest.fixture()
def client():
    import db
    import seed
    db.DB_PATH = os.environ["SPOKES_DB"]
    seed.seed()
    from fastapi.testclient import TestClient
    import app as shop_app
    return TestClient(shop_app.app)
