# PRD-EXPORT-CARD-COMPOSE-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-EXPORT-CARD-COMPOSE-V1.md](../PRD-EXPORT-CARD-COMPOSE-V1.md)（**ECC** · 导出 3:4 卡片统一） |
| **模板来源** | [ecc-export-card-compose-v1-review-TEMPLATE.md](./ecc-export-card-compose-v1-review-TEMPLATE.md) |
| **关联** | [ADR-021 v0.3](../adr/021-export-compose-dual-engine.md) · [PRD-LONGSHOT-2.0.md §6.4](../PRD-LONGSHOT-2.0.md)（superseded）· [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md §6](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md)（部分 superseded） |
| **评审版本** | PRD **v0.2** / ADR **v0.3** → Must-Fix 回写后升 **PRD v0.3.0** |
| **日期** | 2026-08-05 |
| **结论** | **有条件通过（Conditional Go）** |
| **编码** | ☑ **可 Kickoff Stage 1**（模板库落地，纯新增文件，无冲突）　□ Stage 2 挡 BLK-ECC-01～03　□ Stage 3/4 挡 BLK-ECC-04/05 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD §0～§10 + ADR-021 D1～D4 · **对照现网代码**（`compose_canvas.py` · `poster_bric_pack.py` · `collage_pack.py` · `platform_profiles.yaml` · `layout_contract/usage_context.py` · `curation/cover_scoring_v2.py`） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-05 代码现状核查 + PRD v0.2 / ADR v0.3） |
| **本纪要状态** | **已结案 · Conditional Go** · 待 PRD 回写 |

---

## 0. 会前宣读（主持人）

1. **切口**：ECC 统一小红书 / 单张海报 / 画册三出口为 3:4 卡片管线，**不动**微信群 / 朋友圈（Slice-A/B 冻结）。
2. **范围收窄**：三出口**不要求**按聚类 / 分镜拼图，只要求槙位横竖版正确填充——这是用户 2026-08-05 明确简化，不是本场重新讨论的议题。
3. **本场必拍**：模板复用对象是否对口（DEFAULT_FEATURED_WEIGHT vs cover_score_v2）· screen_planner.py 复用边界 · 当前分支代码（v0.1）与新决策（v0.2/v0.3）的落差是否已被 PRD 显式承认 · OQ-ECC-04 是否可开工前给默认解。
4. **勿重开**：单张海报画幅 3:4（已定）、画册两卡+gutter 几何（已定）、9 套模板几何（用户设计稿已确认，含 img9 更正）。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：三出口统一 3:4 卡片、模板库落地、"不要求分镜边界"的简化方向均正确；但 PRD 里两处技术表述与现网代码事实不符——(1) §5.2/D4 引用的 `DEFAULT_FEATURED_WEIGHT` 语义是屏内主图评分权重，不是「代表性精选」，应改引 `cover_scoring_v2.py`；(2) 当前分支 `compose_canvas.py`/`platform_profiles.yaml` 仍是 v0.1（A4/2.8:1/bric_compose/章节优先打包），PRD 需显式承认这是「待迁移债」而非「可直接复用」。这两处不回写会导致实施阶段选错复用对象、或误以为现有 `pack_album_pages_by_chapter` 可以直接留用。Stage 1（模板文件）可立即开工；Stage 2 起步前须先关闭 BLK-ECC-01～03。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 三出口统一叙事清楚；单张海报模板优先级符合"带主图/满版优先"诉求；要求 §5.2 的选图权重来源订正后才能对外讲清楚"代表性精选"到底是什么 |
| **算法** | Conditional Go | `DEFAULT_FEATURED_WEIGHT` 是 `main_eligible_hero_score_gap` / hero 资格评分权重（screen_planner 内部），不是全书代表性排序；正确复用对象是 `cover_scoring_v2.cover_score_v2()`（逐图打分，可排序取 top-N）；此项**必须回写**，否则实施会调错函数 |
| **架构** | Conditional Go | `screen_planner.py` 是 ~1930 行状态化规划器，`CardTemplateSelector` **不能**直接 import 复用其判定函数（耦合/循环 import 风险，参照 ADR-011 延迟 import 精神）；PRD §4 措辞已留"只借鉴思路"的余地，但需要**显式写死**"CardTemplateSelector 是独立新实现，不 import screen_planner 内部状态"，避免开发时图省事直连 |
| **开发** | Conditional Go | 现状核查：`compose_canvas.py`（`A4_CANVAS`/`ALBUM_CANVAS=2.8:1`/`bric_compose`+cover-fill）、`platform_profiles.yaml`（`poster_bric.output.aspect="A4"`、`album_spread.output.aspect="2.8:1"`）**均未同步**新决策，仍是 v0.1；PRD 需把这些列为 Stage 3/4 的**显式迁移项**，不能语焉不详让人以为"结构已就位只是换模板" |
| **测试 / QA** | Conditional Go | AC-ECC-01～06 可测；补充：需锁定 `platform_profiles.yaml` 的 `output.aspect` 字段随 Stage 4 同步更新（回归测试防"文案说 3:4，profile 字段仍报 A4"的用户可见不一致）；`collage_pack.py` 当前 `_xhs_per_page`（3–6）/`_ALBUM_PER_PAGE`（6）不含模板库真实槙数 {1,4,6,7,9} 中的部分值，需在 Stage 2 CardGrouper 落地后整体替换，不能局部改数字了事 |
| **视觉 / 排版** | Conditional Go | 9 套模板几何清楚，`card-4-square-top-triband` 顶部近方槙（`1.125`）裁切损失需要真实素材抽样验证；4 套 6 槙 + 2 套 7 槙模板之间需要一个可执行的默认选择规则（哪怕是简单轮换），否则纯随机会显得杂乱无风格（OQ-ECC-04 需给最小可行默认解） |
| **用户体验 · 狗粮** | Conditional Go | "代表性精选"效果最终要看狗粮盲评，不能只靠公式自证；建议 Stage 3 先出 1–2 本对比册（代表性精选 vs 简单前 N 张）再定稿权重细节 |

**汇总**：**七席 7/7 Conditional Go**。

- **Stage 1**：✅ 可立即 Kickoff（模板库 9 套纯新增文件，无代码冲突）。
- **Stage 2**：BLK-ECC-01/02/03 关闭前不批开工。
- **Stage 3/4**：BLK-ECC-04/05 关闭前不批合入宣称 Done。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 三出口统一动机清楚；两处引用对象错配拉低分 |
| 与既有系统边界 | **7** | 分镜/聚类降级为可选合理；但未点名要退役 `pack_album_pages_by_chapter` |
| 工程可开工性 | **7** | Stage1 干净；Stage2 起点（screen_planner 复用边界）需先钉死避免走偏 |
| AC 可测性 / 防假绿 | **7** | AC-ECC-01～06 够用；缺 profile 字段一致性回归项 |
| 视觉可裁性 | **7** | 9 套模板到位；同槙数多套之间的选择规则是唯一悬空的視覺相关决策 |

---

## 3. 事实核查（对照现网）

| # | 断言 | 会中核查 |
|---|------|---------|
| **F-01** | `compose_canvas.py` 仍为 v0.1：`A4_CANVAS=(1748,2480)`、`ALBUM_CANVAS=(2800,1000)`（2.8:1）、`bric_compose`+`_cover_paste_cell` 装箱 | ✅ 属实（代码现状；PRD/ADR 文档已升 v0.2/v0.3，代码未跟进） |
| **F-02** | `platform_profiles.yaml`：`poster_bric.output.aspect="A4"`（1748×2480）、`album_spread.output.aspect="2.8:1"`（2800×1000） | ✅ 属实，与 ADR-021 D2.1/D2.2 的新决策不一致 |
| **F-03** | `poster_bric_pack.py`：`MIN_N=3, MAX_N=9`，允许 3–9 张塞进 A4 bric | ✅ 属实；与新模板优先级（含主图模板最多 6 槙，`card-4-square-top-triband` 仅 4 槙）不匹配，Stage3 需按所选模板动态定张数上限 |
| **F-04** | `collage_pack.py`：`_XHS_PER_PAGE_MIN/MAX=3/6`，`_ALBUM_PER_PAGE=6` | ✅ 属实；3、5 不在模板库槙数集合 {1,4,6,7,9} 中，Stage2 CardGrouper 落地后需整体替换（不是改常量） |
| **F-05** | `pack_album_pages_by_chapter` 当前**按章分页**（chapter-first packing） | ✅ 属实；这正是 v0.2 明确要移除的"分镜/章节边界约束"，PRD §7 Supersedes 表**未点名**此函数，需补 |
| **F-06** | `DEFAULT_FEATURED_WEIGHT=1.35` 语义 | ✅ 核查：定义于 `layout_contract/usage_context.py`，用于 `screen_planner.py` / `main_eligibility.py` 的 **屏内主图资格评分**（`main_eligible_hero_score_gap` 等），是「一屏内挑 hero」的权重，**不是**「全书代表性精选」信号 |
| **F-07** | `cover_scoring_v2.py` 提供 `cover_score_v2(asset, pool, ...)` | ✅ 属实：逐张打封面分、可对 pool 排序取 top-N，是 §5.2「代表性精选」更对口的复用对象 |
| **F-08** | `screen_planner.py` 规模与耦合度 | ✅ 属实：约 1930 行，`ScreenLayoutPlannerState` 贯穿章节/家族/氛围规则，非可孤立调用的纯函数 |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-09** | `poster_bric_pack.py` 的 `gcs_poster_bric_enabled()` 默认 `True`（GCS Track B），且 Writer 不写 `screens[]` | → 与 PRD §7 Supersedes 表"Writer/flag 挂点不变"一致，**无需改动**该守卫逻辑，仅换内部构图函数 |
| **F-10** | `platform_profiles.yaml` 里 `poster_bric.publish_guide` 文案仍写"A4 竖版拼贴海报" | → 与 Studio 面板已改的"3:4"文案不一致，Stage 4 收口时需同步改这条 YAML 文案，否则用户会看到两套矛盾说明 |

---

## 4. 全场共识

1. ECC 是"统一出口几何 + 真模板"，不是重新讨论分镜/聚类要不要参与（已由用户拍板：不参与）。
2. `DEFAULT_FEATURED_WEIGHT` 不是本 PRD 该引用的信号；`cover_scoring_v2.py` 才是。
3. `CardTemplateSelector` 不得直接 import `screen_planner.py` 的状态化实现；只借鉴判定顺序思路，独立实现。
4. 当前分支代码（`compose_canvas.py` / `platform_profiles.yaml` / `poster_bric_pack.py` / `collage_pack.py`）是 v0.1 状态，PRD 必须显式列出这些文件为迁移目标，不能默认"文档定了代码就自动跟上"。
5. `pack_album_pages_by_chapter` 的章节优先打包在 Stage 2/3 需**主动退役**，不是保留。
6. OQ-ECC-04（同槙数多套模板怎么选）在 Stage 2 开工前需给一个可执行默认解（即便是最简单的"按序轮换"），否则 Stage2 无法收口。
7. Stage 1（模板库 9 套 .md）已是纯新增文档产物，无需等其它 BLK 关闭即可视为完成。

---

## 5. Must-Fix（阻塞）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-ECC-01** | §5.2/D4 选图权重复用对象订正 | 把「复用 `DEFAULT_FEATURED_WEIGHT`」改为「复用 `curation/cover_scoring_v2.py` 的 `cover_score_v2()` 排序取 top-N」；回写 PRD §5.2 + ADR-021 D4 | Stage 2 | ⏳ 待回写 |
| **BLK-ECC-02** | CardTemplateSelector 独立实现声明 | PRD §4 明确写死：「不 import `screen_planner.py` 内部状态/函数；仅参考其判定顺序思路重新实现独立选择函数」 | Stage 2 | ⏳ 待回写 |
| **BLK-ECC-03** | OQ-ECC-04 默认解 | 给出至少一个可执行默认策略（如「按 Card 序号在同槙数模板间轮换」），关闭 OQ-ECC-04 或明确标注默认值 + 后续可调 | Stage 2 | ⏳ 待回写 |
| **BLK-ECC-04** | 代码迁移清单显式化 | PRD §7/§9 补充列出需改动的现网文件：`compose_canvas.py`（A4/2.8:1 常量、bric 装箱）、`platform_profiles.yaml`（`poster_bric`/`album_spread` 的 `output.aspect`/`publish_guide`）、`poster_bric_pack.py`（MIN_N/MAX_N 按模板动态定）、`collage_pack.py`（per-page 常量） | Stage 3/4 | ⏳ 待回写 |
| **BLK-ECC-05** | `pack_album_pages_by_chapter` 退役说明 | PRD §7 Supersedes 表补一行，明确该函数的章节优先分组在 Stage 2/3 被 CardGrouper 取代 | Stage 3 | ⏳ 待回写 |

**Should-Fix（不阻塞 Stage 1）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-ECC-01** | `card-4-square-top-triband` 顶部裁切槙用真实素材试拼，确认裁切损失可接受 | 待 Stage 3 狗粮 |
| **SHD-ECC-02** | `platform_profiles.yaml` 的 `poster_bric.publish_guide`（"A4 竖版拼贴海报"）随 Stage4 一并改文案 | 待 Stage 4 |
| **SHD-ECC-03** | Stage 3 先出 1–2 本"代表性精选 vs 前 N 张"对比册，供用户体验席过一遍 | 待 Stage 3 |

---

## 6. 拍板 D / OQ（锁定）

| ID | 结论 |
|----|------|
| D2.1（单张海报 A4→3:4） | ✅ 维持 |
| D2.2（画册 2.8:1→两卡+gutter） | ✅ 维持 |
| D4（海报选图=代表性精选） | ✅ 维持，**复用对象改为 `cover_scoring_v2`**（BLK-ECC-01） |
| OQ-ECC-01（海报权重公式） | 待实施阶段定稿；本场确认复用起点为 `cover_score_v2` |
| OQ-ECC-02（画册奇数卡配对） | 未关闭；不阻塞 Stage 1–2 |
| OQ-ECC-03（安全区差异化） | 未关闭；9 套模板已到位，留 Stage 3 抽样评估 |
| OQ-ECC-04（同槙数多套模板选择规则） | **本场要求 Stage 2 开工前给默认解**（BLK-ECC-03） |

---

## 7. 结论栏

| 项 | 结果 |
|----|------|
| **Conditional Go** | ✅ |
| **可 Kickoff Stage 1** | ✅ 立即（模板库 9 套已交付，纯新增） |
| **可 Kickoff Stage 2** | ❌ 待关闭 BLK-ECC-01/02/03 |
| **可 Kickoff Stage 3/4** | ❌ 待关闭 BLK-ECC-04/05 |
| **No-Go** | 无 |

---

## 8. 会后动作

1. 回写 PRD → **v0.3.0**（本纪要链接 · BLK-ECC-01～05 回写 · Conditional Go 状态）。
2. 同步更新 ADR-021 D4（复用对象订正）。
3. DOC-STATUS.md / README.md 补登记本评审记录。
4. Stage 2 开工前，工程侧先确认 BLK-ECC-01～03 已在 PRD 落字；Stage 3/4 前确认 BLK-ECC-04/05。
5. 不在本轮重开分镜/聚类是否参与的讨论（已由用户拍板）。

---

## 9. 签字栏（模拟联评）

| 席位 | 表决 | 日期 |
|------|------|------|
| 产品 | Conditional Go | 2026-08-05 |
| 算法 | Conditional Go | 2026-08-05 |
| 架构 | Conditional Go | 2026-08-05 |
| 开发 | Conditional Go | 2026-08-05 |
| 测试 / QA | Conditional Go | 2026-08-05 |
| 视觉 / 排版 | Conditional Go | 2026-08-05 |
| 用户体验 · 狗粮 | Conditional Go | 2026-08-05 |
