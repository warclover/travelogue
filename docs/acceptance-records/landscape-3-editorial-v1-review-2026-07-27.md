# Landscape-3 Editorial V1 · 狗粮验收纪要

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-27 |
| 分支 | `feat/triple-collage-l3e-mixed-1p2l` |
| PRD | [PRD-LANDSCAPE-3-EDITORIAL-V1](../PRD-LANDSCAPE-3-EDITORIAL-V1.md) |
| 接线清单 | [mtso-local-dogfood-GUIDE §0](./mtso-local-dogfood-GUIDE.md) |
| 配置样例 | [`docs/config-landscape-3-editorial-dogfood.example.yaml`](../config-landscape-3-editorial-dogfood.example.yaml) |

## 配置（本机 · 未提交）

- `layout.landscape_3_editorial.enabled=true`
- allowlist 含 `screen-landscape-3-asymmetric-left` / `…-right`
- cohort 含 `demo-2025`

## demo-2025 结果（`curate --layout web` + `render`）

| patternId | 次数 |
|-----------|------|
| `screen-landscape-3-asymmetric-left` | 1 |
| `screen-landscape-3-asymmetric-right` | 1 |
| `landscape3Picker` 探针屏 | 2（`reason=asym_tie`） |

三处对照一致；`assetVersion=ls3a9686369be0`。

## AC（自动化）

| ID | 结果 |
|----|------|
| AC-L3E-01 默认 OFF 三横仍 landscape-1 | ✅ `test_ac_l3e_01_family_off_short_run_stays_landscape_1` |
| AC-L3E-02 ON 可出 asym / fill | ✅ 狗粮 + `test_family_on_triple_run_emits_landscape_3` |
| AC-L3E-03 schema | ✅ `landscape3Picker` + asym patternId |
| AC-L3E-04 tie → asym（非 fill） | ✅ `test_tie_prefers_asym_not_fill` / `test_tie_rotates_asym_mirrors` |
| AC-L3E-05 triple 连续禁 | ✅ `test_landscape_triple_family_is_triple_kind` |

## 接线补丁（同分支）

- `build_chapters_from_plan` / `apply_layout_to_trip` / `layout` CLI 贯通 `trip` + `AppConfig`（漏传 ⇒ 恒 `fallback_fill`）
- `export --sync-journal` 后，CSS-primary（1.7fr / 固定 16:9）落在 `@journal-overlays`，避免下次 sync 冲掉
- slot-aspect：`docs/templates/slot-aspect/screen-landscape-3-asymmetric-*.md`

关联：[Mixed 1P2L 验收](./mixed-1p2l-v1-review-2026-07-27.md) · [Landscape-2](./landscape-2-editorial-v1-review-2026-07-27.md) · [P2VF](./p2vf-portrait-2-variant-family-v1-review-2026-07-27.md)
