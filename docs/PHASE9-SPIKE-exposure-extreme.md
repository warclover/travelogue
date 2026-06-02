# Phase 9 · Spike · exposure_extreme（M30-2e）

| 属性 | 内容 |
|------|------|
| **状态** | **Deferred** · W2+ 评估 |
| **PRD** | [PRD-PHASE9-A §3.1 R-P9-03](./PRD-PHASE9-A-quality-gate-algorithm.md) |
| **更新** | 2026-06-02 |

---

## 结论

**W1 不实现**（D-P9-12）。本 spike 记录后续评估要点，避免重复讨论。

## 目标

Pass 1 硬剔除全黑 / 全白帧（`excludeReason: exposure_extreme`），减少无信息密度图片进入 curate。

## 候选实现

1. **OpenCV 直方图**：均值亮度 &lt; 5 或 &gt; 250（8-bit）且低方差 → 标记极端曝光。
2. **采样成本**：每张 ~1–3ms CPU；250 张 +5–10s，可接受但 W1 已用 sharpness + mediaClass 覆盖大部分坏图。
3. **误杀风险**：夜景 / 雪景高光可能误触；需 featured 豁免 + 保守阈值 + 地板联动。

## 与现网关系

- `CULL_EXCLUDE_REASONS` 已预留 `exposure_extreme`。
- Pass 1 未调用；无 schema 变更需求。

## 建议触发条件（W2+）

- mao/maomi golden 仍出现明显全黑/全白进屏案例；
- 或 Phase 10 food grid 需要更干净的 mundane 池。

## 验收草案

- pytest：合成全黑 JPG → `excludeReason=exposure_extreme`；featured 豁免。
- 保留率：同 fixture 相对 P0 rules **−0% ~ −1%**。
