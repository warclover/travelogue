# Travelogue · 敢发收口优化 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio（本机 Studio / 桌面打包同等体验） |
| **文档版本** | **v1.0.2** |
| **状态** | **Conditional Go · W0–W2 工程已合入** · **§12 质量收口全部必修** |
| **主题代号** | 「敢发收口」— 无 Key 不丢人 · 进度可解释 · 小册少打断 · 词表人话 |
| **触发来源** | [2026-07-18 八席 Persona 完整试用](./acceptance-records/persona-ux-trial-2026-07-18.md)（Agent 模拟联评 + 契约补签）；交叉对照 FST / Share-Ready / QH / Refine / Chapter Naming |
| **前置条件** | Studio 首页 v2（M21）；L0 无 Key 可成稿；FST W0–W2 工程已合入；Share-Ready W0–W2 工程已合入；Output Recipe 可开 |
| **关联文档** | [PRD-FIRST-SESSION-TRUST-V1.md](./PRD-FIRST-SESSION-TRUST-V1.md) · [PRD-SHARE-READY-OPTIMIZATION-V1.md](./PRD-SHARE-READY-OPTIMIZATION-V1.md) · [PRD-STABLE-QUALITY-HARDENING-V1.md](./PRD-STABLE-QUALITY-HARDENING-V1.md) · [PRD-PREVIEW-REFINE-V1.md](./PRD-PREVIEW-REFINE-V1.md) · [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md) · [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) · [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md) · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) · [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) · [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) |
| **评审记录** | [跨职能评审](./acceptance-records/share-face-closeout-v1-review-2026-07-18.md) · Conditional Go · BLK-01～08 |
| **验收** | [ACCEPTANCE-SHARE-FACE-CLOSEOUT-V1.md](./ACCEPTANCE-SHARE-FACE-CLOSEOUT-V1.md)（本文 §10 为索引） |
| **实施清单** | [IMPLEMENTATION-SHARE-FACE-CLOSEOUT-V1.md](./IMPLEMENTATION-SHARE-FACE-CLOSEOUT-V1.md) |
| **手测狗粮** | [acceptance-records/share-face-closeout-v1-dogfood-CHECKLIST.md](./acceptance-records/share-face-closeout-v1-dogfood-CHECKLIST.md) |
| **线框** | [wireframes/share-face-closeout-v1-wireframe.html](./wireframes/share-face-closeout-v1-wireframe.html) · F1–F5（W0：F1–F3 · W1：F4–F5） |
| **试用底稿** | [persona-ux-trial-2026-07-18.md](./acceptance-records/persona-ux-trial-2026-07-18.md) |
| **更新日期** | 2026-07-18 |

> **v1.0.1 评审回写摘要（跨职能 Conditional Go）**
>
> - BLK-01：QH R-QH-05 stale 一字面 → 本主题 D-SFC-06「分享图需更新」  
> - BLK-02：Refine Sparse 快速分享默认跳过 G1；精细制作除外  
> - BLK-03：FST §4.5 禁词表增量指针（竖幅 / 弱枚举 / 标题复读）  
> - BLK-04：OQ-SFC-01～04 **已关闭**（§11.2）  
> - BLK-05：线框 F1–F3 = W0 UI 挡门  
> - BLK-06：AC-SFC-04 必做可测锁（注入/e2e）  
> - BLK-07：AC/IMPL/狗粮已拆文，Kickoff 不重复拆  
> - BLK-08：喜欢项 NR（意图卡 / 按章导出）进完成定义  
> - **本轮不动代码**；编码 Kickoff 另排期

> **定位**
>
> 相邻主题已分别定义：首访可信（FST）、敢发闭环（Share-Ready）、stale 词统一（QH）、精修 IA（Refine）、章名算法（Chapter Naming）。  
> **2026-07-18 试用证明**：排版与配方 CTA 已是强获得感；真正阻断「敢发出去」的，是合同**未兑现到样片 / 缺口未立项**的五类断裂——  
> **① stub 假句仍上分享面** · **② 脏文件夹名仍上封面** · **③ 视觉模型下载时进度为空** · **④ stale 主词仍偏工程** · **⑤ Sparse 小册被 G1 打断**。  
> 本 PRD **不重做首访叙事、不重做配方分流**，只把试用吐槽收成一条可排期的收口合同；并对已有铁律补齐 **禁词实例、fixture 与降级策略**。
>
> **一句话目标**：无 Key 用户打开成片后，**不觉得丢人、不觉得坏了、不被多余步骤拦住**，愿意点「发微信群 / 选择分享」。
>
> **产品共识（五条铁律）**
>
> 1. **空优于假句** — 无合格文案时槽位留空；禁止说明书腔、弱枚举、标题复读填坑。  
> 2. **展示名必须体面** — 封面 / 书架 / FirstSuccess 同源 `displayTitle`；禁止 `--`、尾序号、导出目录腔裸上封面。  
> 3. **忙碌必有主句** — 任意 `status=running` 必须有可读阶段；模型首次下载是一等公民阶段，不得静默。  
> 4. **小册少打断** — Sparse（`kept_n` 1–9）默认不挡主链确认章节；分享者先发得出去。  
> 5. **词表人话** — 用户面禁止「媒资」等工程词；stale 主词面向「还能不能发」，不面向「产物是否过期」。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 与相邻主题的边界（拥有 / 硬化 / 修订） |
| §0.2 | 相对 QH「长图可更新」的产品修订 |
| §1 | 试用结论与问题清单（P-SFC-*） |
| §2 | 目标 / 非目标 / 成功指标 |
| §3 | 体验合同与冻结决策（D-SFC-*） |
| §4 | 触点与文案矩阵 |
| §5 | 工程任务 |
| §6～§8 | 错误 / 埋点 / 非功能 |
| §9 | 线框与里程碑 |
| §10 | 验收 AC 索引 |
| §11 | 风险与 OQ |
| 附录 | 试用映射 · 版本记录 |

### 0.1 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [First-Session Trust](./PRD-FIRST-SESSION-TRUST-V1.md) | **硬化 · 不抢所有权** | 继承 D-FST-01/06/08/09；**本主题拥有**禁词实例表、fixture 回归、视觉模型下载阶段文案 |
| [Share-Ready](./PRD-SHARE-READY-OPTIMIZATION-V1.md) | **并行不抢** | 意图卡 / `kept_n` / CTA 分流仍归 Share-Ready；本主题只保证分享面文案与命名不毁敢发 |
| [Stable-QH](./PRD-STABLE-QUALITY-HARDENING-V1.md) | **修订 R-QH-05** | stale **唯一主词**仍保持单一；**一字面由本主题 supersede**（见 §0.2） |
| [Preview Refine](./PRD-PREVIEW-REFINE-V1.md) | **修订 G1 触发 + 词表** | 保留 G1 横幅组件；**Sparse 默认不 pending**；「媒资」改人话 |
| [Chapter Naming](./PRD-CHAPTER-NAMING.md) | **挡门 + 移交深度** | 本主题挡「×日续」与弱 hook；杂志级章名仍归原轨 |
| [Copy](./PRD-COPY-OPTIMIZATION.md) | **挡门 + 移交深度** | 本主题挡 stub 假句；真 LLM 气质归 Copy / WEA |
| [Wait Tips](./PRD-WAIT-TIPS-V1.md) | **并行 · 次区** | 模型下载阶段主句归本主题；Tips 仍可挂次区教育 |
| [Output Recipe](./PRD-OUTPUT-RECIPE-V1.md) | **不做** | Band / 意图卡合同不变；试用中 L2/L3 为保留项 |
| 手机完整工坊 | **不做** | C9 已知限制，不在本主题范围 |

### 0.2 产品修订：stale 主词人话化（相对 R-QH-05）

| 原合同（QH R-QH-05） | 本主题修订 |
|----------------------|------------|
| 用户面唯一 stale 主词 = **「长图可更新」** | 唯一主词改为 **「分享图需更新」** |
| Dock / 书架 / Help 深链同族 | **全链路同步替换**；禁止两词并存 |
| Help 解释「长图可更新」是什么意思 | 深链标题改为「「分享图需更新」是什么意思」；首句解释「改过版面或照片后，导出最新图再发」 |

> **定案理由（U1 / U4）**：用户关心的是「现在发出去会不会是旧的」，不是「长图产物是否可更新」。QH 已完成「废除待更新 / 已过期乱词」的统一，本主题在**保持唯一主词**前提下换人话。

---

## 1. 背景与问题

### 1.1 试用方法（可复现）

| 项 | 约定 |
|----|------|
| **环境** | Windows · Studio `http://127.0.0.1:8766` · Chrome/Edge |
| **底稿** | [persona-ux-trial-2026-07-18.md](./acceptance-records/persona-ux-trial-2026-07-18.md) |
| **契约** | `TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=1 python scripts/stable_qh_persona_trial.py --base http://127.0.0.1:8766` → P1–P5 PASS |
| **样片** | demo-album（Sparse）· demo-e863ec0da9（Ambiguous）· demo-2025-9（Narrative）· 新导入试用册 |
| **性质** | Agent 模拟联评；**真人 N≥5 仍为完成宣布条件**（对齐 FST USR-06） |

### 1.2 试用结论（给决策者）

| 维度 | 结论 |
|------|------|
| **保留（不要动坏）** | 杂志排版节奏 · Output Recipe 自适应 CTA · 意图卡人话 · 示例试水 · 精修换封面 · 本地无需注册 |
| **收口（本主题）** | stub 假句 · 脏题名 · 模型下载静默 · stale 工程词 · Sparse G1 打断 · 「媒资」 |
| **移交** | 真 LLM 文案气质 → Copy/WEA；手机工坊 → 范围外 |

### 1.3 问题清单（P-SFC-*）

| ID | 试用 ID | 严重度 | 问题 | 波次 | 所有权 |
|----|---------|--------|------|------|--------|
| **P-SFC-01** | C1 | **P0** | stub/L0 图注说明书腔与弱枚举仍进分享面（「竖幅」「抬头看见」「夜景，白天」；标题复读作 alt） | W0 | **本主题硬化** FST D-FST-06 |
| **P-SFC-02** | C2 | **P0** | 脏文件夹名上封面（`2025东澳岛9`、`武大--米娜`）；humanize/回退未在展示链兑现 | W0 | **本主题硬化** FST D-FST-09 |
| **P-SFC-03** | C3 | **P0** | Job `running` 时 `phase/progress/message` 可全空；HF/OpenCLIP 首次下载无阶段主句 | W0 | **本主题新合同**（FST 进度诚实增量） |
| **P-SFC-04** | C4 | **P1** | 「长图可更新」统一后仍偏工程；用户不懂要做什么 | W1 | **本主题修订** QH R-QH-05 |
| **P-SFC-05** | C5 | **P1** | 「×日续」与空/弱 hook；demo-album 仍见「5月27日续」 | W1 | **本主题挡门** + Chapter Naming |
| **P-SFC-06** | C6 | **P2** | Sparse（如 6 张）仍弹 G1「章节结构待确认」挡验货 | W1 | **本主题新合同**（修订 Refine） |
| **P-SFC-07** | C7 | **P2** | 精修「媒资」工程词 | W2 | **本主题新合同** |
| **P-SFC-08** | C8 | **P2** | 无 Key 易被误解为「杂志文案已完成」 | W1 | **对齐** FST USR-03；本主题补 FirstSuccess/预览弱提示规则 |

---

## 2. 目标与非目标

### 2.1 目标（G-SFC-*）

| ID | 目标 |
|----|------|
| **G-SFC-01** | L0/stub/示例成片：分享面零说明书腔、零弱枚举假句；宁可空 |
| **G-SFC-02** | 新导入与回访展示：封面/书架/FirstSuccess 标题体面；fixture 脏名全部被清洗或回退 |
| **G-SFC-03** | 任意导入 `running` ≥1s：UI 可见非空阶段主句；视觉模型首次准备有专属主句 |
| **G-SFC-04** | stale 全链路唯一主词 =「分享图需更新」，首次可理解「要重新导出再发」 |
| **G-SFC-05** | Sparse（`kept_n` 1–9）快速分享主链：默认无 G1 阻断横幅 |
| **G-SFC-06** | 精修用户面零「媒资」；控件标签人话 |

### 2.2 非目标

| 不做 | 说明 |
|------|------|
| 重做 Output Recipe / 意图卡 | 试用中为喜欢项 |
| 真 LLM 杂志级文案 | 归 Copy / WEA；本主题只挡假句 |
| 章名算法全面重做 | 归 Chapter Naming；本主题只禁刺耳形态 |
| 手机完整工坊 | C9 范围外 |
| 教用户如何发微信 | 对齐 FST：成功面不教微信 |
| 自动弹资源管理器 | 对齐 FST D-FST-13 |
| 海外 IG / 小程序鉴权分享 | 范围外 |

### 2.3 成功指标

| 指标 | 目标 | 测量 |
|------|------|------|
| 示例/L0 分享面命中禁词表 | **0** | 单测 fixture + 手测抽检 |
| 脏名 fixture 上封面裸名 | **0** | 单测 `title_humanize` + 导入 e2e |
| 导入 running 无主句持续时间 | **≤1s** | e2e / 手测墙钟 |
| Sparse 快速分享出现 G1 阻断横幅 | **0**（默认设置） | e2e |
| 用户面「媒资」「长图可更新」残留 | **0** | DOM/文案扫描 |
| 真人可用性（完成宣布） | N≥5 含 U1/U3/U7 | 狗粮清单 |

---

## 3. 体验合同与冻结决策

### 3.1 Stub / L0 分享面禁词与空槽合同（P-SFC-01）

**适用范围**：卷轴读者面、长图默认导出面、示例相册、forceStub / 无 Key 成片。

| 槽位 | 必须 | 禁止（含同义改写） |
|------|------|-------------------|
| hook / 开篇 | 可空 | 「慢慢翻」「抬头看见…」「关于{X}的 N 天」「碎片拼成」 |
| 图注 / caption | 可空；合格则地点/时间短标签 | 「…的竖幅」「…的横幅」「抬头看见{标题}」 |
| 弱枚举句 | 禁止进分享面 | 「夜景，白天」「白天，傍晚」等仅时段枚举、无画面信息 |
| alt / 无障碍 | 可与可见图注一致或更短 | **禁止**用杂志全名对每张图复读填坑（试用：整册 alt = 同一标题） |
| EXIF | — | 相机 Make/Model 不得可见（继承 D-FST-07） |

**生成规则（冻结）**

1. stub 模板若只能产出禁词表命中句 → **写空字符串**，不得降级填假句。  
2. 已存在 trip（含 demo-album）在本主题 W0 须 **重烘焙或迁移清洗**，不得只修新导入。  
3. 有 Key / 真 LLM：本主题不评价气质；但若模型产出命中禁词，渲染层 **仍可空**（防御）。

### 3.2 展示名体面合同（P-SFC-02）

**权威字段**：`displayTitle`（或等价展示槽）用于封面主标题、书架卡片、FirstSuccess；精修可编辑原 `meta.title`。

| 输入样例（试用） | 期望展示（OQ-SFC-01 **已关闭**） |
|------------------|----------|
| `2025东澳岛9` | 去尾数字后若剩 2–6 字可读地名 → `{地名} · 旅行`（如 `东澳岛 · 旅行`）；否则 `旅行 · {日期范围}`；**禁止**裸 `…9` |
| `武大--米娜` | `武大 米娜`（折叠连续 `-`/`_`/`.` 为空格后 trim） |
| `爸爸手机导出2` | 回退体面名（继承 FST 噪音启发） |
| 用户手改标题 | 以用户为准，不再二次「诗意改写」 |

**清洗增量（相对现网 humanize）**

| 规则 | 说明 |
|------|------|
| 连续分隔符 | `[_\-.·]+` → 单空格；禁止残留 `--` |
| 中文/词尾序号 | `[\u4e00-\u9fff]\d{1,3}$` 或无分隔粘连+尾数字 → 视为噪音，走回退 |
| 年份前缀+尾数字 | 如 `2025东澳岛9`：去掉尾数字后若仍像目录名，优先地名抽取或回退「旅行 · 日期」 |
| 同源 | FE `title-humanize.js` 与 BE `travelogue.domain.title_humanize` **同测同例**（含最终日期兜底；见 §12.1 · AC-SFC-12） |

### 3.3 导入进度与视觉模型准备（P-SFC-03）

**合同**：`status=running` 时，状态 API 与 UI **禁止**长期（>1s）同时满足 `phase/message` 皆空。

| 阶段（逻辑名） | 用户主句（冻结意图） | 次行（可选） |
|----------------|----------------------|--------------|
| `ingest` | 正在读取照片… | 张数进度（若有） |
| `vision_warmup` | 正在准备识图（首次可能较慢） | 「可取消；取消后仍可做游记」 |
| `vision` / `embed` | 正在识别画面… | — |
| `curate` | 正在挑选与分章… | — |
| `narrate` | 正在写短句… / 跳过配文（无 Key） | 无 Key 不得暗示「杂志文案已完成」 |
| `layout` / `render` | 正在排版… | — |

**视觉模型下载 / 首次准备**

1. 一经进入模型文件获取或加载，必须映射为 **`vision_warmup`**（或等价），主句见上表。  
2. 下载失败或离线：不得卡死；**降级继续主链**（L0 可成稿），toast/次行说明「识图未启用，已用时间与张数整理」。  
3. Wait Tips 可挂在次区，**不得**替代阶段主句。  
4. 与 FST「进度诚实」联合挡门：禁止假 100% / 假 0%。

### 3.4 stale 主词人话（P-SFC-04）

| 触点 | 主词 | 副文（可选） |
|------|------|--------------|
| 书架角标 | **分享图需更新** | — |
| 预览顶栏 / Task Dock | **分享图需更新** | 改过版面或照片后，导出最新图再发 |
| Help 深链 | 「分享图需更新」是什么意思 | 解释「旧长图不要发；点导出更新」 |
| 示例角标 | 同主词 | 不出现「产物」「过期」作唯一主句 |

**禁止**：用户面主词再出现「长图可更新」「长图待更新」「长图已过期」（Help 历史锚点可 301 文案级重写）。

### 3.5 章名与 hook 挡门（P-SFC-05）

| 规则 | 合同 |
|------|------|
| 「续」 | **禁止** `{日期}续`；替换一字面继承 FST §3.5（时段 / `（2）`） |
| hook | 可空；禁止弱枚举（同 §3.1） |
| demo 存量 | W1 前重烘焙 demo-album 章名，验收抽检不得再见「5月27日续」 |

### 3.6 Sparse 小册 G1 降级（P-SFC-06）

| 条件 | 行为（OQ-SFC-02 **已关闭**） |
|------|------|
| `kept_n` ∈ **1–9** 且模式为 **快速分享**（默认） | **不设** `structurePending`；**不展示** G1 阻断横幅 |
| 同上但用户在设置开启「导入后先确认章节」（实验选项） | 允许 G1（尊重高级用户） |
| **精细制作**（即使 `kept_n≤9`） | **可 G1**（不享受 Sparse 跳过） |
| `kept_n` ≥ 10 | 维持 Refine 现合同（可 G1） |
| 优先级栈 | 若 Sparse 快速分享无 G1：`layoutPending > longshotStale`（修订 D-REF-18 在该缺省路径） |

> **定案理由（U1）**：6 张周末短途被「章节顺序 OK」拦住，违背 80% 分享者主链。结构质量问题用更好的默认分章解决，而不是用确认弹层换信任。

### 3.7 精修词表（P-SFC-07）

| 原词 | 用户面 |
|------|--------|
| 媒资 | **照片类型**（下拉：普通照片 / 拼图） |
| 内部 API / schema | 可保留英文枚举，不进 DOM 可见标签 |

验货态继续隐藏该控件（Trust）；精修态仅显示人话标签。

### 3.8 无 Key 预期管理（P-SFC-08）

| 触点 | 允许 | 禁止 |
|------|------|------|
| FirstSuccess | 「游记已做好，可预览与导出」 | 「杂志级文案已完成」「AI 已写好全文」 |
| 预览空文案槽 | 安静留空；或精修内「可点此添加一句」 | 用假句占位 |

### 3.9 冻结决策（D-SFC-*）

| ID | 决策 |
|----|------|
| **D-SFC-01** | stub/L0：禁词表命中 → 空槽；含「竖幅 / 抬头看见 / 弱枚举时段」 |
| **D-SFC-02** | 标题复读不得作为批量可见 alt/图注填坑 |
| **D-SFC-03** | `displayTitle` 同源封面/书架/FirstSuccess；`--` 与尾数字噪音必须清洗或回退 |
| **D-SFC-04** | running >1s 禁止 phase/message 双空；`vision_warmup` 为一等阶段 |
| **D-SFC-05** | 视觉准备失败 → 降级继续，不阻断 L0 成稿 |
| **D-SFC-06** | stale 唯一主词 =「分享图需更新」（supersede R-QH-05） |
| **D-SFC-07** | Sparse 快速分享默认跳过 G1 阻断 · **2026-07-19**：[PCU D-PCU-09](./acceptance-records/preview-chrome-unify-v1-decisions-2026-07-19.md) 默认路径对任意 kept_n / 精细制作一律 auto-lock；本条 Sparse 跳过并入更广默认；实验 `g1ConfirmStructure` 仍可强制 pending |
| **D-SFC-08** | 「媒资」→「照片类型」 |
| **D-SFC-09** | 不新建成功面/进度壳；复用 FST / Dock / Importing 壳 |
| **D-SFC-10** | 喜欢项（Recipe CTA / 意图卡 / 示例试水 / 精修封面）本主题不改行为，仅回归 |

---

## 4. 触点与文案矩阵

### 4.1 触点总表

| ID | 触点 | 问题 | 要点 |
|----|------|------|------|
| **T-SFC-IMPORT** | 导入忙碌壳 | P-SFC-03/08 | §3.3 阶段主句 |
| **T-SFC-SHARE** | 卷轴/长图读者面 | P-SFC-01/02/05 | 禁词 + displayTitle + 章名 |
| **T-SFC-SHELF** | 书架角标/标题 | P-SFC-02/04 | displayTitle +「分享图需更新」 |
| **T-SFC-STALE** | 预览 Dock / 过期条 | P-SFC-04 | 人话主词 + 副文 |
| **T-SFC-G1** | G1 横幅 | P-SFC-06 | Sparse 默认不出现 |
| **T-SFC-REFINE** | 精修行内控件 | P-SFC-07 | 「照片类型」 |
| **T-SFC-FIRST** | FirstSuccess | P-SFC-08 | 不承诺杂志文案 |

### 4.2 禁词表增量（分享面 · 与 FST §4.5 合并扫描）

**新增必须拦截（W0）**

- 竖幅 / 横幅（作图注中心词时）  
- 抬头看见  
- 夜景，白天 / 白天，傍晚（纯枚举）  
- `{标题}` 连续复读（同一屏 ≥3 张可见图注完全相同且等于杂志名）  
- 长图可更新（用户面主词，W1 起）  
- 媒资（用户面标签，W2 起）

### 4.3 Sparse G1 文案（仅高级设置开启时）

保持 Refine 横幅结构；按钮：「章节顺序 OK」/「重新生成结构」。  
默认 Sparse **无此条**。

---

## 5. 工程任务（索引）

> 细项入 IMPLEMENTATION；此处只定波次与边界。

### W0 · 敢秀 + 不假死（P0）

| ID | 任务 |
|----|------|
| **BE-SFC-01** | stub/L0 narrate + render：禁词空槽；弱枚举过滤 |
| **BE-SFC-02** | title_humanize：`--` 折叠、尾数字/年份目录回退；与 FE 同测 |
| **BE-SFC-03** | job status：running 必填 phase/message；`vision_warmup` |
| **FE-SFC-01** | Importing 壳绑定新阶段主句；双空兜底文案 |
| **FE-SFC-02** | 封面/书架/FirstSuccess 读 displayTitle |
| **QA-SFC-01** | fixture：demo-album / `2025东澳岛9` / `武大--米娜` / 竖幅句 |
| **DOC-SFC-01** | 线框 F1–F3；ACCEPTANCE 初稿 |

### W1 · 少打断 + 人话 stale（P1）

| ID | 任务 |
|----|------|
| **BE-SFC-04** | Sparse 快速分享默认 `structurePending=false` |
| **FE-SFC-03** | 「分享图需更新」全链路替换 + Help 深链 |
| **BE-SFC-05** | 章名「续」清洗 / demo 重烘焙 |
| **FE-SFC-04** | FirstSuccess 无 Key 预期文案 |
| **QA-SFC-02** | e2e：Sparse 无 G1；stale 词扫描 |

### W2 · 精修词表与收口（P2）

| ID | 任务 |
|----|------|
| **FE-SFC-05** | 「媒资」→「照片类型」 |
| **QA-SFC-03** | DOM 禁词扫描含精修态 |
| **DOC-SFC-02** | 狗粮清单；相邻 PRD 脚注回写 |

---

## 6. 错误与边界

| 场景 | 行为 |
|------|------|
| 视觉模型下载中取消 | Job cancelled；书架无空壳（继承 QH/P4） |
| 视觉模型失败 | 降级成稿 + 一次人话说明；不失败整单 |
| 旧 trip 无 displayTitle | 读取时即时 humanize；写回可选 |
| 用户故意标题含 `--` | 手改后尊重用户；仅自动生成路径强制清洗 |
| recipe / 意图卡失败 | 不在本主题；归 Share-Ready |

---

## 7. 埋点（建议）

| 事件 | 用途 |
|------|------|
| `sfc_vision_warmup_shown` | 是否露出模型准备主句 |
| `sfc_stub_blanked` | 禁词空槽触发次数（调试） |
| `sfc_title_fallback` | 展示名回退触发 |
| `sfc_g1_suppressed_sparse` | Sparse 跳过 G1 |
| `sfc_stale_label_impression` | 新 stale 主词曝光 |

禁止在埋点 payload 上传照片内容或绝对路径。

---

## 8. 非功能

| 项 | 要求 |
|----|------|
| 性能 | humanize / 禁词过滤 P95 < 5ms / 次；不得拖长导入主链 |
| 兼容 | 桌面 Chrome/Edge 90+；不扩展手机工坊 |
| 隐私 | 本地优先；模型下载须可取消 |
| 文案语言 | 默认简体中文用户面 |
| 回归 | Recipe CTA / 意图卡 / 示例试水 / 精修封面 **零行为回退**（D-SFC-10） |

---

## 9. 线框与里程碑

### 9.1 线框（BLK-05 · W0 挡门 = F1–F3）

| 帧 | 内容 | 波次 | 挡门 |
|----|------|------|------|
| **F1** | 导入：`vision_warmup` 主句 + 可取消 | W0 | **W0 UI** |
| **F2** | 分享面对照：修前假句 → 修后空槽 | W0 | **W0 UI** |
| **F3** | 书架/封面 displayTitle 同源 | W0 | **W0 UI** |
| **F4** | stale：「分享图需更新」+ 副文 | W1 | W1 |
| **F5** | Sparse 无 G1 vs 实验选项 / 精细制作可 G1 | W1 | W1 |

### 9.2 里程碑

| 里程碑 | 定义 |
|--------|------|
| **M0** | PRD 评审 Conditional Go；线框 F1–F5；ACCEPTANCE 初稿 |
| **W0 Go** | P-SFC-01～03 AC 绿；示例成片敢看 |
| **W1 Go** | P-SFC-04～06/08 AC 绿；Sparse 主链顺 |
| **W2 Go** | P-SFC-07 + 全词表扫描绿 |
| **宣布完成** | 真人 N≥5 狗粮通过（含 U1/U3/U7） |

---

## 10. 验收 AC 索引

> 正式条目写入 `ACCEPTANCE-SHARE-FACE-CLOSEOUT-V1.md`；此处为评审挡门索引。

| AC | 断言 | 波次 |
|----|------|------|
| **AC-SFC-01** | forceStub/示例成片：禁词表（§4.2）命中数 = 0 | W0 |
| **AC-SFC-02** | 可见图注不得整册复读杂志全名填坑 | W0 |
| **AC-SFC-03** | 导入脏名 fixture → 封面/书架无裸 `--`、无 `东澳岛9` 类尾数字目录腔 | W0 |
| **AC-SFC-04** | 人为延长 vision 准备：UI ≥1s 内出现「正在准备识图」类主句 | W0 |
| **AC-SFC-05** | vision 失败仍可 succeeded 成稿 | W0 |
| **AC-SFC-06** | 用户面主词仅「分享图需更新」；无「长图可更新」 | W1 |
| **AC-SFC-07** | demo-album 无「×日续」章名 | W1 |
| **AC-SFC-08** | `kept_n≤9` 快速分享：无 G1 阻断横幅（默认设置） | W1 |
| **AC-SFC-09** | 实验选项开启后 Sparse 仍可出现 G1 | W1 |
| **AC-SFC-10** | 精修态可见标签无「媒资」 | W2 |
| **AC-SFC-11** | FirstSuccess 无 Key 无「杂志文案已完成」承诺 | W1 |
| **AC-SFC-12** | **displayTitle 最终兜底 FE/BE 一致（§12.1）**：无地点/噪音标题但有 `dateStart` 时，两端均走 `旅行 · {月日}`（或等价 `_fallback_display`），禁止 FE 独用恒定「旅行 · 游记」 | W0+ |
| **AC-SFC-13** | **trip.json 忙锁回退不丢数据（§12.2）**：Windows `os.replace` 失败走同路径覆写前须保留可恢复副本（`.bak` 或保留完整 tmp）；写失败不得截断 dest 后删除唯一完好副本 | 横切 |
| **AC-SFC-NR-01** | Ambiguous 意图卡三选一仍可用（回归） | 每波 |
| **AC-SFC-NR-02** | Narrative「按章导出」CTA 仍可用（回归） | 每波 |
| **AC-SFC-15** | 真人 N≥5 狗粮通过方可对外宣布 | 宣布 |

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 空槽过多导致「没写完」误解 | P-SFC-08 弱提示 + 精修「添加一句」；空优于假句不变 |
| stale 改名导致 Help/深链死链 | W1 全文扫描 + 重定向文案 |
| Sparse 跳过 G1 降低结构质量 | 仅 1–9；≥10 保持确认；默认分章回归测试 |
| 模型下载阶段暴露「AI/模型」吓人 | 主句用「识图」不提 HF/CLIP/权重文件名 |
| Agent 试用假阳性 | 宣布完成绑定 AC-SFC-15 真人 |

### 11.2 开放问题（OQ）· 2026-07-18 已关闭

| ID | 问题 | 决议 | 写入 |
|----|------|------|------|
| **OQ-SFC-01** | `2025东澳岛9` 回退策略 | 去尾数字后 2–6 字地名 → `{地名} · 旅行`；否则 `旅行 · {日期}`；禁裸尾数字 | §3.2 |
| **OQ-SFC-02** | 精细制作是否跳过 G1 | **否**；仅快速分享 Sparse 跳过 | §3.6 |
| **OQ-SFC-03** | stale 主词一字面 | **分享图需更新**；「导出后再分享」仅可作副文 | §0.2 / §3.4 |
| **OQ-SFC-04** | 存量是否批量写回 | **读时计算**即可；批量写回非 W0 必做 | §6 |

---

## 12. 质量收口（2026-07-18 代码审查 · **全部必修**）

> 触发与总表：[quality-review-remediation-2026-07-18.md](./acceptance-records/quality-review-remediation-2026-07-18.md)。

### 12.1 displayTitle 同源加严（P2 · AC-SFC-12 · D-SFC-03）

| 项 | 冻结 |
|----|------|
| 问题 | JS `resolveDisplayTitle` 最终硬编码「旅行 · 游记」，Python 走日期兜底 → 书架/封面与导入过程文案不一致 |
| 合同 | FE 必须复刻 BE `_date_fallback_label` / `_fallback_display`；同 fixture 同测同例 |
| 优先 | 有后端已写 `meta.displayTitle` 时 FE 优先采用；仅缺失时本地兜底，且兜底规则同源 |

### 12.2 trip.json 保全（P1 · AC-SFC-13）

| 项 | 冻结 |
|----|------|
| 问题 | Windows AV 忙锁回退 `open(dest,"w")` 截断后若写失败，上层再删 tmp → 不可恢复丢数据 |
| 合同 | 回退写前备份或失败保留 tmp；错误信息须含恢复路径提示 |
| 附带 | 原子写与回退写 `newline` 一致；CAS 的 expected revision 与磁盘读口径统一（migrate 或不 migrate 两端一致） |

### 12.3 工程卫生（P3 · 本收口一并修）

| 项 | 要求 |
|----|------|
| 写锁字典 | 长生命周期下避免无界增长（WeakValue / 上限）或文档化可接受 |
| 展示插入 | `displayTitle` 使用 `textContent` / 框架转义，禁止 `innerHTML` 注入文件夹名 |

---

## 附录 A · 试用吐槽 → 合同映射

| 试用 | 合同 |
|------|------|
| C1 | D-SFC-01/02 · AC-SFC-01/02 |
| C2 | D-SFC-03 · AC-SFC-03 |
| C3 | D-SFC-04/05 · AC-SFC-04/05 |
| C4 | D-SFC-06 · AC-SFC-06 |
| C5 | §3.5 · AC-SFC-07 |
| C6 | D-SFC-07 · AC-SFC-08/09 |
| C7 | D-SFC-08 · AC-SFC-10 |
| C8 | §3.8 · AC-SFC-11 |
| L1–L9 喜欢项 | D-SFC-10 回归保护 |

## 附录 B · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v1.0.0** | 2026-07-18 | 首稿：基于八席试用收口；Draft 待评审 |
| **v1.0.0+doc** | 2026-07-18 | Doc 包齐：ACCEPTANCE · IMPLEMENTATION · 线框 F1–F5 · 狗粮清单 · README 索引 |
| **v1.0.1** | 2026-07-18 | 跨职能 Conditional Go · BLK-01～08 · OQ-01～04 关闭 · 可 Kickoff W0 |
| **v1.0.2** | 2026-07-18 | §12 质量收口全部必修：AC-SFC-12 displayTitle FE/BE 日期兜底同源；AC-SFC-13 trip.json 忙锁回退数据保全 |
