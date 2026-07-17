# PRD-FIRST-SESSION-TRUST-V1 · 跨职能评审纪要（模板）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-FIRST-SESSION-TRUST-V1.md](../PRD-FIRST-SESSION-TRUST-V1.md) |
| **线框** | [first-session-trust-v1-wireframe.html](../wireframes/first-session-trust-v1-wireframe.html) · F1–F5 |
| **评审版本** | **v1.0.0 Draft** → Must-Fix 回写后升 **v1.x.x**（填） |
| **日期** | YYYY-MM-DD（填） |
| **结论** | □ Go　□ **Conditional Go**　□ No-Go　（勾选） |
| **编码** | □ 本轮仅文档/设计　□ 可 Kickoff W0　（勾选） |
| **跟进** | ACCEPTANCE / IMPLEMENTATION（评审后拆否：□ 是 □ 否） |
| **参评角色** | 产品 · 交互/UI-UX · 用户体验 · 典型用户（分享者 · 轻度编辑者）· 架构 · 开发 |
| **评审方式** | 分席只读评审（对照 PRD + 线框 F1–F5 + 2026-07-17 CXO 空态实测 + 相邻：FTUE · Help · Share-Ready · Facade · Copy · Chapter Naming） |
| **记录人** | （填） |

> **使用说明**  
> 1. 会前：参评人只读 PRD §0.2 / §2 / §3 + 线框 F1–F4（W0）/ F5（W1）。  
> 2. 会中：按 §2 分席表决 → §4 收 Must-Fix → §6 拍板 OQ。  
> 3. 会后：把本模板另存为 `first-session-trust-v1-review-YYYY-MM-DD.md`，删「模板」字样；Must-Fix 回写 PRD 后再改结论行。

---

## 0. 会前必读（主持人宣读 · 2 分钟）

1. **本主题切口**：进度不假死 · 成功面必出 · 分享面敢秀。  
2. **产品已定案（勿重开）**：**默认成功面不教微信怎么发**；用户熟练微信；成功面 = 已保存 + 打开文件夹。  
3. **不做**：空态/示例入口（FTUE）、真图样品/意图卡（Share-Ready）、Installer、杂志级深润色。  
4. **修订声明**：本主题 **supersede** FTUE §3.3「发群主句第一可读行」——评审须明确同意或提出替代，不得沉默漂移。

---

## 1. 总评（一句话）

> （会后填写：切口是否对准实测断裂？W0 能否独立交付？最大阻塞是什么？）

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | □ Go / □ CG / □ No | |
| **交互 / UI-UX** | □ Go / □ CG / □ No | |
| **用户体验** | □ Go / □ CG / □ No | |
| **用户 · 分享者** | □ Go / □ CG / □ No | |
| **用户 · 轻度编辑者** | □ Go / □ CG / □ No | |
| **架构** | □ Go / □ CG / □ No | |
| **开发** | □ Go / □ CG / □ No | |

**汇总**：_/_ 席 · 结论 ______ · 未回写 Must-Fix 前 □ 不批无条件 Go

---

## 3. 全场共识（预填 · 会中可改）

1. **铁律可裁决**：进度诚实、终端态 ≤1s、成功面停住且不教微信、分享面敢秀、不另起成功面栈。  
2. **W0 ≠ 主题完成**：W0=可等+成功确认；W1=敢秀底线；W2=封底抛光。  
3. **成功面 COPY 唯一**：§4.4「长图已保存」；Help 发群说明降为按需查阅。  
4. **与 FTUE/Share-Ready 挡门**：文档交叉回写必须进 Must-Fix（见 BLK 候选）。  
5. **本轮默认不动代码**（除非结论勾选可 Kickoff W0）。

**会中新增共识**：

- …

---

## 4. Must-Fix（阻塞 Kickoff · 候选清单 · 会中增删）

| ID | 议题 | 来源席位 | 要求 | 状态 |
|----|------|----------|------|------|
| **BLK-01** | FTUE §3.3 / G-FTUE-04 交叉回写 | 产品 / 文档 | 标明发群主句合同以 First-Session Trust D-FST-04/05/12 为准 | □ |
| **BLK-02** | Share-Ready「落盘≠完成」脚注 | 产品 / UX | 完成=稳定成功确认，非微信教学 | □ |
| **BLK-03** | Help：发群说明改为按需查阅 | 产品 / Help | 默认成功面不强制 `publishGuide` | □ |
| **BLK-04** | 线框 F1–F4 为 W0 UI 挡门 | 交互 | 合入前对照线框；F5 随 W1 | □ |
| **BLK-05** | AC / IMPLEMENTATION 是否本轮拆文 | 开发 / QA | 拍板：拆独立文档 or PRD §10 暂充 | □ |
| **BLK-06** | （会中新增） | | | □ |

---

## 5. Should-Fix（不单独挡 Kickoff）

1. 埋点 `import_ui_terminal_ms` / `longshot_success_visible_ms` 进 IMPLEMENTATION。  
2. OQ-FST-02 英文目录名回退后置。  
3. W2 Colophon / 张数同源与 Share-Ready W2 指针一句。  
4. （会中新增）…

---

## 6. OQ 拍板表

| OQ | PRD 倾向 | 本场决议 | 写入 |
|----|----------|----------|------|
| **OQ-FST-01** | 同日多章：「{日期} · 时段」；无时段「{日期}（2）」；禁「续」 | （填） | §3.5 / §11 |
| **OQ-FST-02** | W1 仅中文噪音启发式 | （填） | §3.5 |
| **OQ-FST-03** | stub 空优于假句 | （填） | §3.5 / Copy 指针 |
| **OQ-FST-?** | （会中新增） | | |

---

## 7. 线框对照签核

| 帧 | 挡门 | 交互签 | 产品签 | 备注 |
|----|------|--------|--------|------|
| **F1** 导入进度诚实 | W0 | □ | □ | |
| **F2** FirstSuccess ≤1s | W0 | □ | □ | |
| **F3** 长图进度无假 0% | W0 | □ | □ | |
| **F4** 已保存 · 不教微信 | W0 | □ | □ | **关键修订帧** |
| **F5** 敢秀对照 | W1 | □ | □ | |

---

## 8. 代码对齐摘要（架构 / 开发 · 只读，会前可预填）

| 断言 | 现网观察（预填自 CXO 2026-07-17） | 会中确认 |
|------|-----------------------------------|----------|
| 导入 6/6 后慢安抚僵持 | 属实（忙碌壳 vs job succeeded） | □ 属实 □ 已变 |
| FirstSuccess 切换延迟 | 属实 / 竞态风险 | □ |
| 长图「准备导出 0%」 | 属实 | □ |
| 成功面不稳 / 教学句合同 | FTUE 仍写发群主句；产品要修订 | □ |
| stub 说明书腔 /「日期续」/ EXIF / 文件夹封面名 | 属实（示例+真实相册） | □ |

**人日粗估（开发填）**：W0 ≈ ____ 人日 · W1 ≈ ____ 人日

---

## 9. 与相邻主题挡门关系（会中确认）

| 主题 | 关系 | 确认 |
|------|------|------|
| FTUE | 本主题修订成功面 COPY；空态/示例不变 | □ |
| Help | 发群说明降为按需 | □ |
| Share-Ready | 真图/意图卡不抢；成功面不另起栈 | □ |
| Copy / Chapter Naming | 本主题只定敢秀底线 | □ |
| Export Facade | 复用 Task Dock | □ |

---

## 10. 下一步（勾选）

- [ ] Must-Fix 回写 PRD → 版本 ____  
- [ ] 另存正式纪要 `first-session-trust-v1-review-YYYY-MM-DD.md`  
- [ ] 更新 [docs/README.md](../README.md) 状态行  
- [ ] 拆 `ACCEPTANCE-FIRST-SESSION-TRUST-V1.md` / `IMPLEMENTATION-…`  
- [ ] Kickoff W0 编码排期：____  
- [ ] 狗粮：空态示例导入 + 长图成功面 N≥5

---

## 附录 · 会前材料包

| 材料 | 路径 |
|------|------|
| PRD | [PRD-FIRST-SESSION-TRUST-V1.md](../PRD-FIRST-SESSION-TRUST-V1.md) |
| 线框 | [first-session-trust-v1-wireframe.html](../wireframes/first-session-trust-v1-wireframe.html) |
| 触发实测 | PRD 附录 A · CXO 2026-07-17 |
| 被修订合同 | [PRD-FTUE-OPTIMIZATION-V1.md](../PRD-FTUE-OPTIMIZATION-V1.md) §3.3 · [PRD-HELP-ONBOARDING-V1.md](../PRD-HELP-ONBOARDING-V1.md) 发群兜底 · [PRD-SHARE-READY-OPTIMIZATION-V1.md](../PRD-SHARE-READY-OPTIMIZATION-V1.md) 落盘≠完成 |
