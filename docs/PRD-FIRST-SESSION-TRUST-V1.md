# Travelogue · 首访可信体验优化 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio（本机 Studio / 桌面打包同等体验） |
| **文档版本** | **v1.0.3** |
| **状态** | **Conditional Go · 跨职能 MF + 用户联席 USR 已回写** · **W0–W2 工程已合入** · 完成宣布待狗粮 |
| **主题代号** | 「首访可信」— 进度不假死 · 成功面必出 · 分享面敢秀 |
| **触发来源** | 2026-07-17 CXO 空态首访模拟测试（示例相册 → 成稿 → 验货 → 长图） |
| **前置条件** | Studio 首页 v2（M21）；FTUE V1 W0–W2 合同有效；导出门面 V1；L0 无 Key 可成稿 |
| **关联文档** | [PRD-FTUE-OPTIMIZATION-V1.md](./PRD-FTUE-OPTIMIZATION-V1.md) · [PRD-SHARE-READY-OPTIMIZATION-V1.md](./PRD-SHARE-READY-OPTIMIZATION-V1.md) · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md)（Importing 次区教育 · 不改本主题进度合同） · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) · [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md) · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) · [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) |
| **评审记录** | [跨职能评审](./acceptance-records/first-session-trust-v1-review-2026-07-17.md) · [用户联席](./acceptance-records/first-session-trust-v1-user-panel-2026-07-17.md) |
| **验收** | [ACCEPTANCE-FIRST-SESSION-TRUST-V1.md](./ACCEPTANCE-FIRST-SESSION-TRUST-V1.md)（本文 §10 为索引） |
| **实施清单** | [IMPLEMENTATION-FIRST-SESSION-TRUST-V1.md](./IMPLEMENTATION-FIRST-SESSION-TRUST-V1.md) |
| **线框** | [wireframes/first-session-trust-v1-wireframe.html](./wireframes/first-session-trust-v1-wireframe.html) · F1–F5（本文 §9） |
| **评审模板** | [acceptance-records/first-session-trust-v1-review-TEMPLATE.md](./acceptance-records/first-session-trust-v1-review-TEMPLATE.md)（已产出正式纪要，模板保留备查） |
| **更新日期** | 2026-07-17 |

> **v1.0.1 评审回写摘要（跨职能 Conditional Go）**
>
> - BLK-01～03：FTUE / Help / Share-Ready 交叉脚注（DOC-FST；相邻 PRD 另波次回写）  
> - BLK-04：OQ-FST-01～03 **已关闭**（§11）  
> - BLK-05 / USR-01：成功面主操作 =「在文件夹中显示」  
> - BLK-06：AC-FST-04 必做 e2e  
> - BLK-07：§4.5 为禁词表增量  
> - BLK-08：线框 F1–F4 = W0 UI 挡门  
> - **本轮不动代码**；编码 Kickoff 另排期

> **v1.0.2 用户联席回写摘要（八席 Persona）**
>
> - **USR-02** → D-FST-13：禁止自动 reveal；仅点击「在文件夹中显示」  
> - **USR-03** → §2.4：L0/FirstSuccess 勿承诺杂志级文案  
> - **USR-04** → §3.5：回退名同步 FirstSuccess / 书架展示名  
> - **USR-05** → §0.2：Dock「发微信群」终点语义保留 ≠ 教操作  
> - **USR-06** → §2.3 / §9：真人 N≥5 才对外宣布完成  
> - **USR-07** → §4.3：进度/成功面零工程词 |

> **v1.0.3 交叉脚注（2026-07-17 · DOC-WT / BLK-02）**
>
> [Wait Tips](./PRD-WAIT-TIPS-V1.md) 可嵌于 Importing 进度壳**次区**（阶段主句 / 慢安抚下方），属等待教育，**不修订**本主题：进度诚实、慢安抚次行、FirstSuccess ≤1s、成功面不教微信。  
> Tips 失败或关闭时，本主题进度面须仍完整合格。

> **定位**
>
> FTUE / Help / 敢发闭环已分别定义空态敢试、帮助分层、意图与真图样品。  
> **本 PRD 不重做首访叙事**，只收口 2026-07-17 实测中仍会让用户觉得「像坏了 / 不敢发」的三类断裂：  
> **① 等待与真实阶段不同步** · **② Job 已成功但界面未切换** · **③ L0/stub 分享面文案与元数据毁分享欲**。
>
> **一句话目标**：空态用户不配 API、不读 docs，一次会话内完成  
> **敢点示例 → 清楚在等什么 → 成功面明确停住 → 打开成片后愿意发出去**。
>
> **产品共识（五条铁律）**
>
> 1. **进度诚实** — 计数/百分比必须对应真实阶段；禁止「6/6 已处理」后仍无限「比预期久一些」而无阶段切换。  
> 2. **终端态必切换** — `status=succeeded|failed|cancelled` 后 **≤1s** 离开忙碌态；禁止成功面依赖偶然竞态。  
> 3. **成功面停住，但不教微信** — 用户非常清楚怎么用微信；成功面只确认「已保存 + 打开位置」，**禁止**发群步骤教学文案。  
> 4. **分享面敢秀** — 封面 / hook / 章名 / 图注 / 长图默认面禁止说明书腔、文件夹名腔、相机 EXIF 泄漏。  
> 5. **不另起成功面栈** — 复用 FirstSuccess / Task Dock；禁止第四套 Modal。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 与相邻主题的边界（拥有 vs 依赖 vs 修订） |
| §0.2 | 相对 FTUE/Help「发群引导」的产品修订 |
| §1 | 实测方法、问题清单（P-FST-*） |
| §2 | 目标 / 非目标 / 成功指标 |
| §3 | 体验合同与冻结决策（D-FST-*） |
| §4 | 触点与文案矩阵 |
| §5 | 工程任务 |
| §6～§8 | 错误 / 埋点 / 非功能 |
| §9 | 线框与里程碑 |
| §10 | 验收 AC |
| §11 | 风险与 OQ |
| 附录 | 实测摘要 · 版本记录 |

### 0.1 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [FTUE](./PRD-FTUE-OPTIMIZATION-V1.md) | **部分 supersede · 联合挡门** | **接管**导入/长图「终端态 UI 切换」与进度诚实；**修订** FTUE §3.3「发群主句第一可读行」——见 §0.2 |
| [Help](./PRD-HELP-ONBOARDING-V1.md) | **修订成功面 COPY 优先级** | Help 抽屉 H4 仍可保留「怎么发」供主动查阅；**默认成功面不再强制展示发群三要素** |
| [Wait Tips](./PRD-WAIT-TIPS-V1.md) | **并行 · 次区挂载** | Importing 壳可挂可关闭教育卡；**不改** stage 主句 / 慢安抚 / FirstSuccess（见 v1.0.3） |
| [Share-Ready](./PRD-SHARE-READY-OPTIMIZATION-V1.md) | **并行不抢** | 真图样品 / 意图卡 / `kept_n` 仍归 Share-Ready；本主题只挡「等待假死 + stub 敢发底线」 |
| [Export Facade](./PRD-PREVIEW-EXPORT-FACADE-V1.md) | **复用** | Task Dock 成功面组件；改 COPY 槽位优先级，不新建栈 |
| [Copy](./PRD-COPY-OPTIMIZATION.md) / [Chapter Naming](./PRD-CHAPTER-NAMING.md) | **本主题定义最低门槛；深度润色归原轨** | W0 挡说明书腔 / 「日期续」刺耳形态 / EXIF；杂志级文案仍归 Copy/章名 |
| [L0 Guidance](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) | **依赖** | 无 Key 永不整单失败；本主题断言「主链可走完且敢秀」 |
| [UX Trust](./PRD-UX-TRUST-V1.md) | **交叉** | 工程提示不进分享面；与 Trust 禁词表对齐增量 |
| Installer | **不做** | 非开发者分发仍归 Installer |

### 0.2 产品修订：不教微信怎么发（2026-07-17）

| 原合同（摘要） | 本主题修订 |
|----------------|------------|
| FTUE G-FTUE-04 / §3.3：成功面第一可读行 = 发群三要素 | **改为**：第一可读行 = **已保存确认**（含可读文件名或中文标题）；次要动作 = **在文件夹中显示** |
| Help `publishGuideFallback` 强制进默认成功面 | **默认成功面不展示**发群步骤；`publishGuide` 仅进入 Help 抽屉 / 用户主动打开的帮助 |
| Share-Ready「落盘 ≠ 完成」以发群指引为终点 | **修订为**：落盘后必须有**稳定可见的成功确认**；**完成定义不含**教用户如何操作微信 |

> **定案理由**：目标用户对微信极为熟练；教程式文案占用成功面注意力，且掩盖「文件是否落盘 / 在哪」的真正不确定感。
>
> **澄清（USR-05）**：Preview Dock / 配方 CTA 可见文案「发微信群」表示**交付终点**（导出可发群的长图），**不等于**在成功面教用户如何操作微信。二者并存、不冲突。

---

## 1. 背景与问题

### 1.1 实测方法（可复现）

| 项 | 约定 |
|----|------|
| **环境** | Windows · 本机 Studio · Chrome/Edge |
| **空态** | `python -m travelogue studio --trips-dir <空目录> --no-open --port <闲置端口>` |
| **首访** | 清该 origin 的 `localStorage` / `sessionStorage` 后打开首页 |
| **样片** | 向导「用示例照片试一次」（`useDemoAlbum: true`） |
| **对照** | 真实相册 trip（如书架已有作品）验货文案/章名/EXIF |

### 1.2 目标态剧本（To-Be）

```
第一次打开 Studio（空 trips）
  → 能力卡 →「开始制作」
  → 向导：「用示例照片试一次」
  → 导入进度：
       · 照片处理计数与阶段人话同步
       · 进入配文/排版阶段时，文案切换（不得停在「已处理 N/N」假死）
  → FirstSuccess 在 job.succeeded 后 ≤1s 出现（忙碌态关闭）
  → 打开卷轴预览：封面/章名/图注达到「敢秀」底线
  → Dock「发微信群」→ 导出进度反映真实阶段（禁止长期假 0%）
  → 长图 succeeded：
       · Task Dock 成功面稳定可见 ≥3s（或用户关闭前）
       · 主句：已保存（可读名）
       · 次要：在文件夹中显示
       · 不出现「按顺序发到微信群」类教学句
```

### 1.3 问题清单（P-FST-*）

| ID | 问题 | 严重度 | 波次 | 归属 |
|----|------|--------|------|------|
| **P-FST-01** | 导入进度停在「已处理 N/N」+「比预期久一些」，Job 已成功或已进入后段 | **P0** | W0 | **本主题** |
| **P-FST-02** | `status=succeeded` 后忙碌态未及时切到 FirstSuccess（竞态/刷新链） | **P0** | W0 | **本主题** |
| **P-FST-03** | 长图导出 UI 长期停在「正在准备导出… 0%」，实际已在合成甚至已落盘 | **P0** | W0 | **本主题** |
| **P-FST-04** | 长图成功面闪现/消失，用户不确定是否完成 | **P0** | W0 | **本主题**（修订 FTUE 成功面；**不含**发群教学） |
| **P-FST-05** | L0/stub hook、图注说明书腔（「抬头看见…」「…慢慢翻」） | **P0** | W1 | **本主题最低门槛** + Copy |
| **P-FST-06** | 封面/标题像文件夹名（如「王丹昙华林2」）且无可读回退 | **P1** | W1 | **本主题**（规则回退）+ 精修可改 |
| **P-FST-07** | 章名「日期续」刺耳 | **P1** | W1 | **本主题挡门** + Chapter Naming |
| **P-FST-08** | 相机 EXIF（Make/Model）进入读者面图注 | **P1** | W1 | **本主题** |
| **P-FST-09** | 封底「Colophon」英文化 / 张数与精选数不一致 | **P2** | W2 | **本主题**（文案）+ 计数同源指针 |
| **P-FST-10** | 首页 showcase / 意图卡 / 真图样品 | — | — | **不做**；归 Share-Ready |
| **P-FST-11** | 发群步骤教学弱/不稳 | — | — | **明确不做**（§0.2） |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 可观测 |
|----|------|--------|
| **G-FST-01** | 导入等待全程可解释，无「假死」感 | AC-FST-01～03 |
| **G-FST-02** | Job 终端态 ≤1s 切换到成功/失败面 | AC-FST-04～05 |
| **G-FST-03** | 长图导出进度诚实；成功面稳定停住 | AC-FST-06～08 |
| **G-FST-04** | L0/示例成片达到「敢秀」文案底线 | AC-FST-09～12 |
| **G-FST-05** | 成功面不教微信操作 | AC-FST-13 |

### 2.2 非目标

| 不做 | 原因 |
|------|------|
| 教用户如何把图发到微信群/朋友圈 | 产品决策 §0.2；用户已熟练 |
| 重做空态 / 示例入口 / 能力卡 | 已归 FTUE |
| 首页真图样品 / Ambiguous 意图卡 | 已归 Share-Ready |
| 杂志级文案深度润色 / LLM 叙事质量 | 归 Copy；本主题只定底线 |
| 章名算法全面重做 | 归 Chapter Naming；本主题只禁「日期续」等刺耳形态 |
| 一键调起微信 / 系统分享 Sheet | 平台限制；非本 V1 |
| Installer / 非开发者分发 | 归 Installer |
| 精修深度 / G1 | 另轨 |

### 2.3 成功指标（狗粮目标 · 非发布硬 KPI）

| 指标 | 目标 | 样本建议 |
|------|------|----------|
| 示例导入：succeeded → FirstSuccess 可见 | **100%** · ≤1s | N≥5 |
| 导入过程无「N/N + 慢提示」僵持 >8s（无阶段文案变化） | **0** | N≥5 |
| 长图 succeeded → 成功面可见 ≥3s | ≥95% | N≥5 |
| 默认成功面出现发群教学句 | **0** | 文案断言 |
| 示例/L0 封面+开篇含说明书腔或 EXIF | **0** | 单测 + 手测 |

**主题对外宣布完成（USR-06）**：须 **真人** 可用性样本 N≥5（建议含 U1 分享者 · U3 空态首访 · U7 家庭组织者）；模拟联评 / Agent 狗粮**不能替代**。

### 2.4 对外沟通边界（USR-03）

| 阶段 | 可说 | 勿说 |
|------|------|------|
| L0 / 无 Key / 示例 FirstSuccess | 已生成游记画册；可验货、可导出长图 | 「杂志级文案已就绪」「AI 已写好可直接发」 |
| W1 敢秀底线达成前 | 版式可用；文案可改 | 对外宣称「文案已杂志级」 |

---

## 3. 体验合同与冻结决策

### 3.1 导入进度诚实合同（P-FST-01）

| 必须 | 禁止 |
|------|------|
| `stage` / `stageIndex` 变化时，用户可见主文案同步变化 | 照片计数已到 N/N 后仍只显示「已处理 N/N」超过 **2s** |
| 进入 narrate / render 时使用阶段人话（见 §4.2） | 用慢安抚句（「比预期久一些」）**替代**阶段说明 |
| 慢安抚句仅作**次行**，且阶段主句仍在 | 主区域只剩慢安抚、看不出在做什么 |
| L0/example 冷启动组件准备有独立 stageHint | 静默下载/准备却显示「正在整理照片」 |

**阶段主句冻结（W0）**

| `stage`（或等价） | 用户可见主句 |
|-------------------|--------------|
| `ingest` / 处理媒体 | 正在整理照片…（可附 `已处理 a/b 张`） |
| `curate` | 正在分章与挑选… |
| `narrate` | 正在撰写短文案…（L0 可为「正在生成游记文案…」） |
| `render` | 正在排版杂志页… |
| 冷启动 `preparing_*` | 沿用 FTUE stageHint 人话 |

### 3.2 FirstSuccess 终端切换合同（P-FST-02）

当 `GET /__travelogue/status` 返回 `status=succeeded`：

1. **立即**（目标 ≤300ms，验收 ≤1s）关闭导入忙碌壳。  
2. 调用既有 `showFirstSuccess`；**不得**被 `refreshTrips` / 书架重绘拖住超过验收阈值——trips 刷新可并行，成功面优先。  
3. 失败/取消同理：离开忙碌态 → 既有失败/取消面。  
4. **禁止**依赖「下一次轮询碰巧」才切换；终端态必须在当前轮询回调内处理完。

### 3.3 长图导出进度合同（P-FST-03）

| 必须 | 禁止 |
|------|------|
| 接受 Job 后首屏文案 ≤500ms 变为「正在生成可发微信的长图…」或阶段人话 | 长期「正在准备导出…」+ **0%** 无变化（>3s） |
| 百分比或阶段条与服务端 `stage`/`progress` 同源；无进度时用**不确定进度**（indeterminate），不得假 0% | 用 0% 表示「未知」 |
| `stageHint` 作分类/次行，不泄漏工程词（对齐 Share-Ready FE-SR-07） | 「打开浏览器」「Playwright」等工程句进主句 |

### 3.4 长图成功面合同（P-FST-04 · 修订 FTUE §3.3 · BLK-05 · USR-01/02）

长图 Job `succeeded` 后：

1. **可见成功面**：复用 Preview V3 **Task Dock** `showSuccess`（或等价既有门面）；禁止新平行栈。  
2. **第一可读行（冻结）**：

   > 长图已保存。

   若可知展示标题（含回退名）：`《{displayTitle}》长图已保存。`  
   若分段：`长图已保存（第 n 段）` 或等价短句。

3. **主操作（冻结 · USR-01）**：**在文件夹中显示** — 成功面 **唯一实心主按钮**（主色/金色）；「关闭」为次要描边或文字按钮。  
4. **禁止自动 reveal（USR-02 · D-FST-13）**：Job 成功**不得**自动调用「在文件夹中显示」/ 弹出资源管理器；**仅**用户点击主操作后才 reveal。  
5. **禁止**默认成功面出现以下教学句（及同义改写）：  
   - 「按文件名顺序发到微信群」  
   - 「选图 → 发送」步骤条  
   - 「打开微信 → …」类指引  
6. Help 抽屉仍可保留发群说明，供用户**主动**打开「?」。  
7. **可验收**：成功面可见 ≥ **3s**，或用户主动关闭前保持；自动收起后，再次点击导出入口须能看到「已有长图 / 可更新」类状态，而不是沉默无反馈。

### 3.5 分享面「敢秀」底线合同（P-FST-05～08）

适用于：**卷轴读者面**、**长图默认导出面**、**FirstSuccess 封面缩略**（若展示文案）。

| 槽位 | 必须 | 禁止（进入读者/分享面） |
|------|------|------------------------|
| **hook / 开篇** | 可空；有则像人话短句 | 「慢慢翻」「抬头看见{标题}」「关于{X}的 N 天」说明书腔 |
| **图注 / caption / alt 可见句** | 可空；优先地点/时间短标签 | `{标题}` 填槽复读；**相机 Make/Model**（如 `NIKON CORPORATION…`） |
| **章名 title** | 日期或地名标签可接受 | 「{日期}续」；「抵达/尾声」文艺模板（沿用 Chapter Naming 铁律） |
| **杂志名 / 封面 title** | 优先用户意图标题；否则「某地 · 旅行」或日期范围可读回退 | 原始文件夹名噪音（尾缀数字、无空格粘连手机目录名）裸上封面 |
| **封底** | 中文「辑封」或产品既有中文称呼；张数与精选/版面数同源 | 裸「Colophon」作唯一标题（W2） |

**文件夹名回退规则（W1 · 冻结意图 · USR-04）**

当 `meta.title` 命中「像目录名」启发（**W1 仅中文启发式** · OQ-FST-02 已关闭）：

- 尾缀纯数字（`…2`、`…01`）  
- 无分隔的长粘连中文+数字  
- 明显导出目录腔  

则 **展示名**（`displayTitle`）使用回退：`{主地名或「旅行」} · {日期或「游记」}`，并用于：

1. 卷轴/长图封面主标题  
2. **FirstSuccess** 标题句  
3. **书架**卡片主标题  

**原名**仍可在精修中编辑；不在本主题做 NLP 诗意命名。

**章名「续」替换一字面（OQ-FST-01 已关闭）**

| 条件 | 章名 |
|------|------|
| 同日多章且有时段信号 | `{日期} · {上午\|下午\|傍晚\|晚上}` |
| 同日多章且无时段 | `{日期}（2）` / `{日期}（3）` … |
| 任意 | **禁止** `{日期}续` |

### 3.6 冻结决策（D-FST-*）

| ID | 决策 |
|----|------|
| **D-FST-01** | 进度主句按 stage 切换；慢安抚不得取代主句 |
| **D-FST-02** | `succeeded` → 成功面 ≤1s；trips 刷新不阻塞成功面 |
| **D-FST-03** | 导出禁止假 0%；无进度用 indeterminate |
| **D-FST-04** | 成功面主句 = 已保存；**不教微信** |
| **D-FST-05** | Help 可保留发群说明；默认成功面不引用 `publishGuide` 教学句 |
| **D-FST-06** | L0/stub 说明书腔禁止进分享面（空优于假句 · OQ-FST-03） |
| **D-FST-07** | 相机 EXIF 禁止进读者面可见图注 |
| **D-FST-08** | 「日期续」禁止；一字面见 §3.5（OQ-FST-01） |
| **D-FST-09** | 文件夹名噪音不得裸上封面；回退名同步 FirstSuccess/书架（USR-04） |
| **D-FST-10** | 不新建成功面栈；复用 FirstSuccess / Task Dock |
| **D-FST-11** | Share-Ready 真图/意图卡不在本主题范围 |
| **D-FST-12** | 本主题修订 FTUE §3.3 / G-FTUE-04 中「发群主句」条款；FTUE 其余空态/示例合同不变 |
| **D-FST-13** | 长图成功**禁止自动 reveal**；仅点击「在文件夹中显示」（USR-02） |
| **D-FST-14** | 成功面主操作 =「在文件夹中显示」实心钮（USR-01 / BLK-05） |

---

## 4. 触点与文案矩阵

### 4.1 触点总表

| ID | 触点 | 触发 | 文案要点 |
|----|------|------|----------|
| **T-FST-IMPORT** | 导入忙碌壳 | import job | §3.1 / §4.2 |
| **T-FST-FIRST** | FirstSuccess | import succeeded | 既有 D-HELP-10 结构；转化句可保留 |
| **T-FST-LS-PROG** | 长图进度 | longshot running | §3.3 / §4.3 |
| **T-FST-LS-OK** | 长图成功面 | longshot succeeded | §3.4 / §4.4 |
| **T-FST-SHARE** | 卷轴/长图读者面 | render 结果 | §3.5 / §4.5 |
| **T-FST-HELP** | 帮助抽屉 H4 | 用户点「?」 | 可保留发群说明（非默认强弹） |

### 4.2 导入进度文案

| 槽位 | 冻结 |
|------|------|
| 标题 | 正在生成你的游记画册…（可保持现状） |
| 主句 | 随 stage 变（§3.1 表） |
| 次行 | 已处理 a/b 张（仅 ingest）；或慢安抚（仅次行） |
| 来源眉题 | 来源 · 示例相册 / 文件夹名（可保持） |

### 4.3 长图进度文案（USR-07）

| 槽位 | 用 | 不用 |
|------|----|------|
| 主句 | 正在生成可发微信的长图… | 正在准备导出…（作为唯一长期文案） |
| 次行 | 按章 · 高清（若配方提供） | 打开浏览器 / Chromium / Playwright / jobId |
| 进度 | 真实 % 或 indeterminate | 假 0% |

### 4.4 长图成功面文案（唯一默认 · BLK-05 · USR-01）

| 槽位 | **冻结 To-Be** |
|------|----------------|
| 主句 | 长图已保存。 / 《{displayTitle}》长图已保存。 |
| **主操作** | **在文件夹中显示**（实心主钮；点击才 reveal） |
| 次操作 | 关闭 |
| **禁止** | 任何发群步骤教学（§3.4.5）；禁止成功时自动弹文件夹 |

### 4.5 分享面禁词 / 禁形态（增量 · BLK-07）

| 禁止形态 | 处理 |
|----------|------|
| 「慢慢翻」「抬头看见…」「下次再见，{标题}」等填槽 | 空或换不复读标题的短句；W1 规则挡 |
| 「{日期}续」 | 见 §3.5 OQ-FST-01 一字面 |
| `NIKON` / `Canon` / `Apple` + Model 串 | 读者面剥离；可留 meta 内部 |
| 文件夹名噪音作封面主标题 | §3.5 回退规则（含 FirstSuccess/书架） |
| 「Colophon」唯一眉题 | W2 →「辑封」或去眉题只留统计 |

**声明（BLK-07）**：本表为 [FTUE §4.3](./PRD-FTUE-OPTIMIZATION-V1.md) / [UX Trust](./PRD-UX-TRUST-V1.md) / [Share-Ready §4.4](./PRD-SHARE-READY-OPTIMIZATION-V1.md) 禁词表的 **增量扩展**；**禁止**再平行维护第三套完整禁词表。工程词仍禁。

**2026-07-18 增量（Share-Face Closeout · DOC-SFC / BLK-03）**：[PRD-SHARE-FACE-CLOSEOUT-V1 §4.2](./PRD-SHARE-FACE-CLOSEOUT-V1.md) 并入本表扫描范围——**竖幅/横幅（作图注中心词）**、**弱枚举时段句**（如「夜景，白天」）、**杂志全名整册复读填 alt/图注**。仍禁止另起平行禁词表。

---

## 5. 工程任务

### 5.1 前端

| ID | 内容 | 波次 |
|----|------|------|
| **FE-FST-01** | 导入轮询：stage 主句映射；N/N 后强制切 stage 文案 | W0 |
| **FE-FST-02** | `succeeded` 回调内先 `showFirstSuccess` / 关忙碌，再 `refreshTrips`（或并行且不 await 阻塞） | W0 |
| **FE-FST-03** | 长图进度：去掉假 0%；indeterminate + 人话主句 | W0 |
| **FE-FST-04** | Task Dock 成功面 COPY 按 §4.4；剥离默认 `publishGuide` 教学句；主钮实心「在文件夹中显示」 | W0 |
| **FE-FST-05** | 成功面可见时长 / 关闭前保持；**去掉自动 reveal**；回归 e2e | W0 |
| **FE-FST-06** | （可选）FirstSuccess 转化句保留「用自己的照片再做一本」；L0 勿承诺杂志级文案（USR-03） | W1 |

### 5.2 后端 / 管线

| ID | 内容 | 波次 |
|----|------|------|
| **BE-FST-01** | import job `stage`/`stageHint` 在 narrate/render 段必更新（避免长期停在 ingest 计数语义） | W0 |
| **BE-FST-02** | longshot job 进度字段对客户端可用（或明确无进度 → 前端 indeterminate） | W0 |
| **BE-FST-03** | stub/L0 narrate：禁说明书腔模板；宁可空 | W1 |
| **BE-FST-04** | 读者面渲染剥离 camera Make/Model 可见图注 | W1 |
| **BE-FST-05** | 章名禁止「续」后缀形态；可区分回退 | W1 |
| **BE-FST-06** | 封面展示名：目录名噪音检测 + 回退 | W1 |
| **BE-FST-07** | 封底中文化 / 张数同源（W2） | W2 |

### 5.3 测试

| ID | 内容 | 波次 |
|----|------|------|
| **QA-FST-01** | Playwright：示例导入 succeeded → FirstSuccess ≤1s（**BLK-06 必做**） | W0 |
| **QA-FST-02** | 单测/契约：成功面 COPY 不含发群教学句；无自动 reveal | W0 |
| **QA-FST-03** | Playwright：长图成功面 ≥3s 可见；主钮为「在文件夹中显示」 | W0 |
| **QA-FST-04** | 单测：stub 禁词 / EXIF 不进读者面 | W1 |
| **QA-FST-05** | 手测狗粮脚本（附录 A）N≥5 | W1 |

### 5.4 文档

| ID | 内容 | 波次 |
|----|------|------|
| **DOC-FST-01** | 回写 FTUE §3.3 / G-FTUE-04 交叉引用 → 以本文 D-FST-04/05/12 为准 | W0 |
| **DOC-FST-02** | Share-Ready「落盘≠完成」脚注：完成=稳定成功确认，非微信教学 | W0 |
| **DOC-FST-03** | Help：标明发群说明为**按需查阅**，非默认成功面合同 | W0 |

---

## 6. 错误与降级

| 场景 | 用户可见 | 系统行为 |
|------|----------|----------|
| 导入失败 | 既有失败面 + 可重试 | 关忙碌态 |
| 长图失败 | Task Dock 错误面 | 不假成功 |
| 进度字段缺失 | indeterminate + 主句人话 | 不显示 0% |
| 标题回退触发 | 封面用回退名 | 精修仍见可编辑原 title |
| stub 无合格句 | 槽位留空 | 不填说明书腔 |

---

## 7. 埋点（建议）

| 事件 | 属性 | 用途 |
|------|------|------|
| `import_ui_terminal_ms` | jobId, ms_from_succeeded | 挡 P-FST-02 |
| `import_stage_stall` | stage, stall_ms | 挡 P-FST-01 |
| `longshot_progress_mode` | percent \| indeterminate | 挡假 0% |
| `longshot_success_visible_ms` | ms | 挡 P-FST-04 |
| `share_surface_blocked` | reason=stub_phrase\|exif\|folder_title\|chapter_xu | W1 质量 |

---

## 8. 非功能

| 项 | 要求 |
|----|------|
| 性能 | 成功面切换不因书架全量刷新阻塞 >1s |
| 兼容 | 无 Playwright 时长图失败路径保持既有错误面（不在本主题扩能力） |
| 无障碍 | 成功面 focus 移入面板；忙碌态 `aria-busy` 在终端态清除 |
| 文案语言 | 默认 `locale=zh`；不扩展海外 IG |

---

## 9. 线框与里程碑

### 9.1 线框帧（评审用）

| 帧 | 内容 | 挡门 |
|----|------|------|
| **F1** | 导入进度：ingest → curate → narrate → render 主句切换；慢安抚仅次行 | W0 |
| **F2** | Job succeeded → FirstSuccess（忙碌壳消失）时序 | W0 |
| **F3** | 长图进度 indeterminate / 真实 %；禁假 0% | W0 |
| **F4** | 长图成功面：已保存 + 打开文件夹；无发群教学 | W0 |
| **F5** | 分享面对照：修前说明书腔/EXIF/「日期续」→ 修后敢秀底线 | W1 |

HTML 线框：[first-session-trust-v1-wireframe.html](./wireframes/first-session-trust-v1-wireframe.html)（已齐）。  
评审纪要模板：[first-session-trust-v1-review-TEMPLATE.md](./acceptance-records/first-session-trust-v1-review-TEMPLATE.md)。

### 9.2 里程碑

| 门 | 含义 | 退出标准 |
|----|------|----------|
| **W0 Go** | 可等：进度诚实 + 终端切换 + 成功面稳定（不教微信） | AC-FST-01～08、13 绿 |
| **W1 Go** | 敢秀：stub/EXIF/章名/封面回退底线 | AC-FST-09～12 绿 + 手测 N≥5 |
| **W2 Go** | 封底中文化与计数一致等抛光 | AC-FST-14（可选） |
| **主题完成宣布** | 对外宣称本主题完成前 | **真人** N≥5（USR-06；含 U1/U3/U7） |

---

## 10. 验收 AC

| ID | 断言 | 波次 |
|----|------|------|
| **AC-FST-01** | 示例导入过程中，离开 ingest 后主句不再仅为「已处理 N/N」 | W0 |
| **AC-FST-02** | 慢安抚出现时，阶段主句仍可见 | W0 |
| **AC-FST-03** | 任一 stage 文案停滞（无变化）>8s 视为失败（狗粮） | W0 |
| **AC-FST-04** | `status=succeeded` 后 ≤1s 出现 FirstSuccess，忙碌壳关闭 | W0 |
| **AC-FST-05** | `refreshTrips` 失败不阻止 FirstSuccess | W0 |
| **AC-FST-06** | 长图开始后 >3s 不得仍显示「0%」作为唯一进度 | W0 |
| **AC-FST-07** | 长图主句为人话（§4.3），无工程词 | W0 |
| **AC-FST-08** | 长图 succeeded → 成功面可见 ≥3s 或至用户关闭 | W0 |
| **AC-FST-08b** | 成功时**不**自动 reveal；仅点击主钮后打开文件夹 | W0 |
| **AC-FST-08c** | 成功面主操作可见文案为「在文件夹中显示」且为实心主钮 | W0 |
| **AC-FST-09** | 示例成片封面/开篇不含 §4.5 说明书腔 | W1 |
| **AC-FST-10** | 读者面可见文案不含相机 Make/Model | W1 |
| **AC-FST-11** | 无章名等于「*续」模式；符合 §3.5 一字面 | W1 |
| **AC-FST-12** | 目录名噪音 title 触发回退展示名（封面 + FirstSuccess + 书架） | W1 |
| **AC-FST-13** | 默认长图成功面 DOM/文案不含发群步骤教学句 | W0 |
| **AC-FST-14** | 封底不以「Colophon」为唯一眉题；张数与版面精选同源 | W2 |
| **AC-FST-15** | 真人 N≥5 手测签（主题完成宣布门 · USR-06） | 完成门 |

---

## 11. 风险与 OQ

| ID | 项 | 状态 |
|----|----|------|
| **OQ-FST-01** | 「日期续」替换一字面 | **已关闭**：时段优先，否则（2）（3）；见 §3.5 |
| **OQ-FST-02** | 英文目录名检测 | **已关闭**：W1 仅中文启发式 |
| **OQ-FST-03** | stub 全面改空是否太素 | **已关闭**：空优于假句 |
| **Risk-01** | 与 FTUE 发群合同文档漂移 | DOC-FST-01；跨职能 BLK-01 |
| **Risk-02** | Share-Ready 成功面联合挡门仍写发群句 | DOC-FST-02；BLK-03 |

---

## 附录 A · 2026-07-17 CXO 实测摘要

| 步骤 | 观察 | 映射 |
|------|------|------|
| 能力卡 / 向导示例 | 清晰，敢点 | （非本主题；FTUE 已覆盖） |
| 导入 6/6 后长时间慢提示 | 焦虑「是不是坏了」；后端已 succeeded | P-FST-01/02 |
| 卷轴成片 | 版式 Wow | Delight · 非问题 |
| stub 文案 /「日期续」/ 文件夹封面名 / EXIF | 不敢发 | P-FST-05～08 |
| 长图 CTA「发微信群」 | 终点清晰 | Delight |
| 导出 0% 久停；成功面不稳 | 不确定是否完成 | P-FST-03/04 |
| 发群教学 | **产品决策：用户不需要教** | P-FST-11 不做 |

复现锚点：

- 空态：`--trips-dir <empty> --port 8777` + 清存储  
- 示例导入：`POST /__travelogue/import` · `useDemoAlbum: true`  
- 终端态：`GET /__travelogue/status?jobId=…` → `succeeded` 与 UI 忙碌壳并存即失败  
- 长图：Preview Dock「发微信群」→ Task Dock 成功面 COPY

---

## 附录 B · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v1.0.0** | 2026-07-17 | 首稿：CXO 首访实测驱动；明确不教微信；收口进度诚实 / 终端切换 / 敢秀底线 |
| **v1.0.1** | 2026-07-17 | 跨职能 Conditional Go · BLK-01～08 · OQ-01～03 关闭 |
| **v1.0.2** | 2026-07-17 | 用户联席八席 · USR-01～07 · D-FST-13/14 · AC-FST-08b/08c/15 |
| **v1.0.2+doc** | 2026-07-17 | 拆 ACCEPTANCE / IMPLEMENTATION；DOC-FST-01～03 回写 FTUE v1.1.1 · Help v1.1.2 · Share-Ready v1.0.3 |
