from __future__ import annotations
import asyncio
import json
import os
import sqlite3
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field, model_validator

import db

from config import load_config
from schemas import FindingStatus, InspectionResult
from services.image_inspector import inspect_image
from services.pdf_inspector import inspect_pdf
from services.report_generator import generate_report

MAX_UPLOAD_BYTES = int(os.getenv("PRINTGUARD_MAX_MB", "25")) * 1024 * 1024
PURGE_INTERVAL_S = int(os.getenv("PRINTGUARD_PURGE_MINUTES", "60")) * 60


async def _purge_loop():
    while True:
        try:
            await asyncio.to_thread(db.purge_expired, db_path(), storage())
        except Exception as exc:
            print(f"[purge] failed: {exc}")
        await asyncio.sleep(PURGE_INTERVAL_S)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(_purge_loop())
    yield
    task.cancel()


app = FastAPI(title="PrintGuard AI", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])


def storage() -> Path:
    p = Path(os.getenv("PRINTGUARD_STORAGE", Path(tempfile.gettempdir()) / "printguard"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path() -> Path:
    return storage() / "printguard.db"


def sniff(head: bytes) -> str | None:
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n") or head.startswith(b"\xff\xd8\xff"):
        return "image"
    return None


def _load(insp_id: str) -> InspectionResult:
    if not insp_id.isalnum():
        raise HTTPException(404, "Inspection not found")
    f = storage() / insp_id / "result.json"
    if not f.exists():
        raise HTTPException(404, "Inspection not found")
    return InspectionResult.model_validate_json(f.read_text())


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/inspect", response_model=InspectionResult)
def inspect(file: UploadFile = File(...), config: str | None = Form(None), batch_id: int | None = Form(None)):
    if batch_id is not None and db.get_batch(db_path(), batch_id) is None:
        raise HTTPException(404, "Batch not found")
    try:
        override = json.loads(config) if config else None
        cfg = load_config(override)
    except Exception:
        raise HTTPException(422, "Invalid config JSON")

    insp_id = uuid.uuid4().hex[:12]
    folder = storage() / insp_id
    folder.mkdir(parents=True)
    dest = folder / "upload.bin"
    size = 0
    with dest.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES // 1024 // 1024} MB limit")
            out.write(chunk)
    kind = sniff(dest.read_bytes()[:16])
    if kind is None:
        raise HTTPException(415, "Unsupported file type. Upload PDF, PNG or JPEG.")

    try:
        fn = inspect_pdf if kind == "pdf" else inspect_image
        result = fn(dest, cfg, preview_dir=folder / "previews", inspection_id=insp_id, filename=file.filename)
    except Exception as exc:
        raise HTTPException(422, f"Could not process file: {type(exc).__name__}") from exc
    (folder / "result.json").write_text(result.model_dump_json())
    if batch_id is not None:
        db.link_inspection(db_path(), insp_id, batch_id)
    return result


@app.get("/api/inspections/{insp_id}", response_model=InspectionResult)
def get_inspection(insp_id: str):
    return _load(insp_id)


@app.get("/api/inspections/{insp_id}/pages/{n}")
def get_page(insp_id: str, n: int):
    _load(insp_id)
    img = storage() / insp_id / "previews" / f"page_{n}.png"
    if not img.exists():
        raise HTTPException(404, "Page not found")
    return FileResponse(img, media_type="image/png")


class StatusUpdate(BaseModel):
    status: FindingStatus


@app.patch("/api/inspections/{insp_id}/findings/{finding_id}", response_model=InspectionResult)
def update_finding(insp_id: str, finding_id: str, body: StatusUpdate):
    result = _load(insp_id)
    for f in result.findings:
        if f.id == finding_id:
            f.status = body.status
            (storage() / insp_id / "result.json").write_text(result.model_dump_json())
            return result
    raise HTTPException(404, "Finding not found")


@app.get("/api/inspections/{insp_id}/report")
def get_report(insp_id: str):
    result = _load(insp_id)
    html = generate_report(result, storage() / insp_id / "previews")
    return Response(html, media_type="text/html",
                    headers={"Content-Disposition": f'attachment; filename="printguard-{insp_id}.html"'})


class BatchIn(BaseModel):
    batch_number: str = Field(min_length=1, max_length=64)
    product_name: str | None = Field(None, max_length=200)
    mfg_date: date
    expiry_date: date | None = None
    shelf_life_days: int | None = Field(None, gt=0, le=36500)

    @model_validator(mode="after")
    def _expiry(self):
        if self.expiry_date is None:
            if self.shelf_life_days is None:
                raise ValueError("Provide expiry_date or shelf_life_days")
            self.expiry_date = db.expiry_from_shelf_life(self.mfg_date, self.shelf_life_days)
        if self.expiry_date <= self.mfg_date:
            raise ValueError("expiry_date must be after mfg_date")
        return self


@app.post("/api/batches", status_code=201)
def create_batch(body: BatchIn):
    try:
        return db.create_batch(db_path(), body.batch_number.strip(), body.mfg_date, body.expiry_date, body.product_name)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Batch number already exists")


@app.get("/api/batches")
def list_batches():
    return db.list_batches(db_path())


@app.get("/api/batches/{batch_id}")
def get_batch(batch_id: int):
    b = db.get_batch(db_path(), batch_id)
    if b is None:
        raise HTTPException(404, "Batch not found")
    return b


@app.delete("/api/batches/{batch_id}")
def delete_batch(batch_id: int):
    if not db.delete_batch(db_path(), batch_id, storage()):
        raise HTTPException(404, "Batch not found")
    return {"deleted": True}


@app.post("/api/batches/purge-expired")
def purge_now():
    return {"purged_batches": db.purge_expired(db_path(), storage())}
