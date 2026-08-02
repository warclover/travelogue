# 封面多样式 V6 · 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) **v1.3.0**（产品母文档） |
| **艺术指导 Delta** | [PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md](./PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md) **v1.1.0**（十款 active · 联合/hash/Studio） |
| **视觉真相源** | [cover-styles-v6-art-direction-v2-wireframe.html](./wireframes/cover-styles-v6-art-direction-v2-wireframe.html) |
| **验收** | [ACCEPTANCE-COVER-STYLES-V6.md](./ACCEPTANCE-COVER-STYLES-V6.md)（含 AC-CSV6AD-*） |
| **更新日期** | 2026-08-02 |

> **冲突裁决**：IMPLEMENTATION / 现网代码与 PRD 冲突时，**产品契约以 V6 PRD v1.3.0 为准**；**视觉 token / 手法以 Art Direction Delta 为准**。

---

## 1. 范围门禁

| 做 | 不做（本 PRD） |
|----|----------------|
| Opening 五款 + Engine Registry + resolve/legacy | 封底改版（仅不回归） |
| Schema V6∪V5；写入仅 assignable | 完整 Admin / 实验室 UI（P0.5/P1） |
| M1 可渲染 + Studio 五选一（blurb） | Mobile 五皮肤 |
| M2 联合选型 + 锁定 + Toast/换版式重荐 | 删 V5 CSS（P2） |

---

## 2. 文件挂点清单

### 2.1 新增

| 文件 | 说明 | 里程碑 |
|------|------|--------|
| `travelogue/cover_engine/__init__.py` | 公共 API 出口（CSE 契约） | M1 |
| `travelogue/cover_engine/types.py` | `CoverStyleRecord` / `CoverStyleProfile` / `CoverJointExplain` | M1 |
| `travelogue/cover_engine/registry.py` | Registry 单例、list/get/status/weight | M1 |
| `travelogue/cover_engine/catalog.py` | 五款 active + V5 legacy 映射注册 | M1 |
| `travelogue/cover_engine/resolve.py` | `resolve_style_id` / `legacy_map` / `resolve_cover_opening_style` | M1 |
| `travelogue/cover_engine/studio.py` | `studio_style_options` / `list_preview_matrix` | M1 |
| `travelogue/cover_engine/fit.py` | `style_fit_score` / `style_avoid_penalty` / threshold（M1 骨架，M2 调权） | M1→M2 |
| `travelogue/cover_engine/joint.py` | `pick_*` / `apply_joint_pick` / `hash_fallback` / `repick_*` | **M2** |
| `travelogue/cover_engine/telemetry.py` | `record_cover_joint_event` | **M2** |
| `tests/unit/curation/test_cover_styles_v6.py` | Registry / resolve / legacy / Studio options | M1 |
| `docs/ACCEPTANCE-COVER-STYLES-V6.md` | 封板验收 | 封板前 |

### 2.2 修改（会改）

| 文件 | 变更 | 里程碑 |
|------|------|--------|
| `travelogue/services/cover_opening_style.py` | **薄 shim**：委托 Engine；`assign_*` → 默认占位（废哈希主路径） | M1 |
| `travelogue/services/trip_factory.py` | `coverOpeningStyle = get_default_style_id()`；`coverJointLocked` 可延后 M2 | M1 |
| `schemas/trip.schema.json` | `coverOpeningStyle` enum = V6∪V5；M2 加 `coverJointLocked` / `coverStyleExplain` | M1 / M2 |
| `travelogue/render/assemble.py` | 继续 `resolve_cover_opening_style`（真相源改 Engine） | M1 |
| `travelogue/web/studio_entry.py` | 注入 `coverStyleOptions`（`studio_style_options()`） | M1 |
| `travelogue/web/copy_patch.py` | 写入校验 `is_assignable` | M1 |
| `templates/visual-journal/journal.css` | §4.7 token + 五款皮肤；窄屏仅 CSS 回落 veil；V5 CSS 暂留至 P2 | M1 |
| `templates/studio/preview-toolbar/features.js` | 排版选项改读 entry.`coverStyleOptions`；展示 blurb | M1 |
| `templates/studio/preview-toolbar/sheet.css` | 五款缩略图；V5 thumb 可留 | M1 |
| `templates/studio/preview-toolbar/shell.js` / `core.js` | 默认回落 id → `veil-footer` | M1 |
| `travelogue/curation/curate.py`（`sync_trip_covers`） | 包装 joint + `coverJointLocked` | **M2** |
| `travelogue/curation/curate_scoring.py` / `cover_scoring_v2.py` | 质量分供 joint 复用（只读） | **M2** |
| `tests/unit/curation/test_cover_styles_v5.py` | resolve/create 期望对齐 V6；哈希分布测删除或改 M2 fallback | M1 |
| `tests/unit/trip/test_asset_version.py` | journal.css 变更后 bump golden | M1 |
| `tests/unit/domain/test_guardrails_copy_patch.py` | patch 值改 assignable | M1 |

### 2.3 明确不改（本阶段）

| 文件 / 主题 | 原因 |
|-------------|------|
| `cover-opening.hbs` 块清单 | 一块 DOM 铁律；仅 `data-cover-opening` 分岔 |
| `cover-closing.hbs` / 封底视觉 | §8.3 另立 Closing PRD |
| Admin HTTP / 实验室完整页 | CSE-13/14 非 M1 门禁 |
| Icon Dock 业务逻辑 | 仅 CSS 安全区 / z-index |

---

## 3. Cover Style Engine · M1 契约落地

| ID | 接口 | M1 |
|----|------|----|
| API-CSE-01 | `get_registry` + 启动注册五款 active | ✅ |
| API-CSE-02 | `list_assignable_styles` | ✅ |
| API-CSE-03 | `get_style` / `get_profile` | ✅ |
| API-CSE-04 | `resolve_style_id` + `legacy_map` | ✅ |
| API-CSE-05 | `get_default_style_id` → `veil-footer` | ✅ |
| API-CSE-09 | `studio_style_options` | ✅ |
| API-CSE-06/07/08/12/16/17 | fit / joint / repick / telemetry | M2（M1 可留空实现或 NotImplemented 骨架） |
| API-CSE-10/11 | preview_matrix / set_style_status | M1 库函数可测；不挡视觉合并 |

**兼容映射（D-CSV6-03）**

| V5 | V6 |
|----|-----|
| `card-br` | `veil-footer` |
| `split-mat` | `folio-overlap` |
| `magazine-head` | `folio-overlap` |

渲染期映射，**默认不写回** trip.json。

---

## 4. 任务拆解

### M1（本轮）

- [x] IMPLEMENTATION 文档（本文件）
- [x] `travelogue/cover_engine/` Registry + catalog + resolve + studio
- [x] `cover_opening_style.py` shim；`trip_factory` 占位；`copy_patch` / `studio_entry`
- [x] Schema enum V6∪V5
- [x] `journal.css` 五款 + token + 窄屏回落（≥64rem 分岔；&lt;1024px 呈 veil）
- [x] Studio Sheet 五选一读引擎 + blurb
- [x] 单测：assignable / legacy_map / resolve / create 占位 / Studio options
- [x] assetVersion golden bump

**M1 门禁（PRD §9.1）**：AC 皮肤 + 兼容 + CSE-01～05/09；**可不**开联合默认。

### M2

- [x] `joint.py`：`pick_cover_style_and_asset` / `apply_joint_pick` / `hash_fallback_pick` / `repick_cover_for_style`
- [x] 包装 `sync_trip_covers` + `curation.coverJointLocked`
- [x] Schema：`coverJointLocked` / `coverStyleExplain`
- [x] fit 黄金集；telemetry CSE-17
- [x] Studio：Toast（每 trip 一次）、老 V5 说明、换版式主 CTA=重荐图
- [x] ACCEPTANCE 文档（[ACCEPTANCE-COVER-STYLES-V6.md](./ACCEPTANCE-COVER-STYLES-V6.md)）
- [x] P0 缺口补齐：临时预览角标、Dock 安全区、§4.7 token、folio 无 hook、fit 灰字、黄金集全五款、V6 Playwright 最小套件

### P0.5 / P1+

- 实验室页、Admin HTTP、Closing PRD、删 V5 CSS、band 墨色自动、LLM 平局

---

## 5. 测试命令

```bash
# M1 + M2 + Art Direction Delta
python -m pytest tests/unit/curation/test_cover_styles_v6.py \
  tests/unit/curation/test_cover_styles_v6_joint.py \
  tests/unit/curation/test_cover_styles_v6_golden.py \
  tests/unit/curation/test_cover_styles_v5.py \
  tests/unit/curation/test_cover_by_layout.py \
  tests/unit/domain/test_copy_patch.py \
  tests/unit/trip/test_asset_version.py \
  tests/unit/domain/test_guardrails_copy_patch.py -q -m "not e2e and not playwright_serial"

# V6 Playwright 最小套件
python -m pytest tests/unit/curation/test_cover_styles_v6_playwright.py -q
```

## 6. 本地预览

```bash
# 解析（含 legacy）
python -c "from travelogue.cover_engine import resolve_style_id; print(resolve_style_id('card-br'))"

# 重渲染后浏览器看 data-cover-opening ∈ V6 十值
python -m travelogue render trips/<tripId>/trip.json
```

打开 [art-direction-v2 线框](./wireframes/cover-styles-v6-art-direction-v2-wireframe.html) 对照十款；Studio「排版」应十款 active 且带 blurb。

---

## 7. Art Direction Delta · 落地清单（2026-08-02）

| 项 | 文件 | 状态 |
|----|------|------|
| Delta 决策文档 | `docs/PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md` | ✅ v1.1 |
| Token + 十款 CSS pack | `templates/visual-journal/journal.css` | ✅ |
| `--cover-src` / `data-title` / focal / secondary | `templates/visual-journal/partials/cover-opening.hbs` | ✅ |
| 十款 active + profile | `travelogue/cover_engine/catalog.py` | ✅ |
| diptych 副图 + joint/fit | `joint.py` / `fit.py` / schema `coverSecondaryAssetId` | ✅ |
| band 安全区 → [0.58, 0.70] | catalog + golden/joint fixtures | ✅ |
| AC-CSV6AD-* | ACCEPTANCE § 增量 | ✅ |
| Studio 缩略图十款 | `preview-toolbar/sheet.css` | ✅ |
| 胶片颗粒 / 动效 | — | ⏭ P1 |