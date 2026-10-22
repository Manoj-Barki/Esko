from config import load_config
from services.pdf_inspector import inspect_pdf
from services.image_inspector import inspect_image


def test_low_res_detected_with_location(low_res_pdf):
    r = inspect_pdf(low_res_pdf, load_config())
    f = [x for x in r.findings if x.rule_id == "RES-001"]
    assert len(f) == 1 and f[0].severity == "critical"
    assert abs(f[0].evidence.measurements["dpi_x"] - 60) < 1
    x, y, w, h = f[0].bbox
    assert abs(x - 72 / 595) < 0.01 and abs(w - 360 / 595) < 0.01 and abs(y - 72 / 842) < 0.01


def test_clean_has_no_resolution_finding(clean_pdf):
    assert not [f for f in inspect_pdf(clean_pdf, load_config()).findings if f.rule_id == "RES-001"]


def test_raster_without_size_is_unavailable_not_passed(png_file):
    r = inspect_image(png_file, load_config())
    res = next(c for c in r.checks if c.rule_id == "RES-001")
    assert res.status == "unavailable" and not r.findings


def test_raster_with_target_width_is_checked(png_file):
    r = inspect_image(png_file, load_config({"image_target_width_mm": 254}))
    assert r.findings and r.findings[0].severity == "critical"
