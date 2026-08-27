"""Output Ledger · ``导出文件/outputs.json`` (OLT M1).

Read-time heal uses one ``os.scandir`` + set compare (BLK-OLT-03).
``custom`` is never written (BLK-OLT-01). No edition branches.
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from travelogue.domain.output_fingerprint import (
    copy_fp,
    options_fp,
    source_snapshot,
    structure_fp,
)
from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME

# §4.4 last column · static map, not an edition branch (iron 10).
TICKET_SURFACES = frozenset({"folio", "scroll", "card", "grid", "spread"})
SURFACE_ORDER = {
    "folio": 0,
    "scroll": 1,
    "card": 2,
    "grid": 3,
    "spread": 4,
    "bundle": 5,
}
CHIP_LIMIT = 3

def output_ledger_enabled() -> bool:
    """Release default is True (BE-OLT-10); explicit false still rolls back."""
    try:
        from travelogue.config import get_config

        return bool(getattr(get_config().studio, "output_ledger", True))
    except Exception:
        return True


LEDGER_NAME = "outputs.json"
LEDGER_SCHEMA_VERSION = 1
VALID_STALE_INPUTS = frozenset({"structure", "copy", "bundle", "options"})
BARE_NAME_FORBIDDEN = frozenset({".", ".."})

ScandirFn = Callable[[os.PathLike[str] | str], Iterable[os.DirEntry[str]]]

_ledger_thread_locks: dict[str, threading.RLock] = {}
_ledger_thread_locks_guard = threading.Lock()
_ledger_hold = threading.local()


def _ledger_lock_key(trip_dir: Path) -> str:
    return os.path.normcase(str(Path(trip_dir).resolve())).casefold()


@contextmanager
def _ledger_lock(trip_dir: Path) -> Iterator[None]:
    """Serialize ledger RMW across threads and Studio subprocesses."""
    key = _ledger_lock_key(trip_dir)
    with _ledger_thread_locks_guard:
        lock = _ledger_thread_locks.setdefault(key, threading.RLock())
    lock.acquire()
    held: set[str] = getattr(_ledger_hold, "keys", None) or set()
    outermost = key not in held
    if outermost:
        held = set(held)
        held.add(key)
        _ledger_hold.keys = held
    fh = None
    try:
        if outermost:
            lock_path = ledger_path(trip_dir).with_name(f".{LEDGER_NAME}.lock")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            fh = open(lock_path, "a+b")
            if os.name == "nt":
                import msvcrt

                fh.seek(0)
                if fh.read(1) == b"":
                    fh.write(b"\0")
                    fh.flush()
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if fh is not None:
            try:
                if os.name == "nt":
                    import msvcrt

                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            finally:
                fh.close()
        if outermost:
            held.discard(key)
            _ledger_hold.keys = held
        lock.release()

# share_zip / pdf are not platform_profiles.yaml keys (PRD §4.4).
_NON_PLATFORM: dict[str, dict[str, Any]] = {
    "share_zip": {
        "profile": "share_zip",
        "surface": "bundle",
        "label": "分享包",
        "stale_inputs": ("structure", "copy", "bundle", "options"),
        "stale_options": ("copyDisplay", "breathMode"),
    },
    "pdf": {
        "profile": "pdf",
        "surface": "bundle",
        "label": "PDF",
        "stale_inputs": ("structure", "copy", "bundle", "options"),
        "stale_options": ("copyDisplay", "breathMode"),
    },
}

_WECHAT_CHAT_CHAPTER_LABEL = "微信群 · 分章"


@dataclass(frozen=True)
class OutputMeta:
    output_id: str
    profile: str
    surface: str
    label: str
    stale_inputs: tuple[str, ...]
    stale_options: tuple[str, ...]


class OutputLedgerError(Exception):
    """Raised when the ledger cannot be written (export must not report success)."""


def ledger_path(trip_dir: Path) -> Path:
    return Path(trip_dir) / EXPORT_OUTPUT_DIRNAME / LEDGER_NAME


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _valid_bare_name(raw: Any) -> str | None:
    text = str(raw or "").strip()
    if not text or text in BARE_NAME_FORBIDDEN:
        return None
    if "/" in text or "\\" in text or text in (".", ".."):
        return None
    name = Path(text).name
    if name != text or name in BARE_NAME_FORBIDDEN:
        return None
    return name


def resolve_output_id(profile: str, *, segmented: bool = False) -> str | None:
    """Return ledger primary key, or None when the profile is excluded (custom)."""
    pid = str(profile or "").strip()
    if not pid or pid == "custom":
        return None
    if pid in ("wechat_chat:whole", "wechat_chat:chapter"):
        return pid
    if pid == "wechat_chat":
        return "wechat_chat:chapter" if segmented else "wechat_chat:whole"
    return pid


def _profile_base(output_id: str) -> str:
    if output_id.startswith("wechat_chat:"):
        return "wechat_chat"
    return output_id


def lookup_output_meta(profile: str, *, segmented: bool = False) -> OutputMeta | None:
    output_id = resolve_output_id(profile, segmented=segmented)
    if output_id is None:
        return None
    if output_id in _NON_PLATFORM:
        raw = _NON_PLATFORM[output_id]
        return OutputMeta(
            output_id=output_id,
            profile=str(raw["profile"]),
            surface=str(raw["surface"]),
            label=str(raw["label"]),
            stale_inputs=tuple(raw["stale_inputs"]),
            stale_options=tuple(raw["stale_options"]),
        )
    from travelogue.export.platform_profiles import PlatformProfileError, get_profile

    base = _profile_base(output_id)
    try:
        plat = get_profile(base)
    except PlatformProfileError:
        return None
    label = plat.label
    if output_id == "wechat_chat:chapter":
        label = _WECHAT_CHAT_CHAPTER_LABEL
    stale_inputs = tuple(plat.stale_inputs) or ("structure", "copy", "bundle")
    stale_options = tuple(plat.stale_options)
    if "options" not in stale_inputs:
        stale_options = ()
    return OutputMeta(
        output_id=output_id,
        profile=base,
        surface=str(plat.surface or ""),
        label=str(label),
        stale_inputs=stale_inputs,
        stale_options=stale_options,
    )


def _valid_record(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    output_id = str(raw.get("outputId") or "").strip()
    profile = str(raw.get("profile") or "").strip()
    surface = str(raw.get("surface") or "").strip()
    label = str(raw.get("label") or "").strip()
    files_raw = raw.get("files")
    if not output_id or not profile or not surface or not label:
        return None
    if not isinstance(files_raw, list) or not files_raw:
        return None
    files: list[str] = []
    for item in files_raw:
        name = _valid_bare_name(item)
        if not name:
            return None
        files.append(name)
    stale_inputs = [
        str(x) for x in (raw.get("staleInputs") or []) if str(x) in VALID_STALE_INPUTS
    ]
    if not stale_inputs:
        return None
    stale_options = [str(x) for x in (raw.get("staleOptions") or []) if str(x).strip()]
    if "options" in stale_inputs and not stale_options:
        return None
    source = raw.get("source")
    if not isinstance(source, dict):
        return None
    for key in ("structureFp", "copyFp", "bundleFp"):
        if not str(source.get(key) or "").strip():
            return None
    spec = raw.get("spec") if isinstance(raw.get("spec"), dict) else {}
    try:
        file_count = int(raw.get("fileCount") or len(files))
    except (TypeError, ValueError):
        file_count = len(files)
    record = {
        "outputId": output_id,
        "profile": profile,
        "surface": surface,
        "label": label,
        "edition": str(raw.get("edition") or "journal"),
        "createdAt": str(raw.get("createdAt") or ""),
        "batchId": str(raw.get("batchId") or "") or None,
        "spec": dict(spec),
        "files": files,
        "fileCount": file_count,
        "bytes": raw.get("bytes"),
        "source": {
            "structureFp": str(source.get("structureFp") or ""),
            "copyFp": str(source.get("copyFp") or ""),
            "bundleFp": str(source.get("bundleFp") or ""),
            "optionsFp": source.get("optionsFp"),
        },
        "staleInputs": stale_inputs,
        "staleOptions": stale_options,
    }
    if record["batchId"] is None:
        record.pop("batchId")
    return record


def _export_dir(trip_dir: Path) -> Path:
    return Path(trip_dir) / EXPORT_OUTPUT_DIRNAME


def _existing_names(export_dir: Path, scandir: ScandirFn) -> set[str]:
    if not export_dir.is_dir():
        return set()
    names: set[str] = set()
    with scandir(export_dir) as iterator:
        for entry in iterator:
            if entry.is_file():
                names.add(entry.name)
    return names


def _heal(outputs: list[dict[str, Any]], existing: set[str]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for rec in outputs:
        files = rec.get("files") or []
        if files and set(files) <= existing:
            kept.append(rec)
    return kept


def read_ledger(
    trip_dir: Path,
    *,
    scandir: ScandirFn = os.scandir,
) -> list[dict[str, Any]] | None:
    """Return healed records, empty list when valid-but-empty, or None to fall back."""
    path = ledger_path(trip_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("schemaVersion") != LEDGER_SCHEMA_VERSION:
        return None
    raw_outputs = data.get("outputs")
    if not isinstance(raw_outputs, list):
        return None
    parsed: list[dict[str, Any]] = []
    for item in raw_outputs:
        rec = _valid_record(item)
        if rec is None:
            return None
        parsed.append(rec)
    existing = _existing_names(_export_dir(trip_dir), scandir)
    return _heal(parsed, existing)


def _atomic_write(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)
    except OSError as exc:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise OutputLedgerError(f"failed to write output ledger: {path}") from exc
    return path


def _load_unhealed(trip_dir: Path) -> list[dict[str, Any]]:
    path = ledger_path(trip_dir)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict) or data.get("schemaVersion") != LEDGER_SCHEMA_VERSION:
        return []
    raw_outputs = data.get("outputs")
    if not isinstance(raw_outputs, list):
        return []
    parsed: list[dict[str, Any]] = []
    for item in raw_outputs:
        rec = _valid_record(item)
        if rec is not None:
            parsed.append(rec)
    return parsed


def _append_output_unlocked(trip_dir: Path, record: dict[str, Any]) -> Path | None:
    profile = str(record.get("profile") or record.get("outputId") or "").strip()
    if profile == "custom" or str(record.get("outputId") or "") == "custom":
        return None
    parsed = _valid_record(record)
    if parsed is None:
        raise OutputLedgerError("invalid output record")
    current = _load_unhealed(trip_dir)
    replaced = False
    next_rows: list[dict[str, Any]] = []
    for rec in current:
        if rec["outputId"] == parsed["outputId"]:
            next_rows.append(parsed)
            replaced = True
        else:
            next_rows.append(rec)
    if not replaced:
        next_rows.append(parsed)
    payload = {
        "schemaVersion": LEDGER_SCHEMA_VERSION,
        "updatedAt": _utc_now(),
        "outputs": next_rows,
    }
    return _atomic_write(ledger_path(trip_dir), payload)


def append_output(trip_dir: Path, record: dict[str, Any]) -> Path | None:
    """Replace the matching ``outputId`` and write atomically.

    ``profile == custom`` (or unresolvable id) returns None without writing.
    """
    with _ledger_lock(trip_dir):
        return _append_output_unlocked(trip_dir, record)


def _prune_ledger_unlocked(
    trip_dir: Path,
    *,
    scandir: ScandirFn = os.scandir,
) -> list[dict[str, Any]] | None:
    healed = read_ledger(trip_dir, scandir=scandir)
    if healed is None:
        return None
    payload = {
        "schemaVersion": LEDGER_SCHEMA_VERSION,
        "updatedAt": _utc_now(),
        "outputs": healed,
    }
    _atomic_write(ledger_path(trip_dir), payload)
    return healed


def prune_ledger(
    trip_dir: Path,
    *,
    scandir: ScandirFn = os.scandir,
) -> list[dict[str, Any]] | None:
    with _ledger_lock(trip_dir):
        return _prune_ledger_unlocked(trip_dir, scandir=scandir)


def drop_output_row(trip_dir: Path, output_id: str) -> bool:
    """Remove a ledger row without deleting files (failed recapture → orphans)."""
    wanted = str(output_id or "").strip()
    if not wanted:
        return False
    with _ledger_lock(trip_dir):
        current = _load_unhealed(trip_dir)
        next_rows = [rec for rec in current if rec["outputId"] != wanted]
        if len(next_rows) == len(current):
            return False
        payload = {
            "schemaVersion": LEDGER_SCHEMA_VERSION,
            "updatedAt": _utc_now(),
            "outputs": next_rows,
        }
        _atomic_write(ledger_path(trip_dir), payload)
        return True


def _edition_snapshot(trip: dict[str, Any] | None) -> str:
    studio = trip.get("studio") if isinstance(trip, dict) else None
    raw = studio.get("edition") if isinstance(studio, dict) else None
    text = str(raw or "journal").strip().lower()
    return text if text in ("journal", "portfolio") else "journal"


def _file_bytes(export_dir: Path, files: list[str]) -> int:
    total = 0
    for name in files:
        try:
            total += (export_dir / name).stat().st_size
        except OSError:
            continue
    return total


def load_trip_dict(trip_dir: Path) -> dict[str, Any]:
    path = Path(trip_dir) / "trip.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def spec_from_profile(
    profile: str,
    *,
    scale: int = 1,
    fmt: str = "png",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec: dict[str, Any] = {"format": fmt, "scale": scale}
    if extra:
        spec.update(extra)
    if profile in _NON_PLATFORM:
        return spec
    try:
        from travelogue.export.platform_profiles import get_profile, output_canvas_size

        plat = get_profile(_profile_base(profile))
    except Exception:
        return spec
    size = output_canvas_size(plat)
    out = plat.output or {}
    if size:
        spec.setdefault("width", size[0])
        spec.setdefault("height", size[1])
    elif out.get("width_css"):
        spec.setdefault("width", out.get("width_css"))
        spec.setdefault("width_css", out.get("width_css"))
    if out.get("aspect"):
        spec.setdefault("aspect", out.get("aspect"))
    return spec


def record_dispatch_result(
    trip_dir: Path,
    result: Any,
    *,
    platform: str,
    bundle_fp: str,
    trip: dict[str, Any] | None = None,
    scale: int = 1,
    fmt: str = "png",
    batch_id: str = "",
) -> None:
    """Write ledger rows for a successful dispatch. Raises on write failure."""
    pid = str(getattr(result, "platform", None) or platform or "").strip()
    if pid == "custom":
        return
    trip = trip if isinstance(trip, dict) else load_trip_dict(trip_dir)
    files = [Path(p).name for p in (getattr(result, "paths", None) or []) if p]
    segmented = bool(getattr(result, "segmented", False))
    if files:
        record_successful_output(
            trip_dir,
            trip=trip,
            profile=pid,
            files=files,
            spec=spec_from_profile(pid, scale=scale, fmt=fmt),
            bundle_fp=bundle_fp,
            batch_id=batch_id,
            segmented=segmented,
        )
    elif resolve_output_id(pid) == "portfolio_pages":
        drop_output_row(trip_dir, "portfolio_pages")
    share_zip = getattr(result, "share_zip", None)
    if share_zip:
        record_successful_output(
            trip_dir,
            trip=trip,
            profile="share_zip",
            files=[Path(share_zip).name],
            spec=spec_from_profile("share_zip", scale=1, fmt="zip"),
            bundle_fp=bundle_fp,
            batch_id=batch_id,
        )


def record_successful_output(
    trip_dir: Path,
    *,
    trip: dict[str, Any] | None,
    profile: str,
    files: list[str],
    spec: dict[str, Any],
    bundle_fp: str,
    batch_id: str = "",
    segmented: bool = False,
) -> Path | None:
    """Build one ledger row from a successful export. None = skipped (custom)."""
    meta = lookup_output_meta(profile, segmented=segmented)
    if meta is None:
        return None
    names: list[str] = []
    for raw in files:
        name = _valid_bare_name(Path(str(raw)).name)
        if name:
            names.append(name)
    if not names:
        raise OutputLedgerError("output ledger files must be non-empty")
    record = {
        "outputId": meta.output_id,
        "profile": meta.profile,
        "surface": meta.surface,
        "label": meta.label,
        "edition": _edition_snapshot(trip),
        "createdAt": _utc_now(),
        "batchId": str(batch_id or "").strip() or None,
        "spec": dict(spec or {}),
        "files": names,
        "fileCount": len(names),
        "bytes": _file_bytes(_export_dir(trip_dir), names),
        "source": source_snapshot(
            trip, bundle_fp=bundle_fp, stale_options=meta.stale_options
        ),
        "staleInputs": list(meta.stale_inputs),
        "staleOptions": list(meta.stale_options),
    }
    if record["batchId"] is None:
        record.pop("batchId")
    with _ledger_lock(trip_dir):
        written = _append_output_unlocked(trip_dir, record)
        _prune_ledger_unlocked(trip_dir)
        return written


def on_ticket(record: dict[str, Any]) -> bool:
    """True when §4.4 says this output occupies a ticket chip."""
    return str(record.get("surface") or "") in TICKET_SURFACES


def record_is_outdated(
    record: dict[str, Any],
    trip: dict[str, Any] | None,
    bundle_fp: str,
) -> bool:
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    inputs = {str(x) for x in (record.get("staleInputs") or [])}
    if "structure" in inputs and str(source.get("structureFp") or "") != structure_fp(trip):
        return True
    if "copy" in inputs and str(source.get("copyFp") or "") != copy_fp(trip):
        return True
    if "bundle" in inputs and str(source.get("bundleFp") or "") != str(bundle_fp or ""):
        return True
    if "options" in inputs:
        current = options_fp(trip, record.get("staleOptions") or [])
        if str(source.get("optionsFp") or "") != str(current or ""):
            return True
    return False


def ticket_outputs_outdated(
    records: list[dict[str, Any]],
    trip: dict[str, Any] | None,
    bundle_fp: str,
) -> bool:
    return any(
        on_ticket(rec) and record_is_outdated(rec, trip, bundle_fp) for rec in records
    )


def _sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(records, key=lambda rec: str(rec.get("createdAt") or ""), reverse=True)
    return sorted(ranked, key=lambda rec: SURFACE_ORDER.get(str(rec.get("surface") or ""), 99))


def _reveal_rel(record: dict[str, Any]) -> str | None:
    files = record.get("files") or []
    if not files:
        return None
    return f"{EXPORT_OUTPUT_DIRNAME}/{files[0]}"


def build_output_summary(
    records: list[dict[str, Any]],
    trip: dict[str, Any] | None,
    bundle_fp: str,
) -> dict[str, Any]:
    """Light shelf payload. chips omit fileCount (iron 6)."""
    ticket = _sort_records([rec for rec in records if on_ticket(rec)])
    chips: list[dict[str, Any]] = []
    for rec in ticket[:CHIP_LIMIT]:
        chips.append(
            {
                "outputId": rec["outputId"],
                "label": rec["label"],
                "state": (
                    "outdated" if record_is_outdated(rec, trip, bundle_fp) else "ready"
                ),
                "revealRelPath": _reveal_rel(rec),
            }
        )
    return {"total": len(records), "chips": chips}


def annotate_outputs(
    records: list[dict[str, Any]],
    trip: dict[str, Any] | None,
    bundle_fp: str,
) -> list[dict[str, Any]]:
    """Full manage-list rows. Numbers stay here, not on the ticket."""
    out: list[dict[str, Any]] = []
    for rec in _sort_records(list(records)):
        item = {
            "outputId": rec["outputId"],
            "profile": rec["profile"],
            "surface": rec["surface"],
            "label": rec["label"],
            "createdAt": rec.get("createdAt") or "",
            "fileCount": rec.get("fileCount") or len(rec.get("files") or []),
            "files": list(rec.get("files") or []),
            "bytes": rec.get("bytes"),
            "spec": dict(rec.get("spec") or {}),
            "state": "outdated" if record_is_outdated(rec, trip, bundle_fp) else "ready",
            "revealRelPath": _reveal_rel(rec),
        }
        out.append(item)
    return out


def delete_output(trip_dir: Path, output_id: str) -> bool:
    """Delete files + ledger row. False when the id is missing."""
    wanted = str(output_id or "").strip()
    if not wanted:
        return False
    with _ledger_lock(trip_dir):
        current = _load_unhealed(trip_dir)
        found: dict[str, Any] | None = None
        next_rows: list[dict[str, Any]] = []
        for rec in current:
            if rec["outputId"] == wanted:
                found = rec
            else:
                next_rows.append(rec)
        if found is None:
            return False
        export_dir = _export_dir(trip_dir)
        for name in found.get("files") or []:
            path = export_dir / str(name)
            try:
                if path.is_file():
                    path.unlink()
            except OSError:
                pass
        payload = {
            "schemaVersion": LEDGER_SCHEMA_VERSION,
            "updatedAt": _utc_now(),
            "outputs": next_rows,
        }
        _atomic_write(ledger_path(trip_dir), payload)
        return True
