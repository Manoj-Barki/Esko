from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel

RULES_PATH = Path(__file__).parent / "rules" / "default_rules.json"


class Config(BaseModel):
    min_dpi_warning: float = 150
    min_dpi_critical: float = 72
    min_clearance_mm: float = 3.0
    safe_margin_mm: float | None = 3.0
    safe_area_norm: list[float] | None = None
    dieline_colors: list[list[float]] = []
    color_tolerance: float = 0.08
    dieline_layer_names: list[str] = ["dieline", "die line", "cut", "fold", "crease"]
    detect_dashed_as_fold: bool = True
    image_target_width_mm: float | None = None
    preview_zoom: float = 2.0
    max_pages: int = 20


def load_config(override: dict | None = None) -> Config:
    base = json.loads(RULES_PATH.read_text())
    base.update(override or {})
    return Config.model_validate(base)
