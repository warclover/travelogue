# Travelogue · 敢发净化 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio（本机 Studio / 桌面打包同等体验） |
| **文档版本** | **v0.1.1** |
| **状态** | **Conditional Go · Must-Fix 已回写**（[评审纪要](./acceptance-records/share-face-purity-v1-review-2026-07-24.md) · BLK-SFP-01～10） |
| **主题代号** | 「敢发净化」— **SFP**（Share-Face Purity） |
| **触发来源** | [2026-07-24 十席 Persona 反馈试用](./acceptance-records/persona-feedback-trial-2026-07-24.md)（Agent 模拟联评 + 契约 5/5）；交叉对照 SFC / SFI / Chapter Naming / Copy / NAS |
| **前置条件** | 首页 v2（M21）；Share-Ready / SFC / SFI 工程已合入；**当前版用户面 = 无 AI**（[NAS](./PRD-NO-AI-SURFACE-V1.md)） |
| **关联文档** | [PRD-SHARE-FACE-CLOSEOUT-V1.md](./PRD-SHARE-FACE-CLOSEOUT-V1.md) · [PRD-SHARE-FACE-INTEGRITY-V1.md](./PRD-SHARE-FACE-INTEGRITY-V1.md) · [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md) · [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) · [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md) · [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) · `travelogue/curation/chapter_titles.py` · `travelogue/domain/title_humanize.py` · `travelogue/domain/share_copy_pack.py` |
| **评审记录** | [acceptance-records/share-face-purity-v1-review-2026-07-24.md](./acceptance-records/share-face-purity-v1-review-2026-07-24.md) · **Conditional Go** |
| **验收** | [ACCEPTANCE-SHARE-FACE-PURITY-V1.md](./ACCEPTANCE-SHARE-FACE-PURITY-V1.md)（Kickoff 前建骨架；本文 §10 为索引） |
| **实施清单** | [IMPLEMENTATION-SHARE-FACE-PURITY-V1.md](./IMPLEMENTATION-SHARE-FACE-PURITY-V1.md)（Kickoff 前建骨架） |
| **手测狗粮** | `docs/acceptance-records/share-face-purity-v1-dogfood-CHECKLIST.md`（Kickoff 前补） |
| **线框** | [wireframes/share-face-purity-v1-wireframe.html](./wireframes/share-face-purity-v1-wireframe.html)（**已补** · F1–F5 · **F1–F3 已签核 2026-07-24**；F4/F5 随 W1/W2） |
| **试用底稿** | [persona-feedback-trial-2026-07-24.md](./acceptance-records/persona-feedback-trial-2026-07-24.md) |
| **更新日期** | 2026-07-24 |

> **v0.1.1 评审回写摘要（多席 Conditional Go）**
>
> - BLK-SFP-01：OQ-SFP-01～04 **已关闭**（§11.2）  
> - BLK-SFP-02：线框 F1–F5 挡门；W0 UI ≥ F1–F3 · **✅ F1–F3 已认可（2026-07-24）**  
> - BLK-SFP-03：相邻 PRD 脚注（Chapter Naming 禁序号腔 · SFC 日期串/stale L2）— Kickoff 前落脚注  
> - BLK-SFP-04：同日策略改为 **默认同名日期 · 弱桶才合并**（§4.1）  
> - BLK-SFP-05：「可重排」tooltip + 次级徽标合同（§4.5）  
> - BLK-SFP-06：浮层互斥 **升入 W0**  
> - BLK-SFP-07：打开预览静默 migrate 主路径（§4.2 / §6）  
> - BLK-SFP-08～10：AC/IMPL/狗粮骨架 · 喜欢项零回退 · NAS 文案纪律  
> - **本轮不动代码**；先线框 + 文档骨架，编码 Kickoff 另排期

> **定位**
>
> 07-24 试用证明：导出闭环与分享配方已达「敢用」；真正阻断「敢原样发」的，是读者面仍在泄漏**序号腔章名、脏展示题名、复读式图注、时间轴穿越感、状态词表分裂、面板互斥破洞**，以及小红书「有图无文」的入口错位。  
> 本主题 **不重做配方分流、不重做精修 IA、不解开 NAS 的无 AI 面**，只把试用吐槽收成一条可排期的**读者面净化合同**：从生成规则与状态机根上修，而不是改几个字符串。
>
> **一句话目标**：无 AI 用户打开成片后，章名/题名/图注/时间轴/书架状态词 **不丢人、不穿越、不工程**，小红书导出至少能带走「标题 + 话题」；愿意点「发微信群 / 选择分享」。
>
> **明确排除（产品已决策）**
>
> - **E1 / E9 及一切 AI 文案入口、Key 配置、重新生成文案** —— 属 [NAS](./PRD-NO-AI-SURFACE-V1.md) 有意隐藏，**本主题不立项、不验收、不回写试用吐槽**。  
> - 影楼/机构批量交付、Vlog 成片 —— 范围外。
>
> **产品共识（六条铁律）**
>
> 1. **空优于假句，也优于序号腔** — 同日多章禁止「· 二 / · 三」上读者面；分不出时段时 **允许同名日期**，仅弱桶合并。  
> 2. **展示名必须体面且同源** — 封面 / 书架 / 辑封 / 导出文件名同源解析；脏日期串不得压过体面 `title`。  
> 3. **空优于复读** — 禁止「日期 · 杂志名」式图注填坑；`frame` scope 下 lead 空是合同，不是 bug。  
> 4. **章节时间序是 SSOT** — 章级必须按可靠拍摄时间升序；跨年混拍显式策略，禁止「八月后接一月」无解释。  
> 5. **状态一词一义** — 书架/预览对「算法可重排 / 分享图过期 / 刚导出就绪」分层表达，禁止「可更新」与「分享图需更新」语义打架。  
> 6. **面板互斥** — 同时只允许一层主浮层可点；打开分章必须关掉导出设置（反之亦然）。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 与相邻主题的边界（拥有 / 硬化 / 不碰） |
| §1 | 试用结论、问题清单、**根因树** |
| §2 | 目标 / 非目标 / 成功指标 |
| §3 | 体验合同与冻结决策（D-SFP-*） |
| §4 | 分域方案（章名 / 题名 / 图注 / 时间轴 / 词表 / 浮层 / 小红书） |
| §5 | 工程任务索引 |
| §6～§8 | 错误 / 埋点 / 非功能 |
| §9 | 里程碑 |
| §10 | 验收 AC 索引 |
| §11 | 风险与 OQ |
| 附录 | 试用映射 · 反例 · 版本记录 |

### 0.1 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [NAS · 无 AI 面](./PRD-NO-AI-SURFACE-V1.md) | **遵守 · 不抢** | 默认面继续无 AI；**不**恢复设置/再生文案入口；小红书文案包走**无 LLM 合同**（title + topics，body 可空） |
| [SFC · 敢发收口](./PRD-SHARE-FACE-CLOSEOUT-V1.md) | **硬化执行缺口** | 继承「空优于假句 / 展示名体面 / 词表人话」；本主题补 **序号腔、日期串脏名、三态 stale 模型、浮层互斥** |
| [SFI · 敢发完整性](./PRD-SHARE-FACE-INTEGRITY-V1.md) | **并行硬化** | 离群章名禁跨年拼贴仍归 SFI；本主题补 **章级时间排序 SSOT** 与年度混拍策略 |
| [Chapter Naming](./PRD-CHAPTER-NAMING.md) | **修订同日回退合同** | 本主题 **拥有**「禁止 ·二/·三 上读者面」的冻结决策（**D-SFP-01 supersede** 原「时段/序号可接受」用户侧口述）；杂志级锚点章名仍归原轨。**Kickoff 前**于 Chapter Naming 增脚注指针 |
| [SFC](./PRD-SHARE-FACE-CLOSEOUT-V1.md) | **硬化 + 脚注** | 日期串 noise（D-SFP-04）与 stale L2「可重排」（D-SFP-09）**Kickoff 前**于 SFC 增脚注，避免第三套平行词表 |
| [Copy](./PRD-COPY-OPTIMIZATION.md) | **挡门 · 移交深度** | 本主题挡「题名复读图注」；真 LLM 气质留给 AI-Return |
| [Share-Ready](./PRD-SHARE-READY-OPTIMIZATION-V1.md) / [Output Recipe](./PRD-OUTPUT-RECIPE-V1.md) | **不做** | CTA / Band / 意图卡合同不变；**喜欢项零回退**（五目标 / 人话文件名 / 清晰度像素 / 紧凑密度） |
| AI 文案 / Key / 再生 | **不做** | 试用 E1/E9 **刻意忽略** |

---

## 1. 背景与问题

### 1.1 试用方法（可复现）

| 项 | 约定 |
|----|------|
| **环境** | Windows · Studio `http://127.0.0.1:8766` |
| **样片** | `demo-album` · `demo-d6697c8dca` · `demo-3ee2727aea` · 书架 11+ 本 |
| **方式** | Playwright 实机 + `stable_qh_persona_trial.py` 5/5 PASS + trip.json 抽检 |
| **性质** | Agent 模拟；真人 N≥5 仍待补签 |

### 1.2 问题清单（本主题认领）

| 试用 ID | 本主题 ID | 严重度 | 用户感知 | 本主题是否认领 |
|---------|-----------|--------|----------|----------------|
| E2 | **P-SFP-01** | P0 | 「5月27日 · 三」不敢发 | ✅ |
| E3 | **P-SFP-02** | P0 | 封面 `旅行 · 24 1 20–25 1 16` 出糗 | ✅ |
| E4 | **P-SFP-03** | P0 | 图注复读题名 / 「黄昏」敷衍 | ✅（lead 全空 = 合同，见 §4.3） |
| E5 | **P-SFP-04** | P1 | 八月后接一月像穿越 | ✅ |
| E6 | **P-SFP-05** | P1 | 「可更新」vs「分享图需更新」 | ✅ |
| E7 | **P-SFP-06** | P1 | 分章 × 被导出 ▾ 挡住 | ✅ |
| E8 | **P-SFP-07** | P2 | 小红书有图无文案包入口 | ✅（无 AI 合同） |
| E1 / E9 | — | — | AI 配置 / 再生文案 | ❌ **排除**（NAS） |

### 1.3 核心判断

> 这些问题**不是**「文案模型不够聪明」，而是 **规则回退合法化了丢人字符串**、**展示名解析信任了脏历史**、**状态机三词未分层**、**浮层未互斥**、**能力做了但挂在用户找不到的成功后入口**。  
> 系统性解法 = **改合同 + 改生成/解析 SSOT + 加回归闸**，禁止只改某一本样片或只改 UI 文案。

### 1.4 根因树（按域）

```text
敢发受阻（无 AI 面）
├─ 读者面文字丢人
│  ├─ P-SFP-01 章名「·三」
│  │    └─ chapter_titles._same_day_followup_title 把中文序号当作合法最终名
│  ├─ P-SFP-02 脏 displayTitle
│  │    └─ resolve_display_title 优先接受 stored displayTitle；
│  │       is_folder_title_noise / 日期串检测盖不住「24 1 20–25 1 16」
│  └─ P-SFP-03 图注复读
│       ├─ stub caption 模板即「日期 · place」，place 可退化成题名
│       └─ frame scope 清空 lead（设计正确）但未挡「题名回声」caption 上读者面
├─ 结构可信度崩
│  └─ P-SFP-04 章序穿越
│       └─ clustering 路径信任 segment 输入序；缺「章级时间升序」SSOT
├─ 状态可理解性崩
│  └─ P-SFP-05 词表分裂
│       └─ 「可更新」(algorithm) / 「分享图需更新」(longshot) / 「已就绪」(session)
│          三态真实存在，但用户面未分层解释且「可更新」偏工程
└─ 交互/出口断裂
   ├─ P-SFP-06 浮层叠层
   │    └─ chapter-panel z=245 < export-popover z=400；openPanel 未关导出层
   └─ P-SFP-07 文案包「有能力无入口」
        └─ build_share_copy_pack 已存在；仅成功后 task-dock 且无 AI 时 body 空
```

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-SFP-01** | 读者面章名 **零**「·二/·三/·N」序号腔（新建册 + 刷新章名路径） |
| **G-SFP-02** | 封面/书架题名在「体面 title vs 脏 displayTitle」冲突时 **永不展示脏串** |
| **G-SFP-03** | 读者面图注 **零**「日期 · 杂志题名」复读；无合格图注则空 |
| **G-SFP-04** | 有可靠拍摄时间的章节 **严格时间升序**；跨年混拍有可解释策略 |
| **G-SFP-05** | 书架/预览状态词 **一词一义**，U4 不再问「可更新是什么意思」 |
| **G-SFP-06** | 分章与导出设置 **互斥**，关闭钮 100% 可点 |
| **G-SFP-07** | 小红书目标下，用户在 **导出前或成功面** 能复制「标题 + 话题」（正文按 NAS 可空） |

### 2.2 非目标

| 不做 | 理由 |
|------|------|
| 恢复 AI 文案 / Key /「重新生成文案」 | NAS 产品决策 |
| 强制每章有 lead / 文艺章名 | 与 sparse / Chapter Naming 铁律冲突 |
| 影楼批量、品牌水印、Vlog | 范围外 |
| 重做意图卡 / 五目标配方 | 试用中属喜欢项，已达标 |
| 仅手改样片 trip.json「洗数据」充验收 | 必须修生成与解析路径 |

### 2.3 成功指标（狗粮向）

| 指标 | 门槛 |
|------|------|
| 样片书架抽检章名含「·二/·三」 | **0**（刷新/重导后） |
| `demo-3ee2727aea` 封面可见题名 | 不为 `旅行 · 24 1 20–…` 类脏串；优先体面名或合规回退 |
| 抽检 caption 「日期 · 题名」上读者面 | **0**（允许空） |
| 有 takenAt 的章序逆序对 | **0** |
| 分章打开后点 × | 1 次成功，不被导出 caret 拦截 |
| 小红书路径「复制文案包」可达 | 导出设置确定后 **或** 成功面可见；无 AI 时至少 title+topics |
| 契约 | 既有 persona / SFC 相关自动化不回退 |

---

## 3. 体验合同与冻结决策

### 3.1 冻结决策（D-SFP-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-SFP-01** | **禁止序号腔上读者面** | `_CN_ORDINALS` 回退 **不得**成为最终 `chapter.title`；仅允许内部 debug / explain |
| **D-SFP-02** | **同日多章消歧优先级** | ① 时段（上午/下午/晚上等）② 不重复的 segment 短标 ③ **允许同名日期**（靠章号 01/02 区分）④ **仅弱桶合并**（同日后续桶 `len≤2` 且无 daypart/segment 才并入前桶）⑤ **永不**用「·二/·三」。手改章名（`titleOrigin=user`）不得被 migrate/刷新覆盖（USR-SFP-04） |
| **D-SFP-03** | **展示名质量序** | `resolve_display_title`：**先拒脏 → 再在候选中择优**。候选序：用户手改体面名 > `meta.title`（非 noise）> 清洗后 displayTitle > 地点·日期回退。**禁止**「先到先得」信任脏 stored displayTitle |
| **D-SFP-04** | **日期串 = noise** | 匹配「数字空格日期跨度 / 缺月字的 y.m.d 粘连 / `旅行 ·`+裸日期」等 → `is_folder_title_noise` 或等价判定为真 |
| **D-SFP-05** | **图注合同（无 AI）** | 读者面 caption：空 / 用户手改 / **非题名回声的短中性标签**。禁止 `{date} · {magazineTitle}`。alt 可用技术回退，**不进长图文字层** |
| **D-SFP-06** | **lead 空是合法** | 默认 `frame` / sparse 下 chapter.lead 全空 **不算缺陷**；验收不得要求「补 lead」 |
| **D-SFP-07** | **章级时间 SSOT** | curate 输出 chapters 前必须 `sort_chapters_by_temporal_key`；clustering segment 输入序 **不可**直接决定章序 |
| **D-SFP-08** | **跨年混拍策略** | 若 `dateEnd.year != dateStart.year` 或章间跨年：① 章序仍按绝对时间升序；② 章名跨年必须带年份（继承 SFI）；③ 「为什么这样分章」须解释「按拍摄时间排序，含跨年」 |
| **D-SFP-09** | **状态三层模型** | L1 分享图：`分享图需更新` / `分享图已就绪`（仅其一优先）；L2 算法：`可重排`（**废除「可更新」**用户面字面）；同一封面最多 **1** 枚主徽标；L2 为次级样式。Tooltip 冻结：**「版式算法有更新，可点重新排版」**；不新增第三 CTA |
| **D-SFP-10** | **浮层互斥** | `openChapterPanel` ⇒ close export popover；`openExportSettings` ⇒ close chapter panel；统一 overlay z 阶梯 |
| **D-SFP-11** | **小红书文案包入口** | 在「导出设置 · 小红书」确定后 **或** 成功面提供「复制文案包」；不依赖 AI；body 空时 UI 明示「标题与话题可复制 · 正文可自填」 |
| **D-SFP-12** | **存量治理** | 打开/渲染路径对脏 displayTitle、序号腔章名跑 **idempotent migrate**（用户 `titleOrigin=user` / 手改 caption 除外） |

### 3.2 与旧合同的 supersede 点

| 旧合同 | 本主题 |
|--------|--------|
| SFC「展示名体面」 | **补日期串噪声类** + **择优序**（D-SFP-03/04） |
| Chapter Naming「宁可用日期」 | **明确：日期 ≠ 日期·三**（D-SFP-01/02） |
| SFC「分享图需更新」唯一 stale 主词 | **保留为 L1 唯一主词**；另立 L2「可重排」，废除「可更新」（D-SFP-09） |
| share_copy_pack「成功后 dock」 | **入口前移到设置/成功面**（D-SFP-11）；无 AI body 合同不变 |

---

## 4. 分域方案（系统性解法）

### 4.1 章名净化（P-SFP-01）

**根因**：`chapter_titles._same_day_followup_title` 在时段/segment 无法区分时，用 `_CN_ORDINALS` 生成「·三」，并当作读者面最终名。

**解法（规则层，非 UI 补丁 · 评审冻结 OQ-SFP-01）**：

1. **删读者面序号回退**：无 daypart/segment 时返回 `base`（**允许同名日期**，如两章皆「5月27日」；靠章号区分，禁止「（2）」工程后缀）。  
2. **弱桶合并（例外，非默认）**：仅当同日后续桶 `len(photos)≤2` 且无 daypart/segment 时并入前桶；「为什么这样分章」说明「已合并同一天过短片段」。  
3. **Sequence Pass**：生成后扫描，若仍含 `·[二三四五六七八九十]$` 或 `·\d+$` → 强制改写为 `base`（或满足条件时合并）。  
4. **校验闸**：`narrative_validate` / curate 后断言：读者面 title **禁止**匹配序号腔正则。  
5. **存量 / 手改**：`refresh_chapter_titles_on_trip` 对非用户锁章执行同一规则；**`titleOrigin=user` 永不覆盖**。  
6. **Studio**：已有「改名」保留。

**验收样片**：京都 / 昙华林 / 毕业照重导或刷新后，章名不得出现「·三」。

### 4.2 展示名净化（P-SFP-02）

**根因**：`resolve_display_title` 先 `_accept_display(stored displayTitle)`；`24 1 20–25 1 16` 类串未进 noise，压过体面 `meta.title`（如「夏睿彤年度精选2」）。

**解法**：

1. 扩展 `is_folder_title_noise` / 新增 `_looks_like_digit_date_span`：  
   - `\d{1,2}\s+\d{1,2}\s+\d{1,2}` 跨度；  
   - `旅行\s*·\s*\d`；  
   - 缺「月/日」汉字的数字日期链。  
2. 改解析为 **择优**：对 `[displayTitle, title, raw_title]` 各自 `_accept_display`，按 D-SFP-03 质量分选最高者；全拒再用地点·日期回退。  
3. **打开预览静默 migrate（主路径）**：首次打开预览 / pipeline 收尾时，若 stored displayTitle 为 noise 且存在可接受 `title` → 覆写 displayTitle；**不弹教学窗**；封面/书架文案须即时反映，禁止旧缓存闪一下。用户手改题名除外。  
4. **前后端同律**：`title-humanize.js` 同步规则，避免书架与封面分叉。

**验收样片**：`demo-3ee2727aea` 封面按钮文案 ≠ 脏日期串。

### 4.3 图注净化（P-SFP-03）

**根因分层**：

| 现象 | 是否 bug | 处理 |
|------|----------|------|
| chapter.lead 全空 | **否**（frame/sparse 合同） | D-SFP-06；文档与验收勿误杀 |
| caption =「日期 · 题名」 | **是** | 禁止生成与禁止渲染 |
| 「黄昏」「旅行照片」弱标签 | **视密度** | 允许极短场景词，但 **不得整章复读同一词 ≥3 次**（降级为空） |

**解法**：

1. stub / 规则 caption：**删除** `{date} · {place}` 中 place=题名的路径；无合格信号 → 空。  
2. 渲染层 hardening（SFI 精神）：`resolve_caption` / 分享面过滤器增加 `is_title_echo_caption(caption, title)` → 当空。  
3. 长图文字层与卷轴读者面共用过滤，避免「预览空、导出又冒出来」。  
4. **不**为凑满 lead 而造句（NAS / sparse）。

### 4.4 章级时间序（P-SFP-04）

**根因**：date fallback 路径大体升序；**clustering** 路径信任 `segments` 输入顺序；只做了 bucket **内** `apply_segment_order_to_buckets`，没有章 **间**排序。

**解法**：

1. 在 curate 写 chapters 前增加唯一 SSOT：  
   `temporal_key(chapter) = min(reliable takenAt)`；无可靠时间章置尾。  
2. clustering / geo-event / 手工分章结果 **一律**过该排序（用户锁定章序的产品能力若未来存在，另立；V1 无「用户锁章序」则强制时间序）。  
3. 「为什么这样分章」文案：跨年时增加一句「已按拍摄时间排序（含跨年照片）」。  
4. 与 SFI 离群策略衔接：时间离群照片 **不**打乱主行程章序（附录/降权仍归 SFI；本主题保证主链章序单调）。

### 4.5 状态词表（P-SFP-05）

**根因**：三态真实——算法 stale / 长图 stale / session ready——但用户面把算法态写成「可更新」，与 L1「分享图需更新」混淆。

**解法**：

| 状态 | 旧字面 | 新字面（冻结） | 出现位置 |
|------|--------|----------------|----------|
| longshot stale | 分享图需更新 | **分享图需更新**（不变） | 书架优先徽标、预览条 |
| session ready | 分享图已就绪 | **分享图已就绪**（不变） | 与 stale 互斥 |
| algorithm stale | **可更新** | **可重排** | 次级样式；不得压过 L1；悬停/点击：**「版式算法有更新，可点重新排版」** |

规则：

1. 同一卡片 **最多一个**主徽标；优先级：longshot stale > ready > algorithm。  
2. 全局禁词扫描：用户面 **零**「可更新」字面（Help 深链同步）。  
3. 不把三态压成一字——用户要的是**可理解分层**，不是假装只有一种 stale。  
4. L2 不新增第三按钮；CTA 沿用现有「重新排版」（OQ-SFP-04）。  
5. 视觉：L1 偏警示、L2 偏中性提示（线框 F4）。

### 4.6 浮层互斥（P-SFP-06）

**根因**：分章 panel `z-index:245`，导出 popover `400+`；且打开分章未关闭导出层。

**解法**：

1. **行为互斥**（主）：`mountChapterPanel` / `openPanel` 调用 `closeExportPopover()`；打开导出设置调用 `closeChapterPanel()`。  
2. **层级合同**：主浮层统一档位（建议 sheet/popover ≥ 500，chapter panel 同档或更高；toolbar chrome ≤ 200）。  
3. Playwright 回归：打开分章 → 点击 × → panel 关闭（不依赖 force click）。

### 4.7 小红书文案包（P-SFP-07 · 无 AI）

**根因**：`build_share_copy_pack` 已实现；入口仅在「小红书导出成功后的 task dock」；无 AI 时 body 空，用户感知「没有文案」。

**解法（遵守 NAS）**：

1. **入口前移（OQ-SFP-03）**：主路径 = 选中小红书 → 确定 → **设置内一行「复制文案包」** → 再点金色导出；成功面保留第二入口。不进五目标常驻列表。  
2. **无 AI 交付合同**：`title` + `topics` 必给；`body` 允许空；UI 文案冻结：**「标题和话题已备好 · 正文可粘贴后自填」**；禁止「AI 已写好 / 杂志文案已完成」类暗示（NAS）。  
3. `build_share_copy_pack(..., llm_available=False)` 行为保持；**不**为凑 body 调用 LLM 或 stub 假句。  
4. title 必须走 `resolve_display_title`（与 D-SFP-03 同一套）。

---

## 5. 工程任务索引（预排）

| 包 | 任务 | 主文件（示意） | 认领问题 |
|----|------|----------------|----------|
| **BE-SFP-01** | 同日章名去序号腔 + Sequence Pass + 校验 | `chapter_titles.py` · validate | P-SFP-01 |
| **BE-SFP-02** | displayTitle 噪声类 + 择优解析 + migrate | `title_humanize.py` · pipeline | P-SFP-02 |
| **BE-SFP-03** | caption 题名回声禁止（生成+过滤） | `narrate.py` · `asset_caption.py` · share_face_copy | P-SFP-03 |
| **BE-SFP-04** | 章级时间排序 SSOT | `curate.py` · clustering_buckets · 新 util | P-SFP-04 |
| **FE-SFP-05** | stale 三层词表 + 禁「可更新」 | `shelf.js` · bento · help | P-SFP-05 |
| **FE-SFP-06** | 浮层互斥 + z 阶梯 | `chapter-panel.js` · `longshot.js` · css | P-SFP-06 |
| **FE-SFP-07** | 小红书文案包入口前移 + 空 body 说明 | export settings · task-dock · entry | P-SFP-07 |
| **QA-SFP-08** | fixture：同日三章 / 脏日期 displayTitle / 跨年章序 / 回声 caption | `tests/` · schemas/fixtures | 全 |

> 评审后拆到 IMPLEMENTATION；依赖排序：**W0 = BE-01/02/03 + FE-06 → W1 = BE-04 + FE-05 → W2 = FE-07 + QA**。

---

## 6. 错误与降级

| 场景 | 产品行为 |
|------|----------|
| 同日多章无法消歧 | **同名日期**（默认）；弱桶才合并；**永不**出「·三」 |
| title 与 displayTitle 皆 noise | 地点·日期回退；仍 noise →「游记」 |
| 无可靠 takenAt | 无时间章置尾；不阻断导出 |
| 文案包 title 空 | 按钮禁用 +「先给画册起个名字」 |
| 旧册脏 displayTitle / 序号腔章名 | 打开预览 **静默 migrate** + 即时反映；不弹教学；手改字段跳过 |

---

## 7. 埋点（建议）

| 事件 | 用途 |
|------|------|
| `sfp_chapter_title_sequence_pass` | 序号腔被改写次数 |
| `sfp_display_title_migrated` | 脏 displayTitle 被替换 |
| `sfp_caption_echo_suppressed` | 回声图注被抑制 |
| `sfp_chapter_time_sort_applied` | 章序重排是否发生 |
| `sfp_xhs_copy_pack_copied` | 文案包复制（含 body_empty 维） |

---

## 8. 非功能

| 项 | 要求 |
|----|------|
| 性能 | migrate / sequence pass 在打开册路径 < 50ms（百章内） |
| 兼容 | 用户手改章名/题名/图注（origin=user）不得被静默覆盖 |
| NAS | 零 AI 入口回归；本主题 FE 变更不得重新露出 LLM 设置 |
| i18n | 本主题字面中文冻结；英文面另议 |

---

## 9. 里程碑

| 波次 | 内容 | 退出标准 |
|------|------|----------|
| **W0** | 线框 F1–F3 签核 · BE-01/02/03 · **FE-06 浮层互斥** · 校验闸 · 手改保护负例 | G-SFP-01～03 + G-SFP-06；AC-SFP-01/02/03/06 |
| **W1** | BE-04 章序 · FE-05 词表/徽标（含「可重排」tooltip）· 线框 F4 | G-SFP-04～05；AC-SFP-04/05 |
| **W2** | FE-07 小红书入口 · 线框 F5 · QA fixture · 狗粮清单 | G-SFP-07；AC-SFP-07/08 |
| **W3** | 存量书架抽检 + Persona 复测（Agent）· 真人 N≥5 完成门 | 试用 E2–E8（除 AI）关闭或降级为 P2 残留 |

> 估点可控时允许 **W0a**（章名+题名+互斥）/ **W0b**（图注过滤）拆批，但主题 W0 退出仍绑上表标准。喜欢项（五目标 / 人话文件名 / 清晰度像素 / 紧凑）零回退。

---

## 10. 验收 AC 索引（摘要）

| AC | 断言 |
|----|------|
| **AC-SFP-01** | 新建/刷新后读者面章名不匹配 `[·][二三四五六七八九十\d]+$` |
| **AC-SFP-02** | 脏日期 displayTitle fixture 上封面/书架展示体面名或合规回退 |
| **AC-SFP-03** | 回声 caption fixture 读者面与长图文字层均为空 |
| **AC-SFP-04** | 跨年/乱序 segment fixture 输出章序时间单调不减 |
| **AC-SFP-05** | 用户面源码/渲染树无「可更新」作为 stale 主词；算法态为「可重排」 |
| **AC-SFP-06** | e2e：开分章 → 点 × → panel 关闭（导出 caret 不得拦截） |
| **AC-SFP-07** | 小红书：复制文案包在成功前或成功面可达；无 AI 时 topics 非空、UI 不承诺 AI 正文 |
| **AC-SFP-08** | NAS 回归：设置默认面仍无 AI 文案配置入口 |

完整步骤表见后续 ACCEPTANCE 文。

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 同日合并 bucket 改变版式密度 | 仅合并「无 daypart 且无 segment」的弱桶；有时段则保留 |
| 择优 displayTitle 改掉用户「故意用的日期名」 | 仅当判定 noise；提供精修改名 |
| 章序重排让用户「刚改的顺序」丢失 | V1 无锁章序；若精修已支持拖拽序，需 OQ-SFP-02 |
| 「可重排」仍难懂 | 配 tooltip；狗粮问 U4 |

### 11.2 开放问题（OQ）— **已关闭**（2026-07-24 联席）

| ID | 问题 | **决议（一字面）** |
|----|------|---------------------|
| **OQ-SFP-01** | 同日无法消歧：合并 vs 同名？ | **默认允许同名日期**；仅当后续同日桶 `len(photos)≤2` 且无 daypart/segment 时合并。禁止「·二/·三」 |
| **OQ-SFP-02** | 用户锁定章序？ | V1 **不做**；一律时间升序 |
| **OQ-SFP-03** | 文案包是否常驻五目标？ | **否**；仅选中小红书后设置内一行 + 成功面第二入口 |
| **OQ-SFP-04** | 「可重排」是否新 CTA？ | **否**；只改词 + tooltip；CTA 沿用「重新排版」 |

---

## 附录 A · 试用问题映射

| 试用 | 本主题 | 主决策 | 主工程包 |
|------|--------|--------|----------|
| E2 | P-SFP-01 | D-SFP-01/02 | BE-SFP-01 |
| E3 | P-SFP-02 | D-SFP-03/04/12 | BE-SFP-02 |
| E4 | P-SFP-03 | D-SFP-05/06 | BE-SFP-03 |
| E5 | P-SFP-04 | D-SFP-07/08 | BE-SFP-04 |
| E6 | P-SFP-05 | D-SFP-09 | FE-SFP-05 |
| E7 | P-SFP-06 | D-SFP-10 | FE-SFP-06 |
| E8 | P-SFP-07 | D-SFP-11 | FE-SFP-07 |
| E1/E9 | — | 排除（NAS） | — |

## 附录 B · 反例（禁止当作「已修」）

| 反例 | 为何不算修完 |
|------|----------------|
| 只手改京都册 trip.json 去掉「·三」 | 未改生成规则，新册仍复发 |
| 只把「可更新」全局替换成「分享图需更新」 | 抹平三态，制造新误解 |
| 为无 AI 用户自动填散文 body | 违反 NAS / 空优于假句 |
| 只提高 chapter-panel z-index、不关导出层 | 仍可能被其他 sheet 盖住 |

## 附录 C · 用户侧增量（USR-SFP-* · 联席）

| ID | 建议 | 落点 |
|----|------|------|
| **USR-SFP-01** | 同名日期靠章号区分 | §4.1 · 线框 F1 |
| **USR-SFP-02** | 「可重排」必有人话 tooltip | D-SFP-09 · §4.5 |
| **USR-SFP-03** | 小红书标明正文自填 | D-SFP-11 · §4.7 |
| **USR-SFP-04** | 手改章名/题名永不被 migrate 覆盖 | D-SFP-02 · AC 负例 |
| **USR-SFP-05** | 完成前真人 N≥5（U1/U7/U8） | §9 W3 |

## 附录 D · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-24 | 初稿：基于 persona-feedback-trial-2026-07-24；排除 AI 吐槽；七域根因 + D-SFP-01～12 + W0–W3 |
| v0.1.1 | 2026-07-24 | 多席联席 Conditional Go：OQ 冻结 · 同名优先 · 互斥升 W0 · 可重排 COPY · migrate 主路径 · 线框挡门 · USR-SFP-* |
| v0.1.1+wire | 2026-07-24 | 线框落地；**F1–F3 产品认可**（W0 UI 挡门通过；F4/F5 待签） |
