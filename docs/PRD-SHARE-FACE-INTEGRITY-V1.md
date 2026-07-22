# Travelogue · 敢发面一致性 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio（本机 Studio / 桌面打包同等体验） |
| **文档版本** | **v0.2.1** |
| **状态** | **Conditional Go** · **W2 工程已接**（AC-12 脚本门 ✅ · 盲评/手测/AC-15 仍开 · 分支 `feat/share-face-integrity-w0`） |
| **主题代号** | 「敢发面一致性」— 存量兑现 · 文案刷新 · 时间轴可信 · 交付体面 |
| **触发来源** | 2026-07-21 两轮多 Persona 实机试用：[首轮](./acceptance-records/persona-blogger-trial-2026-07-21.md) · [深走](./acceptance-records/persona-deep-trial-2026-07-21.md)；上承 [persona-ux-trial-2026-07-18.md](./acceptance-records/persona-ux-trial-2026-07-18.md) |
| **前置条件** | 导出门面五目标已上线；FST 成功面合同生效；[Share-Face Closeout](./PRD-SHARE-FACE-CLOSEOUT-V1.md) W0–W2 工程已合入（本主题硬化其未兑现部分） |
| **关联文档** | [FTT](./PRD-FINISH-THIS-TRIP-V1.md) · [FST](./PRD-FIRST-SESSION-TRUST-V1.md) · [SFC](./PRD-SHARE-FACE-CLOSEOUT-V1.md) · [Share-Ready](./PRD-SHARE-READY-OPTIMIZATION-V1.md) · [Copy](./PRD-COPY-OPTIMIZATION.md) · [Chapter Naming](./PRD-CHAPTER-NAMING.md) · [LTN](./PRD-LAYOUT-TRUST-NARRATIVE-V1.md) · [FTUE](./PRD-FTUE-OPTIMIZATION-V1.md) · [ADR-007](./adr/007-native-clustering.md) · [ADR-018](./adr/018-desktop-installer-layout.md) · [CHARTER](./CHARTER.md) |
| **评审记录** | [share-face-integrity-v1-review-2026-07-21.md](./acceptance-records/share-face-integrity-v1-review-2026-07-21.md) · **Conditional Go（6/6）** · BLK-SFI-01～10 已回写本文 |
| **验收** | [ACCEPTANCE-SHARE-FACE-INTEGRITY-V1.md](./ACCEPTANCE-SHARE-FACE-INTEGRITY-V1.md) · 本文 §11 为合同索引 |
| **实施清单** | [IMPLEMENTATION-SHARE-FACE-INTEGRITY-V1.md](./IMPLEMENTATION-SHARE-FACE-INTEGRITY-V1.md) |
| **线框** | [wireframes/share-face-integrity-v1-wireframe.html](./wireframes/share-face-integrity-v1-wireframe.html) · F0–F5（§10） |
| **狗粮** | [acceptance-records/share-face-integrity-v1-dogfood-CHECKLIST.md](./acceptance-records/share-face-integrity-v1-dogfood-CHECKLIST.md) |
| **更新日期** | 2026-07-21 |

> **定位**
>
> 两轮试用一致证明：**流程闭环已经「敢用」**，但**内容层还不「敢发」**。  
> 跨职能评审进一步证明：FST → SFC 已写过禁词 / 展示名同源 / 禁「续」合同且工程已合入，试用踩到的破绽主因是**存量册未重渲、存量 stub 未清洗、旁路未收口**——不是缺第三套合同。  
> **本 PRD 不另起产品叙事**，定性为对 SFC/FST 底线的 **硬化 + 接管执行点 + 存量清洗**，并把两轮新增的刷新入口、时间离群、交付体面收成可排期合同。
>
> **一句话目标**：用户发群前最后一眼扫过封面、章名、图注、文件名，**找不到一处「像机器生成的破绽」**；配好 Key 的用户能一键把旧册文案刷新到应有水平。
>
> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **W0 Go** | 不出糗：存量 13 册重渲后读者面零 stub / 零脏名 / 零工程串；交付文件人话命名；SFC/FST 回归断言绿 | 文案变得优美 |
> | **W1 Go** | 兑现承诺：Key 就绪可一键刷新（替换既有入口）；时间离群不再污染时间轴且用户知情；分章行内可改名 | 策展算法重写 |
> | **W2 Go** | 更体面：紧凑档（真实册归因）· 清晰度参数化 · 署名两处同源可控 · 小红书文案包 | 影楼批量 / 小程序 |
>
> **产品共识（六条铁律）**
>
> 1. **空优于假句** — 无 Key / 低置信时读者面留空或极短中性句，禁止「白天，傍晚」类凑数。
> 2. **一名到底** — `resolve_display_title` 展示名是唯一权威；封面 / 书架 / FirstSuccess / 导出文件名 / zip 同源；禁止半修好。
> 3. **时间轴不说谎** — 离群照片不得决定章区间、不得入选「决定性瞬间」；隔离须**对照片数量诚实**（知情面，非静默消失）。
> 4. **状态即承诺** — 设置写「AI 文案已就绪」就必须提供刷新动作；做不到则措辞须弱化（见 §3.2 间隙期）。
> 5. **读者面零工程词** — `Plate`、`screen-*`、trip ID、裸 `--` 等不进预览 / 长图 / 导出产物。
> 6. **硬化不造轮** — 禁词 / 同源名 / 禁「续」所有权仍归 SFC/FST；本主题只接管执行点与存量兑现，禁止第三套平行禁词表。

> **v0.2.0 评审回写摘要（2026-07-21 · BLK-SFI-01～10）**
>
> - W0 主活改为「存量重渲 + context 层过滤 + 命名 supersede」，不再假装同源代码未写  
> - 刷新 = 替换既有「生成杂志感文案」；章名走 Chapter Naming 规则链，禁止 LLM invent  
> - 离群防线落合并环节 + `dateConfidence` 降档；附录章知情合同；分章行内改名  
> - 紧凑档以真实照片册归因重立项；完成门操作化；线框按波次列全

---

## 0. 读者指南与边界

### 0.1 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [FTT](./PRD-FINISH-THIS-TRIP-V1.md) | **纲领上位** | FTT「敢发」支线内容修复包；不改完工分层；完成门分母仅计真实输入（D-FTT-11） |
| [FST](./PRD-FIRST-SESSION-TRUST-V1.md) | **成功面所有者** | 不改成功面栈；FirstSuccess 标题同源作**硬化 + 回归断言**（非新所有权） |
| **[SFC](./PRD-SHARE-FACE-CLOSEOUT-V1.md)** | **硬化 + 接管执行点 + 存量清洗（supersede 执行层）** | 禁词 / displayTitle 同源 / 禁「续」合同仍归 SFC；本主题把过滤收口到渲染 context、强制存量重渲、补旁路（decorLine / 导出命名） |
| [Copy](./PRD-COPY-OPTIMIZATION.md) | **刷新产出服从其 sparse 预算** | 刷新图注不得从「多数 skip」变成「张张有句」；复用 `edited` / 扩展字段级 origin |
| [Chapter Naming](./PRD-CHAPTER-NAMING.md) | **章名重算权威** | 刷新时章名走 CN 规则链（anchor > segment > 日期）；**禁止 LLM invent / paraphrase 章名**（D-CN-02/09） |
| [LTN](./PRD-LAYOUT-TRUST-NARRATIVE-V1.md) | **互不重叠** | 紧凑档改长图密度杠杆；须进 B3 双预览；不得跳过 B2 保组感降级 |
| [Share-Ready](./PRD-SHARE-READY-OPTIMIZATION-V1.md) | **依赖已关闭** | 意图卡 / recipe / 五目标不重开；`Plate` 调试串 ≠ 精修解释文案 |
| [FTUE](./PRD-FTUE-OPTIMIZATION-V1.md) / [ADR-018](./adr/018-desktop-installer-layout.md) | **命名条款被本主题 supersede** | D-SFI-07 显式 supersede D-FTUE-05 / D-INS-09 的 `{tripId}` 文件命名；轨 1/轨 2 须同函数 |
| 影楼机构方向 | **已决策暂不做**（2026-07-21 产品拍板 · 见试用深走 D7） | 不做、不排期、不预留接口；D-SFI-07/13 系个人用户诉求（C10/D4），**非机构接口** |

### 0.2 试用问题 → 本文落点对照

| 试用编号 | 问题 | 落点 |
|----------|------|------|
| C1 / D1 | stub 章引与图注 · Key 就绪不刷新 | §3.1 · §3.2 · D-SFI-01/02/03 |
| C2 / D3 | 封面脏名与书架不一致 | §3.3 · D-SFI-04（**存量重渲**，非新写同源） |
| D2 | 时间离群污染时间轴 | §3.4 · D-SFI-05/06（双根因） |
| D4 | 导出文件命名工程味 | §3.3 · D-SFI-07（supersede FTUE） |
| C5 / D5 / D8 | 章名「续」/ 日期重叠 / 分章改名断链 | §3.5 · D-SFI-08/09（禁「续」归 SFC/FST 回归） |
| C6 | 精修态露 `Plate` / 模板 ID | §3.6 · D-SFI-10 |
| C7 | 无 Key 仍像杂志文案已完成 | 示例泄漏 → D-SFI-01；预期管理 → **SFC AC-SFC-11 回归**（不在本主题新做） |
| D6 | 长图密度松散 | §3.7 · D-SFI-11（W2 · 真实册归因后） |
| D10 | 清晰度档位无参数 | §3.7 · D-SFI-12（W2） |
| C10 | 辑封署名不可换 | §3.7 · D-SFI-13（W2 · 个人诉求） |
| C8 / D9 | 小红书缺文案包 | §3.7 · D-SFI-14（W2） |
| C3 | 导入忙碌态阶段句 | **不在本主题**；AC-SFI-09 前置核验 FST W0 是否已落地 |
| C4 | stale「分享图需更新」 | SFC 改善项；本主题动命名/渲染时**不回退**（AC-SFI-10） |
| C9 / B3 | 短视频 / Vlog 期待错配 | §2.2 非目标 |
| D7 | 影楼批量 / 品牌 / 锁模板 | §2.2 非目标（已决策暂不做） |

### 0.3 BLK 回写对照（v0.1.1 → v0.2.0）

| BLK | 落点 |
|-----|------|
| BLK-SFI-01 | §0.1 SFC 行 · §1 根因 · §11 SFC 回归 |
| BLK-SFI-02 | §1 · §2.3 · §3.3 · §5 E2 |
| BLK-SFI-03 | §3.3 D-SFI-07 · §5 E2/E7 · §6 |
| BLK-SFI-04 | §3.4 D-SFI-05/06 · §6 |
| BLK-SFI-05 | §3.4 · §5 E5 · OQ-1 关闭 |
| BLK-SFI-06 | §5 E4 · §12 R-1 · §9 |
| BLK-SFI-07 | §3.2 · §4 · §5 E4 |
| BLK-SFI-08 | §3.5 · §5 E6 · AC-SFI-06 |
| BLK-SFI-09 | §3.2 · §3.4 · §4 |
| BLK-SFI-10 | §2.3 · §3.7 · §9 · §11 |

---

## 1. 触发走查与根因诊断

### 1.1 走查摘要

- **首轮**：八席典型用户 + 四席博主；敢发卡在文案与命名。
- **第二轮**：十二席深走；导出闭环真跑通；新增 P0：D1（Key 就绪不刷新）、D2（时间离群）。
- **跨职能评审**：六席 Conditional Go；证实多项「未兑现」来自存量与旁路，非缺合同。

### 1.2 根因诊断（评审实锤）

| 现象 | 错误归因（v0.1.x） | 真实根因（实测） |
|------|-------------------|------------------|
| 封面 `武大--米娜` | 同源代码未写 | `resolve_display_title` / `displayTitle` **已正确**；`index.html` **渲染产物过期**未重渲 |
| 「白天，傍晚」 | 无禁词合同 | SFC `_WEAK_ENUM` 生成侧已拦；存量 `decorLine` 原样透传（`render/chapters.py`）；渲染侧 caption 已滤、**decorLine 未滤** |
| 「2018–2020」章 | 缺百分位检测 | 离群段已被切出，遭 `merge_small_buckets_with_segments` **并回**正常章 |
| 「2015.07」图注 | 图注与章区间矛盾 | 全册 `dateConfidence=low`（mtime）；与章区间**不矛盾**，须按置信度降档 |
| Key 就绪不刷新 | 无入口 | 精修·这本**已有**「生成杂志感文案」，但确认句承诺「可能覆盖」、含工程词，且对象级 `edited` 过保护 |

用户原声（摘）：

> U5：「我配了 Key，为什么章引还是『白天，傍晚』？哪里能重新生成？」  
> F1：「两天的行程里蹦出 2015 年的照片当『决定性瞬间』，长辈会以为我传错相册。」  
> P2：「文件叫 demo-album-longshot.png，我不敢直接发给客户。」

---

## 2. 目标 / 非目标 / 成功指标

### 2.1 目标

1. 存量 13 册重渲后，读者面零 stub、零脏名、零工程串；交付文件人话命名（W0）。
2. Key 就绪用户可在册级一键刷新文案（替换既有入口），明确改什么、多久、手改不动（W1）。
3. 时间离群被识别隔离，章区间与「决定性瞬间」不被污染，且用户知情可移回（W1）。
4. 交付更体面：紧凑档（真实册归因）· 清晰度参数 · 署名两处同源 · 小红书文案包（W2）。

### 2.2 非目标

- **不做**影楼机构方向（批量 / 白标 / 锁模板 / 交付单）。已决策暂不做——不排期、不访谈前置、不预留接口；未来重启须另行立项。
- **不做**视频 / Vlog；对外话术：「成册 + 长图，不做视频」。
- **不做**小程序 / 手机端工坊；窄屏 gate 维持现状。
- **不重写**策展与聚类算法；离群只做「识别 + 隔离」防线，不触碰 ADR-007 章 cap（附录章不计 cap）。
- **不重开**成功面、意图卡、五目标导出。
- **不新建**平行禁词表；以 `domain/share_face_copy.py` 为唯一实现，渲染出口调用之。

### 2.3 成功指标

| 指标 | 现状（07-21） | 目标 |
|------|---------------|------|
| 读者面禁入句抽检 | 武大「白天，傍晚」· 京都「示例游记」 | **0 命中**（重渲后 + e2e） |
| 展示名同源 | trip.json ✅ · 渲染产物 ❌ · 文件名 ❌ | 重渲后封面/文件名/FirstSuccess/书架 100% 同源 |
| 时间离群污染 | 2 处（武大 / 仙本那） | 样本册回归 0 处 |
| Key 就绪 → 刷新可发现 | 入口在「很少需要」进阶折叠区 | 入口提到整本信息区；真人 ≥4/5 自行找到 |
| 真人完成门 | 未测 | 见 §9 操作化协议：观察法「修破绽型」手改事件为零 ∧ 「敢原样发」肯定 ≥3/5 |

---

## 3. 体验合同与冻结决策（D-SFI-*）

### 3.1 读者面禁入句（W0）

**D-SFI-01** 渲染出口统一拦截，**唯一实现**为 `travelogue/domain/share_face_copy.py`（SFC 既有 `_WEAK_ENUM` 等），在 `assemble.build_context` 层调用（四读者面：index / mobile / present / longshot 同一漏斗）。禁止各模板自建正则，禁止第三套禁词表。

| 类别 | 处置 |
|------|------|
| 凑数时段句（「白天，傍晚」等） | 整句抑制（含 `decorLine` / lead / caption） |
| 示例泄漏（「示例游记」等） | 抑制并回退日期章名 |
| 题名复读（图注 == 杂志名 / 章名） | 抑制图注；**空图注时渐变条 `media-card__overlay-text` 整体不渲染**（解「每屏重复小字」） |
| 工程串 | 见 D-SFI-10 |

命中须打点（§7 `stub_hits`），防止生成侧回归被静默吞掉。  
编辑面：若 trip.json 仍含被抑制原文，显示原值 + 标记「不会出现在成片」，或随存量清洗一并修。

**D-SFI-02** 抑制后空位不补占位符、不留孤立标点；按无章引版式走；无章引时章头 padding 收紧一档。导出/截图态下 `inline-edit` 占位符**零进片**（编辑 affordance 不进长图渲染）。

分支 D（九宫格 / 海报 PIL 直出、无文案）**豁免**本过滤器，须在 IMPLEMENTATION 注明理由。

### 3.2 文案刷新入口（W1）

**D-SFI-03** 刷新是对既有「生成杂志感文案」（`data-action="llm"`）的**替换升级**——同一入口、换文案、加手改保护；**禁止并列第二按钮**。

| 项 | 合同 |
|----|------|
| 入口位置 | 精修·这本「整本信息」区（默认可见）；**禁止**埋进「很少需要」折叠进阶区 |
| 章名 | 走 Chapter Naming 规则链重算（anchor > segment > 日期）；**禁止 LLM invent** |
| 章引 / 图说 | 走 Copy 管线；服从 sparse 预算（刷新后不得张张有句） |
| 手改保护 | 字段级 `origin: user\|stub\|llm`（E4 前置）；`origin=user` 永不覆盖 |
| 耗时承诺 | 档位句「通常不到一分钟」（禁写死会说谎的「约 X 秒」）；超时沿 FST 进度纪律升级 |
| 无 Key | 保留既有降级提示「当前为本机文案 · 配置写作引擎后可升级」（与隐藏入口二选一：统一为**保留降级提示**） |

**提示条纪律**（并入 task dock 单槽栈，非另起横幅）：

- 排序：`copyRefresh` > `longshotStale`（先刷新再导出，省一次导出）
- 非模态、不遮挡 / 不下压主 CTA
- 导出流程与成功面内**不出现**
- 「不再提示」= **册级**持久化 dismiss；同会话最多 1 条
- 冻结句见 §4

**间隙期（W0 上线、E4 未落地）**：设置面板「AI 文案 已就绪」临时弱化为「已连接 · 新生成的册子将使用 AI 文案」；E4 落地后恢复「已就绪」+ 刷新入口（铁律 4）。

### 3.3 一名到底（W0）

**D-SFI-04** 展示名同源代码**已上线**（`resolve_display_title` → 封面 / 书架 / FirstSuccess）。本主题 W0 主活：

1. **存量 13 册批量重渲**（或首次打开强制重渲门禁），使 HTML 与 trip.json 一致；
2. 前后端 humanize（`title_humanize.py` ↔ `title-humanize.js`）同步纪律，不造第三份实现。

**D-SFI-07** 导出产物命名统一为 `「展示名-类型[-序号].ext」`（例：`京都雨季漫游-长图.png`）。

- **本决策显式 supersede** [FTUE D-FTUE-05](./PRD-FTUE-OPTIMIZATION-V1.md)、[ADR-018](./adr/018-desktop-installer-layout.md) / D-INS-09 的 `{tripId}` 文件命名条款；轨 1（服务端）与轨 2（html2canvas 客户端回传）**同一命名函数**。
- 命名唯一来源：`resolve_display_title`（禁止原始 `meta.title` 进海报/九宫格文件名）。
- 覆盖：长图 · 按章长图 · 九宫格 · 海报 · **zip 文件名**（现 `trip-{tripId}.zip` 一并改）· zip 内路径。
- 文件系统非法字符安全替换；重名追加序号。
- **旧产物迁移**：导出新文件后，同册旧命名产物归档或清理；书架缩略图 glob（`studio_trips._pick_preview`）与 `longshot_outputs_stale` 同步改匹配规则，禁止 `max(mtime)` 捡到旧脏名文件。
- 注：本条服务个人用户敢发体面（试用 C10/D4），**非影楼机构接口**。

### 3.4 时间轴可信（W1）

**D-SFI-05** 时间离群识别与隔离（双根因对症）：

| 层级 | 合同 |
|------|------|
| 主信号 | 复用现有 segment gap；离群资产**不得**经 `merge_small_buckets_with_segments` 并回正常章 |
| 兜底 | P10–P90 密度区间；阈值 = `clamp(k × 核心跨度, 下限, 180d)`（禁止固定 180 天唯一判据） |
| 小册保护 | 离群占比 >20% 时放弃隔离，走既有多段警告 |
| 多段 / 年度精选 | `segments≥2` 豁免自动隔离或要求用户确认（关闭原 R-2 OQ） |
| 注入点 | `_curate_preflight` 打 `timeOutlier`（与低分辨率排除并列）；封面池 / 决定性瞬间池上游排除 |
| 章区间 | `bucket_day_span` / `title_for_bucket_span` **排除**离群日期 |
| 附录章 | ≥2 张离群 → 册尾附录章，章名冻结「往年 · 旧照 · N 张」；**不计章 cap**、不进 `normalize_bucket_counts`（不触发 ADR-007 R4）；compose 后作为特殊章追加 |
| 仅 1 张 | 不单独开附录章，静默降权；其日期仍须从章区间与图注绝对年份中排除 |
| coverage | 附录资产从长图覆盖率分母排除 |

**知情合同**（对照片数量诚实）：

- 预览附录章头显示「往年 · 旧照 · N 张」
- 分章对话框列出该章及原因句
- 精修支持单张「移回原章」（移回后不再被隔离）
- 长图默认**不含**附录章；导出设置须**显性提示**「未含 · 往年旧照（N 张）」且可勾选包含（原 OQ-1 **关闭**为此口径）

**D-SFI-06** 读者面日期降档：

- `dateConfidence=low`（含 mtime 兜底）→ 抑制绝对年份，仅保留时段词（若有）
- 图注日期与章区间矛盾时同样抑制年份
- §6 降级按 `dateConfidence` 分档，**禁止**「无 EXIF → 不判离群」（`takenAt` 经 mtime 永不为空）

### 3.5 分章体验（W1）

**D-SFI-08** 章名禁「续」：回归断言 [SFC §3.5](./PRD-SHARE-FACE-CLOSEOUT-V1.md) / [FST](./PRD-FIRST-SESSION-TRUST-V1.md)（**非** Chapter Naming 条款）；同日多章用时段 → segment → `·二`/`·三`（禁 `（N）` · [PMX D6](./PRD-POST-MERGE-UX-FIXPACK-V1.md)）。

**D-SFI-09** 分章面板：

- **行内改名**（点「改名」→ 该行输入框 → 失焦保存，auto-persist + IME 防抖）；删除死句「深改请用精修 · 这本」
- **禁止**「关分章 → 开精修 → 找锚点」跳转（精修·这本无章名字段；两面板互斥且 540ms 动画）
- 「为什么这样分章」增补冻结句：「章节按拍摄节奏切分，同一天可能出现在多章」
- 底部危险按钮由「重新生成」改名为「**重新分章**」（全站禁止裸「重新生成」指代两种动作）

### 3.6 工程词零泄漏（W0）

**D-SFI-10** 精修覆盖层 `Plate · 01`、`screen-portrait-*` 等移入 `?debug=1`；普通用户可见面为人话或不显示。属**文案级 UI Delta**（非「零 UI」），须补修前/修后对照帧。

### 3.7 交付体面（W2 · 各项可独立砍；进编码前须有线框）

| 决策 | 内容 |
|------|------|
| **D-SFI-11** | 长图「紧凑」档。**前置**：用 ≥1 本**真实照片册**（非 demo-album 合成占位）重放归因表后方可编码。杠杆：**章头带瘦身**（首章全头，第 2 章起 ≤48px 薄 divider；日期与章名同义时二选一）+ **封面文案去重**（题名/日期各一次）+ **moment 复用屏折叠**（LTN B2 第②级：代表图 + N 徽标）。屏缝 4px **保持不动**。须进 B3 双预览；不得跳过 B2 保组感。切换密度档走「更新版面」流程。 |
| **D-SFI-12** | 清晰度档位标注须与真实产物换算一致：写清「输出宽 = 逻辑宽 × scale」或改造为真 1080/1440；禁止上线即失信的参数 |
| **D-SFI-13** | 署名三态（默认 / 自定义 ≤14 全角单行 / 不显示）为**册级唯一字段**，同时驱动 `cover-closing__brand` 与 `longshot-boundary-footer__brand`，两处格式统一。自定义取消 `uppercase`。关闭态辑封保留 stats 行作版脚锚。系个人诉求，非机构接口 |
| **D-SFI-14** | 小红书导出成功面追加「复制标题 + 正文 + 话题」；无 Key 时仅标题 + 话题模板（OQ-2 倾向冻结）。成功面用 dock 展开/popover，不得硬塞进单行 bar |

---

## 4. 触点与文案矩阵（冻结句）

### 4.1 术语冻结

| 对内 / 数据 | 用户可见 |
|-------------|---------|
| chapter.title | 章名 |
| lead / hook（章级） | 开头一句（禁用「章引」行话于确认句） |
| caption | 图说（与精修面「图说」对齐；禁用与「图注」混用） |
| narrate / llm refresh | 重新生成文案（须带宾语） |
| chapter structure regen | **重新分章**（禁止裸「重新生成」） |

### 4.2 冻结句

| 触点 | 句子 | 波次 |
|------|------|------|
| 刷新提示条（dock） | 「AI 文案已就绪，可为这本重新生成文案」·「重新生成文案」·「不再提示」 | W1 |
| 刷新确认 | 「将为这本重新写开头一句和图说；你自己改过的内容不会动。通常不到一分钟。」 | W1 |
| 间隙期设置 | 「已连接 · 新生成的册子将使用 AI 文案」 | W0→W1 |
| 附录章名 | 「往年 · 旧照 · N 张」 | W1 |
| 导出未含提示 | 「未含 · 往年旧照（N 张）」· 可勾选包含 | W1 |
| 分章解释增补 | 「章节按拍摄节奏切分，同一天可能出现在多章」 | W1 |
| 分章危险按钮 | 「重新分章」 | W1 |
| 署名设置 | 「作品署名：默认 / 自定义 / 不显示」 | W2 |
| 禁入词增量 | 并入 SFC/FTUE/Trust 禁词表（非第三套）：`示例游记`、`Plate`、`screen-`、trip ID、裸 `--` | W0 |

---

## 5. 工程任务（概要）

| # | 任务 | 波次 | 涉及 |
|---|------|------|------|
| E0 | **schema 收敛 + 字段级 origin**（`user\|stub\|llm`）；修 meta/chapter `edited` 漂移；迁移存量布尔 | W1 前置（可与 W0 并行启动） | schemas/trip.schema.json · copy_patch · llm_narrate |
| E1 | context 层调用 `share_face_copy` 统一过滤 + decorLine 覆盖 + 空位/空渐变收缩 + stub_hits 打点；盘点合并既有零散过滤器 | W0 | render/assemble · render/chapters · render/context · domain/share_face_copy |
| E2 | **存量 13 册批量重渲** + 导出命名 supersede（含 zip、轨 2 客户端、glob/stale 消费者、旧产物迁移） | W0 | studio 迁移脚本 · longshot.py · platform_longshot · photo_grid_pack · poster_bric_pack · longshot-client.js · studio_trips |
| E3 | 精修调试串移入 debug；修前/修后对照帧 | W0 | preview-toolbar / refine 覆盖层 |
| E4 | 替换升级「生成杂志感文案」→「重新生成文案」；CN 章名重算 + Copy sparse；字段级手改保护；dock 提示条；事务写回复用现有 tmp+replace | W1 | preview-toolbar · llm_narrate · chapter_titles · studio_narrate |
| E5 | 离群：合并环节硬断言 · 自适应阈值 · timeOutlier 资格 · 附录章 · 知情面 · dateConfidence 读者面降档 | W1 | bucket_planning · time_segments · curate preflight · moment_scoring · 封面池 · moment_exif · chapter-panel |
| E6 | 分章面板行内改名 +「重新分章」改名 + 解释句 | W1 | chapter-panel.js · copy_patch（章名路径） |
| E7 | 紧凑档（真实册归因后）· 清晰度参数 · 署名两处同源 · 小红书文案包 | W2 | longshot.css · export handlers · cover-closing · task-dock |

依赖：E0 先于 E4 的字段级保护；E2 命名先于刷新完成面引用文件名；E5 输出过 LTN 回归；E1 的 W0 豁免先用**对象级** `edited` 粗豁免，E0/E4 落地后收敛字段级。

---

## 6. 错误与降级

| 场景 | 行为 |
|------|------|
| 刷新失败 / 超时（>90s） | toast「这次没写完，稍后再试 · 原文案保持不变」；禁止半册新半册旧（复用 narrate 全缓冲一次落盘） |
| 离群识别 | 按 `dateConfidence` 分档；low 不参与绝对年份展示；占比过高放弃隔离 |
| 文件名重名 | 追加序号；旧命名产物迁移/清理，禁止 stale/缩略图捡旧文件 |
| 重渲失败 | 保留旧 HTML + 可读错误；不进「已重渲」集合 |

---

## 7. 埋点（增量）

| 事件 | 字段 |
|------|------|
| `copy_refresh_shown / clicked / done / failed` | trip_id · stub_hits · duration · origin_skip_count |
| `stub_hits`（渲染侧） | surface · field · pattern_id（防生成回归静默） |
| `outlier_isolated` | trip_id · n_outliers · span_days · dateConfidence 分布 |
| `export_renamed` | 命名规则版本 · legacy_cleaned |
| `album_rerender_batch` | n_ok · n_fail |
| 抽检契约 | 读者面禁入句命中数 = 0（e2e） |

---

## 8. 非功能

- 禁入句过滤在 **context 构建层**同步执行，单册增耗 < 50ms（禁止对最终 HTML 全文跑多模式回溯正则）。
- 离群**识别** 250 张 < 2s（微秒级运算）；隔离引发的 layout 重排**不计入**本预算，单独验收。
- 文案刷新幂等；可取消须保证 kill 发生在 save 之前（现同步 narrate 天然满足；若改异步须单列验收）。

---

## 9. 里程碑与完成门

| 波次 | 内容 | 门 |
|------|------|-----|
| **W0** | E1–E3 + 存量重渲 + 命名 supersede | 13 册抽检禁入句 0；武大封面无 `--`；SFC AC-SFC-01/03/07 + FST 忙碌态前置核验 + stale 文案不回退 |
| **W1** | E0 + E4–E6 | 武大 / 仙本那回归；刷新手改保护用例；附录知情 AC；分章行内改名可用 |
| **W2** | E7（各项可独立砍） | 真实册归因表签字；双轨密度 AC；署名两处同源；各项有线框 |
| **主题完成门** | 真人 N≥5 | 见下方操作化协议 |

**完成门操作化协议**（写入待建 ACCEPTANCE）：

1. **样本**：真实输入（示例册另列，不计分母）；样本须达 FTT **Completed**（ExportSucceeded ∧ DeliveryLocated）
2. **配比**：≥2×U1 · ≥1×U5 · ≥1×F1/F2；有 Key ≥2 · 无 Key ≥1
3. **测法**：观察法任务式——受测者完成「发到群」全任务；记录是否进入文字编辑
4. **归因**：事后访谈；仅「修破绽型」编辑计失败；风格偏好型编辑不计失败
5. **通过**：修破绽型手改事件为零的样本占比 ≥3/5，且语言题「敢原样发吗」肯定作答 ≥3/5（复用 FTT §10.4 题 2）

---

## 10. 线框与依赖

| # | 波次 | 面 | 说明 |
|---|------|-----|------|
| 0 | W0 | E3 修前/修后对照帧 | 调试串移除（文案级 UI Delta） |
| 1 | W1 | 精修·这本「重新生成文案」 | 替换关系、确认弹层、进行中/失败/超时；入口在整本信息区 |
| 2 | W1 | 提示条 × task dock 仲裁图 | copyRefresh > stale；让位规则 |
| 3 | W1 | 分章面板行内改名 | 输入/保存/失败；「重新分章」按钮 |
| 4 | W2 | 署名三态设置分区 | 精修·这本；与封底/长图尾联动 |
| 5 | W2 | 小红书成功面文案包 | dock 展开/popover；无 Key 降级 |

W0 无新交互面（过滤 / 重渲 / 命名为规则与迁移）。  
W2 各项进编码前须有对应线框（§9 W2 门）。

排期：E2 命名 → E4；E5 → 决定性瞬间调优；E0 与 W0 可并行。

---

## 11. 验收合同草案（AC-SFI-*）

| AC | 断言 | 波次 |
|----|------|------|
| AC-SFI-01 | 样本 13 册重渲后读者面禁入句命中 = 0（自动抽检；含 decorLine） | W0 |
| AC-SFI-02 | 武大用例：封面/书架/FirstSuccess/导出文件名四处一致且无 `--` | W0 |
| AC-SFI-03 | 精修态无 `Plate` / `screen-*`（非 debug） | W0 |
| AC-SFI-04 | 题名复读图注抑制后空渐变条不渲染；导出态零 inline-edit 占位 | W0 |
| AC-SFI-05 | Key 就绪 + stub 命中：dock 提示条符合纪律；刷新后禁入句 = 0；`origin=user` 字段不变；章名非 LLM invent | W1 |
| AC-SFI-06 | 仙本那：离群段不被小桶合并回灌；章名无「2018–2020」；附录/降权规则生效 | W1 |
| AC-SFI-07 | 武大：`dateConfidence=low` 读者面无绝对年份「2015」；决定性瞬间不选离群 | W1 |
| AC-SFI-08 | 分章行内改名可用；按钮文案为「重新分章」；解释句含日期重叠说明 | W1 |
| AC-SFI-09 | 附录知情：章头 N 张 · 分章列出原因 · 可移回 · 导出未含时显性提示 | W1 |
| AC-SFI-10 | 回归：SFC AC-SFC-01/03/07；stale「分享图需更新」不回退；C7 预期管理 → AC-SFC-11 | W0 |
| AC-SFI-11 | 导入忙碌态：前置核验 FST W0；若未落地则升级为跨主题阻塞项（非空转回归） | W0 |
| AC-SFI-12 | 紧凑档：非照片纵向像素占比较默认下降 ≥40%（真实册 fixture 脚本）∧ 5 席盲评敢发偏好 ≥3/5 | W2 |
| AC-SFI-13 | 署名三态同时驱动辑封与长图尾；清晰度参数与产物一致；小红书文案包可复制 | W2 |

---

## 12. 风险与开放问题（OQ）

| # | 风险 / OQ | 倾向（v0.2.0） |
|---|-----------|----------------|
| R-1 | 禁入句误杀手改「白天」 | **已关闭**：W0 用对象级 `edited` 粗豁免；W1 随 E0 字段级 origin 收敛 |
| R-2 | 跨年长旅 / 年度精选误伤 | **已关闭**：多段册豁免或确认；阈值随核心跨度缩放 |
| R-3 | 刷新 / 紧凑档与版面联动 | 触发既有「更新版面」流程，不做静默重排 |
| R-4 | 存量重渲耗时与用户感知 | 后台批处理 + 打开时按需门禁；进度人话 |
| **OQ-2** | 小红书文案包无 Key 最低形态 | 标题 + 话题模板，不造正文（W2 编码前冻结） |

> 原 OQ-1（附录是否进长图）**已关闭** → §3.4 知情合同。  
> 影楼方向**已决策暂不做**，不留 OQ。

---

## 13. 评审清单

- [x] 产品：波次划分与铁律 4（间隙期弱化 + E4 兑现）
- [x] 工程：E1 收口在 context 单漏斗；分支 D 豁免
- [x] 工程：字段级 origin + schema 漂移收敛（E0）
- [x] 算法：双根因 + 合并防线 + dateConfidence + 自适应阈值
- [x] UX：提示条 dock 纪律 + 附录知情 + 完成门操作化
- [x] 视觉：紧凑档真实册归因 + 杠杆重写 + AC 双轨
- [x] 边界：SFC supersede 执行层；FTUE 命名 supersede；禁「续」归 SFC/FST
- [x] 上位：FTT 侧回写脚注认可本主题为「敢发」支线（[PRD-FINISH-THIS-TRIP-V1.md](./PRD-FINISH-THIS-TRIP-V1.md) **v0.2.1-FTT** · §4.2 / 附录 C · 2026-07-21）
- [x] 编码前：IMPLEMENTATION + ACCEPTANCE + 线框 F0–F5 + 狗粮清单已建档（2026-07-21）

---

## 附录 A · 紧凑档视觉参数（W2 · 真实册归因后生效）

| 项 | 默认档（**真册基线**：仙本那 DES-SFI-01） | 紧凑档建议 |
|----|---------------------------------------------|------------|
| 照片屏缝 | 4px | **保持 4px** |
| 章头带 | 每章全头 ~109px（Σ≈327px / 3 章） | 首章全头；第 2 章起 ≤48px；日期与章名同义二选一 |
| 封面 panel | 本册 maxDup=1；仍防回归 | 题名 + 日期各一次 + 副题一次 |
| 复读图注 | 每屏杂志名+日期 | W0 D-SFI-01 已抑制；空渐变不渲染 |
| moment 复用屏 | 真册 reused=0；占位册曾 5→7 屏 | 折叠为代表图 + N 徽标（LTN B2 ②） |
| 尾 footer | 偏松 | padding 收紧；署名受三态控制 |
| 验收锚 | 非照片纵向占比 **10.4%**（仙本那 DES 立项）· 复跑默认 **11.3%** | 下降 ≥40% → **≤6.8%**（复跑基线×0.6）；2026-07-21 紧凑实测 **3.0% / −73%** 脚本 ✅ |
| 紧凑主杠杆（补） | 呼吸停顿 ~120px×N | **紧凑档撤掉**（默认档保留）；另压 hook / 封面 panel / 辑封 |

> 立项签字见 [DES-SFI-01 记录](./acceptance-records/share-face-integrity-v1-des01-attribution-2026-07-21.md)。demo-album（~15.9%）仅历史对照，不作基线。  
> AC-12 脚本半门记录：[ac12-compact-2026-07-21](./acceptance-records/share-face-integrity-v1-ac12-compact-2026-07-21.md)。

---

## 附录 B · 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.0 | 2026-07-21 | 首版草案；整合两轮试用 C1–C10 / D1–D10 |
| v0.1.1 | 2026-07-21 | 影楼方向改为已决策暂不做 |
| v0.2.0 | 2026-07-21 | 跨职能评审回写：BLK-SFI-01～10 全部合入；W0/W1/W2 重定义；状态 → Conditional Go（评审回写完成） |
| v0.2.1 | 2026-07-21 | Doc 包齐：IMPLEMENTATION · ACCEPTANCE · 线框 F0–F5 · 狗粮清单 · README 索引；状态 → Ready for Kickoff W0；**DOC-SFI-08** FTT 脚注已回写（FTT v0.2.1） |
| v0.2.2 | 2026-07-21 | **DES-SFI-01**：附录 A 基线改为仙本那真册（非照片纵向 10.4%）；demo-album 降为对照 |
| v0.2.3 | 2026-07-21 | AC-12：紧凑档撤呼吸停顿；仙本那复跑 11.3%→3.0%（−73%）脚本过门；状态 → W2 工程已接 |
