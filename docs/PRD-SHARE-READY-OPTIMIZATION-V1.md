# Travelogue · 敢发闭环优化 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio（本机 Studio / 桌面打包同等体验） |
| **文档版本** | **v1.0.2** |
| **状态** | **Conditional Go · 跨职能 MF + 用户联席 USR 已回写** · 线框已增补 · **编码另排期**（见 [跨职能评审](./acceptance-records/share-ready-optimization-v1-review-2026-07-17.md) · [用户联席](./acceptance-records/share-ready-optimization-v1-user-panel-2026-07-17.md)） |
| **主题代号** | 「敢发闭环」— 看见价值 · 选对分享 · 文案敢发 · 长图知发群 |
| **触发来源** | 2026-07-17 多 Persona 本机走查（分享者 / 近郊周末党 / 编辑者 / 空态首访 / 回访）；交叉对照 FTUE · Output Recipe · L0 · Trust · Copy |
| **前置条件** | Studio 首页 v2（M21）；导出门面 V1；Output Recipe flag 可开；Preview Toolbar V3/V4；Help 发群三要素合同有效 |
| **关联文档** | [PRD-FTUE-OPTIMIZATION-V1.md](./PRD-FTUE-OPTIMIZATION-V1.md) · [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md)（含 **D-OR-27**） · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) · [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) · [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md) · [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) · [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) · [SHARING.md](./SHARING.md) · [CHARTER.md](./CHARTER.md) |
| **评审记录** | [跨职能评审](./acceptance-records/share-ready-optimization-v1-review-2026-07-17.md) · [用户联席评审](./acceptance-records/share-ready-optimization-v1-user-panel-2026-07-17.md) |
| **验收** | [ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md](./ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md) · 本文 §11 为索引 |
| **实施清单** | [IMPLEMENTATION-SHARE-READY-OPTIMIZATION-V1.md](./IMPLEMENTATION-SHARE-READY-OPTIMIZATION-V1.md) |
| **线框** | [wireframes/share-ready-optimization-v1-wireframe.html](./wireframes/share-ready-optimization-v1-wireframe.html) · F1–F6（W0：F1–F3/F6；W1：F4–F5） |
| **更新日期** | 2026-07-17 |

> **定位**
>
> 80% 北极星路径仍是：**选文件夹 → 等待 →（可选）扫一眼预览 → 导出长图 → 发微信 → 结束**。  
> 相邻主题已分别定义首访（FTUE）、配方分流（Output Recipe）、无 Key（L0）、信任壳（Trust）、文案稀疏（Copy）。  
> **本 PRD 不另起产品叙事**，而是把 2026-07-17 多角色走查中仍会阻断「敢试 / 敢选 / 敢发」的断裂点，收成 **一条可排期的主链优化合同**；并明确哪些由本主题 **新编码拥有**，哪些 **强制关闭相邻主题缺口**。
>
> **一句话目标**：普通旅行者在 Windows 本机、不配 API、不读 docs 的前提下，一次会话内完成  
> **看见成片价值 → 选对分享形态 → 看到可发的文案 → 导出长图 → 知道怎么发微信群**，且过程中不出现黑屏样品、误跳意图、系统腔封面、成功面消失。
>
> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **W0 Go** | 敢信：首页真图 · recipe 以服务端 `kept_n` 为准 · 工程提示不进分享面 | 文案质量未完成 |
> | **W1 Go** | 敢选敢发：Ambiguous 必出意图卡 · Dock CTA 人话 · 成功面稳定 · 进度人话 | 章名/精修深度未完成 |
> | **W2 Go** | 敢秀：stub/hook 去说明书腔 · 章名与地点可读 · 书架噪音收敛 | 海外 IG / 小程序路径 B |
>
> **产品共识（六条铁律）**
>
> 1. **看见价值先于学会操作** — 首页 showcase 必须是真成片预览，禁止 PLACEHOLDER 黑块充当样品。  
> 2. **配方分流以策展后 `kept_n` 为唯一权威** — 禁止仅靠 DOM 估图数决定 Band / 意图卡。  
> 3. **Ambiguous 必须显式问「怎么发」** — 含首次导出与「长图可更新」重导出；禁止静默猜默认。  
> 4. **分享面零工程泄漏** — 封面/hook/章名/长图/Share 不得出现排版提示、省略说明、测试文件夹名腔。  
> 5. **落盘 ≠ 完成** — 继承 FTUE/Help：成功面第一可读行=发群三要素；复用 Task Dock，禁止平行栈。  
> 6. **本主题默认中文微信主路径** — **不做**海外 IG / Carousel / `locale=en` 扩展（见 §2.2）。

> **v1.0.1 评审回写摘要（2026-07-17 Conditional Go）**
>
> - BLK-01：Output Recipe 增补 **D-OR-27**（客户端不得用 DOM 估数裁决 Band/`needs_intent`）  
> - BLK-02：OQ-SR-01～04 冻结为已关闭  
> - BLK-03：成功面合同所有者 = FTUE + Help；本主题 W1 **联合挡门**、禁止第二套成功面  
> - BLK-04：线框 F1–F6 已齐  
> - BLK-05：recipe API 失败 toast 冻结句  
> - BLK-06：showcase 资产归属 demo-album 烘焙  
> - BLK-07：AC-SR-02 必做 e2e  
> - BLK-08：§4.4 为 FTUE/Trust 禁词表增量，非平行第三表  
> - **本轮不动代码**；编码 Kickoff 另排期

> **v1.0.2 用户联席回写摘要（2026-07-17）**
>
> - **USR-01** → §4.6：用户可见面禁止工程词（`kept_n` / DOM / recipe…）  
> - **USR-02** → §4.2 / D-SR-15：意图卡微信群长图 = 唯一 primary，禁止三等权  
> - **USR-03** → §3.5 / AC-SR-09b：成功面必含「换种分享方式」可点  
> - **USR-04** → §3.1 / D-SR-16：首页样品须有可见「示例」徽标  
> - **USR-05** → §2.4：W2 完成前对外勿承诺「文案已杂志级」  
> - **USR-06** → §2.3 / §9：主题对外宣布完成前须真人 N≥5（U1/U2/U5）  
> - 线框 F1/F2/F5 已按上项增补

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 与相邻主题的边界（拥有 vs 依赖） |
| §0.2 | v1.0.1 Must-Fix / v1.0.2 USR 回写对照 |
| §1 | 走查方法、Persona、问题清单（P-SR-*） |
| §2 | 目标 / 非目标 / 成功指标 |
| §3 | 体验合同与冻结决策（D-SR-*） |
| §4 | 触点与文案矩阵 |
| §5 | 工程任务 |
| §6～§8 | 错误 / 埋点 / 非功能 |
| §9 | 里程碑 |
| §10 | 线框与依赖排期 |
| §11 | 验收 AC |
| §12 | 风险与 OQ |
| §13 | 评审清单 |
| 附录 | 走查摘要 · 词表 · 版本记录 |

### 0.1 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [FTUE](./PRD-FTUE-OPTIMIZATION-V1.md) | **依赖关闭 · W1 联合挡门** | 不重写空态/示例合同；**发群成功面合同所有者 = FTUE + Help**；本主题 W1 Go 依赖 FTUE W1 同绿；**禁止**本主题实现第二套成功面 |
| [Output Recipe](./PRD-OUTPUT-RECIPE-V1.md) | **本主题 P0 拥有缺陷修复** | 兑现 **D-OR-27**：客户端 `kept_n` 同源；重导出不绕过意图；CTA 可见文案兑现 |
| [Export Facade](./PRD-PREVIEW-EXPORT-FACADE-V1.md) / [Help](./PRD-HELP-ONBOARDING-V1.md) | **复用** | 成功面 / 发群句唯一来源；禁止新成功面栈 |
| [L0 Guidance](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) | **依赖关闭** | 无 Key 永不整单失败；本主题只断言「主链可走完」 |
| [UX Trust](./PRD-UX-TRUST-V1.md) | **交叉** | Share 只读壳 + 门禁不回归；工程提示泄漏归本主题挡 |
| [Copy](./PRD-COPY-OPTIMIZATION.md) / [Chapter Naming](./PRD-CHAPTER-NAMING.md) | **W2 协同** | 本主题定义「敢发」最低文案门槛；深度润色仍归 Copy/章名轨 |
| [Refine UX 1.1](./PRD-PREVIEW-REFINE-UX-V1.1.md) | **不重开** | 仅要求分享默认面不泄漏精修工程提示；S1 真人仍归该主题 |
| [Overseas Share Pack](./PRD-OVERSEAS-SHARE-PACK-V2.md) | **明确不做** | 本主题范围外；不改 `locale=zh` 默认、不加 IG CTA |

### 0.2 Must-Fix / USR 对照（→ 正文）

| BLK | 落点 |
|-----|------|
| **BLK-01** | §3.2 · D-SR-01 · 交叉 [D-OR-27](./PRD-OUTPUT-RECIPE-V1.md) |
| **BLK-02** | §3.8 · §12.3 |
| **BLK-03** | §0.1 FTUE 行 · §3.5 · D-SR-06 |
| **BLK-04** | 文首线框链接 · §10.3 |
| **BLK-05** | §4.5 · §6 |
| **BLK-06** | §3.1 资产策略 |
| **BLK-07** | ACCEPTANCE AC-SR-02 · IMPLEMENTATION QA-SR-01 |
| **BLK-08** | §4.4 开篇声明 |
| **USR-01** | §4.6 |
| **USR-02** | §4.2 · D-SR-15 |
| **USR-03** | §3.5 · ACCEPTANCE AC-SR-09b |
| **USR-04** | §3.1 · D-SR-16 |
| **USR-05** | §2.4 |
| **USR-06** | §2.3 · §9 |

---

## 1. 背景与问题

### 1.1 实测方法（可复现）

| 项 | 约定 |
|----|------|
| **日期** | 2026-07-17 |
| **环境** | Windows · `python -m travelogue studio --port 8766` · Chrome/Edge 桌面视口（≥1280×720） |
| **配置** | `studio.output_recipe.enabled: true`（`config.yaml`） |
| **样例 trip** | `demo-album`（Sparse）· `ux-handtest-photos-v2`（Sparse）· `ha-amb-18`（Ambiguous · API `kept_n=18`）· `demo-49551086fe`（Narrative 档边缘 · 31 张） |
| **方法** | Persona 剧本走查 + Playwright MCP 实机点击 + recipe API 对照 |
| **非方法** | 非 N≥5 真人访谈；海外 IG 未测 |

### 1.2 Persona 与目标态剧本

#### P1 · 极简分享者（~80%）

```
打开首页（须见真成片样品）
  → 开始制作 →（可选）示例
  → 预览扫一眼（文案不刺眼）
  → Dock 主 CTA 语义=「导出长图 · 发微信群」
  → 导出进度说人话
  → 成功面：发群三要素 + 打开文件夹 → 结束
```

#### P2 · 近郊周末党（10–30 张）

```
打开 Ambiguous trip
  → 点 Dock 长图
  → **必须**出现意图卡：发群长图 / 九宫格 / 长图连读
  → 选择并导出 → 成功面与产物名实一致
  → 若书架显示「长图可更新」：重导出仍可换分享方式
```

#### P3 · 轻度编辑者（~20%）

```
预览 → 精修（改杂志名 / 换封面 / ★）
  → 画面与导出面不见工程提示
  → 更新版面（若 pending）→ 长图 → 发群
```

#### P4 · 空态首访 / P5 · 回访

- P4：继承 FTUE To-Be（空态不灰、向导示例、L0 可成稿）。  
- P5：书架标题人话、技术 meta 降噪；一键按上次方式导出（见 §3.6）。

### 1.3 As-Is 关键断裂（走查实录）

| 断裂 | 实况 | 用户感受 |
|------|------|----------|
| 首页样品黑屏 | `demo-showcase/**/*-PLACEHOLDER.webp` 约 1×1 px | 「这产品能做出东西吗？」 |
| Ambiguous 意图卡被跳过 | API `needs_intent=true` + `kept_n=18`；UI 直接「正在导出」 | 系统替我做了决定 |
| 根因 | `estimatePhotoCountFromDom` 数版面图槽 ≠ 服务端 `kept_n` | Band 误判为 Sparse |
| CTA 名实分离 | `aria-label`=完整配方句；可见字仍是「长图」 | 不知道导出是为了发群 |
| 双长图入口 | Dock「长图」+ 文内「保存长图」 | 点哪个？ |
| 系统/工程句进分享面 | 「关于…的1天」「主体偏上，适合雾底题签」「已省略封底图」 | 不敢发 |
| stub 说明书腔 | 「31 张照片汇成这一页」；地点常「旅途」 | 不像游记 |
| 成功面不稳 | 导出结束后发群引导易消失 | 文件在哪？怎么发？ |
| 进度工程口吻 | 「按章 · 2× · 正在打开浏览器…」 | 像开发者工具 |
| 书架噪音 | 测试截断名、`模板已锁定` 常驻 | 不像「我的画册」 |

### 1.4 问题清单（P-SR-*）

| ID | 问题 | 严重度 | 波次 | 拥有 |
|----|------|--------|------|------|
| **P-SR-01** | 客户端 DOM 估数导致 Ambiguous 跳过意图卡 | **P0** | W0 | **本主题** |
| **P-SR-02** | 「长图可更新」重导出可绕过意图选择 | **P0** | W0 | **本主题** |
| **P-SR-03** | 首页 showcase PLACEHOLDER 黑屏 | **P0** | W0 | **本主题** |
| **P-SR-04** | 工程提示 / 省略说明泄漏进封面与卷轴 | **P0** | W0 | **本主题**（交叉 Trust/FTUE） |
| **P-SR-05** | 长图成功面 / 发群引导不稳定 | **P0** | W1 | **关闭 FTUE**（本主题挡门） |
| **P-SR-06** | Dock 可见 CTA 未兑现配方文案 | **P1** | W1 | **本主题** |
| **P-SR-07** | 双长图入口争抢注意力 | **P1** | W1 | **对齐 FTUE D-FTUE-07** |
| **P-SR-08** | 导出进度工程口吻 | **P1** | W1 | **本主题** |
| **P-SR-09** | stub hook/结语说明书腔（张数、关于 X 的 N 天） | **P1** | W2 | **本主题最低门槛** + Copy |
| **P-SR-10** | 地点恒为「旅途」/ 章名「日期续」 | **P2** | W2 | Chapter Naming + 本主题断言 |
| **P-SR-11** | 书架技术 meta / 测试标题噪音 | **P2** | W2 | **本主题** |
| **P-SR-12** | 精修默认路径仍重（发现性） | **P2** | W2 | **不重开**；仅挡泄漏 + 指针 Refine S1 |
| **P-SR-13** | 无 Key / 空态 / 文件名乱码 | **P0/P1** | 随 FTUE·L0 | **依赖关闭**（本主题回归断言） |
| **P-SR-14** | 非开发者安装偏 pip | **P2** | — | **Installer**（本主题不做） |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 可观测 |
|----|------|--------|
| **G-SR-01** | 首页 3 秒内看见真实成片价值（非黑块） | AC-SR-01 |
| **G-SR-02** | Band / 意图卡与服务端 `kept_n` 一致 | AC-SR-02～04 |
| **G-SR-03** | Ambiguous 首次与 stale 重导出均可选意图 | AC-SR-03 / 05 |
| **G-SR-04** | 分享面零工程泄漏 | AC-SR-06～07 |
| **G-SR-05** | Sparse Dock CTA 人话可读（发微信群） | AC-SR-08 |
| **G-SR-06** | 长图成功后稳定知道发群 + 文件位置 | AC-SR-09～10 |
| **G-SR-07** | 导出进度人话 | AC-SR-11 |
| **G-SR-08** | L0 stub 成片文案不低于「敢发」门槛 | AC-SR-12～13 |
| **G-SR-09** | 回访书架主信息是标题与封面，不是工程状态 | AC-SR-14 |

### 2.2 非目标

| 不做 | 原因 |
|------|------|
| **海外 IG / Carousel / 英语 UI / `locale=en` 主路径** | 明确延期；见 Overseas Share Pack |
| 小程序路径 B / 云托管 / 账号体系 | CHARTER / SHARING 另轨 |
| 官方代付 LLM | Desktop LLM 非目标 |
| 重做精修信息架构 / G1 / 排版算法 | Refine / Layout 另轨 |
| 假九宫格或削弱名实铁律 | 继承 Output Recipe D-OR-* |
| 新造成功面 / toast 平行体系 | 复用 Help / Facade / FTUE |
| 全能社交导出中心 | 导出门面铁律；主路径仍是微信长图 |
| Installer 签名 / Gate 全量 | PRD-DESKTOP-INSTALLER |

### 2.3 成功指标（狗粮目标 · 非发布硬 KPI）

| 指标 | 目标 | 样本 |
|------|------|------|
| Ambiguous 预览点长图 → 意图卡出现率 | **100%**（`kept_n` 10–30 且无 session intent） | 手测 + e2e |
| 首页 showcase 真图（naturalWidth≥200） | **100%** 关键帧 | 手测 |
| 分享面工程泄漏 | **0** | 词表扫描 + 手测 |
| 成稿 → 见发群引导（≥3s 或可找回） | ≥ 85% | N≥5（对齐 FTUE） |
| Sparse 用户无需打开 ▾ 即理解「为发群」 | ≥ 80% 口述正确 | N≥5 |
| 主题对外宣布完成前真人复测（USR-06） | U1/U2/U5 剧本各至少覆盖；合计 **N≥5** | 非作者手测 |

### 2.4 对外沟通约束（USR-05）

| 阶段 | 允许对外说法 | 禁止 |
|------|--------------|------|
| W0 / W1 未完成 W2 前 | 「可导出微信长图」「本机成册」 | 「文案已达杂志级」「AI 游记文案已完善」 |
| W2 Go 后 | 可按 Copy 验收结果表述文案能力 | 夸大尚未验收的润色效果 |

---

## 3. 体验合同与冻结决策

### 3.1 首页价值展示合同（P-SR-03 · USR-04）

| 必须 | 禁止 |
|------|------|
| 大屏卷轴 carousel **与**手机长图 strip 使用真实成片图（可由示例 trip 烘焙） | 以 `*PLACEHOLDER*` 1×1 / 空图充当默认样品 |
| 样品区须有**持久可见**的「示例」徽标或等价标签（不只靠文案里夹「示例 ·」） | 黑屏 + 仅页码点；样品与书架「我的作品」无区分 |
| 资源缺失时显示明确占位插画/色块+「示例加载中」 | 静默黑矩形 |

**资产策略（定案 · BLK-06）**：W0 用现有 `trips/demo-album`（或打包内 demo）导出/裁切静态 webp 替换 `templates/studio/assets/demo-showcase/`；刷新步骤写入 `WORKSHOP.md` 或该目录 README（DOC-SR-03）。缺图时用明确插画/色块文案，**禁止**静默黑矩形。

### 3.2 Output Recipe `kept_n` 同源合同（P-SR-01 / 02）— **本主题核心**

> **权威交叉**：与 [PRD-OUTPUT-RECIPE-V1 **D-OR-27**](./PRD-OUTPUT-RECIPE-V1.md) 同义；冲突时以 D-OR-27 + 本文为准。

| 项 | 合同 |
|----|------|
| **权威来源** | 服务端 resolve 使用的策展后 `kept_n`（与 `/__travelogue/output-recipe?tripId=` 一致） |
| **客户端** | 触发意图卡 / Band CTA **前**必须取得服务端 recipe（或启动时注入的 `keptN`）；**禁止**单独用 `estimatePhotoCountFromDom` 决定 `needs_intent`（**D-OR-27**） |
| **DOM 估数** | 仅可用于「约 N 张」提示、小红书张数估算等 **非 Band 裁决**场景；若使用须标注为 estimate |
| **Ambiguous + preview + 无 intent** | **必须** `showAmbiguousIntentCard`；主钮「选择并导出」 |
| **stale /「重新导出」** | 若当前 session/prefs **无有效 intent**，或用户点「换种分享」→ **同等**出意图卡；禁止因 stale 直出默认 chat |
| **已有 session intent** | 可直出；成功面提供「换种分享方式」 |
| **书架入口** | 仍遵守 Output Recipe D-OR-16（书架可不强制意图卡）；但 **预览内**本条优先 |
| **flag 关闭** | 回退 LNG2 默认；本主题 AC 标 N/A |

### 3.3 分享面零泄漏合同（P-SR-04）

下列字符串 **禁止**出现在：封面主文案、hook、章名、结语、长图栅格可见字、`?share=1` 面：

| 类别 | 示例（非穷尽） | 允许去向 |
|------|----------------|----------|
| 排版/封面工程提示 | 「主体偏上，适合雾底题签」「备选有限…」 | 精修面板 / 内部 feedback |
| 省略/降级说明 | 「已省略封底图」 | 仅 Studio 创作者 tip（非版心） |
| 模板系统句 | 「模板已锁定」作正文 | 书架次级 meta |
| 测试/路径名腔 | 原始文件夹名作杂志主标题（无用户编辑时） | ingest 默认 title 须经可读化（§3.7） |
| stub 说明书句式 | 「关于{title}的 N 天」「N 张照片汇成这一页」 | 见 §3.7 替换规则 |

创作者精修面板内可保留解释性文案；**退出精修 / Share / 导出成功预览**不得残留。

### 3.4 Dock CTA 与双入口合同（P-SR-06 / 07）

| 项 | 合同 |
|----|------|
| Sparse 默认 | 可见主 CTA **优先**显示配方 `cta_label`（如「导出长图 · 发微信群」）；Dock 极窄时可显示缩短形「发微信群」，完整句保留 `aria-label` + tooltip |
| Ambiguous 未选意图 | 可见「选择分享方式」或配方 `cta_label`（「选择并导出」）；**不得**仅显示「长图」却直接开导 |
| Narrative | 可「导出长图」+ subtitle/hint「建议按章」；≥50 保持整卷确认钩子 |
| 文内「保存长图」 | **保留**；tertiary；不脉冲、不 tip（= FTUE D-FTUE-07） |
| ▾ 高级项 | 平台/清晰度/切段仍在高级；不抬到与主 CTA 同级 |

### 3.5 导出进度与成功面合同（P-SR-05 / 08）

**进度（人话优先）**

| 阶段 | 用户可见（冻结方向） | 禁止单独展示 |
|------|----------------------|--------------|
| 排队/启动 | 正在生成可发微信的长图… | 仅「正在打开浏览器…」 |
| 合成 | 正在合成长图… | 裸露 `2×` 无解释 |
| 保存 | 正在保存到本机… | 无 |
| 附注 | 次行小字可写「按章导出 · 高清」 | 工程参数抢第一行 |

**成功面（BLK-03 · USR-03）**：合同所有者 = **FTUE + Help**；完整继承 FTUE §3.3 / Help `publishGuideFallback`：

1. 复用 Task Dock `showSuccess`；**禁止**本主题新建平行 Modal/toast 栈。  
2. 第一可读行=发群三要素。  
3. 可见 ≥3s 或关闭前保持；自动收起后可经再点长图 / H4 找回。  
4. 次要：「在文件夹中显示」。  
5. **须提供**可点「换种分享方式」（Ambiguous / 已导出后换 intent；Sparse 可进入高级或意图卡等价入口）——用户联席 U2/U4 刚需。  
6. 本主题 **W1 Go** 与 FTUE W1 **联合挡门**（同绿才过）。

### 3.6 回访书架合同（P-SR-11）

| 必须 | 禁止 |
|------|------|
| 卡片主信息：标题 · 封面 · 相对时间 | 主标题为未截断友好化的内部 id |
| 「长图可更新」可作角标 | 主行堆叠「智能匹配 · 模板已锁定」为默认强调 |
| 打开预览后导出遵守 §3.2 | 书架一键导出在 Ambiguous **无 intent** 时静默猜错且无提示（若保留书架直出，须 toast hint，对齐 D-OR-16） |

### 3.7 「敢发」文案最低门槛（P-SR-09 / 10）

本主题 **不**重做 Copy 全案，但 W2 必须满足：

| 字段 | 禁止（L0/stub） | 最低允许 |
|------|-----------------|----------|
| `meta.hook` | 「关于{title}的 N 天」「N 张照片汇成…」 | 空 **或**「{短标题} · {日期或地点}」类非说明书句；宁可空 |
| `meta.places` | 无信号时硬填「旅途」进读者面强调位 | 无信号则空/隐藏「1 个地方」话术 |
| 章 `title` | 连续「日期」「日期续」且无区分度时无提示可改 | 允许日期底线；编辑者可改；指针 Chapter Naming |
| 默认杂志名 | 原始文件夹名 / `ux-handtest-*` 腔 | 可读化：去哈希后缀、过长截断带省略、非法字符清理 |

### 3.8 冻结决策（D-SR-*）

| ID | 决策 |
|----|------|
| **D-SR-01** | Band / `needs_intent` **以服务端 `kept_n` 为唯一权威**；DOM 估数不裁决意图卡（= **D-OR-27**） |
| **D-SR-02** | Ambiguous 预览导出（含 stale 重导且无 intent）**必须**意图卡 |
| **D-SR-03** | 首页 showcase **禁止** PLACEHOLDER 黑块默认上线 |
| **D-SR-04** | 分享面工程提示 / 省略说明 **零泄漏** |
| **D-SR-05** | Sparse 可见 CTA：完整句或缩短形 **「发微信群」**（OQ-SR-01 已关） |
| **D-SR-06** | 成功面合同所有者 = FTUE+Help；本主题 W1 **联合挡门**；禁止第二套栈 |
| **D-SR-07** | 导出进度第一行人话；技术参数次行 |
| **D-SR-08** | 文内「保存长图」保留但降强调（对齐 FTUE） |
| **D-SR-09** | stub 说明书句式 W2 清除；宁可空 hook |
| **D-SR-10** | **本主题不做海外 IG**；不加 IG 主 CTA / 英语默认 |
| **D-SR-11** | 不新造成功面栈；不削弱九宫格名实铁律 |
| **D-SR-12** | 精修深度体验不重开；仅挡泄漏 |
| **D-SR-13** | recipe API 失败：允许降级 chat + 冻结 toast（§4.5）；不静默假 Sparse |
| **D-SR-14** | title 可读化仅新导入默认；不覆盖已编辑标题（OQ-SR-04） |
| **D-SR-15** | 意图卡：**微信群 · 长图** 为唯一 primary 视觉权重；九宫格/连读 secondary；禁止三钮等权（USR-02） |
| **D-SR-16** | 首页样品须有可见「示例」徽标（USR-04） |
| **D-SR-17** | 用户可见 UI **禁止**工程词：`kept_n`、DOM、recipe、output-recipe 等（USR-01）；评审旁注除外 |

---

## 4. 触点与文案矩阵

### 4.1 触点总表

| ID | 触点 | 触发 | 要点 |
|----|------|------|------|
| **T-SR-HOME** | 首页 bento 样品 | idle | 真图 §3.1 |
| **T-SR-CTA** | Dock 主导出钮 | 预览 idle | §3.4 |
| **T-SR-INTENT** | Ambiguous 意图卡 | needs_intent | 三选一；选择并导出 |
| **T-SR-STALE** | 长图可更新 | stale | §3.2 重导 |
| **T-SR-PROG** | 导出进度 | running | §3.5 |
| **T-SR-OK** | 成功面 | succeeded | FTUE §3.3 |
| **T-SR-LEAK** | 版心/封面 | render | §3.3 拦截 |
| **T-SR-SHELF** | 书架卡片 | 回访 | §3.6 |
| **T-SR-INLINE** | 文内保存长图 | 滚动工具条 | tertiary |

### 4.2 意图卡文案与视觉权重（继承 Output Recipe 词表 · USR-02）

以 [PRD-OUTPUT-RECIPE-V1 附录 C](./PRD-OUTPUT-RECIPE-V1.md) 为单一真相源；本主题不另造「朋友圈」一名两义。

| intent | 用户可见方向（摘要） | 视觉权重 |
|--------|----------------------|----------|
| `chat_longshot` | 微信群 · 长图 | **primary**（实心底 / 主色；唯一） |
| `moments_grid` | 朋友圈 · 九宫格（真 grid） | secondary（描边） |
| `moments_scroll` | 朋友圈 · 长图连读 | secondary（描边） |

Hint（**用户可见**唯一句式）：

> 这趟精选了 N 张，你想怎么发？

- **N** 的数值必须来自服务端 `kept_n`（工程约束，**不得**把「kept_n」三字写进 UI）。  
- 取消 = 不导出。  
- 禁止三钮做成相同填充/相同字重的「等权选择题」。

### 4.3 进度文案（冻结草案）

| key | 文案 |
|-----|------|
| `export_start` | 正在生成可发微信的长图… |
| `export_compose` | 正在合成长图… |
| `export_save` | 正在保存到本机… |
| `export_secondary` | 按章 · 高清（示例；随 prefs 变） |

### 4.4 系统句 / 工程句拦截表（BLK-08 · FTUE/Trust 增量）

> 本表是 [FTUE §4.3](./PRD-FTUE-OPTIMIZATION-V1.md) / Trust 禁词的 **增量扩展**，**不是**第三套平行词表。合并扫描时并集生效。

| 禁止模式（建议正则/子串） | 处理 |
|---------------------------|------|
| `主体偏上` / `雾底题签` / `适合雾底` | 移出版心 |
| `已省略封底` | 移出版心 |
| `关于.+的\d+天` | stub 禁止生成 |
| `\d+\s*张照片汇成` | stub 禁止生成 |
| `备选有限` | 仅精修/内部 |
| 原始 `asset-` 明文 | 已有 Refine AC；保持 |

### 4.5 recipe API 失败 toast（冻结 · BLK-05 / D-SR-13）

**唯一句**（用户可见）：

> 暂时按微信群长图导出，可稍后重试选分享方式。

允许继续导出为 `chat_longshot`；须可取消。禁止无提示直出且假装「已选分享方式」。

### 4.6 用户可见面禁工程词（USR-01 · D-SR-17）

下列词/片语 **禁止**出现在任何终端用户可见字符串（按钮、标题、hint、toast、进度、成功面、首页样品区）。允许出现在：开发者文档、评审线框「定案/旁注」、`data-*`、日志、埋点属性名。

| 禁止（用户面） | 用户面应写 |
|----------------|------------|
| `kept_n` / keptN | 「精选了 N 张」中的数字 N |
| DOM / 估数 / 槽位 | （不解释） |
| recipe / output-recipe / Band / Sparse / Ambiguous / Narrative | 「分享方式」/「怎么发」 |
| `needs_intent` / session intent | （不解释） |
| Playwright / Chromium（进度主句） | 「正在生成可发微信的长图…」 |

验收：对预览/首页可见 DOM 文本做禁词扫描（AC-SR-15）。

---

## 5. 工程任务

### 5.1 前端（Studio / Preview）

| ID | 内容 | 波次 |
|----|------|------|
| **FE-SR-01** | 替换 demo-showcase 真图资产；缺失态 UI；**「示例」徽标**（USR-04） | W0 |
| **FE-SR-02** | `startLongshotWithRecipe`：先 fetch/注入 server recipe，再用 `needs_intent` | W0 |
| **FE-SR-03** | stale「重新导出」走同一 recipe 门；无 intent 弹卡 | W0 |
| **FE-SR-04** | 版心/封面隐藏工程 tip；精修内保留 | W0 |
| **FE-SR-04b** | 意图卡/进度/toast **用户文案**去工程词（§4.6）；primary 权重（§4.2） | W0 |
| **FE-SR-05** | Dock 可见 CTA 同步 `cta_label` / 缩短形策略 | W1 |
| **FE-SR-06** | 文内长图降强调（对齐 FTUE） | W1 |
| **FE-SR-07** | 进度文案 §4.3；参数次行 | W1 |
| **FE-SR-08** | 成功面入口矩阵回归；**必含「换种分享方式」**（USR-03） | W1 |
| **FE-SR-09** | 书架主 meta 降噪；角标保留 stale | W2 |

### 5.2 后端 / 管线

| ID | 内容 | 波次 |
|----|------|------|
| **BE-SR-01** | preview 注入 `keptN` / recipe bootstrap（减少竞态） | W0 |
| **BE-SR-02** | 确认 `handle_output_recipe` 与 longshot resolve 同源 | W0 |
| **BE-SR-03** | templateFeedback / veil 提示不进 hook 与读者字段 | W0 |
| **BE-SR-04** | stub hook 去掉说明书句式；places 无信号不填「旅途」强展示 | W2 |
| **BE-SR-05** | 默认 title 可读化（文件夹名清洗） | W2 |
| **BE-SR-06** | 封底省略不写进读者可见 HTML | W0 |

### 5.3 测试

| ID | 内容 | 波次 |
|----|------|------|
| **QA-SR-01** | e2e：`kept_n=18` 但 DOM 槽位少 → **仍**出意图卡 | W0 |
| **QA-SR-02** | 单测：拦截表 §4.4 不进 render 读者字段 | W0 |
| **QA-SR-03** | 回归 Output Recipe persona 套件 8/8 | W0 |
| **QA-SR-04** | 成功面可见窗口 / 可找回 | W1 |
| **QA-SR-05** | stub hook 禁止模式单测 | W2 |

### 5.4 文档

| ID | 内容 | 波次 |
|----|------|------|
| **DOC-SR-01** | 本文评审 + README 索引 | W0 |
| **DOC-SR-02** | 回写 Output Recipe：客户端不得用 DOM 估数裁决 Band | W0 |
| **DOC-SR-03** | showcase 资产刷新说明（WORKSHOP 或 templates README） | W0 |
| **DOC-SR-04** | 拆 ACCEPTANCE / IMPLEMENTATION（评审后） | W0 |

---

## 6. 错误与边界

| 场景 | 期望 |
|------|------|
| recipe API 失败 | 安全降级：toast **§4.5 冻结句** + 可继续 chat / 可取消；**不得**用错误 DOM 数假装 Sparse 而跳过本可展示的意图（若上次成功缓存 `kept_n` 可用则用缓存） |
| `kept_n` 与 DOM 差 > 阈值 | 埋点 `recipe_keptn_dom_mismatch`；UI 仍以 server 为准 |
| flag 关闭 | 无意图卡；CTA 回退「长图」；AC-SR-02～05 N/A |
| 无 Playwright | 既有错误码；成功面不假装已导出 |
| 示例 showcase 图缺失 | 非黑屏占位 + 日志；不阻断导入 |
| Ambiguous 用户取消意图卡 | 不导出；停留预览 |
| 海外用户误入 | 仍走中文微信主路径；不出现 IG 主 CTA（本主题范围） |

---

## 7. 埋点

| 事件 | 说明 |
|------|------|
| `share_ready_recipe_server_used` | 导出前使用服务端 `kept_n` |
| `recipe_keptn_dom_mismatch` | server vs DOM 差异（含两值） |
| `ambiguous_intent_shown` | 意图卡展示（含 `source=stale_reexport|first`） |
| `ambiguous_intent_skipped_illegal` | **调试告警**：needs_intent 但未展示（应为 0） |
| `home_showcase_placeholder_hit` | 仍命中 PLACEHOLDER（应为 0） |
| `longshot_success_share_hint_shown` | 复用现网；断言 W1 |
| `share_surface_leak_blocked` | 拦截工程句（可选） |

---

## 8. 非功能

| 项 | 要求 |
|----|------|
| 性能 | recipe bootstrap 不得明显拖慢首屏；可与 toolbar init 并行；超时 ≤2s 后走 §6 降级 |
| 兼容 | Chrome/Edge 90+ Windows；桌面视口主路径 |
| 安全 | 不引入云同步；照片仍本机 |
| 可测试 | W0 缺陷须有 e2e 锁死「DOM 少图仍出意图卡」 |
| i18n | 本主题仅维护 `locale=zh` 用户可见句 |

---

## 9. 里程碑

| 里程碑 | 范围 | Go / No-Go |
|--------|------|------------|
| **W0** | showcase 真图+示例徽标 · `kept_n` 同源 · stale 不绕过 · 零泄漏 · 用户面无工程词 · primary 意图权重 · e2e | **Go**：AC-SR-01～07 · 15 · 01b；Ambiguous 手测过门 |
| **W1** | CTA 人话 · 双入口降噪 · 进度人话 · 成功面+换种分享（联合 FTUE） | **Go**：AC-SR-08～11 · 09b；发群引导狗粮 ≥85% |
| **W2** | stub 敢发门槛 · title 可读化 · 书架降噪 | **Go**：AC-SR-12～14 |
| **主题对外宣布完成** | W0+W1+W2 且 **USR-06 真人 N≥5**（U1/U2/U5） | Agent 联评 **不得**替代 |

**主题完成 ≠** Refine S1 真人签满、Installer Gate、Copy 全量艺术润色。

---

## 10. 线框与依赖排期

### 10.1 建议排期（可并行）

```text
W0 ──┬─ FE/BE recipe kept_n 同源 + e2e
     ├─ showcase 资产
     └─ 泄漏拦截
W1 ──┬─ CTA / 进度 / 双入口
     └─ 成功面（与 FTUE W1 合流挡门）
W2 ──┬─ stub / title / shelf
     └─ 指针 Chapter Naming / Copy 深度
```

### 10.2 依赖

| 依赖 | 阻塞关系 |
|------|----------|
| FTUE W1 成功面 | 本主题 W1 Go 共同挡门 |
| L0 无 Key 可成稿 | 主链狗粮前置 |
| Output Recipe flag | Ambiguous AC 需开启 |
| Copy / 章名 | 仅 W2 深度；W0/W1 不阻塞 |

### 10.3 线框清单（已齐 · BLK-04）

线框文件：[wireframes/share-ready-optimization-v1-wireframe.html](./wireframes/share-ready-optimization-v1-wireframe.html)

| ID | 画面 | 挡门 | v1.0.2 增补 |
|----|------|------|-------------|
| **F1** | 首页真图样品（对比 As-Is 黑屏） | W0 | **「示例」徽标**（USR-04） |
| **F2** | Ambiguous 意图卡（数值同源） | W0 | 用户面无工程词 · primary 权重（USR-01/02） |
| **F3** | stale 重导出仍出意图 / 换种分享 | W0 | — |
| **F4** | Dock CTA Sparse「发微信群」 | W1 | — |
| **F5** | 导出进度人话 + 成功面发群 | W1 | **强调「换种分享方式」**（USR-03） |
| **F6** | 封面无工程 tip（精修内可有） | W0 | — |

---

## 11. 验收 AC

权威勾选表见 [ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md](./ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md)。以下为索引摘要。

### 11.1 W0

| ID | Given | When | Then |
|----|-------|------|------|
| **AC-SR-01** | 首页 idle | 查看 carousel/phone 样品 | 关键帧 `naturalWidth≥200`；URL/路径不含默认黑 PLACEHOLDER |
| **AC-SR-01b** | 首页样品区 | 目视 | 有持久可见「示例」徽标/标签（USR-04） |
| **AC-SR-02** | trip `kept_n=18`，DOM 可见图槽 ≤6 | 打开预览点 Dock 长图 | 意图卡出现；hint 中数字=18（文案不出现 kept_n） |
| **AC-SR-03** | Ambiguous · 无 session intent | 点长图 | 三选一可见；**微信群长图**为 primary；取消则不导出 |
| **AC-SR-04** | `/__travelogue/output-recipe` 与 UI Band | 对照 | `needs_intent` / `band` 一致 |
| **AC-SR-05** | `longshotStale=true` · 无 intent | 点「重新导出」或 Dock 长图 | 仍出意图卡或明确「换种分享」 |
| **AC-SR-06** | demo / handtest 预览 | 扫封面与正文 | 无「雾底题签」「已省略封底」等 §4.4 项 |
| **AC-SR-07** | `?share=1` | 打开 | 无精修工程 tip；无 §4.4 泄漏 |
| **AC-SR-15** | 首页/预览/意图卡/进度可见文本 | 禁词扫描 | 无 §4.6 工程词（USR-01） |

### 11.2 W1

| ID | Given | When | Then |
|----|-------|------|------|
| **AC-SR-08** | Sparse · recipe on | 看 Dock 主钮 | 可见文案含「微信」或完整 `cta_label`；不只光秃「长图」 |
| **AC-SR-09** | 导出成功 | 看成功面 | 发群主句第一可读行；≥3s 或可找回 |
| **AC-SR-09b** | 导出成功 | 看成功面动作区 | **可点「换种分享方式」**（USR-03） |
| **AC-SR-10** | 成功面 | 点打开文件夹 | 资源管理器定位到 PNG |
| **AC-SR-11** | 导出中 | 读进度第一行 | 匹配 §4.3 人话；无孤立「正在打开浏览器…」作唯一主句 |
| **AC-SR-R01** | 文内「保存长图」 | 首访 | 无脉冲/无 tip（回归 FTUE） |

### 11.3 W2

| ID | Given | When | Then |
|----|-------|------|------|
| **AC-SR-12** | L0 stub 新导入 | 看 hook | 不匹配说明书禁止模式；可空 |
| **AC-SR-13** | 无地理信号 | 看封面/Colophon | 不强行「旅途」造「1 个地方」仪式感（或隐藏） |
| **AC-SR-14** | 书架 | 扫卡片 | 主标题可读；「模板已锁定」不抢主行 |

### 11.4 非回归

| ID | 说明 |
|----|------|
| **AC-SR-NR-01** | Output Recipe persona e2e 8/8 |
| **AC-SR-NR-02** | 九宫格名实：可见「九宫格」⇒ grid 产物 |
| **AC-SR-NR-03** | 零精修仍可导出（UX-P5-80-01） |
| **AC-SR-NR-04** | 无海外 IG 主 CTA 出现在默认中文预览 |

---

## 12. 风险与开放问题

### 12.1 风险

| 风险 | 缓解 |
|------|------|
| recipe 请求延迟导致导出变慢 | 预注入 + 超时降级 §6 |
| 真图资产版权/体积 | 用自有 demo trip 烘焙；控制 webp 体积 |
| 与 FTUE W1 抢同一成功面 | 合同复用；联合挡门，不双栈 |
| stub 清空 hook 后封面过空 | 允许空；靠照片与标题撑场（Copy 共识） |
| DOM 估数仍被他处误用 | 代码评审 + mismatch 埋点 |

### 12.2 开放问题（OQ）

本轮评审后 **无阻塞开放题**。新问题进入下一版再开。

### 12.3 已关闭（含评审拍板）

| ID | 结论 |
|----|------|
| **海外 IG 是否纳入本主题** | **否**（D-SR-10） |
| 是否用 DOM 估数加速免请求 | **否**作为 Band 裁决（D-SR-01 / **D-OR-27**） |
| 是否删除文内「保存长图」 | **否**；降强调（D-SR-08） |
| **OQ-SR-01** | 缩短形 = **「发微信群」** |
| **OQ-SR-02** | 允许降级 chat + §4.5 toast（D-SR-13） |
| **OQ-SR-03** | 书架不强制意图卡（D-OR-16）；预览内强制 |
| **OQ-SR-04** | title 可读化仅新导入（D-SR-14） |
| **OQ-SR-05** | 已拆 ACCEPTANCE / IMPLEMENTATION |

---

## 13. 评审清单与结论

| 席位 | 必答 | 2026-07-17 |
|------|------|------------|
| **产品** | W0/W1/W2 完成定义是否可挡门？与 FTUE/OR 边界是否清晰？ | Conditional Go |
| **交互** | CTA 缩短形、意图卡、成功面是否需新线框？ | Conditional Go · 线框已补 |
| **用户体验** | 「敢发」文案最低门槛是否够严/过严？ | Conditional Go |
| **用户 · 分享者** | 黑屏/意图跳过/成功面三点是否被合同钉死？ | Conditional Go |
| **用户 · 编辑者** | 工程 tip 仅精修可见是否可接受？ | Conditional Go |
| **架构** | `kept_n` 注入点是否单一真相源？降级是否安全？ | Conditional Go · D-OR-27 |
| **开发** | W0 工作量与 e2e 锁是否可 Kickoff？ | Conditional Go · **编码另排期** |

**结论**：**Conditional Go** · 跨职能 MF（v1.0.1）+ 用户联席 USR（v1.0.2）已回写 · 线框已增补 · **Ready for Kickoff（编码）另排期**。详见 [跨职能评审](./acceptance-records/share-ready-optimization-v1-review-2026-07-17.md) · [用户联席](./acceptance-records/share-ready-optimization-v1-user-panel-2026-07-17.md)。

---

## 附录 A · 2026-07-17 走查摘要

| Persona | 关键发现 | 映射 |
|---------|----------|------|
| 极简分享者 | 首页黑屏；CTA 只写「长图」；成功面弱；stub 不敢发 | P-SR-03/06/05/09 |
| 近郊周末党 | API 要意图、UI 跳过；DOM 估数根因；stale 重导 | P-SR-01/02 |
| 编辑者 | 「雾底题签」「已省略封底」进版心；精修重 | P-SR-04/12 |
| 空态首访 | 与 FTUE/L0 问题集重合 | P-SR-13 |
| 回访 | 书架技术噪音、截断测试名 | P-SR-11 |
| 海外 IG | **本主题不做** | D-SR-10 |

复现锚点：

- Showcase：`/__studio/assets/demo-showcase/**/*PLACEHOLDER*`  
- Recipe：`GET /__travelogue/output-recipe?tripId=ha-amb-18` → `needs_intent=true`  
- 客户端风险代码：`estimatePhotoCountFromDom`（`templates/studio/js/longshot-export-panel.js`）被 `startLongshotWithRecipe` 用于 Band 裁决  

---

## 附录 B · 用户可见词表（本主题增量）

| 场景 | 用 | 不用 |
|------|----|------|
| Sparse 主 CTA | 导出长图 · 发微信群 / 发微信群 | 仅「长图」（作为唯一可见语义） |
| Ambiguous 未选 | 选择分享方式 / 选择并导出 | 直接「导出中」 |
| 进度 | 正在生成可发微信的长图… | 仅「正在打开浏览器…」 |
| 成功 | Help 发群三要素同源句 | 「导出成功」空成功 |
| 泄漏 | — | 雾底题签、已省略封底、关于 X 的 N 天 |

九宫格 / 连读 / 发群专名 **仍以 Output Recipe 附录 C 为准**。

---

## 附录 C · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v1.0.0** | 2026-07-17 | 首稿 Draft；基于多 Persona 走查；排除海外 IG；定义 W0–W2 与 D-SR-* |
| **v1.0.1** | 2026-07-17 | Conditional Go 评审回写 BLK-01～08；线框/AC/IMPL 齐备；OQ 关闭；交叉 D-OR-27；明确本轮不动代码 |
| **v1.0.2** | 2026-07-17 | 用户联席 USR-01～06 回写；D-SR-15～17；§4.6 禁工程词；线框 F1/F2/F5 增补；AC-SR-01b/09b/15 |
