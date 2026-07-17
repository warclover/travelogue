# PRD-WAIT-TIPS-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-WAIT-TIPS-V1.md](../PRD-WAIT-TIPS-V1.md) |
| **实施** | [IMPLEMENTATION-WAIT-TIPS-V1.md](../IMPLEMENTATION-WAIT-TIPS-V1.md) |
| **验收** | [ACCEPTANCE-WAIT-TIPS-V1.md](../ACCEPTANCE-WAIT-TIPS-V1.md) |
| **线框** | [wait-tips-v1-wireframe.html](../wireframes/wait-tips-v1-wireframe.html) · F1–F5 |
| **文案润色** | [wait-tips-v1-copy-workshop-2026-07-17.md](./wait-tips-v1-copy-workshop-2026-07-17.md) |
| **评审版本** | **v0.1.3 Draft** → Must-Fix 回写 **v0.2.0** |
| **日期** | 2026-07-17 |
| **结论** | **有条件通过（Conditional Go）** · MF 已回写 PRD v0.2.0 · **可 Kickoff W0（编码另排期；本轮仅文档）** |
| **参评角色** | 产品 · 交互/UI-UX · 用户体验 · 市场营销 · 运营 · 典型用户（分享者）· 开发 |
| **评审方式** | 分席只读评审（对照 PRD + 线框 + 三席润色 + FST/Help/FTUE 边界） |
| **记录人** | 产品 / UX / 市场 / 工程联合纪要（模拟跨职能评审） |
| **编码** | **本轮明确不动代码**；Kickoff 以 IMPLEMENTATION W0 另排期 |

---

## 1. 总评（一句话）

> **切口正确：用等待空档做 Outcome-first 教育，且明确非 L1，不与「忙碌态零 L1」冲突；三席润色后文案可挡 W0。阻塞在相邻 PRD 脚注、OQ 一字面冻结、以及验收/实施拆文对齐。MF 回写后标 Ready for Kickoff（编码）。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 填能力卡→FirstSuccess 空档；必须钉死「非 L1」与 FST 进度优先 |
| **交互 / UI-UX** | Conditional Go | F1 嵌壳层级清楚；弱视觉+可关是底线；F1/F3 作 W0 UI 挡门 |
| **用户体验** | Conditional Go | 宁可不出现，也不能抢「正在分章」；≥2s 延迟显现正确 |
| **市场营销** | Conditional Go | v0.1.3 隐私卡过关；禁止回退到「照片留在本机」当标题 |
| **运营** | Conditional Go | 无「主链」；选片/示例卡能降咨询；关闭持久化避免骚扰 |
| **用户 · 分享者** | Conditional Go | 等的时候看看可以，烦了要一秒关掉；别教我发微信 |
| **开发** | Conditional Go | W0 ≈ 1.5–2.5 人日；模块独立、静默降级；先脚注再编码 |

**汇总**：**七席一致 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go**。

---

## 3. 全场共识

1. **Wait Tips ≠ Help L1**：不写 Help seen；不脉冲；不挡取消。  
2. **进度主句绝对优先**：Tips 是次阅读；与 stage/estimate 同义复述禁止。  
3. **§4 v0.1.3（及回写后版本）六张为文案唯一源**；改字单点改 COPY 表。  
4. **隐私卡叙事冻结**：目的在标题，本机/不上传在正文；禁辩解腔。  
5. **本轮只做评审与文档回写**；编码 Kickoff 另排期。  
6. **长图 Dock 不做 Tips**（D-WT-09）本场确认。

---

## 4. Must-Fix（阻塞 Kickoff 编码 · 合入 PRD v0.2.0）

| ID | 议题 | 来源席位 | 要求 |
|----|------|----------|------|
| **BLK-01** | **Help 忙碌态脚注** | 产品 / Help | [PRD-HELP-ONBOARDING-V1](../PRD-HELP-ONBOARDING-V1.md)：D-HELP-08′ 增注——Importing 进度壳内允许 **非 L1** Wait Tips（[PRD-WAIT-TIPS-V1](../PRD-WAIT-TIPS-V1.md)）；仍禁止 coach/脉冲/tip |
| **BLK-02** | **FST 边界脚注** | 产品 / FST | [PRD-FIRST-SESSION-TRUST-V1](../PRD-FIRST-SESSION-TRUST-V1.md) §0.1：Wait Tips 可嵌 Importing 次区；**不改**阶段主句/慢安抚/FirstSuccess ≤1s |
| **BLK-03** | **FTUE 时段脚注** | 产品 / FTUE | [PRD-FTUE-OPTIMIZATION-V1](../PRD-FTUE-OPTIMIZATION-V1.md)：能力卡仅 idle；Importing 教育归 Wait Tips，二者不叠 |
| **BLK-04** | **OQ 一字面冻结** | 产品 / 交互 | OQ-WT-01～05 写入「已关闭」（见本纪要 §6） |
| **BLK-05** | **线框 F1/F3 = W0 UI 挡门** | 交互 | W0 合入前对照线框；F2 文案墙为 COPY 挡门 |
| **BLK-06** | **ACCEPTANCE / 手测清单拆文** | 开发 / QA | 本轮拆 [ACCEPTANCE-WAIT-TIPS-V1](../ACCEPTANCE-WAIT-TIPS-V1.md) + dogfood；IMPLEMENTATION 已有 |
| **BLK-07** | **文案版本钉死** | 市场 / 产品 | Kickoff 时 COPY 表字面 = PRD §4（v0.2.0）；契约单测锁禁区词 |

---

## 5. Should-Fix（不单独挡 Kickoff）

1. W2 帮助抽屉「重播等待提示」保持可选，不进 W0。  
2. 埋点 `wait_tips_*` 已在 IMPLEMENTATION §6；W0 最少 show/manual_nav/dismiss。  
3. 成功指标（关闭率等）编码后一周一看，不挡 Kickoff。  
4. 模板保留：[wait-tips-v1-review-TEMPLATE.md](./wait-tips-v1-review-TEMPLATE.md)。

---

## 6. OQ 拍板汇总（已关闭）

| OQ | 决议 |
|----|------|
| **OQ-WT-01** | dismiss 用 **localStorage** `travelogue.waitTips.dismissed`；不采用 session-only |
| **OQ-WT-02** | V1 **不按 stage 同步**卡片；进度主句独占阶段信息 |
| **OQ-WT-03** | V1 **纯文案 + 标签色**；禁止截图墙；极简符号非挡门 |
| **OQ-WT-04** | 短尾抑制归 **W1**（D-WT-07）；W0 可不做启发式，但 succeeded 必须立刻卸载 |
| **OQ-WT-05** | 默认 **不加**第 7 张「可离开」；estimate 行已覆盖 |

---

## 7. 线框对照签核

| 帧 | 挡门 | 结论 |
|----|------|------|
| **F1** 嵌进度壳 | W0 | **通过** · UI 合入挡门 |
| **F2** 文案墙 | W0 | **通过** · COPY 挡门（三席润色） |
| **F3** 交互 | W0 | **通过** · UI 合入挡门 |
| **F4** 仲裁 | W0 | **通过** · 非 L1 合同 |
| **F5** 禁止形态 | W0 | **通过** · 评审拒收清单 |

---

## 8. 人日粗估

| 波次 | 估时 |
|------|------|
| W0 | **1.5–2.5 人日** |
| W1 | **0.5–1 人日** |
| W2（可选） | **~0.5 人日** |

---

## 9. 与相邻主题挡门关系（本场确认）

| 主题 | 关系 | 确认 |
|------|------|------|
| First-Session Trust | Tips 嵌次区；进度/成功面合同不变 | ✅ |
| Help | 忙碌零 L1 仍成立；Tips 显式降级为非 L1 次内容 | ✅ |
| FTUE | 能力卡 idle；Importing 归 Tips | ✅ |
| Share-Ready / 精修 | 不做 | ✅ |

---

## 10. 下一步

- [x] Must-Fix 回写 PRD → **v0.2.0**  
- [x] 正式纪要本文  
- [x] 拆 ACCEPTANCE + dogfood  
- [x] Help / FST / FTUE 脚注  
- [x] 更新 README / IMPLEMENTATION 状态  
- [ ] **Kickoff W0 编码**（另排期 · 建议分支 `feat/wait-tips-v1-w0`）  

---

## 附录 · 材料包

| 材料 | 路径 |
|------|------|
| PRD v0.2.0 | [PRD-WAIT-TIPS-V1.md](../PRD-WAIT-TIPS-V1.md) |
| 实施 | [IMPLEMENTATION-WAIT-TIPS-V1.md](../IMPLEMENTATION-WAIT-TIPS-V1.md) |
| 验收 | [ACCEPTANCE-WAIT-TIPS-V1.md](../ACCEPTANCE-WAIT-TIPS-V1.md) |
| 手测 | [wait-tips-v1-dogfood-CHECKLIST.md](./wait-tips-v1-dogfood-CHECKLIST.md) |
| 线框 | [wait-tips-v1-wireframe.html](../wireframes/wait-tips-v1-wireframe.html) |
| 润色 | [wait-tips-v1-copy-workshop-2026-07-17.md](./wait-tips-v1-copy-workshop-2026-07-17.md) |
