"""Studio · Title Art（路线 B/C）一次性生成触发入口
(PRD-COVER-CALLIGRAPHY-TITLE-V1 §8 · D-CAL-14/16/21)。

W1 落地路线 B/C 引擎与 CLI ``title-art`` 命令后，Studio 里一直没有对应
入口——PRD「未完成」清单如实记录了这个缺口：产品能改 ``coverOpeningStyle``
（走 ``meta.coverOpeningStyle`` copy-patch，见 ``copy_patch.py``），但没有
任何按钮能真正触发 ``resolve_title_art`` 重算并把结果渲染出来；唯一入口
只有 CLI。本文件补上 Studio 端的入口。

设计要点：
- 一次性生成（点一次算一次），不是可反复实时调参的面板；每次点击默认
  ``force=True`` 重算，语义上等价于 CLI ``title-art --force``。
- 路线 C 是否尝试由「请求体 routeC」∧「服务端 ``config.title_art.
  route_c_enabled`` 总闸」共同决定——总闸关闭时静默按路线 B 处理，不报
  错（OQ-CAL-06：路线 C 长期定位为「用户可选高级项」，不是「用户可绕过
  运营总闸」）。前端会先读 ``GET /__travelogue/config`` 的
  ``titleArt.routeCEnabled`` 决定要不要展示这个勾选框，但后端仍在这里
  做二次收口，不依赖前端诚实。
- 未知异常按 D-CAL-16 fail-open 原则处理：绝不 500，写回禁用占位并
  200 返回（跟引擎自身「非白名单/空标题/字形不覆盖」的 fail-open 语义
  一致），前端只需要判断 ``enabled`` 字段，不需要特殊处理错误态。
- **付费/耗时副作用在 CAS 之外执行**：``resolve_title_art``（含路线 C
  网络轮询与写 PNG）先在 trip 快照上算完，``TripService.update`` 的
  mutator 只写入已算好的 ``meta.titleArt``。否则：① 持锁期间阻塞可达
  分钟级，卡住同 trip 其它写；② CAS 重放会重复打付费 API。
"""

from __future__ import annotations

import copy
import hashlib
import logging

from travelogue.cover_engine.title_art import resolve_title_art
from travelogue.cover_engine.title_art.models import disabled_meta_dict
from travelogue.web.studio_errors import internal_error_payload
from travelogue.web.studio_handlers.common import (
    load_trip_or_404,
    studio_ctx,
    trip_update_or_respond,
)
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol

_log = logging.getLogger(__name__)


def _rerender(trip_json) -> bool:
    from travelogue.web.rerender import rerender_draft_trip

    try:
        rerender_draft_trip(trip_json)
        return True
    except Exception:
        _log.exception("title-art rerender failed for %s", trip_json)
        return False


def handle_post_resolve_title_art(handler: StudioHandlerProtocol, trip_id: str) -> None:
    body = handler._read_json_body() or {}
    force = bool(body.get("force", True))
    route_c_requested = bool(body.get("routeC", body.get("route_c", False)))
    style_id = str(body.get("styleId") or body.get("route_c_style_id") or "").strip() or None

    loaded = load_trip_or_404(handler, trip_id)
    if loaded is None:
        return
    trip_dir, trip0 = loaded
    trip_json = trip_dir / "trip.json"
    ctx = studio_ctx(handler)
    route_c_allowed = bool(ctx.cfg.title_art.route_c_enabled)
    route_c_enabled = route_c_requested and route_c_allowed
    ta = ctx.cfg.title_art
    model_name = getattr(ta, "model_name", None) or "wanx2.1-t2i-plus"
    prompt_version = getattr(ta, "prompt_version", None) or "v2"
    max_attempts = int(getattr(ta, "route_c_max_attempts", 2) or 2)
    ocr_enabled = bool(getattr(ta, "ocr_verify", True))

    art_dir = trip_dir / "trip-derived" / "title-art"

    def _resolve_asset_path(asset: dict):
        from travelogue.media.source_resolve import resolve_source_path

        return resolve_source_path(asset, trip_dir)

    def _write_png(data: bytes) -> str:
        art_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(data).hexdigest()[:16]
        out_path = art_dir / f"{digest}.png"
        out_path.write_bytes(data)
        return str(art_dir.relative_to(trip_dir) / out_path.name).replace("\\", "/")

    # 在 CAS / 跨进程锁之外跑耗时计算（含 Route C 网络）。mutator 只写字典。
    trip_work = copy.deepcopy(trip0)
    result = None
    try:
        result = resolve_title_art(
            trip_work,
            resolve_asset_path=_resolve_asset_path,
            write_png=_write_png,
            route_c_enabled=route_c_enabled,
            route_c_style_id=style_id,
            force=force,
            model_name=model_name,
            prompt_version=prompt_version,
            route_c_max_attempts=max_attempts,
            ocr_verify_enabled=ocr_enabled,
        )
    except Exception:
        _log.exception("title-art resolve failed for trip %s", trip_id)
        trip_work.setdefault("meta", {})["titleArt"] = disabled_meta_dict(
            reason="E_TITLE_ART_UNEXPECTED"
        )
        result = None

    if result is not None:
        title_art_payload = result.to_meta_dict()
    else:
        title_art_payload = (
            trip_work.get("meta", {}).get("titleArt")
            if isinstance(trip_work.get("meta"), dict)
            else None
        )
        if not isinstance(title_art_payload, dict):
            title_art_payload = disabled_meta_dict(reason="E_TITLE_ART_UNEXPECTED")

    def mutator(t: dict):
        meta = t.setdefault("meta", {})
        if not isinstance(meta, dict):
            meta = {}
            t["meta"] = meta
        meta["titleArt"] = copy.deepcopy(title_art_payload)
        return result

    ok, _persisted = trip_update_or_respond(handler, ctx.trip_service(), trip_json, mutator)
    if not ok:
        return
    if not _rerender(trip_json):
        handler._json_response(500, internal_error_payload())
        return

    if result is None:
        handler._json_response(
            200,
            {
                "ok": True,
                "enabled": False,
                "routeCRequested": route_c_requested,
                "routeCAllowedByConfig": route_c_allowed,
            },
        )
        return

    handler._json_response(
        200,
        {
            "ok": True,
            "enabled": result.enabled,
            "engine": result.engine,
            "assetPath": result.asset_path,
            "fallbackFrom": result.fallback_from,
            "ocrVerified": result.ocr_verified,
            "routeCRequested": route_c_requested,
            "routeCAllowedByConfig": route_c_allowed,
        },
    )
