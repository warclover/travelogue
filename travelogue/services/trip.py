"""Trip.json load/save and trip directory layout."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from travelogue.errors import CodeError
from travelogue.services.validate import load_json
from travelogue.util.datetime_ import utc_now_iso

T = TypeVar("T")


class TripNotFoundError(FileNotFoundError):
    code = "E_TRIP_NOT_FOUND"


class TripSaveError(OSError):
    """Atomic trip.json write failed (I/O, permissions, target locked)."""

    code = "E_TRIP_SAVE_BUSY"


class TripConflictError(CodeError):
    """Optimistic lock conflict after CAS retries exhausted."""

    def __init__(self, message: str) -> None:
        super().__init__("E_TRIP_CONFLICT", message)


_trip_write_locks: dict[str, threading.Lock] = {}
_trip_write_locks_guard = threading.Lock()


def _trip_lock_key(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _get_trip_write_lock(path: Path) -> threading.Lock:
    key = _trip_lock_key(path)
    lock = _trip_write_locks.get(key)
    if lock is None:
        with _trip_write_locks_guard:
            lock = _trip_write_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                _trip_write_locks[key] = lock
    return lock


def meta_revision(trip: dict) -> int:
    meta = trip.get("meta")
    if not isinstance(meta, dict):
        return 0
    raw = meta.get("revision", 0)
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def _read_disk_revision(path: Path) -> int:
    if not path.is_file():
        return 0
    raw = load_json(path)
    return meta_revision(raw)


_UNSET = object()


def _clean_str(value: Any, *, limit: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:limit]


def apply_intent(
    trip: dict,
    *,
    title: Any = _UNSET,
    places: Any = _UNSET,
    places_user_set: Any = _UNSET,
    user_notes: Any = _UNSET,
    travel_notes: Any = _UNSET,
    date_range: Any = _UNSET,
    travel_plan: Any = _UNSET,
    folders: Any = _UNSET,
    featured_subjects: Any = _UNSET,
    layout_density: Any = _UNSET,
    photo_cull_enabled: Any = _UNSET,
    keep_near_duplicates: Any = _UNSET,
    submitted_at: str | None = None,
) -> dict:
    """Single writer for Phase 4 ``trip.intent`` (PRD-PHASE4 §4.1/§14).

    Atomically updates ``intent`` and mirrors the structural fields to
    ``meta.title`` / ``meta.places`` / top-level ``userNotes`` so the
    double-write invariant (AC-P4-09) always holds. Only arguments that are
    explicitly passed are touched; ``None`` clears the field.

    Returns the updated ``trip.intent`` object.
    """
    intent = dict(trip.get("intent") or {})
    intent["version"] = "1"
    meta = trip.setdefault("meta", {})

    if title is not _UNSET:
        cleaned = _clean_str(title, limit=20)
        if cleaned:
            intent["title"] = cleaned
            meta["title"] = cleaned
        else:
            intent.pop("title", None)
            meta.pop("title", None)

    if places is not _UNSET:
        place_list = [
            p
            for p in (
                _clean_str(item, limit=20) for item in (places or [])
            )
            if p
        ][:10]
        if place_list:
            intent["places"] = place_list
            meta["places"] = list(place_list)
        else:
            intent.pop("places", None)
            # meta.places is schema-required (minItems: 1); omitting intent places
            # only means copy may prefer title/EXIF — keep a valid meta placeholder.
            if not meta.get("places"):
                meta["places"] = ["旅途"]

    if places_user_set is not _UNSET:
        if places_user_set:
            intent["placesUserSet"] = True
        else:
            intent.pop("placesUserSet", None)

    if user_notes is not _UNSET:
        cleaned = _clean_str(user_notes, limit=200)
        if cleaned:
            intent["userNotes"] = cleaned
            trip["userNotes"] = cleaned
        else:
            intent.pop("userNotes", None)
            trip.pop("userNotes", None)

    if travel_notes is not _UNSET:
        cleaned = _clean_str(travel_notes, limit=500)
        if cleaned:
            intent["travelNotes"] = cleaned
        else:
            intent.pop("travelNotes", None)

    if date_range is not _UNSET:
        if not date_range:
            intent.pop("dateRange", None)
        else:
            if not isinstance(date_range, dict):
                raise ValueError("dateRange must be an object")
            start = _clean_str(date_range.get("start"), limit=10)
            end = _clean_str(date_range.get("end"), limit=10)
            source = _clean_str(date_range.get("source"), limit=16)
            payload: dict[str, str] = {}
            if start:
                payload["start"] = start
            if end:
                payload["end"] = end
            if source in ("user", "exif", "mixed"):
                payload["source"] = source
            if payload:
                intent["dateRange"] = payload
            else:
                intent.pop("dateRange", None)

    if travel_plan is not _UNSET:
        if travel_plan:
            if not isinstance(travel_plan, dict):
                raise ValueError("travelPlan must be an object")
            import json

            payload = json.dumps(travel_plan, ensure_ascii=False)
            if len(payload.encode("utf-8")) > 8192:
                raise ValueError("travelPlan too large (max 8KB)")
            intent["travelPlan"] = travel_plan
        else:
            intent.pop("travelPlan", None)

    if folders is not _UNSET:
        if folders:
            intent["folders"] = folders
        else:
            intent.pop("folders", None)

    if layout_density is not _UNSET:
        from travelogue.curation.layout_density import normalize_layout_density

        if layout_density is None:
            intent.pop("layoutDensity", None)
        else:
            intent["layoutDensity"] = normalize_layout_density(layout_density)

    if photo_cull_enabled is not _UNSET:
        if photo_cull_enabled is None:
            intent.pop("photoCullEnabled", None)
        else:
            intent["photoCullEnabled"] = bool(photo_cull_enabled)

    if keep_near_duplicates is not _UNSET:
        if keep_near_duplicates is None:
            intent.pop("keepNearDuplicates", None)
        else:
            intent["keepNearDuplicates"] = bool(keep_near_duplicates)

    if featured_subjects is not _UNSET:
        from travelogue.services.cohort import normalize_featured_subjects, validate_seeds_exist

        if not featured_subjects:
            intent.pop("featuredSubjects", None)
        else:
            normalized = normalize_featured_subjects(featured_subjects)
            assets_by_id = {
                a["id"]: a for a in (trip.get("assets") or []) if a.get("id")
            }
            validate_seeds_exist(normalized, assets_by_id)
            intent["featuredSubjects"] = normalized

    intent["submittedAt"] = submitted_at or datetime.now(UTC).isoformat(
        timespec="seconds"
    )
    trip["intent"] = intent
    return intent


class TripService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()

    def trip_dir(self, trip_id: str) -> Path:
        return self.root / "trips" / trip_id

    def trip_json_path(self, trip_id: str) -> Path:
        return self.trip_dir(trip_id) / "trip.json"

    def load(self, path: Path | str) -> dict:
        p = Path(path)
        if not p.is_file():
            raise TripNotFoundError(f"E_TRIP_NOT_FOUND {p}")
        from travelogue.curation.trip_migration import strip_legacy_curation_fields

        return strip_legacy_curation_fields(load_json(p))

    def save(self, trip: dict, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(trip, ensure_ascii=False, indent=2) + "\n"
        fd, tmp_path = tempfile.mkstemp(
            suffix=".json",
            prefix=f".{p.stem}-",
            dir=p.parent,
        )
        opened = False
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                opened = True
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.replace(tmp_path, p)
            except OSError as exc:
                win_busy = os.name == "nt" and getattr(exc, "winerror", None) in (5, 32)
                if win_busy or isinstance(exc, PermissionError):
                    raise TripSaveError(
                        f"E_TRIP_SAVE_BUSY cannot replace {p.name}: file may be open elsewhere"
                    ) from exc
                raise
        except Exception:
            if not opened:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def update(
        self,
        trip_json_path: Path | str,
        mutator: Callable[[dict], T],
        *,
        max_retries: int = 3,
    ) -> T:
        """Atomic read-modify-write with ``meta.revision`` optimistic locking."""
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        path = Path(trip_json_path)
        lock = _get_trip_write_lock(path)
        last_expected = 0
        for _attempt in range(max_retries):
            with lock:
                trip = self.load(path)
                expected = meta_revision(trip)
                last_expected = expected
                result = mutator(trip)
                meta = trip.setdefault("meta", {})
                meta["revision"] = expected + 1
                trip["updatedAt"] = utc_now_iso()
                if _read_disk_revision(path) != expected:
                    continue
                self.save(trip, path)
                return result
        raise TripConflictError(
            f"revision conflict for {path} (expected {last_expected})"
        )

    apply_intent = staticmethod(apply_intent)

    def resolve_trip_root(self, trip_json: Path) -> Path:
        """Directory containing trip.json and assets/."""
        return trip_json.resolve().parent

    def resolve_trip_json(self, trip_id_or_path: str | Path, *, trips_dir: Path | None = None) -> Path:
        """Resolve tripId, trip dir, or trip.json path."""
        p = Path(trip_id_or_path)
        if p.is_file():
            return p.resolve()

        cwd = Path.cwd()
        cwd_trip_json = cwd / "trip.json"
        cwd_trip_id = cwd.name if cwd_trip_json.is_file() else None
        normalized = str(p).replace("\\", "/").strip("/")

        search_roots: list[Path] = [p, self.root / p, cwd / p]
        if cwd_trip_id:
            if p in (Path("."), Path("..")) or normalized in (
                cwd_trip_id,
                f"trips/{cwd_trip_id}",
                f"./{cwd_trip_id}",
            ):
                search_roots.insert(0, cwd)

        seen: set[Path] = set()
        for root in search_roots:
            try:
                resolved = root.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.is_dir():
                trip_json = resolved / "trip.json"
                if trip_json.is_file():
                    return trip_json.resolve()

        if p.suffix == ".json" and p.exists():
            return p.resolve()

        base = trips_dir or (self.root / "trips")
        trip_key = p.name if normalized.startswith("trips/") else str(trip_id_or_path)
        candidate = base / trip_key / "trip.json"
        if candidate.is_file():
            return candidate.resolve()

        if cwd_trip_id and str(trip_id_or_path) == cwd_trip_id:
            return cwd_trip_json.resolve()

        raise TripNotFoundError(f"E_TRIP_NOT_FOUND {trip_id_or_path}")


def persist_trip_snapshot(
    svc: TripService,
    trip_json_path: Path | str,
    work: dict,
    *,
    max_retries: int = 3,
) -> None:
    """Merge an in-memory trip dict onto disk via revision CAS."""

    def mutator(trip: dict) -> None:
        for key, value in work.items():
            trip[key] = value

    svc.update(trip_json_path, mutator, max_retries=max_retries)


def write_new_trip(svc: TripService, trip: dict, trip_json_path: Path | str) -> None:
    """Initial trip.json write when no concurrent CAS is required."""
    svc.save(trip, trip_json_path)
