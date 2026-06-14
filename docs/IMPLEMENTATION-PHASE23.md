# Travelogue · Phase 23 实施任务清单（最佳时刻）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md) v0.23.2 |
| **验收** | [ACCEPTANCE-PHASE23.md](./ACCEPTANCE-PHASE23.md) |
| **分支** | `phase23/peak-moment` |
| **状态** | ☑ W1–W4 闭环 |
| **更新** | 2026-06-14 |

---

## 交付分期

| 波次 | 范围 | 出口 |
|------|------|------|
| **P23-W1** | ingest exif + `build_moment_pool` + curate 落盘 | pool + 签名字段 |
| **P23-W2** | `moment-screen` 模板 + assemble + CSS + EXIF 行 | 读者可见 |
| **P23-W3** | closing exclude + secondary 加权 + validate + 单测 | 双层闭环 |
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
| P23-2b | `build_moment_screen_context` | `render/moment_screen.py` | ☑ |
| P23-2c | assemble + `journal.hbs` | `render/assemble.py`, `journal.hbs` | ☑ |
| P23-2d | `moment-screen.hbs` + CSS | `partials/`, `journal-screens.css` | ☑ |
| P23-2e | `tests/test_moment_render.py` | — | ☑ |
| P23-2f | `performance` profile 省略 moment 屏 | `render/assemble.py` | ☑ |
| P23-2g | 英文 locale 标签 `Moment` | `render/moment_screen.py` | ☑ |

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
