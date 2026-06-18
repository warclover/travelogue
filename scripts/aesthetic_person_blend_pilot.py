"""AA · person stratum blend pilot (landscape + person · PC-M1)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import AestheticConfig, get_config, resolve_learned_blend  # noqa: E402
from travelogue.curation.aesthetic_blind_review import srcc_report  # noqa: E402
from travelogue.curation.aesthetic_learned_eval import (  # noqa: E402
    _read_learned_aesthetic_score,
    blended_score,
    grid_search_blend,
    load_merged_assets_for_specs,
    per_stratum_rules_vs_blend,
    rules_for_purpose,
)
from travelogue.curation.aesthetic_score import refresh_portrait_subject_clarity_overall  # noqa: E402
from travelogue.curation.aesthetic_stratum_audit import remap_rows_for_merged  # noqa: E402
from travelogue.curation.photo_cull_ml import pyiqa_available  # noqa: E402


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def refresh_portrait_on_assets(assets_by_id: dict[str, dict], *, portrait_cfg) -> int:
    app = get_config()
    ae = app.aesthetic
    n = 0
    for asset in assets_by_id.values():
        if refresh_portrait_subject_clarity_overall(asset, cfg=ae, portrait_cfg=portrait_cfg):
            n += 1
    return n


def evaluate_person_pilot(
    *,
    corpus: dict[str, Any],
    labels_doc: dict[str, Any],
    stratum_blend_only: tuple[str, ...] = ("landscape", "person"),
    person_blend: float = 0.6,
    landscape_blend: float = 0.6,
    apply_portrait: bool = True,
) -> dict[str, Any]:
    rows = remap_rows_for_merged(list(labels_doc.get("rows") or []))
    specs = [t for t in (corpus.get("trips") or []) if not str(t.get("tripId") or "").startswith("TBD")]
    assets_by_id, scored = load_merged_assets_for_specs(specs, root=ROOT, metric="nima", allow_cpu=True)

    app = get_config()
    portrait_refreshed = 0
    if apply_portrait:
        portrait_refreshed = refresh_portrait_on_assets(assets_by_id, portrait_cfg=app.cull.portrait)

    blends = dict(app.aesthetic.stratum_blends or {})
    blends.update({"landscape": landscape_blend, "person": person_blend})

    person_rows = [r for r in rows if r.get("stratum") == "person" and r.get("humanScore") is not None]

    rules_cfg = AestheticConfig(ml_calibrate=False, use_purpose_presets=True, portrait_lite_enabled=False)
    pilot_cfg = AestheticConfig(
        ml_calibrate=True,
        use_stratum_blend=True,
        stratum_blends=blends,
        stratum_blend_only=stratum_blend_only,
        use_purpose_presets=True,
        portrait_lite_enabled=False,
    )

    def _predict(asset: dict, _row: dict[str, Any]) -> float | None:
        rules = rules_for_purpose(asset, "default", cfg=pilot_cfg)
        learned = _read_learned_aesthetic_score(asset)
        blend = resolve_learned_blend(asset, pilot_cfg)
        return blended_score(rules, learned, blend)

    person_grid = grid_search_blend(
        assets_by_id,
        person_rows,
        cfg=rules_cfg,
        purposes=("default",),
        blend_min=0.0,
        blend_max=0.6,
        blend_step=0.05,
    )

    per_stratum = per_stratum_rules_vs_blend(rows, assets_by_id, recommended_blends=blends, portrait_lite=False)

    pilot_rows = []
    for row in person_rows:
        asset = assets_by_id.get(str(row.get("assetId") or ""))
        if not asset:
            continue
        pred = _predict(asset, row)
        if pred is None:
            continue
        pilot_rows.append({**row, "predictedOverall": float(pred)})

    pilot_srcc = srcc_report(pilot_rows, by_stratum=False)

    return {
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "stratumBlendOnly": list(stratum_blend_only),
        "recommendedBlends": blends,
        "portraitRefreshed": portrait_refreshed,
        "scoredByTrip": scored,
        "personGrid": person_grid.get("purposes", {}).get("default"),
        "perStratum": per_stratum,
        "personPilotSrcc": pilot_srcc,
        "personStratum": per_stratum.get("person"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AA · person blend pilot")
    parser.add_argument("--corpus", type=Path, default=Path("docs/acceptance-records/aesthetic-alignment-corpus.v3.json"))
    parser.add_argument("--labels", type=Path, default=Path("docs/acceptance-records/aesthetic-human-labels.merged.v3.json"))
    parser.add_argument("--write", type=Path, default=Path("docs/acceptance-records/aesthetic-person-blend-pilot.v3.json"))
    parser.add_argument("--person-blend", type=float, default=0.6)
    parser.add_argument("--landscape-blend", type=float, default=0.6)
    parser.add_argument("--no-portrait-refresh", action="store_true")
    args = parser.parse_args(argv)

    if not pyiqa_available():
        print("E_AA_PERSON_PILOT: pyiqa not installed", file=sys.stderr)
        return 2

    report = evaluate_person_pilot(
        corpus=_load_json(_resolve(args.corpus)),
        labels_doc=_load_json(_resolve(args.labels)),
        person_blend=args.person_blend,
        landscape_blend=args.landscape_blend,
        apply_portrait=not args.no_portrait_refresh,
    )
    out = _resolve(args.write)
    _save_json(out, report)
    person = report.get("personStratum") or {}
    print(out)
    print(f"person SRCC rules={person.get('rulesSrcc')} blend={person.get('stratumBlendSrcc')} delta={person.get('delta')}")
    print(f"person pilot SRCC={report.get('personPilotSrcc', {}).get('srcc')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
