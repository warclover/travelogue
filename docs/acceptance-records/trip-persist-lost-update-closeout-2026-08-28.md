# trip persist 丢更新 · 结案（2026-08-28）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **closed**（本波关闭 · 不再开实施） |
| **日期** | 2026-08-28 |
| **合同来源** | 现场核实：全量旧快照丢并发业务更新 + 三道架构门禁红灯；**未新开 PRD** |
| **分支** | `feat/pfm-portfolio-folio-mode-v1` @ `849191fd` |
| **合入** | `98e6ac45` persist · `849191fd` 门禁 |
| **现行写入合同** | [ADR-008](../adr/008-trip-storage-boundaries.md) §10 |

---

## 交付

| 项 | 结果 |
|----|------|
| 热路径不再全量覆盖 | `run_trip` / render / CLI / packager / demo 改走 `persist_pipeline_owned` |
| 旧快照禁止重放 | `persist_trip_snapshot(..., base_revision=)`；磁盘 revision 变化直接 `TripConflictError` |
| 生产代码禁全量快照 | `scripts/lint_trip_save_calls.py` 只允许 `travelogue/services/trip.py` 定义处 |
| 用户文案 | `copy_persist` 在结构推送后回填 lead / decorLine / title / hook / epilogue / 图注 / 已编辑屏文 |
| Intent flush | 字段级合并：`travelPlan` / hints / folders 由管线写；HTTP 标题、笔记、`placesUserSet` 磁盘赢 |
| DPI | `crossing_longshot.py` 零身份词；folio 判断在 S-07 `export/dispatch.py` |
| God module | 基线只降：`curate.py` 2014→**1646**，`studio_pipeline.py` 1380→**1144** |
| tsc | `npm run tsc:preview-toolbar` exit 0 |

## 验收证据

```text
pytest --fast --collect-only -q tests/unit/trip/test_persist_snapshot_cas.py tests/unit/media/test_ingest_merge_mutator.py
# 14 collected · 3 integration deselected

pytest tests/unit/trip/test_persist_snapshot_cas.py tests/unit/media/test_ingest_merge_mutator.py -q
# 14 passed

pytest tests/integration/trip/test_persist_concurrent_intent.py -q
# 3 passed（import / render / narrate×lead）

python scripts/lint_dual_pipeline_ownership.py   # hits=1（baseline 1）
python scripts/lint_trip_save_calls.py           # OK
```

`pytest --fast` 托底单测：`tests/unit/trip/test_persist_snapshot_cas.py`、`tests/unit/media/test_ingest_merge_mutator.py`。并发集成标 `integration`，fast 不跑。

## 明确不做（本波关闭，不再跟）

- 不再拆 `curate.py` / `studio_pipeline.py` 换行数
- 不为 Output / Telemetry 新造 trip 顶层 mutator
- 不把 `persist_trip_snapshot` 加回热路径
- 不新开所有权文档；键表继续写在 `ingest_persist.py`
- `export` 整段推送、`run_trip` 阶段内不回读磁盘：记下、不本波修
- Pipeline Throughput 的 `PT-M1-10`（ProcessPool ingest × `persist_every_n` × HTTP）仍属 [IMPLEMENTATION-PIPELINE-THROUGHPUT.md](../IMPLEMENTATION-PIPELINE-THROUGHPUT.md)，**不是本结案范围**

## 结案声明

导入期间「改标题 / 改笔记 / 改这段文案」三条用户写入已闭环。本修复计划关闭，勿再往同一主题加刀。
