
from __future__ import annotations
from tests._repo_root import repo_root

import json
import subprocess
import sys
from pathlib import Path


def test_phase9_eval_baseline_outputs_required_metrics(tmp_path: Path) -> None:
    golden = tmp_path / "golden.json"
    quality = tmp_path / "quality.json"
    out = tmp_path / "baseline.json"
    golden.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "tripId": "t1",
                        "metrics": {
                            "scanned": 10,
                            "cullUserLine": "经挑选 9 张进入排版",
                            "nonFeaturedKeepRatio": 0.8,
                            "ingestMs": 1200.0,
                            "excludedByReason": {"cull_quota": 1},
                            "mlFallbackRateL1": 0.0,
                            "branchFallbackRateL2": 0.1,
                            "branchFallbackByReasonL2": {"gray_zone": 1},
                            "failOpenRateL3": 0.0,
                        },
                    },
                    {
                        "tripId": "t2",
                        "metrics": {
                            "scanned": 20,
                            "layoutEligibleCount": 16,
                            "nonFeaturedKeepRatio": 0.75,
                            "ingestMs": 1800.0,
                            "excludedByReason": {"blur": 2},
                            "failOpen": True,
                            "mlFallbackRateL1": 1.0,
                            "branchFallbackRateL2": 0.4,
                            "branchFallbackByReasonL2": {"face_signal_missing": 2},
                            "failOpenRateL3": 1.0,
                        },
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    quality.write_text(
        json.dumps({"w1Status": "done", "w2Status": "partial", "w3Status": "done"}),
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "scripts/phase9_eval_baseline.py",
        "--golden",
        str(golden),
        "--quality",
        str(quality),
        "--write",
        str(out),
    ]
    proc = subprocess.run(cmd, cwd=repo_root(__file__), check=True)
    assert proc.returncode == 0
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))

    assert "cull_keep_ratio_non_featured" in data
    assert "final_keep_ratio_non_featured" in data
    assert "excluded_by_reason" in data
    assert "fail_open_rate" in data
    assert "ingest_elapsed_ms" in data
    assert "l1_ml_fallback_rate" in data
    assert "l2_branch_fallback_rate" in data
    assert "l2_branch_fallback_by_reason" in data
    assert "l3_fail_open_rate" in data
    assert data["tripCount"] == 2
    assert data["fail_open_rate"] == 0.5
    assert data["excluded_by_reason"]["blur"] == 2
    assert data["excluded_by_reason"]["cull_quota"] == 1
    assert data["l1_ml_fallback_rate"]["avg"] == 0.5
    assert data["l2_branch_fallback_rate"]["avg"] == 0.25
    assert data["l2_branch_fallback_by_reason"]["face_signal_missing"] == 2
    assert data["l3_fail_open_rate"]["max"] == 1.0
    rec = data.get("phase92Recommendations") or {}
    assert "recommendedConfig" in rec
    assert "m4_bucketed_blur_thresholds" in rec
    assert "m5_duplicate_group_penalty" in rec
    assert "m6_cull_explain" in rec
    assert "m7_ml_cache" in rec

