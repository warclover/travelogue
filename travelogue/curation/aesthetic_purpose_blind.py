"""AA · GAP-03/13 · purpose pick comparison + pairwise blind export."""

from __future__ import annotations

import random
from typing import Any, Callable, Literal

from travelogue.config import AestheticConfig
from travelogue.curation.aesthetic_blind_review import normalize_human_score
from travelogue.curation.aesthetic_learned_eval import rules_for_purpose
from travelogue.curation.aesthetic_score import purpose_overall

PurposeKey = Literal["cover", "hero", "moment", "solo"]


def _eligible(asset: dict) -> bool:
    return (
        asset.get("type", "image") != "video"
        and asset.get("layoutEligible") is not False
        and bool(asset.get("id"))
    )


def pick_top_asset(
    assets: list[dict],
    purpose: PurposeKey,
    *,
    cfg: AestheticConfig,
    score_fn: Callable[[dict], float | None] | None = None,
) -> str | None:
    """Highest purpose score among layout-eligible images."""
    ranked: list[tuple[float, str]] = []
    for asset in assets:
        if not _eligible(asset):
            continue
        aid = str(asset.get("id") or "")
        if score_fn is not None:
            val = score_fn(asset)
        else:
            val = purpose_overall(asset, purpose, cfg=cfg)
        if val is None:
            continue
        ranked.append((float(val), aid))
    if not ranked:
        return None
    ranked.sort(key=lambda t: (-t[0], t[1]))
    return ranked[0][1]


def rules_only_purpose_score(asset: dict, purpose: PurposeKey) -> float | None:
    cfg = AestheticConfig(ml_calibrate=False, use_purpose_presets=True)
    return rules_for_purpose(asset, purpose, cfg=cfg)


def _aligned_purpose_score(
    asset: dict,
    purpose: PurposeKey,
    *,
    cfg: AestheticConfig,
    p_by_stratum: dict[str, float],
    album_relative: bool,
) -> float | None:
    from travelogue.curation.aesthetic_score import relative_purpose_score

    if album_relative or cfg.use_album_relative:
        return relative_purpose_score(asset, purpose, p_by_stratum=p_by_stratum, cfg=cfg)
    return purpose_overall(asset, purpose, cfg=cfg)


def rank_assets_for_purpose(
    assets: list[dict],
    purpose: PurposeKey,
    *,
    cfg: AestheticConfig,
    album_relative: bool = False,
    p_by_stratum: dict[str, float] | None = None,
    score_fn: Callable[[dict], float | None] | None = None,
) -> list[dict[str, Any]]:
    """Descending purpose scores for layout-eligible assets."""
    from travelogue.curation.aesthetic_score import stratum_score_percentiles

    ref = p_by_stratum
    if ref is None and (album_relative or cfg.use_album_relative):
        ref = stratum_score_percentiles(
            assets,
            purpose=purpose,
            cfg=cfg,
            percentile=cfg.album_relative_percentile,
        )
    ranked: list[dict[str, Any]] = []
    for asset in assets:
        if not _eligible(asset):
            continue
        aid = str(asset.get("id") or "")
        if score_fn is not None:
            val = score_fn(asset)
        elif cfg.ml_calibrate:
            val = _aligned_purpose_score(
                asset,
                purpose,
                cfg=cfg,
                p_by_stratum=ref or {},
                album_relative=album_relative or cfg.use_album_relative,
            )
        else:
            val = rules_only_purpose_score(asset, purpose)
        if val is None:
            continue
        rel = str(asset.get("displayFile") or asset.get("sourceFile") or "")
        ranked.append(
            {
                "assetId": aid,
                "displayFile": rel,
                "score": round(float(val), 4),
            }
        )
    ranked.sort(key=lambda r: (-float(r["score"]), r["assetId"]))
    return ranked


def export_purpose_pick_pairs(
    assets: list[dict],
    *,
    rules_cfg: AestheticConfig,
    aligned_cfg: AestheticConfig,
    trip_id: str = "",
    purposes: tuple[PurposeKey, ...] = ("cover", "hero"),
    pairs_per_purpose: int = 6,
    top_k: int = 20,
    seed: int = 42,
    album_relative: bool = True,
    min_score_gap: float = 0.02,
) -> dict[str, Any]:
    """A/B pairs where rules ranking disagrees with aligned ranking (AC-SC-03)."""
    rng = random.Random(seed)
    pairs: list[dict[str, Any]] = []
    pair_id = 0
    seen: set[tuple[str, frozenset[str]]] = set()

    def _add_pair(
        purpose: PurposeKey,
        left: dict[str, Any],
        right: dict[str, Any],
        *,
        left_role: str,
        right_role: str,
    ) -> None:
        nonlocal pair_id
        asset_key = frozenset({left["assetId"], right["assetId"]})
        dedupe_key = (purpose, asset_key)
        if dedupe_key in seen:
            return
        seen.add(dedupe_key)
        pair_id += 1
        pairs.append(
            {
                "pairId": f"{purpose}-{pair_id:03d}",
                "purpose": purpose,
                "tripId": trip_id,
                "optionLeft": {
                    "assetId": left["assetId"],
                    "displayFile": left.get("displayFile"),
                    "score": left.get("score"),
                },
                "optionRight": {
                    "assetId": right["assetId"],
                    "displayFile": right.get("displayFile"),
                    "score": right.get("score"),
                },
                "leftRole": left_role,
                "rightRole": right_role,
                "judgeVerdict": None,
                "notes": "盲选更适合作封面/主图的一张；左右顺序随机，不透露算法版本。",
            }
        )

    for purpose in purposes:
        rules_rank = rank_assets_for_purpose(assets, purpose, cfg=rules_cfg)
        aligned_rank = rank_assets_for_purpose(
            assets,
            purpose,
            cfg=aligned_cfg,
            album_relative=album_relative,
        )
        local: list[tuple[dict, dict, str, str]] = []
        purpose_added = 0

        if rules_rank and aligned_rank:
            rt, at = rules_rank[0], aligned_rank[0]
            if rt["assetId"] != at["assetId"]:
                before = len(seen)
                if rng.random() < 0.5:
                    _add_pair(purpose, rt, at, left_role="rules", right_role="aligned")
                else:
                    _add_pair(purpose, at, rt, left_role="aligned", right_role="rules")
                if len(seen) > before:
                    purpose_added += 1

        top_pick_key: frozenset[str] | None = None
        if rules_rank and aligned_rank and rules_rank[0]["assetId"] != aligned_rank[0]["assetId"]:
            top_pick_key = frozenset({rules_rank[0]["assetId"], aligned_rank[0]["assetId"]})

        for r_row in rules_rank[:top_k]:
            for a_row in aligned_rank[:top_k]:
                if r_row["assetId"] == a_row["assetId"]:
                    continue
                if frozenset({r_row["assetId"], a_row["assetId"]}) == top_pick_key:
                    continue
                if abs(float(r_row["score"]) - float(a_row["score"])) < min_score_gap:
                    continue
                if rng.random() < 0.5:
                    local.append((r_row, a_row, "rules", "aligned"))
                else:
                    local.append((a_row, r_row, "aligned", "rules"))

        rng.shuffle(local)
        for left, right, l_role, r_role in local:
            if purpose_added >= pairs_per_purpose:
                break
            before = len(seen)
            _add_pair(purpose, left, right, left_role=l_role, right_role=r_role)
            if len(seen) > before:
                purpose_added += 1

    top_picks: dict[str, Any] = {}
    for purpose in purposes:
        rr = rank_assets_for_purpose(assets, purpose, cfg=rules_cfg)
        ar = rank_assets_for_purpose(
            assets,
            purpose,
            cfg=aligned_cfg,
            album_relative=album_relative,
        )
        top_picks[purpose] = {
            "rules": rr[0] if rr else None,
            "aligned": ar[0] if ar else None,
        }

    rng.shuffle(pairs)
    return {
        "version": "1",
        "tripId": trip_id,
        "pairCount": len(pairs),
        "pairsPerPurpose": pairs_per_purpose,
        "purposes": list(purposes),
        "seed": seed,
        "pairs": pairs,
        "topPicks": top_picks,
    }


def score_purpose_pairwise_export(doc: dict[str, Any]) -> dict[str, Any]:
    """Summarize human pairwise verdicts (aligned win rate)."""
    pairs = list(doc.get("pairs") or [])
    by_purpose: dict[str, Any] = {}
    wins = 0
    comparable = 0
    for pair in pairs:
        purpose = str(pair.get("purpose") or "cover")
        verdict = pair.get("judgeVerdict")
        block = by_purpose.setdefault(purpose, {"comparable": 0, "alignedWins": 0, "ties": 0})
        if not verdict:
            continue
        if verdict == "tie":
            block["ties"] += 1
            continue
        picked = pair.get("leftRole") if verdict == "left" else pair.get("rightRole")
        block["comparable"] += 1
        comparable += 1
        if picked == "aligned":
            block["alignedWins"] += 1
            wins += 1
    winrate = round(100.0 * wins / comparable, 2) if comparable else None
    return {
        "pairCount": len(pairs),
        "comparable": comparable,
        "alignedWins": wins,
        "alignedWinratePct": winrate,
        "targetWinratePct": 60.0,
        "passed": winrate is not None and winrate >= 60.0,
        "byPurpose": by_purpose,
    }


def build_purpose_pairwise_html(
    export: dict[str, Any],
    *,
    image_base_url: str = "",
    title: str = "Purpose 盲评 A/B",
) -> str:
    """Side-by-side pairwise reviewer; hides rules vs aligned mapping."""
    import json as _json

    trip_id = str(export.get("tripId") or "")
    pairs = export.get("pairs") or []
    public_pairs = [
        {
            "pairId": p.get("pairId"),
            "purpose": p.get("purpose"),
            "tripId": p.get("tripId", trip_id),
            "optionLeft": p.get("optionLeft"),
            "optionRight": p.get("optionRight"),
        }
        for p in pairs
    ]
    payload = {
        "title": title,
        "tripId": trip_id,
        "imageBase": image_base_url.rstrip("/"),
        "pairCount": len(public_pairs),
        "pairs": public_pairs,
    }
    data_json = _json.dumps(payload, ensure_ascii=False)
    storage_key = _json.dumps(f"purpose-pairwise-{trip_id}-{export.get('seed', 42)}")
    purpose_labels_json = _json.dumps(
        {"cover": "封面", "hero": "主图", "moment": "瞬间", "solo": "单人"},
        ensure_ascii=False,
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
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 16px 20px 32px; }}
    h1 {{ font-size: 1.1rem; margin: 0 0 8px; }}
    .meta {{ color: var(--muted); font-size: 0.85rem; }}
    .progress {{ height: 6px; background: var(--border); border-radius: 999px; overflow: hidden; margin: 12px 0; }}
    .progress > i {{ display: block; height: 100%; width: 0%; background: var(--ok); transition: width .2s; }}
    .stage {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 12px; }}
    .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .col {{ background: #000; border-radius: 8px; overflow: hidden; min-height: 36vh; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 2px solid transparent; }}
    .col img {{ max-width: 100%; max-height: 55vh; object-fit: contain; }}
    .col.selected {{ border-color: var(--ok); }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    button {{ border: 1px solid var(--border); background: #252932; color: var(--text); padding: 8px 14px; border-radius: 8px; cursor: pointer; }}
    button.primary {{ background: #2b4a7a; border-color: #3d6cb9; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: #252932; font-size: 0.75rem; color: var(--muted); }}
    @media (max-width: 720px) {{ .cols {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1 id="title">{title}</h1>
    <div class="meta" id="counter">—</div>
    <div class="progress"><i id="bar"></i></div>
    <div class="stage">
      <div class="meta" style="margin-bottom:10px"><span class="badge" id="purposeBadge">—</span></div>
      <div class="cols">
        <div class="col" id="colL" title="选左图"><img id="imgL" alt="A" /></div>
        <div class="col" id="colR" title="选右图"><img id="imgR" alt="B" /></div>
      </div>
      <div class="toolbar">
        <button type="button" id="pickL">选左图</button>
        <button type="button" id="pickR">选右图</button>
        <button type="button" id="pickTie">差不多</button>
        <button type="button" id="prev">← 上一组</button>
        <button type="button" id="next">下一组 →</button>
        <button type="button" id="export" class="primary">下载结果 JSON</button>
      </div>
      <p class="meta" style="margin-top:10px;line-height:1.5">盲选：左右顺序随机，不显示算法分数。键盘 <kbd>1</kbd> 左 · <kbd>2</kbd> 右 · <kbd>3</kbd> 差不多 · <kbd>←</kbd>/<kbd>→</kbd> 切换。</p>
    </div>
  </div>
  <script id="review-data" type="application/json">{data_json}</script>
  <script>
    const DATA = JSON.parse(document.getElementById("review-data").textContent);
    const STORAGE_KEY = {storage_key};
    const PURPOSE_LABELS = {purpose_labels_json};
    let index = 0;
    let verdicts = {{}};

    function loadState() {{
      try {{
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) verdicts = JSON.parse(raw).verdicts || JSON.parse(raw);
      }} catch (e) {{ verdicts = {{}}; }}
    }}
    function saveState() {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify({{ verdicts }}));
      updateProgress();
    }}
    function imageUrl(row) {{
      const file = (row.displayFile || "").replace(/^\\//, "");
      if (DATA.imageBase) return DATA.imageBase + "/" + file;
      return file;
    }}
    function judgedCount() {{
      return DATA.pairs.filter(p => verdicts[p.pairId]).length;
    }}
    function updateProgress() {{
      const n = judgedCount();
      const total = DATA.pairs.length;
      document.getElementById("bar").style.width = (total ? (100 * n / total) : 0) + "%";
      document.getElementById("counter").textContent = `已评 ${{n}} / ${{total}} · 第 ${{index + 1}} 组`;
    }}
    function showAt(i) {{
      index = Math.max(0, Math.min(DATA.pairs.length - 1, i));
      const p = DATA.pairs[index];
      document.getElementById("purposeBadge").textContent = (PURPOSE_LABELS[p.purpose] || p.purpose) + " · " + p.pairId;
      document.getElementById("imgL").src = imageUrl(p.optionLeft);
      document.getElementById("imgR").src = imageUrl(p.optionRight);
      const v = verdicts[p.pairId];
      document.getElementById("colL").classList.toggle("selected", v === "left");
      document.getElementById("colR").classList.toggle("selected", v === "right");
      updateProgress();
    }}
    function pick(v) {{
      const p = DATA.pairs[index];
      verdicts[p.pairId] = v;
      saveState();
      showAt(index);
      if (index < DATA.pairs.length - 1) showAt(index + 1);
    }}
    document.getElementById("pickL").onclick = () => pick("left");
    document.getElementById("pickR").onclick = () => pick("right");
    document.getElementById("pickTie").onclick = () => pick("tie");
    document.getElementById("colL").onclick = () => pick("left");
    document.getElementById("colR").onclick = () => pick("right");
    document.getElementById("prev").onclick = () => showAt(index - 1);
    document.getElementById("next").onclick = () => showAt(index + 1);
    document.getElementById("export").onclick = () => {{
      const rows = DATA.pairs.map(p => ({{ ...p, judgeVerdict: verdicts[p.pairId] || null }}));
      const blob = new Blob([JSON.stringify({{
        version: "1",
        tripId: DATA.tripId,
        exportedAt: new Date().toISOString(),
        pairs: rows
      }}, null, 2)], {{ type: "application/json" }});
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "purpose-pairwise-" + DATA.tripId + ".json";
      a.click();
    }};
    document.addEventListener("keydown", e => {{
      if (e.key === "1") pick("left");
      if (e.key === "2") pick("right");
      if (e.key === "3") pick("tie");
      if (e.key === "ArrowLeft") showAt(index - 1);
      if (e.key === "ArrowRight") showAt(index + 1);
    }});
    loadState();
    showAt(0);
  </script>
</body>
</html>"""


def export_pairwise_pairs(
    rows: list[dict[str, Any]],
    *,
    pairs_per_stratum: int = 15,
    seed: int = 42,
    score_key: str = "predictedOverall",
) -> dict[str, Any]:
    """GAP-13 · stratified pairs with different predicted scores for A/B review."""
    by_stratum: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("humanScore") is not None:
            continue
        stratum = str(row.get("stratum") or "general")
        by_stratum.setdefault(stratum, []).append(row)

    rng = random.Random(seed)
    pairs: list[dict[str, Any]] = []
    pair_id = 0
    for stratum, pool in sorted(by_stratum.items()):
        scored = [
            r
            for r in pool
            if r.get(score_key) is not None and r.get("assetId")
        ]
        if len(scored) < 2:
            continue
        scored.sort(key=lambda r: float(r[score_key]))
        attempts = 0
        local = 0
        while local < pairs_per_stratum and attempts < pairs_per_stratum * 10:
            attempts += 1
            low = rng.choice(scored[: max(1, len(scored) // 2)])
            high = rng.choice(scored[len(scored) // 2 :])
            if low.get("assetId") == high.get("assetId"):
                continue
            if abs(float(high[score_key]) - float(low[score_key])) < 0.03:
                continue
            pair_id += 1
            local += 1
            pairs.append(
                {
                    "pairId": f"p{pair_id:03d}",
                    "stratum": stratum,
                    "scoreKey": score_key,
                    "optionA": {
                        "assetId": low["assetId"],
                        "displayFile": low.get("displayFile"),
                        "predicted": low.get(score_key),
                        "label": "A",
                    },
                    "optionB": {
                        "assetId": high["assetId"],
                        "displayFile": high.get("displayFile"),
                        "predicted": high.get(score_key),
                        "label": "B",
                    },
                    "judgeVerdict": None,
                    "notes": "Pick the photo you would rather feature. A=lower algo score, B=higher.",
                }
            )
    return {
        "version": "1",
        "pairCount": len(pairs),
        "pairsPerStratum": pairs_per_stratum,
        "seed": seed,
        "pairs": pairs,
    }


def automated_purpose_win_report(
    assets: list[dict],
    label_rows: list[dict[str, Any]],
    *,
    rules_cfg: AestheticConfig | None = None,
    aligned_cfg: AestheticConfig | None = None,
    purposes: tuple[PurposeKey, ...] = ("cover", "hero", "moment"),
    album_relative: bool = False,
) -> dict[str, Any]:
    """Proxy win rate: aligned pick has higher human score than rules pick."""
    from travelogue.curation.aesthetic_score import (
        relative_purpose_score,
        stratum_score_percentiles,
    )

    rules_cfg = rules_cfg or AestheticConfig(ml_calibrate=False, use_purpose_presets=True)
    aligned_cfg = aligned_cfg or AestheticConfig(
        ml_calibrate=True, use_purpose_presets=True, mllm=rules_cfg.mllm
    )
    labels_by_id = {
        str(r.get("assetId") or ""): r
        for r in label_rows
        if r.get("assetId") and r.get("humanScore") is not None
    }

    report: dict[str, Any] = {"purposes": {}, "targetWinratePct": 60.0}
    for purpose in purposes:
        rules_id = pick_top_asset(
            assets,
            purpose,
            cfg=rules_cfg,
            score_fn=lambda a, p=purpose: rules_only_purpose_score(a, p),
        )
        use_relative = album_relative or aligned_cfg.use_album_relative
        p_by_stratum: dict[str, float] = {}
        if use_relative:
            p_by_stratum = stratum_score_percentiles(
                assets,
                purpose=purpose,
                cfg=aligned_cfg,
                percentile=aligned_cfg.album_relative_percentile,
            )

        def _aligned_score(asset: dict, p=purpose, ref=p_by_stratum) -> float | None:
            if use_relative:
                return relative_purpose_score(asset, p, p_by_stratum=ref, cfg=aligned_cfg)
            return purpose_overall(asset, p, cfg=aligned_cfg)

        aligned_id = pick_top_asset(
            assets,
            purpose,
            cfg=aligned_cfg,
            score_fn=_aligned_score,
        )
        block: dict[str, Any] = {
            "rulesPick": rules_id,
            "alignedPick": aligned_id,
            "samePick": rules_id == aligned_id,
        }
        if rules_id and aligned_id and rules_id != aligned_id:
            try:
                hs_rules = normalize_human_score(labels_by_id[rules_id]["humanScore"])
                hs_aligned = normalize_human_score(labels_by_id[aligned_id]["humanScore"])
            except (KeyError, TypeError, ValueError):
                block["verdict"] = "missing_labels"
            else:
                if hs_aligned > hs_rules:
                    block["verdict"] = "aligned_wins"
                elif hs_aligned < hs_rules:
                    block["verdict"] = "rules_wins"
                else:
                    block["verdict"] = "tie"
                block["humanRules"] = round(hs_rules, 4)
                block["humanAligned"] = round(hs_aligned, 4)
        elif rules_id == aligned_id:
            block["verdict"] = "same_pick"
        else:
            block["verdict"] = "incomplete"
        report["purposes"][purpose] = block

    wins = sum(
        1
        for p in report["purposes"].values()
        if p.get("verdict") == "aligned_wins"
    )
    comparable = sum(
        1
        for p in report["purposes"].values()
        if p.get("verdict") in ("aligned_wins", "rules_wins", "tie")
    )
    report["automatedWinCount"] = wins
    report["comparablePurposes"] = comparable
    report["automatedWinratePct"] = round(100.0 * wins / comparable, 2) if comparable else None
    report["passed"] = (
        report["automatedWinratePct"] is not None
        and report["automatedWinratePct"] >= 60.0
    )
    return report


def export_purpose_blind_signoff(
    trip_id: str,
    automated: dict[str, Any],
    *,
    pairs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Signoff template for manual judgeVerdict on purpose picks."""
    items: list[dict[str, Any]] = []
    for purpose, block in (automated.get("purposes") or {}).items():
        items.append(
            {
                "purpose": purpose,
                "rulesPick": block.get("rulesPick"),
                "candidatePick": block.get("alignedPick"),
                "automatedVerdict": block.get("verdict"),
                "judgeVerdict": None,
                "notes": "A=rules pick · B=candidate (aligned) · C=tie",
            }
        )
    return {
        "version": "1",
        "tripId": trip_id,
        "targetWinratePct": 60.0,
        "automated": automated,
        "pairwise": pairs,
        "purposeComparisons": items,
    }
