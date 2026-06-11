#!/usr/bin/env python3
"""Keep Studio running for local share smoke / Playwright."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_studio_server import _distinct_album, _free_port, _start_studio_server
from travelogue.web.studio_jobs import reset_job_store
from travelogue.web.studio_pipeline import run_studio_pipeline

TRIPS_ROOT = ROOT / "trips"
SMOKE_TRIP_ID = "album-distinct"


def ensure_smoke_trip() -> None:
    """在标准 trips/ 下确保 share 对照用画册存在（与 start-studio.bat 同一根目录）。"""
    if (TRIPS_ROOT / SMOKE_TRIP_ID / "index.html").is_file():
        return
    TRIPS_ROOT.mkdir(parents=True, exist_ok=True)
    work = TRIPS_ROOT / ".share-smoke-work"
    work.mkdir(parents=True, exist_ok=True)
    album = _distinct_album(work, 6)
    run_studio_pipeline(
        album,
        trips_dir=TRIPS_ROOT,
        title="Share 对照",
        place="本地",
        dedupe=False,
    )


def main() -> None:
    reset_job_store()
    ensure_smoke_trip()
    port = _free_port()
    server = _start_studio_server(TRIPS_ROOT, port)
    meta = {
        "port": port,
        "tripId": SMOKE_TRIP_ID,
        "tripsDir": str(TRIPS_ROOT),
        "draftUrl": f"http://127.0.0.1:{port}/{SMOKE_TRIP_ID}/index.html",
        "shareUrl": f"http://127.0.0.1:{port}/{SMOKE_TRIP_ID}/index.html?share=1",
        "shareMobileUrl": f"http://127.0.0.1:{port}/{SMOKE_TRIP_ID}/index-mobile.html?share=1",
        "homeUrl": f"http://127.0.0.1:{port}/",
    }
    print(json.dumps(meta, ensure_ascii=False), flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
