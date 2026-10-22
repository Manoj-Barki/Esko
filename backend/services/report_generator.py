from __future__ import annotations
import base64
from html import escape
from pathlib import Path
from schemas import InspectionResult

COLORS = {"critical": "#d92d20", "warning": "#f79009", "info": "#2e90fa"}
CSS = """body{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#1d2939}
.stage{position:relative;display:inline-block;max-width:100%;border:1px solid #d0d5dd}.stage img{display:block;max-width:100%}
.box{position:absolute;border:2px solid;box-sizing:border-box}.box b{position:absolute;top:-1.1em;left:-2px;color:#fff;font-size:11px;padding:0 4px}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #eaecf0;padding:.4rem .6rem;text-align:left;font-size:14px}
.sev{color:#fff;padding:1px 8px;border-radius:9px;font-size:12px}.note{background:#fffaeb;border:1px solid #fedf89;padding:.6rem 1rem;border-radius:6px}
.finding{border:1px solid #eaecf0;border-radius:8px;padding:.8rem 1rem;margin:.8rem 0}"""


def generate_report(result: InspectionResult, preview_dir: Path | None = None) -> bytes:
    e = escape
    out = [f"<!doctype html><meta charset=utf-8><title>PrintGuard report</title><style>{CSS}</style>",
           "<h1>PrintGuard AI inspection report</h1>",
           f"<p><b>File:</b> {e(result.file.filename)} · {result.file.page_count} page(s) · "
           f"{result.duration_ms} ms</p><p class=note>{e(result.disclaimer)}</p>"]
    s = result.summary
    out.append(f"<h2>Summary</h2><p>{s['findings_total']} finding(s): "
               + ", ".join(f"{n} {k}" for k, n in s["by_severity"].items())
               + ". Checks: " + ", ".join(f"{n} {k}" for k, n in s["checks"].items()) + ".</p>")

    out.append("<h2>Checks run</h2><table><tr><th>Rule</th><th>Check</th><th>Status</th><th>Detail</th></tr>")
    for c in result.checks:
        out.append(f"<tr><td>{e(c.rule_id)}</td><td>{e(c.name)}</td><td>{e(c.status)}</td><td>{e(c.detail)}</td></tr>")
    out.append("</table>")

    for page in result.pages:
        out.append(f"<h2>Page {page.number}</h2><div class=stage>")
        img = (preview_dir / f"page_{page.number}.png") if preview_dir else None
        if img and img.exists():
            out.append(f"<img src='data:image/png;base64,{base64.b64encode(img.read_bytes()).decode()}'>")
        else:
            out.append("<div style='width:600px;height:800px;background:#f2f4f7'></div>")
        for f in (f for f in result.findings if f.page == page.number):
            x, y, w, h = f.bbox
            col = COLORS[f.severity]
            out.append(f"<div class=box style='left:{x*100}%;top:{y*100}%;width:{w*100}%;height:{h*100}%;border-color:{col}'>"
                       f"<b style='background:{col}'>{e(f.id[3:].lstrip('0') or '0')}</b></div>")
        out.append("</div>")

    out.append("<h2>Findings</h2>")
    for f in result.findings:
        m = ", ".join(f"{k}: {v}" for k, v in f.evidence.measurements.items())
        out.append(f"<div class=finding><h3>{e(f.id)} · {e(f.title)} <span class=sev style='background:{COLORS[f.severity]}'>"
                   f"{f.severity}</span></h3><p><b>Status:</b> {f.status} · <b>Confidence:</b> {f.confidence:.2f} · "
                   f"<b>Rule:</b> {e(f.rule_id)} · page {f.page}</p>"
                   f"<p><b>Observed:</b> {e(f.observed)}<br><b>Expected:</b> {e(f.expected)}</p>"
                   f"<p><b>Evidence:</b> {e(f.evidence.source)} — {e(f.evidence.reference)}<br><small>{e(m)}</small></p>"
                   f"<p>{e(f.explanation)}</p><p><b>Recommended action:</b> {e(f.recommendation)}</p></div>")
    if not result.findings:
        out.append("<p>No findings from the implemented checks (see 'Checks run' for what could not be evaluated).</p>")
    return "".join(out).encode("utf-8")
