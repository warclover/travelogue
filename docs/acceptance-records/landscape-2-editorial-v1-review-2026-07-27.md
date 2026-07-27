# Landscape-2 Editorial V1 · 狗粮验收纪要

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-27 |
| 分支 | `feat/mixed-1l1p-landscape-2-editorial` |
| PRD | [PRD-LANDSCAPE-2-EDITORIAL-V1](../PRD-LANDSCAPE-2-EDITORIAL-V1.md) |
| 接线清单 | [mtso-local-dogfood-GUIDE §0](./mtso-local-dogfood-GUIDE.md) |

## 配置（本机 · 未提交）

- `layout.landscape_2_editorial.enabled=true`
- allowlist 含 overlap×2 + `screen-landscape-2-asymmetric-left`
- cohort 含 `demo-2025`

## demo-2025 结果（re-curate + render）

| patternId | 次数 |
|-----------|------|
| `screen-landscape-2` (fill) | 5 |
| `screen-landscape-2-overlap-tlbr` | 4 |
| `screen-landscape-2-overlap-bltr` | 3 |
| `screen-landscape-2-asymmetric-left` | 1 |
| `landscape2Picker` 探针屏 | 13 |

`journal-screens.css` 含 overlap absolute 与 asym grid；无 blur 边填。`validate` OK。

## AC

| ID | 结果 |
|----|------|
| AC-M2-01 默认 OFF 短横游程仍可 landscape-1 | ✅ `test_ac_m2_01_family_off_short_run_stays_landscape_1` |
| AC-M2-02 ON 可见 overlap/asym/fill | ✅ 狗粮 + `test_family_on_short_run_emits_landscape_2_pair` |
| AC-M2-03 schema | ✅（含 `overlap_tie` reason） |
| AC-M2-04 无 blur | ✅（CSS 纸色留白） |
| AC-M2-05 tie → overlap | ✅ `test_tie_prefers_overlap_not_fill` / `test_tie_rotates_overlap_diagonals` |
| AC-M2-06 家族 streak | ✅ `test_landscape_pair_family_streak` + post-check `landscape_pair_streak` |

## 补丁（同日）

- picker：tie 池仅留 overlap，消除 fill 权重压制
- `append_screen` 传入 `ctx.app_config.mosaic`，与 picker cohort 门一致
- `max_landscape_pair_streak` 进 rhythm / post-check

## Deferred

- `asymmetric-right`
