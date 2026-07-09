"""Trip workspace commands."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from travelogue.cli._apps import trip_app
from travelogue.cli._helpers import _trips_root
from travelogue.curation.curate import CurateError, run_curate
from travelogue.media.ingest import IngestError, ingest_into_trip
from travelogue.runtime import app_context_for_trips_dir
from travelogue.services.trip import persist_trip_snapshot
from travelogue.services.trip_factory import create_trip


@trip_app.command("new")
def cmd_trip_new(
    trip_id: str = typer.Argument(..., help="trip folder name under trips/"),
    title: str = typer.Option("待命名旅程", "--title", "-t"),
    place: str = typer.Option("旅途", "--place", "-p"),
    from_dir: Path | None = typer.Option(None, "--from", help="photo folder; chains ingest"),
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
    layout: str = typer.Option("mobile", "--layout", "-l", help="exportLayout for ingest/curate"),
    force: bool = typer.Option(False, "--force", help="allow non-empty trip dir"),
) -> None:
    """Create trip workspace (draft_ingest) and optionally ingest photos."""
    root = _trips_root(trips_dir)
    trip_dir = root / trip_id
    if trip_dir.exists() and any(trip_dir.iterdir()) and not force:
        typer.echo(f"E_TRIP_EXISTS {trip_dir} (use --force)", err=True)
        raise typer.Exit(1)
    trip_json = create_trip(trip_id, root, title=title, place=place, export_layout=layout)
    typer.echo(f"OK trip {trip_dir}")
    if from_dir:
        svc = app_context_for_trips_dir(trips_dir).trip_service()
        trip = svc.load(trip_json)
        try:
            result = ingest_into_trip(trip, trip_dir, from_dir=from_dir, generate_crops=False)
        except IngestError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        persist_trip_snapshot(svc, trip_json, trip)
        typer.echo(f"OK ingest +{result.added} assets · batch {result.batch_id}")
        if layout != "auto":
            try:
                cur = run_curate(trip, export_layout=layout, trip_dir=trip_json.parent)
            except CurateError as exc:
                typer.echo(str(exc), err=True)
                raise typer.Exit(1) from exc
            persist_trip_snapshot(svc, trip_json, trip)
            typer.echo(f"OK curate {cur.chapter_count} chapters · {cur.layout_summary}")


@trip_app.command("list")
def cmd_trip_list(
    trips_dir: Path = typer.Option(Path("trips"), "--trips-dir"),
) -> None:
    """List trips under trips_dir."""
    root = _trips_root(trips_dir)
    if not root.is_dir():
        typer.echo("(no trips directory)")
        return
    rows: list[tuple[str, str, str, str]] = []
    for d in sorted(root.iterdir()):
        tj = d / "trip.json"
        if not tj.is_file():
            continue
        try:
            trip = json.loads(tj.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        meta = trip.get("meta", {})
        pipe = trip.get("pipeline", {})
        rows.append(
            (
                trip.get("tripId", d.name),
                pipe.get("status", "?"),
                pipe.get("layoutStatus", "-") or "-",
                meta.get("title", "")[:20],
            )
        )
    if not rows:
        typer.echo("(no trips)")
        return
    for tid, status, layout_st, title in rows:
        typer.echo(f"{tid}\t{status}\t{layout_st}\t{title}")

