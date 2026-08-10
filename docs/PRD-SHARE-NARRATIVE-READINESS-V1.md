# Travelogue · 敢发叙事就绪 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.1.0** |
| **状态** | **Draft · 线框 F1–F8 已签核 · W0 编码中** |
| **DOC-STATUS** | **active** |
| **主题代号** | 「敢发叙事就绪」— **SNR**（Share Narrative Readiness） |
| **触发来源** | [2026-08-10 十席 Persona 试用](./acceptance-records/persona-feedback-trial-2026-08-10.md)（Agent 模拟联评 + 全库扫描）；交叉对照 SFP / SFI / SAS / AIR / Chapter Naming |
| **前置条件** | 首页 v2（M21）；SFC / SFI / SFP 敢发净化合同已落地（脏题名/序号腔清零）；预览 Dock v4；[SAS](./PRD-STUDIO-AI-SURFACE-V1.md) AI Sheet 已合入；[NAS](./PRD-NO-AI-SURFACE-V1.md) 门控仍有效 |
| **关联文档** | [PRD-SHARE-FACE-PURITY-V1.md](./PRD-SHARE-FACE-PURITY-V1.md) · [PRD-SHARE-FACE-INTEGRITY-V1.md](./PRD-SHARE-FACE-INTEGRITY-V1.md) · [PRD-SHARE-FACE-CLOSEOUT-V1.md](./PRD-SHARE-FACE-CLOSEOUT-V1.md) · [PRD-STUDIO-AI-SURFACE-V1.md](./PRD-STUDIO-AI-SURFACE-V1.md) · [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md) · [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md) · [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) · [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [CHARTER.md](./CHARTER.md) O2/O3 |
| **评审记录** | 待补（七席+典型用户） |
| **验收** | [ACCEPTANCE-SHARE-NARRATIVE-READINESS-V1.md](./ACCEPTANCE-SHARE-NARRATIVE-READINESS-V1.md)（§10 为源） |
| **实施清单** | [IMPLEMENTATION-SHARE-NARRATIVE-READINESS-V1.md](./IMPLEMENTATION-SHARE-NARRATIVE-READINESS-V1.md) |
| **线框** | [wireframes/share-narrative-readiness-v1-wireframe.html](./wireframes/share-narrative-readiness-v1-wireframe.html)（**F1–F8 已签核 2026-08-10**） |
| **试用底稿** | [persona-feedback-trial-2026-08-10.md](./acceptance-records/persona-feedback-trial-2026-08-10.md) |
| **更新日期** | 2026-08-10 |

> **定位（首席 UX / 设计视角）**
>
> 08-10 试用证明：用户已经愿意**打开、导出、相信本地隐私**；真正阻断「原样发出去」的，不再是脏题名或说明书腔假句，而是**成片读起来像半成品**——整册无导语、章名只剩日期、偶然冒出「2015」往年戳、AI 明明「可生成」却看不出变了什么、Dock 还挡住关闭钮。  
> 本主题把 SFP「空优于假句」**升维**为「**空要诚实，可读要够格**」：不复活流水账 stub，但必须给成片一个**可读姿态**（纯照片 / 可升级 / 已杂志感），并把 AI 生成、导出 CTA、浮层互斥等交互债一次收口。
>
> **一句话目标**：用户打开任意成册，**30 秒内**判断「这本能不能发」；若不能，知道**点哪里补一句故事**；补完后**看得见变了什么**；全程不被浮层与工程词绊倒。
>
> **产品铁律**
>
> 1. **空优于假句** — 继承 D-SFP-05/06；禁止「白天，傍晚」「旅行照片」式敷衍上长图文字层。  
> 2. **空必须诚实** — 整册无叙事时，必须有**可读姿态徽标/提示**，不得假装「杂志文案已完成」。  
> 3. **薄优于无结构** — 章名在无 AI 时可用「地点 · 时段 / 场景短标」升维，仍禁止序号腔与编造地名。  
> 4. **点按才烧额度** — 继承 SAS / AIR；生成后必须有**可见 diff**。  
> 5. **一层浮层** — 扩展 D-SFP-10 / D-SAS-04：AI ↔ 导出 ↔ 分章 ↔ 精修互斥；关闭钮永可点。  
> 6. **喜欢项零回退** — 六平台导出、清晰度像素、窄屏 gate、脏题名清零、AI「不自动消耗」文案不得倒退。  
> 7. **Fail-open** — 叙事增强失败 = 回退到诚实空态，不影响导出长图。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语 |
| §0.2 | 与相邻主题边界（尤其 SFP「lead 空合法」如何升维） |
| §1 | 试用结论、问题清单、根因树 |
| §2 | 目标 / 非目标 / 成功指标 |
| §3 | 冻结决策 D-SNR-* |
| §4 | 分域方案（逐槽点 C1–C8） |
| §5 | 文案 COPY-SNR-* |
| §6 | 工程任务索引 |
| §7 | 错误与降级 |
| §8 | 埋点 |
| §9 | 非功能 |
| §10 | 里程碑 |
| §11 | 验收 AC 索引 |
| §12 | 风险与开放问题 |
| 附录 | 试用映射 · 版本记录 |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **叙事姿态 `narrativePosture`** | 成册级可读状态枚举：`photo_led`（纯照片）/ `upgrade_ready`（可一键升杂志感）/ `narrative_ready`（已有合格版心叙事） |
| **薄章名** | 无 LLM 时的章名升维：地点短标 · 时段 · 场景词；仍可含日期，但**禁止**整册仅裸日期且无区分信号 |
| **可见 diff** | AI 生成/换语气完成后，用户能指出「改了哪些槽位」的摘要条 + 可选跳转 |
| **金色主 CTA** | 预览 Dock 导出主按钮；必须用人话平台名，不得仅显示「N 个模式」 |
| **往年泄漏** | 单张照片 EXIF 年份与行程年差过大，仍以精确年份出现在读者面图注/高光角标 |

### 0.2 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [SFP · 敢发净化](./PRD-SHARE-FACE-PURITY-V1.md) | **继承并升维** | 继承空优于假句 / 序号腔禁令 / 浮层互斥；**修订**「整册 lead 全空可无解释」——见 **D-SNR-01**（扩展而非废除 D-SFP-06） |
| [SFI · 敢发完整性](./PRD-SHARE-FACE-INTEGRITY-V1.md) | **硬化执行** | 离群年/跨年策略落地到**图注与高光角标**（C3），不只章序 |
| [SAS · AI Surface](./PRD-STUDIO-AI-SURFACE-V1.md) | **硬化交互 + 补 diff** | 互斥扩展到导出设置；关闭命中区；生成后 diff 归本主题 **F-SNR-04**；不重做 Sheet IA |
| [AIR · AI Return](./PRD-AI-RETURN-V1.md) | **消费出口** | 杂志文案质量 / 三语气 / 渠道包算法仍归 AIR；本主题规定**何时填 body**、**姿态如何切换** |
| [Chapter Naming](./PRD-CHAPTER-NAMING.md) | **修订薄章名合同** | 本主题拥有「无 AI 薄章名优先级」（D-SNR-03）；脚注指针 Kickoff 前落入 Chapter Naming |
| [NAS · 无 AI 面](./PRD-NO-AI-SURFACE-V1.md) | **遵守门控** | `aiSurfaceEnabled=false` 时：不出现「生成杂志感」主路径；仍交付 `photo_led` 诚实姿态 + 薄章名 + 导出 CTA |
| [Output Recipe / Export Facade](./PRD-OUTPUT-RECIPE-V1.md) | **CTA 文案硬化** | 配方分流不变；本主题只改 **Dock 主钮可见文案**（C8） |
| 影楼批量 / 移动端成册 | **不做** | 范围外 |

**对 D-SFP-06 的正式关系**：

> D-SFP-06「单章 lead 空合法」**仍然成立**。  
> D-SNR-01 新增：**成册级**不得对用户隐瞒「这是一本纯照片册」；且当存在可升级路径时必须可见。  
> 验收不得再把「49/49 lead 空」单独判 PASS——必须同时满足姿态诚实（AC-SNR-01）。

---

## 1. 背景与问题

### 1.1 试用方法（可复现）

| 项 | 约定 |
|----|------|
| **环境** | Windows · Studio `8766` · AI Surface ON |
| **样片** | 15 本书架 · `demo-album` · `demo-20ecc928d6` |
| **扫描** | chapters=49 · empty_leads=49 · alt_旅行照片=1338 · dirty_titles=0 |
| **性质** | Agent 模拟；真人 N≥5 仍待补签 |

### 1.2 问题清单（本主题认领）

| 试用 ID | 本主题 ID | 严重度 | 用户感知 | 认领 |
|---------|-----------|--------|----------|------|
| C1 | **P-SNR-01** | P0 | 「像半成品，没故事」 | ✅ |
| C2 | **P-SNR-02** | P0 | 「章名全是日期，分不清」 | ✅ |
| C3 | **P-SNR-03** | P0 | 「2015 怎么出现在这趟」 | ✅ |
| C4 | **P-SNR-04** | P1 | 「可生成但点了像没变 / 还没生成」 | ✅ |
| C5 | **P-SNR-05** | P1 | 「AI 关不掉」 | ✅ |
| C6 | **P-SNR-06** | P1 | 「面板叠在一起」 | ✅ |
| C7 | **P-SNR-07** | P2 | 「文案包正文还是空的」 | ✅ |
| C8 | **P-SNR-08** | P2 | 「2 个模式是啥」 | ✅ |

### 1.3 核心判断

> 上一代敢发主题（SFC/SFI/SFP）成功把「出糗字符串」清出读者面；副作用是**安全的空**铺满了版心。  
> 用户对空的容忍度取决于**是否读得懂产品意图**：若标明「纯照片成册」，空是克制；若封面书法很满、章导语却全无，空就是缺陷。  
> 系统性解法 = **姿态合同 + 薄结构升维 + AI 闭环可见 + 浮层/CTA 工程债**，禁止只改一两本文案或只洗样片。

### 1.4 根因树

```text
敢发受阻（叙事就绪）
├─ 成片像半成品
│  ├─ P-SNR-01 整册 lead 空 + alt 旅行照片
│  │    ├─ frame/sparse 合同清空 lead（正确）但无成册姿态说明
│  │    └─ alt 技术回退泄漏进读者感知 / 部分导出面
│  └─ P-SNR-02 章名日期腔
│       └─ 无 AI 时 chapter_titles 过早停在日期；地点/场景短标未优先
├─ 时间可信度崩
│  └─ P-SNR-03 往年 EXIF 上高光/图注
│       └─ 有跨年章序策略，缺「单张年份离群」读者面抑制
├─ AI 闭环断感
│  └─ P-SNR-04 状态「可生成」与预览空并存；生成后无 diff
├─ 交互工程债
│  ├─ P-SNR-05 AI × 命中区被 Dock caret 拦截（z / hit-test）
│  └─ P-SNR-06 AI Sheet 未纳入导出互斥集合
└─ 出口半成品
   ├─ P-SNR-07 有杂志文案时仍不填 shareCopyPack.body
   └─ P-SNR-08 Dock 主钮优先显示「N 个模式」而非平台人话名
```

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-SNR-01** | 每本成册有明确 **narrativePosture**；用户 30 秒内读懂「纯照片 / 可升级 / 已杂志感」 |
| **G-SNR-02** | 无 AI 时章名达到**薄可读**：同册多章不得「仅裸日期且无法区分」；优先地点·时段·场景短标 |
| **G-SNR-03** | 读者面 / 长图文字层 **零**「旅行照片」可见字样；alt 用更具体回退或不进文字层 |
| **G-SNR-04** | 往年泄漏：高光角标/图注不得无解释地展示离群年份 |
| **G-SNR-05** | AI 生成杂志文案后，**必现** diff 摘要（改了哪些槽）；状态从「可生成」正确切到「已是杂志文案」 |
| **G-SNR-06** | AI × / Esc / 再点 Dock「AI」均可关闭；命中不被 Dock 遮挡 |
| **G-SNR-07** | 同时最多一层主浮层：AI ↔ 导出设置 ↔ 分章 ↔ 精修 |
| **G-SNR-08** | 小红书等渠道：有版心叙事时文案包 body **可一键带出**；无则保持诚实空说明 |
| **G-SNR-09** | Dock 金色主 CTA **人话平台名**（如「导出小红书」）；多选时主文案仍可读 |

### 2.2 非目标

| 不做 | 理由 |
|------|------|
| 复活「白天，傍晚」类 stub 假句 | 与 SFP / CHARTER 气质冲突 |
| 强制每章都有文艺 lead（无 Key） | 违背空优于假句；无信号时保持 `photo_led` |
| 重写 narrate Prompt / 三语气算法 | 归 AIR |
| 重做 AI Sheet 信息架构 | 归 SAS；本主题只补 diff / 互斥 / 关闭 |
| 影楼批量、手机完整工坊 | 范围外 |
| 仅手洗样片充验收 | 必须改生成/渲染/Dock 主路径 |

### 2.3 成功指标（狗粮向）

| 指标 | 门槛 |
|------|------|
| 抽样 5 本成册均有可见姿态（徽标或预览条） | **5/5** |
| 同册 ≥3 章且无 AI：裸日期且无区分信号的章占比 | **≤30%**（或全部有时段/地点短标） |
| 长图 OCR / 文字层含「旅行照片」 | **0** |
| 武大类样片高光角标无解释「2015」 | **0**（抑制或改「往年」） |
| AI 生成后 diff 条出现且可关闭 | **1 次操作可见** |
| AI × 一次点中 | **100%**（自动化） |
| 打开导出设置时 AI Sheet 已关 | **100%** |
| 金色 CTA 不含孤立「N 个模式」作主文案 | **抽检 0** |
| 契约 | SFP / SAS 相关自动化不回退 |

---

## 3. 体验合同与冻结决策（D-SNR-*）

| ID | 决策 | 合同要点 |
|----|------|----------|
| **D-SNR-01** | **成册叙事姿态** | 每册计算 `narrativePosture ∈ {photo_led, upgrade_ready, narrative_ready}`。规则见 §4.1。预览顶栏或卷轴首屏附近展示**一条**姿态信号（徽标或轻提示），不得同时堆 ≥2 条主提示。 |
| **D-SNR-02** | **扩展而非废除 D-SFP-06** | 单章 lead 空仍合法；**整册**若 `photo_led`，必须诚实标注；若 `upgrade_ready`，必须露出「生成杂志感文案」捷径（AI Surface ON 且 Key 就绪时指向 AI Sheet；否则指向配置/帮助，禁止假按钮）。 |
| **D-SNR-03** | **无 AI 薄章名优先级** | 最终章名生成序：① 用户手改（`titleOrigin=user`）② 可用地点短标（±时段）③ 场景短标（非复读）④ 日期±时段 ⑤ 同名日期（靠 01/02）。**禁止**序号腔（继承 D-SFP-01）。禁止编造未证实地名。 |
| **D-SNR-04** | **「旅行照片」禁入文字层** | `alt` 可用内部回退，但**长图 / 卷轴可见 caption / 分享面**不得出现「旅行照片」。可见层无合格信号 → **空**。新 alt 优先：地点 · 时段 · 「照片」中性词 · 空。 |
| **D-SNR-05** | **往年泄漏抑制** | 定义离群：`abs(photoYear - tripPrimaryYear) ≥ 2`（或相对行程中位年）。高光角标/自动图注：**省略年份**或改「往年 · 时段」；「为什么这样分章」可解释「含往年照片」。用户手改图注不覆盖。 |
| **D-SNR-06** | **生成后可见 diff** | 杂志文案 / 换语气成功 → 非模态摘要条（≤2 行）：列出变更槽位数与类型（封面钩子 / 章导语 / 辑封等）+「查看第一处」；10s 可自动收或手动关。失败不显示假 diff。 |
| **D-SNR-07** | **AI 状态诚实** | Sheet「杂志文案」状态机：`未配置` / `可生成` / `生成中` / `已是杂志文案` / `失败可重试`。`可生成` **不得**暗示预览已是杂志感。`narrative_ready` ↔ `已是杂志文案` 对齐。 |
| **D-SNR-08** | **浮层互斥全集** | 打开任一 ⇒ 关闭其他：`AI Sheet` · `导出设置` · `分章` · `精修`。**Supersede 执行缺口**：D-SFP-10 / D-SAS-04 未覆盖「AI↔导出」的部分由本决策补全。 |
| **D-SNR-09** | **关闭命中保证** | AI Sheet 关闭控件（×）与 Esc、Dock「AI」toggle **三通道**可用；× 的点击命中区不得被 Dock caret / 金色钮遮挡（z-index 或 hit-test 修复）。 |
| **D-SNR-10** | **文案包 body 填充分级** | L0（无版心叙事）：title+topics，body 空 + 诚实说明（继承 D-SFP-11）。L1（`narrative_ready`）：body 由 hook + 章 lead 摘要规则拼装（禁编造）；提供「复制文案包」。可选「只用标题话题」。 |
| **D-SNR-11** | **金色 CTA 人话** | 单选：`导出{平台短名}`（例：导出小红书 / 导出长图 · 发微信群）。多选：`导出 · {主平台短名}等 N 项` 或 `导出 N 项`（N≥2），**禁止**主文案仅为「N 个模式」。「N 个模式」可留作设置摘要次级信息。 |
| **D-SNR-12** | **喜欢项零回退** | 六平台、清晰度像素、密度、窄屏 gate、脏题名 0、AI「不自动消耗额度」文案、示例「已经做过了」对话框 — 本主题验收不得倒退。 |

---

## 4. 分域方案（逐槽点）

### 4.1 C1 · 成片叙事空壳（P-SNR-01）→ F-SNR-01

**用户故事**：作为职场晒旅用户，我不接受「封面很满、正文没一句话」却没有任何解释；要么告诉我这是纯照片，要么告诉我怎么补。

**姿态判定（实现合同）**：

| 姿态 | 条件（AND/OR 见注） | 用户可见 |
|------|---------------------|----------|
| `narrative_ready` | 存在非空 `meta.hook` **或** ≥1 章非空 `lead`，且来源非禁词/回声 | 姿态轻提示可省略或显示「杂志感文案」次级 |
| `upgrade_ready` | 非 `narrative_ready`，且 AI Surface ON，且写作引擎就绪 | 条：**「纯照片成册 · 可生成杂志感文案」** + 按钮打开 AI Sheet 并聚焦杂志文案 |
| `photo_led` | 其余（含 NAS / 无 Key） | 条：**「纯照片成册」**；帮助链「如何升级文案」（不硬推） |

注：单章空 lead 仍合法；判定看**成册聚合**。

**alt / 可见层**：

1. 渲染与长图文字管道共用 `resolve_visible_caption()`：命中「旅行照片」→ 置空。  
2. 新增/收紧 alt 回退表（COPY-SNR-A\*）。  
3. 全库扫描闸：文字层「旅行照片」= 0（AC-SNR-03）。

**不做什么**：不自动用 LLM；不批量灌 stub 句。

---

### 4.2 C2 · 日期腔章名（P-SNR-02）→ F-SNR-02

**用户故事**：作为轻度编辑，我希望不打开 AI 也能分清「上午在武大门口 / 下午在樱园」，而不是三个「7月8日」。

**生成规则（无 AI）**：

1. 继承 D-SFP-01/02（禁序号腔、同日策略）。  
2. **升维**：当 segment/place 置信可用，章名优先 `{地点短标}` 或 `{地点短标} · {时段}`；日期可进副信息（章眉/进度）不必占主标题。  
3. 无地点时：`{日期} · {时段}` > 裸日期。  
4. 分章面板「改名」旁：AI Surface ON 时次级链「用 AI 润色章名」（跳转 AI Sheet · 杂志文案），**不**在分章面板内嵌第二套生成器。  
5. 存量：打开预览可对**非手改**章名跑 idempotent 薄章名 refresh（与 D-SFP-12 同纪律）。

**线框 F2**：章眉 01 +「樱园 · 下午」vs 旧「7月8日 · 下午」。

---

### 4.3 C3 · 往年 EXIF 泄漏（P-SNR-03）→ F-SNR-03

**用户故事**：作为家庭组织者，我不希望朋友问「你们 2015 年就去武大了？」。

**规则**：

1. 计算 `tripPrimaryYear`（行程起止年众数或中位）。  
2. 离群照片（D-SNR-05）：自动图注/高光角标 **不展示四位年份**；可用 `往年 · 下午` 或仅时段。  
3. 分章「为什么这样分章」在存在离群时追加一句 COPY-SNR-T02。  
4. 不删除照片、不强制移出高光池（避免误伤「翻拍旧照」叙事）；只修**读者面时间措辞**。  
5. OQ-SNR-01：是否在精修对照片打「往年」小标 — 默认 W2 再定。

---

### 4.4 C4 · AI「可生成」预期差（P-SNR-04）→ F-SNR-04

**用户故事**：作为 AI 尝鲜者，我要点一次就看见版心变了，并知道改了哪几处。

**闭环**：

| 阶段 | UI |
|------|-----|
| 前 | 状态「可生成」+ 姿态 `upgrade_ready`；预览可有轻提示，**禁止**「杂志文案已完成」 |
| 中 | busy「正在生成杂志感文案…」；Dock AI 入口保留可取消语义（若支持） |
| 后成功 | 刷新预览 → **diff 条**（D-SNR-06）→ 状态「已是杂志文案」→ 姿态 `narrative_ready` |
| 后失败 | toast 人话失败；姿态保持；无假 diff |

**与 AIR 边界**：语气/覆盖确认框仍用 SAS COPY-SAS-N06；本主题只强制 diff 与状态对齐。

**线框 F4**：diff 条「已更新：封面钩子 · 3 段章导语 · 辑封一句」+「查看第一处」。

---

### 4.5 C5 · AI 关闭被挡（P-SNR-05）→ F-SNR-05

**根因**：Sheet × 与 Dock `▾` 命中区重叠 / z 阶梯错误（08-10 Playwright 实锤）。

**方案**：

1. Sheet 关闭钮提升至独立层，`pointer-events` 不被 Dock 截获。  
2. 自动化：`AC-SNR-06` 强制真实 click ×（禁止只测 Esc）。  
3. Esc 与 Dock toggle 仍保留（三通道）。

---

### 4.6 C6 · 浮层叠开（P-SNR-06）→ F-SNR-06

**方案**：

1. 实现 D-SNR-08 互斥表（单一 `closeAllChromePanelsExcept(id)`）。  
2. 打开导出设置 ⇒ 关 AI；打开 AI ⇒ 关导出设置。  
3. 回归：分章 ↔ 导出（D-SFP-10）不得回退。

---

### 4.7 C7 · 文案包正文（P-SNR-07）→ F-SNR-07

**方案**：

1. 实现 D-SNR-10 L0/L1。  
2. L1 body 拼装顺序（规则，非新 LLM 调用）：`hook` → 最多 3 条非空章 lead（截断）→ 可选地点/日期一行。  
3. UI：`复制文案包` 旁增加次级「仅标题和话题」（L0 行为）。  
4. 当 `upgrade_ready`：文案包区增加一句「生成杂志感后可带正文」+ 链到 AI Sheet。  
5. 完整三通道仿写仍归 AIR；本主题只打通「已有版心 → body」。

---

### 4.8 C8 · 金色 CTA 人话（P-SNR-08）→ F-SNR-08

**方案**：

1. 实现 D-SNR-11 文案表（COPY-SNR-C\*）。  
2. 设置摘要可保留「已选 N 项」次级；主钮禁止孤立「N 个模式」。  
3. 多选导出进度 / Task Dock 仍可用「N 项」计数，但主 CTA 优先平台名。

**线框 F8**：主钮「导出小红书」；旁「设置 ▾」；摘要「另选了微信群」。

---

## 5. 文案合同（COPY-SNR-*）

| ID | 场景 | 冻结文案 |
|----|------|----------|
| **COPY-SNR-P01** | 姿态 · photo_led | 纯照片成册 |
| **COPY-SNR-P02** | 姿态 · upgrade_ready | 纯照片成册 · 可生成杂志感文案 |
| **COPY-SNR-P03** | 姿态 CTA | 生成杂志感文案 |
| **COPY-SNR-P04** | 姿态 · 次级 | 如何升级文案 |
| **COPY-SNR-D01** | diff 条标题 | 文案已更新 |
| **COPY-SNR-D02** | diff 摘要模板 | 已更新：{slots} |
| **COPY-SNR-D03** | diff 动作 | 查看第一处 |
| **COPY-SNR-T01** | 往年图注/角标 | 往年 · {daypart}（daypart 可空） |
| **COPY-SNR-T02** | 分章解释追加 | 含往年照片，已按拍摄时间排序；角标不强调旧年份。 |
| **COPY-SNR-S01** | 杂志文案状态 | 未配置 / 可生成 / 生成中 / 已是杂志文案 / 失败可重试 |
| **COPY-SNR-X01** | 文案包 L0 | 标题和话题已备好 · 正文可粘贴后自填 |
| **COPY-SNR-X02** | 文案包 L1 提示 | 已带入杂志文案摘要 · 可粘贴后微调 |
| **COPY-SNR-X03** | 文案包次级 | 仅标题和话题 |
| **COPY-SNR-X04** | upgrade 提示 | 生成杂志感后可带正文 |
| **COPY-SNR-C01** | CTA 微信群 | 导出长图 · 发微信群 |
| **COPY-SNR-C02** | CTA 小红书 | 导出小红书 |
| **COPY-SNR-C03** | CTA 朋友圈 | 导出朋友圈 · 长图连读 |
| **COPY-SNR-C04** | CTA 多选 | 导出 · {主平台}等 {n} 项 |
| **COPY-SNR-A01** | 可见层禁词 | 旅行照片（禁止出现在 caption/长图字） |

禁词增量（并入 SFC/SFP 禁词表，不另起炉灶）：`杂志文案已完成`（在 `upgrade_ready`/`photo_led` 时）、孤立主 CTA `N 个模式`。

---

## 6. 工程任务索引

详见 [IMPLEMENTATION-SHARE-NARRATIVE-READINESS-V1.md](./IMPLEMENTATION-SHARE-NARRATIVE-READINESS-V1.md)。

| ID | 任务 | 主路径 |
|----|------|--------|
| **BE-SNR-01** | `narrativePosture` 计算 + trip/API 投影 | domain / web handlers |
| **BE-SNR-02** | 薄章名生成序 + 存量 refresh | `chapter_titles.py` |
| **BE-SNR-03** | 往年抑制 + caption/alt resolve | render / longshot text |
| **BE-SNR-04** | shareCopyPack L1 body 拼装 | `share_copy_pack.py` |
| **FE-SNR-05** | 姿态条 + upgrade CTA | preview chrome |
| **FE-SNR-06** | AI diff 条 + 状态机文案 | `ai-sheet.js` |
| **FE-SNR-07** | 浮层互斥全集 + × 命中 | preview-toolbar / sheets |
| **FE-SNR-08** | 金色 CTA 人话 | `dock.js` / longshot entry |
| **QA-SNR-09** | 扫描闸 + Playwright 互斥/关闭/CTA | tests |

---

## 7. 错误与降级

| 场景 | 行为 |
|------|------|
| 姿态计算失败 | 默认为 `photo_led`，不阻断预览 |
| 薄章名 refresh 失败 | 保留原章名；打点 |
| 往年判定缺年 | 不抑制（Fail-open 展示原逻辑） |
| AI 生成失败 | 无 diff；状态失败可重试；姿态不变 |
| body 拼装无材料 | 回退 L0 说明 |
| 互斥 close 抛错 | 仍尝试关目标面板；导出主路径优先 |

---

## 8. 埋点

| 事件 | 关键属性 |
|------|----------|
| `snr_posture_impression` | posture / tripId |
| `snr_upgrade_cta_click` | source=`banner\|ai_sheet\|copy_pack` |
| `snr_diff_show` | slots_count / voice |
| `snr_diff_jump` | — |
| `snr_outlier_year_suppressed` | count |
| `snr_panel_mutex` | opened / closed[] |
| `snr_cta_label` | label / platforms[] |
| `snr_copy_pack` | tier=`L0\|L1` / channel |

禁止上传原图；属性仅枚举与计数。

---

## 9. 非功能

| 项 | 要求 |
|----|------|
| 性能 | 姿态计算 < 50ms / 打开预览；不新增默认 LLM 调用 |
| 隐私 | 继承本地优先；往年抑制纯本地规则 |
| a11y | 姿态条与 diff 条可被读屏；× 可键盘关闭 |
| 兼容 | NAS 关闭时无 upgrade 主按钮；薄章名与往年抑制仍生效 |
| 20 分钟成片 | 不增加导入默认耗时（CHARTER O2） |

---

## 10. 里程碑

| 里程碑 | 交付 | 关门 |
|--------|------|------|
| **W0** | 线框 F1–F8 **已出**待签核 · FE-07 互斥+关闭命中 · FE-08 CTA 人话 · 扫描闸骨架 | C5/C6/C8 可狗粮 |
| **W1** | BE-01 姿态 · FE-05 姿态条 · BE-03 往年+禁「旅行照片」文字层 | C1 诚实空 · C3 |
| **W2** | BE-02 薄章名 · FE-06 diff/状态 · BE-04/FE 文案包 L1 | C2/C4/C7 |
| **W3** | 全库狗粮 + Persona 复测 · 真人 N≥5 · 喜欢项零回退签核 | C1–C8 关闭或降为 P2 残留 |

---

## 11. 验收 AC 索引

源文件：[ACCEPTANCE-SHARE-NARRATIVE-READINESS-V1.md](./ACCEPTANCE-SHARE-NARRATIVE-READINESS-V1.md)

| AC | 覆盖 |
|----|------|
| AC-SNR-01～02 | 姿态诚实 / upgrade 捷径 |
| AC-SNR-03～04 | 旅行照片禁文字层 / 薄章名 |
| AC-SNR-05 | 往年抑制 |
| AC-SNR-06～07 | AI 关闭命中 / 浮层互斥 |
| AC-SNR-08～09 | diff + 状态机 |
| AC-SNR-10～11 | 文案包 L1 / CTA 人话 |
| AC-SNR-12 | 喜欢项零回退 |

---

## 12. 风险与开放问题

### 12.1 风险

| 风险 | 缓解 |
|------|------|
| 姿态条变成新噪音 | 同时最多 1 条主提示；`narrative_ready` 可隐藏 |
| 薄章名误用低置信地点 | 置信门槛 + 宁可日期 |
| 「往年」伤怀旧叙事 | 只改自动角标；手改保留；OQ-SNR-01 |
| diff 与覆盖确认打架 | diff 在确认接受并刷新后出现 |
| 与 SCR 屏级文案区重叠 | 姿态条挂 chrome 不进 screen copy region |

### 12.2 开放问题

| ID | 问题 | 默认倾向 | 关门 |
|----|------|----------|------|
| **OQ-SNR-01** | 精修媒资是否打「往年」小标 | **关闭：不做**（仅自动角标/图注；精修媒资不加小标） | W2 关 |
| **OQ-SNR-02** | `narrative_ready` 是否在书架卡片露小点 | **关闭：否**（免噪音） | 关 |
| **OQ-SNR-03** | 多选 CTA 用「等 N 项」还是轮播主平台名 | **关闭：「等 N 项」** | W0 线框 |
| **OQ-SNR-04** | 无地点时是否允许场景词（美食/夜景）上章名 | **关闭：允许**极短非复读（薄章名 `scene_short`） | W2 关 |

---

## 附录 A · 试用槽点 ↔ 决策 ↔ 任务

| 试用 | 问题 | 决策 | 任务 |
|------|------|------|------|
| C1 | P-SNR-01 | D-SNR-01/02/04 | BE-01 · FE-05 · BE-03 |
| C2 | P-SNR-02 | D-SNR-03 | BE-02 |
| C3 | P-SNR-03 | D-SNR-05 | BE-03 |
| C4 | P-SNR-04 | D-SNR-06/07 | FE-06 |
| C5 | P-SNR-05 | D-SNR-09 | FE-07 |
| C6 | P-SNR-06 | D-SNR-08 | FE-07 |
| C7 | P-SNR-07 | D-SNR-10 | BE-04 |
| C8 | P-SNR-08 | D-SNR-11 | FE-08 |

---

## 附录 B · 线框帧映射（W0）

| 帧 | 内容 | 规格 |
|----|------|------|
| **F1** | 姿态条 · photo_led / upgrade_ready | F-SNR-01 |
| **F2** | 薄章名章眉 | F-SNR-02 |
| **F3** | 往年角标「往年 · 下午」 | F-SNR-03 |
| **F4** | AI diff 条 | F-SNR-04 |
| **F5** | AI × 命中热区示意 | F-SNR-05 |
| **F6** | 互斥：开导出则 AI 已关 | F-SNR-06 |
| **F7** | 文案包 L0/L1 | F-SNR-07 |
| **F8** | 金色 CTA 人话 | F-SNR-08 |

---

## 附录 C · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-08-10 | 初稿：基于 08-10 十席试用 C1–C8；首席 UX/设计视角成文；待评审 |
| **v0.1.0+wf** | 2026-08-10 | 补齐线框 F1–F8（含拍板清单 Tab）；索引已挂 README / wireframes README |
