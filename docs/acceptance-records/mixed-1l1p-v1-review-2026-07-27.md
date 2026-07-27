# Mixed 1L1P V1 · 狗粮验收纪要

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-27 |
| 分支 | `feat/mixed-1l1p-landscape-2-editorial` |
| PRD | [PRD-MIXED-1L1P-V1](../PRD-MIXED-1L1P-V1.md) |
| 接线清单 | [mtso-local-dogfood-GUIDE §0](./mtso-local-dogfood-GUIDE.md) |

## 配置（本机 · 未提交）

- `layout.mixed_1l1p.enabled=true`
- `mosaic.template_experiments` allowlist 含：
  - `screen-landscape-1-portrait-1`
  - `screen-portrait-1-landscape-1`
- `cohort_trip_ids` 含 `demo-2025`

## demo-2025 结果（re-curate + render）

| patternId | 次数 |
|-----------|------|
| `screen-landscape-1-portrait-1` | 9 |
| `screen-portrait-1-landscape-1` | 5 |
| `mixed1l1pPicker` 探针屏 | 14 |

三处对照：config ON · `trip.json` patternId · `index.html` `data-pattern` 一致；`validate` OK。

## AC

| ID | 结果 |
|----|------|
| AC-M1-01 双开关 OFF 不发射 | ✅ `test_picker_off_returns_none` |
| AC-M1-02 cohort 空不可见 | ✅ `test_empty_cohort_invisible` |
| AC-M1-03 狗粮命中镜像 | ✅ |
| AC-M1-04 schema | ✅ |
| 平局轮换 | ✅ `test_tie_rotates_mirrors_via_recent_window` |

## 硬路径说明

本家族无 person-pair 硬 emit；关门回退拆单图。与 P2VF fill 分流验收正交。

关联：[Landscape-2 Editorial 验收](./landscape-2-editorial-v1-review-2026-07-27.md) · [P2VF](../PRD-PORTRAIT-2-VARIANT-FAMILY-V1.md)
