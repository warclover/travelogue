# PRD-MOSAIC-SLOT-ADAPTATION-V1 · 跨职能评审纪要（模板）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MOSAIC-SLOT-ADAPTATION-V1.md](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md)（**MSA** · 拼图槽位自适应） |
| **相邻挡门** | [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [P15](../PRD-PHASE15-photo-mosaic-evolution.md) · [P16](../PRD-PHASE16-layout-template-engine.md) · [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [P21](../PRD-PHASE21-mosaic-density-budget.md) · [TPC](../PRD-TEMPLATE-CONTRACT-V1.md) · [6 张拼图](../PRD-6张拼图优化.md) |
| **验收 / 实施** | 评审后拆否：□ 是 → `ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md` / `IMPLEMENTATION-…`　□ 否 · 暂用 PRD §8–§10 |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.x.x**（填） |
| **日期** | YYYY-MM-DD（填） |
| **结论** | □ Go　□ **Conditional Go**　□ No-Go　（勾选） |
| **编码** | □ 本轮仅文档回写　□ 可 Kickoff **M0**　□ 可 Kickoff **M1 / PR-A**　□ 可开 M2　（勾选） |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（LTE·装裱）· 用户体验（狗粮手测） |
| **评审方式** | 分席只读（PRD 定位块 · §0 · §2 · §5 D-MSA · §6 方案 · §10 AC）+ **对照现网代码核查**（见 §3） |
| **记录人** | （填） |
| **本纪要状态** | **模板 · 备查**（正式结案另存 `msa-mosaic-slot-adaptation-v1-review-YYYY-MM-DD.md`） |

> **使用说明**  
> 1. 会前：参评人只读 PRD 定位块 + §0.2 F-01～F-06 + §0.2 非目标 + §5 D-01/D-02/D-06/D-07；对照单反 3:2 / 手机 4:3 手测体感。  
> 2. 会中：§2 分席表决 → §3 确认代码事实 → §5 收 Must-Fix → §7 拍板 D-MSA / O-*。  
> 3. 会后：另存日期版纪要；Must-Fix 回写 PRD；更新 [DOC-STATUS](../DOC-STATUS.md)、[README](../README.md)。  
> 4. **勿重开**：舞台改 3:2、SoftCollage/GA 搜拓扑（M1–M2）、放宽朝向硬门、把 MSA 塞进 MTSO PR-D、QFX/NAS 正交议题。

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：修的是 **同族内槽位度量与 fit**，不是再堆模板、不是改选型政治（MTSO）。  
2. **手测债**：16:9 扁槽 + cover → 单反 3:2 / 手机 4:3 高度不够、主体被砍。  
3. **已定案精神（勿重开）**：舞台仍 16:9；拓扑（槽数/样式）不变；学习型拓扑 M1–M2 不做。  
4. **本场必拍**：D-MSA-01/02（拓扑固定·轨道可变）、D-06（留白预算）、D-07（默认 off）、D-08（与 MTSO 正交）、O-01/04。  
5. **本轮默认**：先文档/Must-Fix；**M0** 必过；**M1** 可在 BLK 回写后 Kickoff；禁止单 PR 塞满 M1–M3。

---

## 1. 总评（一句话）

> （会后填写：参数实例路线是否立得住？留白上限是否可签核？最大阻塞是求解可测性、mobile 变体、还是 contain 视觉？）

---

## 2. 分席表决

| 席位 | 表决 | 一句话（必填） |
|------|------|----------------|
| **产品** | □ Go / □ CG / □ No | |
| **算法** | □ Go / □ CG / □ No | |
| **架构** | □ Go / □ CG / □ No | |
| **开发** | □ Go / □ CG / □ No | |
| **测试 / QA** | □ Go / □ CG / □ No | |
| **视觉 / 排版 · 装裱** | □ Go / □ CG / □ No | |
| **用户体验 · 狗粮手测** | □ Go / □ CG / □ No | |

**汇总**：_/_ 席 · 结论 ______ · 未回写 Must-Fix 前 □ 不批无条件 Go · □ 不批 M1 合码 · □ 不批 M2

**对齐评分（主观 · 会后填）**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | | Q1–Q5 / F-01～F-06 |
| 与 MTSO/P16/P21 边界清晰度 | | 有无并轨转正或改密度 |
| 工程可开工性 | | M1 白名单族是否可独立 Kickoff |
| AC 可测性 / 防假绿 | | AR 容差、whitespace、父 OFF |
| 视觉/装裱可签核性 | | contain 底 · 留白上限 |

---

## 3. 事实核查（会前代码核对 · 影响结论）

> 下列为 **2026-07-23 探查预填**；会中勾选「属实 / 修正」。

| # | PRD / 手测假设 | 代码事实（预填） | 会中 |
|---|----------------|------------------|------|
| **F-01** | 轨道权重静态 | LTE `stage.cols/rows` 写死；`displayAspect=(col_frac/row_frac)×stageAR` | □ 属实 □ 修正：___ |
| **F-02** | 舞台 16:9 主导槽 AR | 默认 stage 16:9；大量 landscape 槽 ≈1.6–1.8 | □ 属实 □ 修正：___ |
| **F-03** | 横槽默认 cover | builders / lte_adapter：landscape/main 默认 `fit=cover` | □ 属实 □ 修正：___ |
| **F-04** | 有 AR 梯子但不改轨 | `preferLadder` / `main_ar_guard` / `f_aspect_fit` 影响入主，不改 cols/rows | □ 属实 □ 修正：___ |
| **F-05** | 3:2→16:9 槽裁切可感 | 几何量级约 15%；4:3 更狠 | □ 属实 □ 修正：___ |
| **F-06** | MTSO 不修槽 AR | MTSO 管选型/生命周期；与度量正交 | □ 属实 □ 修正：___ |

**会中新增事实**：

- …

---

## 4. 全场共识（预填 · 会中可改）

1. **根因是度量错配**，不是缺模板。  
2. **拓扑固定 · 轨道可变** 是根本路线；禁止舞台改 3:2。  
3. **MSA ⊥ MTSO**：转正指标不得搅合。  
4. **宁留白不毁构图**；whitespace 必须有硬预算。  
5. **默认 fail-closed**（`slot_adaptation.enabled=false`）至 M3。  
6. **列车拆分**：M0 文档 → M1 profile+solve → M2 contain/评分 → M3 狗粮。  
7. **本轮默认先回写文档**；M1 在 BLK 关闭后 Kickoff。

**会中新增共识**：

- …

---

## 5. Must-Fix（阻塞 Kickoff / 合码 · 候选）

| ID | 议题 | 来源席位 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|----------|-------------------|----|------|
| **BLK-MSA-01** | 架构路线不推翻 | 产品 / 架构 | D-01/D-02 写死：舞台/拓扑稳定；轨道+fit 可变；禁平行模板库 | M0 | □ |
| **BLK-MSA-02** | 实例持久化 | 架构 / 开发 | 拍板 `trackOverride`/`slotFits` 是否写入 screen 并重渲染复用（建议持久化） | M1 | □ |
| **BLK-MSA-03** | 峰判定可测 | 算法 / QA | landPeak 占比阈值、梯子容差、clamp 进 AC fixture | M1 | □ |
| **BLK-MSA-04** | mobile 变体 | 架构 / 视觉 | 9:16 stage 下 MSA 合同（同拓扑重解或禁用）写死 | M1 | □ |
| **BLK-MSA-05** | 拆 ACCEPTANCE/IMPL | 测试 / 产品 | Conditional Go 后、M1 合码前必须拆文 | M1 | □ |
| **BLK-MSA-06** | contain 视觉底线 | 视觉 / UX | M2 前冻结 contain 底色/边距最低合同（O-02） | M2 | □ |
| **BLK-MSA-07** | 面积合同不跌破 | 算法 / QA | 自适应后 main 面积/prominence 相对模板下限的硬断言 | M1 | □ |
| **BLK-MSA-08** | 日志挡门 | 测试 / 开发 | D-10 字段进 AC-08；展示层不得作唯一源 | M1 | □ |

---

## 6. Should-Fix / 建议（不阻塞 M0/M1）

| ID | 建议 | 席位 | 状态 |
|----|------|------|------|
| **S-01** | 本机狗粮 GUIDE：三画像 A/B/C + on/off 对照截图清单 | 产品 / UX | □ |
| **S-02** | M1 族白名单按曝光排序冻结（hero 5/6、竖主、4 hero） | 算法 / 开发 | □ |
| **S-03** | crop_risk 与 DESIGN-PHASE15 face IoU 路线对齐时间表 | 算法 | □ |
| **S-04** | 盲评表固定三问：主体完整性 / 杂志感 / 气质统一 | QA / 视觉 | □ |
| **S-05** | MTSO GUIDE 互链「槽 AR 问题见 MSA」 | 产品 | □ |

---

## 7. D-MSA / O-* 拍板表

### 7.1 决策（对照 PRD §5）

| ID | PRD 建议摘要 | 结论 | 备注 |
|----|--------------|------|------|
| **D-MSA-01** | 舞台/拓扑稳定；轨道+fit 可变 | □ 按建议　□ 修改：___ | |
| **D-MSA-02** | 参数实例覆盖，不平行建库 | □ 按建议　□ 修改：___ | |
| **D-MSA-03** | 主槽目标贴窗峰，不默认 16:9 | □ 按建议　□ 修改：___ | |
| **D-MSA-04** | 最扁辅槽保护强图 | □ 按建议　□ 修改：___ | |
| **D-MSA-05** | 混峰 median+clamp；整屏一套轨 | □ 按建议　□ 修改：___ | |
| **D-MSA-06** | 高 crop_risk→contain；whitespace≤W_max | □ 按建议　□ 改 W_max：___ | |
| **D-MSA-07** | 默认 enabled=false 至 M3 | □ 按建议　□ 修改：___ | |
| **D-MSA-08** | 与 MTSO 正交 | □ 按建议　□ 修改：___ | |
| **D-MSA-09** | 求解失败回退静态轨 | □ 按建议　□ 修改：___ | |
| **D-MSA-10** | raw 日志挡门 | □ 按建议　□ 修改：___ | |
| **D-MSA-11** | M1–M2 禁学习拓扑 | □ 按建议　□ 修改：___ | |
| **D-MSA-12** | 成功指标：AR 误差↓ + 主体完整↑ | □ 按建议　□ 修改：___ | |

### 7.2 开放项（PRD §13）

| ID | 问题 | 结论 |
|----|------|------|
| **O-MSA-01** | whitespace_max=0.08 | □ 按 0.08　□ 改：___　□ 保持开放至盲评 |
| **O-MSA-02** | contain 底色 | □ 纸色　□ 纯黑　□ 主色　□ 会后视觉出样 |
| **O-MSA-03** | M1 族白名单 | □ 本场冻结列表：___　□ 会后按曝光排 |
| **O-MSA-04** | override 是否持久化 | □ 持久化进 screen　□ 仅渲染态　□ 其他：___ |
| **O-MSA-05** | 默认 enabled=true 时机 | □ M3 后再定　□ 其他：___ |

---

## 8. 风险与回滚确认

| 风险 | 可接受？ | 备注 |
|------|----------|------|
| 求解抖动导致重 curate 版式闪烁 | □ 是 □ 否 | 缓存/盒约束 |
| 留白过多像贴图板 | □ 是 □ 否 | W_max 硬门 |
| CSS/长图丢掉 override | □ 是 □ 否 | 单一渲染路径 |
| 与 MTSO 指标搅合 | □ 是 □ 否 | 分文档 |

**回滚顺序确认**：`slot_adaptation.enabled=false` → **MTSO/P21 保持**　□ 同意

---

## 9. 结论与下一步

| 项 | 内容 |
|----|------|
| **结论** | □ Go　□ Conditional Go　□ No-Go |
| **可 Kickoff M0** | □ 是　□ 否 |
| **可 Kickoff M1 / PR-A** | □ 是　□ 否（须先关 BLK：___） |
| **可开 M2 合码** | □ 是　□ 否（须先关 BLK：___） |
| **Must-Fix 责任人** | |
| **回写 PRD 目标版本** | v0.2.0（Conditional Go 后） |
| **是否拆 ACCEPTANCE / IMPLEMENTATION** | □ 是　□ 豁免至：___ |

**建议列车**

| PR | 内容 | 依赖 |
|----|------|------|
| **PR-A / M1** | profile + 白名单求解 + 日志 + 父开关 | BLK-02/03/04/05/07/08 |
| **PR-B / M2** | crop_risk contain + 分配精修 + 评分 | BLK-06 · PR-A |
| **PR-C / M3** | 三画像狗粮 + 盲评 + 默认 on 决策 | AC-09～11 |

---

## 10. 签名栏

| 角色 | 姓名 | 日期 | 表决 |
|------|------|------|------|
| 产品 | | | |
| 算法 | | | |
| 架构 | | | |
| 开发 | | | |
| 测试 / QA | | | |
| 视觉 / 排版 | | | |
| 用户体验 · 狗粮 | | | |

---

## 附录 A · 会前阅读清单（15 分钟）

| # | 材料 | 必读段落 |
|---|------|----------|
| 1 | [MSA PRD](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) | 定位块 · §0 · §5 · §6 · §10 |
| 2 | [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | §0.1 与 MSA 边界 |
| 3 | [P16](../PRD-PHASE16-layout-template-engine.md) | stage / slots / weighted tracks |
| 4 | 代码锚点（可选） | `layout_templates/geometry.py` · `mosaic/builders.py` fit · `lte_adapter` |

## 附录 B · 表决口径

| 符号 | 含义 |
|------|------|
| **Go** | 合同可开工；无阻塞 Must-Fix |
| **Conditional Go (CG)** | 方向成立；列出的 BLK 回写前不批对应里程碑合码 |
| **No-Go** | 根因/边界不成立；须改切口或缩范围后再评 |
