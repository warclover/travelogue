# IMPLEMENTATION · 日更质量修复包 V1（QFX）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v0.1.0** |
| **对应 PRD** | [PRD-QUALITY-FIXPACK-V1.md](./PRD-QUALITY-FIXPACK-V1.md) **v0.2.1** |
| **评审** | [acceptance-records/quality-fixpack-v1-review-2026-07-22.md](./acceptance-records/quality-fixpack-v1-review-2026-07-22.md) · Conditional Go |
| **邻接实施** | [IMPLEMENTATION-NO-AI-SURFACE-V1.md](./IMPLEMENTATION-NO-AI-SURFACE-V1.md) **v0.2.2**（S7/S7b · BE-NAS-03/04） |
| **DOC-STATUS** | **active** |
| **状态** | **PR-B in progress**（`fix/qfx-pr-b-longshot-current`；PR-A 已合 master） |
| **更新日期** | 2026-07-23 |

> **定位**：把 QFX PRD v0.2.1 的 S/D/AC 展开为可执行任务卡与 PR 切片。  
> **铁律**：禁止单 PR 塞满 Fix all；PR-A → B → C → D；主干红禁叠主题。

---

## 0. 已锁定决策（实施源）

以 PRD §0.4 为准。实施高频引用：

| ID | 一句话 |
|----|--------|
| **D-QFX-02** | 抽策展预处理模块；禁止空搬 keep-all 充数 |
| **D-QFX-03** | FE 无公开 setter；安全边界在 BE |
| **D-QFX-04/04b** | status 早拒 403；config off 投影收口 |
| **D-QFX-06/06b** | M1′：整卷 mtime + 最小 `current.json`；分段完整规则 M2′ |
| **D-QFX-07** | 永不从旧布尔升 keep_all；skip 仅 mode==keep_all |
| **D-QFX-08** | 回填→清标→条件硬丢；禁整函数短路 |
| **S-QFX-01** | CSC 已在 PR；本包加窄门禁，勿全量 e2e 上 PR |

---

## 1. PR 切片与退出

| PR | 里程碑 | 任务卡 | 退出 AC（最低） |
|----|--------|--------|-----------------|
| **PR-A** | M1′ 止血 | T-00～05 | 01 · 04 · 05 · 12 · 23 · 27 ·（02 或留痕）· 24 起步 |
| **PR-B** | M1′ 导出权威 | T-02 起步 · T-06 | 11 · 25（最小 current） |
| **PR-C** | M2′ 合同真 | T-02 收口 · T-07～10 | 03 · 06～10 · 13 · 16～22 · 26 · 25 分段 |
| **PR-D** | M3′ 防复发 | T-11 | 14 · 15 · 24 · Closed 指针 |

**合并规则**：PR-A 未绿不得合 PR-B 进主干；同理 B→C→D。

---

## 2. 任务卡详述

### T-QFX-00 · 文档对齐（PR-A 前或同 PR）

| 项 | 内容 |
|----|------|
| **动作** | ✅ IMPLEMENTATION-NAS → v0.2.2（status 403 · config 投影）；ACCEPTANCE 增 AC-NAS-17d |
| **验收** | 文内不再出现「status 可 200」为现行合同 |
| **状态** | ✅ 2026-07-23 |

---

### T-QFX-01 · Recipe 基线 + PR 窄门禁（PR-A）

| 项 | 内容 |
|----|------|
| **动作** | ✅ 同步 `csc-w0-baseline-happy-path-recipe.json` 与单测至 151/54 |
| **CI** | ✅ PR `lint` 增：`studio_ui_detail_static_audit.py --strict` + QFX 窄 unit（ai_surface / ui_detail / photo_keep_mode / recipe）；CSC 原已在 lint；**未**挂全量 e2e |
| **路径** | `docs/acceptance-records/csc-w0-baseline-*.json` · `tests/unit/orchestrator/*` · `.github/workflows/ci.yml` |
| **验收** | AC-QFX-01 · AC-24 起步 ✅ |
| **状态** | ✅ 2026-07-23 |

---

### T-QFX-02 · 策展预处理 / god-module（PR-B/C）

| 项 | 内容 |
|----|------|
| **动作** | 新建（或扩展）预处理模块：`backfill_native_dimensions` → 清 `excludeReason==low_resolution` → 条件硬丢；`curate._curate_preflight` 只编排 |
| **禁止** | 仅为降行数搬 `should_skip_low_res_exclusion` 六行；禁止整函数 mock「未调用」当绿 |
| **棘轮** | ✅ PR-A 留痕：`csc-w2b-god-module-ratchet-baseline.json` → 1945 / 1154；纪要 [qfx-god-module-ratchet-bump-2026-07-23.md](./acceptance-records/qfx-god-module-ratchet-bump-2026-07-23.md)（主因 `studio_pipeline` +27） |
| **验收** | AC-02（PR-A 留痕 ✅）· AC-13/26（完整在 PR-C） |

---

### T-QFX-03 · status 早拒 + config 投影（PR-A）

| 项 | 内容 |
|----|------|
| **动作** | ✅ `handle_llm_status`：off → 403，不调 `_status_body`；`config_handlers`：off 时剥离 `llmAvailable`/`llmProvider`/`tripsDir` 等，保留 `aiSurfaceEnabled` |
| **对齐** | IMPLEMENTATION-NAS BE-NAS-03/04 |
| **测试** | ✅ unit：off 不进 `_status_body` + 零敏感键；config 键断言；dark ON 回归 |
| **路径** | `llm_settings_handlers.py` · `config_handlers.py` · `test_ai_surface_gate.py` |
| **验收** | AC-05/23/27 · AC-NAS-17c/17d ✅ |
| **状态** | ✅ 2026-07-23 |

---

### T-QFX-04 · FE 只读 AI surface（PR-A）

| 项 | 内容 |
|----|------|
| **动作** | ✅ `ai-surface.js`：setter / hydrate 写路径改私有；导出只读 API；`studioAuthHeaders`；失败不清永久 false + 不误报 gate |
| **清理** | ✅ 删除 `llm-readiness.js` |
| **测试** | ✅ 动态 import 负向 + 设置区/LLM 入口源码门控（AC-04） |
| **路径** | `templates/studio/js/ai-surface.js` · `http.js` · 调用方 |
| **验收** | AC-04 ✅；（AC-09/10/21/22 可延 PR-C） |
| **状态** | ✅ 2026-07-23 |

---

### T-QFX-05 · keep-all 意图单源（PR-A）

| 项 | 内容 |
|----|------|
| **动作** | ✅ `resolvePhotoKeepModeFromDraft` = Python `infer_mode_from_bools`；改 `import-run.js` 遥测推断；`should_skip_low_res_exclusion` **仅**认 `photoKeepMode==keep_all` |
| **合同向量** | ✅ `tests/fixtures/qfx/photo_keep_mode_vectors.json`；Python + JS 同读 |
| **路径** | `import-wizard-logic.js` · `import-run.js` · `photo_keep_mode.py` · `tests/js/import-wizard-logic.test.mjs` |
| **验收** | AC-12 ✅ |
| **状态** | ✅ 2026-07-23 |

**向量表示例（最小）**

| photoKeepMode | cull | dupes | expectMode | expectSkipLowRes |
|---------------|------|-------|------------|------------------|
| （缺） | false | false | recommended | false |
| （缺） | false | true | keep_bursts | false |
| （缺） | true | true | keep_bursts | false |
| keep_all | * | * | keep_all | true |
| keep_bursts | * | * | keep_bursts | false |

---

### T-QFX-06 · 长图最小 current + 整卷 mtime（PR-B）

| 项 | 内容 |
|----|------|
| **写** | ✅ Job `export_handlers.runner` 成功、`handle_longshot_upload` 完整批 → 原子写 |
| **读** | ✅ `_build_longshot_pages` 最前读 current；否则整卷 `(st_mtime, name)` 降序 |
| **禁止** | 分段逐文件 mtime 混排（保持名序 fallback） |
| **路径** | `export_handlers.py` · `studio_bento_preview.py` · `export/longshot.py` |
| **锁定路径** | **`{trip_dir}/longshot-current.json`**（与 PNG 同层） |
| **测试** | ✅ AC-11 双文件 mtime；AC-25 current 优先；helper 孤儿/半批 |
| **验收** | AC-11 · AC-25（最小） |
| **状态** | ✅ 编码中 / 2026-07-23 |

**`longshot-current.json` 字段（锁定）**

```json
{
  "schemaVersion": 1,
  "batchId": "string",
  "createdAt": "ISO-8601",
  "kind": "whole | segmented",
  "files": ["相对 trip 根有序文件名"]
}
```

---

### T-QFX-07 · 预处理完整 + 分段批次（PR-C）

| 项 | 内容 |
|----|------|
| **动作** | 完成 T-02：幂等清标；真实图测；分段完整批次聚合 / 不完整批拒绝 |
| **删除** | `test_keep_all_skips_low_res` 整函数 mock 假绿（或改负例） |
| **验收** | AC-13/26 · AC-25 分段 |

---

### T-QFX-08 · Hydration 三态 + telemetry schema（PR-C）

| 项 | 内容 |
|----|------|
| **动作** | `unknown|disabled|enabled`；失败可重试；成功后 track；`sessionStorage` 去重；服务端 `ai_surface_gate` meta 恰好 `{enabled:bool}` |
| **路径** | `ai-surface.js` · `analytics.js` · `telemetry_handlers.py` · `studio_events.py` |
| **验收** | AC-09/10/21/22 |

---

### T-QFX-09 · UI Detail fail-closed（PR-C）

| 项 | 内容 |
|----|------|
| **动作** | 删 wave11 假 DOM；测试 DI 挂真卡；helpers schema P0；bare `--strict`→`all`；token 块内 `var()` 引用 |
| **路径** | wave11 playwright · `ui_detail_runtime_helpers.py` · `studio_ui_detail_static_audit.py` · `capability-card.js` |
| **验收** | AC-06～08/16～20 |

---

### T-QFX-10 · Facade 扩扫（PR-C/D）

| 项 | 内容 |
|----|------|
| **动作** | 扩 `lint_layout_engine_facade.py` 扫描根；grandfather + owner/expiry；**不上**新 import-linter |
| **验收** | AC-03 |

---

### T-QFX-11 · 体验与结案（PR-D）

| 项 | 内容 |
|----|------|
| **动作** | `narrow-gate.js` 复制三态；L1 `data-csc-key` == `l1Keys` 门禁；`scripts/quality_fixpack_gate.py`（或文档钉死命令列表）挂 PR required；DOC Closed 指针 |
| **验收** | AC-14/15/24 · S-QFX-08 |

---

## 3. 建议文件改动地图（按 PR）

### PR-A

| 区域 | 文件 |
|------|------|
| CSC | `csc-w0-baseline-happy-path-recipe.json` · recipe/studio 单测 |
| NAS BE | `llm_settings_handlers.py` · `config_handlers.py` · `test_ai_surface_gate.py` |
| NAS FE | `ai-surface.js` · 调用方 · `llm-readiness.js` |
| Keep-all | `import-wizard-logic.js` · `import-run.js` · `photo_keep_mode.py` · 合同向量 + JS/Py 测 |
| CI | `ci.yml`（窄测进 PR，可选） |
| 文档 | 已同步 NAS IMPLEMENTATION/ACCEPTANCE |

### PR-B

| 区域 | 文件 |
|------|------|
| 导出 | `export_handlers.py` · upload handler · `studio_bento_preview.py` |
| 可选 | 预处理模块起步 · god-module baseline 留痕 |

### PR-C

| 区域 | 文件 |
|------|------|
| 策展 | 预处理模块 · `curate.py` · `media/quality.py` |
| 审计 | helpers · wave11 · static_audit |
| Telemetry | handlers · ai-surface 三态收口 |
| Facade | `lint_layout_engine_facade.py` · baseline JSON |

### PR-D

| 区域 | 文件 |
|------|------|
| UX | `narrow-gate.js` |
| CSC | L1 DOM 契约测 · `studio-home-v2.html`（仅当差集非空） |
| Gate | `scripts/quality_fixpack_gate.py` · `ci.yml` |
| DOC | DOC-STATUS Closed 指针 · 邻接 Acceptance 勾选 |

---

## 4. 本地门禁命令

### PR-A / 日常

```powershell
python scripts/lint_csc_recipe_baseline.py
python scripts/lint_csc_god_module_ratchet.py
python -m pytest tests/unit/web/test_ai_surface_gate.py tests/unit/domain/test_photo_keep_mode.py -q
# 合同向量落地后：
# python -m pytest tests/unit/.../test_photo_keep_mode_vectors.py -q
# npm run test:js -- import-wizard-logic
```

### PR-B+

```powershell
python -m pytest tests/unit/web/test_studio_bento_preview*.py -q
python scripts/studio_ui_detail_static_audit.py --strict
```

### 聚合（PR-D）

```powershell
python scripts/quality_fixpack_gate.py
```

（脚本未建前，以 PRD §11.1 命令列表为等价入口。）

---

## 5. 风险与缓解（实施）

| 风险 | 缓解 |
|------|------|
| 读错 IMPLEMENTATION-NAS 旧 S7 | 以 **v0.2.2** 为准；PR-A 先合文档或同 PR |
| config 整端 403 打断 hydration | BE-NAS-04：仅投影，不 403 |
| 分段 mtime 假修 | PR-B 代码评审检查点 |
| 预处理打乱 curate 顺序 | 不变量单测 + 金样 trip |
| PR 时长被 e2e 拖死 | 窄标记；全量 e2e 仍 push |

---

## 6. Kickoff 勾选（相对 PRD §10.3）

- [x] PRD v0.2.1  
- [x] NAS PRD D-NAS-17b  
- [x] IMPLEMENTATION-NAS S7/S7b（v0.2.2）  
- [x] 本文 IMPLEMENTATION-QFX v0.1.0  
- [x] `current.json` 字段草签（§ T-06 / PRD §11.4）  
- [x] 合同向量路径约定（`tests/fixtures/qfx/photo_keep_mode_vectors.json`）  
- [x] 开分支 `fix/qfx-pr-a-m1-hemostasis` 并开始编码（T-01/03/04/05）  

---

## 7. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-23 | 初稿：按 PRD v0.2.1 展开 T-00～11 · PR-A/B/C/D；未改业务代码 |
