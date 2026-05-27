"""Phase 2 automated acceptance prerequisites (AC-P2 / UX-P2 / LS-P2).

Runs static checks + optional longshot stability when trips are provided.

Usage:
  python scripts/phase2_studio_acceptance.py
  python scripts/phase2_studio_acceptance.py --trips-dir trips
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.paths import STUDIO_TEMPLATE_DIR
from travelogue.web.studio_chrome import should_inject_studio_chrome
from travelogue.web.studio_stages import all_stage_hints, ingest_stage_hint


def _check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok


def run_checks(*, trips_dir: Path | None) -> int:
    ok = True
    ok &= _check("studio.html", (STUDIO_TEMPLATE_DIR / "studio.html").is_file())
    ok &= _check("preview-toolbar.js", (STUDIO_TEMPLATE_DIR / "preview-toolbar.js").is_file())
    ok &= _check("studio_stages.yaml", (STUDIO_TEMPLATE_DIR / "studio_stages.yaml").is_file())
    ok &= _check("stage hints loaded", bool(all_stage_hints().get("llm_narrate")))
    ok &= _check("ingest hint tier", ingest_stage_hint(80) == "约 1 分钟")
    ok &= _check(
        "longshot page not in chrome allowlist",
        not should_inject_studio_chrome("index-longshot.html"),
    )
    ok &= _check(
        "preview page in chrome allowlist",
        should_inject_studio_chrome("index.html"),
    )

    if trips_dir is not None:
        script = ROOT / "scripts" / "phase2_longshot_stability.py"
        proc = subprocess.run(
            [sys.executable, str(script), str(trips_dir), "--min-success", "0.8"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        print(proc.stdout.strip())
        if proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)
        ok &= _check("LS-P2-01 longshot stability", proc.returncode == 0)
    else:
        print("[SKIP] LS-P2-01 — pass --trips-dir to run longshot stability")

    print("\nManual gates still required: AC-P2-01a/b, AC-P2-02, PF-P2-* timing with real users.")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 automated acceptance checks")
    parser.add_argument("--trips-dir", type=Path, default=None)
    args = parser.parse_args()
    return run_checks(trips_dir=args.trips_dir)


if __name__ == "__main__":
    raise SystemExit(main())
