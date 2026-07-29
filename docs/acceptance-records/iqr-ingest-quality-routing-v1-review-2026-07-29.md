# PRD-INGEST-QUALITY-ROUTING-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-INGEST-QUALITY-ROUTING-V1.md](../PRD-INGEST-QUALITY-ROUTING-V1.md) |
| **关联** | [PRD-PHOTO-CULL-USER-TOGGLE.md](../PRD-PHOTO-CULL-USER-TOGGLE.md) · [RESEARCH-PHOTO-QUALITY-SELECTION-SURVEY-2026-07-28.md](../RESEARCH-PHOTO-QUALITY-SELECTION-SURVEY-2026-07-28.md) · Import Wizard `photoKeepMode`（现网 P9-F3） |
| **评审版本** | **v0.1.0 Draft** |
| **日期** | 2026-07-29 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff W0（开关/字段骨架）**；**W1 合码前须消化 BLK 回写** |
| **编码** | W0 可开；**主路径三卡 UI / 自动 messy 不得按 v0.1.0 原文落地**，须先冻结合并矩阵与门时序 |
| **参评席位** | 典型用户代表 · 架构 · 算法 · 产品 · UI/UX |
| **评审方式** | 分席只读（PRD 全文 + 对照现网 Import Sheet / cull 配置 / P9-F1） |
| **本纪要状态** | **第一轮结案** · Must-Fix 已回写 **PRD v0.2.0**（2026-07-29） |

---

## 1. 总评（一句话）

> **三分法与「不选 → 推荐 / 失败 → typical」方向正确，对准「选片天花板」根因；阻塞在：未对齐现网已落地的 `photoKeepMode` 三档、messy 与 `keep_ratio_floor` 冲突、Pass C 软/硬语义未钉死、自动进 messy 伤 FTUE、确认门时序含糊。消化 BLK 后可 Kickoff；默认 `quality_routing.enabled=true` 须另过发布门。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **典型用户** | Conditional Go | 不选就推荐很香；「已是精选」易误点、n≥150 易误推 messy |
| **架构** | Conditional Go | 策略正交合理；必须先定与 P9-F3 权威源，禁双三选一 |
| **算法** | Conditional Go | 可 profile 化现网 Pass；Pass C / floor / AC 量化须先冻 |
| **产品** | Conditional Go | 定位诚实；curated 文案与 P9-F1 边界、发布门禁、FTUE 须补 |
| **UI/UX** | Conditional Go | 推荐默认与确认门对；须合并现网「调整照片处理」抽屉 |

**汇总**：**五席一致 Conditional Go**。

---

## 3. 全场共识

1. **问题诊断成立**：惊艳 vs 凌乱主要差在输入选片，不在版式。  
2. **三模式合同值得做**：`curated` / `typical` / `messy`；默认安全落点 **`typical`**。  
3. **用户可不选**是正确产品决定；推断失败不得进 `messy`。  
4. **现网已不是 P9-F1 二元勾选**，而是 Import Wizard **`photoKeepMode`：`recommended` / `keep_bursts` / `keep_all`**——附录 A 必须重写。  
5. **主路径只允许一套「照片怎么处理」控件**；禁止 IQR 三卡与照片处理抽屉双三选一并存。  
6. **`messy` 要砍得动**，必须显式下调/关闭 `keep_ratio_floor`（现网默认 ~0.90 会否决强精简）。  
7. **对外禁「放弃懒用户」**；`curated` 禁绝对「全部进排版」（低清/去重仍可减张）。  
8. **W1 建议可砍自动推断**（显式三模式 + 默认 typical），推断放 W2 且仍受「勿无确认落 messy」约束。

---

## 4. Must-Fix（BLK · W1 合码前）

| ID | 议题 | 来源席 | 冻结要求（一字面） |
|----|------|--------|-------------------|
| **BLK-01** | 与 P9-F3 合并 | 架构 / UI | 定权威：**(A) IQR 取代 `photoKeepMode` 为唯一枚举**，或 **(B) IQR 仅作 intensity、UI 仍挂 keep 档之下**。禁止平行双三选一。附录 A 覆盖 `recommended`/`keep_bursts`/`keep_all` ↔ IQR（+ 可选连拍进阶）。 |
| **BLK-02** | 意图单源 / 派生表 | 架构 | 唯一 `resolve_ingest_quality_policy(trip,cfg)` → `{skip_cull, cull_overlay, skip_low_res, keep_near_dupes, mode, sources}`；禁止 FE 本地多源推导。 |
| **BLK-03** | messy 确认门时序 | 架构 / UI / 用户 | **二选一钉死**：**T0 提交前确认**（推荐，probe 估 M/N），**或** job `awaiting_iqr_confirm`+resume。禁止「curate 前或 FirstSuccess 前」含糊「或」。禁止 FirstSuccess 后再弹精简门。 |
| **BLK-04** | Pass C 软/硬 | 算法 | **typical = soft_demote only**（不进封面/hero/moment，可仍 layoutEligible）；**messy = hard_cull（top% 外）**。禁止「软淘汰或降权」混写。 |
| **BLK-05** | keep_ratio_floor | 算法 / 架构 | messy：**关闭 floor 或改为服从 `keep_top_pct`**，另用 `min_layout_eligible` 护栏。否则 AC「显著变薄」不可测。 |
| **BLK-06** | ★ / featured | 算法 | V1：`★ ≡ userTier=featured`；百分位分母排除 ★；Pass C 不出局（Pass A 豁免沿用现网）。 |
| **BLK-07** | 自动 messy / FTUE | 产品 / 用户 | **置信不足或未显式确认，不得因「不改选项」生效 messy**（可推荐徽标，生效须确认或显式点选）。仅张数不得推 messy。 |
| **BLK-08** | curated 诚实口径 | 产品 / 用户 / 架构 | 继承 P9-F1：仅跳质量 cull；dedupe/低清门是否跳与 `keep_all` 对齐并写死。文案禁「全部进排版」绝对表述；须 N/M 诚实。 |
| **BLK-09** | curated 误点 | 用户 | 副文案写清代价「几乎每张都进册」；或点选短确认。 |
| **BLK-10** | AC 量化 | 算法 / 产品 | fixture 写死保留率区间；替换「显著低于」「故事仍在」。发布门：`enabled=true` 绑三模式狗粮 + FTUE 零改点 typical 路径无必过 Modal。 |
| **BLK-11** | 过少护栏 UI | UI | `min_layout_eligible` 触发独立门态（主 CTA→改 typical）；FE 任务补齐。 |
| **BLK-12** | W1 前拆文 | 全席 | **W1 merge 前**拆 `ACCEPTANCE` + `IMPLEMENTATION`（含合并矩阵与派生表）。 |

---

## 5. Should（不挡 W0，挡默认开）

| ID | 摘要 |
|----|------|
| **SH-01** | 区标题改为结果导向：「这批照片希望怎么处理？」 |
| **SH-02** | messy 标题去「较杂」评判感 →「未整理的大量连拍 / 需要强力精简」 |
| **SH-03** | 推断阈值全部数值化（burst/tech 的 low/high）；path_hints 仅 mid confidence |
| **SH-04** | typical 百分位在 Pass A/B **存活集**上算 |
| **SH-05** | 会话不跨会话默认记住 messy/curated（对齐 P9-F1） |
| **SH-06** | 窄屏三卡竖排 + sticky CTA；「恢复推荐」FE-IQR-13 |
| **SH-07** | 与 HIT / 精选双文件夹边界表（≤5 行）写入 PRD |
| **SH-08** | W1 可不含自动推断；W2 再上推荐徽标（仍受 BLK-07） |

---

## 6. 建议冻结的合并矩阵（供 Kickoff 拍板）

| 用户目标 | IQR（建议权威） | 现网 `photoKeepMode` | 备注 |
|----------|-----------------|----------------------|------|
| 已筛好，别再丢 | `curated` | ≈ `keep_all` | 对齐是否跳低清门 |
| 大多数手机册 | `typical`（默认） | ≈ `recommended` | 「保留连拍」→ typical 下**进阶**开关，不占主卡 |
| 乱册要砍薄 | `messy`（新） | 无对应 | 不可与 `keep_bursts` 混谈 |

**推荐 UI**：confirm 区一套主三选一；原「调整照片处理」抽屉收敛为 **IQR 派生摘要 + 进阶（连拍）**。

---

## 7. 算法默认阈值修订建议（摘录）

| 键 | v0.1.0 | 评审建议 |
|----|--------|----------|
| typical `bottom_soft_pct` | 0.12 | 保持；动作=soft_demote |
| typical `burst_keep` | 2 | 写死 2 |
| messy `keep_top_pct` | 0.20 | **0.25**（略松） |
| messy `keep_ratio_floor` | （未写） | **0.0 / 关闭** |
| 自动 messy | n≥150 + 单条件 | **n≥150 且 (burst∨tech) 高，且 ≥2 有效信号**；禁「仅张数」 |

---

## 8. Kickoff 清单

- [x] 拍板 **BLK-01** → PRD v0.2.0 冻结 **方案 A**（IQR 取代 `photoKeepMode`）  
- [x] 拍板 **BLK-03** → **T0 提交前确认**  
- [x] 拍板 **BLK-04/05/06** → soft_demote / floor=0 / ★≡featured  
- [x] 拍板 **BLK-07** → **W1 不含自动推断**；自动 messy 须确认  
- [x] 回写 PRD → **v0.2.0**  
- [ ] 拆 ACCEPTANCE + IMPLEMENTATION（BLK-12）  
- [ ] 然后 **W0**：字段 + `enabled=false` 骨架 +（可选）静态 UI 不接双控件  

---

## 9. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1 | 2026-07-29 | 五席第一轮：一致 Conditional Go；BLK-01～12 |
| v1.1 | 2026-07-29 | BLK 已回写 PRD v0.2.0；Kickoff 清单前五项勾选 |
