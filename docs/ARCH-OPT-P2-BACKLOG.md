# 架构优化后续立项 · WS1 收尾后（2026-07-09）

> 前置：[`ARCH-OPT-REVIEW-2026-07-09.md`](./ARCH-OPT-REVIEW-2026-07-09.md) P0/P1 已闭环；本文件只跟踪 **P2 结构性债**。

---

## P2-A · 拆解 `run_curate`（god function）

| 项 | 内容 |
|----|------|
| 现状 | `travelogue/curation/curate.py` ≈1256 行；`run_curate` 单函数 ≈570 行 |
| 目标 | 显式 stage 序列（已有 `_CuratePreflight` / `_CurateBucketPlan` 雏形可沿用） |
| 建议切分 | preflight → bucket/plan → cover/hero → mosaic attach → metrics/persist |
| 验收 | 每 stage 可单测；`run_curate` 变为编排壳 ≤80 行；`arch_equivalence_check` 全绿 |
| 风险 | 行为漂移；需 golden trip + equivalence 双跑 |
| 估时 | 3–5 人日 |

## P2-B · `.trip.lock` 跨进程文件锁（原 M-A1c 遗留）

| 项 | 内容 |
|----|------|
| 现状 | `TripService.update` 有进程内 `threading.Lock` + `meta.revision` CAS；「比较」与 `os.replace` 之间跨进程无锁 |
| 目标 | 同 trip 目录下 `.trip.lock`（或 `portalocker`/`filelock`）包住 RMW 临界区 |
| 验收 | `tests/integration/trip/test_trip_cross_process_update.py` 在 Windows/Linux 稳定绿；文档更新 AC-ARC-02 |
| 风险 | Windows 文件锁语义差异；死锁/残留锁文件需 TTL 或进程崩溃清理策略 |
| 估时 | 1–2 人日 |

## P2-C · `layout_contract` 准入标准

| 项 | 内容 |
|----|------|
| 现状 | 第 0 层 kernel 在救火中被塞入 chapter_items / feedback / scoring 等业务实现，约 23 文件，准入边界模糊 |
| 目标 | 书面标准：**纯函数 + DTO / 注册表钩子 only**；禁止依赖 `curation` / `layout_engine` / `web` / `templating` |
| 机制 | `import-linter` 已约束分层；另加 `scripts/lint_layout_contract_surface.py`（禁止非白名单符号、禁止副作用 import） |
| 验收 | 准入文档进 TECH-ARCH §18；CI 门禁；新文件 PR checklist 勾选 |
| 估时 | 1 人日（文档+门禁）+ 后续按需下沉 |

## 建议排期

1. **P2-C**（低风险、防回归）→ 2. **P2-B**（数据安全）→ 3. **P2-A**（最大收益、需独立 PR）

与已完成的 P1（shim 退役 / hero 反向边）解耦，勿混入同一 PR。
