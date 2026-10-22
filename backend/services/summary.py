from __future__ import annotations
import time
from schemas import CheckResult, FileMeta, Finding, InspectionResult, PageInfo

_SEV = {"critical": 0, "warning": 1, "info": 2}


def finalize(*, inspection_id: str, started: float, findings: list[Finding], checks: list[CheckResult],
             file: FileMeta, pages: list[PageInfo]) -> InspectionResult:
    findings = sorted(findings, key=lambda f: (f.page, _SEV[f.severity], f.bbox[1], f.bbox[0]))
    for i, f in enumerate(findings, 1):
        f.id = f"PG-{i:03d}"
    summary = {
        "findings_total": len(findings),
        "by_severity": {s: sum(f.severity == s for f in findings) for s in _SEV},
        "checks": {s: sum(c.status == s for c in checks) for s in ("passed", "failed", "skipped", "unavailable")},
    }
    return InspectionResult(id=inspection_id, file=file, pages=pages, findings=findings, checks=checks,
                            summary=summary, duration_ms=int((time.perf_counter() - started) * 1000))
