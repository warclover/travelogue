# PRD · Mixed 1L1P（竖+横双图混排）V1

| 属性 | 内容 |
|------|------|
| 状态 | M1 试点 |
| 关联 | [P2VF](./PRD-PORTRAIT-2-VARIANT-FAMILY-V1.md) · [MTSO 狗粮 §0](./acceptance-records/mtso-local-dogfood-GUIDE.md) |
| 家族 | `mixed-1l1p` |

## 1. 目标

补齐 **1 竖 + 1 横** 双图屏（现网仅有三图 `screen-portrait-1-landscape-2`）。左右镜像各一独立 `patternId`，不引入 flip 标志。

## 2. 轮换集

| patternId | 布局 | status |
|-----------|------|--------|
| `screen-landscape-1-portrait-1` | 左横右竖 | experimental |
| `screen-portrait-1-landscape-1` | 左竖右横 | experimental |

无 GA fill：关门时 **不强制成屏**，回退拆成 `screen-portrait-1` + `screen-landscape-1`。

## 3. 几何（16:9 · CSS-primary）

角色固定：竖图进 portrait 槽，横图进 landscape 槽；仅左右镜像变化。

- **竖槽**：与舞台**等高**；列宽 ≈ `42.1875%`（16:9 舞台上的 3:4 开孔）
- **横槽**：占**剩余宽度**（`1fr`），与舞台**等高**，`object-fit: cover`（不再 3:2 居中）
- **间距**：小 `column-gap` + 极窄左右内边距；opt-out 通用 contain-collapse
- **L\|P / P\|L**：列顺序镜像，规则相同
- **SSOT**：几何写在 `journal-screens-overlays.css`（`export --sync-journal` 不会冲掉）

## 4. 准入与选型

- 窗口恰 1P+1L，且 `takenAt` 链满足 `mixed_proximity_seconds`
- 双开关：`layout.mixed_1l1p.enabled` ∧ `mosaic.template_experiments`（enabled + allowlist + cohort 含 tripId）
- 强弱：竖更强 → 优先 P\|L；横更强 → 优先 L\|P；平局 → `recent_window` 轮换
- MCS lifecycle **不**自动解锁；可见性仅 picker 判定
- `tripId` 必须贯通 attach→picker（见 MTSO §0）

## 5. 配置样例

见 [`docs/config-mixed-1l1p-dogfood.example.yaml`](./config-mixed-1l1p-dogfood.example.yaml)。

## 6. AC（摘要）

| ID | 断言 |
|----|------|
| AC-M1-01 | 双开关 OFF → 无新 patternId |
| AC-M1-02 | cohort 空 / trip 不在列表 → 不可见 |
| AC-M1-03 | 1P+1L 近时窗 → 命中镜像之一；`data-pattern` 与 trip.json 一致 |
| AC-M1-04 | schema 含两 id + `mixed1l1pPicker` |
| AC-M1-05 | 平局 → `recent_window` 轮换 L\|P / P\|L |

## 7. Deferred

- 人物硬路径专属混排（V1 不挡人，但也不做 person-pair 式硬 emit）
- 带文案 kicker 的编辑向变体
