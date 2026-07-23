# PRD-MOSAIC-SLOT-ADAPTATION-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MOSAIC-SLOT-ADAPTATION-V1.md](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md)（**MSA** · 拼图槽位自适应） |
| **模板来源** | [msa-mosaic-slot-adaptation-v1-review-TEMPLATE.md](./msa-mosaic-slot-adaptation-v1-review-TEMPLATE.md) |
| **相邻挡门** | [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [P15](../PRD-PHASE15-photo-mosaic-evolution.md) · [P16](../PRD-PHASE16-layout-template-engine.md) · [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [P21](../PRD-PHASE21-mosaic-density-budget.md) · [TPC](../PRD-TEMPLATE-CONTRACT-V1.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-07-23 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff M0**（决策回写 + 拆 ACCEPTANCE/IMPL）；**M1 合码前须关闭 BLK-MSA-02～05、07、08**；**M2 合码前须关闭 BLK-MSA-06** |
| **编码** | □ 本轮仅文档　☑ **可 Kickoff M0**　□ 可 Kickoff M1（待 BLK）　□ 可开 M2 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（LTE·装裱）· 用户体验（狗粮手测） |
| **评审方式** | 分席只读 + **对照现网代码核查**（`geometry.slot_display_aspect` · builders/lte_adapter `fit=cover` · MTSO 边界） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-07-23 实机债 + 代码探查 + PRD v0.1.0） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写** · 可 Kickoff M0 |
| **审查基线** | LTE 固定轨道 + cover · 舞台 16:9 · MTSO 选型正交 |

---

## 0. 会前宣读（主持人）

1. **切口**：同族内 **轨道度量 + fit**，不是堆模板，不是改 MTSO 选型。  
2. **手测债**：3:2 / 4:3 进扁槽被 cover 砍高度——属实且可几何量化。  
3. **勿重开**：舞台改 3:2、M1–M2 上 SoftCollage、放宽朝向硬门、MSA 并进 MTSO 转正 KPI。  
4. **本场必拍**：D-01/02 · D-06 · D-07 · D-08 · O-04 持久化。  
5. **列车**：M0 先过；M1 在 BLK 回写后 Kickoff；禁单 PR 塞满。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：「拓扑固定 · 轨道可变 · 高风险可留白」链条成立，且与 MTSO/BRIC 定位清晰；但 v0.1 有三处开工前必须钉死——screen 实例是否持久化、mobile 9:16 变体合同、峰判定阈值进 AC——否则 M1 会在渲染长图与验收假绿上翻车。M0（回写+拆文）可立即 Kickoff；M1 合码挡在 BLK-02～05/07/08。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 三画像与「宁留白不毁构图」对齐用户债；须承诺不借 MSA 改舞台、不搅 MTSO 转正 |
| **算法** | **Conditional Go** | 窗峰→\(r^*\)→轨道求解方向对；峰占比/容差必须进 fixture，否则 AC-02/03 不可复现 |
| **架构** | **Conditional Go** | 参数实例正确；**O-04 必须在 M1 前拍板持久化**，否则 preview/export/重 curate 三套几何 |
| **开发** | **Conditional Go** | M1 白名单族可开；CSS/grid 覆盖与 mobile variant 要同一合同，禁只改 web 16:9 |
| **测试 / QA** | **Conditional Go** | AC-01 父 OFF 可测；须钉 AR 容差与 whitespace 硬门；日志字段必须进单测 |
| **视觉 / 排版 · 装裱** | **Conditional Go** | 支持主槽贴 3:2/4:3；`W_max=0.08` 可作起点；contain 底色未定前不批 M2 视觉签核 |
| **用户体验 · 狗粮手测** | **Conditional Go** | 单反用户痛点真实；混排「一页一种气质」是正确北星；要有 A/B/C 对照截图清单 |

**汇总**：**七席一致 Conditional Go**。  
- **M0**：可 Kickoff（回写 v0.2 + 拆 ACCEPTANCE/IMPL）。  
- **M1 合码**：BLK-MSA-02～05、07、08 关闭前 **不批**。  
- **M2 合码**：BLK-MSA-06（contain 视觉）关闭前 **不批**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | **9** | Q1–Q5 / F-01～F-06 与手测一致 |
| 与 MTSO/P16/P21 边界清晰度 | **9** | 正交写清楚；勿并轨 |
| 工程可开工性 | **6** | M0 可开；M1 卡在持久化/mobile/峰阈值 |
| AC 可测性 / 防假绿 | **6** | 容差与峰判定须硬化 |
| 视觉/装裱可签核性 | **5** | contain 底与留白观感仍开放 |

---

## 3. 事实核查（代码核对 · 全部属实）

| # | 假设 | 代码事实 | 会中 |
|---|------|----------|------|
| **F-01** | 轨道静态 | `geometry.slot_display_aspect` 吃 YAML `cols/rows` | ✅ 属实 |
| **F-02** | 舞台 16:9→扁槽 | 多枚 mosaic landscape 槽 AR≈1.6–1.8 | ✅ 属实 |
| **F-03** | 横默认 cover | `builders` / `lte_adapter` landscape/main → `cover` | ✅ 属实 |
| **F-04** | ladder 不改轨 | `main_eligibility` / scorer aspect 项不写 track | ✅ 属实 |
| **F-05** | 3:2 裁切可感 | 几何约 15%；手测「高度不够」成立 | ✅ 属实 |
| **F-06** | MTSO 正交 | MTSO 管选型/生命周期，不改槽度量 | ✅ 属实 |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-07** | 模板常有 `stage.variants`（web 16:9 / mobile 9:16） | MSA 必须定义 **每个 variant 是否重解**；只解 web 会让手机预览回潮扁槽 |
| **F-08** | screen 今日可带 `layoutGeometry` / per-slot displayAspect（LTE solidify 路径） | 持久化 override **有挂载点**，不是从零发明 |
| **F-09** | portrait 已有 `portrait_fit→contain` 先例 | MSA contain 可复用语义，避免第二套 fit 方言 |

---

## 4. 全场共识

1. **根因是度量错配**，不是缺模板。  
2. **拓扑固定 · 轨道可变** 锁定为根本路线。  
3. **MSA ⊥ MTSO**；转正/漏斗字段分离。  
4. **宁留白不毁构图**；`whitespace_max` 为硬门（数值可盲评微调）。  
5. **默认 fail-closed** 至 M3。  
6. **实例几何必须单一真相源**（preview = export = 重渲染）。  
7. **mobile 变体与 web 同合同**，禁止只优化 16:9。  
8. **列车**：M0 → M1 → M2 → M3；禁单 PR 塞满。

---

## 5. Must-Fix（结案成立）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-MSA-01** | 架构路线 | D-01/D-02 不推翻 | M0 | ✅ 本场确认 |
| **BLK-MSA-02** | 实例持久化 | **拍板：持久化**进 screen（`layoutGeometry.trackOverride` + `slots[].fit`）；重渲染复用 | M1 | ✅ 本场拍板 · 待回写 PRD |
| **BLK-MSA-03** | 峰判定可测 | 占比≥0.60、梯子容差 0.08、clamp、wide_peak_fraction 进 AC | M1 | ✅ 阈值确认 · 待回写 |
| **BLK-MSA-04** | mobile 变体 | **每个激活 variant 各自求解**；无解则该 variant 回退静态轨并打点 | M1 | ✅ 本场拍板 · 待回写 |
| **BLK-MSA-05** | 拆 ACCEPTANCE/IMPL | M1 合码前必须拆文 | M1 | ✅ M0 已拆 |
| **BLK-MSA-06** | contain 视觉 | M2 前出最低合同：底色=杂志纸色（默认）、边距不引入装饰框 | M2 | ✅ [BLK06](./msa-contain-visual-contract-BLK06.md) |
| **BLK-MSA-07** | 面积不跌破 | 自适应后 main 面积/prominence ≥ 模板声明下限（硬断言） | M1 | ✅ 已在 D-03 · AC 强化 |
| **BLK-MSA-08** | 日志挡门 | D-10 字段进 AC-08 fixture | M1 | ✅ 已有 D-10 · AC 强化 |

---

## 6. Should-Fix

| ID | 建议 | 席位 | 状态 |
|----|------|------|------|
| **S-01** | `msa-local-dogfood-GUIDE`：A/B/C + on/off 截图清单 | UX / 产品 | ✅ PR-C |
| **S-02** | M1 白名单：横主 5/6 hero、竖主 1P4L/2P3L、4-hero-sidebar | 算法 | ✅ gap-close 冻结 |
| **S-03** | crop_risk M2 对齐 face IoU（D-MCS-14） | 算法 | ☐ |
| **S-04** | 盲评三问表进 acceptance-records | QA / 视觉 | ✅ TEMPLATE |
| **S-05** | MTSO dogfood GUIDE 互链 MSA | 产品 | ✅ MSA GUIDE 互链 |

---

## 7. D-MSA / O-* 拍板

### 7.1 决策

| ID | 结论 |
|----|------|
| **D-MSA-01～05** | ✅ **按建议** |
| **D-MSA-06** | ✅ **按建议**；`whitespace_max` 默认 **0.08**（O-01 盲评前可 ±0.02，不改硬门语义） |
| **D-MSA-07～12** | ✅ **按建议** |

### 7.2 开放项

| ID | 结论 |
|----|------|
| **O-MSA-01** | **暂定 0.08**；M3 盲评可调 |
| **O-MSA-02** | **默认杂志纸色**；M2 前出样（BLK-06） |
| **O-MSA-03** | 会后按曝光冻结；S-02 候选列表通过 |
| **O-MSA-04** | ✅ **关闭：持久化进 screen**（BLK-02） |
| **O-MSA-05** | **保持开放至 M3** |

---

## 8. 风险与回滚

| 风险 | 可接受？ | 备注 |
|------|----------|------|
| 求解抖动 | ✅ | 盒约束 + 同窗缓存（IMPL 写） |
| 留白过多 | ✅ | W_max 硬门 |
| 长图丢 override | ✅ | 持久化 + 单路径渲染（BLK-02） |
| 与 MTSO 搅合 | ✅ | 分文档分字段 |

**回滚顺序**：`slot_adaptation.enabled=false` → MTSO/P21 保持　✅ 同意

---

## 9. 结论与下一步

| 项 | 内容 |
|----|------|
| **结论** | **Conditional Go** |
| **可 Kickoff M0** | ✅ 是 |
| **可 Kickoff M1** | ❌ 否（先关 BLK-02～05、07、08 文档/合同；再开码） |
| **可开 M2** | ❌ 否（BLK-06） |
| **Must-Fix 责任人** | 产品+架构主笔合同回写；开发落 M1；视觉主笔 contain 底 |
| **回写 PRD** | **v0.2.0** |
| **拆 ACCEPTANCE / IMPLEMENTATION** | ✅ 是（BLK-05 · M1 合码前） |

**建议列车**

| PR | 内容 | 依赖 |
|----|------|------|
| **M0** | PRD v0.2 回写 · 拆 ACCEPTANCE/IMPL · DOC-STATUS | 本纪要 |
| **PR-A / M1** | profile + 白名单求解 + 持久化实例 + 日志 + 父开关 | BLK-02～05/07/08 |
| **PR-B / M2** | crop_risk contain + 分配精修 + 评分 | BLK-06 · PR-A |
| **PR-C / M3** | 三画像狗粮 + 盲评 + 默认 on 决策 | AC-09～11 |

---

## 10. 签名栏（模拟联评）

| 角色 | 表决 |
|------|------|
| 产品 | Conditional Go |
| 算法 | Conditional Go |
| 架构 | Conditional Go |
| 开发 | Conditional Go |
| 测试 / QA | Conditional Go |
| 视觉 / 排版 | Conditional Go |
| 用户体验 · 狗粮 | Conditional Go |

---

## 附录 · 结案清单

| 项 | 状态 |
|----|------|
| 日期版纪要落盘 | ✅ 本文 |
| PRD 回写 v0.2.0 | ✅ 同步 |
| DOC-STATUS / README | ✅ 同步 |
| 模板保留备查 | ✅ TEMPLATE |
| ACCEPTANCE / IMPLEMENTATION 拆文 | ✅ M0 |
