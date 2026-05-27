# PRD-EXPERIENCE · 实施任务清单

| 属性 | 内容 |
|------|------|
| **权威 PRD** | [PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) |
| **ADR** | [adr/003-experience-reading-modes.md](./adr/003-experience-reading-modes.md) |
| **矩阵** | [experience-matrix.yaml](./experience-matrix.yaml) |
| **更新** | 2026-05-27 |

本文档按 **逻辑依赖顺序** 排列任务；前置未完成时，后置仅可 stub/跳过。

---

## 阶段总览

| 阶段 | Epic | 目标 | 用户可见 |
|------|------|------|----------|
| **0 · 契约** | E0 | 屏序测试、文档对齐 | 无 |
| **1 · 配置壳** | E1 | `export.reading` + HTML 注入 | 无（可 `--reading-profile` 验证） |
| **2 · Hybrid 最小包** | E2 | snap + breath soft + folio lite | **有** |
| **3 · 模式同步** | E3–E4 | present↔scroll、longshot teardown | 有 |
| **4 · 精选域** | E5 | 双文件夹 `userTier` | 有 |
| **5 · 增强** | E6–E8 | flow / folio full / cinematic | 可选 |

| **当前进度**：E0–E8 Epic 已落地；**Post-Epic P0–P5 已全部完成** |

---

## Post-Epic 收尾（2026-05-27 · 文档 / CI / AC 补全）

- [x] `schemas/fixtures/trip.linzhi_screens.json` · CI 用 5 章 20 屏屏序契约（无本地 `trips/linzhi` 时不 skip）
- [x] `test_linzhi_ci_screen_order_contract` · 替代 CI 中空跑的 skip
- [x] `tests/test_reading_ac_regression.py` · AC-EXP-02/05 · AC-FO-03/04/05 · skipAuxBlocks · present 书签
- [x] 文档阶段总览 / Post-Epic P2–P4 落地 / 验证命令同步

PRD 总 AC 中 **浏览器 E2E**（AC-EXP-06 视口对齐、AC-EXP-10/12 真无 JS 环境）仍为 **静态/渲染 smoke**，非 Playwright 级 E2E。

---

## 后续任务 · P0–P5

PRD 完整度约 **90%+**；Epic + Post-Epic P0–P5 清单已闭环；剩余为可选浏览器 E2E。

### P0 · 发布门禁 / 契约（优先）

| # | 任务 | PRD / AC | 模块 | 状态 |
|---|------|----------|------|------|
| P0-1 | 林芝屏序 = present 序回归 | E0-3 · AC-EXP-01 | `trip.linzhi_screens.json` + `trips/linzhi` | **完成** |
| P0-2 | inline-edit 禁用 present | AC-EXP-09 | `engine.py` · `context.py` · `journal.hbs` | **完成** |
| P0-3 | flow/cinematic 后 longshot 捕获 smoke | AC-EXP-03 | `tests/test_reading_flow.py` | **完成** |
| P0-4 | `present.skipAuxBlocks` 端到端 | PRD §5.2 | `screenplay.js` · partials | **完成** |

**P0 出口**：AC-EXP-01 / 03 / 09 有自动化或签核；draft 无 inline-edit + present 冲突。（2026-05-27 已达成）

### Post-Epic · P0 落地（2026-05-27）

- [x] P0-1 · `test_linzhi_ci_screen_order_contract` + 可选 `trips/linzhi`
- [x] P0-2 · `should_include_screenplay(export_mode=draft)` → False；draft 保留 longshot-bridge toolbar
- [x] P0-3 · flow profile + longshot teardown API smoke
- [x] P0-4 · `skipAuxBlocks` · `presentSlideSelector` · `data-present-aux` partials

### Post-Epic · P1 落地（2026-05-27）

- [x] P1-1 · `importSource` on ingest · `resolve_import_source` · schema enum · `test_user_tier.py`
- [x] P1-2 · `from-album` / `demo` · `--featured-dir` / `--material-dir` → `run_demo_from_album` → ingest
- [x] P1-3 · AC-DF-01～08 自动化子集 · `test_user_tier.py` · `test_ac_df_*`
- [x] P1-4 · beam `featured_beam` · +0.15/asset · hero_separation 0.5 when featured hero reuse

### Post-Epic · P2 落地（2026-05-27）

- [x] P2-1 … P2-6 · foreword-spread · screen-spread · screen-plate · epilogue-screen · manifest · `test_reading_folio.py`

### Post-Epic · P3 落地（2026-05-27）

- [x] P3-1 … P3-4 · gallery screens pin · present 书签 · AC-BR-02 · curate WARN

### Post-Epic · P4 落地（2026-05-27）

- [x] P4-1 … P4-5 · breathMode/folioMode 别名 · schema · AC-EXP-10/12 · ADR-003 checklist

### P1 · 附录 A 补齐

| # | 任务 | 模块 |
|---|------|------|
| P1-1 | ingest 写 `importSource` | `ingest.py` · schema | **完成** |
| P1-2 | `from-album` / demo 接双文件夹 CLI | `cli.py` | **完成** |
| P1-3 | AC-DF 自动化子集 | `test_user_tier.py` | **完成** |
| P1-4 | beam featured 加权 + hero_separation 减半 | `layout_scoring.py` · `layout_search.py` | **完成** |

### P2 · Folio full 剩余块

| # | 任务 | 模块 |
|---|------|------|
| P2-1 | `foreword-spread` | partial · `context.py` | **完成** |
| P2-2 | `screen-spread` | partial · planner | **完成** |
| P2-3 | 专用 `screen-plate` + `.plate-caption` | `screen_planner` · hbs | **完成** |
| P2-4 | `epilogue-screen` 独立 block | partial | **完成** |
| P2-5 | manifest 白名单 | `manifest.json` | **完成** |
| P2-6 | AC-FO 自动化子集 | `test_reading_folio.py` | **完成** |

### P3 · 动效 / present 打磨

| # | 任务 | 模块 |
|---|------|------|
| P3-1 | web 路径 gallery pin（或改 PRD 口径） | `breath-gsap.js` | **完成** |
| P3-2 | present + folio 辅助块书签 | `screenplay.js` | **完成** |
| P3-3 | AC-BR-02 flow tail ≤300ms | perf smoke | **完成** |
| P3-4 | cinematic + folio full + 大 trip WARN | `curate.py` | **完成** |

### P4 · 兼容 / schema / 文档

| # | 任务 | 模块 |
|---|------|------|
| P4-1 | `export.breathMode` / `folioMode` 别名 | `reading_profile.py` | **完成** |
| P4-2 | `tripCuration` schema 补全 | `trip.schema.json` | **完成** |
| P4-3 | AC-EXP-10 reduced-motion E2E | tests | **完成** |
| P4-4 | AC-EXP-12 无 JS 可读 | templates · CSS | **完成** |
| P4-5 | ADR-003 checklist 同步 | `docs/adr/` | **完成** |

### P5 · 增强（2026-05-27 落地）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| P5-1 | URL hash `#present/N` 深链 | `screenplay.js` · `reading_profile.py` | **完成** |
| P5-2 | 可选真 GSAP（`scroll.breathEngine: gsap`） | `breath-gsap.js` · `journal.hbs` | **完成** |
| P5-3 | G2 serve tier 升格 | `user_tier.py` · `serve.py` · `tier promote` CLI | **完成** |
| P5-4 | PDF 导出 | `export/pdf.py` · `export-pdf` CLI | **完成** |
| P5-5 | mobile breath/folio（`export.reading.mobileProfile`） | `reading_profile.py` · schema | **完成** |

### Post-Epic · P5 落地（2026-05-27）

- [x] P5-1 · `#present/12` · hashchange · `present.deepLink`
- [x] P5-2 · GSAP CDN + ScrollTrigger scrub 分支
- [x] P5-3 · `POST /__travelogue/promote-tier` · `travelogue tier promote`
- [x] P5-4 · `travelogue export-pdf`（Playwright）
- [x] P5-5 · `mobileProfile: default_hybrid` opt-in
- [x] `tests/test_reading_p5.py`

### 建议执行顺序

```text
Phase 1: P0-1 → P0-2 → P0-3 → P0-4
Phase 2: P1-*
Phase 3: P2-*
Phase 4: P3-* + P4-*
```

---

## E0 · 屏序契约（前置 · 低代码）

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E0-1 | 自动化：scroll 屏数 = screenplay slides 数 | `tests/test_reading_screen_order.py` | screens fixture | **完成** |
| E0-2 | 自动化：longshot cards ≥ Σ screens slots | 同上 + `test_longshot_chapter.py` | E0-1 | **完成** |
| E0-3 | 林芝 fixture 纳入 CI | `trip.linzhi_screens.json` + 可选 `trips/linzhi` | E0-1 | **完成** |

**不改**：`screen_planner.py` 主算法、`flatten_screens_to_items()`。

---

## E1 · Profile 配置壳（当前实施）

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E1-1 | `trip.schema.json` 增加 `export.reading`、`assets.userTier` | `schemas/` | — | **完成** |
| E1-2 | `reading_profile.py`：加载 matrix、按 surface 解析 profile | `travelogue/render/` | E1-1 | **完成** |
| E1-3 | `build_render_context` 注入 `__TRAVELOGUE_READING__` + `data-*` attrs | `context.py` + `journal.hbs` | E1-2 | **完成** |
| E1-4 | `render_html` / `render_trip` / `render_trip_surfaces` 传递 `index_name`、`reading_profile_override` | `engine.py` | E1-3 | **完成** |
| E1-5 | CLI `render --reading-profile` | `cli.py` | E1-4 | **完成** |
| E1-6 | `config.yaml` `render.reading.*` 默认值 | `config.py` + `config.yaml.example` | E1-2 | **完成** |
| E1-7 | `screenplay.js` 读 `present.dwellMs`；toolbar 改「放映」 | `templates/` | E1-3 | **完成** |
| E1-8 | `longshot.js` 捕获前 `teardown` 钩子（no-op API） | `longshot.js` | E1-3 | **完成** |
| E1-9 | `test_reading_profile.py`：各 surface 默认 profile | `tests/` | E1-3 | **完成** |

**验收**：`render --dual` 后 `index.html` 含 `__TRAVELOGUE_READING__` 且 `profile=default_hybrid`；`--reading-profile legacy` 全 off；share 模式 `performance`。

---

## E2 · Hybrid 最小包

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E2-1 | CSS：`[data-snap="proximity"]` 整页 scroll-snap | `journal-screens.css` | E1 | **完成** |
| E2-2 | 新 `breath.js`：soft 档（IO + CSS，无 GSAP） | `templates/` | E1 | **完成** |
| E2-3 | folio lite：页眉/页码 partial + CSS variables | `layout-screen.hbs` + CSS | E1 | **完成** |
| E2-4 | present 启动时 pause breath | `screenplay.js` + `breath.js` | E2-2 | **完成** |
| E2-5 | AC-EXP-02 自动化 | `tests/test_reading_experience.py` | E2-1–3 | **完成** |

---

## E3 · Present ↔ Scroll 同步

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E3-1 | render 为 `.layout-screen` 写 `data-screen-index` | `layout-screen.hbs` | E1 | **完成**（E2） |
| E3-2 | `screenplay.js` 退出时 `scrollIntoView` | `screenplay.js` | E3-1 | **完成** |
| E3-3 | 读 `present.syncScrollOnExit` | `screenplay.js` | E1 | **完成** |
| E3-4 | AC-EXP-06 | `tests/test_reading_present_sync.py` | E3-2 | **完成** |

---

## E4 · Longshot teardown

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E4-1 | `TravelogueBreath.destroy()` 清除 transform/opacity | `breath.js` | E2-2 | **完成** |
| E4-2 | 捕获后恢复 scroll + breath | `longshot.js` | E4-1 | **完成** |
| E4-3 | teardown/restore API 测试 | `tests/test_reading_present_sync.py` | E4-1 | **完成** |

---

## E5 · 附录 A · userTier

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E5-1 | 双源 `from-album` / ingest 目录布局 | `ingest.py` + CLI | E1-1 | **完成** |
| E5-2 | `userTier` / `userTierSource` 写入 asset | `ingest.py` | E5-1 | **完成** |
| E5-3 | `cover_score` featured 加权 | `curate_scoring.py` | E5-2 | **完成** |
| E5-4 | `screen_planner` plate/hero 优先 featured | `screen_planner.py` | E5-3 | **完成** |
| E5-5 | `userTierSummary` 报告 | `curate.py` | E5-2 | **完成** |
| E5-6 | render 注入 `featuredAssetIds` | `reading_profile.py` | E5-2 | **完成** |
| E5-7 | `present.featuredOnly` 过滤 | `screenplay.js` | E5-6 | **完成** |

---

## E6 · breath flow + featured present

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E6-1 | `breath-lenis.js` · lerp 平滑滚轮 | `templates/` | E2 | **完成** |
| E6-2 | `breath.js` flow 路由 + destroy Lenis | `breath.js` | E6-1 | **完成** |
| E6-3 | render 按 profile 打包 lenis | `engine.py` + `journal.hbs` | E6-1 | **完成** |
| E6-4 | present 激活/退出 pause/resume Lenis | `screenplay.js` | E6-2 | **完成** |
| E6-5 | 精选放映 toggle（`featuredOnly` 运行时切换） | `screenplay.js` + toolbar | E5 | **完成** |
| E6-6 | featured reveal 时长 ×1.15（flow CSS） | `breath.css` | E5 | **完成** |
| E6-7 | AC-BR-02 / flow 自动化 | `tests/test_reading_flow.py` | E6-1–5 | **完成** |

---

## E7 · folio full + featured-grid

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E7-1 | `folio_plan.py` · grid 选取 + screens 去重 | `curation/` | E5 | **完成** |
| E7-2 | curate 写入 `curation.folioPlan` | `curate.py` | E7-1 | **完成** |
| E7-3 | render · `trip-index` + `featured-grid` partial | `context.py` + `journal.hbs` | E7-1 | **完成** |
| E7-4 | folio full CSS | `journal-screens.css` | E2 | **完成** |
| E7-5 | schema · `folioPlan` | `trip.schema.json` | E7-2 | **完成** |
| E7-6 | AC-EXP-11 自动化 | `tests/test_reading_folio.py` | E7-1–3 | **完成** |

---

## E8 · cinematic + gallery pin

| # | 任务 | 模块 | 依赖 | 状态 |
|---|------|------|------|------|
| E8-1 | `breath-gsap.js` · TravelogueScrub（无 GSAP 硬依赖） | `templates/` | E2 | **完成** |
| E8-2 | cinematic · cover/header/首屏视差 scrub | `breath-gsap.js` | E8-1 | **完成** |
| E8-3 | gallery · `media-scroll` 章 pin 横滑 | `breath-gsap.js` | E8-1 | **完成** |
| E8-4 | `breath.js` 路由 + teardown | `breath.js` | E8-1 | **完成** |
| E8-5 | render 按 breath 档位打包 scrub | `engine.py` + `journal.hbs` | E8-1 | **完成** |
| E8-6 | AC-BR-03 / scrub 自动化 | `tests/test_reading_cinematic.py` | E8-1–5 | **完成** |

---

## 不建议改动的模块

- `should_include_long_shot` / bridge 分叉（Plan A）
- `render_trip_surfaces` 双 index 结构
- `flatten_screens_to_items`
- Agent 2 narrate 核心（E5 之前）

---

## 已完成（2026-05-27 · E1 首批）

- [x] E1-1 `trip.schema.json` · `export.reading` + `userTier`
- [x] E1-2 `reading_profile.py`
- [x] E1-3 `build_render_context` + `journal.hbs` 注入
- [x] E1-4 `engine.py` · `index_name` / override 传递
- [x] E1-5 CLI `--reading-profile`
- [x] E1-6 `config.yaml.example` · `render.reading`
- [x] E1-7 `screenplay.js` · dwellMs + 「放映」文案
- [x] E1-8 `longshot.js` · teardown 钩子
- [x] E1-9 `test_reading_profile.py`

### E0 + E2（同日）

- [x] E0-1 / E0-2 / **E0-3** · `test_reading_screen_order.py` · `test_linzhi_screen_order_contract`
- [x] E2-1 … E2-5 · breath.js/css · folio lite · snap CSS · `test_reading_experience.py`

### E3 + E4（同日）

- [x] E3-2/3 · `screenplay.js` · `syncScrollToSlide` + `syncScrollOnExit`
- [x] E4-1/2 · `breath.destroy` · `longshot` teardown/restore · `test_reading_present_sync.py`

### E5 · userTier / 双文件夹

- [x] E5-1 … E5-7 · ingest 双源 · curate 加权 · screen_planner hero · `featuredAssetIds` · `present.featuredOnly`
- [x] `tests/test_user_tier.py`

### E6 · breath flow + featured present

- [x] E6-1 … E6-7 · `breath-lenis.js` · Lenis pause · 精选放映 toggle · `tests/test_reading_flow.py`

### E7 · folio full

- [x] E7-1 … E7-6 · `folio_plan.py` · trip-index · featured-grid · screens 去重 · `tests/test_reading_folio.py`

### E8 · cinematic + gallery pin

- [x] E8-1 … E8-6 · `breath-gsap.js` · TravelogueScrub · gallery pin · `tests/test_reading_cinematic.py`

---

## 本地验证命令

```powershell
# 默认 Hybrid profile
python -m travelogue render trips\<id>\trip.json --dual

# 回归基线
python -m travelogue render trips\<id>\trip.json --dual --reading-profile legacy

# 测试（reading / experience 子集）
python -m pytest tests/test_reading_profile.py tests/test_user_tier.py tests/test_demo_from_album.py tests/test_reading_flow.py tests/test_reading_folio.py tests/test_reading_cinematic.py tests/test_reading_present_sync.py tests/test_reading_experience.py tests/test_reading_screen_order.py tests/test_reading_compat.py tests/test_curate_reading_warnings.py tests/test_reading_ac_regression.py tests/test_reading_p5.py -q

# PDF（需 playwright）
python -m travelogue export-pdf trips\<id>

# G2 tier 升格
python -m travelogue tier promote trips\<id>\trip.json asset-003
```
