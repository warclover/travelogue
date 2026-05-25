"""Load config.yaml (see config.yaml.example)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from travelogue.paths import ROOT

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from travelogue.llm.presets import PROVIDER_PRESETS


@dataclass
class IngestConfig:
    max_photos: int = 250
    webp_widths: tuple[int, ...] = (800, 1600, 2400)
    webp_quality: int = 82
    generate_crops: bool = False
    min_edge_px: int = 320
    phash_threshold: int = 8
    burst_seconds: float = 3.0
    dedupe_phash: bool = True
    dedupe_burst: bool = True
    min_long_edge_layout_px: int = 800
    min_short_edge_layout_px: int = 600
    low_res_median_ratio: float = 0.55
    low_res_peak_ratio: float = 0.42
    detect_faces: bool = True
    face_min_size_px: int = 48


@dataclass
class VisionConfig:
    enabled: bool = False


@dataclass
class ExportConfig:
    max_zip_mb: int = 25


@dataclass
class NarrativeConfig:
    tone_default: str = "relaxed"
    max_auto_fix_retries: int = 2
    banned_phrases: tuple[str, ...] = ()


@dataclass
class LlmConfig:
    provider: str = "stub"  # stub | deepseek | dashscope
    model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"
    base_url: str | None = None
    timeout_sec: int = 120


@dataclass
class LayoutConfig:
    """Web layout engine default when exportLayout is web (see docs/web端模板升级计划.md)."""
    web_layout_engine: str = "screens"  # legacy | screens
    screen_plan_scope: str = "day"  # chapter | day — day = 按策展日桶全序列组屏
    mixed_proximity_seconds: float = 12.0  # 1竖+2横混排 takenAt 跨度上限


@dataclass
class AppConfig:
    trips_dir: Path = field(default_factory=lambda: ROOT / "trips")
    ingest: IngestConfig = field(default_factory=IngestConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    narrative: NarrativeConfig = field(default_factory=NarrativeConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)


def _ingest_from_dict(raw: dict[str, Any]) -> IngestConfig:
    widths = raw.get("webp_widths") or [800, 1600, 2400]
    return IngestConfig(
        max_photos=int(raw.get("max_photos", 250)),
        webp_widths=tuple(int(w) for w in widths),
        webp_quality=int(raw.get("webp_quality", 82)),
        generate_crops=bool(raw.get("generate_crops", False)),
        min_edge_px=int(raw.get("min_edge_px", 320)),
        phash_threshold=int(raw.get("phash_threshold", 8)),
        burst_seconds=float(raw.get("burst_seconds", 3.0)),
        dedupe_phash=bool(raw.get("dedupe_phash", True)),
        dedupe_burst=bool(raw.get("dedupe_burst", True)),
        min_long_edge_layout_px=int(raw.get("min_long_edge_layout_px", 800)),
        min_short_edge_layout_px=int(raw.get("min_short_edge_layout_px", 600)),
        low_res_median_ratio=float(raw.get("low_res_median_ratio", 0.55)),
        low_res_peak_ratio=float(raw.get("low_res_peak_ratio", 0.42)),
        detect_faces=bool(raw.get("detect_faces", True)),
        face_min_size_px=int(raw.get("face_min_size_px", 48)),
    )


def load_config(path: Path | None = None) -> AppConfig:
    """Load config.yaml from path, or ./config.yaml, or defaults."""
    candidates = [path, Path.cwd() / "config.yaml", ROOT / "config.yaml"]
    cfg_path = next((p for p in candidates if p and p.is_file()), None)
    data: dict[str, Any] = {}
    if cfg_path and yaml is not None:
        with cfg_path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                data = loaded
    trips = data.get("trips_dir", "./trips")
    trips_dir = Path(trips)
    if not trips_dir.is_absolute():
        trips_dir = (Path.cwd() / trips_dir).resolve()
    ingest_raw = data.get("ingest") if isinstance(data.get("ingest"), dict) else {}
    layout_raw = data.get("layout") if isinstance(data.get("layout"), dict) else {}
    web_engine = str(layout_raw.get("web_layout_engine", "screens")).strip().lower()
    if web_engine not in ("legacy", "screens"):
        web_engine = "screens"
    scope = str(layout_raw.get("screen_plan_scope", "day")).strip().lower()
    if scope not in ("chapter", "day"):
        scope = "day"
    mixed_gap = float(layout_raw.get("mixed_proximity_seconds", 12.0))
    export_raw = data.get("export") if isinstance(data.get("export"), dict) else {}
    vision_raw = data.get("vision") if isinstance(data.get("vision"), dict) else {}
    narrative_raw = data.get("narrative") if isinstance(data.get("narrative"), dict) else {}
    llm_raw = data.get("llm") if isinstance(data.get("llm"), dict) else {}
    vision_enabled = bool(vision_raw.get("enabled", False))
    banned_raw = narrative_raw.get("banned_phrases") or []
    banned = tuple(str(p) for p in banned_raw if p) if isinstance(banned_raw, list) else ()
    llm_provider = str(llm_raw.get("provider", "stub")).strip().lower()
    if llm_provider not in ("stub", "deepseek", "dashscope"):
        llm_provider = "stub"
    llm_preset = PROVIDER_PRESETS.get(llm_provider, {})
    llm_base = llm_raw.get("base_url")
    llm_base_url = str(llm_base).strip() if llm_base else None
    return AppConfig(
        trips_dir=trips_dir,
        ingest=_ingest_from_dict(ingest_raw),
        export=ExportConfig(max_zip_mb=int(export_raw.get("max_zip_mb", 25))),
        layout=LayoutConfig(
            web_layout_engine=web_engine,
            screen_plan_scope=scope,
            mixed_proximity_seconds=mixed_gap,
        ),
        vision=VisionConfig(enabled=vision_enabled),
        narrative=NarrativeConfig(
            tone_default=str(narrative_raw.get("tone_default", "relaxed")),
            max_auto_fix_retries=int(narrative_raw.get("max_auto_fix_retries", 2)),
            banned_phrases=banned,
        ),
        llm=LlmConfig(
            provider=llm_provider,
            model=str(llm_raw.get("model") or llm_preset.get("default_model", "deepseek-chat")),
            api_key_env=str(llm_raw.get("api_key_env") or llm_preset.get("api_key_env", "DEEPSEEK_API_KEY")),
            base_url=llm_base_url,
            timeout_sec=int(llm_raw.get("timeout_sec", 120)),
        ),
    )


def default_web_layout_engine(export_layout: str) -> str:
    """Resolve layoutEngine when not set on trip (config + exportLayout)."""
    if export_layout not in ("web", "auto"):
        return "legacy"
    cfg = get_config()
    if cfg.layout.web_layout_engine == "screens":
        return "screens"
    return "legacy"


def default_screen_plan_scope() -> str:
    return get_config().layout.screen_plan_scope


def default_mixed_proximity_seconds() -> float:
    return get_config().layout.mixed_proximity_seconds


_cached: AppConfig | None = None


def get_config(*, reload: bool = False, path: Path | None = None) -> AppConfig:
    global _cached
    from travelogue.env import load_dotenv_files

    load_dotenv_files()
    if _cached is None or reload:
        _cached = load_config(path)
    return _cached
