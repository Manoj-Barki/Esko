from config import load_config
from services.pdf_inspector import inspect_pdf


def geom(r, rule): return [f for f in r.findings if f.rule_id == rule]


def test_text_crossing_fold_detected(fold_crossing_pdf):
    r = inspect_pdf(fold_crossing_pdf, load_config())
    g = geom(r, "GEOM-001")
    assert len(g) == 1
    assert "FRESH GRANOLA" in g[0].observed and g[0].status == "needs_review"
    x, y, w, h = g[0].bbox
    assert x < 300 / 595 < x + w


def test_configured_color_raises_confidence_and_severity(fold_crossing_pdf):
    r = inspect_pdf(fold_crossing_pdf, load_config({"dieline_colors": [[1, 0, 1]]}))
    assert geom(r, "GEOM-001")[0].severity == "critical"


def test_no_dieline_means_unavailable_not_pass(edge_text_pdf):
    r = inspect_pdf(edge_text_pdf, load_config())
    assert next(c for c in r.checks if c.rule_id == "GEOM-001").status == "unavailable"


def test_safe_area_violation(edge_text_pdf):
    assert len(geom(inspect_pdf(edge_text_pdf, load_config()), "SAFE-001")) == 1


def test_safe_area_respects_config(edge_text_pdf):
    r = inspect_pdf(edge_text_pdf, load_config({"safe_margin_mm": 0.1}))
    assert not geom(r, "SAFE-001")


def test_clean_artwork_no_false_alarms(clean_pdf):
    r = inspect_pdf(clean_pdf, load_config())
    assert r.findings == []
    assert r.summary["checks"]["failed"] == 0


def test_rotated_page_coordinates(rotated_pdf):
    r = inspect_pdf(rotated_pdf, load_config())
    p = r.pages[0]
    assert (p.width, p.height) == (842, 595) and p.rotation == 90
    for f in r.findings:
        x, y, w, h = f.bbox
        assert 0 <= x <= 1 and 0 <= y <= 1 and x + w <= 1.001 and y + h <= 1.001
