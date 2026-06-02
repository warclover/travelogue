# Travelogue · Phase 9 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE9.md](./PRD-PHASE9.md) v0.9.1 及 P9-A～E |
| **验收** | [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md) |
| **里程碑** | M30 · Quality Gate |
| **W1 状态** | **Done**（2026-06-02） |
| **W2 状态** | **Partial**（P1 ML 降级已落地；完整 GPU 验收待 S2） |
| **更新** | 2026-06-02 |

---

## 波次总览

| 波次 | 目标 | 出口 |
|------|------|------|
| **M30-W1** | P0 cull + **M30-0a** + UX 第二行 toast | **独立发版** ✅ |
| **M30-W2** | P1 ml（不阻塞 W1） | 可选发版 · 部分完成 |
| **M30-W3** | subject 桥接 | Phase 10 解锁 ✅ |

---

## M30-0a · 前置（W1 Day 1 · 阻塞）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M30-0a | `layout_eligible_assets` 读 `layoutEligible` | `curate.py` | ☑ |
| M30-0b | grep 同步 degradation/clustering/cover 池 | 多文件 | ☑ |
| M30-0c | pytest 覆盖 culled asset 不进 curate 池 | `tests/test_photo_cull.py` | ☑ |

---

## M30-W1 · P0

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M30-1a | `CullConfig` + yaml（**mode 默认 rules**） | `config.py`, `config.yaml.example` | ☑ |
| M30-1b | `photo_cull.py` Pass 1–4 P0 + fail-open | `curation/photo_cull.py` | ☑ |
| M30-1c | `_finalize_ingest_assets` 挂钩 · **全 trip re-cull** | `media/ingest.py` | ☑ |
| M30-1d | featured 低清豁免 | `asset_quality.py` | ☑ |
| M30-1e | `cullSummary` + schema | `photo_cull.py`, `trip.schema.json` | ☑ |
| M30-1f | `format_ingest_report` 分项 | `ingest_report.py` | ☑ |
| M30-1g | Job stats `cullUserLine` | `studio_pipeline.py`, `studio_subprocess.py` | ☑ |
| M30-1h | toast **第二行** | `templates/studio/js/import-flow.js`, `homepage-v2/first-success.js` | ☑ |
| M30-1i | fixtures + `test_photo_cull.py` | `tests/` | ☑ |
| M30-1j | NR-P9-01～03 | tests | ☑ |
| M30-1k | NR-P9-04 mao/maomi golden 签 off | `docs/acceptance-records/` | ☑ |
| M30-1l | 附录 A §3.2 修订 | `PRD-EXPERIENCE-附录A` | ☑ |

**W1 不做**：exposure_extreme · pyiqa · CLI `travelogue cull` · ingest cull 细粒度 stageHint

---

## M30-W2 · P1 ML（可选）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M30-2a | pyiqa 集成 + 降级 | `photo_cull_ml.py` | ☑ |
| M30-2b | `cull.mode=auto` | `config.py` | ☑ |
| M30-2c | stageHint ML 变体 | `studio_pipeline.py`, `photo_cull.py`, `ingest.py` | ☑ |
| M30-2d | maxPhotos WARN toast | `import-flow.js`, `first-success.js` + Playwright | ☑ |
| M30-2e | exposure_extreme Spike | [PHASE9-SPIKE-exposure-extreme.md](./PHASE9-SPIKE-exposure-extreme.md) | ☑ deferred |

---

## M30-W3 · 桥接

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M30-3a | `subject_class_for_asset` CLIP 优先 | `subject_tagging.py` | ☑ |
| M30-3b | `test_subject_tagging_bridge.py` | tests | ☑ |

---

## W1 发布闸门

见 [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md) §5 **G-P9-W1** — **已全部满足**（2026-06-02）。

## W2 待办（不阻塞 W1）

- AC-P9-ML-02～04：需 GPU + `pip install -e ".[cull-ml]"` 后运行：
  ```bash
  python scripts/phase9_ml_acceptance.py --write docs/acceptance-records/phase9-ml-acceptance.json
  pytest tests/test_photo_cull_ml.py::test_ac_p9_ml_02_keep_ratio_within_rules_delta
  ```
- InsightFace / `portrait_face_aesthetic`：PRD W2 规划，config 键未消费（Phase 10 前评估）
- M30-2c 细粒度 ingest 内 per-photo cull 进度（可选；当前为 finalize 阶段 hint）

---

## 回归清单

```bash
pytest tests/test_photo_cull.py tests/test_trip_schema_cull.py tests/test_studio_phase9_cull_playwright.py -v
pytest tests/test_ingest_enrichment.py tests/test_asset_quality.py -v
pytest tests/test_curate.py -v --timeout=120
python -m travelogue demo verify
```

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.3 | 2026-06-02 | W2 部分：stageHint · maxPhotos WARN · exposure spike · AC-P9-10 |
| v0.9.2 | 2026-06-02 | W1 Done：NR-P9-04 签 off · Pass 2 material-only skip |
| v0.9.1 | 2026-06-02 | Kickoff：M30-0a · W1 范围 · ACCEPTANCE 链接 |
| v0.9.0 | 2026-06-02 | 初稿 |
