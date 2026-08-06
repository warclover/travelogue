# MTSO · AC-11 / AC-12 收口记录（PR-D 转正）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-03 |
| **PRD** | [PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) |
| **依据** | [ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](../ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [mtso-local-dogfood-GUIDE.md §4](./mtso-local-dogfood-GUIDE.md) |
| **证据性质** | **开发者本机非正式回溯确认**（非独立第三方盲评）——如需更高置信度，可后补一次真正的打乱标签盲评；本记录先解决"代码已完成但无任何书面结论"的问题 |
| **状态** | ✅ **已收口 · 已转正 GA**（2026-08-03，`mosaic.selection_optimization.enabled` 默认改 `true`） |

> 使用方式：下面每一项我已经列好判定标准（抄自 GUIDE §2 对照场景 + §4 待手测清单），你只需要在「结果」列填 ✅ / ⚠️ / ❌ 并补一句观察，或者直接告诉我，我来帮你填。

---

## 1. AC-11 · 代表 trip 双阈值 compare

| # | 配置 | 期望 | 你测过吗 | 结果 | 观察 / trip id |
|---|------|------|:---:|:---:|------|
| A | `selection_optimization=true` + experiments 三元组 | 强竖 1P4L 窗出现 `1p4l-portrait-hero`；2P3L 窗出现 `2p3l-portrait-hero-rail`；硬拒时 reason=`mixed_routing:mixed_portrait_is_hero` | ✅ | ✅ | 见下方汇总 |
| B | `selection_optimization=true` + experiments OFF | 硬拒 detail 含 `dual_sku_gated`；MCS 失败后强竖 → `screen-portrait-1` rescue | ✅ | ✅ | 见下方汇总 |
| C | `selection_optimization=false` | 与仓库默认路径一致，无 `mixed_routing` 硬拒 | ✅ | ✅ | 见下方汇总 |
| D | 恰 3P+2L，辅竖锐度领先 | `screen-mosaic-5-3p2l-portrait-hero-quad` | ✅ | ✅ | 见下方汇总 |
| E | 恰 3P+2L，横图锐度领先 | `screen-mosaic-5-3p2l-portrait-hero-lp-stack` | ✅ | ✅ | 见下方汇总 |
| F | 2P+3L | 不应出 3P2L，应走 `2p3l-portrait-hero-rail` | ✅ | ✅ | 见下方汇总 |

**测试范围与汇总观察（开发者原话，2026-08-03）**：
- 代表 trip（每次迭代固定用这三个，覆盖三种典型场景）：
  - `demo-d6697c8dca` —「王丹昙华林半日游」
  - `demo-2025` —「2025东澳岛一日游」
  - `demo-49cbe46479` —「张智慧仲夏日漫游斯里兰卡」
- A~F 六个场景**都测过**；但**未逐项精确核对单项判定标准**（例如未逐条肉眼比对 reason 字符串是否严格等于 `mixed_routing:mixed_portrait_is_hero`），是"跑过 + 看总体输出"的粗颗粒度回归，不是逐条断言级的人工核对。
- **总体结论**：三个代表 trip 多轮迭代下，输出效果满意，未观察到明显异常/退化。
- ⚠️ 备注：上表"结果"列的 ✅ 反映的是"整体满意、无异常"，不代表 A~F 每一条的具体断言都被逐项核对过；如需更高置信度，建议后续挑一个 trip 做一次逐场景手工复核（预计 15-20 分钟）。

## 2. AC-12 · 几何截图签核

| 项 | 判定标准 | 结果 | 截图路径 |
|----|----------|:---:|----------|
| 2P3L 三列几何 | 辅竖满高，AR≈0.27，肉眼可读不糊 | ⚠️ 未留存 | 无 |
| 3P2L 主槽几何 | 主槽 area=0.55，displayAspect≈0.978（**不是** cols=12 的 AR≈1.07 假竖主） | ⚠️ 未留存 | 无 |

**说明（开发者原话，2026-08-03）**：没有留存截图；算法更新后 2P3L / 3P2L 这两种拼图组合的出现概率很低——大部分拼图落在 3 张和 4 张照片区间，5 张及以上组合出现概率很低。因此这两条几何判定标准目前是**理论核对**（未做像素级实拍复核），实际风险敞口较小（触发频率低），但也意味着"确认几何正确"这件事本身还没有被真实验证过。

**处理建议（供你确认，见第 4 节结论）**：由于该组合天然低频，不建议为此单独阻塞转正；可标记为"已知未验证角落，留待生产中偶遇 5 张+ 拼图时再回归确认"，而不强行现在补跑渲染截图。

## 3. 自动化基线（可直接跑，不需要你回忆）

```powershell
python -m pytest tests/unit/layout_engine/test_mtso_pr_d.py tests/unit/layout_engine/test_mtso_pr_c2_skus.py tests/unit/layout_engine/test_mosaic_5_3p2l.py tests/unit/layout_engine/test_tri_col_equal_family.py -q
```

- [x] 已跑，全绿 —— **2026-08-03 由 Agent 代跑**：`31 passed in 5.47s`，0 failed / 0 error / 0 skipped

## 4. 结论（填完上面再回填这里）

| 项 | 勾选 | 依据 |
|----|------|------|
| AC-11 通过 | ✅ | A~F 六场景均测过，三个代表 trip 多轮迭代，总体输出满意；未逐项断言级核对（已在 §1 注明），置信度为"高但非满分" |
| AC-12 通过 | ⚠️ 有条件通过 | 判定标准本身合理，但因 2P3L/3P2L 天然低频（多数拼图落在 3~4 张），未做实拍复核；建议标记"已知未验证角落"而非阻塞项 |
| **转正**：`mosaic.selection_optimization.enabled` 默认改 `true` | ✅ 建议 | AC-11 高置信通过 + 自动化基线 31/31 全绿 + AC-12 的未验证部分属低频角落，风险可接受 |
| 或 **归档**：保持默认 `false`，本 PRD 标记 Conditional Closed | ☐ | — |

> 以上为 Agent 基于你提供的信息给出的**建议判定**，最终是否转正请你确认（见对话中的确认问题）。

**签名**：开发者口头确认 + Agent 代填　日期：2026-08-03

---

## 5. 转正后需要同步的文件（勾选后我来批量改）

- [x] `config.yaml.example` — `mosaic.selection_optimization.enabled: false → true`
- [x] `docs/IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md` 状态行 — "PR-D 进行中" → "已转正 GA"
- [x] `docs/ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md` — 勾 AC-11/12
- [x] `docs/DOC-STATUS.md` — MTSO 状态行更新
- [x] `docs/README.md` — MTSO 一行状态更新

> 以上 5 处已于 2026-08-03 由 Agent 同步完成。
