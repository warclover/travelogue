# Travelogue · Phase 22 验收标准

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE22-storage-platform.md](./PRD-PHASE22-storage-platform.md) v0.22.1 |
| **关联实施** | [IMPLEMENTATION-PHASE22.md](./IMPLEMENTATION-PHASE22.md) |
| **关联 ADR** | [ADR-008](./adr/008-trip-storage-boundaries.md) |
| **代号** | P22-StoragePlatform |
| **更新日期** | 2026-06-11 |
| **状态** | **Draft · 待 Kickoff** |

---

## 1. 验收环境

- `pip install -e ".[dev]"`；
- `master` 含 Phase 21；
- 基线 trip：`trips/demo-2025-4/trip.json`（约 **420 KiB**，< 512 KiB 告警线）；
- Studio：`python -m travelogue studio --no-open`（8766）；
- 可选 vision：`pip install -e ".[clip]"`（incremental dogfood 含 cluster 时需）。

---

## 2. P22-MVP 功能验收（W1–W3 · 必过）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-P22-01** | ADR-008 Accepted；denylist 与 CacheRegistry 一致 | 文档 + `CacheRegistry.describe()` 对照 |
| **AC-P22-02** | revision 冲突：后者 PATCH 409；无静默丢字段 | `pytest tests/test_trip_revision.py -v` |
| **AC-P22-05** | 每次 pipeline 写 `runs/run-*.json` | 跑 `run_trip` 后检查 runs/ |
| **AC-P22-07** | `purge_trip` 清 trip 级 cache；保留 geocode | `pytest tests/test_cache_registry.py -v` |
| **AC-P22-08** | demo trip < 512 KiB；注入 debug 顶层键 lint 失败 | `python scripts/lint_trip_json.py trips/demo-2025-4/trip.json` |
| **AC-P22-09** | layoutDecisionLog 迁出：trip 仅 digest；jsonl 全量 | curate 后检查 trip + `runs/layout-decisions.jsonl` |
| **AC-P22-11** | 改单条 caption 后 incremental 较全链 ≥40% 省时 | dogfood 记录（见 §6） |
| **AC-P22-13** | MVP 相关 pytest 全绿 | §7 命令 |

---

## 3. P22-Plus 功能验收（W4–W5）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-P22-03** | export.reading 变更 → incremental 只 render | `pytest tests/test_pipeline_incremental.py -v` |
| **AC-P22-04** | `from_stage=render` + fingerprint 命中 → 无 ingest/curate | 同上 |
| **AC-P22-06** | library index workspace 键；updated_at 排序 | `pytest tests/test_library_index.py -v` |
| **AC-P22-10** | v0.2 → v0.3 migrate dry-run | `pytest tests/test_trip_migration.py -v` |
| **AC-P22-12** | template config 变更 → 不得错误 skip curate/render | incremental 负向用例 |
| **AC-P22-14** | zip 导出不含 `runs/`、`.cache/` | export 回归或手动 inspect zip |

---

## 4. Studio UX 验收

| ID | 条件 | 验证方式 |
|----|------|----------|
| **UX-P22-01** | 409 时 Toast + 自动 reload trip | 手动：双 tab PATCH 或模拟 |
| **UX-P22-02** | pipeline 进行中 PATCH 按钮禁用 | Studio 导入流程目测 |
| **UX-P22-03** | 书架首屏不阻塞于 reconcile | 启动 Studio；>10 trip 时测首屏 <2s |

---

## 5. 非回归（NR-P22）

| ID | 条件 |
|----|------|
| **NR-P22-01** | `python -m travelogue validate trips/<id>/trip.json` 对 golden fixtures 仍通过 |
| **NR-P22-02** | `pytest --fast -q` CI 子集无新增失败 |
| **NR-P22-03** | `pipeline.incremental.enabled: false` 行为等同 P21 全链 |
| **NR-P22-04** | `studio.optimistic_lock: false` 兼容期仍可保存（带 warn 日志） |
| **NR-P22-05** | `chapter_explain` / peval 在 jsonl-only 模式可读 decision |

---

## 6. Dogfood 记录（AC-P22-11）

在 `docs/acceptance-records/phase22-incremental-timing.json` 记录：

```json
{
  "tripId": "demo-2025-4",
  "baselineFullRunSec": 0,
  "captionEditIncrementalSec": 0,
  "savingsPercent": 0,
  "notes": ""
}
```

**步骤：**

1. `travelogue run … --full` 记时；
2. 改一条 caption，`--incremental --from-stage=narrate`（或 MVP 允许的最短路径）记时；
3. `savingsPercent >= 40` 为通过。

---

## 7. 建议验收命令

```powershell
python -m pytest tests/test_trip_revision.py tests/test_cache_registry.py tests/test_pipeline_incremental.py tests/test_library_index.py tests/test_trip_migration.py -q

python scripts/lint_trip_json.py trips/demo-2025-4/trip.json

python -m travelogue validate trips/demo-2025-4/trip.json
```

---

## 8. 发布闸门（G-P22）

| 闸门 | 条件 |
|------|------|
| **G-P22-MVP** | AC-P22-01、02、05、07～09、11、13 + NR-P22-01～03 |
| **G-P22-Full** | MVP + Plus AC + NR-P22-04～05 + UX-P22-01～03 |

**合并 master 前：** ADR-008 状态 → **Accepted**；PRD 状态 → **Implemented**。

---

## 9. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.22.1 | 2026-06-11 | 初版；对齐 PRD v0.22.1 评审闭合 |
