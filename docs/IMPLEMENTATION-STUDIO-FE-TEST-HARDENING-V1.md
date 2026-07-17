# IMPLEMENTATION · Studio FE Test Hardening V1（SFH）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-STUDIO-FE-TEST-HARDENING-V1.md](./PRD-STUDIO-FE-TEST-HARDENING-V1.md) |
| **评审** | [studio-fe-test-hardening-v1-review-2026-07-17.md](./acceptance-records/studio-fe-test-hardening-v1-review-2026-07-17.md) |
| **状态** | **Done（本机）** · [结案](./acceptance-records/studio-fe-test-hardening-v1-closeout-2026-07-17.md) |
| **更新日期** | 2026-07-17 |

## W0a · 已落盘 ✅

| 项 | 路径 / 命令 |
|----|-------------|
| JS 入口 | `scripts/run-js-tests.mjs` |
| npm | `npm run test:js` |
| pytest 聚合 | `tests/unit/web/test_studio_home_v2.py::test_v2_js_logic_node_units` |
| CI 合同 | `.github/workflows/ci.yml` → `test-pr`：`setup-node@22` + `npm run test:js` |
| 文档 | `docs/TESTING.md` §1.1 |

## W0b · Output Recipe 纯逻辑 ✅（本机单测）

| 项 | 路径 |
|----|------|
| 纯逻辑 | `templates/studio/js/output-recipe-logic.js` |
| 壳层 | `templates/studio/js/output-recipe.js`（fetch/DOM/sessionStorage；成功载荷走 `mapServerRecipePayload`） |
| Node 测 | `tests/js/output-recipe-logic.test.mjs` |
| 共享向量 | `tests/fixtures/output_recipe_band_vectors.json` |
| Python 双端 | `tests/unit/export/test_output_recipe_band_vectors.py` |

### 行为等价对照（抽离前后）

| 入口 | 输入要点 | 期望（冻结） |
|------|----------|--------------|
| `classifyBand` | keptN vs sparse/ambiguous 阈值 | sparse / ambiguous / narrative |
| `needsFullExportConfirm` | enabled + narrative + full + chat + ≥hint | true；否则 false |
| `resolveClientRecipe` | ambiguous+preview | needsIntent=true |
| `resolveClientRecipe` | ambiguous+shelf | chat 降级、needsIntent=false |
| `resolveClientRecipe` | enabled=false | flag_disabled → chat |
| `mapServerRecipePayload` | recipe.needs_intent | source=server，采信 band |
| session helpers | 假 storage | round-trip / clear |

### 合同降噪（1 簇）

| 旧断言 | 风险 | 新护栏 | 处置 |
|--------|------|--------|------|
| `照片较多…` 必须出现在 `output-recipe.js` | 叙事深提示丢失 | 同串断言迁至 `output-recipe-logic.js` + 壳层 import 指针 | 改写 guards |

### 本机验收证据（2026-07-17 · W0b）

```text
- npm run test:js: 48 pass（当时）→ 现含 W1 共 57 pass
- pytest band_vectors + guards: green
- e2e share-ready + persona: 11 passed
```

## W1 · Import-run + Longshot ✅

| 项 | 路径 |
|----|------|
| import 纯逻辑 | `templates/studio/homepage-v2/import-run-logic.js` |
| import Node 测 | `tests/js/import-run-logic.test.mjs` |
| longshot 纯逻辑 | `templates/studio/preview-toolbar/longshot-logic.js` |
| longshot Node 测 | `tests/js/longshot-logic.test.mjs` |

### 合同降噪（第 2 簇）

| 旧断言 | 新护栏 | 处置 |
|--------|--------|------|
| 仅扫 `buildImportPayload` 于 import-run.js | Node `buildImportPayloadFields` + logic 指针 ASH-CONTRACT | 改写 payload contract |

### 本机验收证据（2026-07-17 · W1）

```text
SFH evidence (local · Actions quota exhausted)
- npm run test:js: exit 0 · # tests 57 · # pass 57 · # fail 0
- pytest v2_js_logic_node_units + ds_03: green
- e2e toolbar / import: （见跑次）
```

## W2 · 约定固化 + Wizard 薄切片 ✅

| 项 | 路径 |
|----|------|
| wizard 纯逻辑 | `templates/studio/homepage-v2/import-wizard-logic.js` |
| Node 测 | `tests/js/import-wizard-logic.test.mjs`（关闭确认 / dirty / 步骤矩阵） |
| TESTING | §1.1 全金字塔 |
| DoD | Studio FE logic + `tests/js` 勾选 |

### 结案补丁（缺口收口）

- OR-X-05/06：`normalizeBands` / `isBandThresholdOrderValid` + Node/Python 测  
- IR-U-03：`shouldPerformCancelImport`（无 cancelling 枚举；无 job → API no-op）  
- T-W2-03：`preview-toolbar/README.md` SFH 节  
- §9.3：import wizard 全量 29 绿；Recipe/stale/arc14c 见 closeout  

### 汇总本机证据

```text
SFH evidence (local · Actions quota exhausted)
- node -v: v22.19.0
- npm run test:js: # tests 65 · # pass 65 · # fail 0
- pytest v2_js_logic_node_units + band_vectors: green
- e2e import_wizard_v3 + SR-02 + persona intent: 29 passed
- e2e arc14c + lte stale + hp21 stale + guards: 4 passed
- ci.yml test-pr: patched（未刷 Actions）
```
