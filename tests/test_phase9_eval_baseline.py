from __future__ import annotations

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
    proc = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], check=True)
    assert proc.returncode == 0
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))

    assert "cull_keep_ratio_non_featured" in data
    assert "final_keep_ratio_non_featured" in data
    assert "excluded_by_reason" in data
    assert "fail_open_rate" in data
    assert "ingest_elapsed_ms" in data
    assert data["tripCount"] == 2
    assert data["fail_open_rate"] == 0.5
    assert data["excluded_by_reason"]["blur"] == 2
    assert data["excluded_by_reason"]["cull_quota"] == 1
    rec = data.get("phase92Recommendations") or {}
    assert "recommendedConfig" in rec
    assert "m4_bucketed_blur_thresholds" in rec
    assert "m5_duplicate_group_penalty" in rec
    assert "m6_cull_explain" in rec
    assert "m7_ml_cache" in rec

