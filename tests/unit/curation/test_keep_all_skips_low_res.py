"""P9-F3 · keep_all 跳过低分硬丢；keep_bursts / 旧盘不跳。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from travelogue.curation.curate import _curate_preflight


def _minimal_trip(*, intent: dict) -> dict:
    assets = [
        {
            "id": f"a{i}",
            "type": "image",
            "relPath": f"a{i}.jpg",
            "takenAt": "2024-05-01T10:00:00",
            "nativeWidth": 80,
            "nativeHeight": 60,
            "layoutEligible": True,
        }
        for i in range(4)
    ]
    return {
        "tripId": "t-keep-all",
        "intent": intent,
        "meta": {"title": "测试"},
        "assets": assets,
        "pipeline": {},
        "curation": {},
    }


def _run_preflight(trip, tmp_path, mock_low):
    with patch(
        "travelogue.curation.curate.apply_low_resolution_exclusion",
        mock_low,
    ):
        with patch(
            "travelogue.curation.time_outlier.apply_time_outlier_marks",
            return_value=[],
        ):
            with patch(
                "travelogue.curation.time_segments.cluster_time_segments",
                return_value=[],
            ):
                with patch(
                    "travelogue.curation.curate.layout_eligible_assets",
                    return_value=list(trip["assets"]),
                ):
                    with patch(
                        "travelogue.curation.curate.sync_trip_covers",
                        return_value="a0",
                    ):
                        return _curate_preflight(
                            trip,
                            export_layout="web",
                            layout_engine=None,
                            trip_dir=tmp_path,
                            cfg=None,
                            saved_memory_anchors=[],
                        )


def test_keep_all_skips_low_resolution_exclusion(tmp_path) -> None:
    trip = _minimal_trip(intent={"photoKeepMode": "keep_all", "photoCullEnabled": False})
    mock_low = MagicMock(return_value="should-not-run")
    _run_preflight(trip, tmp_path, mock_low)
    mock_low.assert_not_called()


def test_keep_bursts_still_runs_low_resolution_exclusion(tmp_path) -> None:
    trip = _minimal_trip(
        intent={
            "photoKeepMode": "keep_bursts",
            "photoCullEnabled": True,
            "keepNearDuplicates": True,
        }
    )
    mock_low = MagicMock(return_value=None)
    _run_preflight(trip, tmp_path, mock_low)
    mock_low.assert_called_once()


def test_legacy_no_mode_still_runs_low_res(tmp_path) -> None:
    trip = _minimal_trip(
        intent={"photoCullEnabled": False, "keepNearDuplicates": True}
    )
    mock_low = MagicMock(return_value=None)
    _run_preflight(trip, tmp_path, mock_low)
    mock_low.assert_called_once()
