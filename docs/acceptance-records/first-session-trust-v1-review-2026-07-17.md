# PRD-FIRST-SESSION-TRUST-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-FIRST-SESSION-TRUST-V1.md](../PRD-FIRST-SESSION-TRUST-V1.md) |
| **线框** | [first-session-trust-v1-wireframe.html](../wireframes/first-session-trust-v1-wireframe.html) · F1–F5 |
| **评审版本** | **v1.0.0 Draft** → Must-Fix 回写 **v1.0.1** |
| **日期** | 2026-07-17 |
| **结论** | **有条件通过（Conditional Go）** · Must-Fix 已回写 PRD v1.0.1 · **可 Kickoff W0（编码另开；本轮文档/设计）** |
| **跟进** | [用户联席](./first-session-trust-v1-user-panel-2026-07-17.md) · ACCEPTANCE / IMPLEMENTATION 可随 Kickoff 拆 |
| **参评角色** | 产品 · 交互/UI-UX · 用户体验 · 典型用户（分享者 · 轻度编辑者）· 架构 · 开发 |
| **评审方式** | 分席只读评审（对照 PRD + 线框 F1–F5 + 2026-07-17 CXO 空态实测 + 相邻：FTUE · Help · Share-Ready · Facade · Copy · Chapter Naming） |
| **记录人** | 产品 / UX / 工程联合纪要（模拟跨职能评审） |
| **编码** | **本轮明确不动代码**；Kickoff 以 IMPLEMENTATION W0 任务卡另排期 |

---

## 1. 总评（一句话）

> **切口对准可复现断裂（导入假死、成功面不稳、stub 不敢发），「不教微信」定案正确且应立刻回写 FTUE/Help/Share-Ready 以免合同漂移；W0（F1–F4）可独立交付，阻塞在文档交叉回写、终端切换 e2e 锁、以及 OQ 章名一字面未冻结。Must-Fix 回写后可标 Ready for Kickoff（编码）。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | §0.2 不教微信必须写进相邻 PRD；W0/W1 分门清楚 |
| **交互 / UI-UX** | Conditional Go | F1–F4 够挡 W0；F4 主操作「在文件夹中显示」权重要钉死 |
| **用户体验** | Conditional Go | 「像坏了」比「不会发微信」严重一个数量级；进度诚实是信任根 |
| **用户 · 分享者** | Conditional Go | 不要教程；告诉我存好了、文件在哪就行 |
| **用户 · 轻度编辑者** | Conditional Go | EXIF/文件夹名/「续」进封面我会直接不发；F5 不能再往后推没人管 |
| **架构** | Conditional Go | 终端态切换必须在当前轮询回调完成；禁止 await 书架刷新；不另起成功面栈 |
| **开发** | Conditional Go | W0 ≈ 2–3.5 人日（含 e2e）；W1 stub/EXIF/章名另估；先文档回写 |

**汇总**：**七席一致 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go**。

---

## 3. 全场共识

1. **铁律对**：进度诚实、终端 ≤1s、成功面停住且不教微信、敢秀底线、复用 Task Dock——可裁决。  
2. **§0.2 是产品定案不是可选项**：默认成功面禁止发群步骤教学；Help 仅按需。  
3. **W0 ≠ 主题完成**：W0=可等+成功确认；W1=敢秀；W2=封底抛光。  
4. **P-FST-01/02/03/04 属缺陷闭合**，不是新功能愿景。  
5. **本轮只做评审/文档回写**：编码 Kickoff 另排期。

---

## 4. Must-Fix（阻塞 Kickoff 编码 · 合入 PRD v1.0.1）

| ID | 议题 | 来源席位 | 要求 |
|----|------|----------|------|
| **BLK-01** | **FTUE 成功面合同回写** | 产品 / 文档 | [PRD-FTUE-OPTIMIZATION-V1](../PRD-FTUE-OPTIMIZATION-V1.md) §3.3 / G-FTUE-04 增脚注或修订段：默认成功面第一可读行以 First-Session Trust **D-FST-04** 为准（已保存）；发群教学句不再作为默认成功面合同 |
| **BLK-02** | **Help 发群说明降级** | 产品 / UX | [PRD-HELP-ONBOARDING-V1](../PRD-HELP-ONBOARDING-V1.md) 标明：`publishGuide` / 发群三要素为 **按需查阅**（H4/抽屉），**非**默认长图成功面强制槽位 |
| **BLK-03** | **Share-Ready「落盘≠完成」脚注** | 产品 / UX | [PRD-SHARE-READY-OPTIMIZATION-V1](../PRD-SHARE-READY-OPTIMIZATION-V1.md) 脚注：完成 = **稳定可见成功确认**；不含微信操作教学（与 D-FST-12 对齐） |
| **BLK-04** | **OQ 正文冻结** | 产品 / 交互 | OQ-FST-01～03 写入「已关闭」一字面（见本纪要 §6） |
| **BLK-05** | **成功面主操作权重** | 交互 / 用户 | F4：「在文件夹中显示」为成功面 **主操作**（实心/主色）；「关闭」次要；禁止只有文案没有强 CTA |
| **BLK-06** | **AC-FST-04 自动化锁** | 开发 / QA | Kickoff 时 IMPLEMENTATION 标明必做 e2e：示例导入 `succeeded` → FirstSuccess 可见且忙碌壳关闭（阈值 ≤1s 或同轮询） |
| **BLK-07** | **禁词表单一扩展点** | UX / Trust | §4.5 声明为 FTUE/Trust/Share-Ready 禁词表 **增量**；禁止第三套平行表 |
| **BLK-08** | **线框 F1–F4 W0 挡门** | 交互 | W0 UI 合入前对照线框；F5 随 W1 |

---

## 5. Should-Fix（建议合入，不单独挡 Kickoff）

1. 埋点 `import_ui_terminal_ms` / `longshot_success_visible_ms` 写入 IMPLEMENTATION。  
2. 拆独立 ACCEPTANCE / IMPLEMENTATION 文档（可与 W0 Kickoff 同批）。  
3. W2 Colophon / 张数同源与 Share-Ready W2 指针一句。  
4. 英文目录名噪音检测后置（OQ-FST-02 已冻结）。  
5. 用户联席 USR-* 见 [用户联席纪要](./first-session-trust-v1-user-panel-2026-07-17.md)。

---

## 6. OQ 拍板汇总

| OQ | 决议 |
|----|------|
| **OQ-FST-01** | 同日多章章名：**优先**「{日期} · {时段}」（上午/下午/傍晚/晚上）；无时段信号则「{日期}（2）」「{日期}（3）」；**禁止**「续」后缀 |
| **OQ-FST-02** | W1 文件夹名噪音检测 **仅中文启发式**；英文目录后置 |
| **OQ-FST-03** | stub/L0：**空优于假句**；与 Copy sparse 一致；不要求填满 hook |

---

## 7. 线框签核

| 帧 | 挡门 | 交互 | 产品 | 备注 |
|----|------|------|------|------|
| **F1** 导入进度诚实 | W0 | ✅ | ✅ | 慢安抚仅次行 |
| **F2** FirstSuccess ≤1s | W0 | ✅ | ✅ | 与 BLK-06 联锁 |
| **F3** 长图进度 | W0 | ✅ | ✅ | 禁假 0% |
| **F4** 已保存 · 不教微信 | W0 | ✅ | ✅ | BLK-05 主操作 |
| **F5** 敢秀对照 | W1 | ✅ | ✅ | 不挡 W0 Kickoff |

---

## 8. 代码对齐摘要（只读 · 本轮不改）

| 断言 | 现网（CXO 2026-07-17） | 结论 |
|------|------------------------|------|
| 导入 6/6 + 慢安抚僵持 | job `succeeded` 与忙碌壳并存可复现 | **属实 · P0** |
| FirstSuccess 切换 | 依赖刷新链，存在延迟/竞态 | **属实 · P0** |
| 长图「准备导出 0%」 | 可复现；后台可已落盘 | **属实 · P0** |
| 成功面不稳 | reveal 可能已调、面板不稳 | **属实 · P0** |
| stub /「日期续」/ EXIF / 文件夹封面名 | 示例+真实相册可见 | **属实 · P0/P1** |
| FTUE 仍写发群主句 | 文档合同与产品定案冲突 | **须 BLK-01 回写** |

**人日粗估**：W0 ≈ 2–3.5 人日；W1 ≈ 2–4 人日（含规则与单测）。

---

## 9. 与相邻主题挡门关系

| 主题 | 本场确认 |
|------|----------|
| FTUE | 空态/示例不变；成功面 COPY **以本主题为准**（BLK-01） |
| Help | 发群说明 **按需**（BLK-02） |
| Share-Ready | 真图/意图卡不抢；落盘完成定义脚注（BLK-03） |
| Copy / Chapter Naming | 本主题只定敢秀底线；章名一字面 §6 冻结后指针章名轨 |
| Export Facade | 复用 Task Dock；禁止第二套成功面 |

---

## 10. 下一步

1. ~~Must-Fix 回写 PRD v1.0.1~~（本纪要同步完成）  
2. 用户联席 USR 回写（见用户联席纪要 → PRD v1.0.2）  
3. DOC-FST-01～03：FTUE / Help / Share-Ready 交叉脚注（可与编码前文档波次同做）  
4. Kickoff W0 编码 + e2e（BLK-06）  
5. 主题对外宣布完成前：真人 N≥5（用户联席 USR）

---

## 11. 签字

| 席位 | 日期 | 结论 |
|------|------|------|
| 产品 · 交互 · UX · 分享者 · 轻度编辑 · 架构 · 开发 | 2026-07-17 | **Conditional Go**（模拟联评一致） |
| 主持 | 2026-07-17 | 附议 · Must-Fix 如上 |
