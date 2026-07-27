# PRD · Landscape-2 Editorial（双横编辑向）V1

| 属性 | 内容 |
|------|------|
| 状态 | M2 试点 |
| 关联 | [Mixed 1L1P](./PRD-MIXED-1L1P-V1.md) · [P2VF](./PRD-PORTRAIT-2-VARIANT-FAMILY-V1.md) · [MTSO §0](./acceptance-records/mtso-local-dogfood-GUIDE.md) |
| 家族 | `landscape-2-editorial` |

## 1. 目标

在 GA 基线 `screen-landscape-2`（上下等权 stack）之上，增加对角叠压与非对称缩放变体，服务「两张横图有编辑关系」的窗口。

## 2. 轮换集

| patternId | variantRole | status |
|-----------|-------------|--------|
| `screen-landscape-2` | fill | ga（不改视觉合同） |
| `screen-landscape-2-overlap-tlbr` | overlap-tlbr | experimental |
| `screen-landscape-2-overlap-bltr` | overlap-bltr | experimental |
| `screen-landscape-2-asymmetric-left` | asymmetric-left | experimental |

**Deferred：** `asymmetric-right`（草图未给出）。

## 3. 叠压约定

- 屏级 `position: relative`；两槽 `absolute` + **贴对角** inset（约 50%×54%，角距约 3%）+ `z-index`（slot1 前景）
- 重叠宜轻：槽位向 TL/BR（或 BL/TR）拉开并略缩小，避免大面积盖住
- 禁止 blur 假第三图；纸色留白为设计
- 两槽 `fit: cover`

## 4. Picker

- 双开关：`layout.landscape_2_editorial.enabled` ∧ `template_experiments` 三元组
- OFF / 不可见实验 → emit fill `screen-landscape-2`（当本路径决定成对时）
- 强弱接近（tie）→ **仅** overlap 两对角轮换（`reason=overlap_tie`；不得因 fill `base_weight` 更高而落 stack）
- 左槽明显更强 → `asymmetric-left`（左大右小；时间序不换槽）
- 右槽更强 → fill / overlap（无 asym-right；V1 deferred）
- 硬路径（person-pair 等）不进本 picker
- 发射点：landscape 短游程在家族 ON 时优先成对（2 张），替代「≤3 一律 landscape-1」
- 节奏：`LANDSCAPE_PAIR_PATTERNS` 家族 streak 默认 ≤2（`max_landscape_pair_streak`）；触顶回退 landscape-1

## 5. 配置样例

见 [`docs/config-landscape-2-editorial-dogfood.example.yaml`](./config-landscape-2-editorial-dogfood.example.yaml)。

## 6. AC（摘要）

| ID | 断言 |
|----|------|
| AC-M2-01 | 默认 OFF → 行为与改前一致（短横游程仍可 landscape-1） |
| AC-M2-02 | ON + cohort → 可出现 overlap / asym；fill 仍可 |
| AC-M2-03 | schema 含三实验 id + `landscape2Picker` |
| AC-M2-04 | 叠压屏无 blur 边填 |
| AC-M2-05 | tie → overlap（非 fill）；对角可经 recent 轮换 |
| AC-M2-06 | 家族连续 > `max_landscape_pair_streak` 不可再 emit pair |
