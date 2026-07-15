"""Ingest partial persist helpers (Pipeline Throughput · merge mutator)."""

from __future__ import annotations

from travelogue.services.trip import STAMP_RENDERED_REVISION

# Top-level keys ingest may write during / at end of import.
_INGEST_OWNED_TOP = (
    "assets",
    "coverAssetId",
)

# curation keys owned by ingest finalize / low-res marks
_INGEST_CURATION_KEYS = (
    "excludedLowResAssetIds",
)

# pipeline keys owned by ingest (do not clobber HTTP-side locks blindly)
_INGEST_PIPELINE_KEYS = (
    "ingestStats",
    "status",
    "lastBatchId",
    "pendingAssets",
    "runs",
    "timings",
)

# HTTP / Studio user writes — never clobber from pipeline memory snapshot.
_HTTP_OWNED_TOP = frozenset({"intent", "userNotes"})

# Pipeline-owned structure after curate (safe to push from memory after sync).
_PIPELINE_STRUCTURE_TOP = (
    "chapters",
    "screens",
    "epilogue",
    "export",
    "exportLayout",
    "templateId",
    "curation",
)


def merge_ingest_partial(disk_trip: dict, *, memory_trip: dict) -> None:
    """Incrementally merge ingest-owned fields onto disk trip.

    Prohibits ``disk_trip.clear(); disk_trip.update(full_memory_trip)``.
    Preserves concurrent HTTP writes (intent / copy / chapters / screens).
    """
    for key in _INGEST_OWNED_TOP:
        if key in memory_trip:
            val = memory_trip[key]
            disk_trip[key] = list(val) if key == "assets" and isinstance(val, list) else val

    mem_cur = memory_trip.get("curation")
    if isinstance(mem_cur, dict):
        disk_cur = disk_trip.get("curation")
        if not isinstance(disk_cur, dict):
            disk_cur = {}
            disk_trip["curation"] = disk_cur
        for key in _INGEST_CURATION_KEYS:
            if key in mem_cur:
                disk_cur[key] = mem_cur[key]

    mem_pipe = memory_trip.get("pipeline")
    if isinstance(mem_pipe, dict):
        disk_pipe = disk_trip.get("pipeline")
        if not isinstance(disk_pipe, dict):
            disk_pipe = {}
            disk_trip["pipeline"] = disk_pipe
        for key in _INGEST_PIPELINE_KEYS:
            if key in mem_pipe:
                disk_pipe[key] = mem_pipe[key]
        mem_locks = mem_pipe.get("locks")
        if isinstance(mem_locks, dict):
            disk_locks = disk_pipe.get("locks")
            if not isinstance(disk_locks, dict):
                disk_pipe["locks"] = dict(mem_locks)
            else:
                # Only fill missing lock keys; never clear an HTTP-set lock.
                for lk, lv in mem_locks.items():
                    if lk not in disk_locks:
                        disk_locks[lk] = lv

    # meta dates may be filled during finalize; merge date fields only.
    # title / places / tone are HTTP-intent mirrors — never clobber mid-ingest.
    mem_meta = memory_trip.get("meta")
    if isinstance(mem_meta, dict):
        disk_meta = disk_trip.get("meta")
        if not isinstance(disk_meta, dict):
            disk_meta = {}
            disk_trip["meta"] = disk_meta
        for key in ("dateStart", "dateEnd", "dates"):
            if key in mem_meta:
                disk_meta[key] = mem_meta[key]


def merge_pipeline_persist(disk_trip: dict, *, memory_trip: dict) -> None:
    """Stage-end persist: push pipeline fields without clobbering HTTP intent/notes.

    Unlike a full ``disk.update(memory)``, ``intent`` / ``userNotes`` on disk win
    when both sides have values (AC-ARC-02-parallel).
    """
    merge_ingest_partial(disk_trip, memory_trip=memory_trip)

    for key in _PIPELINE_STRUCTURE_TOP:
        if key == "curation":
            continue  # already partially merged
        if key in memory_trip:
            disk_trip[key] = memory_trip[key]

    mem_cur = memory_trip.get("curation")
    if isinstance(mem_cur, dict):
        disk_cur = disk_trip.get("curation")
        if not isinstance(disk_cur, dict):
            disk_trip["curation"] = dict(mem_cur)
        else:
            for ck, cv in mem_cur.items():
                disk_cur[ck] = cv

    # Intent: only seed if disk has none (pre-ingest flush); never overwrite HTTP.
    mem_intent = memory_trip.get("intent")
    if isinstance(mem_intent, dict) and not isinstance(disk_trip.get("intent"), dict):
        disk_trip["intent"] = dict(mem_intent)
    mem_notes = memory_trip.get("userNotes")
    if mem_notes is not None and disk_trip.get("userNotes") in (None, ""):
        disk_trip["userNotes"] = mem_notes

    # When disk already has HTTP intent, keep meta title/places/tone aligned with it
    # (do not push stale memory mirrors). Otherwise seed from memory.
    disk_intent = disk_trip.get("intent")
    mem_meta = memory_trip.get("meta")
    if isinstance(mem_meta, dict):
        disk_meta = disk_trip.get("meta")
        if not isinstance(disk_meta, dict):
            disk_meta = {}
            disk_trip["meta"] = disk_meta
        if isinstance(disk_intent, dict):
            for key in ("title", "places", "tone"):
                if key in disk_intent:
                    disk_meta[key] = disk_intent[key]
                elif key in mem_meta and key not in disk_meta:
                    disk_meta[key] = mem_meta[key]
        else:
            for key in ("title", "places", "tone"):
                if key in mem_meta:
                    disk_meta[key] = mem_meta[key]
        # mark_render_bundle_current sets this on memory meta; TripService.update
        # consumes it from the disk trip the mutator edits. Without this hand-off,
        # post-render timings/status persists bump revision ahead of renderedRevision
        # and false-flag「预览产物已过期」right after a fresh import.
        if mem_meta.get(STAMP_RENDERED_REVISION):
            disk_meta[STAMP_RENDERED_REVISION] = True

    # Copy any other non-HTTP top-level keys from memory (template extras, etc.)
    for key, value in memory_trip.items():
        if key in _HTTP_OWNED_TOP:
            continue
        if key in disk_trip or key in _INGEST_OWNED_TOP or key in _PIPELINE_STRUCTURE_TOP:
            continue
        if key in ("meta", "pipeline", "version", "tripId", "createdAt", "updatedAt"):
            continue
        disk_trip[key] = value


def make_ingest_merge_mutator(memory_trip: dict):
    """Return a TripService.update mutator that applies :func:`merge_ingest_partial`."""

    def mutator(disk_trip: dict) -> None:
        merge_ingest_partial(disk_trip, memory_trip=memory_trip)

    return mutator


def make_pipeline_persist_mutator(memory_trip: dict):
    """Return a TripService.update mutator for stage-end pipeline persist."""

    def mutator(disk_trip: dict) -> None:
        merge_pipeline_persist(disk_trip, memory_trip=memory_trip)

    return mutator


def make_intent_flush_mutator(memory_trip: dict):
    """Flush intent + mirrored notes/meta from memory onto disk (pre-ingest)."""

    def mutator(disk_trip: dict) -> None:
        if "intent" in memory_trip:
            disk_trip["intent"] = memory_trip["intent"]
        if "userNotes" in memory_trip:
            disk_trip["userNotes"] = memory_trip["userNotes"]
        mem_meta = memory_trip.get("meta")
        if isinstance(mem_meta, dict):
            disk_meta = disk_trip.setdefault("meta", {})
            if not isinstance(disk_meta, dict):
                disk_trip["meta"] = {}
                disk_meta = disk_trip["meta"]
            for key in ("title", "places", "tone", "dateStart", "dateEnd", "dates"):
                if key in mem_meta:
                    disk_meta[key] = mem_meta[key]

    return mutator


def make_intent_folders_merge_mutator(memory_trip: dict):
    """Deep-merge ``intent.folders`` from memory onto disk (Stable-QH D-QH-02).

    Pipeline persist must not clobber HTTP-owned intent (ADR-008). After ingest,
    ``featuredDetected`` is applied only in memory; this mutator pushes *folders*
    keys onto disk without replacing the rest of intent.
    """

    def mutator(disk_trip: dict) -> None:
        mem_intent = memory_trip.get("intent")
        if not isinstance(mem_intent, dict):
            return
        mem_folders = mem_intent.get("folders")
        if not isinstance(mem_folders, dict) or not mem_folders:
            return
        disk_intent = disk_trip.get("intent")
        if not isinstance(disk_intent, dict):
            disk_trip["intent"] = {"version": mem_intent.get("version", "1"), "folders": dict(mem_folders)}
            # Keep required shape if memory has more; prefer minimal seed when disk empty.
            for key in ("title", "places", "placesUserSet", "userNotes", "photoCullEnabled", "keepNearDuplicates"):
                if key in mem_intent:
                    disk_trip["intent"][key] = mem_intent[key]
            return
        disk_folders = dict(disk_intent.get("folders") or {})
        disk_folders.update(mem_folders)
        disk_intent["folders"] = disk_folders

    return mutator
