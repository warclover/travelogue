"""Studio handler routing helpers."""

from __future__ import annotations

from travelogue.web.studio_handlers.common import (
    match_entry,
    match_trip_curate,
    match_trip_intent,
    match_trip_pipeline,
    match_trip_suffix,
)
from travelogue.web.studio_handlers.paths import (
    CURATE_SUFFIX,
    INTENT_SUFFIX,
    PIPELINE_SUFFIX,
    TRIPS_PATH,
)


def test_match_trip_suffix_extracts_trip_id() -> None:
    path = f"{TRIPS_PATH}/my-trip{INTENT_SUFFIX}"
    assert match_trip_suffix(path, INTENT_SUFFIX) == "my-trip"


def test_match_trip_suffix_rejects_nested_trip_id() -> None:
    path = f"{TRIPS_PATH}/a/b{INTENT_SUFFIX}"
    assert match_trip_suffix(path, INTENT_SUFFIX) is None


def test_match_wrappers_align_with_suffix() -> None:
    tid = "demo-01"
    assert match_entry(f"{TRIPS_PATH}/{tid}/entry") == tid
    assert match_trip_intent(f"{TRIPS_PATH}/{tid}{INTENT_SUFFIX}") == tid
    assert match_trip_pipeline(f"{TRIPS_PATH}/{tid}{PIPELINE_SUFFIX}") == tid
    assert match_trip_curate(f"{TRIPS_PATH}/{tid}{CURATE_SUFFIX}") == tid
