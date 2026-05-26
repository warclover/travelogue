"""Human-readable ingest / reexport summaries for CLI."""

from __future__ import annotations

from travelogue.curation.layout_planner import summarize_orientations


def format_ingest_report(result, trip: dict | None = None) -> str:
    """Multi-line report from IngestResult or ReexportResult-like object."""
    lines: list[str] = []
    stats = getattr(result, "stats", {}) or {}
    added = getattr(result, "added", None)
    skipped = getattr(result, "skipped", None)
    updated = getattr(result, "updated", None)

    if added is not None:
        lines.append(f"导入 +{added} 张，跳过 {skipped or 0} 张")
    if updated is not None:
        lines.append(f"重导出 {updated} 张")

    if stats.get("scanned"):
        lines.append(f"扫描 {stats['scanned']} · 入选 {stats.get('used', '?')}")
    if stats.get("total_assets"):
        lines.append(f"trip 内共 {stats['total_assets']} 张")

    for key, label in (
        ("deduped", "完全重复"),
        ("deduped_phash", "相似图(phash)"),
        ("deduped_burst", "连拍"),
        ("deduped_phash_replaced", "相似图替换为更清晰"),
        ("deduped_burst_replaced", "连拍替换为更清晰"),
        ("skipped_small", "过小"),
        ("skipped_open", "无法打开"),
    ):
        if stats.get(key):
            lines.append(f"  {label}: {stats[key]}")

    if any(stats.get(k) for k in ("exif_dates", "filename_dates", "mtime_dates")):
        lines.append(
            f"  日期来源: exif={stats.get('exif_dates', 0)} "
            f"filename={stats.get('filename_dates', 0)} "
            f"mtime={stats.get('mtime_dates', 0)}"
        )
    for w in stats.get("date_warnings") or []:
        lines.append(f"  WARN: {w}")
    for hint in stats.get("journey_hints") or []:
        lines.append(f"  提示: {hint}")
    summary = stats.get("mediaClassSummary")
    if isinstance(summary, dict) and summary:
        parts = [f"{k}={v}" for k, v in sorted(summary.items()) if v]
        lines.append(f"  素材类型: {', '.join(parts)}")
    if stats.get("exif_rotations"):
        lines.append(f"  EXIF 旋转: {stats['exif_rotations']}")

    thumb_ids = stats.get("suspected_thumbnail_ids") or []
    if thumb_ids:
        preview = ", ".join(thumb_ids[:8])
        if len(thumb_ids) > 8:
            preview += f" …共 {len(thumb_ids)} 张"
        lines.append(f"  疑似缩略图（短边过小）: {preview}")

    curate_preview = stats.get("low_res_excluded_ids") or stats.get("curate_low_res_preview_ids") or []
    if curate_preview:
        preview = ", ".join(curate_preview[:8])
        if len(curate_preview) > 8:
            preview += f" …共 {len(curate_preview)} 张"
        lines.append(f"  低分辨率（不参与排版）: {preview}")
        warn = stats.get("low_res_excluded_warn") or stats.get("curate_low_res_preview_warn")
        if warn:
            lines.append(f"  {warn}")

    faces_n = stats.get("faces_detected", 0)
    if faces_n:
        lines.append(f"  检测到人脸: {faces_n} 张（排版将避免人物竖拼/人景混排）")

    gps_n = stats.get("gps_assets", 0)
    if gps_n:
        lines.append(f"  含 GPS: {gps_n} 张")

    if trip and trip.get("assets"):
        layout = trip.get("exportLayout", "mobile")
        s = summarize_orientations(trip["assets"], export_layout=layout)  # type: ignore[arg-type]
        lines.append(
            f"  构图: 横{s.landscape} 竖{s.portrait} 方{s.square} "
            f"全景{s.panorama} 超长{s.tall}"
        )

    failed = getattr(result, "failed", None)
    if failed:
        lines.append(f"  失败: {', '.join(failed[:5])}")

    return "\n".join(lines)


def format_g1_status(trip: dict) -> str:
    """G1-style structure + layout summary."""
    lines: list[str] = []
    meta = trip.get("meta", {})
    lines.append(f"标题: {meta.get('title', '')} · {meta.get('dateStart', '')} — {meta.get('dateEnd', '')}")
    lines.append(f"封面: {trip.get('coverAssetId', '-')}")
    cands = trip.get("coverCandidates") or []
    if cands:
        lines.append(f"封面候选: {', '.join(cands[:5])}")

    cur = trip.get("curation") or {}
    orient = cur.get("orientationSummary")
    if orient:
        lines.append(
            f"构图统计: 共{orient.get('total', 0)} "
            f"横{orient.get('landscape', 0)} 竖{orient.get('portrait', 0)} "
            f"方{orient.get('square', 0)} 全景{orient.get('panorama', 0)}"
        )

    for ch in trip.get("chapters", []):
        titles = ch.get("title", "")
        n_items = len(ch.get("items", []))
        rows = sum(1 for it in ch["items"] if it.get("type") == "media-row")
        lines.append(f"  [{ch.get('index')}] {titles} · {ch.get('patternId')} · {n_items} 块 ({rows} 行)")

    curation = trip.get("curation") or {}
    if curation.get("layoutPlanVersion"):
        lines.append(f"排版版本: {curation['layoutPlanVersion']}")
    return "\n".join(lines)
