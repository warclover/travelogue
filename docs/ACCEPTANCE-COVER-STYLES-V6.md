# 封面多样式 V6 · 验收记录

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) **v1.3.0** |
| **实施清单** | [IMPLEMENTATION-COVER-STYLES-V6.md](./IMPLEMENTATION-COVER-STYLES-V6.md) |
| **视觉真相源** | [cover-styles-v6-hi-fi-adefg.html](./wireframes/cover-styles-v6-hi-fi-adefg.html) |
| **更新日期** | 2026-07-10 |
| **门禁结论** | **M1 + M2 代码门禁通过**；P0 缺口补齐（角标 / Dock / 黄金集 / fit 灰字 / V6 Playwright 最小套件） |

---

## 1. 实施范围

| 阶段 | 内容 | 状态 |
|------|------|------|
| M1 | Cover Style Engine Registry + resolve/legacy | ✅ |
| M1 | 五款 CSS + §4.7 token + 窄屏 CSS 回落 veil | ✅（静态 CSS AC）；Playwright 视觉待补 |
| M1 | Schema V6∪V5；写入仅 assignable | ✅ |
| M1 | Studio 五选一读引擎 + blurb | ✅ |
| M1 | create 占位 `veil-footer` | ✅ |
| M2 | 联合选型默认开 + `coverJointLocked` | ✅ |
| M2 | `repick_cover_for_style` / 换版式默认重荐 | ✅ |
| M2 | Toast / 老 V5 说明 / telemetry | ✅（代码）；E2E Toast 待补 |
| P0.5 | 封面实验室完整 UI | ⏭ 非封板条件 |
| — | 封底改版 | ❌ 不在本 PRD（仅不回归） |
| — | Admin 后台 | ❌ 不在本 PRD P0 |

---

## 2. 自动化验收

| 套件 | 命令 | 结果 |
|------|------|------|
| V6 Engine + Joint | 见 IMPLEMENTATION §5 | ✅ **见下** |
| 封底不回归 | `tests/unit/domain/test_cover_closing.py` | ✅ 既有套件 |

```bash
python -m pytest \
  tests/unit/curation/test_cover_styles_v6.py \
  tests/unit/curation/test_cover_styles_v6_joint.py \
  tests/unit/curation/test_cover_styles_v6_golden.py \
  tests/unit/domain/test_copy_patch.py \
  tests/unit/curation/test_cover_by_layout.py \
  tests/unit/domain/test_cover_closing.py \
  tests/unit/trip/test_asset_version.py \
  tests/unit/domain/test_guardrails_copy_patch.py \
  -q -m "not e2e and not playwright_serial"
```

Playwright 最小套件：

```bash
python -m pytest tests/unit/curation/test_cover_styles_v6_playwright.py -q
```

---

## 3. AC 覆盖映射（PRD §10）

### 10.1 替代与兼容

| AC ID | 状态 | 自动化 / 证据 |
|-------|------|----------------|
| **AC-CSV6-01** | ✅ | `test_create_trip_placeholder_veil_footer` |
| **AC-CSV6-02** | ✅ | `test_studio_style_options_active_only_with_blurb` + entry `coverStyleOptions` |
| **AC-CSV6-03** | ✅ | `test_legacy_map_table` / `test_resolve_style_id_legacy_and_default` |
| **AC-CSV6-04** | ✅ | resolve → `folio-overlap`；宽屏无溢出见 `test_cover_styles_v6_wide_no_overflow` |
| **AC-CSV6-05** | ✅ | `test_schema_accepts_v5_and_v6_cover_opening_style` |

### 10.2 五款皮肤

| AC ID | 状态 | 自动化 / 证据 |
|-------|------|----------------|
| **AC-CSV6-10～14** | ✅ | CSS + `test_cover_styles_v6_wide_no_overflow`；对照 hi-fi 人工 |
| **AC-CSV6-12** | ✅ token | `--cover-band-center: 72%` + §4.7 收编 |
| **AC-CSV6-15** | ✅ | folio 无 hook 去 accent：`test_cover_styles_v6_folio_no_hook_hides_accent` |
| **AC-CSV6-16** | ⏭ | 对比度人工 / 后续 Playwright |
| **AC-CSV6-17** | ✅ | 窄屏回落：`test_cover_styles_v6_narrow_presents_as_veil` |
| **AC-CSV6-18** | ✅ | Dock 安全区：`test_cover_styles_v6_dock_safe_zone` |

### 10.3 联合选型与锁定

| AC ID | 状态 | 自动化 / 证据 |
|-------|------|----------------|
| **AC-CSV6-20** | ✅ | `test_band_cut_not_optimal_when_focal_in_strip` |
| **AC-CSV6-21** | ✅ | `test_cameo_prefers_center_subject` |
| **AC-CSV6-22** | ✅ | `test_pick_cover_style_and_asset_returns_assignable` + apply |
| **AC-CSV6-23** | ✅ | `test_hash_fallback_pick_source` |
| **AC-CSV6-24** | ✅ | `test_sync_trip_covers_respects_lock` |
| **AC-CSV6-25** | ✅ | `test_repick_cover_for_style_keeps_lock` |

### 10.4 使用说明与沟通

| AC ID | 状态 | 自动化 / 证据 |
|-------|------|----------------|
| **AC-CSV6-30** | ✅ | `test_studio_style_options_active_only_with_blurb` |
| **AC-CSV6-31** | ✅ 代码；⏭ E2E | `shell.js` §7.2 文案 + localStorage 一次 |
| **AC-CSV6-33** | ✅ 代码；⏭ E2E | `features.js` 默认 `repickCover`；勾选可 keep |
| **AC-CSV6-34** | ✅ 代码；⏭ E2E | `coverLegacyMapped` + §7.4 Toast |

### 10.5 封底

| AC ID | 状态 | 自动化 / 证据 |
|-------|------|----------------|
| **AC-CSV6-32** | ✅ | `tests/unit/domain/test_cover_closing.py` |

### 10.6 Cover Style Engine

| AC ID | 状态 | 自动化 / 证据 |
|-------|------|----------------|
| **AC-CSV6-40** | ✅ | assignable ≡ studio options ≡ joint `list_assignable_styles` |
| **AC-CSV6-41** | ✅ | `test_set_style_status_retired_drops_assignable` |
| **AC-CSV6-42** | ✅ | `test_no_hardcoded_v6_tuple_outside_engine` |
| **AC-CSV6-43** | ✅ | `test_legacy_map_table` |
| **AC-CSV6-44** | ✅ | `test_preview_matrix_each_active_has_fixture` |
| **AC-CSV6-45** | ✅ | CSE-01～12/16～17；黄金集 `test_cover_styles_v6_golden.py`；CSE-13/14 非本 PRD |

---

## 4. 人工走查清单（封板前）

- [ ] 高保真 A/D/E/F/G 与实渲染五款对照（≥1024px）
- [ ] `band-cut` 题带中线目测 ∈ 70%–74%
- [ ] 窄屏 &lt;1024px：任意 style attribute 不变，呈现雾底
- [ ] Icon Dock 五款可点
- [ ] 真实 trip ≥20 本联合结果抽检（PRD §6.3.1）
- [ ] Studio：联合后 Toast 一次；老 V5 trip 说明一次；换版式默认重荐
- [ ] 封底在 Web+epilogue 条件下仍可用（不回归）

## 5. 已知限制

- V5 布局 Playwright 已 skip；V6 最小套件见 `test_cover_styles_v6_playwright.py`
- folio 竖排跑题为 CSS 近似（一块 DOM 约束下）
- 换版式「保留封面图」为勾选次要路径；低 fit 时灰字依赖 `fitBelowThreshold`
- ≥20 本真实 trip 联合抽检仍为人工封板项
- 完整 Admin / 实验室 UI / 封底改版不在本验收范围

## 6. 样例验证建议

```bash
python -c "from travelogue.cover_engine import resolve_style_id, studio_style_options; print(resolve_style_id('card-br')); print([o['id'] for o in studio_style_options()])"
python -m travelogue render trips/<tripId>/trip.json
```

浏览器打开 Studio 预览：`data-cover-opening` ∈ V6 五值；排版 Sheet 五款 + blurb。
