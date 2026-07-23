"""Clustering cache CLI (Phase 3 M14)."""

from __future__ import annotations

from pathlib import Path

import typer

from travelogue.cli._apps import cluster_app
from travelogue.config import get_config
from travelogue.runtime import app_context_for_trips_dir
from travelogue.services.trip import TripNotFoundError, TripService, persist_trip_snapshot


def _cluster_resolve(
    trip: str, *, trips_dir: Path | None
) -> tuple[TripService, Path]:
    """Resolve trip.json; loose mode when trips_dir is omitted (AAD-02)."""
    ctx = app_context_for_trips_dir(trips_dir)
    svc = ctx.trip_service()
    try:
        return svc, svc.resolve_trip_json(trip, trips_dir=trips_dir)
    except TripNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@cluster_app.command("recluster")
def cluster_recluster(
    trip: str = typer.Argument(..., help="trip id or path to trip.json"),
    trips_dir: Path | None = typer.Option(
        None, "--trips-dir", help="trips root when trip is an id"
    ),
    force: bool = typer.Option(True, "--force/--no-force", help="force full cache rebuild"),
) -> None:
    """Re-run scene clustering with optional force full embed (F-CLU-CACHE-03)."""
    from dataclasses import replace

    from travelogue.curation.clustering import run_clustering_layer

    svc, trip_json = _cluster_resolve(trip, trips_dir=trips_dir)
    trip_dir = trip_json.parent
    body = svc.load(trip_json)
    base = get_config(reload=True)
    clustering = replace(base.clustering, enabled="true", force_recluster=force)
    vision = replace(base.vision, enabled="true")
    cfg = replace(base, clustering=clustering, vision=vision)
    if force:
        from travelogue.vision.cache import clear_cluster_cache

        clear_cluster_cache(trip_dir)
    result = run_clustering_layer(body, trip_dir=trip_dir, cfg=cfg)
    persist_trip_snapshot(svc, trip_json, body)
    typer.echo(
        f"OK recluster · mode={result.mode} segments={result.geo_event_count} "
        f"clusters={result.scene_cluster_count} force={force}"
    )


@cluster_app.command("reshotgroup")
def cluster_reshotgroup(
    trip: str = typer.Argument(..., help="trip id or path to trip.json"),
    trips_dir: Path | None = typer.Option(
        None, "--trips-dir", help="trips root when trip is an id"
    ),
    look: bool = typer.Option(
        True,
        "--look/--no-look",
        help="Run M2 look split when CLIP/appearance is available (default: on)",
    ),
) -> None:
    """Re-run smart shot grouping from existing sceneClusterId (SSG · no recluster)."""
    from dataclasses import replace

    from travelogue.curation.shot_grouping import run_shot_grouping_layer

    svc, trip_json = _cluster_resolve(trip, trips_dir=trips_dir)
    trip_dir = trip_json.parent
    body = svc.load(trip_json)
    base = get_config(reload=True)
    look_cfg = replace(base.shot_grouping.look, enabled="true" if look else "false")
    ssg = replace(base.shot_grouping, enabled="true", look=look_cfg)
    cfg = replace(base, shot_grouping=ssg)
    result = run_shot_grouping_layer(body, trip_dir=trip_dir, cfg=cfg)
    persist_trip_snapshot(svc, trip_json, body)
    typer.echo(
        f"OK reshotgroup · mode={result.mode} groups={result.group_count} "
        f"softSplits={result.soft_split_count} lookGroups={result.look_group_count}"
    )


@cluster_app.command("cache-clear")
def cluster_cache_clear(
    trip: str = typer.Argument(..., help="trip id or path to trip.json"),
    trips_dir: Path | None = typer.Option(
        None, "--trips-dir", help="trips root when trip is an id"
    ),
) -> None:
    """Remove `.cluster-cache/` for a trip (M14 · F-CLU-CACHE CLI)."""
    from travelogue.vision.cache import clear_cluster_cache

    _svc, trip_json = _cluster_resolve(trip, trips_dir=trips_dir)
    trip_dir = trip_json.parent
    if clear_cluster_cache(trip_dir):
        typer.echo(f"OK cleared cluster cache · {trip_dir / '.cluster-cache'}")
    else:
        typer.echo(f"OK no cluster cache · {trip_dir}")


@cluster_app.command("pending-assets")
def cluster_pending_assets(
    trip: str = typer.Argument(..., help="trip id or path to trip.json"),
    trips_dir: Path | None = typer.Option(
        None, "--trips-dir", help="trips root when trip is an id"
    ),
) -> None:
    """List pipeline.pendingAssets after structure lock (F-CLU-CACHE-04)."""
    from travelogue.vision.cache import list_pending_assets

    svc, trip_json = _cluster_resolve(trip, trips_dir=trips_dir)
    body = svc.load(trip_json)
    pending = list_pending_assets(body)
    status = (body.get("pipeline") or {}).get("status") or "unknown"
    typer.echo(f"pipeline.status={status}")
    if pending:
        for aid in pending:
            typer.echo(aid)
    else:
        typer.echo("(no pending assets)")


@cluster_app.command("process-pending")
def cluster_process_pending(
    trip: str = typer.Argument(..., help="trip id or path to trip.json"),
    trips_dir: Path | None = typer.Option(
        None, "--trips-dir", help="trips root when trip is an id"
    ),
    run: bool = typer.Option(
        True,
        "--run/--no-run",
        help="Re-run scene clustering across the trip (chapter boundaries stay frozen)",
    ),
    clear: bool = typer.Option(
        True,
        "--clear/--keep",
        help="Empty pipeline.pendingAssets after processing (default: clear)",
    ),
) -> None:
    """Drain pipeline.pendingAssets after a structure lock (F-CLU-CACHE-04).

    Optionally re-runs the clustering layer so the new ids pick up scene tags;
    chapter boundaries and locks remain untouched per PRD §7.4.
    """
    from dataclasses import replace

    from travelogue.curation.clustering import run_clustering_layer
    from travelogue.vision.cache import (
        clear_pending_assets,
        is_pipeline_locked,
        list_pending_assets,
    )

    svc, trip_json = _cluster_resolve(trip, trips_dir=trips_dir)
    trip_dir = trip_json.parent
    body = svc.load(trip_json)
    pending_before = list_pending_assets(body)
    status_before = (body.get("pipeline") or {}).get("status") or "unknown"
    if not pending_before:
        typer.echo(f"OK no pending assets · status={status_before}")
        return
    if not is_pipeline_locked(body):
        typer.echo(
            "WARN trip is not in a locked state; pendingAssets typically appear only after "
            f"structure lock (status={status_before}). Proceeding anyway."
        )

    cluster_mode: str = "skipped"
    cluster_clusters = 0
    cluster_segments = 0
    if run:
        base = get_config(reload=True)
        clustering = replace(base.clustering, enabled="true")
        cfg = replace(base, clustering=clustering)
        result = run_clustering_layer(body, trip_dir=trip_dir, cfg=cfg)
        cluster_mode = result.mode
        cluster_clusters = result.scene_cluster_count
        cluster_segments = result.geo_event_count

    cleared: list[str] = []
    if clear:
        cleared = clear_pending_assets(body)

    persist_trip_snapshot(svc, trip_json, body)
    typer.echo(
        "OK process-pending · "
        f"pending={len(pending_before)} cleared={len(cleared)} "
        f"cluster_mode={cluster_mode} segments={cluster_segments} clusters={cluster_clusters} "
        f"status={status_before}"
    )
