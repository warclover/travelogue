#!/usr/bin/env python3
"""Local Studio share vs draft smoke (MP-WV-01~03, partial HTML checks)."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import threading
import time
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_studio_server import _distinct_album, _free_port  # noqa: E402
from travelogue.web.serve import TripPreviewHandler  # noqa: E402
from travelogue.web.studio_jobs import reset_job_store  # noqa: E402
from travelogue.web.studio_pipeline import run_studio_pipeline  # noqa: E402


def _fetch(url: str) -> tuple[int, str]:
    with request.urlopen(url, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def _start_server(trips_dir: Path, port: int) -> ThreadingHTTPServer:
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".placeholder" / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="127.0.0.1",
        studio_port=port,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    time.sleep(0.3)
    return server


def main() -> int:
    reset_job_store()
    with tempfile.TemporaryDirectory(prefix="share-smoke-") as tmp:
        tmp_path = Path(tmp)
        album = _distinct_album(tmp_path, 6)
        trips_dir = tmp_path / "trips"
        trips_dir.mkdir()
        result = run_studio_pipeline(
            album,
            trips_dir=trips_dir,
            title="Share 对照",
            place="本地",
            dedupe=False,
        )
        trip_id = result.trip_id
        port = _free_port()
        server = _start_server(trips_dir, port)
        base = f"http://127.0.0.1:{port}/{trip_id}"
        checks: dict[str, dict] = {}

        try:
            _, draft_html = _fetch(f"{base}/index.html")
            _, share_html = _fetch(f"{base}/index.html?share=1")
            _, share_mobile_html = _fetch(f"{base}/index-mobile.html?share=1")

            checks["MP-WV-01"] = {
                "passed": (
                    'data-preview-share="on"' in share_html
                    and 'data-preview-toolbar="on"' not in share_html
                    and "preview-toolbar--share-minimal" not in share_html
                    and "preview-toolbar/index.js" in share_html
                ),
                "notes": "share body attr + minimal init via JS (no full toolbar DOM at inject)",
            }
            checks["MP-WV-02"] = {
                "passed": (
                    'data-preview-toolbar="on"' in draft_html
                    and 'data-preview-share="on"' not in draft_html
                    and "preview-toolbar/index.js" in draft_html
                ),
                "notes": "draft 注入完整 toolbar chrome",
            }
            checks["MP-WV-03"] = {
                "passed": (
                    'data-preview-share="on"' in share_mobile_html
                    and 'data-preview-toolbar="on"' not in share_mobile_html
                    and "<html" in share_mobile_html
                ),
                "notes": "mobile share 同样走 share chrome",
            }

            trip = json.loads((trips_dir / trip_id / "trip.json").read_text(encoding="utf-8"))
            privacy = (trip.get("privacy") or {}).get("confirmedAt")
            checks["MP-WV-05"] = {
                "passed": bool(privacy),
                "notes": f"privacy.confirmedAt={privacy!r}",
            }

            longshot_off = trip.get("export", {}).get("longShot") is False
            checks["MP-WV-04"] = {
                "passed": longshot_off or "longshot-toolbar" not in share_html,
                "notes": "share 页内 longshot FAB 由 CSS/配置控制",
            }

            bundle_hits = re.findall(r"/__travelogue/bundle/[^\"']+", draft_html)
            checks["A-14-draft-bundle"] = {
                "passed": len(bundle_hits) > 0,
                "notes": f"shared bundle refs: {len(bundle_hits)}",
            }

            print(json.dumps({"tripId": trip_id, "base": base, "checks": checks}, ensure_ascii=False, indent=2))
            ok = all(c.get("passed") for c in checks.values())
            return 0 if ok else 1
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
