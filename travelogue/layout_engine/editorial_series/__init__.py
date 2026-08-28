"""Editorial series matcher (PFM · TSU D-U-15).

Independent of ``layout_templates`` / ``mosaic`` selection cores.
``layoutEngine`` stays ``screens``; identity is ``trip.studio.edition``.
"""

from travelogue.layout_engine.editorial_series.catalog import load_official_series
from travelogue.layout_engine.editorial_series.compose import compose_portfolio_trip

__all__ = [
    "compose_portfolio_trip",
    "load_official_series",
]
