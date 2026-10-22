from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional
from schemas import Evidence, Finding

Rect = tuple[float, float, float, float]
Pt = tuple[float, float]
MM_PER_PT = 25.4 / 72


@dataclass
class TextLine:
    bbox: Rect
    text: str
    size: float
    font: str


@dataclass
class ImageRef:
    bbox: Rect
    px_w: int
    px_h: int
    width_pt: Optional[float]
    height_pt: Optional[float]
    ref: str = ""


@dataclass
class PathRef:
    segments: list[tuple[Pt, Pt]]
    bbox: Rect
    dashed: bool
    color: Optional[tuple]
    layer: Optional[str]
    index: int = 0


@dataclass
class PageData:
    number: int
    width: float
    height: float
    rotation: int = 0
    text_lines: list[TextLine] = field(default_factory=list)
    images: list[ImageRef] = field(default_factory=list)
    paths: list[PathRef] = field(default_factory=list)


@dataclass
class DocumentData:
    kind: Literal["pdf", "image"]
    pages: list[PageData]
    physical_size_known: bool


def norm_bbox(r: Rect, page: PageData) -> list[float]:
    x0, x1 = sorted((r[0], r[2]))
    y0, y1 = sorted((r[1], r[3]))
    x0, x1 = max(0.0, x0), min(page.width, x1)
    y0, y1 = max(0.0, y0), min(page.height, y1)
    return [round(x0 / page.width, 5), round(y0 / page.height, 5),
            round(max(0.0, x1 - x0) / page.width, 5), round(max(0.0, y1 - y0) / page.height, 5)]


def make_finding(*, rule_id, title, category, severity, status, page: PageData, rect_pt: Rect,
                 observed, expected, explanation, recommendation, source, reference,
                 measurements=None, confidence) -> Finding:
    return Finding(
        rule_id=rule_id, title=title, category=category, severity=severity, status=status,
        page=page.number, bbox=norm_bbox(rect_pt, page), observed=observed, expected=expected,
        explanation=explanation, recommendation=recommendation, confidence=confidence,
        evidence=Evidence(source=source, reference=reference, measurements=measurements or {}),
    )
