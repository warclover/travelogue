# 五项回归失败 · 可修复性评估与修复方案

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-16 |
| **发现于** | `arch/algo-deepening-v1` 全量回归（相对 master **同源**，非 AAD 引入） |
| **分支建议** | 另开 `fix/cover-intent-regression`（勿混入 AAD PR） |
| **实施状态** | **F1–F5 已修**（分支 `fix/cover-intent-regression`） |

---

## 总览

| # | 失败用例 | 可修？ | 难度 | 优先级 | 根因一句话 |
|---|----------|--------|------|--------|------------|
| F1 | `test_cover_opening_title_card_styles` | **是** | S | P0 | 模板 CSS 已迁 V5，测试仍切 V4 注释块 → `IndexError` |
| F2 | `test_v4_cover_opening_layout_playwright` | **是** | M | P1 | 几何/样式合同随 V5 变；断言仍按 V4 书名卡 |
| F3 | `test_v4_dock_states_playwright` | **是** | M | P1 | 同上 + Dock/toolbar 交互可能超时 |
| F4 | `test_cover_styles_v5_sheet_switch_and_apply_layout` | **是** | M | P1 | Playwright：Sheet/菜单点击或 toast 超时（UI 时序） |
| F5 | `test_pipeline_with_plan_text_persists_intent` | **是** | S–M | **P0** | `ingest_travel_plan` 只改内存，未落盘；`_sync_trip_from_disk` 冲掉 `travelPlan.cities` |

**结论：5/5 均可修**；F1+F5 可当天修；F2–F4 需对齐 V5 合同 + 稳定 Playwright 选择器/等待。

---

## F5 · Intent 行程计划城市丢失（P0 · 真功能 bug）

### 现象
`plan.txt` 已写入 `source/intent/`，`parse_plan_text` 能解析出 `大阪/京都`，但最终 `trip.json` 的 `intent.travelPlan.cities` / `curation.intentHints.planCities` 为缺失。

### 根因（已复现）
```text
apply_intent → flush intent 到盘
→ ingest_travel_plan（内存写入 travelPlan + hints，只落盘 plan.txt）
→ run_trip(ingest) …
→ _sync_trip_from_disk  ← 用盘上旧 intent 覆盖内存 → cities 丢失
```

关键代码：`travelogue/web/studio_pipeline.py`（`ingest_travel_plan` 后无二次 flush）；`make_intent_flush_mutator` 只在 plan 解析**之前**调用。

### 修复方案
1. 在 `ingest_travel_plan(...)` **之后**立刻 `svc.update(trip_json, make_intent_flush_mutator(trip))`，并扩展 mutator（或新建）把：
   - `intent` 全量（含 `travelPlan`）
   - `curation.intentHints`（至少 `planCities`）
   一并写入磁盘。
2. 单测：保留 `test_pipeline_with_plan_text_persists_intent`；可补「仅 ingest 阶段后读盘即有 cities」的更短集成测。
3. 回归：跑 `tests/unit/curation/test_intent_plan.py`。

**验收**：`cities == ["大阪","京都"]` 且章标题含城市名。

---

## F1 · Cover V4 CSS 合同单测（P0 · 测试债）

### 现象
```python
css.split("/* V4 · 右下实心书名卡 */", 1)[1]  # IndexError
```
`templates/visual-journal/journal.css` **已无**该注释；封面已演进为 V5 多 `data-cover-opening` 样式（`veil-footer` 等）。`trips/linzhi/journal.css` 仍残留旧注释，说明狗粮副本未统一。

### 修复方案（二选一，推荐 A）
**A. 更新测试合同到 V5（推荐）**
- 删除/改写 `test_cover_opening_title_card_styles`，改为断言现行默认样式（如 `veil-footer` / panel 关键 token）。
- Token 清单与产品/设计对齐（`position`、`max-width`、隐藏 `.trip-meta` 等仍可保留能在现 CSS 中找到的部分）。

**B. 恢复 V4 注释锚点（不推荐）**
- 仅加回注释而不恢复几何 → 测过无意义；完整恢复 V4 会与 V5 产品方向冲突。

**验收**：无 `IndexError`；断言与 `journal.css` 现行源一致。

---

## F2 / F3 · Cover V4 Playwright（P1 · 合同漂移）

### 现象
基于 V4 书名卡几何（`max-content`、右下实心卡、`rgba(18,17,16,0.9)`、`border-left: 5px` 等）做 layout AC；CSS/产品已 V5，易导致尺寸断言失败或等待超时。

### 修复方案
1. **产品定案**：V4 AC 是废弃还是保留为「历史布局」？
   - 若废弃 → 标记 `@pytest.mark.skip(reason="superseded by V5")` 或迁移到 `test_cover_styles_v5*`。
   - 若保留兼容 → 在 CSS 为默认/`data-cover-opening` 显式恢复可测几何，并更新 seed HTML。
2. 推荐路径：**迁到 V5 AC**（封面一屏、panel 在视口内、toolbar 不挡标题），重写 `page.evaluate` 度量阈值。
3. Playwright：统一 `wait_for`（dock visible、fonts ready、无 toast）；超时从 30s 调到稳定值或重试 1 次。

**验收**：Chromium 本地绿；不依赖中文注释 split。

---

## F4 · Cover V5 Sheet 切换（P1 · E2E 不稳）

### 现象
`test_cover_styles_v5_sheet_switch_and_apply_layout`：菜单/Sheet/`save-copy`/toast「封面版式已更新」链路超时（曾见 `Locator.click` 30s）。

### 修复方案
1. **稳定选择器**：确认 `.preview-toolbar__menu-btn`、`.preview-sheet__tab[data-sheet-tab="layout"]`、`[data-cover-style=…]` 在当前 toolbar v3 仍存在；若改名则改测。
2. **时序**：`networkidle` 后显式等 dock；点菜单前关掉 toast；`expect_response(/save-copy/)` 保留。
3. **隔离**：已有 `playwright_serial`；确认无并行 studio server 端口冲突。
4. 若产品改了「切换封面不发 save-copy」→ 同步改断言事件名。

**验收**：连续 3 次本地跑通该单测。

---

## 建议实施顺序

```text
Day 0（0.5d）  F5 落盘 flush + 单测绿
Day 0（0.5d）  F1 改写 CSS 合同到 V5
Day 1（1d）    F2/F3 迁 V5 Playwright AC 或 skip+文档
Day 1–2（1d）  F4 选择器/等待加固，串行复跑 3 次
```

**不做**：把上述修混进 AAD PR；AAD 保持 flag 关合入。

---

## 分支 / PR 切分

| PR | 内容 | 门禁 |
|----|------|------|
| PR-intent | F5 pipeline flush | `test_intent_plan` |
| PR-cover-contract | F1 +（可选）F2/F3 合同迁移 | cover v4/v5 相关 |
| PR-cover-e2e | F4 稳定性 | playwright_serial 绿 |

---

## 与 AAD 关系

- AAD **未引入**上述失败（master worktree 已复现 F1/F5）。
- 合入 AAD 后可用本方案清债，使 `layout_engine+curation+media` 全量更接近 exit 0。
