# 测试失败记录 & 下次会话提示词

| 属性 | 内容 |
|------|------|
| **日期** | 2026-06-05 |
| **分支/状态** | 算法 V2 已落地；全仓测试有失败项，**与 V2 无关** |
| **用途** | 暂停工作后，下次专门修失败用例；可直接把 §6 复制给 AI |

---

## 1. 已确认通过（无需下次重跑，除非改相关代码）

### 算法 V2 专项（61/61 · ~19s）

```bash
python -m pytest \
  tests/test_cover_scoring_v2.py \
  tests/test_cover_scoring_v2_gates.py \
  tests/test_sharpness_v2.py \
  tests/test_heuristic_v2_gates.py \
  tests/test_cover_candidates_v2.py \
  tests/test_phase6_cover_scoring.py \
  tests/test_phase6_heuristic_vector.py \
  tests/test_embedding_cache_schema.py \
  tests/test_algorithm_profile.py \
  tests/test_cluster_cache.py \
  tests/test_phase7_incremental_modes.py \
  -q
```

### 自动化门禁

| 项 | 结果 |
|----|------|
| A-M1 Kendall τ | mean=1.0（合成 10 本） |
| A-M4 / A-M7 / B-M5 | 全绿 |
| C-M1 / C-M2 heuristic-v2 | 全绿 |
| D-M1 proxy LOO | accuracy=1.0 |
| `algorithm-v2-signoff.json` | `python scripts/algorithm_v2_signoff.py --from-json docs/acceptance-records/algorithm-v2-signoff.json` → `ok: true` |

### V2 仍待人工（非测试失败）

- R0' 盲评：`docs/acceptance-records/algorithm-v2-signoff.json` 中 `judgeVerdict` 未填
- 真实 trip：`trips/mao` 等未落地

---

## 2. 全量测试概况（2026-06-05 实测）

| 运行 | 命令/范围 | 通过 | 失败 | 跳过 | 耗时 |
|------|-----------|------|------|------|------|
| **全量** | `pytest tests/ -q` | 1605 | **96** | 7 | ~31 min |
| **去掉 2 个 UI playwright 文件** | `--ignore=test_studio_p9_qa_playwright.py --ignore=test_studio_p10_layout_playwright.py` | 1624 | **72** | 7 | ~21 min |
| **CI 快套件** | `pytest -m "not integration and not e2e and not vision and not playwright_serial and not legacy_homepage" -q` | 1381 | **24** | 6 (+270 deselected) | ~8 min |

**结论**：96 失败 ≈ **Playwright E2E（~72）** + **Mosaic/Studio 单元（24，与快套件重叠部分）**。算法 V2 专项 0 失败。

---

## 3. 失败清单 · Bucket A — CI 快套件（24 项，已完整记录）

> 下次优先修这一组：不依赖浏览器，复现快，与 V2 无关。

| # | 测试 |
|---|------|
| 1 | `tests/test_golden_layouts.py::test_mosaic5_exposure_ab_fixture` |
| 2 | `tests/test_golden_mosaic_unified.py::test_golden_mosaic_portrait_4_avoids_wide_grid` |
| 3 | `tests/test_golden_mosaic_unified.py::test_golden_mosaic_landscape_6_matches_mcs` |
| 4 | `tests/test_golden_mosaic_unified.py::test_mosaic_landscape_6_ab_unified_vs_legacy` |
| 5 | `tests/test_golden_mosaic_unified.py::test_golden_mosaic_landscape_9` |
| 6 | `tests/test_layout_service.py::test_apply_layout_web_portrait_mosaic` |
| 7 | `tests/test_mosaic_candidates.py::test_generate_window_candidates_multiple_patterns` |
| 8 | `tests/test_mosaic_candidates.py::test_time_gap_still_yields_candidates_lower_score` |
| 9 | `tests/test_mosaic_compose_deterministic.py::test_pick_best_five_stable_signature` |
| 10 | `tests/test_mosaic_decision_log_contract.py::test_pick_best_logs_top3_reason_codes_router_version` |
| 11 | `tests/test_mosaic_fallback.py::test_low_score_fallback_reason` |
| 12 | `tests/test_mosaic_integration.py::test_mosaic_enabled_increases_mosaic5_exposure` |
| 13 | `tests/test_mosaic_replan.py::test_replan_screen_alt_topk_changes_pattern` |
| 14 | `tests/test_mosaic_replan.py::test_replan_alt_topk_picks_second_rank_when_best_matches_current` |
| 15 | `tests/test_mosaic_replan.py::test_replan_screen_syncs_chapter_items` |
| 16 | `tests/test_mosaic_self_heal.py::test_self_heal_tightened_rescore` |
| 17 | `tests/test_mosaic_self_heal.py::test_self_heal_disabled_uses_legacy` |
| 18 | `tests/test_mosaic_unified_mode.py::test_unified_on_mosaic5_still_works` |
| 19 | `tests/test_phase9_ingest_regression.py::test_ingest_e2e_ml_cache_reused_between_rebuilds` |
| 20 | `tests/test_photo_cull_ml.py::test_apply_aesthetic_scores_uses_persistent_cache` |
| 21 | `tests/test_studio_handlers_replan.py::test_handle_patch_screen_replan` |
| 22 | `tests/test_studio_ux_p3.py::test_ux_p3_04_cluster_notice_non_blocking_string` |
| 23 | `tests/test_studio_ux_p3.py::test_ux_p3_05_06_slow_hint_thresholds_and_copy` |
| 24 | `tests/test_subject_layout.py::test_landscape_four_mixed_buckets_compose_via_mcs` |

**一键复现：**

```bash
python -m pytest -m "not integration and not e2e and not vision and not playwright_serial and not legacy_homepage" -q --tb=short
```

**按主题复现：**

```bash
# Mosaic 簇（17 项）
python -m pytest tests/test_golden_mosaic_unified.py tests/test_mosaic_*.py tests/test_golden_layouts.py::test_mosaic5_exposure_ab_fixture tests/test_layout_service.py::test_apply_layout_web_portrait_mosaic tests/test_subject_layout.py::test_landscape_four_mixed_buckets_compose_via_mcs -q --tb=short

# Ingest / ML cache（2 项）
python -m pytest tests/test_phase9_ingest_regression.py::test_ingest_e2e_ml_cache_reused_between_rebuilds tests/test_photo_cull_ml.py::test_apply_aesthetic_scores_uses_persistent_cache -q --tb=short

# Studio 非 playwright（3 项）
python -m pytest tests/test_studio_handlers_replan.py tests/test_studio_ux_p3.py -q --tb=short
```

---

## 4. 失败清单 · Bucket B — Playwright E2E（全量 96 中约 72 项）

> 日志只截取了尾部用例名；其余约 **58 项** 在同标记套件内，需下次逐文件枚举。

### 4.1 已记录用例名（18 项）

**`test_studio_p9_qa_playwright.py`（11）**

- `test_p9_qa_playwright_empty_keyboard_and_sheet`
- `test_p9_qa_playwright_returning_skip_link_target`
- `test_p9_qa_playwright_no_horizontal_overflow_empty[980|1100|1280|1440]`
- `test_p9_qa_playwright_no_horizontal_overflow_returning[980|1100|1280|1440]`
- `test_p9_qa_playwright_sheet_pick_button_clickable`

**`test_studio_p10_layout_playwright.py`（3）**

- `test_p10_playwright_compact_failure_overlay`
- `test_p10_playwright_loading_compact_masthead`
- `test_p10_playwright_resize_import_stage_copy`

**`test_studio_phase9_cull_playwright.py`（4）**

- `test_ac_p9_ux_02_v3_success_msg_cull_line`
- `test_ac_p9_ux_04_max_photos_warn_non_blocking`
- `test_ac_p9_ux_05_fail_open_no_cull_line`
- `test_ac_p9_ux_06_compact_success_msg_no_overflow`

### 4.2 待下次枚举的 Playwright 文件（约 54 项推测）

| 文件 | 说明 |
|------|------|
| `tests/test_studio_lcp_playwright.py` | LCP |
| `tests/test_studio_home_v2_ac_playwright.py` | Homepage v2 AC |
| `tests/test_phase13_g8_studio_playwright.py` | Phase 13 G8 |
| `tests/g8_playwright_suite.py` | G8 套件 |
| 其他带 `playwright_serial` 标记的用例 | 见 `tests/conftest.py` |

**环境前置：**

```bash
pip install playwright
playwright install chromium
```

**一键枚举全部 playwright 失败（下次第一件事）：**

```bash
python -m pytest -m playwright_serial -q --tb=line 2>&1 | tee docs/reports/playwright-failures-YYYYMMDD.log
```

**全量复现：**

```bash
python -m pytest tests/ -q --tb=line 2>&1 | tee docs/reports/full-suite-failures-YYYYMMDD.log
```

---

## 5. 建议下次修复顺序

| 优先级 | 范围 | 理由 |
|--------|------|------|
| **P0** | Bucket A · Mosaic（17 项） | 无浏览器、阻塞 CI 快套件、可能与近期布局/MCS 变更有关 |
| **P1** | Bucket A · ingest/ML cache + studio replan/ux（5 项） | 独立小簇，修完快套件可全绿 |
| **P2** | Bucket B · Playwright | 需浏览器环境；先枚举完整列表再分批修 |
| **P3** | V2 人工 | `trips/mao` 落地 + 盲评 `judgeVerdict`（非 pytest 失败） |

---

## 6. 下次会话提示词（复制即用）

```text
请阅读 docs/reports/test-failures-handoff-2026-06-05.md，按 §5 优先级修复失败测试。

背景：
- 算法 V2（cover/sharpness/heuristic-v2）专项 61/61 已通过，不要动 V2 除非失败用例指向它。
- 全量 pytest tests/ 有 96 失败，主要是 Playwright；CI 快套件有 24 失败，主要是 Mosaic。

本次目标（按需选一或按顺序）：
1. 先跑 CI 快套件确认 24 项仍失败，从 Mosaic 簇开始修到全绿。
2. 跑 `pytest -m playwright_serial` 生成完整失败列表到 docs/reports/playwright-failures-*.log，再修 p9/p10/cull playwright。
3. 仅验证：跑 §1 的 V2 专项命令 + algorithm_v2_signoff --from-json。

约束：最小 diff；修测试前先 --tb=short 看断言；不要提交除非我要求。
```

---

## 7. 相关文档

- 实施清单：`docs/IMPLEMENTATION-ALGORITHM-V2.md`
- Kendall 报告：`docs/reports/algorithm-v2-kendall.md`
- 验收记录：`docs/acceptance-records/algorithm-v2-signoff.json`
- CI 快套件 marker 定义：`pyproject.toml` §tool.pytest.ini_options

---

## 8. 版本历史

| 日期 | 说明 |
|------|------|
| 2026-06-05 | 全量/快套件实测后初版；V2 全绿，记录 24+72 失败分布 |
