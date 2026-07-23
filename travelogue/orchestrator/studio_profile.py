"""Studio-specific orchestration profile (M-B2 · PRD §5.1.2 S2)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

PersistCallback = Callable[[], None]
AssetAddedCallback = Callable[[dict], None]
IngestProgressCallback = Callable[[int, int], None]
CullHintCallback = Callable[[str], None]
IngestCompleteCallback = Callable[[dict], None]


@dataclass
class IngestProfile:
    """Ingest option group aligned with studio_pipeline.py."""

    featured_dir: Path | None = None
    material_dir: Path | None = None
    resume_ingest: bool = False
    generate_crops: bool | None = None
    max_photos: int | None = None
    on_progress: IngestProgressCallback | None = None
    on_cull_hint: CullHintCallback | None = None
    on_persist: PersistCallback | None = None
    on_asset_added: AssetAddedCallback | None = None
    on_complete: IngestCompleteCallback | None = None
    use_parallel_embed: bool = False


@dataclass
class StudioProfile:
    """Parameter surface for unified run_trip (Studio + CLI)."""

    run_clustering: bool = False
    run_shot_grouping: bool | None = None  # None → follow run_clustering (D-SSG-26)
    apply_editorial_hints: bool = False
    export_layout: str = "mobile"
    apply_layout_on_curate: bool = True
    ingest: IngestProfile = field(default_factory=IngestProfile)

    def should_run_shot_grouping(self) -> bool:
        if self.run_shot_grouping is None:
            return bool(self.run_clustering)
        return bool(self.run_shot_grouping)

    @classmethod
    def cli_default(cls) -> StudioProfile:
        return cls()

    @classmethod
    def studio_default(cls) -> StudioProfile:
        return cls(
            run_clustering=True,
            run_shot_grouping=True,
            apply_editorial_hints=True,
            export_layout="auto",
            ingest=IngestProfile(resume_ingest=True, use_parallel_embed=True),
        )
