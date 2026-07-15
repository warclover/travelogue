"""Purge incomplete import trips (Stable-QH M3 · D-QH-05 方案 A).

previewable 冻结定义（与 PRD §7.3 对齐）：
- ``index.html`` 存在且非空；且
- ``pipeline.status`` ∈ PREVIEWABLE_PIPELINE_STATUSES
  （缺 trip.json / 无法解析时保守视为 previewable，避免误删）。
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from travelogue.services.trip import meta_revision
from travelogue.web.studio_trip_id import is_valid_studio_trip_id

_log = logging.getLogger(__name__)

# 产线可预览态（含 G1 structure_draft；有合法 index.html 即可打开卷轴）
PREVIEWABLE_PIPELINE_STATUSES: frozenset[str] = frozenset(
    {
        "structure_draft",
        "structure_locked",
        "copy_draft",
        "copy_locked",
        "rendered",
        "exported",
    }
)


def trip_is_previewable(trip_dir: Path) -> bool:
    index = trip_dir / "index.html"
    try:
        if not index.is_file() or index.stat().st_size <= 0:
            return False
    except OSError:
        return False

    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        return True
    trip = _load_trip_dict(trip_json)
    if trip is None:
        return True
    status = str((trip.get("pipeline") or {}).get("status") or "").strip()
    return status in PREVIEWABLE_PIPELINE_STATUSES


def trip_has_user_patches(trip: dict[str, Any]) -> bool:
    """用户有效精修 / 闸口确认 → 不得当半成品自动删。"""
    locks = (trip.get("pipeline") or {}).get("locks")
    if isinstance(locks, dict) and (locks.get("structure") or locks.get("copy")):
        return True
    curation = trip.get("curation")
    if isinstance(curation, dict) and curation.get("closingUserPicked"):
        return True
    # 导入初始 revision 多为 0/1；≥2 视为用户或编辑写回
    if meta_revision(trip) >= 2:
        return True
    return False


def maybe_purge_incomplete_import_trip(
    trips_root: Path,
    trip_id: str | None,
    *,
    reason: str = "import_incomplete",
) -> bool:
    """Delete trip dir if incomplete. Returns True when purged."""
    tid = str(trip_id or "").strip()
    if not tid or not is_valid_studio_trip_id(tid):
        return False
    trip_dir = (trips_root / tid).resolve()
    try:
        trip_dir.relative_to(trips_root.resolve())
    except ValueError:
        return False
    if not trip_dir.is_dir():
        return False

    if trip_is_previewable(trip_dir):
        _log.info("skip purge previewable trip %s (%s)", tid, reason)
        return False

    trip_json = trip_dir / "trip.json"
    trip = _load_trip_dict(trip_json) if trip_json.is_file() else {}
    if trip:
        from travelogue.web.studio_handlers.trip_common import is_protected_demo_trip

        if is_protected_demo_trip(tid, trip):
            _log.info("skip purge protected demo %s", tid)
            return False
    if trip and trip_has_user_patches(trip):
        _log.info("skip purge user-patched trip %s (%s)", tid, reason)
        return False

    # 与 handle_delete_trip 同路径：目录级删除（列表为扫盘，无需独立 index reconcile）
    if trip_is_previewable(trip_dir):
        return False
    try:
        shutil.rmtree(trip_dir)
    except OSError:
        _log.exception("purge incomplete trip failed for %s", trip_dir)
        return False
    _log.info("purged incomplete import trip %s (%s)", tid, reason)
    return True


def cleanup_import_terminal_artifacts(
    trips_root: Path,
    *,
    job_id: str,
    trip_id: str | None,
    status: str,
) -> bool:
    """On cancelled/failed import: purge incomplete trip + upload staging."""
    from travelogue.web.studio_uploads import delete_upload_dir

    purged = False
    if status in ("cancelled", "failed"):
        purged = maybe_purge_incomplete_import_trip(
            trips_root,
            trip_id,
            reason=f"import_{status}",
        )
    upload = trips_root / "_uploads" / job_id
    if upload.exists():
        delete_upload_dir(upload, trips_dir=trips_root)
    return purged


def _load_trip_dict(trip_json: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None
