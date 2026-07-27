# Mixed 1P2L V1 · 狗粮验收纪要

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-27 |
| 分支 | `feat/triple-collage-l3e-mixed-1p2l` |
| PRD | [PRD-MIXED-1P2L-V1](../PRD-MIXED-1P2L-V1.md) |
| 接线清单 | [mtso-local-dogfood-GUIDE §0](./mtso-local-dogfood-GUIDE.md) |
| 配置样例 | [`docs/config-mixed-1p2l-dogfood.example.yaml`](../config-mixed-1p2l-dogfood.example.yaml) |

## 配置（本机 · 未提交）

- `layout.mixed_1p2l.enabled=true`
- allowlist 含 `screen-landscape-2-portrait-1`
- cohort 含 `demo-8261bd0a55`（及 demo 系列）
- 狗粮时暂关 `mixed_1l1p`，避免 1L1P 抢窗

## demo-8261bd0a55 结果（`layout --layout web --web-layout screens` + `render`）

| patternId | 次数 |
|-----------|------|
| `screen-portrait-1-landscape-2` (fill) | 1 |
| `screen-landscape-2-portrait-1` (镜像) | 1 |
| `mixed1p2lPicker` | 2（`rotate`） |

三处对照：config · `trip.json` · `index.html` `data-pattern` 一致。

## AC

| ID | 结果 |
|----|------|
| AC-M1P2L-01 OFF → 仍 p1l2 | ✅ `test_emit_off_stays_p1l2` |
| AC-M1P2L-02 ON → 可出镜像 | ✅ 狗粮 + `test_emit_on_can_mirror` / `test_dogfood_window_try_mixed_emits_mirror` |
| AC-M1P2L-03 schema | ✅ |
| AC-M1P2L-04 竖图含人仍拒 | ✅ `test_hard_gate_blocks_person_portrait` |

## 补丁（同日）

- picker：tie 时等权 base，避免 fill `base_weight` 永久压制镜像轮换
- CSS：`2landscape-right-portrait` 槽位 height 强化与 p1l2 fill 对齐；LTE sync + overlays 保全手写合同

关联：[Landscape-3 Editorial 验收](./landscape-3-editorial-v1-review-2026-07-27.md) · [Mixed 1L1P](./mixed-1l1p-v1-review-2026-07-27.md)
