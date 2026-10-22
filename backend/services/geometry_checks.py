from __future__ import annotations
import math
from config import Config
from schemas import CheckResult, Finding
from .document import DocumentData, MM_PER_PT, PageData, PathRef, Pt, Rect, make_finding

GEOM, SAFE = "GEOM-001", "SAFE-001"


def _orient(a: Pt, b: Pt, c: Pt) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _seg_intersect(a: Pt, b: Pt, c: Pt, d: Pt) -> bool:
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def _pt_seg_dist(p: Pt, a: Pt, b: Pt) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def _seg_seg_dist(a: Pt, b: Pt, c: Pt, d: Pt) -> float:
    if _seg_intersect(a, b, c, d):
        return 0.0
    return min(_pt_seg_dist(a, c, d), _pt_seg_dist(b, c, d), _pt_seg_dist(c, a, b), _pt_seg_dist(d, a, b))


def rect_segment_distance(r: Rect, a: Pt, b: Pt) -> float:
    x0, y0, x1, y1 = r
    inside = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    if inside(a) or inside(b):
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return min(_seg_seg_dist(a, b, corners[i], corners[(i + 1) % 4]) for i in range(4))


def _rgb(color) -> tuple | None:
    if color is None:
        return None
    if len(color) == 1:
        return (color[0],) * 3
    return tuple(color) if len(color) == 3 else None


def identify_dielines(page: PageData, config: Config) -> list[tuple[PathRef, str, float, str]]:
    out = []
    for p in page.paths:
        rgb = _rgb(p.color)
        by_color = rgb is not None and any(
            all(abs(c - t) <= config.color_tolerance for c, t in zip(rgb, target))
            for target in config.dieline_colors)
        by_layer = bool(p.layer) and any(n.lower() in p.layer.lower() for n in config.dieline_layer_names)
        if by_color or by_layer:
            out.append((p, "fold" if p.dashed else "dieline", 0.9, "configured colour" if by_color else "layer name"))
        elif config.detect_dashed_as_fold and p.dashed:
            out.append((p, "fold", 0.6, "dashed stroke (heuristic)"))
    return out


def _check_dieline_clearance(document: DocumentData, config: Config):
    findings: list[Finding] = []
    clearance_pt = config.min_clearance_mm / MM_PER_PT
    n_dielines = 0
    for page in document.pages:
        dielines = identify_dielines(page, config)
        n_dielines += len(dielines)
        for line in page.text_lines:
            x0, y0, x1, y1 = line.bbox
            best = None
            for path, kind, conf, basis in dielines:
                px0, py0, px1, py1 = path.bbox
                if px1 < x0 - clearance_pt or px0 > x1 + clearance_pt or \
                   py1 < y0 - clearance_pt or py0 > y1 + clearance_pt:
                    continue
                for a, b in path.segments:
                    d = rect_segment_distance(line.bbox, a, b)
                    if best is None or d < best[0]:
                        best = (d, path, kind, conf, basis)
                    if d == 0:
                        break
            if best is None or best[0] >= clearance_pt:
                continue
            d, path, kind, conf, basis = best
            crossing = d == 0
            explicit = conf >= 0.85
            findings.append(make_finding(
                rule_id=GEOM,
                title=f"Text crosses {kind} line" if crossing else f"Text too close to {kind} line",
                category="geometry",
                severity="critical" if (crossing and explicit) else "warning",
                status="needs_review",
                page=page, rect_pt=line.bbox,
                observed=(f"Text \"{line.text[:40]}\" overlaps a {kind} line" if crossing else
                          f"Text \"{line.text[:40]}\" is {d*MM_PER_PT:.1f} mm from a {kind} line"),
                expected=f"Minimum clearance {config.min_clearance_mm:g} mm (configurable)",
                explanation="Text on or near a cut/fold may be cut through, distorted or hard to read after finishing.",
                recommendation="Verify against the packaging specification and move the text if needed.",
                source="pdf_geometry", reference=f"page {page.number}, path #{path.index}, identified by {basis}",
                measurements={"distance_mm": round(d * MM_PER_PT, 2), "required_mm": config.min_clearance_mm,
                              "line_kind": kind, "line_identification": basis},
                confidence=round(min(0.95, conf + (0.05 if crossing else 0)), 2)))
    if n_dielines == 0:
        chk = CheckResult(rule_id=GEOM, name="Text vs cut/fold lines", status="unavailable",
                          detail="No dieline paths identified. Configure dieline_colors or layer names, or upload the dieline PDF.")
    else:
        chk = CheckResult(rule_id=GEOM, name="Text vs cut/fold lines", status="failed" if findings else "passed",
                          detail=f"{n_dielines} candidate dieline path(s) evaluated")
    return findings, chk


def _safe_rect(page: PageData, config: Config) -> Rect | None:
    if config.safe_area_norm:
        x, y, w, h = config.safe_area_norm
        return (x * page.width, y * page.height, (x + w) * page.width, (y + h) * page.height)
    if config.safe_margin_mm is not None:
        m = config.safe_margin_mm / MM_PER_PT
        return (m, m, page.width - m, page.height - m)
    return None


def _check_safe_area(document: DocumentData, config: Config):
    findings: list[Finding] = []
    evaluated = False
    for page in document.pages:
        safe = _safe_rect(page, config)
        if safe is None:
            continue
        evaluated = True
        for line in page.text_lines:
            x0, y0, x1, y1 = line.bbox
            out_by = max(safe[0] - x0, safe[1] - y0, x1 - safe[2], y1 - safe[3])
            if out_by <= 0.01:
                continue
            findings.append(make_finding(
                rule_id=SAFE, title="Text outside safe area", category="geometry", severity="warning",
                status="confirmed" if config.safe_area_norm else "needs_review", page=page, rect_pt=line.bbox,
                observed=f"Text \"{line.text[:40]}\" extends {out_by*MM_PER_PT:.1f} mm beyond the safe area",
                expected="All text inside the configured safe area",
                explanation="Text near the trim edge risks being clipped by cutting tolerances.",
                recommendation="Move the text inward or confirm the safe area with the printer.",
                source="pdf_geometry", reference=f"page {page.number}, text \"{line.text[:20]}\"",
                measurements={"outside_by_mm": round(out_by * MM_PER_PT, 2),
                              "safe_margin_mm": config.safe_margin_mm},
                confidence=0.9 if config.safe_area_norm else 0.7))
    if not evaluated:
        chk = CheckResult(rule_id=SAFE, name="Text inside safe area", status="unavailable",
                          detail="No safe margin or safe_area_norm configured.")
    else:
        chk = CheckResult(rule_id=SAFE, name="Text inside safe area", status="failed" if findings else "passed",
                          detail="Measured from page edge" if not config.safe_area_norm else "Explicit safe area")
    return findings, chk


def check_geometry(document: DocumentData, config: Config) -> tuple[list[Finding], list[CheckResult]]:
    if document.kind != "pdf" or not any(p.text_lines or p.paths for p in document.pages):
        why = ("Raster upload has no vector geometry. Provide the dieline PDF." if document.kind == "image"
               else "No text or vector geometry could be extracted (image-only PDF?).")
        return [], [CheckResult(rule_id=GEOM, name="Text vs cut/fold lines", status="unavailable", detail=why),
                    CheckResult(rule_id=SAFE, name="Text inside safe area", status="unavailable", detail=why)]
    f1, c1 = _check_dieline_clearance(document, config)
    f2, c2 = _check_safe_area(document, config)
    return f1 + f2, [c1, c2]
