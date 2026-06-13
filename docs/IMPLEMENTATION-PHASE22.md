# Travelogue · Phase 22 实施任务清单（存储平台纪律）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE22-storage-platform.md](./PRD-PHASE22-storage-platform.md) v0.22.1 |
| **验收** | [ACCEPTANCE-PHASE22.md](./ACCEPTANCE-PHASE22.md) |
| **分支** | `phase22/storage-platform` |
| **状态** | ☐ 待启动 |
| **更新** | 2026-06-11 |

---

## 交付分期

| 分期 | 范围 | 出口 AC |
|------|------|---------|
| **P22-MVP** | W0–W3 | 01、02、05、07～09、11、13 |
| **P22-Plus** | W4–W5 | 03～04、06、10、12、14 |

---

## 波次总览

| 波次 | 目标 | 出口 |
|------|------|------|
| **P22-W0** | Kickoff | PRD v0.22.1 / ADR-008 Accepted |
| **P22-W1** | 边界 + log 迁出 + 缓存 | lint + layoutDecisionLog + CacheRegistry |
| **P22-W2** | revision + Studio UX | 409 + bump_revision 规则 |
| **P22-W3** | trace + render incremental | run-*.json + render skip MVP |
| **P22-W4** | library + migration | workspace SQLite + migrate CLI |
| **P22-W5** | Plus incremental + hardening | curate/narrate skip + export strip |

---

## P22-W0 · Kickoff

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P22-0a | PRD v0.22.1 评审闭合 | `docs/PRD-PHASE22-storage-platform.md` | ☑ |
| P22-0b | ACCEPTANCE-PHASE22 | `docs/ACCEPTANCE-PHASE22.md` | ☑ |
| P22-0c | ADR-008 → Accepted | `docs/adr/008-trip-storage-boundaries.md` | ☐ |
| P22-0d | 开分支 | `phase22/storage-platform` | ☐ |

---

## P22-W1 · 写入边界与缓存（MVP）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P22-1a | ADR-008 Accepted | `docs/adr/008-trip-storage-boundaries.md` | ☐ |
| P22-1b | trip.json denylist + 体积 lint | `scripts/lint_trip_json.py` | ☐ |
| P22-1c | layoutDecisionLog → jsonl dual-write | `curation/curate.py`, `runs/layout-decisions.jsonl` | ☐ |
| P22-1d | trip 内 digest + count；停写全量 log | `curate.py` | ☐ |
| P22-1e | chapter_explain / peval dual-read | `chapter_explain.py`, `eval/peval.py` | ☐ |
| P22-1f | `CacheRegistry` | `travelogue/services/cache_registry.py` | ☐ |
| P22-1g | purge / invalidate | `cache_registry.py` | ☐ |
| P22-1h | ingest invalidate hooks | `media/ingest.py` | ☐ |
| P22-1i | Studio delete → purge | `web/studio_handlers/*` | ☐ |
| P22-1j | `tests/test_cache_registry.py` | — | ☐ |
| P22-1k | `tests/test_layout_decision_log_migration.py` | dual-write / digest | ☐ |

---

## P22-W2 · Revision 乐观锁（MVP）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P22-2a | `TripRevisionConflictError` | `services/trip.py` | ☐ |
| P22-2b | `save(..., expected_revision=, bump_revision=)` | `trip.py` | ☐ |
| P22-2c | 新建 trip `meta.revision: 0` | `trip_factory.py` | ☐ |
| P22-2d | schema optional `meta.revision` | `schemas/trip.schema.json` | ☐ |
| P22-2e | Studio PATCH → 409 + UX | handlers + 前端 toast/reload | ☐ |
| P22-2f | `studio.optimistic_lock` config | `config/studio.py` | ☐ |
| P22-2g | CLI `--expect-revision` | `cli/pipeline.py` | ☐ |
| P22-2h | `tests/test_trip_revision.py` | — | ☐ |

---

## P22-W3 · Run Trace + Render Incremental（MVP）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P22-3a | `pipeline_fingerprint.py` | `services/pipeline_fingerprint.py` | ☐ |
| P22-3b | 五阶段 fingerprint（对齐 run.py） | 同上 | ☐ |
| P22-3c | `stageFingerprints` + `bump_revision=False` save | `pipeline_state.py`, `trip.py` | ☐ |
| P22-3d | **render-only** incremental skip | `orchestrator/run.py` | ☐ |
| P22-3e | CLI `--incremental` / `--full` + 优先级 | `cli/pipeline.py` | ☐ |
| P22-3f | `RunTraceWriter` | `services/run_trace.py` | ☐ |
| P22-3g | config `pipeline.incremental.mvp_render_only` | `config/` | ☐ |
| P22-3h | `tests/test_pipeline_incremental.py` | render skip MVP | ☐ |
| P22-3i | dogfood timing 记录 | `docs/acceptance-records/phase22-incremental-timing.json` | ☐ |

---

## P22-W4 · Library + Migration（Plus）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P22-4a | `LibraryIndex` SQLite `(workspace_root, trip_id)` | `services/library_index.py` | ☐ |
| P22-4b | JSON fallback | 同上 | ☐ |
| P22-4c | 异步 reconcile on studio start | `web/serve.py` | ☐ |
| P22-4d | upsert on pipeline complete | `orchestrator/run.py` | ☐ |
| P22-4e | 书架 API 读 index | `web/studio_handlers/*` | ☐ |
| P22-4f | `storage.*` config | `config.yaml.example` | ☐ |
| P22-4g | migration v0.2→v0.3 | `curation/trip_migration.py` | ☐ |
| P22-4h | `travelogue trip migrate` | `cli/*` | ☐ |
| P22-4i | `tests/test_library_index.py` | — | ☐ |
| P22-4j | `tests/test_trip_migration.py` | — | ☐ |

---

## P22-W5 · Plus Incremental + Hardening

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P22-5a | invalidation 矩阵接线 curate/narrate skip | `orchestrator/run.py` | ☐ |
| P22-5b | `mvp_render_only: false` 启用 Plus | config | ☐ |
| P22-5c | export zip strip runs/.cache | `export/` | ☐ |
| P22-5d | nested denylist lint（optional） | `lint_trip_json.py` | ☐ |
| P22-5e | DATA-MODEL + ARCHITECTURE 更新 | `docs/` | ☐ |
| P22-5f | CI optional trip size job | `.github/workflows/ci.yml` | ☐ |

---

## 依赖与顺序

```text
W1 (ADR + log迁出 + CacheRegistry)
  → W2 (revision)
  → W3 (trace + render incremental)     ← MVP 出口
  → W4 (library + migration)
  → W5 (Plus incremental + strip)
```

---

## 迁移说明

- **layoutDecisionLog**：W1 dual-write → W2 读者切 jsonl → W3 删 trip 全量。
- **meta.revision**：缺失 trip 首次 migrate 设为 `1`。
- **library.db**：路径改为 `{trips_dir}/.travelogue/`；旧 `~/.travelogue/library.db` 不自动导入。

**验收命令**：见 [ACCEPTANCE-PHASE22.md](./ACCEPTANCE-PHASE22.md) §7。
