"""Dogfood: start longshot, cancel mid-flight, assert slot frees.

Usage:
  python scripts/lcc_cancel_dogfood.py --base http://127.0.0.1:8768 --trip demo-815dc906d3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _post(base: str, path: str, body: dict) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return exc.code, payload


def _get(base: str, path: str) -> tuple[int, dict]:
    with urllib.request.urlopen(f"{base}{path}", timeout=60) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def wait_idle_longshot(base: str, timeout: float = 90.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        st, body = _post(
            base,
            "/__travelogue/longshot",
            {"tripId": "__probe__", "scale": 1, "format": "png", "platform": "wechat_moments"},
        )
        if st == 409 or body.get("error") == "E_STUDIO_JOB_BUSY":
            time.sleep(0.5)
            continue
        # 404 trip not found means slot was free enough to accept
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8768")
    parser.add_argument("--trip", default="demo-815dc906d3")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT
        / "docs"
        / "acceptance-records"
        / "lcc-cancel-dogfood-2026-07-15.md",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")
    trip = args.trip

    lines = [
        "# LCC V1 · 长图协作取消狗粮（2026-07-15）",
        "",
        f"| Studio | `{base}` |",
        f"| Trip | `{trip}` |",
        "",
        "## 步骤与结果",
        "",
    ]
    ok_all = True

    def note(label: str, ok: bool, detail: str) -> None:
        nonlocal ok_all
        mark = "PASS" if ok else "FAIL"
        if not ok:
            ok_all = False
        print(f"[{mark}] {label}: {detail}")
        lines.append(f"- **{label}**: {'✅' if ok else '❌'} {detail}")

    try:
        with urllib.request.urlopen(f"{base}/", timeout=10) as resp:
            note("SETUP", resp.status == 200, f"HTTP {resp.status}")
    except Exception as exc:
        note("SETUP", False, str(exc))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    wait_idle_longshot(base)

    st, body = _post(
        base,
        "/__travelogue/longshot",
        {
            "tripId": trip,
            "scale": 1,
            "format": "png",
            "platform": "wechat_moments",
        },
    )
    job_id = body.get("jobId")
    note("START", st == 202 and bool(job_id), f"status={st} body={body}")
    if not job_id:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    # Let Playwright actually start
    time.sleep(2.5)
    _, mid = _get(base, f"/__travelogue/status?jobId={job_id}")
    note(
        "MID-STATUS",
        mid.get("status") in ("queued", "running", "cancelled", "succeeded", "failed"),
        f"status={mid.get('status')} hint={mid.get('stageHint')!r}",
    )

    cst, cbody = _post(base, "/__travelogue/cancel", {"jobId": job_id})
    note(
        "CANCEL",
        cst == 200 and cbody.get("status") == "cancelled",
        f"http={cst} body={cbody}",
    )

    # Slot must free after await inside cancel
    time.sleep(0.3)
    rst, rbody = _post(
        base,
        "/__travelogue/longshot",
        {
            "tripId": trip,
            "scale": 1,
            "format": "png",
            "platform": "wechat_moments",
        },
    )
    # May get 202 (new job) or still 409 if runner slow — wait briefly
    if rst == 409:
        deadline = time.time() + 35
        while time.time() < deadline and rst == 409:
            time.sleep(0.5)
            rst, rbody = _post(
                base,
                "/__travelogue/longshot",
                {
                    "tripId": trip,
                    "scale": 1,
                    "format": "png",
                    "platform": "wechat_moments",
                },
            )
    note(
        "RESTART",
        rst == 202 and bool(rbody.get("jobId")),
        f"status={rst} jobId={rbody.get('jobId')}",
    )

    # Cancel the second job too to leave studio idle
    if rbody.get("jobId"):
        _post(base, "/__travelogue/cancel", {"jobId": rbody["jobId"]})
        time.sleep(0.5)

    _, final = _get(base, f"/__travelogue/status?jobId={job_id}")
    note(
        "FINAL",
        final.get("status") == "cancelled" and final.get("result") is None,
        f"status={final.get('status')} result={final.get('result')}",
    )

    lines.extend(
        [
            "",
            f"**汇总**: {'全部通过' if ok_all else '有失败'}",
            "",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {args.out}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
