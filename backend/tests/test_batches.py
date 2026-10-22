from datetime import date, timedelta
from fastapi.testclient import TestClient
import db, main


def mk(c, num, mfg, expiry):
    return c.post("/api/batches", json={"batch_number": num, "mfg_date": mfg.isoformat(),
                                        "expiry_date": expiry.isoformat()})


def test_create_and_shelf_life(storage_env):
    c = TestClient(main.app)
    r = c.post("/api/batches", json={"batch_number": "B-1", "mfg_date": "2026-01-01", "shelf_life_days": 180})
    assert r.status_code == 201 and r.json()["expiry_date"] == "2026-06-30"
    assert c.post("/api/batches", json={"batch_number": "B-1", "mfg_date": "2026-01-01",
                                        "shelf_life_days": 10}).status_code == 409
    assert c.post("/api/batches", json={"batch_number": "B-2", "mfg_date": "2026-01-01"}).status_code == 422
    assert c.post("/api/batches", json={"batch_number": "B-3", "mfg_date": "2026-01-01",
                                        "expiry_date": "2025-01-01"}).status_code == 422


def test_expired_batch_and_inspection_are_purged(storage_env, low_res_pdf):
    c = TestClient(main.app)
    today = date.today()
    old = mk(c, "OLD", today - timedelta(days=400), today - timedelta(days=1)).json()
    new = mk(c, "NEW", today, today + timedelta(days=100)).json()
    pdf = low_res_pdf.read_bytes()
    i_old = c.post("/api/inspect", files={"file": ("a.pdf", pdf, "application/pdf")},
                   data={"batch_id": old["id"]}).json()["id"]
    i_new = c.post("/api/inspect", files={"file": ("a.pdf", pdf, "application/pdf")},
                   data={"batch_id": new["id"]}).json()["id"]

    assert c.post("/api/batches/purge-expired").json() == {"purged_batches": 1}
    assert c.get(f"/api/batches/{old['id']}").status_code == 404
    assert c.get(f"/api/inspections/{i_old}").status_code == 404
    assert c.get(f"/api/batches/{new['id']}").status_code == 200
    assert c.get(f"/api/inspections/{i_new}").status_code == 200


def test_batch_kept_through_expiry_day(storage_env):
    c = TestClient(main.app)
    b = mk(c, "TODAY", date.today() - timedelta(days=30), date.today()).json()
    assert c.post("/api/batches/purge-expired").json() == {"purged_batches": 0}
    assert db.purge_expired(main.db_path(), main.storage(), today=date.today() + timedelta(days=1)) == 1


def test_unknown_batch_rejected_on_inspect(storage_env, low_res_pdf):
    r = TestClient(main.app).post("/api/inspect", files={"file": ("a.pdf", low_res_pdf.read_bytes(), "application/pdf")},
                                  data={"batch_id": 999})
    assert r.status_code == 404
