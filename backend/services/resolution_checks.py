from __future__ import annotations
from config import Config
from schemas import CheckResult, Finding
from .document import DocumentData, make_finding

RULE = "RES-001"
NAME = "Effective image resolution"


def check_resolution(document: DocumentData, config: Config) -> tuple[list[Finding], list[CheckResult]]:
    findings: list[Finding] = []
    measured = unknown = total = 0
    for page in document.pages:
        for im in page.images:
            total += 1
            if not im.width_pt or not im.height_pt:
                unknown += 1
                continue
            measured += 1
            dpi_x = im.px_w / (im.width_pt / 72)
            dpi_y = im.px_h / (im.height_pt / 72)
            dpi = min(dpi_x, dpi_y)
            if dpi >= config.min_dpi_warning:
                continue
            critical = dpi < config.min_dpi_critical
            findings.append(make_finding(
                rule_id=RULE, title="Low effective image resolution", category="resolution",
                severity="critical" if critical else "warning", status="confirmed",
                page=page, rect_pt=im.bbox,
                observed=f"Effective resolution is {dpi:.0f} DPI ({im.px_w}x{im.px_h} px placed at "
                         f"{im.width_pt/72:.2f}x{im.height_pt/72:.2f} in)",
                expected=f"At least {config.min_dpi_warning:.0f} DPI (configurable; depends on print process)",
                explanation="The image has too few pixels for its printed size and may look soft or pixelated.",
                recommendation="Replace with a higher-resolution original or reduce the placed size; "
                               "confirm the required DPI with the printer.",
                source="pdf_image_metadata" if document.kind == "pdf" else "raster_image",
                reference=f"page {page.number}, {im.ref or 'image'}",
                measurements={"dpi_x": round(dpi_x, 1), "dpi_y": round(dpi_y, 1),
                              "pixel_width": im.px_w, "pixel_height": im.px_h,
                              "threshold_warning_dpi": config.min_dpi_warning,
                              "threshold_critical_dpi": config.min_dpi_critical},
                confidence=0.95 if document.kind == "pdf" else 0.8))

    if total == 0:
        check = CheckResult(rule_id=RULE, name=NAME, status="skipped", detail="No embedded raster images found.")
    elif measured == 0:
        check = CheckResult(rule_id=RULE, name=NAME, status="unavailable",
                            detail="Physical print size unknown. Set image_target_width_mm to enable this check.")
    else:
        detail = f"{measured} image(s) measured" + (f", {unknown} could not be measured" if unknown else "")
        check = CheckResult(rule_id=RULE, name=NAME, status="failed" if findings else "passed", detail=detail)
    return findings, [check]
