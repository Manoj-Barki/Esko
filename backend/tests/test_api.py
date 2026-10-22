from fastapi.testclient import TestClient
import main


def client(storage_env): return TestClient(main.app)


def test_end_to_end(storage_env, low_res_pdf):
    c = client(storage_env)
    r = c.post("/api/inspect", files={"file": ("a.pdf", low_res_pdf.read_bytes(), "application/pdf")})
    assert r.status_code == 200
    body = r.json(); iid = body["id"]
    assert body["findings"][0]["id"] == "PG-001"
    assert c.get(f"/api/inspections/{iid}").json()["summary"]["findings_total"] == 1
    assert c.get(f"/api/inspections/{iid}/pages/1").headers["content-type"] == "image/png"
    rep = c.get(f"/api/inspections/{iid}/report")
    assert rep.status_code == 200 and b"PG-001" in rep.content
    up = c.patch(f"/api/inspections/{iid}/findings/PG-001", json={"status": "false_positive"})
    assert up.json()["findings"][0]["status"] == "false_positive"


def test_image_upload(storage_env, png_file):
    r = client(storage_env).post("/api/inspect", files={"file": ("a.png", png_file.read_bytes(), "image/png")})
    assert r.status_code == 200 and r.json()["file"]["kind"] == "image"


def test_corrupt_pdf_safe_error(storage_env):
    r = client(storage_env).post("/api/inspect", files={"file": ("x.pdf", b"%PDF-1.4 garbage", "application/pdf")})
    assert r.status_code == 422


def test_wrong_type_rejected(storage_env):
    r = client(storage_env).post("/api/inspect", files={"file": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_oversized_rejected(storage_env, monkeypatch):
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 100)
    r = client(storage_env).post("/api/inspect", files={"file": ("x.pdf", b"%PDF" + b"0" * 500, "application/pdf")})
    assert r.status_code == 413
