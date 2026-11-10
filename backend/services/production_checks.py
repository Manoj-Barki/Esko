"""
Production-ready validation checks for packaging prepress.
Implements industry-standard validation for bleed, trim marks, fonts, overprints, and text legibility.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import pymupdf
from pathlib import Path

from schemas import Finding, CheckStatus
from config import Config


# Industry standards
MIN_BLEED_MM = 3.0  # Standard bleed for packaging
MIN_BLEED_INCH = 0.118  # 3mm in inches
MIN_TEXT_PT_GENERAL = 6.0  # Minimum for coated stock
MIN_TEXT_PT_REVERSED = 7.0  # Minimum for reversed/white text
MIN_TEXT_PT_UNCOATED = 8.0  # Minimum for uncoated stock


def mm_to_points(mm: float) -> float:
    """Convert millimeters to PDF points (1 inch = 72 points, 1 inch = 25.4mm)."""
    return (mm / 25.4) * 72


def points_to_mm(points: float) -> float:
    """Convert PDF points to millimeters."""
    return (points / 72) * 25.4


def check_bleed(doc: pymupdf.Document, config: Config) -> tuple[CheckStatus, List[Finding]]:
    """
    Check if document has adequate bleed areas.

    Industry standard: 3mm (0.118 inches) bleed on all sides for packaging.
    Bleed ensures ink extends to the edge after trimming.

    Rule ID: BLEED-001
    """
    findings = []
    min_bleed_pts = mm_to_points(MIN_BLEED_MM)

    try:
        for page_num, page in enumerate(doc, start=1):
            # Get page boxes
            mediabox = page.mediabox  # Full page including bleed
            cropbox = page.cropbox if hasattr(page, 'cropbox') and page.cropbox else page.mediabox
            trimbox = page.bound()  # Actual content area

            # Calculate bleed on each side
            bleed_left = trimbox.x0 - mediabox.x0
            bleed_right = mediabox.x1 - trimbox.x1
            bleed_top = trimbox.y0 - mediabox.y0
            bleed_bottom = mediabox.y1 - trimbox.y1

            # Check each side
            issues = []
            if bleed_left < min_bleed_pts:
                issues.append(f"left: {points_to_mm(bleed_left):.1f}mm")
            if bleed_right < min_bleed_pts:
                issues.append(f"right: {points_to_mm(bleed_right):.1f}mm")
            if bleed_top < min_bleed_pts:
                issues.append(f"top: {points_to_mm(bleed_top):.1f}mm")
            if bleed_bottom < min_bleed_pts:
                issues.append(f"bottom: {points_to_mm(bleed_bottom):.1f}mm")

            if issues:
                severity = "critical" if any(points_to_mm(b) < 1.5 for b in [bleed_left, bleed_right, bleed_top, bleed_bottom]) else "warning"

                findings.append(Finding(
                    id=f"BLEED-001-P{page_num}",
                    rule_id="BLEED-001",
                    page=page_num,
                    severity=severity,
                    title="Insufficient bleed area",
                    message=f"Bleed areas below 3mm industry standard: {', '.join(issues)}",
                    observed=f"Bleed: {', '.join(issues)}",
                    expected=f"Minimum 3mm (0.118 inches) bleed on all sides",
                    explanation="Bleed is the area of ink that extends beyond the trim line. Industry standard for packaging is 3mm to prevent white edges after cutting due to slight misalignment.",
                    recommendation="Extend artwork 3mm beyond trim lines on all sides. Ensure critical content stays within safe area.",
                    confidence=0.95,
                    location=[
                        trimbox.x0 / page.rect.width,
                        trimbox.y0 / page.rect.height,
                        trimbox.width / page.rect.width,
                        trimbox.height / page.rect.height
                    ],
                    evidence={
                        "source": "pdf_boxes",
                        "measurements": {
                            "bleed_left_mm": round(points_to_mm(bleed_left), 2),
                            "bleed_right_mm": round(points_to_mm(bleed_right), 2),
                            "bleed_top_mm": round(points_to_mm(bleed_top), 2),
                            "bleed_bottom_mm": round(points_to_mm(bleed_bottom), 2),
                            "minimum_required_mm": MIN_BLEED_MM
                        }
                    },
                    status="confirmed"
                ))

        status = CheckStatus.failed if findings else CheckStatus.passed
        return (status, findings)

    except Exception as e:
        return (CheckStatus.unavailable, [])


def check_trim_marks(doc: pymupdf.Document, config: Config) -> tuple[CheckStatus, List[Finding]]:
    """
    Check for presence of trim/crop marks.

    Trim marks indicate where the page should be cut. Essential for production.

    Rule ID: TRIM-001
    """
    findings = []

    try:
        for page_num, page in enumerate(doc, start=1):
            # Look for typical trim mark patterns
            # Trim marks are usually thin lines in corners/edges outside trim area
            paths = page.get_drawings()

            # Simple heuristic: look for short lines near page edges
            trim_mark_candidates = 0
            page_width = page.rect.width
            page_height = page.rect.height
            edge_margin = 20  # Points from edge to check

            for path in paths:
                rect = path.get("rect")
                if rect:
                    x0, y0, x1, y1 = rect
                    width = x1 - x0
                    height = y1 - y0

                    # Trim marks are typically small lines near edges
                    is_small = width < 30 or height < 30
                    near_edge = (x0 < edge_margin or x1 > page_width - edge_margin or
                               y0 < edge_margin or y1 > page_height - edge_margin)

                    if is_small and near_edge:
                        trim_mark_candidates += 1

            # If we found few potential trim marks, flag it
            if trim_mark_candidates < 4:  # Expect at least 4 (one per corner)
                findings.append(Finding(
                    id=f"TRIM-001-P{page_num}",
                    rule_id="TRIM-001",
                    page=page_num,
                    severity="info",
                    title="Trim marks not detected",
                    message=f"Expected trim/crop marks not found on page {page_num}",
                    observed=f"{trim_mark_candidates} potential trim marks detected",
                    expected="4 or more trim marks (corners/sides) for production cutting",
                    explanation="Trim marks guide the cutting process in production. Without them, operators must manually align cuts, increasing error risk.",
                    recommendation="Add trim marks using your design software's crop mark feature. Standard placement is 6mm from trim edge.",
                    confidence=0.7,
                    location=[0, 0, 1, 1],
                    evidence={
                        "source": "path_analysis",
                        "measurements": {
                            "trim_mark_candidates": trim_mark_candidates,
                            "expected_minimum": 4
                        }
                    },
                    status="needs_review"
                ))

        status = CheckStatus.passed if not findings else CheckStatus.failed
        return (status, findings)

    except Exception as e:
        return (CheckStatus.unavailable, [])


def check_fonts(doc: pymupdf.Document, config: Config) -> tuple[CheckStatus, List[Finding]]:
    """
    Check if all fonts are embedded or subsetted.

    Missing fonts cause text to display incorrectly or fail at RIP.

    Rule ID: FONT-001
    """
    findings = []

    try:
        # Get all fonts used in document
        fonts_info = {}
        for page_num, page in enumerate(doc, start=1):
            font_list = page.get_fonts(full=True)
            for font in font_list:
                xref, ext, font_type, base_name, name, encoding, embedded = font[:7]

                if name not in fonts_info:
                    fonts_info[name] = {
                        "type": font_type,
                        "embedded": embedded,
                        "pages": []
                    }
                fonts_info[name]["pages"].append(page_num)

        # Check for non-embedded fonts
        non_embedded = [name for name, info in fonts_info.items() if not info["embedded"]]

        if non_embedded:
            for font_name in non_embedded:
                info = fonts_info[font_name]
                pages = info["pages"]

                findings.append(Finding(
                    id=f"FONT-001-{font_name.replace(' ', '_')}",
                    rule_id="FONT-001",
                    page=pages[0],
                    severity="critical",
                    title="Font not embedded",
                    message=f"Font '{font_name}' is not embedded or subsetted",
                    observed=f"Font '{font_name}' referenced but not embedded (used on {len(pages)} page(s))",
                    expected="All fonts embedded or subsetted in PDF for production",
                    explanation="Non-embedded fonts may not be available on the RIP or output device, causing text to display incorrectly or fail to print. PDF/X standards require font embedding.",
                    recommendation=f"Re-export PDF with 'Embed All Fonts' or 'Subset Fonts' enabled. Font appears on pages: {', '.join(map(str, pages[:5]))}{'...' if len(pages) > 5 else ''}",
                    confidence=0.99,
                    location=[0, 0, 1, 1],
                    evidence={
                        "source": "font_list",
                        "measurements": {
                            "font_name": font_name,
                            "font_type": info["type"],
                            "pages_affected": len(pages),
                            "embedded": False
                        }
                    },
                    status="confirmed"
                ))

        status = CheckStatus.failed if findings else CheckStatus.passed
        return (status, findings)

    except Exception as e:
        return (CheckStatus.unavailable, [])


def check_white_overprint(doc: pymupdf.Document, config: Config) -> tuple[CheckStatus, List[Finding]]:
    """
    Detect white elements set to overprint.

    White set to overprint becomes transparent, causing elements to disappear.
    This is a critical error in prepress.

    Rule ID: OVERPRINT-001
    """
    findings = []

    try:
        for page_num, page in enumerate(doc, start=1):
            # Get drawing paths
            paths = page.get_drawings()

            white_overprint_count = 0
            for path in paths:
                # Check fill and stroke colors
                fill = path.get("fill")
                stroke = path.get("color")
                fill_opacity = path.get("fill_opacity", 1.0)

                # White is RGB (1, 1, 1) or CMYK (0, 0, 0, 0)
                is_white_fill = (fill and
                               ((len(fill) == 3 and all(c > 0.95 for c in fill)) or
                                (len(fill) == 4 and all(c < 0.05 for c in fill))))

                is_white_stroke = (stroke and
                                 ((len(stroke) == 3 and all(c > 0.95 for c in stroke)) or
                                  (len(stroke) == 4 and all(c < 0.05 for c in stroke))))

                # Note: PyMuPDF doesn't directly expose overprint settings
                # This is a limitation - we'll flag suspicious white elements
                if (is_white_fill or is_white_stroke) and fill_opacity < 1.0:
                    white_overprint_count += 1

            if white_overprint_count > 0:
                findings.append(Finding(
                    id=f"OVERPRINT-001-P{page_num}",
                    rule_id="OVERPRINT-001",
                    page=page_num,
                    severity="warning",
                    title="Potential white overprint issue",
                    message=f"Found {white_overprint_count} white element(s) with transparency that may cause printing issues",
                    observed=f"{white_overprint_count} white elements with reduced opacity detected",
                    expected="White elements should knock out (not overprint) underlying colors",
                    explanation="White set to overprint becomes transparent in production, causing elements to disappear. This is a common critical error in prepress files.",
                    recommendation="Check white elements in separations preview. Ensure overprint is OFF for white fills and strokes. Use 'Overprint Preview' in Acrobat to verify.",
                    confidence=0.6,
                    location=[0, 0, 1, 1],
                    evidence={
                        "source": "path_analysis",
                        "measurements": {
                            "suspicious_white_elements": white_overprint_count
                        }
                    },
                    status="needs_review"
                ))

        status = CheckStatus.passed if not findings else CheckStatus.failed
        return (status, findings)

    except Exception as e:
        return (CheckStatus.unavailable, [])


def check_small_text(doc: pymupdf.Document, config: Config) -> tuple[CheckStatus, List[Finding]]:
    """
    Check for text smaller than minimum legible sizes.

    Industry standards:
    - General text: 6pt minimum (coated), 8pt (uncoated)
    - Reversed/white text: 7pt minimum
    - Body copy: 8-10pt recommended

    Rule ID: TEXT-001
    """
    findings = []

    try:
        for page_num, page in enumerate(doc, start=1):
            # Extract text with formatting
            blocks = page.get_text("dict").get("blocks", [])

            small_text_instances = []
            for block in blocks:
                if block.get("type") != 0:  # Not text block
                    continue

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue

                        font_size = span.get("size", 0)
                        font_name = span.get("font", "")
                        color = span.get("color", 0)
                        bbox = span.get("bbox", [0, 0, 0, 0])

                        # Determine if text is reversed (light on dark)
                        # Color is integer RGB packed value
                        is_light = color > 0xCCCCCC  # Approximate white/light text

                        min_size = MIN_TEXT_PT_REVERSED if is_light else MIN_TEXT_PT_GENERAL

                        if font_size < min_size and font_size > 0:
                            small_text_instances.append({
                                "text": text[:30] + "..." if len(text) > 30 else text,
                                "size": font_size,
                                "font": font_name,
                                "is_reversed": is_light,
                                "bbox": bbox
                            })

            if small_text_instances:
                # Group by severity
                critical = [t for t in small_text_instances if t["size"] < 5.0]
                warning = [t for t in small_text_instances if 5.0 <= t["size"] < MIN_TEXT_PT_GENERAL]

                if critical or warning:
                    severity = "critical" if critical else "warning"
                    smallest = min(small_text_instances, key=lambda x: x["size"])

                    findings.append(Finding(
                        id=f"TEXT-001-P{page_num}",
                        rule_id="TEXT-001",
                        page=page_num,
                        severity=severity,
                        title="Small text below legibility threshold",
                        message=f"Found {len(small_text_instances)} text instance(s) below minimum size",
                        observed=f"Smallest text: {smallest['size']:.1f}pt ('{smallest['text']}')",
                        expected=f"Minimum {MIN_TEXT_PT_GENERAL}pt for general text, {MIN_TEXT_PT_REVERSED}pt for reversed text, {MIN_TEXT_PT_UNCOATED}pt for uncoated stock",
                        explanation="Small text may be illegible when printed, especially on uncoated substrates or reversed (white on dark). Industry standards ensure readability across viewing distances and substrates.",
                        recommendation=f"Increase text size to at least {MIN_TEXT_PT_GENERAL}pt for body copy. For reversed text, use {MIN_TEXT_PT_REVERSED}pt minimum. Fine print (legal text) may use 5-6pt on coated stock only.",
                        confidence=0.9,
                        location=[
                            smallest["bbox"][0] / page.rect.width,
                            smallest["bbox"][1] / page.rect.height,
                            (smallest["bbox"][2] - smallest["bbox"][0]) / page.rect.width,
                            (smallest["bbox"][3] - smallest["bbox"][1]) / page.rect.height
                        ],
                        evidence={
                            "source": "text_analysis",
                            "measurements": {
                                "total_small_text": len(small_text_instances),
                                "smallest_size_pt": round(smallest["size"], 2),
                                "critical_count": len(critical),
                                "warning_count": len(warning)
                            }
                        },
                        status="confirmed"
                    ))

        status = CheckStatus.failed if findings else CheckStatus.passed
        return (status, findings)

    except Exception as e:
        return (CheckStatus.unavailable, [])


def run_all_production_checks(doc: pymupdf.Document, config: Config) -> tuple[List[CheckStatus], List[Finding]]:
    """Run all production validation checks and return combined results."""
    all_statuses = []
    all_findings = []

    checks = [
        ("Bleed Validation", check_bleed),
        ("Trim Marks", check_trim_marks),
        ("Font Embedding", check_fonts),
        ("White Overprint", check_white_overprint),
        ("Text Legibility", check_small_text),
    ]

    for check_name, check_func in checks:
        try:
            status, findings = check_func(doc, config)
            all_statuses.append(status)
            all_findings.extend(findings)
        except Exception as e:
            print(f"[Production Check] {check_name} failed: {e}")
            all_statuses.append(CheckStatus.unavailable)

    return (all_statuses, all_findings)
