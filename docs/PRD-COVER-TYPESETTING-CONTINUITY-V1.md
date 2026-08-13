# Travelogue · 封面成册感 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **策划已冻结 · 可 Kickoff W1（Spec + 身份线）；扩白名单仍受 W0/W3 门禁** |
| **DOC-STATUS** | **planning-frozen**（[七席纪要 2026-08-09](./acceptance-records/cts-cover-typesetting-continuity-v1-review-2026-08-09.md) · Conditional Go · BLK-CTS-01～05 已关） |
| **主题代号** | 「成册」— **CTS**（Cover Typesetting Continuity） |
| **触发来源** | 2026-08-09 封面系统复盘：`feat/cover-calligraphy-title-v1`（CAL）已收口艺术字默认开、字体调性矩阵、装帧身份线、埋点与质量审计；下一阶段从「有装帧声音」转向「像同一位编辑排的一页」 |
| **前置条件** | 见下方 **前置条件（双轨）**；[PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) 十款 Opening 可分配 |
| **关联文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md) · [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) · [PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md](./PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md) · [PRD-SHARE-FACE-INTEGRITY-V1.md](./PRD-SHARE-FACE-INTEGRITY-V1.md)（D-SFI-13 署名三态）· [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)（CAD · 姊妹，非硬依赖） |
| **验收** | Kickoff 时拆 `ACCEPTANCE-COVER-TYPESETTING-CONTINUITY-V1.md`；本文 §10 为源 |
| **实施清单** | Kickoff 时拆 `IMPLEMENTATION-COVER-TYPESETTING-CONTINUITY-V1.md` |
| **更新日期** | 2026-08-09 |

**前置条件（双轨 · BLK-CTS-01）**

| 轨 | 适用 | 要求 |
|----|------|------|
| **（A）已合入** | G-CTS-05 埋点解读、W3 扩白名单 go/no-go、正式环境 dogfood | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（CAL · v0.6.27+）已合入 `master`（或等价主干）；D-CAL-27 在该环境可读 jsonl |
| **（B）分支等价** | W1 Spec 文档起草、身份线审计、本地/预发手测 | CAL 能力以 `feat/cover-calligraphy-title-v1`（或其后继）dogfood / 预发为准；**不得**用空数据把 W3 / D-CTS-04 判绿 |

> 禁止再写含糊单行「已合入或等价可用」。W1 允许在（B）下开工；G-CTS-03 / G-CTS-05 必须走（A）。

> **定位**
>
> CAL（「点睛」）解决的是封面**标题字本身的艺术感**；CTS（「成册」）解决的是封面**作为一页编辑结果的连续性与可预期品质**——风格、标题长度与署名是否像同一位设计师排的，而不是功能开关碰巧叠在一起。
>
> **一句话目标**：把封面从「功能可用」推进到「翻开即信任」——用一份可执行的排版契约 + 标题长度作为一等设计变量 + 风格引导，减少失败封面，而不是再开一条生成路线。
>
> **战略原则（本 PRD 冻结）**
>
> 1. **契约先于特效** — 先写清三层信息层级与字数档，再谈新字体/新风格/新白名单。
> 2. **宁缺勿滥** — 艺术字白名单不追求 10 款全开；精品路径可以苛刻，默认路径必须稳。
> 3. **人话引导，不做算法品味** — 风格与标题气质冲突时给轻提示；不重做「哪款字体更好认」类自动门禁（D-CAL-24 已关闭）。
> 4. **路线 C 维持高级项** — 不因本主题升级为默认主路径（承接 OQ-CAL-06）。
> 5. **印章/图形印记不做** — 三层里的「印记」仅指弱身份文字层，不复活印章图形（产品已否决）。
> 6. **合入后听数据再扩** — W0 先合 CAL 并读 D-CAL-27 漏斗；没有真实转化/失败率，不开放下一款艺术字风格。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §1 | 背景：CAL 已交付什么、还缺什么 |
| §2 | 目标 / 非目标 |
| §3 | 冻结决策 D-CTS-* |
| §4 | Cover Typesetting Spec（字数合同 + 三层 + 字数档） |
| §5 | 风格 × 标题长度引导（Studio） |
| §6 | 艺术字白名单扩展政策 |
| §7 | 装帧身份线「一本感」打磨 |
| §8 | 合入门禁与埋点解读 |
| §9 | 里程碑 |
| §10 | 验收标准 AC-CTS-* |
| §11 | 开放问题 OQ-CTS-* |
| §12 | 变更记录 |

---

## 1. 背景与问题

### 1.1 CAL 已交付（基线，不在本 PRD 重做）

| 能力 | 状态 | 文档锚点 |
|------|------|----------|
| 路线 B 字库合成 + 4 款艺术字白名单 | ✅ 默认开（用户点击生成） | CAL D-CAL-05 / AC-CAL-BLIND |
| Typeface Voice Matrix | ✅ | CAL D-CAL-25 |
| 装帧身份线前封回声（10 款） | ✅ | CAL D-CAL-26 |
| 漏斗埋点 impression / resolve | ✅ | CAL D-CAL-27 |
| 换封面指纹 / CAS 外计算 | ✅ | CAL D-CAL-28 |
| 路线 C | ✅ 高级项，默认关 | CAL OQ-CAL-06 |

> 上表描述的是 **CAL 分支能力基线**。是否已在 `master` 生效，见文首前置条件双轨（A）/（B）。

### 1.2 仍存在的成册缺口（本主题交付范围）

1. **排版规则散落**：主标题 / hook / 身份线的强弱关系写在各风格 CSS、引擎注释与验收记录里，没有一张「设计师与工程师共用」的契约表。
2. **标题长度是二等公民**：`veil-footer` 长标题、`type-monument` 换行重叠已靠补丁止血，但「字数档 → 各风格降级策略」尚未产品化；用户仍可能选到与标题气质冲突的版式。
3. **身份线「一本感」未验收**：前封 / 封底 / 长图脚三处已接线，但跨风格字重、字距、撞工具条等未做成册级核对清单。
4. **扩白名单的诱惑**：容易为覆盖率把剩余风格硬接艺术字——与「克制胜过堆砌」冲突。

### 1.2.1 背景观察（非本主题交付 · BLK-CTS-02）

joint 选图、Opening 风格、艺术字生成今天仍是三件独立决策；失败封面有时是「三选都合法、合在一起不对」。这是封面系统的长期观察，**不**构成本主题目标——本主题不做 joint 选图 × Opening 配型改造（见 **NG-CTS-08**）。若未来要做，另立主题。

### 1.3 成功长什么样（产品叙事）

用户打开预览时，封面应读作：

> **一张画面 + 一层主字 + 一句弱副信息 + 一行可辨认的署名**

而不是：功能面板、统计条、多重印章、或「生成了但挡脸/字太小/风格与书名打架」的拼贴。

本主题成功 ≠ 必须开放下一款艺术字；W3 允许书面 no-go。

---

## 2. 目标 / 非目标

### 2.1 目标（本主题必须交付）

| ID | 目标 |
|----|------|
| **G-CTS-01** | 产出并冻结 **Cover Typesetting Spec**（三层信息 + 标题字数档 + 每风格禁区摘要），作为后续 CSS / 引擎 / Studio 文案的唯一品味源 |
| **G-CTS-02** | Studio 在「标题长度与当前风格气质冲突」时给出**一句人话轻提示**（可换风格或缩短标题），不阻断操作 |
| **G-CTS-03** | 定义艺术字白名单**扩展准入门槛**（埋点门槛 + 字数档策略就绪 + 真实截图核对），并给出下一款开放优先级（默认建议：`horizon-split`） |
| **G-CTS-04** | 装帧身份线做一次跨表面「一本感」核对清单并修掉明确撞位/字级漂移 |
| **G-CTS-05** | 在前置条件 **（A）** 环境下，用 D-CAL-27 事件读一轮 dogfood / 早期流量，形成书面解读（转化、回退、disabled）——作为 G-CTS-03 的前置数据 |

### 2.2 非目标（本主题明确不做）

| ID | 非目标 | 理由 |
|----|--------|------|
| **NG-CTS-01** | 路线 C 升为默认主路径 | OQ-CAL-06；非确定性伤信任 |
| **NG-CTS-02** | 印章 / 图形印记层 | 产品已否决审美风险 |
| **NG-CTS-03** | 自动「可读性 / 哪款字体更好」算法门禁 | D-CAL-24 已关闭 |
| **NG-CTS-04** | 10 款 Opening 全部接艺术字 | 宁缺勿滥；竖排/镂空另案 |
| **NG-CTS-05** | 新开一款封面视觉风格（第 11 款） | 本主题是契约与引导，不是扩 catalog |
| **NG-CTS-06** | 章标题 / 长图分段艺术字 | 承接 OQ-CAL-02（仅 Opening） |
| **NG-CTS-07** | 第一屏营销叠层（徽章、统计、促销） | 破坏封面信任叙事 |
| **NG-CTS-08** | joint 选图 × Opening 风格配型改造 | BLK-CTS-02；背景观察另案，本主题只做标题×风格契约与引导 |

---

## 3. 冻结决策（D-CTS-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CTS-01** | **标题长度分三档** | `compact` ≤4 字 · `regular` 5–7 字 · `long` ≥8 字。计数合同见 **§4.0**；与 monument 命名映射见 **§4.0.1**。全主题 Spec / 引导 / 白名单扩展均引用此三档，禁止各模块私自另起阈值 |
| **D-CTS-02** | **三层信息层级** | ①主标题（唯一英雄）②副信息（hook / 日期地点等，永远弱一档）③身份（`worksBrandLine`，可辨认但不抢戏）。「印记」= ③，**不是**印章图形 |
| **D-CTS-03** | **引导不强制** | 风格×字数冲突时只提示、不自动改风格、不禁止生成；尊重用户终选（与「零强迫」产品气质一致） |
| **D-CTS-04** | **艺术字扩展须过三道门** | ①D-CAL-27：该风格相关 resolve 失败率可接受（见 §8.3；n&lt;20 改人工）②该风格字数档策略已写入 Spec 并有截图③产品负责人书面点名开放——缺一不可。数据须来自前置条件 **（A）** |
| **D-CTS-05** | **下一款艺术字默认候选 = `horizon-split`** | 天生「上图下纸、承长标题」；`scroll-head`（竖排）与 `type-monument`（镂空巨字）列为**精品路径**，本主题不默认开放艺术字 |
| **D-CTS-06** | **Spec 是品味真相源** | 与 CSS / `whitelist.py` / `journal.css` 冲突时：先改实现或先改 Spec 并留变更记录，禁止长期双源漂移（呼应 CAL 白名单 CSS 未同步教训）。可测性见 **AC-CTS-09** |
| **D-CTS-07** | **W0 合入 CAL 不绑定本主题 W1 Kickoff** | CAL 合入可独立进行。**W1 Spec / 身份线允许在前置条件（B）下开工**；**G-CTS-03 扩展白名单不得早于 G-CTS-05**，且 G-CTS-05 必须在（A）下完成 |
| **D-CTS-08** | **艺术字主串仍 ≤8** | 继承 CAL `MAX_MAIN_CHARS=8`。long 档（≥8）可触发风格 hint，但 **不得**暗示贴纸会排完整长标题；贴纸仍截断至 8 字并记 `truncated` |

---

## 4. Cover Typesetting Spec（核心交付）

### 4.0 字数档计数合同（BLK-CTS-03）

| 项 | 冻结一字面 |
|----|------------|
| **输入串** | `resolve_display_title(meta)` 的返回值（与封面展示主串同源） |
| **规范化** | Unicode **NFC** 后计长 |
| **空白** | 去**首尾**空白；**不去**中间空白与标点（除非某风格 Spec 行另表例外） |
| **单位** | Unicode **码点**长度（非 UTF-16 代码单元、非「视觉字宽」） |
| **禁止** | 前端用 raw `meta.title` / 未清洗 `displayTitle` 私算 tier |
| **实现** | 共享模块或由 BE 下发 `titleLengthTier`；禁止在 `features.js` 内复制第二套规则 |

金样与验收见 **AC-CTS-08**。

### 4.0.1 三档 ↔ monument 命名映射（BLK-CTS-04 · 关闭 OQ-CTS-01）

| D-CTS-01 档 | 字数 | `resolve_monument_title_layout` |
|-------------|------|----------------------------------|
| `compact` | ≤4 | `compact` |
| `regular` | 5–7 | `wrapped` |
| `long` | ≥8 | `wrapped-long` |

全局只保留上述三档；`type-monument` 更严的气质用 Spec 格内「首选 / 谨慎 / 提示」表达，**不**另起第四档阈值。

### 4.1 文档形态

Kickoff 后落地独立短文（建议路径）：

`docs/acceptance-records/cover-typesetting-spec-v1-2026-MM-DD.md`

或 `docs/wireframes/` 旁的可打印一页表。本 PRD §4 给**必须覆盖的字段**；数值以 Spec 定稿为准，此处给初稿默认值供实施。

### 4.2 三层契约（全风格共用）

| 层 | DOM / 数据 | 注意力预算 | 硬约束 |
|----|------------|------------|--------|
| **主标题** | `.cover-opening__title` 或 title-art 贴纸 | 唯一英雄 | 同时只允许一层「抢注意力」的主字（艺术字开时原生标题 sr-only / 弱化，沿用 CAL §7） |
| **副信息** | hook / place / archive / subtitle | 弱一档 | 不得压过主字对比度与字号；过长截断策略按风格已有规则，Spec 须点名 |
| **身份** | `.cover-opening__brand` 等 `worksBrandLine` | 可辨认 | 10px 量级、opacity ≤0.55 量级（已有基线）；禁止与 Studio 工具条重叠（CAL D-CAL-26 教训） |

### 4.3 标题字数档 × 风格气质（初稿）

| 风格 id | 气质一句话 | compact (≤4) | regular (5–7) | long (≥8) |
|---------|------------|--------------|---------------|-----------|
| `veil-footer` | 电影开场雾底 | 理想 | 可用（艺术字已调宽） | 可用但冲击力下降；提示可缩短 |
| `band-cut` | 断带风景切割 | 理想 | 理想 | 可用；贴纸区偏扁，过长易缩字 |
| `contact-stamp` | 纪实档案 | 理想 | 可用 | 谨慎；右下已挤 |
| `folio-overlap` | 书信骑缝 | 理想 | 可用 | 谨慎；纸栏窄 |
| `type-monument` | 镂空巨字 | **首选** | 可用（wrapped） | 谨慎（wrapped-long）；**提示更适合短书名** |
| `cameo-aperture` | 圆窗焦点 | 理想 | 可用 | 谨慎（竖排区窄） |
| `horizon-split` | 上图下纸 | 可用 | **理想** | **首选长标题** |
| `scroll-head` | 中式竖题 | 理想 | 可用 | 竖排能力未接艺术字前仅原生 |
| `portal-arch` | 拱门取景 | 理想 | 可用 | 谨慎 |
| `diptych-seam` | 双联断字 | 理想 | 可用 | 谨慎 |

> **Spec 定稿时**：每格补「字号策略 / 是否劝退艺术字 / Studio 提示文案 key」三列；上表是初稿，不是最终实现常量名。long 档涉及艺术字时须遵守 **D-CTS-08**。

### 4.4 与已有代码的关系

| 已有能力 | Spec 如何消费 |
|----------|----------------|
| `resolve_monument_title_layout`（compact / wrapped / wrapped-long） | 按 **§4.0.1** 映射到 D-CTS-01；实现可保留旧函数名，对外产品语言用 compact/regular/long |
| `_MAIN_TEXT_MAX_WIDTH_RATIO_BY_STYLE` | Spec 记录「为何该风格更宽/更窄」，避免再变魔法数 |
| `FONT_VOICE_BY_STYLE`（D-CAL-25） | Spec 附「调性一句话」，不改映射除非产品重拍 |
| `_COVER_OPENING_BRAND_STYLES` | 身份层全开已定；Spec 只规范视觉，不缩白名单 |
| `DEFAULT_ENABLED_STYLES` + title-art CSS 选择器 | Spec 定稿须与二者集合核对（**AC-CTS-09**） |

---

## 5. 风格 × 标题长度引导（Studio）

### 5.1 触发点

| 时机 | 行为 |
|------|------|
| 用户修改 `meta.title`（copy-patch）后 | 若当前 `coverOpeningStyle` 对当前字数档为「谨慎 / 提示」→ toast 或面板内一行 hint |
| 用户切换封面版式时 | 若新风格对当前标题字数档不友好 → 同上一行 hint |
| 点击「生成装帧标题」前（可选） | 仅当该风格艺术字白名单内且字数档为「谨慎」时，status 区追加半句提示；**不**拦截请求；若 long 档，可提示贴纸仍最多 8 字（D-CTS-08） |

### 5.2 文案原则

- 一句人话，优先 ≤28 字，硬顶 36 字；不说「算法」「阈值」「OCR」。
- 须说清用户下一步（缩短书名 **或** 换某版式），不能只抱怨。
- 示例：「镂空巨字更适合短书名，也可换「地平线」版式。」
- 禁止恐吓色 / 禁止模态对话框（D-CTS-03）。
- 禁止暗示 long 档艺术字会排完整长标题（D-CTS-08）。

### 5.3 实现边界

- 档位计算必须遵守 **§4.0**；禁止前端私算。
- 提示文案可先硬编码在 `features.js`；若超过 6 条风格×档位组合，再抽到共享常量模块（避免过早抽象）。

### 5.4 埋点（承接 D-CAL-27）

| 事件 | 时机 | 关键 meta | V1 |
|------|------|-----------|-----|
| `cover_title_length_hint_shown` | 提示实际展示 | `tripId` · `coverOpeningStyle` · `titleLengthTier` · `surface`（`title-edit` / `style-change` / `title-art`） | **必做** |
| `cover_title_length_hint_acted` | 用户点击提示中的建议动作 | 同上 + `action` | **不做**（OQ-CTS-02：V1 无一键切风格；避免半实现白名单） |

须进前后端白名单，模式同 D-CAL-27。

---

## 6. 艺术字白名单扩展政策

### 6.1 当前冻结集合（CAL）

艺术字默认白名单：**`veil-footer` / `band-cut` / `contact-stamp` / `folio-overlap`**。本主题**不**自动扩大该集合。

### 6.2 扩展优先级（设计建议，须过 D-CTS-04）

| 优先级 | 风格 | 理由 | 本主题态度 |
|--------|------|------|------------|
| P0 候选 | `horizon-split` | 长标题友好、纸面区天然承托 | 数据过门后优先开放（**独立切片**，见 §6.3） |
| P1 精品 | `type-monument` | 短标题神器；长标题已有降级但仍苛刻 | 仅 compact 档鼓励；艺术字接入另立验收 |
| P2 延后 | `scroll-head` | 竖排与横版画布假设冲突（CAL 已述） | 本主题不做 |
| P2 延后 | `cameo-aperture` / `portal-arch` / `diptych-seam` | 收益/风险比一般 | 听埋点后再议 |

### 6.3 单风格开放检查清单（AC 用）

1. Spec §4.3 该行已定稿（含 long 档策略）  
2. 真实 trip：compact / regular / long 各至少 1 张截图  
3. 换封面后指纹失效行为仍正确（D-CAL-28）  
4. 身份线不撞工具条  
5. D-CAL-27：前置条件（A）下该风格 `outcome=error|network` 占比可接受（见 §8.3）  
6. 产品负责人点名「开」  
7. **（BLK-CTS-05）** 开放 = **placement 预设 + title-art CSS + 指纹回归** 的独立小切片，**不只**改 `DEFAULT_ENABLED_STYLES` / `enabled_styles` 一行

---

## 7. 装帧身份线「一本感」

### 7.1 范围

不新开渲染位；在 D-CAL-26 / D-SFI-13 已有三处上做**一致性核对与小修**：

- 前封 `.cover-opening__brand`
- 封底 `.cover-closing__brand`
- 长图脚 `.longshot-boundary-footer__brand`

### 7.2 核对清单

| 项 | 通过标准 |
|----|----------|
| 默认 `Travelogue` | 三处大写/字距/字号观感一致（允许因底色改颜色，不允许一处像导航一处像正文） |
| 自定义署名 | 三处同步；`--custom` 取消 uppercase 行为一致 |
| `hidden` | 三处皆无 |
| Studio 预览 | 10 款前封身份线均不与 `screenplay-toolbar` 重叠（回归 D-CAL-26 §8.2） |
| 分享面 | 与 draft 同源字段，无分享专用第二套文案 |

### 7.3 交付物

一份带截图的验收记录（建议挂 `docs/acceptance-records/cover-typesetting-continuity-identity-line-audit-*.md`），列出 10 款前封 + 1 款封底 + 1 款长图脚样例即可（不必 10×3 穷举）。

---

## 8. 合入门禁与埋点解读

### 8.1 W0 · CAL 合入（可并行于 CTS 文档工作）

| 项 | 要求 |
|----|------|
| 分支 | `feat/cover-calligraphy-title-v1` → `master`（或等价主干）→ 满足前置条件 **（A）** |
| 质量 | D-CAL-28 审计项已合入；无 P0/P1 未决阻断 |
| 残留杂物 | 不把 `字体/`、`README - 副本.md`、`arttext-miniapp/` 误合入 |

### 8.2 G-CTS-05 · 埋点解读门槛（扩展白名单前置）

须在前置条件 **（A）** 下积累（dogfood 可放宽样本量，但须书面说明；**禁止**用（B）空数据假绿）：

| 指标 | 建议观察窗口 | 解读问题 |
|------|--------------|----------|
| `title_art_impression` → `title_art_resolve` | ≥1 周或 ≥30 次 impression | 入口是否被看见/愿点 |
| `outcome` 分布 | 同上 | `disabled` 是否过高（总闸关 / 非白名单 / 空标题 / 未生成须区分） |
| `routeCRequested` / `fallback` | 若有人开高级项 | C 是否值得推广，还是应更深藏 |
| 分风格 `coverOpeningStyle` | 可选 | 哪款风格最常生成 |

**不设**「必须达到某转化率才能 Kickoff CTS W1」——只设「扩展艺术字白名单前必须有解读备忘」。

### 8.3 失败率阈值（D-CTS-04）

某风格进入扩展候选时，其 `title_art_resolve` 且 `outcome ∈ {error, network}` 的占比建议 **&lt; 5%**；样本量 **&lt; 20** 时改为人工逐条看，**不卡硬阈值**。

---

## 9. 里程碑

| 里程碑 | 内容 | 退出标准 | 前置轨 |
|--------|------|----------|--------|
| **W0** | CAL 合入主干；确认埋点落盘路径 | master 可玩；jsonl 能见到 impression/resolve | →（A） |
| **W1** | Spec 定稿（§4）；身份线一本感核对（§7） | Spec 文档合并；身份线验收记录通过；AC-CTS-01/04/08/09 | 允许（B） |
| **W2** | Studio 字数档轻提示（§5）+ 埋点 `hint_shown` | AC-CTS-02/03；相关单测；**须 W1 Spec 已定稿** | 建议（A），可用（B）手测 |
| **W3** | 埋点解读备忘（G-CTS-05）→ 决策是否开放 `horizon-split` 艺术字 | 书面 go/no-go；若 go，完成 §6.3 清单（含第 7 条切片） | **必须（A）** |

> W3 **允许**结论为「暂不开下一款」——本主题成功 ≠ 必须扩白名单。

---

## 10. 验收标准（AC-CTS-*）

| ID | 标准 | 里程碑 |
|----|------|--------|
| **AC-CTS-01** | Cover Typesetting Spec 已合并；含三层契约 + 10 款字数档表 + 与 CAL/CSS 冲突裁决句（D-CTS-06） | W1 |
| **AC-CTS-02** | 标题或风格变更导致「谨慎」档时，Studio 展示一句 hint；不阻断保存/生成 | W2 |
| **AC-CTS-03** | `cover_title_length_hint_shown` 前后端白名单均登记，本地 jsonl 可落盘 | W2 |
| **AC-CTS-04** | 身份线一本感验收记录通过（§7.2 清单） | W1 |
| **AC-CTS-05** | 存在一份 D-CAL-27 解读备忘（转化 / outcome / 是否扩白名单）；数据来自前置条件（A） | W3 |
| **AC-CTS-06** | 若开放 `horizon-split` 艺术字：§6.3 **七条**全部勾选并有截图 | W3（条件） |
| **AC-CTS-07** | 回归：既有 4 款艺术字白名单 + D-CAL-28 换封面指纹行为不被本主题破坏 | W2/W3 |
| **AC-CTS-08** | 字数档金样：至少 3 组固定标题串 → 期望 `compact` / `regular` / `long`；实现与 §4.0 一致（BLK-CTS-03） | W1 |
| **AC-CTS-09** | Spec 定稿含与 `DEFAULT_ENABLED_STYLES` 及 `journal.css` 中 title-art 选择器集合的一致性核对句；若冲突，按 D-CTS-06 留变更记录（BLK-CTS-05） | W1 |

---

## 11. 开放问题（OQ-CTS-*）

| ID | 问题 | 状态 / 倾向 |
|----|------|-------------|
| **OQ-CTS-01** | 字数档与 monument 4/7 分界是否统一？ | **✅ 已关闭（v0.2.0）**：全局三档 + §4.0.1 映射；格内用首选/谨慎表达更严 |
| **OQ-CTS-02** | hint 是否提供「一键切换到推荐风格」？ | V1 **不做**；不实现 `acted` 事件；W2 后看 `hint_shown` 量再开 |
| **OQ-CTS-03** | `horizon-split` 艺术字开放时，贴纸进 panel 流还是绝对定位？ | 倾向对齐该风格原生标题锚点；开放切片 Kickoff 时对照 `journal.css` 拍板 |
| **OQ-CTS-04** | Spec 是否升格为 `docs/PRD-COVER-TYPESETTING-SPEC-V1.md` 独立母文档？ | 倾向 W1 先挂 acceptance-records；若被 V6/CAD 多方引用再升格 |
| **OQ-CTS-05** | mobile / &lt;1024 回落 `veil-footer` 呈现时，hint 是否仍按原 `coverOpeningStyle` 计算？ | 倾向：按**属性上的风格**提示；**V1 不验**窄屏专属文案（不挡 W2） |

---

## 12. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-08-09 | 初稿：Typesetting Spec、字数档引导、白名单扩展政策、身份线一本感、合入与埋点门禁 |
| — | 2026-08-09 | 七席评审：[cts-cover-typesetting-continuity-v1-review-2026-08-09.md](./acceptance-records/cts-cover-typesetting-continuity-v1-review-2026-08-09.md) · Conditional Go · BLK-CTS-01～05 |
| **v0.2.0** | 2026-08-09 | 回写 BLK-CTS-01～05：前置双轨（A/B）；收窄照片×风格叙事 + NG-CTS-08；§4.0 字数合同 + AC-CTS-08；§4.0.1 三档映射 + D-CTS-08（艺术字 ≤8）关闭 OQ-CTS-01；AC-CTS-09 + §6.3 开放=切片；D-CTS-07 明确 W1 可在（B）开工 |

---

## 附录 A · 与 CAL 决策的继承关系

| CAL | CTS 态度 |
|-----|----------|
| D-CAL-05 默认开艺术字入口 | 继承；本主题不改默认 |
| D-CAL-24 不做可读性自检 | 继承；写入 NG-CTS-03 |
| D-CAL-25 字体调性矩阵 | 继承；Spec 只加人文描述 |
| D-CAL-26 身份线 | 继承并做一本感核对（§7） |
| D-CAL-27 埋点 | 继承并扩展 hint `shown`（§5.4）；`acted` V1 不做 |
| D-CAL-28 换封面指纹 | 继承；扩白名单检查清单强制回归 |
| OQ-CAL-06 路线 C 不升默认 | 继承为 NG-CTS-01 |
| `MAX_MAIN_CHARS=8` | 继承为 D-CTS-08 |

## 附录 B · 建议 Kickoff 顺序（给实施清单用）

1. **并行**：W0 合 CAL →（A）；同时可在（B）下开 W1 Spec + 身份线审计  
2. W1 退出后 → W2 字数档 hint + `hint_shown`  
3. W0/（A）就绪后积累数据 → W3 解读备忘 → go/no-go `horizon-split`（若 go，按 §6.3 七条做独立切片）  

**本主题成功的标志**：六个月后回看封面，失败样例变少、用户更少「生成了但不好看」——而不是艺术字风格数变多。
