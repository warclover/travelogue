# Travelogue · 封面编辑契约 V1 产品需求文档（PRD）

> **DOC-STATUS: superseded** · 2026-08-11  
> 产品目标纠偏为「2–3 款稳定出片、提升装帧质感」，本文主交付（Style Covenant + Recommend-3）与该目标不对齐。  
> **继任**：[PRD-COVER-CRAFT-FOCUS-V1.md](./PRD-COVER-CRAFT-FOCUS-V1.md)（**CCF**）。  
> 下文仅作历史对标备忘；**勿按本文 Kickoff / 实施**。

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.1.0** |
| **状态** | **Superseded**（勿实施） |
| **DOC-STATUS** | **superseded** → [PRD-COVER-CRAFT-FOCUS-V1.md](./PRD-COVER-CRAFT-FOCUS-V1.md) |
| **主题代号** | 「封面编辑契约」— **CEC**（Cover Editorial Covenant） |
| **触发来源** | 2026-08-11 外部 Skill 对标：[Punk-Skill / punk-cover](https://github.com/adrianpunk/Punk-Skill)（风格原子 + 标题层级 + 图文共生 + 推荐 3 款）；对照本仓 V6 / CAL / CTS / CAD 后收敛为**可落地的封面优化方向** |
| **前置条件** | [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) Cover Style Engine / Registry 可用；[PRD-COVER-CALLIGRAPHY-TITLE-V1.md](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md) 艺术字基线可对照；[PRD-COVER-TYPESETTING-CONTINUITY-V1.md](./PRD-COVER-TYPESETTING-CONTINUITY-V1.md)（CTS）策划已冻结（三层信息 + 字数档合同为本主题消费源） |
| **关联文档** | [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)（CAD · 下游消费者）· [PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md](./PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md) · `travelogue/cover_engine/{types,catalog,fit,studio,joint}.py` · `templates/studio/preview-toolbar/features.js` |
| **验收** | Kickoff 后拆 `ACCEPTANCE-COVER-EDITORIAL-COVENANT-V1.md`；本文 §10 为源 |
| **实施清单** | Kickoff 后拆 `IMPLEMENTATION-COVER-EDITORIAL-COVENANT-V1.md` |
| **更新日期** | 2026-08-11 |

> **定位**
>
> CEC 把 Punk-Skill 里**值得借的编辑方法论**产品化到真照片画册封面，而不是引入「文生图假封面」。  
> 交付三件套：**风格契约（机器可读）** · **标题层级作为选型信号（消费 CTS）** · **Studio「推荐 3 款 + 一句理由」**。  
> 与 CTS 分工：CTS 写「成册排版 Spec + 字数冲突轻提示」；CEC 写「风格 must_preserve / 图文共生 / 按当前封面图推荐版式」。  
> 与 CAD 分工：CEC 是 Mode A「可解释换样式」的前身能力；**不**做一键导演、不写 `artDirection` 全量决策。
>
> **一句话目标**：让每款 Opening 都有一份可执行的编辑契约，并让用户在换版式时看到「为什么推荐这三款」，减少「合法但不对」的失败封面。
>
> **战略原则（拟冻结）**
>
> 1. **真照片默认** — 主视觉像素必须来自 trip 资产；禁止把 AI 整图封面设为默认路径（承接 CAD / CHARTER）。  
> 2. **契约先于新皮肤** — 先补齐现网风格的 must_preserve / 图文关系，再谈第 11 款 Opening。  
> 3. **单风格落地** — 一次只应用一个 Opening；禁止多风格拼贴提示词式混搭。  
> 4. **人话推荐，规则打分** — top3 由 `fit` + 字数档亲和 +（可选）弱语义信号排出；理由一句人话，不做品味黑盒。  
> 5. **引导不强制** — 推荐可一点采纳，但绝不自动改用户已锁定的版式/封面图。  
> 6. **宁缺勿滥** — 不因对标 Punk 的 24 款风格而膨胀 catalog；视觉灵感最多进入 CAD / craft Delta，不进本主题交付。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语 |
| §0.2 | 相邻边界（V6 / CAL / CTS / CAD / Punk） |
| §1 | 背景与问题 |
| §2 | 目标 / 非目标 |
| §3 | 冻结决策 D-CEC-* |
| §4 | 风格契约（Style Covenant）规格 |
| §5 | 推荐 3 + 理由 |
| §6 | 标题层级信号（消费 CTS） |
| §7 | 数据模型与 API |
| §8 | Studio 体验 |
| §9 | 里程碑 |
| §10 | 验收 AC-CEC-* |
| §11 | 风险与 OQ |
| §12 | 变更记录 |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **Style Covenant（风格契约）** | 挂在 Registry 上的机器可读编辑合同：`must_preserve` / `avoid_when` / `image_text_relationship` / `title_tier_affinity` 等 |
| **Recommend-3** | 针对**当前封面图 + 当前标题字数档**，返回至多 3 个可分配 Opening 及一句理由 |
| **A/B/C 标题层** | 消费 CTS D-CTS-02：主标题 / 副信息 / 身份；**不**另起第四套层级名 |
| **字数档** | 消费 CTS D-CTS-01：`compact` / `regular` / `long`；计数合同见 CTS §4.0 |
| **Punk 对标** | 仅方法论来源；本主题**不**安装、不依赖该仓库运行时 |

### 0.2 相邻边界

| 主题 | CEC 拥有 | CEC 不碰 |
|------|----------|----------|
| **V6 Engine** | 扩展 `CoverStyleProfile` / Studio 投影；消费 `fit.py` | 不重写 joint 选图主公式；不删 active 五款 |
| **CTS** | 消费 Typesetting Spec / 字数档；把档位变成推荐权重 | 不重做 Spec 正文、身份线审计、艺术字白名单门禁 |
| **CAL** | 换版式后沿用 stale / resolve 既有路径 | 不改路线 B/C 引擎；不扩艺术字白名单 |
| **CAD** | 为 Mode A「可解释换样式」提供契约与 Recommend-3 | 不实现一键导演、双封面、装饰层、假风景模式 |
| **Punk-Skill** | 借鉴 META/Blueprint 字段语义与推荐 UX | 不接入文生图封面流水线；不引入社媒画幅为主路径 |

> **相对 CTS NG-CTS-08**：CTS 明确不做「joint 选图 × Opening 配型改造」。CEC **只做「给定当前封面图 → 推荐版式」的产品面**（反向：图已定，荐风格），**不**回改创建时 joint 主路径的锁定策略。若未来要做双向配型，另立主题或并入 CAD。

---

## 1. 背景与问题

### 1.1 As-Is

| 能力 | 现状 | 缺口 |
|------|------|------|
| Opening 皮肤 | V6 + Delta：Registry + `prefer`/`avoid` + `text_safe_regions` + `studio_blurb` | 缺 Punk 式 `must_preserve` / 图文共生 / 禁用场景的**显式契约层** |
| 图×风格 | joint 打分 + `CoverJointExplain` | 解释面向引擎；Studio **没有**「推荐这 3 款版式」列表 |
| 标题×风格 | CTS 已冻三层 + 字数档；monument layout 部分落地 | 字数档尚未成为**推荐信号**；hint 工程未齐 |
| 艺术字 | CAL 白名单 4 款 + 调性矩阵 | 与版式推荐脱节（换风格后用户不知是否还适合生成） |
| 市场对标 | Punk-cover 24 风格 + prompt 蓝图 | 若照搬文生图 → 伤害「这是我的旅行」信任 |

### 1.2 问题陈述（P-CEC-*）

| ID | 问题 | 严重度 |
|----|------|--------|
| **P-CEC-01** | 风格适图规则散落在 `prefer`/`avoid` 键与 CSS 注释，设计师/工程师无共用契约表 | 严重 |
| **P-CEC-02** | 用户换版式时只见全量按钮 + 当前 blurb，缺少「就这张封面图」的排序推荐 | 严重 |
| **P-CEC-03** | 标题过长/过短与版式气质冲突时，推荐层不感知字数档（CTS 提示另案且未落地） | 中等 |
| **P-CEC-04** | 失败封面常是「图、版式、标题各自合法，合在一起不对」——缺图文共生语言 | 中等 |
| **P-CEC-05** | 外部 Skill 的「巨字透视 / 整图生成」易被误读为产品方向，缺书面否决边界 | 阻塞（文档） |

### 1.3 成功长什么样

用户打开 Studio「封面版式」时，应读到：

> **当前封面图下，推荐这三款版式（各一句为什么）→ 一点可切换 → 其余版式仍可选但不强推。**

工程师打开 Registry 时，应读到：

> **每款风格有 must_preserve / avoid_when / 图文如何长在画面里 / 字数档亲和。**

---

## 2. 目标与非目标

### 2.1 目标（In Scope）

| ID | 目标 |
|----|------|
| **G-CEC-01** | 定义并落地 **Style Covenant** 字段集，写入 `CoverStyleProfile`（或并列契约对象），覆盖全部 **assignable** Opening |
| **G-CEC-02** | 产出 **Recommend-3** API / Studio 投影：`[{styleId, reason, score, signals}]`，理由 ≤28 字人话 |
| **G-CEC-03** | 推荐打分消费：现网 `net_style_fit` + CTS 字数档亲和 +（可选 P2）弱 mood 信号 |
| **G-CEC-04** | Studio「封面版式」面板展示推荐条；一点采纳走现有 copy-patch；**不**自动改锁定封面 |
| **G-CEC-05** | 与 CTS Spec 对齐：契约中的层级/字数档命名 **只引用** D-CTS-01/02，禁止双源 |
| **G-CEC-06** | 书面冻结对 Punk 的采纳/否决清单（附录 A），避免后续评审反复争论文生图默认路径 |

### 2.2 非目标（Out of Scope · V1）

| ID | 非目标 | 理由 |
|----|--------|------|
| **NG-CEC-01** | AI 整图生成替换用户封面照片 | 信任；CAD Mode D 禁止默认 |
| **NG-CEC-02** | 新增第 11+ 款 Opening CSS 皮肤 | 契约先于扩 catalog；灵感进 CAD/Delta |
| **NG-CEC-03** | 路线 C 升默认 / 开放式 prompt | CAL OQ-CAL-06；CTS NG-CTS-01 |
| **NG-CEC-04** | 重写 joint 创建锁定主路径 | 遵守 CTS NG-CTS-08 边界；本主题只做「图已定→荐风格」 |
| **NG-CEC-05** | 实现 CAD 一键导演 / `artDirection` 全量 | 下游主题；CEC 只供可解释积木 |
| **NG-CEC-06** | 可读性 /「哪款字体更好」算法门禁 | D-CAL-24 已关闭 |
| **NG-CEC-07** | punk-avatar / 宠物头像能力 | 与画册封面无关 |
| **NG-CEC-08** | 以小红书 3:4 / 公号 2.35:1 为封面主画幅 | 本产品主战场仍是 Web/导出成册 |

---

## 3. 冻结决策（D-CEC-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CEC-01** | **契约挂 Registry，不挂 trip** | Style Covenant 是风格台账属性；trip 只存用户选择的 `coverOpeningStyle` 与推荐解释快照（可选） |
| **D-CEC-02** | **Recommend-3 默认开（只读）** | 面板始终可算推荐；**采纳**才写回。用户锁定版式时推荐仍展示，但不自动覆盖 |
| **D-CEC-03** | **理由模板化** | 理由由信号拼装（适图 / 字数档 / 禁区），禁止运行时 LLM 自由生成理由（V1） |
| **D-CEC-04** | **单风格** | 推荐列表每项是完整 Opening id；禁止「A 的字 + B 的框」组合推荐 |
| **D-CEC-05** | **字数档同源 CTS** | `titleLengthTier` 计算必须遵守 CTS §4.0；前端禁止私算 |
| **D-CEC-06** | **与 titleArt 的关系** | 采纳推荐换风格后：沿用现网 stale 标记；若新风格不在艺术字白名单，面板一句说明「装帧标题将回落系统字」，不阻断切换 |
| **D-CEC-07** | **P0 覆盖 assignable 全集** | 凡 `list_assignable_styles()` 返回的风格，契约字段必须齐全（可先填保守默认，禁止空契约上线推荐） |
| **D-CEC-08** | **弱语义信号默认关** | mood / metaphor 仅 P2 flag；开启后也只作平局微扰，不得压过 fit 与字数档 |

---

## 4. 风格契约（Style Covenant）规格

### 4.1 设计意图（对标 Punk META，落地到本仓）

Punk `META.md` 的有用部分是结构化锚点，不是 diffusion 文案。CEC 映射如下：

| Punk 概念 | CEC 字段 | 用途 |
|-----------|----------|------|
| `style_anchors` | `anchors`（短句列表，≤5） | 设计师可读的气质锚；可投影到 Studio 长说明 |
| `must_preserve` | `must_preserve` | 不可破坏的画面/排版事实（如「主体须在上半」「断带不切脸」） |
| `avoid_when_applying_to_cover` | `avoid_when` | 何时不该推荐该风格 |
| `cover_shape_adaptation` | `image_text_relationship` | 标题如何「长在」版式里（非贴纸感） |
| Use For / Avoid prose | `title_tier_affinity` + 现有 `studio_blurb` | 字数档亲和 + 人话 |

现有 `prefer` / `avoid` / `text_safe_regions` **保留**，作为适图打分与压字安全的执行层；Covenant 是其**产品语义上层**，禁止长期与执行层矛盾（冲突时先改契约或先改 fit 键，并留变更记录）。

### 4.2 字段合同（拟扩展 `CoverStyleProfile`）

```text
CoverStyleProfile:
  prefer: dict                    # 现网 · 执行层
  avoid: dict                     # 现网 · 执行层
  text_safe_regions: list[rect]   # 现网 · 压字安全
  title_max_lines: int            # 现网

  # --- CEC 新增 ---
  anchors: list[str]              # ≤5；气质锚，中文短句
  must_preserve: list[str]        # ≤6；不可破事实
  avoid_when: list[str]           # ≤6；不宜推荐条件（人话，可映射信号）
  image_text_relationship: str    # 1–2 句；标题如何存在于画面
  title_tier_affinity:            # compact|regular|long → ideal|ok|caution
    compact: ideal|ok|caution
    regular: ideal|ok|caution
    long: ideal|ok|caution
```

> **初值来源**：`title_tier_affinity` 默认对齐 CTS §4.3 初稿表；`must_preserve` / `image_text_relationship` 由设计+工程对照真实 CSS 与 `studio_blurb` 填写；Kickoff 时产出 `docs/acceptance-records/cover-editorial-covenant-catalog-*.md` 作为填表底稿。

### 4.3 填写示例（非最终常量）

| style id | image_text_relationship（例） | must_preserve（例） | long 档 |
|----------|-------------------------------|---------------------|---------|
| `veil-footer` | 主字坐在下半雾罩里，像电影字幕开场，不是漂浮贴纸 | 主体偏上；下半可暗 | ok（冲击力下降） |
| `band-cut` | 标题嵌在断带纸签语言里，沿切线呼吸 | 切线附近无人脸；天际线可读 | ok |
| `type-monument` | 标题即画面结构（镂空巨字），摄影从字内透出 | 书名宜短；留白够透图 | caution |
| `horizon-split` | 上图下纸，长标题落在纸面栏 | 天际线可承分割 | ideal |
| `contact-stamp` | 标题贴近档案卡/日戳秩序 | 右下不与身份线/工具条互撞 | caution |

### 4.4 视觉灵感（附录级 · 不进 P0 交付）

以下 Punk 风格**仅作 CAD / craft 参考**，本主题不实现新皮肤：

| Punk Style ID | 可借鉴点 | 本仓态度 |
|---------------|----------|----------|
| `avant-retro-architecture-poster` | 单地标、色块、负空间放字 | CAD / 地标游概念 |
| `minimal-public-space-photography` | 空间秩序、极简编辑摄影感 | 最贴近真照片；可丰富 anchors 措辞 |
| `french-minimal-ink-poster` | 克制墨线 | 仅 Route C / 装饰层灵感 |
| `giant-perspective-chinese-title` | 标题即空间 | **默认不采纳**；与「点睛非主视觉」冲突，最多高级实验 |

---

## 5. 推荐 3 + 理由

### 5.1 输入

| 输入 | 来源 |
|------|------|
| 当前封面资产特征 | 现网 cover score / focal / 已用于 `fit.py` 的特征 |
| 可分配风格列表 | `list_assignable_styles()` |
| `titleLengthTier` | CTS §4.0 合同（BE 计算或下发） |
| 用户锁定态 | Bookends / 版式是否 lock（若 lock 风格：仍展示推荐，采纳需显式确认或禁用一键） |
| flag `cec_mood_signal` | 默认关；开时可读 trip 叙事摘要 mood（P2） |

### 5.2 打分（V1 规则）

```text
score(style) =
  w_fit   * normalize(net_style_fit(style, asset))
+ w_tier  * tier_affinity_score(style, titleLengthTier)   # ideal=1, ok=0.55, caution=0.15
+ w_mood  * mood_bonus(style)                             # 仅 flag 开；|bonus| ≤ 0.05
- penalty * hard_avoid_hit(style, asset)                  # 触碰 must_preserve/执行层硬伤
```

| 权重（初值） | 值 | 说明 |
|--------------|-----|------|
| `w_fit` | 0.70 | 主信号；复用 V6 fit |
| `w_tier` | 0.30 | 字数档；无标题时该分量置 0 并重归一 |
| `w_mood` | 0.00（P2 开后 ≤0.10 且从 fit 让出） | 微扰 |

**硬过滤**：`avoid` 执行层触发「不可用」或契约 `avoid_when` 映射的硬信号 → 不进 top3（可进「其他版式」区但不标推荐）。

### 5.3 理由拼装（D-CEC-03）

优先级取前 1–2 个信号，拼一句 ≤28 字（硬顶 36）：

| 信号 | 文案模板（例） |
|------|----------------|
| fit 高 + ideal 档 | 「天际线清楚，断带版式更合适。」 |
| caution 档 | 「书名偏长，镂空巨字易挤，可先试地平线。」 |
| hard avoid 未进榜（不展示在推荐理由） | — |
| 艺术字白名单外 | 切换确认时追加：「装帧标题将用系统字。」 |

禁止出现：分数、logit、OCR、模型名、英文 id（UI 用 `studio_label`）。

### 5.4 输出形状

```json
{
  "titleLengthTier": "regular",
  "recommendations": [
    {
      "styleId": "band-cut",
      "score": 0.82,
      "reason": "天际线清楚，断带版式更合适。",
      "signals": ["fit", "tier_ideal"],
      "titleArtEligible": true
    }
  ],
  "scoringVersion": "cec-recommend-v1"
}
```

---

## 6. 标题层级信号（消费 CTS）

| CTS 资产 | CEC 用法 |
|----------|----------|
| D-CTS-02 三层 | 契约文案与 Studio 解释只使用「主标题 / 副信息 / 身份」语言 |
| D-CTS-01 字数档 | Recommend-3 的 `w_tier`；与 CTS §5 轻提示**可并存**：CTS 管「当前风格冲突 hint」，CEC 管「该换哪三款」 |
| D-CTS-03 引导不强制 | 推荐采纳 = 用户动作；禁止静默改风格 |
| D-CTS-08 艺术字 ≤8 | 理由不得暗示贴纸会排完整 long 标题 |

**本主题不交付**：CTS Typesetting Spec 正文、身份线一本感审计、白名单扩展门禁（仍归 CTS）。

---

## 7. 数据模型与 API

### 7.1 代码挂点

| 模块 | 变更 |
|------|------|
| `cover_engine/types.py` | 扩展 `CoverStyleProfile` 契约字段 |
| `cover_engine/catalog.py` | 为 10 款填齐契约初值 |
| `cover_engine/fit.py` 或新 `recommend.py` | Recommend-3 纯函数 |
| `cover_engine/studio.py` | `studio_style_options` 可附带 `covenantSummary`；新增 `studio_style_recommendations(...)` |
| `web/studio_entry.py` | 下发 `coverStyleRecommendations`（或按需 endpoint） |
| `features.js` `mountCoverStyleControls` | 推荐条 UI + 一点采纳 |

### 7.2 trip 字段

| 字段 | V1 |
|------|-----|
| `meta.coverOpeningStyle` | 不变；采纳推荐时写此字段 |
| `meta.coverStyleRecommendExplain`（可选） | 最近一次展示/采纳的 top3 快照 + `scoringVersion`；供遥测与回放；**可不阻断渲染** |

### 7.3 埋点

| 事件 | 时机 | meta |
|------|------|------|
| `cover_style_recommend_shown` | 推荐条渲染 | `tripId` · `topStyleIds` · `titleLengthTier` · `scoringVersion` |
| `cover_style_recommend_accepted` | 用户点击采纳某一推荐 | 同上 + `acceptedStyleId` · `fromStyleId` |
| `cover_style_recommend_dismissed` | 用户收起推荐条（若有） | `tripId` · `scoringVersion` |

须进前后端白名单，模式同 D-CAL-27。

---

## 8. Studio 体验

### 8.1 面板结构（在现有「封面版式」上增量）

1. **推荐区（新）**：最多 3 张卡片/行——`studio_label` + 一句 `reason` +「使用」按钮。  
2. **全部版式（现网）**：按钮组 + 当前 `studio_blurb` + fit hint。  
3. **冲突提示（CTS §5，若已落地）**：与推荐区并存；推荐区回答「换谁」，hint 回答「当前为何别扭」。

### 8.2 交互铁律

- 推荐区默认展开；无封面图 / 特征不足时展示降级文案：「先选定封面照片后再推荐版式。」  
- 「使用」= 一次 click 切换版式（走现有 patch）；若风格 lock，先解锁确认（文案产品定）。  
- 保留「保留当前封面图」现网语义：换版式默认不强制重选图（与现网一致）。  
- 无障碍：推荐项须键盘可达；理由进 `aria-describedby`。

### 8.3 视觉克制

- 推荐区不是营销 banner；无徽章簇、无分数条、无「AI 精选」炫耀文案。  
- 可用极轻「推荐」字样；颜色走现有 Studio token。

---

## 9. 里程碑

| 波次 | 交付 | 出门标准 |
|------|------|----------|
| **W0** | 本文评审；附录 A 拍板；契约填表底稿 | 产品/设计/工程 Conditional Go |
| **W1** | Profile 字段 + catalog 填齐 + 单测；Recommend-3 纯函数 | AC-CEC-01～04 |
| **W2** | Studio 推荐条 + patch 采纳 + 埋点 | AC-CEC-05～08 |
| **W3** | 与 CTS hint 联调（若 CTS W2 已合）；dogfood N≥5 trip | AC-CEC-09；书面解读 |
| **P2（可选）** | mood 微扰 flag；契约驱动 CAD Mode A 解释条复用 | 另评估 |

---

## 10. 验收标准（AC-CEC-*）

| ID | 验收项 |
|----|--------|
| **AC-CEC-01** | `list_assignable_styles()` 中每一款均具备完整契约字段；单元测试断言非空与 enum 合法 |
| **AC-CEC-02** | `title_tier_affinity` 与 CTS §4.3 初稿无命名冲突；long/compact 映射可单测 |
| **AC-CEC-03** | 同一 fixture 资产上 Recommend-3 稳定（同输入同输出）；`scoringVersion` 固定 |
| **AC-CEC-04** | 触碰执行层 hard avoid 的风格不得出现在 top3 |
| **AC-CEC-05** | Studio 在有封面图时展示 ≤3 条推荐；理由长度 ≤36 字；无原始 style id 裸露 |
| **AC-CEC-06** | 点击「使用」后 `meta.coverOpeningStyle` 更新；预览 DOM `data-cover-opening` 一致 |
| **AC-CEC-07** | 版式锁定时不静默覆盖；行为符合 D-CEC-02 |
| **AC-CEC-08** | 埋点 `shown` / `accepted` 可在 dogfood 环境检索到 |
| **AC-CEC-09** | 与 CAL：切到非白名单风格后，title-art 区块提示回落系统字，且不 500 |
| **AC-CEC-10** | **否决回归**：默认路径无文生图整图封面入口（文档+产品面抽查） |

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 契约与 `prefer`/`avoid` 双源漂移 | D-CEC 变更记录；AC 抽检；CTS D-CTS-06 同精神 |
| 推荐与用户审美不合 | 引导不强制；保留全量版式；埋点看采纳率 |
| 与 CTS 提示文案重复吵闹 | 联调时合并视觉层级：推荐在上、hint 一行 |
| 被理解为「要上 Punk 生图」 | 附录 A + AC-CEC-10 |

### 11.2 开放问题（OQ-CEC-*）

| ID | 问题 | 默认倾向 |
|----|------|----------|
| **OQ-CEC-01** | Recommend-3 用入口下发还是独立 GET？ | 入口下发快照 + 换封面图后刷新 endpoint |
| **OQ-CEC-02** | retired 风格是否可出现在「全部」但不进推荐？ | 是：推荐仅 assignable/active |
| **OQ-CEC-03** | 无标题时 `w_tier` 归零是否足够？ | 是；不阻塞推荐 |
| **OQ-CEC-04** | 是否在分享面暴露推荐解释？ | V1 **否**；仅 Studio |

---

## 12. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-08-11 | 初稿：对标 Punk-Skill 可借鉴能力，收敛为 Style Covenant + Recommend-3 + 消费 CTS 字数档；明确否决文生图默认封面 |

---

## 附录 A · Punk-Skill 采纳 / 否决清单（G-CEC-06）

| 能力 | 态度 | 落入 |
|------|------|------|
| META `must_preserve` / anchors / avoid | **采纳** | §4 Style Covenant |
| 封面 Blueprint 的标题 A/B/C 层 | **采纳语义** | 消费 CTS 三层，不另起名 |
| 文章摘要 → mood/metaphor | **延后** | P2 弱信号（D-CEC-08） |
| 推荐 3 款 + 一句理由 | **采纳** | §5 Recommend-3 |
| 单风格融合、禁止拼贴多风格 | **采纳** | D-CEC-04 |
| prompt-only / 产物落盘纪律 | **部分采纳** | 推荐快照 + scoringVersion；不做 diffusion prompt 文件 |
| 24 款社媒视觉皮肤 | **否决扩库** | NG-CEC-02；灵感仅附录 |
| 文生图整图封面流水线 | **否决默认** | NG-CEC-01 / AC-CEC-10 |
| 平台画幅（小红书/公号/X）主路径 | **否决** | NG-CEC-08 |
| punk-avatar | **否决** | NG-CEC-07 |
| 巨型透视中文标题作默认主视觉 | **否决默认** | 与 CAL「点睛」冲突；§4.4 |

---

## 附录 B · 与现网类型的关系（实施备忘）

现网（摘录）：

```12:16:travelogue/cover_engine/types.py
class CoverStyleProfile:
    prefer: dict[str, Any] = field(default_factory=dict)
    avoid: dict[str, Any] = field(default_factory=dict)
    text_safe_regions: list[dict[str, float]] = field(default_factory=list)
    title_max_lines: int = 2
```

CEC W1 在此结构上**增量字段**；`studio_blurb` 仍留在 `CoverStyleRecord`。Recommend-3 **不要**塞进未落地的 CAD `artDirection`，避免 CAL 已证明的倒挂依赖。
