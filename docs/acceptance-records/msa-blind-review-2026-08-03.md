# MSA · 盲评记录（AC-09）· 2026-08-03

| 属性 | 内容 |
|------|------|
| **行程 / 语料** | 三个开发者代表 trip（长期迭代回归用）：`demo-d6697c8dca`（王丹昙华林半日游）· `demo-2025`（2025东澳岛一日游）· `demo-49cbe46479`（张智慧仲夏日漫游斯里兰卡） |
| **日期** | 2026-08-03 |
| **评分人** | 开发者（本人），Agent 代打乱标签盲评（评分人不知道 A/B 对应 on/off，Agent 揭晓前不透露） |
| **MSA 配置** | on: `slot_adaptation.enabled=true` · off: `false`（其余 mosaic 配置不变；用本机 `config.yaml` 实际值） |
| **关联 GUIDE** | [msa-local-dogfood-GUIDE.md](./msa-local-dogfood-GUIDE.md) |
| **对照单位** | **整章（chapter）**而非单屏——见"方法说明" |

> **方法说明（重要偏差）**：GUIDE 原设计是"同屏同资产序"对照单屏截图。实测发现 `render` 命令不会重新求解 MSA（几何在 `curate`/`layout` 阶段persist，`render` 只读复用，符合 D-MSA-02 设计）；改用 `python -m travelogue layout <trip.json> --layout auto --web-layout screens --render` 重新求解后才有真实差异。但同时发现 **on/off 切换会改变同一 trip 的 items blocks 总数**（例：`demo-2025` 全篇 24→17），即窗口尺寸选型（MCS）本身随 MSA 开关变化，导致同一 chapter 在 on/off 下包含的屏数不同（4 vs 2 ~ 5 vs 4 ~ 12 vs 13）。因此本次对照单位从"单屏"改为"整章"，尽量保留同一批照片可比。

## 成对结果（打乱标签，A/B 已揭晓）

| 画像 | 对编号 | off | on | 评分人选择 | 主体完整性/杂志感（合并判） | 备注 |
|------|--------|-----|-----|:---:|:---:|------|
| P1（混排，81张 3:2+4:3） | P1-A/P1-B | A | B | **B（on）** | on 优 | "差别很小，B 胜在无空白，排版与 A 一致" |
| P2（重混排，129张多比例） | P2-A/P2-B | A | B | **A（off）** | off 优 | "A 内容更多；B 与 A 上半部分排版/内容一致，缺下半部分" —— 见下方"pacing 副作用" |
| P3（近全单反，223张多 3:2） | P3-A/P3-B | A | B | **A（off）**（首次因截图懒加载 bug 误判为"都有空白"，修复重截后确认判 A） | off 优 | 修复懒加载 artifact 后确认 |

**汇总：3 组中 2 组倾向 off，1 组倾向 on。未达到 AC-09 通过线（On ≥ Off）。**

## 新发现：MSA 开关会连带改变 pacing（超出 D-MSA-08 设计意图）

- `demo-2025` 全篇 items blocks：off=24 → on=17（同一 chapter 内屏数 4→2）。
- 推测机制：PR-B 评分项（`aspect_fit` / `crop_risk_penalty` / `whitespace_penalty`，T-MSA-13）反馈进 MCS 候选打分，间接改变了窗口尺寸（5/6 张窗 vs 拆成多个 3/2 张窗）的选型倾向，从而改变了同一天照片落入哪个 chapter/屏的 pacing——这不是 MSA PRD 声明的"仅改几何、不改 lifecycle/experiments"范围内的行为。
- **建议**：作为独立风险项跟踪，不与 AC-09 通过/不通过绑定（AC-09 本身已经不通过），但应在下一轮 MSA 复测前排查评分反馈是否应该对 MCS 候选选型可见。

## 红线检查

| 检查 | Off | On |
|------|-----|-----|
| 朝向硬门回退（竖进宽槽等） | 无 | 无 |
| dense / 相邻 / large 红线 | 无 | 无 |
| 舞台 AR 被改（禁止） | 无 | 无 |
| pacing / 分章漂移（非既定红线，但本次新记录） | — | **有**（见上） |

## 结论

| 项 | 勾选 |
|----|------|
| AC-09 通过（On ≥ Off 主体完整性；红线无回退） | ☐ |
| **不通过 · 保持默认 off** | ✅ |
| 截图附件路径 | `docs/acceptance-records/attachments/msa-blind-2026-08-03/`（P1-A/B、P2-A/B、P3-A/B，整章截图） |

**签名**：开发者盲评 + Agent 代记录　日期：2026-08-03

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-08-03 | 首次实册盲评，3 组 2/3 倾向 off，AC-09 判定不通过；记录 pacing 副作用新发现 |
