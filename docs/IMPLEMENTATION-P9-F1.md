# Travelogue · P9-F1 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHOTO-CULL-USER-TOGGLE.md](./PRD-PHOTO-CULL-USER-TOGGLE.md) v0.2 Approved |
| **功能代号** | P9-F1 · 智能挑选照片用户开关 |
| **状态** | Done |
| **预估** | 2–3 人日（单人全栈） |
| **更新** | 2026-06-19 |

---

## 落地原则

1. **默认不改变主路径**：未传字段、旧 trip、新会话均等同 `photoCullEnabled=true`。
2. **先护栏后 UI**：schema → helper → pipeline → Sheet → FirstSuccess。
3. **文案诚实**：成功态必须 N/M 双数字，禁止假「全部进入排版」。
4. **会话内记忆、会话外重置**：不用 localStorage 跨会话默认关。

---

## 里程碑总览

| 里程碑 | 目标 | 出口 |
|--------|------|------|
| **F1.0 护栏层** | schema、helper、intent、API 透传 | 单测绿；旧 import 无回归 |
| **F1.1 管线** | cull / recull / ingest hint / Job result | AC-F1-02/03/05/12/13 单测覆盖 |
| **F1.2 Import UI** | checkbox + 草稿 + multipart | 手工两模式可提交 |
| **F1.3 完成态** | FirstSuccess N/M + Importing hint | AC-F1-09 Playwright 绿 |
| **F1.4 收尾** | telemetry、文档、全量回归 | AC-F1-01～17 |

---

## F1.0 护栏层（P0）

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| F1-0a | `intent.photoCullEnabled` optional boolean | `schemas/trip.schema.json` | — | ✅ |
| F1-0b | `apply_intent(..., photo_cull_enabled=)` | `travelogue/services/trip.py` | F1-0a | ✅ |
| F1-0c | `photo_cull_enabled_for_trip()` helper | `travelogue/curation/photo_cull.py` | — | ✅ |
| F1-0d | helper 单测：缺省 true / false / config off | `tests/test_photo_cull_policy.py` | F1-0c | ✅ |
| F1-0e | 解析 `photoCullEnabled`（JSON + multipart，缺省 true） | `travelogue/web/studio_handlers/import_handlers.py` | — | ✅ |
| F1-0f | worker_payload 透传 | `travelogue/web/studio_subprocess.py` | F1-0e | ✅ |
| F1-0g | `run_studio_pipeline(..., photo_cull_enabled=)` + 首次 `apply_intent` | `travelogue/web/studio_pipeline.py` | F1-0b | ✅ |
| F1-0h | import API 单测：缺字段、false、非法值 | `tests/test_studio_handlers_import_export.py` | F1-0e | ✅ |
| F1-0i | intent 落盘单测 | `tests/test_studio_intent.py` | F1-0b,F1-0g | ✅ |

---

## F1.1 管线（P0）

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| F1-1a | `apply_photo_cull` 早返回：`userDisabled` / `configDisabled` summary | `travelogue/curation/photo_cull.py` | F1-0c | ✅ |
| F1-1b | 用户关闭时不写 `cullUserLine`、不改 `layoutEligible` | `travelogue/curation/photo_cull.py` | F1-1a | ✅ |
| F1-1c | `should_recull_on_curate` 读 `photo_cull_enabled_for_trip` | `travelogue/curation/algorithm_profile.py` | F1-0c | ✅ |
| F1-1d | `_finalize_ingest_assets`：hint + cull 前读 trip intent | `travelogue/media/ingest.py` | F1-0c | ✅ |
| F1-1e | `format_ingest_progress_hint` / `cull_stage_hint` 分支 | `travelogue/curation/photo_cull.py` | F1-1d | ✅ |
| F1-1f | `StudioPipelineResult` 增 `photo_cull_enabled`、`layout_eligible_count` | `travelogue/web/studio_pipeline.py` | F1-1a | ✅ |
| F1-1g | job result 回传 `photoCullEnabled`、`layoutEligibleCount` | `travelogue/web/studio_subprocess.py` | F1-1f | ✅ |
| F1-1h | 单测：cull off → summary.userDisabled；recull skip | `tests/test_photo_cull_policy.py` | F1-1a,F1-1c | ✅ |
| F1-1i | 单测：低清在 cull off 时仍可降 M | `tests/test_photo_cull_policy.py` | F1-1a | ✅ |

---

## F1.2 Import Sheet UI（P0）

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| F1-2a | DOM：checkbox + 可展开说明 + `aria-live` 副文案区 | `templates/studio/studio-home-v2.html` | — | ✅ |
| F1-2b | 样式：单行默认、展开、opt-out 副文案、主题对比度 | `templates/studio/studio-home-v2.css` | F1-2a | ✅ |
| F1-2c | `readSheetDraft` / `saveSheetDraft` · `photoCullEnabled` | `templates/studio/homepage-v2/import-sheet.js` | F1-2a | ✅ |
| F1-2d | 新会话默认 checked；取消勾选更新副文案 + dedupe 提示 | `templates/studio/homepage-v2/import-sheet.js` | F1-2c | ✅ |
| F1-2e | `buildImportBody` 注入 `photoCullEnabled` | `templates/studio/homepage-v2/import-sheet.js` | F1-2c | ✅ |
| F1-2f | multipart `form.append("photoCullEnabled", ...)` | `templates/studio/homepage-v2/import-run.js` | F1-2e | ✅ |
| F1-2g | upload 确认区展示 checkbox +「开始上传」 | `import-sheet.js` · `import-run.js` | F1-2f | ✅ |
| F1-2h | 冒烟：DOM 含 `v2-photo-cull-enabled` | `tests/test_studio_home_v2.py` | F1-2a | ✅ |

---

## F1.3 完成态与进度（P1）

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| F1-3a | `populateSuccessUi`：读 `result.photoCullEnabled` | `templates/studio/homepage-v2/first-success.js` | F1-1g | ✅ |
| F1-3b | cull 关：N/M 文案 + M<N 低清弱提示（必做） | `templates/studio/homepage-v2/first-success.js` | F1-3a | ✅ |
| F1-3c | `import-run.js` 将 Job result 字段传给 `showFirstSuccess` | `templates/studio/homepage-v2/import-run.js` | F1-1g,F1-3a | ✅ |
| F1-3d | Playwright：cull on → 有「经挑选」 | `tests/test_studio_phase9_cull_playwright.py` | F1-3b | ✅ |
| F1-3e | Playwright：cull off → 无「经挑选」、有 N/M 规则 | `tests/test_studio_phase9_cull_playwright.py` | F1-3b | ✅ |
| F1-3f | Playwright：390px checkbox 区不溢出（AC-F1-07） | `tests/test_studio_phase9_cull_playwright.py` | F1-2b | ✅ |

---

## F1.4 观测、文档与回归（P1–P2）

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| F1-4a | `studio-intent.json` 写 `photoCullEnabled`、`layoutEligibleFinal` | `travelogue/web/studio_intent_telemetry.py` | F1-0g | ✅ |
| F1-4b | `import_photo_cull_pref` 完整字段 + import 完成补发 | `analytics.js` · `import-sheet.js` · `import-run.js` | F1-2f | ✅ |
| F1-4c | dev harness import 透传字段 | `templates/studio/homepage-v2/harness.js` | F1-2f | ✅ |
| F1-4d | 更新 PRD-PHASE9 / PHASE14 / ACCEPTANCE 索引 | `docs/*.md` | F1-3e | ✅ |
| F1-4e | IMPLEMENTATION-PHASE9 勾选 P9-F1 | `docs/IMPLEMENTATION-PHASE9.md` | F1-4d | ✅ |
| F1-4f | 全量相关 pytest + 记录 phase 摘要 | `docs/acceptance-records/`（可选） | F1-3e | ☐ |

---

## 建议执行顺序（单人）

```text
Day 1 AM   F1-0a → F1-0d → F1-0e → F1-0h        （护栏 + 单测）
Day 1 PM   F1-0b → F1-0f → F1-0g → F1-0i
           F1-1a → F1-1c → F1-1h                （管线核心）
Day 2 AM   F1-1b → F1-1d → F1-1e → F1-1i
           F1-1f → F1-1g
Day 2 PM   F1-2a → F1-2f → F1-2h                （UI + 提交）
Day 3 AM   F1-3a → F1-3e → F1-3f                （成功态 + E2E）
Day 3 PM   F1-4a → F1-4f                        （telemetry + 文档）
```

---

## 完成定义（Definition of Done）

- [x] PRD AC-F1-01～17 均有对应测试或手工记录
- [x] 默认勾选路径与 v0.1 基线行为一致（金样 mao/maomi cull-on 不回归）
- [x] `photoCullEnabled=false` 路径 E2E 通过
- [x] 无 localStorage 跨会话记忆实现
- [x] Job result 含 `photoCullEnabled`；FirstSuccess 不二次 fetch trip
- [x] 关联 docs 索引已更新

---

## 任务统计

| 里程碑 | 任务数 | P0 |
|--------|--------|-----|
| F1.0 护栏层 | 9 | 9 |
| F1.1 管线 | 9 | 8 |
| F1.2 Import UI | 8 | 8 |
| F1.3 完成态 | 6 | 3 |
| F1.4 收尾 | 6 | 0 |
| **合计** | **38** | **28** |
