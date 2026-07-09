#!/usr/bin/env python3
"""One-shot M-C2 migration: move remaining top-level tests into unit/integration/e2e."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
BASELINE = ROOT / "docs" / "acceptance-records" / "m-c2-top-level-baseline.txt"

KEEP_TOP = frozenset({"test_ingest.py"})

# prefix -> destination dir under tests/
PREFIX_RULES: list[tuple[str, str]] = [
    ("test_studio_", "unit/web"),
    ("test_aesthetic_", "unit/curation"),
    ("test_cluster", "unit/curation"),
    ("test_curate", "unit/curation"),
    ("test_diff_curate", "unit/curation"),
    ("test_food_grid", "unit/curation"),
    ("test_collage_", "unit/layout_engine"),
    ("test_cover_", "unit/curation"),
    ("test_narrate", "unit/curation"),
    ("test_narrative_", "unit/validate"),
    ("test_scene_", "unit/curation"),
    ("test_portrait_", "unit/curation"),
    ("test_photo_cull", "unit/curation"),
    ("test_solo_scoring", "unit/curation"),
    ("test_peak_moment", "unit/curation"),
    ("test_late_chapter", "unit/curation"),
    ("test_subject_tagging", "unit/curation"),
    ("test_epilogue_", "unit/curation"),
    ("test_optimization_backfill", "unit/curation"),
    ("test_chapter_explain", "unit/curation"),
    ("test_intent_", "unit/curation"),
    ("test_arc_", "unit/curation"),
    ("test_album_profile", "unit/curation"),
    ("test_time_segments", "unit/curation"),
    ("test_burst_priority", "unit/curation"),
    ("test_workshop_pipeline", "unit/curation"),
    ("test_services_cohort", "unit/curation"),
    ("test_cohort_faces", "unit/curation"),
    ("test_copy_", "unit/domain"),
    ("test_guardrails_copy", "unit/domain"),
    ("test_phase15_curate", "unit/curation"),
    ("test_phase16_template", "unit/layout_templates"),
    ("test_phase11_copy", "unit/domain"),
    ("test_phase11_decor", "unit/render"),
    ("test_reading_", "unit/render"),
    ("test_longshot_", "unit/render"),
    ("test_bsp_", "unit/render"),
    ("test_moment_render", "unit/render"),
    ("test_mobile_render", "unit/render"),
    ("test_serve_", "unit/render"),
    ("test_dom_regression", "unit/render"),
    ("test_golden_reference", "unit/render"),
    ("test_preview_toolbar", "unit/web"),
    ("test_breath_image", "unit/render"),
    ("test_llm_", "unit/llm"),
    ("test_image_ops", "unit/media"),
    ("test_phash", "unit/media"),
    ("test_sharpness", "unit/media"),
    ("test_clip_", "unit/media"),
    ("test_blur_fill", "unit/media"),
    ("test_color_metrics", "unit/media"),
    ("test_exposure_metrics", "unit/media"),
    ("test_asset_quality", "unit/media"),
    ("test_asset_caption", "unit/media"),
    ("test_embedding_cache", "unit/media"),
    ("test_subject_detect", "unit/media"),
    ("test_cfg_injection", "unit/config"),
    ("test_env", "unit/config"),
    ("test_algorithm_profile", "unit/config"),
    ("test_chapter_items_screens", "unit/trip"),
    ("test_asset_version", "unit/trip"),
    ("test_lrg_repair", "unit/trip"),
    ("test_screen_tone", "unit/layout_engine"),
    ("test_search_budget", "unit/layout_engine"),
    ("test_six_slot", "unit/layout_engine"),
    ("test_slot_geometry", "unit/layout_engine"),
    ("test_replan_items", "unit/layout_engine"),
    ("test_lrg_dogfood", "unit/layout_engine"),
    ("test_event_recap", "unit/layout_templates"),
    ("test_discovery_sort", "unit/layout_templates"),
    ("test_phase16_template", "unit/layout_templates"),
    ("test_template_", "unit/layout_templates"),
    ("test_p17_", "integration/p17"),
    ("test_pa_acceptance", "integration"),
    ("test_phase", "integration"),
    ("test_demo_", "integration/demo"),
    ("test_e2e_", "integration"),
    ("test_reexport", "integration"),
    ("test_arch_equivalence", "unit/lint"),
    ("test_pytest_markers", "unit/lint"),
    ("test_cli_spec_sync", "unit/lint"),
    ("test_code_error", "unit/lint"),
    ("test_minor_guards", "unit/lint"),
    ("test_rhythm_ci_gate", "unit/layout_engine"),
    ("test_acceptance_docs_hub", "unit/lint"),
    ("test_adaptive_breakpoint", "unit/render"),
    ("test_geocode", "unit/curation"),
    ("test_geo_events", "unit/curation"),
    ("test_feedback", "unit/web"),
    ("test_desktop_m11", "unit/web"),
    ("test_error_paths", "unit/web"),
    ("test_api_miniapp", "integration"),
    ("test_clip_real", "integration"),
    ("test_aesthetic_failopen_e2e", "integration"),
    ("test_m21_", "integration"),
    ("test_heuristic_v2", "integration"),
    ("test_phase6_", "integration"),
    ("test_phase5_", "integration"),
    ("test_phase9_", "integration"),
    ("test_phase10_", "integration"),
    ("test_lrg_overlay", "e2e"),  # playwright
]

EXPLICIT: dict[str, str] = {
    "test_import_wizard_v3_playwright.py": "e2e",
    "test_breath_lenis_scroll_playwright.py": "e2e",
    "test_studio_home_v2_ac_playwright.py": "e2e",
    "test_studio_intent_ac_p4_playwright.py": "e2e",
    "test_studio_lcp_playwright.py": "e2e",
    "test_studio_phase9_cull_playwright.py": "e2e",
    "test_phase13_g8_studio_playwright.py": "e2e",
    "test_bsp_moment_playwright.py": "e2e",
    "test_bsp_surface_playwright.py": "e2e",
    "test_lrg_overlay_computed_playwright.py": "e2e",
    "test_studio_server.py": "integration/studio",
    "test_studio_ac_visual_capture.py": "integration/studio",
    "test_validate.py": "unit/validate",  # if still at top - check
}


def resolve_dest(name: str) -> str | None:
    if name in KEEP_TOP:
        return None
    if name in EXPLICIT:
        return EXPLICIT[name]
    if "playwright" in name:
        return "e2e"
    for prefix, dest in PREFIX_RULES:
        if name.startswith(prefix):
            return dest
    return "unit/misc"


def ensure_init(dir_path: Path) -> None:
    init = dir_path / "__init__.py"
    if not init.exists():
        init.write_text("", encoding="utf-8")


def git_mv(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ensure_init(dest.parent)
    if dest.exists():
        raise FileExistsError(dest)
    subprocess.run(["git", "mv", str(src), str(dest)], cwd=ROOT, check=True)


def main() -> int:
    top = sorted(TESTS.glob("test_*.py"))
    mapping: dict[str, str] = {}
    for path in top:
        name = path.name
        dest_rel = resolve_dest(name)
        if dest_rel is None:
            continue
        dest = TESTS / dest_rel / name
        mapping[name] = dest_rel
        print(f"mv {name} -> {dest_rel}/")
        git_mv(path, dest)

    # Update baseline to only kept files
    kept = sorted(KEEP_TOP)
    BASELINE.write_text("\n".join(kept) + "\n", encoding="utf-8")
    manifest = ROOT / "docs" / "acceptance-records" / "m-c2-import-manifest.txt"
    lines = []
    for name, dest_rel in sorted(mapping.items()):
        mod = name[:-3]
        new_mod = dest_rel.replace("/", ".") + "." + mod
        lines.append(f"{mod}\t{new_mod}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nbaseline -> {len(kept)} file(s): {kept}")
    print(f"migrated {len(mapping)} files")
    print(f"manifest -> {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
