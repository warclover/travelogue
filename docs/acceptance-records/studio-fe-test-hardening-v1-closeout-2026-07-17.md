# SFH V1 · 结案记录（Studio FE Test Hardening）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-STUDIO-FE-TEST-HARDENING-V1.md](../PRD-STUDIO-FE-TEST-HARDENING-V1.md) v1.1.0-SFH |
| **评审** | [studio-fe-test-hardening-v1-review-2026-07-17.md](./studio-fe-test-hardening-v1-review-2026-07-17.md) |
| **实施** | [IMPLEMENTATION-STUDIO-FE-TEST-HARDENING-V1.md](../IMPLEMENTATION-STUDIO-FE-TEST-HARDENING-V1.md) |
| **日期** | 2026-07-17 |
| **结论** | **Done（本机）** · 主交付已合入；结案补丁含 OR-X-05/06 冻结测、IR-U-03、README 指针、§9.3 复跑 |
| **合入** | `a2d615f`（主施工）· 本记录随结案补丁一并推送 |

---

## 1. §9.5 本机证据

```text
SFH evidence (local · Actions quota exhausted)
- node -v: v22.19.0
- npm run test:js: exit 0 · # tests 65 · # pass 65 · # fail 0
- pytest v2_js_logic_node_units + band_vectors/or_x: green
- ci.yml: patched yes（test-pr setup-node@22 + npm run test:js；not executed on Actions）
```

### §9.3 映射旅程（本机复跑 · 2026-07-17）

| 模块 | nodeid / 套件 | 结果 |
|------|---------------|------|
| Recipe | `test_share_ready_w0_playwright.py::test_ac_sr_02_server_kept_n_wins_over_sparse_dom` | ✅ |
| Recipe | `test_output_recipe_persona_playwright.py::test_persona_ambiguous_intent_card_three_options_and_export` | ✅ |
| Import | `tests/e2e/test_import_wizard_v3_playwright.py`（全量） | ✅ **29 passed**（含上列 2 条共 29） |
| Longshot 发起 | `test_preview_toolbar_arc14_playwright.py::test_arc14c_export_longshot_starts_from_dock` | ✅ |
| Longshot/布局 stale | `test_lte_studio_playwright.py::test_ac11_preview_toolbar_shows_layout_css_stale_hint` | ✅ |
| 书架 stale 文案 | `test_studio_home_v2_ac_playwright.py::test_ac_hp21_06_stale_user_copy` | ✅ |
| 成功面换种分享（源码合同） | `test_output_recipe_guards.py::test_phase_a_must_fix_ui_guards` | ✅ |

> 备注：Playwright 真导出「成功面主/次 CTA 可见」尚无独立 e2e 专测；以 arc14c 发起 + guards/FTUE 源码合同 + Share-Ready persona 意图卡为护栏组合。额度恢复后可补真成功面 e2e（非本波阻塞）。

---

## 2. 结案补丁相对缺口表

| 缺口 | 处置 |
|------|------|
| closeout / §9.6 | **本文件** |
| OR-X-05 非法阈值 | **冻结** `Number(x)\|\|default`；Node 测覆盖 NaN/非法/0 |
| OR-X-06 顺序护栏 | **`isBandThresholdOrderValid`** + 向量集断言 sparse&lt;ambiguous；乱序不自动改写（行为等价） |
| IR-U-03 cancelling | **N/A 现网无枚举**；以 `shouldPerformCancelImport(activeJobId)` 表达「有 job 才 POST；无 job API no-op」 |
| T-W2-03 README | `templates/studio/preview-toolbar/README.md` 已加 SFH 节 |
| T-W2-04 ASH 反向链 | **Won’t（可选）** |
| Actions 抽查 test:js | **待额度恢复后补记**（非阻塞） |

---

## 3. 交付清单（文件）

- `scripts/run-js-tests.mjs` · `package.json` `test:js` · `ci.yml` test-pr Node
- `output-recipe-logic.js` · `import-run-logic.js` · `longshot-logic.js` · `import-wizard-logic.js`
- `tests/js/*-logic.test.mjs` · `tests/fixtures/output_recipe_band_vectors.json`
- `docs/TESTING.md` §1.1 · `DEFINITION-OF-DONE.md` SFH 勾选 · PRD/IMPLEMENTATION/评审

---

## 4. 签字

| 项 | 结论 |
|----|------|
| W0a–W2 工程 | ✅ Done（本机） |
| 结案补丁 | ✅ 本记录 |
| Actions 远程绿 | ⏸ 额度用尽 · 合同已落库 |
