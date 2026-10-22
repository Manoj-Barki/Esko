from __future__ import annotations
import time
from pathlib import Path
from PIL import Image, ImageOps

from config import Config
from schemas import FileMeta, InspectionResult, PageInfo
from .document import DocumentData, ImageRef, MM_PER_PT, PageData
from .geometry_checks import check_geometry
from .resolution_checks import check_resolution
from .summary import finalize

Image.MAX_IMAGE_PIXELS = 100_000_000


def inspect_image(path, config: Config, preview_dir: Path | None = None,
                  inspection_id: str = "local", filename: str | None = None) -> InspectionResult:
    t0 = time.perf_counter()
    path = Path(path)
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        w, h = im.size
        if preview_dir is not None:
            preview_dir.mkdir(parents=True, exist_ok=True)
            prev = im.convert("RGB")
            prev.thumbnail((2400, 2400))
            prev.save(preview_dir / "page_1.png")

    target_w_pt = config.image_target_width_mm / MM_PER_PT if config.image_target_width_mm else None
    target_h_pt = target_w_pt * h / w if target_w_pt else None
    page = PageData(number=1, width=float(w), height=float(h))
    page.images.append(ImageRef(bbox=(0, 0, w, h), px_w=w, px_h=h, width_pt=target_w_pt,
                                height_pt=target_h_pt, ref="uploaded raster"))
    document = DocumentData(kind="image", pages=[page], physical_size_known=target_w_pt is not None)

    f1, c1 = check_resolution(document, config)
    f2, c2 = check_geometry(document, config)
    return finalize(
        inspection_id=inspection_id, started=t0, findings=f1 + f2, checks=c1 + c2,
        file=FileMeta(filename=filename or path.name, kind="image", size_bytes=path.stat().st_size,
                      page_count=1, physical_size_known=document.physical_size_known),
        pages=[PageInfo(number=1, width=w, height=h, unit="px",
                        preview_url=f"/api/inspections/{inspection_id}/pages/1")])
