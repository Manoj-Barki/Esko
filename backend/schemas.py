from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

Severity = Literal["critical", "warning", "info"]
FindingStatus = Literal["confirmed", "needs_review", "false_positive", "resolved"]
CheckStatus = Literal["passed", "failed", "skipped", "unavailable"]


class Evidence(BaseModel):
    source: str
    reference: str
    measurements: dict[str, float | str | None] = {}


class Finding(BaseModel):
    id: str = ""
    rule_id: str
    title: str
    category: Literal["resolution", "geometry", "text", "font", "other"]
    severity: Severity
    status: FindingStatus
    page: int
    bbox: list[float] = Field(min_length=4, max_length=4)
    unit: Literal["normalized"] = "normalized"
    observed: str
    expected: str
    evidence: Evidence
    explanation: str
    recommendation: str
    confidence: float


class CheckResult(BaseModel):
    rule_id: str
    name: str
    status: CheckStatus
    detail: str = ""


class PageInfo(BaseModel):
    number: int
    width: float
    height: float
    unit: Literal["pt", "px"]
    rotation: int = 0
    preview_url: str | None = None


class FileMeta(BaseModel):
    filename: str
    kind: Literal["pdf", "image"]
    size_bytes: int
    page_count: int
    physical_size_known: bool


class InspectionResult(BaseModel):
    id: str = ""
    status: Literal["completed", "failed"] = "completed"
    file: FileMeta
    pages: list[PageInfo]
    findings: list[Finding]
    checks: list[CheckResult]
    summary: dict = {}
    disclaimer: str = ("Automated preflight assistant. This is not a certification "
                       "that the artwork is print-ready.")
    duration_ms: int = 0
