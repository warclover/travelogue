"""Demo verify: fixtures + golden DOM + pytest + optional album smoke."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from travelogue.demo.golden_reference import golden_reference_dir, materialize_golden_reference
from travelogue.paths import FIXTURES_DIR, GOLDEN_HTML, ROOT
from travelogue.render.golden_regression import GOLDEN_TRIP_FIXTURE, run_golden_regression
from travelogue.services.validate import validate_trip

QUICK_TEST_PATHS = [
    "tests/test_validate.py",
    "tests/test_layout_planner.py",
    "tests/test_layout_service.py",
    "tests/test_dual_layout_engine.py",
    "tests/test_demo_build.py",
    "tests/test_demo_from_album.py",
    "tests/test_dom_regression.py",
    "tests/test_demo_verify.py",
    "tests/test_golden_reference.py",
]

FIXTURE_NAMES = [
    "trip.copy_locked.json",
    "trip.ingest_ready.json",
    "trip.structure_locked.json",
    "trip.render_golden.json",
]


@dataclass
class VerifyResult:
    ok: bool
    pytest_code: int = 0
    fixture_errors: list[str] = field(default_factory=list)
    dom_errors: list[str] = field(default_factory=list)
    reference_message: str | None = None
    smoke_ok: bool | None = None
    messages: list[str] = field(default_factory=list)


def _validate_fixtures() -> list[str]:
    errors: list[str] = []
    for name in FIXTURE_NAMES:
        path = FIXTURES_DIR / name
        if not path.is_file():
            errors.append(f"missing fixture {path}")
            continue
        trip = json.loads(path.read_text(encoding="utf-8"))
        errs = [e for e in validate_trip(trip, level="all") if not e.startswith("WARN:")]
        for e in errs:
            errors.append(f"{name}: {e}")
    return errors


def _run_pytest(paths: list[str], *, full: bool) -> tuple[int, str]:
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if full:
        cmd.append("tests/")
    else:
        cmd.extend(paths)
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def _run_album_smoke(album_dir: Path) -> tuple[bool, str]:
    from travelogue.demo.build import run_demo_from_album

    with tempfile.TemporaryDirectory() as tmp:
        trips = Path(tmp) / "trips"
        try:
            result = run_demo_from_album(
                album_dir,
                trips_dir=trips,
                trip_id="demo-verify-smoke",
                title="验收",
                dedupe=False,
                validate=False,
            )
        except Exception as exc:
            return False, str(exc)
        if not result.index_html.is_file():
            return False, "smoke: index.html missing"
        if result.photo_count < 4:
            return False, f"smoke: only {result.photo_count} photos"
        return True, f"smoke OK · {result.photo_count} photos · {', '.join(result.stages)}"


def run_demo_verify(
    *,
    album_dir: Path | None = None,
    full_tests: bool = False,
    skip_pytest: bool = False,
    skip_dom: bool = False,
    sync_reference: bool = False,
    trips_dir: Path | None = None,
) -> VerifyResult:
    """Run validation gates for CI / pre-demo checklist."""
    result = VerifyResult(ok=True)
    messages = result.messages

    if not GOLDEN_HTML.is_file():
        result.ok = False
        messages.append(f"missing golden.html: {GOLDEN_HTML}")
    else:
        messages.append(f"golden.html: {GOLDEN_HTML}")

    if not GOLDEN_TRIP_FIXTURE.is_file():
        result.ok = False
        messages.append(f"missing {GOLDEN_TRIP_FIXTURE.name}")
    else:
        messages.append(f"golden fixture: {GOLDEN_TRIP_FIXTURE.name}")

    fixture_errs = _validate_fixtures()
    result.fixture_errors = fixture_errs
    if fixture_errs:
        result.ok = False
        messages.append(f"fixtures: {len(fixture_errs)} error(s)")
        for line in fixture_errs[:8]:
            messages.append(f"  {line}")
        if len(fixture_errs) > 8:
            messages.append(f"  ... and {len(fixture_errs) - 8} more")
    else:
        messages.append(f"fixtures: {len(FIXTURE_NAMES)} OK (schema+manifest)")

    if skip_dom:
        messages.append("dom regression: skipped")
    else:
        dom_errs = run_golden_regression()
        result.dom_errors = dom_errs
        if dom_errs:
            result.ok = False
            messages.append(f"dom regression: {len(dom_errs)} error(s)")
            for line in dom_errs[:10]:
                messages.append(f"  {line}")
            if len(dom_errs) > 10:
                messages.append(f"  ... and {len(dom_errs) - 10} more")
        else:
            messages.append("dom regression: OK (fixture render vs golden.html)")

    ref_dir = golden_reference_dir(trips_dir)
    if sync_reference:
        ref = materialize_golden_reference(trips_dir, force=True)
        result.reference_message = ref.message
        messages.append(ref.message)
    elif ref_dir.is_dir() and (ref_dir / "index.html").is_file():
        messages.append(f"reference trip: {ref_dir} (use --sync-reference to refresh)")
    else:
        messages.append(
            f"reference trip: not materialized ({ref_dir}); run: travelogue demo golden --sync-reference"
        )

    if not skip_pytest:
        code, out = _run_pytest(QUICK_TEST_PATHS, full=full_tests)
        result.pytest_code = code
        if code != 0:
            result.ok = False
            messages.append(f"pytest: failed (exit {code})")
            if out:
                messages.append(out[-2000:])
        else:
            label = "full" if full_tests else "quick"
            messages.append(f"pytest: {label} OK")
    else:
        messages.append("pytest: skipped")

    if album_dir is not None:
        smoke_ok, smoke_msg = _run_album_smoke(album_dir.resolve())
        result.smoke_ok = smoke_ok
        messages.append(smoke_msg)
        if not smoke_ok:
            result.ok = False

    return result
