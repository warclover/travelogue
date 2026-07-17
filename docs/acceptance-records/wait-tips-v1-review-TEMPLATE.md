# PRD-WAIT-TIPS-V1 · 跨职能评审纪要（模板）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-WAIT-TIPS-V1.md](../PRD-WAIT-TIPS-V1.md) |
| **实施** | [IMPLEMENTATION-WAIT-TIPS-V1.md](../IMPLEMENTATION-WAIT-TIPS-V1.md) |
| **线框** | [wait-tips-v1-wireframe.html](../wireframes/wait-tips-v1-wireframe.html) · F1–F5 |
| **文案润色** | [wait-tips-v1-copy-workshop-2026-07-17.md](./wait-tips-v1-copy-workshop-2026-07-17.md) |
| **评审版本** | **v0.1.3 Draft** → Must-Fix 回写后升 **v0.x.x / v1.0.0**（填） |
| **日期** | YYYY-MM-DD（填） |
| **结论** | □ Go　□ **Conditional Go**　□ No-Go　（勾选） |
| **编码** | □ 本轮仅文档/设计　□ 可 Kickoff W0　（勾选） |
| **参评角色** | 产品 · 交互/UI-UX · 用户体验 · 市场营销 · 运营 · 典型用户（分享者）· 开发 |
| **评审方式** | 分席只读（PRD §2～§4 + 线框 F1–F5 + 三席润色纪要 + 相邻：FST · Help · FTUE） |
| **记录人** | （填） |

> **使用说明**  
> 1. 会前：只读 PRD 铁律 / §3 / §4 六张文案 + 线框 F1（嵌壳）/ F2（文案）/ F4（仲裁）。  
> 2. 会中：§2 分席表决 → §4 Must-Fix → §6 拍板 OQ。  
> 3. 会后：另存 `wait-tips-v1-review-YYYY-MM-DD.md`；MF 回写 PRD 后再改结论行。

---

## 0. 会前必读（主持人 · 2 分钟）

1. **切口**：导入等待壳内可关闭教育 · Outcome-first · **非 L1**。  
2. **已定案（勿重开结构）**：嵌 Importing 次区；进度主句优先；不教微信/精修；长图 Dock 不做。  
3. **文案**：以三席润色 v0.1.3 为唯一字符串源；隐私卡目的在标题、手段在正文。  
4. **本轮默认不动代码**（除非勾选可 Kickoff W0）。

---

## 1. 总评（一句话）

> （会后填：是否值得做？会不会抢进度？文案是否过关？W0 能否独立交付？）

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | □ Go / □ CG / □ No | |
| **交互 / UI-UX** | □ Go / □ CG / □ No | |
| **用户体验** | □ Go / □ CG / □ No | |
| **市场营销** | □ Go / □ CG / □ No | |
| **运营** | □ Go / □ CG / □ No | |
| **用户 · 分享者** | □ Go / □ CG / □ No | |
| **开发** | □ Go / □ CG / □ No | |

**汇总**：_/_ 席 · 结论 ______ · 未回写 MF 前 □ 不批无条件 Go

---

## 3. 全场共识（预填 · 可改）

1. Tips ≠ Help L1；不写 Help seen。  
2. 进度诚实仍归 FST；Tips 失败时进度壳须完整。  
3. §4 六张为 W0 文案挡门；改字走 COPY 单点。  
4. W0 ≠ 主题完成；W1=短尾/reduced-motion；W2=重播可选。  
5. 本轮默认只做评审/文档。

**会中新增**：

- …

---

## 4. Must-Fix（阻塞 Kickoff · 候选）

| ID | 议题 | 来源 | 要求 | 状态 |
|----|------|------|------|------|
| **BLK-01** | Help「忙碌态零 L1」脚注 | 产品 / Help | 标明 Wait Tips = 进度壳**次内容**，非 coach/脉冲 | □ |
| **BLK-02** | FST 边界脚注 | 产品 / FST | Importing 次区可挂 Tips；不改 stage/慢安抚/FirstSuccess | □ |
| **BLK-03** | OQ-WT 冻结 | 产品 | OQ-01～05 写入已关闭一字面 | □ |
| **BLK-04** | 线框 F1/F3 = W0 UI 挡门 | 交互 | 合入前对照 | □ |
| **BLK-05** | ACCEPTANCE 拆文 | 开发 / QA | 本轮是否拆独立验收 | □ |
| **BLK-06** | （会中新增） | | | □ |

---

## 5. Should-Fix

1. FTUE 脚注：能力卡 → Importing Tips 时段错开。  
2. 埋点进 IMPLEMENTATION（已有草案则核对）。  
3. （会中新增）…

---

## 6. OQ 拍板表

| OQ | PRD 倾向 | 本场决议 | 写入 |
|----|----------|----------|------|
| **OQ-WT-01** | localStorage dismiss | （填） | §5 |
| **OQ-WT-02** | V1 不按 stage 同步卡 | （填） | §3 / §10 |
| **OQ-WT-03** | V1 纯文案+标签色 | （填） | §3 |
| **OQ-WT-04** | 短尾 D-WT-07 | （填） | W1 |
| **OQ-WT-05** | 默认不加第 7 张「可离开」 | （填） | §4 |

---

## 7. 线框对照签核

| 帧 | 挡门 | 交互签 | 产品签 | 市场签 | 备注 |
|----|------|--------|--------|--------|------|
| **F1** 嵌进度壳 | W0 | □ | □ | — | |
| **F2** 文案墙 | W0 | □ | □ | □ | 关键 |
| **F3** 交互 | W0 | □ | □ | — | |
| **F4** 仲裁 | W0 | □ | □ | — | 非 L1 |
| **F5** 禁止形态 | W0 | □ | □ | — | |

---

## 8. 人日粗估（开发）

W0 ≈ ____ 人日 · W1 ≈ ____ 人日 · W2（可选）≈ ____ 人日

---

## 9. 下一步（勾选）

- [ ] Must-Fix 回写 PRD → 版本 ____  
- [ ] 另存正式纪要 `wait-tips-v1-review-YYYY-MM-DD.md`  
- [ ] 更新 docs/README 状态行  
- [ ] 拆/更新 ACCEPTANCE · IMPLEMENTATION  
- [ ] Kickoff W0 编码排期：____  

---

## 附录 · 会前材料包

| 材料 | 路径 |
|------|------|
| PRD | [PRD-WAIT-TIPS-V1.md](../PRD-WAIT-TIPS-V1.md) |
| 实施 | [IMPLEMENTATION-WAIT-TIPS-V1.md](../IMPLEMENTATION-WAIT-TIPS-V1.md) |
| 线框 | [wait-tips-v1-wireframe.html](../wireframes/wait-tips-v1-wireframe.html) |
| 文案润色 | [wait-tips-v1-copy-workshop-2026-07-17.md](./wait-tips-v1-copy-workshop-2026-07-17.md) |
| 相邻 | [PRD-FIRST-SESSION-TRUST-V1](../PRD-FIRST-SESSION-TRUST-V1.md) · [PRD-HELP-ONBOARDING-V1](../PRD-HELP-ONBOARDING-V1.md) · [PRD-FTUE-OPTIMIZATION-V1](../PRD-FTUE-OPTIMIZATION-V1.md) |
