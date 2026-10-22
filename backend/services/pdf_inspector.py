from __future__ import annotations
import math
import time
from pathlib import Path
import pymupdf

from config import Config
from schemas import FileMeta, InspectionResult, PageInfo
from .document import DocumentData, ImageRef, PageData, PathRef, TextLine
from .geometry_checks import check_geometry
from .resolution_checks import check_resolution
from .summary import finalize

MAX_SEGMENTS_PER_PAGE = 20000


def _rect(r, rot) -> tuple:
    rr = pymupdf.Rect(r) * rot
    rr.normalize()
    return (rr.x0, rr.y0, rr.x1, rr.y1)


def _pts(points, rot):
    out = []
    for p in points:
        q = pymupdf.Point(p) * rot
        out.append((q.x, q.y))
    return out


def extract_document(path: str | Path, config: Config, preview_dir: Path | None = None) -> DocumentData:
    pages: list[PageData] = []
    with pymupdf.open(str(path)) as doc:
        if doc.needs_pass:
            raise ValueError("PDF is password protected.")
        if doc.page_count == 0:
            raise ValueError("PDF has no pages.")
        for i, page in enumerate(doc):
            if i >= config.max_pages:
                break
            rot = page.rotation_matrix
            pd = PageData(number=i + 1, width=page.rect.width, height=page.rect.height, rotation=page.rotation)

            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    text = "".join(s.get("text", "") for s in spans).strip()
                    if text:
                        pd.text_lines.append(TextLine(
                            bbox=_rect(line["bbox"], rot), text=text,
                            size=max((s.get("size", 0) for s in spans), default=0),
                            font=spans[0].get("font", "") if spans else ""))

            for info in page.get_image_info(xrefs=True):
                a, b, c, d = info.get("transform", (0, 0, 0, 0, 0, 0))[:4]
                w_pt, h_pt = math.hypot(a, b), math.hypot(c, d)
                if w_pt <= 0 or h_pt <= 0:
                    bb = pymupdf.Rect(info["bbox"])
                    w_pt, h_pt = bb.width, bb.height
                pd.images.append(ImageRef(
                    bbox=_rect(info["bbox"], rot), px_w=info["width"], px_h=info["height"],
                    width_pt=w_pt, height_pt=h_pt, ref=f"image xref {info.get('xref', '?')}"))

            seg_count = 0
            for idx, d in enumerate(page.get_drawings()):
                if d.get("color") is None or "s" not in d.get("type", ""):
                    continue
                segs = []
                for it in d["items"]:
                    op = it[0]
                    if op == "l":
                        pts = [it[1], it[2]]
                    elif op == "c":
                        pts = [it[1], it[4]]
                    elif op == "re":
                        r = pymupdf.Rect(it[1])
                        pts = [r.tl, r.tr, r.br, r.bl, r.tl]
                    elif op == "qu":
                        q = it[1]
                        pts = [q.ul, q.ur, q.lr, q.ll, q.ul]
                    else:
                        continue
                    tp = _pts(pts, rot)
                    segs.extend(zip(tp[:-1], tp[1:]))
                if not segs or seg_count + len(segs) > MAX_SEGMENTS_PER_PAGE:
                    continue
                seg_count += len(segs)
                dashes = (d.get("dashes") or "").strip()
                xs = [p[0] for s in segs for p in s]
                ys = [p[1] for s in segs for p in s]
                pd.paths.append(PathRef(
                    segments=segs, bbox=(min(xs), min(ys), max(xs), max(ys)),
                    dashed=bool(dashes) and not dashes.startswith("[]"),
                    color=tuple(d["color"]), layer=d.get("layer"), index=idx))
            pages.append(pd)

            if preview_dir is not None:
                preview_dir.mkdir(parents=True, exist_ok=True)
                page.get_pixmap(matrix=pymupdf.Matrix(config.preview_zoom, config.preview_zoom)) \
                    .save(str(preview_dir / f"page_{i + 1}.png"))
    return DocumentData(kind="pdf", pages=pages, physical_size_known=True)


def inspect_pdf(path, config: Config, preview_dir: Path | None = None,
                inspection_id: str = "local", filename: str | None = None) -> InspectionResult:
    t0 = time.perf_counter()
    path = Path(path)
    document = extract_document(path, config, preview_dir)
    f1, c1 = check_resolution(document, config)
    f2, c2 = check_geometry(document, config)
    return finalize(
        inspection_id=inspection_id, started=t0, findings=f1 + f2, checks=c1 + c2,
        file=FileMeta(filename=filename or path.name, kind="pdf", size_bytes=path.stat().st_size,
                      page_count=len(document.pages), physical_size_known=True),
        pages=[PageInfo(number=p.number, width=p.width, height=p.height, unit="pt", rotation=p.rotation,
                        preview_url=f"/api/inspections/{inspection_id}/pages/{p.number}") for p in document.pages])
