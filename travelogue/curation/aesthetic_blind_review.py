"""AA · blind-review corpus sampling + SRCC reporting (M0)."""

from __future__ import annotations

import random
from typing import Any, Literal

from travelogue.curation.aesthetic_score import aesthetic_overall, purpose_overall
from travelogue.curation.pa_acceptance import srcc_from_label_rows
from travelogue.curation.subject_tagging import semantic_category_for_asset, subject_class_for_asset

ReviewStratum = Literal["person", "landscape", "food", "group", "general"]

DEFAULT_STRATA_QUOTAS: dict[str, int] = {
    "person": 40,
    "landscape": 40,
    "food": 25,
    "group": 25,
    "general": 20,
}

DEFECT_TAG_VALUES: tuple[str, ...] = ("closed_eyes", "blur_face")
PORTRAIT_REVIEW_STRATA: frozenset[str] = frozenset({"person", "group"})


def _face_count(asset: dict) -> int:
    """Face count for review stratum only — requires bbox list, not stale quality.faceCount."""
    faces = asset.get("faces")
    if isinstance(faces, list) and len(faces) > 0:
        return len(faces)
    # quality.faceCount without ``faces[]`` is often false-positive on scenery (e.g. safari).
    return 0


def _is_portraitish_tags(asset: dict) -> bool:
    tags = {str(t).lower() for t in (asset.get("tags") or []) if t}
    return bool(tags & {"selfie", "portrait", "合影", "人像"})


def review_stratum_for_asset(asset: dict) -> ReviewStratum:
    """Coarse stratum for stratified blind-review sampling."""
    faces = _face_count(asset)
    if faces > 1:
        return "group"
    if faces == 1:
        return "person"

    from travelogue.curation.layout_planner import aspect_kind_for_asset

    aspect = aspect_kind_for_asset(asset)
    if aspect in ("landscape", "panorama") and not _is_portraitish_tags(asset):
        return "landscape"

    bucket = subject_class_for_asset(asset)
    if bucket == "person":
        return "person"
    category = semantic_category_for_asset(asset)
    if category == "food" or bucket == "food":
        return "food"
    if category in {"landscape", "nature", "architecture", "temple", "street", "mountain", "sea"}:
        return "landscape"
    if bucket == "landscape":
        return "landscape"
    return "general"


def _eligible_image(asset: dict) -> bool:
    if asset.get("type") == "video":
        return False
    if asset.get("layoutEligible") is False:
        return False
    return bool(asset.get("id"))


def all_eligible_for_review(assets: list[dict]) -> list[dict]:
    """Export every layout-eligible image (full-trip relabel)."""
    return [a for a in assets if _eligible_image(a)]


def sample_assets_for_review(
    assets: list[dict],
    *,
    target_n: int = 150,
    strata_quotas: dict[str, int] | None = None,
    seed: int = 42,
) -> list[dict]:
    """Stratified sample of image assets for human blind review."""
    quotas = dict(strata_quotas or DEFAULT_STRATA_QUOTAS)
    pool = [a for a in assets if _eligible_image(a)]
    by_stratum: dict[str, list[dict]] = {k: [] for k in quotas}
    by_stratum.setdefault("general", [])
    for asset in pool:
        stratum = review_stratum_for_asset(asset)
        if stratum not in by_stratum:
            by_stratum[stratum] = []
        by_stratum[stratum].append(asset)

    rng = random.Random(seed)
    picked: list[dict] = []
    picked_ids: set[str] = set()

    for stratum, quota in quotas.items():
        candidates = by_stratum.get(stratum) or []
        rng.shuffle(candidates)
        for asset in candidates:
            if len(picked) >= target_n:
                break
            aid = str(asset["id"])
            if aid in picked_ids:
                continue
            if sum(1 for p in picked if review_stratum_for_asset(p) == stratum) >= quota:
                break
            picked.append(asset)
            picked_ids.add(aid)

    if len(picked) < target_n:
        remainder = [a for a in pool if str(a["id"]) not in picked_ids]
        rng.shuffle(remainder)
        for asset in remainder:
            if len(picked) >= target_n:
                break
            picked.append(asset)
            picked_ids.add(str(asset["id"]))

    return picked


def build_review_row(
    asset: dict,
    *,
    trip_id: str,
    trip_dir: str,
    display_order: int,
    stratum_override: str | None = None,
) -> dict[str, Any]:
    """One blind-review row; scores included for SRCC, order is shuffled externally."""
    aid = str(asset.get("id") or "")
    aesthetic = (asset.get("quality") or {}).get("aesthetic") if isinstance(asset.get("quality"), dict) else None
    dims = dict(aesthetic.get("dims") or {}) if isinstance(aesthetic, dict) else {}
    rel = str(asset.get("displayFile") or asset.get("sourceFile") or "")
    stratum_auto = review_stratum_for_asset(asset)
    stratum = str(stratum_override) if stratum_override else stratum_auto
    row: dict[str, Any] = {
        "displayOrder": display_order,
        "assetId": aid,
        "tripId": trip_id,
        "tripDir": trip_dir,
        "displayFile": rel,
        "stratum": stratum,
        "stratumAuto": stratum_auto,
        "predictedOverall": aesthetic_overall(asset),
        "predictedCover": purpose_overall(asset, "cover"),
        "predictedHero": purpose_overall(asset, "hero"),
        "predictedMoment": purpose_overall(asset, "moment"),
        "predictedSolo": purpose_overall(asset, "solo"),
        "dims": dims,
        "humanScore": None,
        "defectTags": [],
    }
    if rel:
        row["imagePath"] = f"{trip_dir.rstrip('/')}/{rel}".replace("\\", "/")
    return row


def shuffle_blind_rows(rows: list[dict[str, Any]], *, seed: int = 42) -> list[dict[str, Any]]:
    """Shuffle export order so reviewers are not biased by algorithm ranking."""
    rng = random.Random(seed)
    out = [dict(r) for r in rows]
    rng.shuffle(out)
    for i, row in enumerate(out):
        row["displayOrder"] = i + 1
    return out


def normalize_human_score(value: float | int) -> float:
    """Accept 1–5 Likert (int or whole float) or [0,1] float; 1–10 when >5."""
    if isinstance(value, bool):
        raise TypeError
    if isinstance(value, int) and 1 <= value <= 5:
        return (value - 1) / 4.0
    v = float(value)
    # Already on [0,1] (e.g. merged v3 labels); must run before Likert whole-float branch.
    if 0.0 <= v <= 1.0:
        return v
    if v == int(v) and 1 <= int(v) <= 5:
        return (int(v) - 1) / 4.0
    if v > 5.0:
        return min(1.0, max(0.0, v / 10.0))
    if v > 1.0:
        return min(1.0, max(0.0, (v - 1.0) / 4.0))
    return min(1.0, max(0.0, v))


def srcc_report(
    rows: list[dict[str, Any]],
    *,
    predicted_key: str = "predictedOverall",
    by_stratum: bool = False,
) -> dict[str, Any]:
    """SRCC vs human labels; optional per-stratum breakdown."""
    prepared: list[dict[str, Any]] = []
    for row in rows:
        if row.get("humanScore") is None:
            continue
        try:
            raw_hs = row["humanScore"]
            if isinstance(raw_hs, bool) or raw_hs is None:
                continue
            hs = normalize_human_score(raw_hs)
            pred = row.get(predicted_key, row.get("predictedOverall", row.get("overall")))
            if pred is None:
                continue
            prepared.append({**row, "humanScore": hs, "predictedOverall": float(pred)})
        except (TypeError, ValueError):
            continue

    base = srcc_from_label_rows(prepared)
    report: dict[str, Any] = {
        "predictedKey": predicted_key,
        "sampleCount": base["sampleCount"],
        "srcc": base["srcc"],
        "labeledCount": sum(1 for r in rows if r.get("humanScore") is not None),
        "exportCount": len(rows),
    }
    if not by_stratum:
        return report

    strata: dict[str, Any] = {}
    for stratum in sorted({str(r.get("stratum") or "general") for r in prepared}):
        subset = [r for r in prepared if str(r.get("stratum") or "general") == stratum]
        sub = srcc_from_label_rows(subset)
        strata[stratum] = {"sampleCount": sub["sampleCount"], "srcc": sub["srcc"]}
    report["byStratum"] = strata
    return report


def compare_predicted_keys(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """SRCC for overall vs purpose-specific predictions (baseline diagnostics)."""
    keys = ("predictedOverall", "predictedCover", "predictedHero", "predictedMoment", "predictedSolo")
    out: dict[str, Any] = {}
    for key in keys:
        rep = srcc_report(rows, predicted_key=key, by_stratum=False)
        out[key] = {"sampleCount": rep["sampleCount"], "srcc": rep["srcc"]}
    return out


def init_corpus_template() -> dict[str, Any]:
    return {
        "version": "1",
        "notes": "Fill tripDir paths. targetTotal ≥150. Adjust strata quotas for coverage.",
        "targetTotal": 150,
        "seed": 42,
        "strataQuotas": dict(DEFAULT_STRATA_QUOTAS),
        "trips": [
            {"tripId": "album-a", "tripDir": "trips/album-a", "tags": ["portrait_heavy"]},
            {"tripId": "album-b", "tripDir": "trips/album-b", "tags": ["mixed"]},
        ],
    }


def init_labels_from_export(export: dict[str, Any]) -> dict[str, Any]:
    rows = export.get("rows") or []
    label_rows: list[dict[str, Any]] = []
    for row in rows:
        label_rows.append(
            {
                "assetId": row.get("assetId"),
                "tripId": row.get("tripId"),
                "stratum": row.get("stratum"),
                "stratumAuto": row.get("stratumAuto", row.get("stratum")),
                "displayFile": row.get("displayFile"),
                "humanScore": row.get("humanScore"),
                "predictedOverall": row.get("predictedOverall"),
                "predictedCover": row.get("predictedCover"),
                "predictedHero": row.get("predictedHero"),
                "predictedMoment": row.get("predictedMoment"),
                "predictedSolo": row.get("predictedSolo"),
                "defectTags": list(row.get("defectTags") or []),
            }
        )
    return {
        "version": "1",
        "frozen": False,
        "notes": "humanScore: 1–5 Likert or 0–1. Set frozen=true when baseline is locked.",
        "sourceExport": export.get("exportedAt"),
        "rows": label_rows,
    }


def relative_trip_image_bases(export: dict[str, Any], *, html_depth: int = 2) -> dict[str, str]:
    """Repo-relative bases for HTML under docs/acceptance-records/ → ../../trips/<id>."""
    prefix = "/".join([".."] * html_depth)
    bases: dict[str, str] = {}
    for trip in export.get("trips") or []:
        tid = str(trip.get("tripId") or "").strip()
        if not tid:
            continue
        tdir = str(trip.get("tripDir") or f"trips/{tid}").replace("\\", "/").strip("/")
        bases[tid] = f"{prefix}/{tdir}".replace("//", "/")
    for row in export.get("rows") or []:
        tid = str(row.get("tripId") or "").strip()
        if not tid or tid in bases:
            continue
        tdir = str(row.get("tripDir") or f"trips/{tid}").replace("\\", "/").strip("/")
        bases[tid] = f"{prefix}/{tdir}".replace("//", "/")
    return bases


def build_blind_review_html(
    export: dict[str, Any],
    *,
    image_base_urls: dict[str, str] | None = None,
    default_image_base_url: str = "",
    use_relative_image_urls: bool = True,
    title: str = "审美盲评",
) -> str:
    """Standalone HTML reviewer; hides algorithm scores during rating."""
    import json as _json

    rows = export.get("rows") or []
    trip_bases = dict(image_base_urls or {})
    if default_image_base_url and not trip_bases:
        for trip in export.get("trips") or []:
            tid = str(trip.get("tripId") or "")
            if tid:
                trip_bases[tid] = default_image_base_url.rstrip("/")
    elif not trip_bases and use_relative_image_urls:
        trip_bases = relative_trip_image_bases(export)

    payload = {
        "title": title,
        "exportedAt": export.get("exportedAt"),
        "sampleCount": export.get("sampleCount", len(rows)),
        "tripBases": trip_bases,
        "rows": [
            {
                "displayOrder": r.get("displayOrder"),
                "assetId": r.get("assetId"),
                "tripId": r.get("tripId"),
                "displayFile": r.get("displayFile"),
                "stratum": r.get("stratum"),
                "stratumAuto": r.get("stratumAuto", r.get("stratum")),
                "predictedOverall": r.get("predictedOverall"),
                "predictedCover": r.get("predictedCover"),
                "predictedHero": r.get("predictedHero"),
                "predictedMoment": r.get("predictedMoment"),
                "defectTags": list(r.get("defectTags") or []),
            }
            for r in rows
        ],
    }
    data_json = _json.dumps(payload, ensure_ascii=False)
    storage_key = _json.dumps(
        f"aesthetic-blind-{export.get('corpusSource', 'export')}-{export.get('seed', 42)}"
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0f1115; --panel: #1a1d24; --text: #e8eaed; --muted: #9aa0a6;
      --accent: #6ea8fe; --ok: #3dd68c; --border: #2a2f3a;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Segoe UI", system-ui, sans-serif; background: var(--bg); color: var(--text); }}
    .wrap {{ max-width: 960px; margin: 0 auto; padding: 16px 20px 32px; }}
    header {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
    h1 {{ font-size: 1.1rem; font-weight: 600; margin: 0; }}
    .meta {{ color: var(--muted); font-size: 0.85rem; }}
    .progress {{ height: 6px; background: var(--border); border-radius: 999px; overflow: hidden; margin: 8px 0 16px; }}
    .progress > i {{ display: block; height: 100%; width: 0%; background: var(--ok); transition: width .2s; }}
    .stage {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 12px; }}
    .img-box {{ display: flex; align-items: center; justify-content: center; min-height: 52vh; background: #000; border-radius: 8px; overflow: hidden; }}
    .img-box img {{ max-width: 100%; max-height: 70vh; object-fit: contain; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }}
    button, .score-btn {{
      border: 1px solid var(--border); background: #252932; color: var(--text);
      padding: 8px 14px; border-radius: 8px; cursor: pointer; font-size: 0.95rem;
    }}
    button:hover, .score-btn:hover {{ border-color: var(--accent); }}
    button.primary {{ background: #2b4a7a; border-color: #3d6cb9; }}
    button.primary:hover {{ background: #35598f; }}
    .score-btn.selected {{ background: #2d5a3d; border-color: var(--ok); }}
    .score-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .hint {{ color: var(--muted); font-size: 0.82rem; margin-top: 10px; line-height: 1.5; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: #252932; font-size: 0.75rem; color: var(--muted); }}
    .stratum-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; align-items: center; }}
    .stratum-btn {{ padding: 4px 10px; font-size: 0.8rem; }}
    .stratum-btn.selected {{ background: #2b4a7a; border-color: var(--accent); }}
    .defect-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; align-items: center; }}
    .defect-btn {{ padding: 4px 10px; font-size: 0.8rem; }}
    .defect-btn.selected {{ background: #5a3030; border-color: #c96; }}
    .rubric {{ background: #12151c; border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; margin-top: 10px; font-size: 0.82rem; line-height: 1.55; color: var(--muted); }}
    .rubric strong {{ color: var(--text); }}
    @media (max-width: 640px) {{ .img-box {{ min-height: 40vh; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1 id="title">{title}</h1>
      <div class="meta" id="counter">—</div>
    </header>
    <div class="progress"><i id="bar"></i></div>
    <div class="stage">
      <div class="meta" style="margin-bottom:8px">
        <span class="badge" id="stratumBadge">—</span>
        <span id="assetId" style="margin-left:8px"></span>
      </div>
      <div class="stratum-row" id="stratumPick"></div>
      <div class="defect-row" id="defectPick" hidden></div>
      <div class="img-box"><img id="photo" alt="review" /></div>
      <div class="rubric" id="rubric"></div>
      <div class="score-row" id="scores"></div>
      <div class="toolbar">
        <button type="button" id="prev">← 上一张</button>
        <button type="button" id="next">下一张 →</button>
        <button type="button" id="export" class="primary">下载标签 JSON</button>
      </div>
      <p class="hint">
        键盘：<kbd>1</kbd>–<kbd>5</kbd> 打分 · <kbd>←</kbd>/<kbd>→</kbd> 切换 · 进度自动保存在本机浏览器。<br/>
        先确认照片类型（风景/人像/合影/美食），类型不对请先点上方按钮修改，再按对应标准打分。<br/>
        单人照/合影可勾选「闭眼」「糊脸」缺陷标签（可选，导出至 defectTags）。
      </p>
    </div>
  </div>
  <script id="review-data" type="application/json">{data_json}</script>
  <script>
    const DATA = JSON.parse(document.getElementById("review-data").textContent);
    const STORAGE_KEY = {storage_key};
    const SCORE_LABELS = {{1:"废片",2:"偏弱",3:"一般",4:"好",5:"很好"}};
    const STRATUM_LABELS = {{
      person: "单人照", group: "合影", landscape: "风景", food: "美食", general: "其他"
    }};
    const RUBRICS = {{
      person: "5=表情自然清晰 · 3=平淡或有瑕疵 · 1=糊/闭眼/废片",
      group: "5=关键人物清晰、表情可接受 · 3=有人略糊 · 1=多人闭眼/糊脸",
      landscape: "5=构图光线舒服、有代表性 · 3=普通记录 · 1=平淡或技术硬伤",
      food: "5=诱人、主体清楚 · 3=食欲感一般 · 1=难辨认/无食欲",
      general: "按「是否值得在这本游记里重点展示」打 1–5"
    }};
    const STRATA = ["landscape", "person", "group", "food", "general"];
    const DEFECT_TAGS = ["closed_eyes", "blur_face"];
    const DEFECT_LABELS = {{ closed_eyes: "闭眼", blur_face: "糊脸" }};
    const PORTRAIT_STRATA = new Set(["person", "group"]);
    let index = 0;
    let scores = {{}};
    let strata = {{}};
    let defects = {{}};

    function loadScores() {{
      try {{
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {{
          const parsed = JSON.parse(raw);
          scores = parsed.scores || parsed;
          strata = parsed.strata || {{}};
          defects = parsed.defects || {{}};
        }}
      }} catch (e) {{ scores = {{}}; strata = {{}}; defects = {{}}; }}
      for (const row of DATA.rows) {{
        if (!defects[row.assetId] && row.defectTags && row.defectTags.length) {{
          defects[row.assetId] = row.defectTags.slice();
        }}
      }}
    }}
    function saveScores() {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify({{ scores, strata, defects }}));
      updateProgress();
    }}
    function currentStratum(row) {{
      return strata[row.assetId] || row.stratum || "general";
    }}
    function currentDefects(row) {{
      return defects[row.assetId] || [];
    }}
    function isPortraitStratum(s) {{
      return PORTRAIT_STRATA.has(s);
    }}
    function imageUrl(row) {{
      const base = (DATA.tripBases && DATA.tripBases[row.tripId]) || "";
      const file = (row.displayFile || "").replace(/^\\//, "");
      if (base) return base.replace(/\\/$/, "") + "/" + file;
      return file;
    }}
    function ratedCount() {{
      return DATA.rows.filter(r => scores[r.assetId] != null).length;
    }}
    function updateProgress() {{
      const n = ratedCount();
      const total = DATA.rows.length;
      document.getElementById("bar").style.width = (total ? (100 * n / total) : 0) + "%";
      document.getElementById("counter").textContent = `已评 ${{n}} / ${{total}} · 第 ${{index + 1}} 张`;
    }}
    function renderStratumPick() {{
      const row = DATA.rows[index];
      const box = document.getElementById("stratumPick");
      box.innerHTML = "<span style='color:var(--muted);font-size:0.8rem'>类型：</span>";
      const cur = currentStratum(row);
      for (const s of STRATA) {{
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "stratum-btn" + (cur === s ? " selected" : "");
        btn.textContent = STRATUM_LABELS[s] || s;
        btn.addEventListener("click", () => {{
          strata[row.assetId] = s;
          saveScores();
          showAt(index);
        }});
        box.appendChild(btn);
      }}
    }}
    function renderDefectPick() {{
      const row = DATA.rows[index];
      const box = document.getElementById("defectPick");
      const s = currentStratum(row);
      if (!isPortraitStratum(s)) {{
        box.hidden = true;
        box.innerHTML = "";
        return;
      }}
      box.hidden = false;
      box.innerHTML = "<span style='color:var(--muted);font-size:0.8rem'>人像缺陷（可选）：</span>";
      const cur = new Set(currentDefects(row));
      for (const tag of DEFECT_TAGS) {{
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "defect-btn" + (cur.has(tag) ? " selected" : "");
        btn.textContent = DEFECT_LABELS[tag] || tag;
        btn.addEventListener("click", () => {{
          const next = new Set(currentDefects(row));
          if (next.has(tag)) next.delete(tag); else next.add(tag);
          defects[row.assetId] = Array.from(next);
          saveScores();
          renderDefectPick();
        }});
        box.appendChild(btn);
      }}
    }}
    function renderRubric() {{
      const row = DATA.rows[index];
      const s = currentStratum(row);
      const el = document.getElementById("rubric");
      el.innerHTML = "<strong>" + (STRATUM_LABELS[s] || s) + " · 打分参考</strong><br/>" + (RUBRICS[s] || "");
    }}
    function renderScores() {{
      const row = DATA.rows[index];
      const box = document.getElementById("scores");
      box.innerHTML = "";
      for (let s = 1; s <= 5; s++) {{
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "score-btn" + (scores[row.assetId] === s ? " selected" : "");
        btn.textContent = s + " · " + SCORE_LABELS[s];
        btn.addEventListener("click", () => setScore(s, true));
        box.appendChild(btn);
      }}
    }}
    function showAt(i) {{
      index = Math.max(0, Math.min(DATA.rows.length - 1, i));
      const row = DATA.rows[index];
      document.getElementById("photo").src = imageUrl(row);
      const s = currentStratum(row);
      document.getElementById("stratumBadge").textContent = STRATUM_LABELS[s] || s;
      document.getElementById("assetId").textContent = row.assetId || "";
      renderStratumPick();
      renderDefectPick();
      renderRubric();
      renderScores();
      updateProgress();
    }}
    function setScore(s, advance) {{
      const row = DATA.rows[index];
      scores[row.assetId] = s;
      saveScores();
      renderScores();
      if (advance && index < DATA.rows.length - 1) showAt(index + 1);
    }}
    function exportLabels() {{
      const rows = DATA.rows.map(r => {{
        const s = currentStratum(r);
        const row = {{
          assetId: r.assetId,
          tripId: r.tripId,
          stratum: s,
          stratumAuto: r.stratumAuto || r.stratum,
          displayFile: r.displayFile,
          humanScore: scores[r.assetId] ?? null,
          predictedOverall: r.predictedOverall ?? null,
          predictedCover: r.predictedCover ?? null,
          predictedHero: r.predictedHero ?? null,
          predictedMoment: r.predictedMoment ?? null,
          defectTags: isPortraitStratum(s) ? currentDefects(r) : [],
        }};
        return row;
      }});
      const payload = {{
        version: "1",
        frozen: false,
        notes: "Exported from blind-review HTML · humanScore 1–5",
        sourceExport: DATA.exportedAt,
        rows,
      }};
      const blob = new Blob([JSON.stringify(payload, null, 2)], {{type: "application/json"}});
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "aesthetic-human-labels.json";
      a.click();
      URL.revokeObjectURL(a.href);
    }}
    document.getElementById("prev").addEventListener("click", () => showAt(index - 1));
    document.getElementById("next").addEventListener("click", () => showAt(index + 1));
    document.getElementById("export").addEventListener("click", exportLabels);
    document.addEventListener("keydown", (e) => {{
      if (e.key >= "1" && e.key <= "5") {{ setScore(Number(e.key), true); e.preventDefault(); }}
      if (e.key === "ArrowLeft") {{ showAt(index - 1); e.preventDefault(); }}
      if (e.key === "ArrowRight") {{ showAt(index + 1); e.preventDefault(); }}
    }});
    loadScores();
    showAt(0);
  </script>
</body>
</html>
"""
