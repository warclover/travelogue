"""批量（多平台 · 排队串行）长图导出调度层。

对应 `docs/PRD-BATCH-EXPORT-MULTISELECT-V1.md` Stage 1 · 后端调度函数。

设计要点（D-BEX-02 / D-BEX-03 / D-BEX-05）：
- **零侵入**：本模块只是一个 for 循环，逐平台调用既有 `export_trip_longshot`；
  不改任何 CardGrouper / CardRenderer / Playwright 切分逻辑。
- **单 Job 语义不变**：调用方（`export_handlers.handle_longshot`）仍只创建
  *一个* `StudioJob`，本模块在该 Job 的 worker 线程内部顺序跑完所有平台；
  `StudioJobStore._longshot_running` 单锁模型完全不变。
- **部分失败不阻塞整体**：某平台 `LongshotExportError`（含未预期异常）→ 记录该项
  失败，continue 到下一个平台；只有 `LongshotCancelled`（用户主动取消）才中断
  整个批量循环，交由外层 `run_longshot_job` 按现有取消语义处理。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.export.longshot import (
    LongshotCancelled,
    LongshotExportError,
    LongshotExportResult,
    export_trip_longshot,
)

CancelCheckFn = Callable[[], bool]
CancelRegisterFn = Callable[[Any], None]
# (item_index, item_total, platform_id, cur, total, hint) — D-BEX-04 平台清单进度
BatchProgressFn = Callable[[int, int, str, int, int, str], None]


@dataclass
class BatchExportRequest:
    """一个批量导出条目 · 对应 payload.platforms[i]（D-BEX-01 平台专属设置）。

    `segment_mode` / `copy_display` 按平台预先算好传入（非 chat 平台强制 auto /
    moments·grid·poster 强制纯照片——与单平台路径 `handle_longshot` 的既有规则
    完全一致，只是从"整请求一份"变成"逐项各算一份"）。
    """

    platform: str
    slide_count: int | None = None
    pad_mode: str | None = None
    segment_mode: str = "auto"
    copy_display: str = "full"


@dataclass
class BatchExportItemResult:
    """单个平台的导出结果（D-BEX-05 · 独立记录成败，不中断整体循环）。"""

    platform: str
    ok: bool
    result: LongshotExportResult | None = None
    error_code: str | None = None
    error_message: str = ""


def export_trip_longshot_batch(
    trip_dir: Path,
    *,
    requests: list[BatchExportRequest],
    common: dict[str, Any] | None = None,
    progress: BatchProgressFn | None = None,
    cancel_check: CancelCheckFn | None = None,
    cancel_register: CancelRegisterFn | None = None,
) -> list[BatchExportItemResult]:
    """依平台顺序调用既有 `export_trip_longshot`，逐项捕获异常、不中断整体循环。

    `common` 是所有平台共享的导出参数（scale / fmt / include_appendix，来自
    payload 顶层字段，非 per-item）。
    """
    common = dict(common or {})
    total = len(requests)
    results: list[BatchExportItemResult] = []

    for i, req in enumerate(requests):
        if cancel_check and cancel_check():
            break

        def _item_progress(
            cur: int, item_total: int, hint: str, _i: int = i, _platform: str = req.platform
        ) -> None:
            if progress:
                progress(_i, total, _platform, cur, item_total, hint)

        try:
            result = export_trip_longshot(
                trip_dir,
                platform=req.platform,
                slide_count=req.slide_count,
                pad_mode=req.pad_mode,
                segment_mode=req.segment_mode,
                copy_display=req.copy_display,
                progress=_item_progress,
                cancel_check=cancel_check,
                cancel_register=cancel_register,
                **common,
            )
        except LongshotCancelled:
            # D-BEX-05 明确排除主动取消：不算作"该项失败"，中断整个批量循环。
            raise
        except LongshotExportError as exc:
            results.append(
                BatchExportItemResult(
                    platform=req.platform,
                    ok=False,
                    error_code=exc.code,
                    error_message=str(exc),
                )
            )
            continue
        except Exception as exc:  # noqa: BLE001 · 单平台意外异常不应拖垮整批
            results.append(
                BatchExportItemResult(
                    platform=req.platform,
                    ok=False,
                    error_code="E_LNG_CAPTURE_FAILED",
                    error_message=str(exc),
                )
            )
            continue

        results.append(BatchExportItemResult(platform=req.platform, ok=True, result=result))

    return results
