from __future__ import annotations
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_number  TEXT NOT NULL UNIQUE,
    product_name  TEXT,
    mfg_date      TEXT NOT NULL,
    expiry_date   TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_batches_expiry ON batches(expiry_date);
CREATE TABLE IF NOT EXISTS batch_inspections (
    inspection_id TEXT PRIMARY KEY,
    batch_id      INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE
);
"""


@contextmanager
def connect(db_path: Path):
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_batch(db_path: Path, batch_number: str, mfg: date, expiry: date, product_name: str | None) -> dict:
    with connect(db_path) as c:
        cur = c.execute("INSERT INTO batches (batch_number, product_name, mfg_date, expiry_date) VALUES (?,?,?,?)",
                        (batch_number, product_name, mfg.isoformat(), expiry.isoformat()))
        return get_batch_in(c, cur.lastrowid)


def get_batch_in(c: sqlite3.Connection, batch_id: int) -> dict | None:
    row = c.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["inspection_ids"] = [r["inspection_id"] for r in
                           c.execute("SELECT inspection_id FROM batch_inspections WHERE batch_id=?", (batch_id,))]
    d["expired"] = d["expiry_date"] < date.today().isoformat()
    return d


def get_batch(db_path: Path, batch_id: int) -> dict | None:
    with connect(db_path) as c:
        return get_batch_in(c, batch_id)


def list_batches(db_path: Path) -> list[dict]:
    with connect(db_path) as c:
        ids = [r["id"] for r in c.execute("SELECT id FROM batches ORDER BY expiry_date, id")]
        return [get_batch_in(c, i) for i in ids]


def link_inspection(db_path: Path, inspection_id: str, batch_id: int) -> None:
    with connect(db_path) as c:
        c.execute("INSERT OR REPLACE INTO batch_inspections (inspection_id, batch_id) VALUES (?,?)",
                  (inspection_id, batch_id))


def delete_batch(db_path: Path, batch_id: int, storage_dir: Path) -> bool:
    with connect(db_path) as c:
        ids = [r["inspection_id"] for r in
               c.execute("SELECT inspection_id FROM batch_inspections WHERE batch_id=?", (batch_id,))]
        deleted = c.execute("DELETE FROM batches WHERE id=?", (batch_id,)).rowcount > 0
    for iid in ids:
        if iid.isalnum():
            shutil.rmtree(storage_dir / iid, ignore_errors=True)
    return deleted


def purge_expired(db_path: Path, storage_dir: Path, today: date | None = None) -> int:
    cutoff = (today or date.today()).isoformat()
    with connect(db_path) as c:
        batch_ids = [r["id"] for r in c.execute("SELECT id FROM batches WHERE expiry_date < ?", (cutoff,))]
    return sum(delete_batch(db_path, b, storage_dir) for b in batch_ids)


def expiry_from_shelf_life(mfg: date, shelf_life_days: int) -> date:
    return mfg + timedelta(days=shelf_life_days)
