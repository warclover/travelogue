"""Typer application instances (shared by command modules)."""

from __future__ import annotations

import typer

app = typer.Typer(help="Travelogue — photos to HTML travelogue", no_args_is_help=True)
trip_app = typer.Typer(help="Create and list trip workspaces")
demo_app = typer.Typer(help="Quick demos (real photos → HTML preview)")
llm_app = typer.Typer(help="LLM provider utilities")
media_app = typer.Typer(help="Re-export pixels from source/")
tier_app = typer.Typer(help="userTier promote (G2 serve · appendix A)")
cluster_app = typer.Typer(help="Phase 3 clustering cache & pending assets (M14)")

app.add_typer(trip_app, name="trip")
app.add_typer(demo_app, name="demo")
app.add_typer(llm_app, name="llm")
app.add_typer(media_app, name="media")
app.add_typer(tier_app, name="tier")
app.add_typer(cluster_app, name="cluster")
