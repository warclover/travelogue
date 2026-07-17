# PRD-SHARE-READY-OPTIMIZATION-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-SHARE-READY-OPTIMIZATION-V1.md](../PRD-SHARE-READY-OPTIMIZATION-V1.md) |
| **评审版本** | **v1.0.0 Draft** → Must-Fix 回写 **v1.0.1** |
| **日期** | 2026-07-17 |
| **结论** | **有条件通过（Conditional Go）** · Must-Fix 已回写 PRD v1.0.1 · **可 Kickoff W0（编码另开；本轮仅文档/设计）** |
| **跟进** | 线框 [share-ready-optimization-v1-wireframe.html](../wireframes/share-ready-optimization-v1-wireframe.html) · [ACCEPTANCE](../ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md) · [IMPLEMENTATION](../IMPLEMENTATION-SHARE-READY-OPTIMIZATION-V1.md) · Output Recipe 回写 §见 BLK-01 |
| **参评角色** | 产品 · 交互/UI-UX · 用户体验 · 典型用户（分享者 · 轻度编辑者）· 架构 · 开发 |
| **评审方式** | 分席只读评审（对照 PRD + 2026-07-17 本机走查实录 + 相邻合同：FTUE · Output Recipe · Help/Facade · L0 · Trust） |
| **记录人** | 产品 / UX / 工程联合纪要 |
| **编码** | **本轮明确不动代码**；Kickoff 编码以 IMPLEMENTATION W0 任务卡为准另排期 |

---

## 1. 总评（一句话）

> **切口正确、P0 可复现（意图卡被 DOM 估数跳过 + 首页 PLACEHOLDER 黑屏 + 工程句进分享面），W0 可独立交付；阻塞不在愿景，而在四处合同未钉死：① Output Recipe 未写明「客户端不得用 DOM 裁决 Band」；② OQ-SR-01～04 未在正文冻结；③ 成功面与 FTUE W1 联合挡门所有权需一句写清；④ 线框/验收/实施未齐。Must-Fix 回写后可标 Ready for Kickoff（编码）。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 排除海外 IG 正确；W0/W1/W2 完成定义可挡门；须回写 OR + 冻结 OQ |
| **交互 / UI-UX** | Conditional Go | 缺 F1/F2/F4 线框则 W0 UI 不可合入；CTA 缩短形用「发微信群」赞成 |
| **用户体验** | Conditional Go | 「敢发」对准分享者；工程泄漏与意图跳过同级严重；成功面必须与 FTUE 合流 |
| **用户 · 分享者** | Conditional Go | 要真图、要问怎么发、要成功后会发群；不要黑屏和说明书文案 |
| **用户 · 轻度编辑者** | Conditional Go | 工程 tip 可留在精修内；版心/Share 见到「雾底题签」会直接不想发 |
| **架构** | Conditional Go | `kept_n` 单一真相源必须服务端；DOM 估数降级为 hint；禁止双成功面栈 |
| **开发** | Conditional Go | W0 ≈ 2.5–3.5 人日（含 e2e 锁）；showcase 资产有烘焙路径即可；本轮先文档 |

**汇总**：**七席一致 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go**。

---

## 3. 全场共识

1. **铁律对**：真图样品、`kept_n` 权威、Ambiguous 必问、零工程泄漏、落盘≠完成、不做海外 IG——可裁决。  
2. **P-SR-01 是缺陷修复不是「新功能」**：API 已正确、UI 误判；W0 必须有 e2e「DOM 少图仍出意图卡」。  
3. **成功面不另起炉灶**：复用 FTUE §3.3 / Help / Task Dock；本主题 W1 与 FTUE W1 **联合挡门**。  
4. **W0 ≠ 主题完成**：W0=敢信；W1=敢选敢发；W2=敢秀（文案门槛）。  
5. **本轮只做评审/文档/设计**：编码 Kickoff 另排期，避免与文档回写抢序。

---

## 4. Must-Fix（阻塞 Kickoff 编码 · 合入 PRD v1.0.1）

| ID | 议题 | 来源席位 | 要求 |
|----|------|----------|------|
| **BLK-01** | **Output Recipe 合同回写** | 产品 / 架构 | 在 [PRD-OUTPUT-RECIPE-V1](../PRD-OUTPUT-RECIPE-V1.md) 增补决策：**客户端裁决 `needs_intent` / Band 必须以服务端 `kept_n`（或同源注入）为准；禁止单独用 DOM 估图数**。本主题 PRD §0.1 / §3.2 交叉引用该决策 ID。 |
| **BLK-02** | **OQ 正文冻结** | 产品 / 交互 | OQ-SR-01→缩短形「发微信群」；OQ-SR-02→允许降级 chat+toast；OQ-SR-03→书架保持 D-OR-16；OQ-SR-04→仅新导入改默认 title。写入 §3.8 / §12.3「已关闭」。 |
| **BLK-03** | **成功面联合挡门所有权** | 产品 / UX / 架构 | 正文写死：发群成功面 **合同所有者=FTUE+Help**；本主题 W1 Go **依赖** FTUE W1 同绿，**禁止**本主题实现第二套成功面。 |
| **BLK-04** | **线框 F1/F2/F4（+F3/F6）最低集** | 交互 | W0 UI 合入前对照线框；F5 可随 W1。 |
| **BLK-05** | **recipe API 失败冻结 COPY** | 交互 / 开发 | 降级 toast 唯一句：「暂时按微信群长图导出，可稍后重试选分享方式。」写入 §4 / §6。 |
| **BLK-06** | **showcase 资产归属** | 开发 / 文档 | 写明：默认替换 `templates/studio/assets/demo-showcase/`；推荐源 `trips/demo-album` 烘焙；刷新步骤入 WORKSHOP 或 templates README（DOC 任务，可 W0 文档波次）。 |
| **BLK-07** | **AC-SR-02 自动化锁** | 开发 / QA | IMPLEMENTATION 标明必做 e2e：`kept_n∈[10,30]` 且 DOM 槽位人为偏少 → 仍出意图卡。 |
| **BLK-08** | **泄漏词表单一扩展点** | UX / Trust | §4.4 声明为 FTUE §4.3 / Trust 的 **增量扩展**；禁止第三套平行禁词表。 |

---

## 5. Should-Fix（建议 v1.0.1 合入，不单独挡 Kickoff）

1. 埋点 `ambiguous_intent_skipped_illegal` 仅 debug / CI 告警，不进用户面。  
2. W2「旅途」隐藏策略与 Colophon「N 个地方」文案联动写一句，避免空 places 仍显示「1 个地方」。  
3. Dock 极窄断点（px）留给实现，线框只定文案优先级。  
4. 与 Refine S1 指针：本主题 AC 不替代 Refine 真人签。  
5. ACCEPTANCE 手测表增加「非作者签字」空栏（对齐 OR 先例）。

---

## 6. OQ 拍板汇总

| OQ | 决议 |
|----|------|
| **OQ-SR-01** | Dock 极窄 Sparse 缩短形 = **「发微信群」**（完整句 aria/tooltip） |
| **OQ-SR-02** | recipe API 失败 → **允许**降级微信群长图 + 冻结 toast（BLK-05） |
| **OQ-SR-03** | 书架 Ambiguous **不**升级强制意图卡（保持 D-OR-16）；预览内强制 |
| **OQ-SR-04** | title 可读化 **仅新导入默认**；`titleEdited` / 已有标题不覆盖 |
| **OQ-SR-05** | 已拆独立 ACCEPTANCE / IMPLEMENTATION；AC 以 ACCEPTANCE 为准、PRD §11 保留索引 |

---

## 7. 代码对齐摘要（架构 / 开发 · 只读，本轮不改）

| 断言 | 现网 | 结论 |
|------|------|------|
| Ambiguous API `needs_intent` | `ha-amb-18` → true · `kept_n=18` | 属实 |
| UI 跳过意图卡 | `startLongshotWithRecipe` 用 `estimatePhotoCountFromDom` | **属实 · P0** |
| 首页 PLACEHOLDER | `demo-showcase/**/*PLACEHOLDER*` · ~1×1 | **属实 · P0** |
| 工程 tip 进版心 | 「主体偏上，适合雾底题签」「已省略封底图」可见 | **属实 · P0** |
| Dock 可见「长图」vs aria 完整 CTA | aria 有、可见字短 | **属实 · P1** |
| 双长图入口 | Dock + 文内「保存长图」 | 属实；对齐 FTUE 降强调即可 |
| Output Recipe flag | `config.yaml` `enabled: true` | 狗粮环境已开 |

---

## 8. 与相邻主题挡门关系

```text
Share-Ready W0 ──独立──► showcase · kept_n 同源 · 泄漏拦截
Share-Ready W1 ──联合──► FTUE W1 成功面 / 发群三要素
Share-Ready W2 ──协同──► Copy / Chapter Naming（不阻塞 W0/W1）
Overseas IG ──不做──► 本主题全程排除
```

---

## 9. 建议狗粮脚本（编码后 · 非本轮）

1. 清缓存打开首页 → 样品非黑屏（F1）。  
2. 打开 `kept_n` 10–30 trip → 点长图 → 意图卡 N 正确（F2）。  
3. stale「长图可更新」→ 重导仍可问怎么发（F3）。  
4. Sparse → Dock 可见「发微信群」语义（F4）。  
5. 导出 → 进度人话 → 成功面发群句 ≥3s（F5）。  
6. 封面无雾底/省略句；精修内可有解释（F6）。

---

## 10. 签字

| 项 | 负责人 | 日期 | 结论 |
|----|--------|------|------|
| 分席评审 | 七席联合 | 2026-07-17 | **Conditional Go** |
| Must-Fix 回写 PRD v1.0.1 | 产品/文档 | 2026-07-17 | ✅ 本轮完成 |
| 线框 F1–F6 | 交互/文档 | 2026-07-17 | ✅ 本轮完成 |
| ACCEPTANCE / IMPLEMENTATION | 工程/文档 | 2026-07-17 | ✅ 本轮完成 |
| Output Recipe 合同回写 | 产品/文档 | 2026-07-17 | ✅ 本轮完成 |
| **编码 Kickoff** | — | — | **另排期 · 本轮不动代码** |
