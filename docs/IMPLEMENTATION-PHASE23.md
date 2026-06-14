# Travelogue · Phase 23 实施任务清单（最佳时刻）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md) v0.23.3 |
| **验收** | [ACCEPTANCE-PHASE23.md](./ACCEPTANCE-PHASE23.md) |
| **分支** | `phase23/peak-moment` |
| **状态** | ☑ W1–W4 闭环 |
| **更新** | 2026-06-14 |

---

## 交付分期

| 波次 | 范围 | 出口 |
|------|------|------|
| **P23-W1** | ingest exif + `build_moment_pool` + curate 落盘 | pool + 签名字段 |
| **P23-W2** | inline `layout-screen` + `moment-exif-bar` + assemble + CSS | 读者可见 |
| **P23-W3** | closing exclude + `pool_solo` + validate + 单测 | 双层闭环 |
| **P23-W4** | Studio 池条带 + 盲评脚本 | 可运营调参 |

---

## P23-W0 · Kickoff

| ID | 任务 | 状态 |
|----|------|------|
| P23-0a | PRD v0.23.2 | ☑ |
| P23-0b | ACCEPTANCE-PHASE23 | ☑ |
| P23-0c | 开分支 `phase23/peak-moment` | ☑ |
| P23-0d | IMPLEMENTATION-PHASE23 | ☑ |

---

## P23-W1 · 选型与数据

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P23-1a | `MomentConfig` + loader | `config/moment.py`, `config/curate.py`, `loader.py` | ☑ |
| P23-1b | `read_camera_exif` | `media/exif_camera.py` | ☑ |
| P23-1c | ingest 写入 `assets[].exif` | `media/ingest.py` | ☑ |
| P23-1d | `moment_scoring.py` 双层选型 | `curation/moment_scoring.py` | ☑ |
| P23-1e | curate preflight + finalize | `curation/curate.py` | ☑ |
| P23-1f | aesthetic `moment` preset | `config/aesthetic.py`, `aesthetic_score.py` | ☑ |
| P23-1g | `tests/test_peak_moment_scoring.py` | — | ☑ |
| P23-1h | `tests/test_ingest_exif_camera.py` | — | ☑ |

---

## P23-W2 · 渲染

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P23-2a | `format_moment_exif_line` | `render/moment_exif.py` | ☑ |
| P23-2b | `build_layout_screen` moment/peak 上下文 | `render/context.py` | ☑ |
| P23-2c | assemble + `journal.hbs` | `render/assemble.py`, `journal.hbs` | ☑ |
| P23-2d | `layout-screen.hbs` 角标 + peak role + CSS | `partials/`, `journal-screens.css` | ☑ |
| P23-2e | `tests/test_moment_render.py` | — | ☑ |
| P23-2f | `performance` profile 省略 EXIF 保留 solo | `render/assemble.py` | ☑ |
| P23-2g | 英文 locale 角标 `Moment` | `render/context.py` | ☑ |

---

## P23.1 · 池内全员 solo + EXIF（v0.23.3）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P23.1-1 | `pool_solo` / `pool_exif` / `signature_label` 配置 | `config/moment.py` | ☑ |
| P23.1-2 | `ensure_pool_assets_solo_screens` + plate 避让 | `curation/moment_scoring.py` | ☑ |
| P23.1-3 | `moment_exif_pool_ids` 渲染 + performance solo 解耦 | `render/assemble.py`, `chapters.py`, `context.py` | ☑ |
| P23.1-4 | inline 角标 + `data-role="peak"` | `layout-screen.hbs`, `journal-screens.css` | ☑ |
| P23.1-5 | schema `layoutScreen.role` | `schemas/trip.schema.json` | ☑ |
| P23.1-6 | 池内/performance/配置回退测试 | `tests/test_moment_render.py` 等 | ☑ |
| P23.1-7 | `effective_secondary_boost` pool_solo 降级 | `config/moment.py`, `curate.py` | ☑ |
| P23.1-8 | breath peak 屏 + screen-weight 分层 | `breath.js`, `breath.css`, `journal-screens.css` | ☑ |
| P23.1-9 | `config.yaml` / example / demo 文档化 | `config.yaml`, `config.yaml.example`, `config.demo.yaml` | ☑ |
| P23.1-10 | 文档/验收同步 v0.23.3 | PRD · AC · RENDER-CONTRACT | ☑ |

---

## P23-W3 · 封底与 secondary

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P23-3a | `resolve_closing_asset_id(exclude_ids=)` | `render/cover_closing.py` | ☑ |
| P23-3b | peak 章 hero `preferred_id` + 跨章去重 | `curate.py`, `curate_scoring.py` | ☑ |
| P23-3c | `config.yaml.example` moment + aesthetic | `config.yaml.example` | ☑ |
| P23-3d | `layout_scoring` secondary_boost | `layout_scoring.py`, `mosaic/search.py` | ☑ |
| P23-3e | featured-grid 排除 `momentAssetId` | `folio_plan.py`, `curate.py` | ☑ |
| P23-3f | `validate_trip` moment 规则 | `services/validate.py` | ☑ |
| P23-3g | `DATA-MODEL.md` v0.2.3 字段 | `docs/DATA-MODEL.md` | ☑ |
| P23-3h | `tests/test_validate_moment.py` | — | ☑ |
| P23-3i | `tests/test_bsp_moment_playwright.py` | — | ☑ |

---

## P23-W4 · Studio / 盲评

| ID | 任务 | 状态 |
|----|------|------|
| P23-4a | Studio 池条带 + `momentExplain` 展示 | ☑ |
| P23-4b | PATCH `momentAssetId` API 校验 | ☑ |
| P23-4c | 盲评脚本 + `phase23-moment-blind-review.json` | ☑ |

---

## 关键接口

```python
# curation/moment_scoring.py
def sync_trip_moments_preflight(trip, layout_assets, cfg, ...) -> list[str]
def sync_trip_moments_finalize(trip, layout_assets, chapters, cfg, ...) -> str | None
```

```python
# curation/layout_scoring.py
def moment_secondary_plan_bonus(screens, *, arc_segment, secondary_ids, boost) -> float
```

```python
# render/cover_closing.py
def resolve_closing_asset_id(..., exclude_ids: set[str] | None = None) -> str | None
```

---

## 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | Kickoff · 双层模型实施清单 |
| v0.2 | 2026-06-14 | W1–W3 代码与单测落地 |
| v0.3 | 2026-06-14 | W3 补齐：secondary_boost · featured-grid · validate · Playwright |
