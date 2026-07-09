"""HTML rendering (Agent 3)."""

import travelogue.render.admission_golden  # noqa: F401
from travelogue.render.engine import RenderError, render_trip, render_trip_surfaces

__all__ = ["RenderError", "render_trip", "render_trip_surfaces"]
