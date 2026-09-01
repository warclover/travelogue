"""EA-02a runner: trip table, caliber wiring, no pipeline_isolation."""

from __future__ import annotations

import importlib.util
import json
import sys

from tests._repo_root import repo_root

ROOT = repo_root(__file__)


def _load_mod():
    path = ROOT / "scripts" / "ea02a_shadow_compare.py"
    spec = importlib.util.spec_from_file_location("ea02a_shadow_compare_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ea02a_shadow_compare_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_trip_table_has_three_bands_and_twenty_trips() -> None:
    mod = _load_mod()
    assert len(mod.TRIP_TABLE) == 20
    bands = {band for _tid, band, _n in mod.TRIP_TABLE}
    assert bands == {"sparse-60-140", "regular-196-326", "overflow-424-1000"}
    counts = {band: 0 for band in bands}
    for _tid, band, _n in mod.TRIP_TABLE:
        counts[band] += 1
    assert all(n >= 3 for n in counts.values())
    assert "phase16-dogfood" not in mod.BAND_BY_TRIP


def test_tie_tolerance_is_declared_and_positive() -> None:
    mod = _load_mod()
    assert mod.TIE_TOLERANCE == 0.02
    assert mod.CALIBER_DOC == "docs/成册指标口径定义.md"


def test_table_keys_are_folder_names_not_json_trip_id() -> None:
    mod = _load_mod()
    assert "_bai_w1b_titleart" in mod.BAND_BY_TRIP
    assert "demo-65db8fd377" in mod.BAND_BY_TRIP
    ids = mod.select_trips(None, None)
    assert ids[10] == "_bai_w1b_titleart"


def test_hash_mismatch_invalidates_both_rows() -> None:
    mod = _load_mod()
    rows = [
        {
            "tripId": "t1",
            "pipeline": "mosaic",
            "inputSnapshotHash": "aaa",
            "eligibleSequenceHash": "s1",
            "status": "ok",
            "tripFail": False,
            "integrityFail": False,
        },
        {
            "tripId": "t1",
            "pipeline": "series",
            "inputSnapshotHash": "bbb",
            "eligibleSequenceHash": "s1",
            "status": "ok",
            "tripFail": False,
            "integrityFail": False,
        },
    ]
    mod.invalidate_hash_pairs(rows)
    assert all(r["status"] == "inputInvalid" for r in rows)


def test_from_jsonl_reaggregates_without_compose(tmp_path) -> None:
    mod = _load_mod()
    src = tmp_path / "in.jsonl"
    md = tmp_path / "out.md"
    out = tmp_path / "out.jsonl"
    rows = [
        {
            "comparisonRunId": "ea02a-test",
            "tripId": "demo-album",
            "pipeline": "mosaic",
            "status": "ok",
            "coverage": 0.9,
            "placedEligible": 9,
            "eligible": 10,
            "band": "sparse-60-140",
            "planMsMedian": 1,
            "codeRevision": "abc",
            "overflowCapped": None,
            "placementGap": 1,
        },
        {
            "comparisonRunId": "ea02a-test",
            "tripId": "demo-album",
            "pipeline": "series",
            "status": "ok",
            "coverage": 0.8,
            "placedEligible": 8,
            "eligible": 10,
            "band": "sparse-60-140",
            "planMsMedian": 2,
            "codeRevision": "abc",
            "overflowCapped": 0,
            "placementGap": 2,
            "intakeLoss": 0,
        },
    ]
    src.write_text(
        "\n".join(json.dumps(r) for r in rows)
        + "\n"
        + json.dumps({"_summary": {"comparisonRunId": "ea02a-test", "warmup": 1, "runs": 3}})
        + "\n",
        encoding="utf-8",
    )
    rc = mod.main(
        [
            "--from-jsonl",
            str(src),
            "--write-markdown",
            str(md),
            "--write-jsonl",
            str(out),
        ]
    )
    assert rc == 0
    text = md.read_text(encoding="utf-8")
    assert "已完成 · 有阻断性发现 · 非质量通过" in text
    assert "all-valid coverage" in text
    assert "paired-ok coverage" in text
    src_blobs, _, _ = mod.split_jsonl_file(src)
    out_blobs, _, out_meta = mod.split_jsonl_file(out)
    assert out_blobs == src_blobs
    digest = mod.hash_data_row_blobs(src_blobs)
    assert out_meta["dataRowsHash"] == digest
    assert digest in text
    summary_line = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines() if x.startswith('{"_summary"')][0]
    assert summary_line["_summary"]["coverageSets"]["pairedOk"]["nPairs"] == 1


def _pair_row_delta(markdown: str, trip_id: str) -> str:
    needle = f"| `{trip_id}` |"
    for line in markdown.splitlines():
        if line.startswith(needle):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            return cells[4]
    raise AssertionError(f"no pairing row for {trip_id}")


def test_markdown_delta_emdash_when_either_arm_invalid() -> None:
    mod = _load_mod()
    rows = [
        {
            "tripId": "demo-album",
            "pipeline": "mosaic",
            "status": "ok",
            "coverage": 0.9,
            "placedEligible": 9,
            "eligible": 10,
            "band": "sparse-60-140",
            "planMsMedian": 1,
            "codeRevision": "abc",
            "placementGap": 0,
        },
        {
            "tripId": "demo-album",
            "pipeline": "series",
            "status": "ok",
            "coverage": 0.8,
            "placedEligible": 8,
            "eligible": 10,
            "band": "sparse-60-140",
            "planMsMedian": 2,
            "codeRevision": "abc",
            "overflowCapped": 0,
            "placementGap": 2,
            "intakeLoss": 0,
        },
        {
            "tripId": "demo-65db8fd377",
            "pipeline": "mosaic",
            "status": "outputInvalid",
            "coverage": 0.95,
            "placedEligible": 43,
            "eligible": 45,
            "band": "regular-196-326",
            "planMsMedian": 1,
            "codeRevision": "abc",
            "placementGap": 1,
            "duplicatePlacements": 1,
        },
        {
            "tripId": "demo-65db8fd377",
            "pipeline": "series",
            "status": "ok",
            "coverage": 0.28,
            "placedEligible": 13,
            "eligible": 45,
            "band": "regular-196-326",
            "planMsMedian": 90,
            "codeRevision": "abc",
            "overflowCapped": 2,
            "placementGap": 30,
            "intakeLoss": 0,
        },
    ]
    summary = mod.folio.aggregate_shadow_rows(rows, tie_tolerance=mod.TIE_TOLERANCE)
    md = mod.render_markdown(
        rows=rows,
        summary=summary,
        comparison_run_id="ea02a-test",
        warmup=1,
        runs=3,
        skipped=[],
        unofficial=False,
    )
    assert _pair_row_delta(md, "demo-album") == "-10.0%"
    assert _pair_row_delta(md, "demo-65db8fd377") == "—"
    assert "纯 placement gap" in md
    assert "gap 主导的混合原因" in md
    assert "干净的容量内失败" not in md


def test_from_jsonl_rejects_mutated_data_rows(tmp_path) -> None:
    mod = _load_mod()
    src = tmp_path / "in.jsonl"
    md = tmp_path / "out.md"
    out = tmp_path / "out.jsonl"
    row = {
        "comparisonRunId": "ea02a-test",
        "tripId": "demo-album",
        "pipeline": "mosaic",
        "status": "ok",
        "coverage": 0.9,
        "placedEligible": 9,
        "eligible": 10,
        "band": "sparse-60-140",
        "planMsMedian": 1,
        "codeRevision": "abc",
    }
    other = dict(row)
    other["pipeline"] = "series"
    other["coverage"] = 0.8
    other["placedEligible"] = 8
    other["overflowCapped"] = 0
    other["placementGap"] = 2
    other["intakeLoss"] = 0
    src.write_text(
        json.dumps(row) + "\n" + json.dumps(other) + "\n"
        + json.dumps({"_summary": {"comparisonRunId": "ea02a-test", "warmup": 1, "runs": 3}})
        + "\n",
        encoding="utf-8",
    )
    assert mod.main(["--from-jsonl", str(src), "--write-markdown", str(md), "--write-jsonl", str(out)]) == 0
    blobs, parsed, meta = mod.split_jsonl_file(out)
    assert meta["dataRowsHash"] == mod.hash_data_row_blobs(blobs)
    tampered = tmp_path / "tampered.jsonl"
    mutated = json.loads(blobs[0])
    mutated["coverage"] = 0.1
    tampered.write_bytes(
        mod.serialize_data_row(mutated) + blobs[1]
        + (json.dumps({"_summary": meta}, ensure_ascii=False) + "\n").encode("utf-8")
    )
    try:
        mod.main(
            [
                "--from-jsonl",
                str(tampered),
                "--write-markdown",
                str(tmp_path / "tampered.md"),
                "--write-jsonl",
                str(tmp_path / "tampered-out.jsonl"),
            ]
        )
    except SystemExit as exc:
        assert "dataRowsHash mismatch" in str(exc)
    else:
        raise AssertionError("expected dataRowsHash mismatch")

