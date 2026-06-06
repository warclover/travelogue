# P2 架构还债任务清单 · 2026-06-06

> 来源：质量审计 P2 建议（ADR-010 · DEFINITION-OF-DONE §1.1）  
> 前置：P0–P1 已合并（`df7b0f6`）

## 执行原则

- 每项独立 PR / commit，拆完跑 `quality_gate.py` + 相关 pytest
- 不改 HTTP 路径、CLI 命令名、schema 字段
- 先抽模块、再删旧代码；`trip_handlers` 保留 re-export 门面

---

## 任务总览

| ID | 任务 | 优先级 | 状态 | 验收 |
|----|------|--------|------|------|
| P2-1 | `trip_handlers` 按域拆分 | P0 | ☑ 完成 | 各文件 <300 行；`test_studio_handlers_*` 全绿 |
| P2-2 | `config.py` 按域拆包 | P1 | ☑ 完成 | `get_config()` API 不变；配置测试全绿 |
| P2-3 | `cli.py` 子命令模块化 | P1 | ◐ 进行中 | `travelogue --help` 不变 |
| P2-4 | `trips/linzhi` 缓存版本策略 | P2 | ☐ | export 后无时间戳脏 diff |
| P2-5 | `ingest.py` / `curate.py` 减负 | P3 | ☐ | 算法 Phase 稳定后再动 |

---

## P2-1 · trip_handlers 拆分（已完成）

```
studio_handlers/
  trip_common.py           # _is_protected_demo_trip
  trip_list_handlers.py    # list / delete / entry / aesthetic / bento / chapter_layout
  trip_intent_handlers.py  # intent / cohort / template / copyIntent
  trip_replan_handlers.py  # screen replan
  trip_pipeline_handlers.py # pipeline lock / curate / rerender
  trip_handlers.py         # re-export 门面（studio_routes 不变）
```

**验证命令：**

```bash
python -m pytest tests/test_studio_handlers_trip.py tests/test_studio_handlers_cohort.py tests/test_studio_handlers_replan.py tests/test_studio_trip_delete.py -q
python scripts/quality_gate.py
```

---

## P2-2 · config 拆包（计划）

```
travelogue/config/
  __init__.py    # get_config, AppConfig re-export
  ingest.py      # IngestConfig
  cull.py
  curate.py
  mosaic.py
  vision.py
  loader.py      # YAML merge
```

---

## P2-3 · cli 拆分（计划）

```
travelogue/cli/
  __init__.py    # typer app
  trip.py
  demo.py
  studio.py
```

---

## P2-4 · linzhi 版本号（计划）

- 方案 B：render 时用 `journal.css` 内容 hash 生成 `?v=`，替代时间戳
- 或方案 C：文档化 `git restore trips/linzhi` 纪律

---

## P2-5 · ingest/curate（暂缓）

- 等 Phase 15 unified_mode 完全收口后再拆
- 目标：`ingest_loop.py` + `asset_entry.py`；`curate_buckets.py`
