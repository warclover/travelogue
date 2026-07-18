# PRD-MCS-SIGNATURE-ROUTING-V1 · 跨职能评审纪要（模板）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MCS-SIGNATURE-ROUTING-V1.md](../PRD-MCS-SIGNATURE-ROUTING-V1.md) |
| **对标** | Shutterfly US8131114 · Smart photobook creation（LLPP 格式签名 · Claim 12 图注一体） |
| **相邻挡门** | [PRD-MCS-GEOMETRIC-QUALITY-V1.md](../PRD-MCS-GEOMETRIC-QUALITY-V1.md)（D-MGQ-02）· [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) · [PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md](../PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [P17-LSE-处置建议.md](../P17-LSE-处置建议.md) · [观感提升路线图.md](../观感提升路线图.md) |
| **验收 / 实施** | 评审后拆否：□ 是 → `ACCEPTANCE-…` / `IMPLEMENTATION-…`　□ 否 · 暂用 PRD §9 |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.x.x**（填） |
| **日期** | YYYY-MM-DD（填） |
| **结论** | □ Go　□ **Conditional Go**　□ No-Go　（勾选） |
| **编码** | □ 本轮仅文档/设计　□ 可 Kickoff W0　（勾选） |
| **参评角色** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 设计（LTE SKU）· 典型用户（旅行厚册 / 图文叙事册） |
| **评审方式** | 分席只读（PRD §0.1 D/OQ · §2 目标/非目标 · §5 签名 · §6 图文 · §7 page-group · OUT-01～11） |
| **记录人** | （填） |
| **本纪要状态** | **模板 · 备查**（正式结案见 [mcs-signature-routing-v1-review-2026-07-18.md](./mcs-signature-routing-v1-review-2026-07-18.md)） |

> **使用说明**  
> 1. 会前：参评人只读 PRD 定位块 + §0.1 + §2.2 非目标 + §3.1 硬过滤顺序；对照 MGQ「禁 runtime 改 rect」、LSE 冻结、Hungarian 非主杠杆。  
> 2. 会中：§2 分席表决 → §4 收 Must-Fix → §6 拍板 D-MSR / OQ-MSR（**OQ-01 / OQ-02 / OQ-05 本场建议关**）。  
> 3. 会后：另存 `mcs-signature-routing-v1-review-YYYY-MM-DD.md`，删「模板」字样；Must-Fix 回写 PRD 后再改结论行与 README 状态。

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：学 Shutterfly 的是 **签名硬路由 + 图文一体**，不是整段重写成印刷相册流水线。  
2. **已定案精神（勿重开）**：MCS 权威选窗；LSE 冻结；禁止 runtime 改 `slots[].rect`；Hungarian 默认 off、非观感主故事。  
3. **三轨**：A=有序签名索引；B=caption-aware；C=章内时间 page-group（色调不做 V1）。  
4. **双轨债**：YAML `mix` vs `try_order_for_pattern` —— 本场要拍「签名是否成为候选入口权威」。  
5. **本场必拍**：D-MSR-01～10；建议关闭 OQ-MSR-01 / 02 / 05。  
6. **本轮默认不动代码**（除非结论勾选可 Kickoff W0）。

---

## 1. 总评（一句话）

> （会后填写：签名硬筛是否成立？caption 两阶段是否可接受？最大阻塞是字母表、ordering 收敛，还是 narrate replan？W0 能否只做 shadow？）

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | □ Go / □ CG / □ No | |
| **算法** | □ Go / □ CG / □ No | |
| **架构** | □ Go / □ CG / □ No | |
| **开发** | □ Go / □ CG / □ No | |
| **测试 / QA** | □ Go / □ CG / □ No | |
| **设计 · LTE SKU** | □ Go / □ CG / □ No | |
| **用户 · 旅行厚册** | □ Go / □ CG / □ No | |
| **用户 · 图文叙事册** | □ Go / □ CG / □ No | |

**汇总**：_/_ 席 · 结论 ______ · 未回写 Must-Fix 前 □ 不批无条件 Go

---

## 3. 全场共识（预填 · 会中可改）

1. **签名 = 硬路由契约**，不是替换 MCS soft。  
2. **有序 LLPP 优先于 bag-of-mix**；L3 size 兜底防枯竭。  
3. **caption 优先是产品差异点**；全册 narrate 后重跑 MCS 禁止。  
4. **Hungarian 不作本主题卖点**。  
5. **Lab 色调子分组不做 V1**。  
6. **W0 ≠ 主题完成**：W0=决策冻结 + shadow；W1=硬筛挂候选；W2=page-group/replan；W3=盲评。  
7. **本轮默认只做评审/文档回写**。

**会中新增共识**：

- …

---

## 4. Must-Fix（阻塞 Kickoff · 候选清单 · 会中增删）

| ID | 议题 | 来源席位 | 要求 | 状态 |
|----|------|----------|------|------|
| **BLK-01** | 落点一字面冻结 | 架构 | D-MSR-01/11 与 OUT-03 写死；禁止默认同步进 LSE | □ |
| **BLK-02** | 硬过滤顺序 | 算法 / 架构 | §3.1 顺序冻结；soft 不得绕过 `signature:*` | □ |
| **BLK-03** | 字母表与方图 | 算法 | 关闭 OQ-01；写进 §5.1 | □ |
| **BLK-04** | 签名资产序 | 算法 | 关闭 OQ-02；与 chronology 一致 | □ |
| **BLK-05** | YAML SSOT | 设计 / 开发 | 关闭 OQ-05：派生为主 vs 显式字段 | □ |
| **BLK-06** | ordering 收敛 | 开发 | D-MSR-04 的 W1/W2 迁移合同可测 | □ |
| **BLK-07** | caption SSOT 字段名 | 开发 / 产品 | `captionAreas` / `supportsCaption` 钉死一个 | □ |
| **BLK-08** | W1 前拆 AC/IMPL | 测试 | 与 MGQ/GCS 同纪律 | □ |

---

## 5. Should-Fix / 建议（不阻塞 W0）

| ID | 建议 | 席位 | 状态 |
|----|------|------|------|
| S-01 | GCS 轨 A 枚举输出带 `formatSignature` 元数据 | 设计 | □ |
| S-02 | Studio 调屏序另立 PRD，本场只记 OQ-04=B | 产品 | □ |
| S-03 | 盲评切片单独含「横竖混排 + 有图注」子集 | QA | □ |

---

## 6. D-MSR / OQ 拍板表

| ID | 结论 | 备注 |
|----|------|------|
| D-MSR-01 | □ 按建议　□ 修改：___ | |
| D-MSR-02 | □ 按建议　□ 修改：___ | |
| D-MSR-03 | □ 按建议　□ 修改：___ | |
| D-MSR-04 | □ 按建议　□ 修改：___ | |
| D-MSR-05 | □ 按建议　□ 修改：___ | |
| D-MSR-06 | □ 按建议　□ 修改：___ | |
| D-MSR-07 | □ 按建议　□ 修改：___ | |
| D-MSR-08 | □ 按建议　□ 修改：___ | |
| D-MSR-09 | □ 按建议　□ 修改：___ | |
| D-MSR-10 | □ 按建议　□ 修改：___ | |
| OQ-MSR-01 | □ 关闭·A　□ 关闭·其他：___　□ 保持开放 | |
| OQ-MSR-02 | □ 关闭·A　□ 关闭·其他：___　□ 保持开放 | |
| OQ-MSR-03 | □ 关闭·A　□ 关闭·其他：___　□ 保持开放 | |
| OQ-MSR-04 | □ 关闭·B　□ 关闭·其他：___　□ 保持开放 | |
| OQ-MSR-05 | □ 关闭·A　□ 关闭·其他：___　□ 保持开放 | |

---

## 7. 结论与下一步

| 项 | 内容 |
|----|------|
| **结论** | □ Go　□ Conditional Go　□ No-Go |
| **可 Kickoff W0** | □ 是　□ 否 |
| **Must-Fix 责任人** | |
| **回写 PRD 目标版本** | v0.2.0（Conditional Go 后） |
| **README 状态行** | 评审后更新 |

---

## 8. 签名栏

| 角色 | 姓名 | 日期 |
|------|------|------|
| 产品 | | |
| 算法 | | |
| 架构 | | |
| 开发 | | |
| 测试 | | |
