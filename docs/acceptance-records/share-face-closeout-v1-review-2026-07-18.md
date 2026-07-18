# PRD-SHARE-FACE-CLOSEOUT-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-SHARE-FACE-CLOSEOUT-V1.md](../PRD-SHARE-FACE-CLOSEOUT-V1.md) |
| **线框** | [share-face-closeout-v1-wireframe.html](../wireframes/share-face-closeout-v1-wireframe.html) · F1–F5 |
| **验收 / 实施** | [ACCEPTANCE](../ACCEPTANCE-SHARE-FACE-CLOSEOUT-V1.md) · [IMPLEMENTATION](../IMPLEMENTATION-SHARE-FACE-CLOSEOUT-V1.md) |
| **试用底稿** | [persona-ux-trial-2026-07-18.md](./persona-ux-trial-2026-07-18.md) |
| **评审版本** | **v1.0.0 Draft** → Must-Fix 回写 **v1.0.1** |
| **日期** | 2026-07-18 |
| **结论** | **有条件通过（Conditional Go）** · Must-Fix 已回写 PRD v1.0.1 · **可 Kickoff W0（编码另开；本轮文档/设计）** |
| **编码** | **本轮明确不动代码**；Kickoff 以 IMPLEMENTATION W0 任务卡另排期 |
| **参评角色** | 产品 · 交互/UI-UX · 用户体验 · 典型用户（分享者 · 家庭组织者 · 轻度编辑者）· 架构 · 开发 |
| **评审方式** | 分席只读评审（对照 PRD + 线框 F1–F5 + 2026-07-18 八席试用 + 相邻：FST · Share-Ready · QH · Refine · Chapter Naming） |
| **记录人** | 产品 / UX / 工程联合纪要（模拟跨职能评审） |

---

## 0. 会前宣读（2 分钟）

1. **切口**：无 Key 不丢人 · 进度可解释 · 小册少打断 · 词表人话。  
2. **不做**：重做 Recipe/意图卡、真 LLM 气质、手机工坊、教微信怎么发。  
3. **修订声明**：本主题 **supersede** QH **R-QH-05** stale 一字面；**修订** Refine Sparse 路径下 G1 默认触发。  
4. **喜欢项保护**：杂志排版、配方 CTA、意图卡、示例试水、精修封面 — 本主题零行为回退（D-SFC-10）。

---

## 1. 总评（一句话）

> **试用切口对准「敢发」真断裂（假句/脏名/空进度），不是再堆功能；W0（F1–F3）可独立交付。阻塞在相邻合同脚注（QH stale 词、Refine G1、FST 禁词增量）、OQ 未冻结、以及 vision_warmup 必须有可测 AC。Must-Fix 回写后标 Ready for Kickoff（编码）。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 收口正确；stale 改名必须脚注 QH，避免两套主词 |
| **交互 / UI-UX** | Conditional Go | F1–F3 够挡 W0；F4 角标「分享图需更新」可读；F5 对照清楚 |
| **用户体验** | Conditional Go | 空进度=像坏了，优先于词表抛光；空优于假句不可松 |
| **用户 · 分享者** | Conditional Go | 6 张别拦我确认章节；告诉我在干什么就行 |
| **用户 · 家庭组织者** | Conditional Go | `东澳岛9` / `--` 上封面太丢人；回退名要真上书架 |
| **用户 · 轻度编辑者** | Conditional Go | 假句我改到烦；「媒资」可 W2，但别再冒新工程词 |
| **架构** | Conditional Go | vision_warmup 必须进 status 契约；失败降级不得整单 failed |
| **开发** | Conditional Go | W0 ≈ 2.5–4 人日；AC-SFC-04 要可注入/可测；先文档脚注 |

**汇总**：**八席一致 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go**。

---

## 3. 全场共识

1. **铁律可裁决**：空优于假句、体面名同源、忙碌必有主句、Sparse 少打断、词表人话。  
2. **W0 ≠ 主题完成**：W0=敢秀+不假死；W1=stale/G1/章名；W2=精修词表。  
3. **FST/Share-Ready 已合入底线不重造**：本主题补 fixture、未兑现路径与缺口合同。  
4. **Agent 试用不能替代真人**：完成宣布仍绑 AC-SFC-15。  
5. **本轮只做评审/文档回写**：编码 Kickoff 另排期。

**会中新增共识**：

- stale 改名全链路扫描进 W1 完成定义（防 Help 死链）。  
- `vision_warmup` 用户面只用「识图」，禁止 HF/CLIP/权重文件名。  
- 精细制作小册 **不**享受 Sparse 跳过 G1（OQ-02）。

---

## 4. Must-Fix（阻塞 Kickoff 编码 · 合入 PRD v1.0.1）

| ID | 议题 | 来源席位 | 要求 |
|----|------|----------|------|
| **BLK-01** | **QH stale 主词 supersede** | 产品 / 文档 | [PRD-STABLE-QUALITY-HARDENING-V1](../PRD-STABLE-QUALITY-HARDENING-V1.md) R-QH-05 增脚注：用户面唯一主词一字面以 Share-Face Closeout **D-SFC-06「分享图需更新」** 为准；QH「长图可更新」为历史统一阶段 |
| **BLK-02** | **Refine Sparse G1 例外** | 产品 / UX | [PRD-PREVIEW-REFINE-V1](../PRD-PREVIEW-REFINE-V1.md) D-REF-09/18 增脚注：`kept_n` 1–9 且快速分享默认不设 `structurePending`（实验选项可开）；精细制作除外 |
| **BLK-03** | **FST 禁词表增量指针** | UX / Trust | [PRD-FIRST-SESSION-TRUST-V1](../PRD-FIRST-SESSION-TRUST-V1.md) §4.5 声明 SFC §4.2 为同一禁词表增量（竖幅/弱枚举/标题复读）；禁止第三套平行表 |
| **BLK-04** | **OQ 正文冻结** | 产品 / 交互 | OQ-SFC-01～04 写入「已关闭」一字面（见本纪要 §6） |
| **BLK-05** | **线框 F1–F3 = W0 UI 挡门** | 交互 | W0 UI 合入前对照线框；F4–F5 随 W1 |
| **BLK-06** | **AC-SFC-04 可测锁** | 开发 / QA | Kickoff 时 IMPLEMENTATION 标明：vision_warmup 主句可见须有注入钩或 e2e；不得仅手测 |
| **BLK-07** | **AC/IMPL/狗粮已拆文确认** | 开发 | 文档包已存在；Kickoff 不重复拆文，只跟状态 |
| **BLK-08** | **喜欢项回归门** | 产品 | W0/W1 完成定义含 AC-SFC-NR-01/02（意图卡 / 按章导出） |

---

## 5. Should-Fix（不单独挡 Kickoff）

1. 埋点 `sfc_*` 写入 IMPLEMENTATION（已有索引，Kickoff 接入）。  
2. demo-album 重烘焙与假句清洗可与 W0 DATA-SFC-01 同批。  
3. W2「媒资」→「照片类型」不挡 W0/W1。  
4. 可选用户联席加厚（U6/U8）——本场已含分享者/家庭/编辑；不强制二场。  
5. OQ-SFC-04 存量批量写回保持可选，不进 W0 必做。

---

## 6. OQ 拍板汇总

| OQ | 决议 |
|----|------|
| **OQ-SFC-01** | `2025东澳岛9`：先去尾数字；若剩余为 2–6 字可读地名（如「东澳岛」）则用 `{地名} · 旅行`；否则回退 `旅行 · {日期范围}`。禁止裸尾数字目录腔上封面 |
| **OQ-SFC-02** | Sparse 跳过 G1 **仅**快速分享；**精细制作**即使 `kept_n≤9` 仍可 G1 |
| **OQ-SFC-03** | stale 唯一主词 = **「分享图需更新」**（不用「导出后再分享」作角标主词；后者可作副文） |
| **OQ-SFC-04** | 存量 trip：**读时计算** displayTitle 即可；批量写回非 W0 必做 |

---

## 7. 线框签核

| 帧 | 挡门 | 交互 | 产品 | 备注 |
|----|------|------|------|------|
| **F1** 识图准备主句 | W0 | ✅ | ✅ | 禁 HF 文件名 |
| **F2** 分享面空优于假句 | W0 | ✅ | ✅ | 与 BLK-03 联锁 |
| **F3** 体面名同源 | W0 | ✅ | ✅ | OQ-01 |
| **F4** stale 人话 | W1 | ✅ | ✅ | BLK-01 |
| **F5** Sparse G1 | W1 | ✅ | ✅ | BLK-02 · OQ-02 |

---

## 8. 代码对齐摘要（只读 · 本轮不改）

| 断言 | 现网（试用 2026-07-18） | 结论 |
|------|------------------------|------|
| stub「竖幅 / 抬头看见 / 夜景，白天」 | demo-album / 试用册可见 | **属实 · P0** |
| `武大--米娜` / `2025东澳岛9` 上封面 | 展示链未完全兑现 humanize/回退 | **属实 · P0** |
| import running phase/message 双空 | vision/HF 下载期间可复现 | **属实 · P0** |
| 「长图可更新」偏工程 | QH 已统一但仍吐槽 | **属实 · P1 · 改一字面** |
| Sparse 6 张弹 G1 | `qhtrial-p1-*` 可复现 | **属实 · P2** |
| Recipe CTA / 意图卡 | 试用喜欢项 | **保留 · 回归** |

**人日粗估**：W0 ≈ 2.5–4 人日；W1 ≈ 1.5–2.5 人日；W2 ≈ 0.3–0.5 人日。

---

## 9. 与相邻主题挡门关系

| 主题 | 本场确认 |
|------|----------|
| FST | 进度诚实 / 敢秀底线继承；禁词增量归同一表（BLK-03） |
| Share-Ready | 意图卡/`kept_n` 不抢；NR 回归门（BLK-08） |
| QH | stale **一字面**以本主题为准（BLK-01） |
| Refine | Sparse 快速分享默认跳过 G1（BLK-02） |
| Chapter Naming / Copy | 本主题挡「续」与假句；深度算法/润色仍归原轨 |
| Wait Tips | 次区教育；不替代 vision_warmup 主句 |

---

## 10. 决议与下一步

| 项 | 决议 |
|----|------|
| **结论** | **Conditional Go** |
| **PRD** | 回写 v1.0.1（OQ 关闭 + BLK 脚注完成） |
| **编码** | 本轮不动；Ready for Kickoff W0 |
| **分支建议** | `feat/share-face-closeout-v1-w0` |
| **完成宣布** | 仍须 AC-SFC-15 真人 N≥5 |

---

## 附录 · 会务记录

| 项 | 内容 |
|----|------|
| 会时 | 约 45 分钟（分席只读 + 表决 + OQ） |
| 材料 | PRD v1.0.0 · 线框 F1–F5 · ACCEPTANCE · IMPLEMENTATION · 试用底稿 |
| 缺席补读 | 可按本纪要 §0–§6 异步附议；异议须 24h 内提出 |
