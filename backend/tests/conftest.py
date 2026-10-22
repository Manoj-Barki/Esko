import io, os, sys
from pathlib import Path
import pymupdf, pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
FOLD_X = 300


def _png(px: int) -> bytes:
    im = Image.effect_noise((px, px), 80).convert("RGB")
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()


def _page(doc):
    return doc.new_page(width=595, height=842)


def _fold(page):
    page.draw_line((FOLD_X, 50), (FOLD_X, 800), color=(1, 0, 1), width=1, dashes="[4 3] 0")


@pytest.fixture
def low_res_pdf(tmp_path):
    d = pymupdf.open(); p = _page(d)
    p.insert_image(pymupdf.Rect(72, 72, 432, 432), stream=_png(300))
    f = tmp_path / "lowres.pdf"; d.save(f); return f


@pytest.fixture
def fold_crossing_pdf(tmp_path):
    d = pymupdf.open(); p = _page(d); _fold(p)
    p.insert_text((220, 400), "FRESH GRANOLA", fontsize=24)
    p.insert_text((60, 600), "Far from the fold", fontsize=12)
    f = tmp_path / "fold.pdf"; d.save(f); return f


@pytest.fixture
def edge_text_pdf(tmp_path):
    d = pymupdf.open(); p = _page(d)
    p.insert_text((3, 100), "TOO CLOSE TO EDGE", fontsize=10)
    f = tmp_path / "edge.pdf"; d.save(f); return f


@pytest.fixture
def clean_pdf(tmp_path):
    d = pymupdf.open(); p = _page(d); _fold(p)
    p.insert_image(pymupdf.Rect(72, 72, 144, 144), stream=_png(300))
    p.insert_text((80, 400), "Clean artwork text", fontsize=12)
    f = tmp_path / "clean.pdf"; d.save(f); return f


@pytest.fixture
def rotated_pdf(tmp_path):
    d = pymupdf.open(); p = _page(d)
    p.insert_text((100, 200), "ROTATED", fontsize=20)
    p.set_rotation(90)
    f = tmp_path / "rot.pdf"; d.save(f); return f


@pytest.fixture
def png_file(tmp_path):
    f = tmp_path / "art.png"; f.write_bytes(_png(400)); return f


@pytest.fixture
def storage_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINTGUARD_STORAGE", str(tmp_path / "store"))
