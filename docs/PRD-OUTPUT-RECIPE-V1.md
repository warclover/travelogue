# Travelogue · 输出配方引擎 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v1.1.0-OUTPUT-RECIPE** |
| **状态** | Draft · **跨职能有条件通过 · P0 Must-Fix 已回写** · 见 [评审纪要](./acceptance-records/output-recipe-v1-review-2026-07-14.md) |
| **主题代号** | 「Output Recipe V1」— 按精选张数分流默认产出 · 意图选配方 · 可覆盖可扩展 |
| **前置条件** | Longshot 1.x 微信群长图稳定；[ADR-016](./adr/016-longshot-platform-export.md) 分支 A/B（及本主题增补 **分支 D**）可用；[PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) Phase A 可灰度；[PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) 主 CTA / ▾ 高级项合同有效 |
| **关联文档** | [SHARING.md](./SHARING.md) · [CHARTER.md](./CHARTER.md) · [config/platform_profiles.yaml](../config/platform_profiles.yaml) · [PRD-OVERSEAS-SHARE-PACK-V2.md](./PRD-OVERSEAS-SHARE-PACK-V2.md) · [TRAVELOGUE-PROJECT-BUSINESS-ASSESSMENT.md](./TRAVELOGUE-PROJECT-BUSINESS-ASSESSMENT.md) · [ROADMAP-EVIDENCE-DRIVEN-GROWTH-12M.md](./ROADMAP-EVIDENCE-DRIVEN-GROWTH-12M.md) · [评审纪要](./acceptance-records/output-recipe-v1-review-2026-07-14.md) |
| **验收** | [ACCEPTANCE-OUTPUT-RECIPE-V1.md](./ACCEPTANCE-OUTPUT-RECIPE-V1.md) |
| **实施清单** | [IMPLEMENTATION-OUTPUT-RECIPE-V1.md](./IMPLEMENTATION-OUTPUT-RECIPE-V1.md) |
| **更新日期** | 2026-07-17（增补 D-OR-27 · Share-Ready 交叉） |

> **定位**
>
> Travelogue 的价值主张保持不变：**旅行记忆的编辑 / 杂志风成书**，不是全能社交导出器。  
> 本 PRD 只解决「**同一本游记，按相册规模与分享意图，选对默认交付物**」：引入薄的 **Output Recipe（输出配方）** 层，把张数默认、平台惯用规格、用户临时覆盖收敛为一份可解析合同。
>
> **一句话**：价值主张聚焦叙事成书用户；交付配方服务多种发行场景。

> **对外禁语（P0-7 / 增长）**
>
> - 禁止：「支持一切社交」「全能导出」「一键发到所有平台」  
> - 允许：「同一本游记，按你要发的地方出片」「杂志风游记 · 微信长图为主，朋友圈/小红书为发行配方」

> **产品共识（六条铁律）**
>
> 1. **张数分流看 `kept_n`（策展后保留图）**，不用原始 ingest 数做唯一依据。  
> 2. **Sparse / Narrative 强默认；Ambiguous（10–30）必须显式意图**，禁止假装系统已猜对。  
> 3. **UI 选「意图」，不是堆「平台设置面板」**；不破坏导出门面「不弱化 80% 路径」。  
> 4. **新平台 = 新 Recipe Preset（YAML）+ 文案**；禁止为此 fork 第二套策展/排版引擎。  
> 5. **朋友圈必须拆名**：`moments_grid`（九宫格配图）≠ `wechat_moments` / `moments_scroll`（长图连读切片）。  
> 6. **名实一致（P0-1）**：任何用户可见「九宫格」**必须**对应真 `moments_grid` Writer 产物；**禁止**用 `wechat_moments` scroll 顶替并宣称九宫格。

> **v1.1 评审回写摘要（2026-07-14 Conditional Go）**
>
> - 否决 OQ-OR-06（假九宫格过渡）  
> - Phase A 范围锁：Band + resolve + CTA + Ambiguous（发群 / 长图连读）；真九宫格与小红书主卡 → Phase B  
> - ADR-016 增补分支 D；入口矩阵 / pending 优先级冻结  
> - Overseas IG 仅 `hook_only`；改写 G-OR-10  
> - 词表单一真相源；feature flag；OQ-OR-01/02/04/05 升格决策

---

## 0. 读者指南

| 章节 | 必须澄清的问题 |
|------|----------------|
| §1 | 为何现有「一律长图 / 一律平台切」不够 |
| §2 | 目标、非目标、成功指标 |
| §3 | 已拍板决策（D-OR-*） |
| §4 | 设计原则与战略边界 |
| §5 | 三档 Band 定义与阈值 |
| §6 | Output Recipe 数据合同 |
| §7 | 意图目录与默认矩阵 |
| §8 | Studio / CLI 体验 |
| §9 | 与 LNG2 / 导出门面 / Overseas 的边界 |
| §10 | 解析器、持久化、API |
| §11 | 埋点与实验 |
| §12 | NFR |
| §13 | 验收 AC 索引 |
| §14 | 里程碑（含 Phase A 锁） |
| §15 | 风险与已关闭/开放问题 |
| 附录 C | 用户可见词表（单一真相源） |

---

## 1. 背景与问题

### 1.1 产品洞察（已共识）

| 判断 | 含义 |
|------|------|
| 摄影爱好者 / 多日游（常 ≥50 张） | 需要杂志叙事 + **按章多张长图**；这是品牌与付费锚 |
| 近郊 / 半天（常 ≤30 张） | 可能要发群长图、朋友圈九宫格、或其他平台惯用尺寸 |
| 极少图（1–9 张） | **不必凑九宫格**；默认单张微信群长图即可 |
| 只做微信长图 | 能服务摄影向，但会冷落「想快速发圈」的普通路径 |
| 做成全能导出中心 | 会拖垮 80% 路径，违反 [导出门面](./PRD-PREVIEW-EXPORT-FACADE-V1.md) 铁律 |

### 1.2 As-Is

| 能力 | 现状 | 缺口 |
|------|------|------|
| 默认 platform | 固定 `wechat_chat`（D-LNG2-01） | 不随 `kept_n` 变化 |
| 朋友圈 | `wechat_moments` = 长卷 **content_balanced** 切 ≤9 段 | **不是**竖保 + 横三拼的真九宫格 |
| 少图提示 | `<15` 选朋友圈 → toast 建议微信群（D-LNG2-17） | 仅提示，无默认分流 |
| 小红书 / IG | profile 已有；Studio 灰度 / CLI | 未纳入「按规模推荐」 |
| 导出门面 | 主 CTA = 长图；平台在 ▾ | 主 CTA 文案不随 band 变 |
| 配置 | `platform_profiles.yaml` | 缺统一 Recipe / Band → 默认映射 |

### 1.3 核心问题（P-OR-*）

| ID | 问题 | 影响 |
|----|------|------|
| **P-OR-01** | 1–9 与 200+ 共用同一默认成功态 | 小相册仪式过重或错误引导凑九宫格 |
| **P-OR-02** | 10–30 意图高度歧义，却无显式选择 | 猜错默认会同时得罪发圈与发群用户 |
| **P-OR-03** | 「朋友圈」一名两义（切片 vs 九宫格） | 用户期望与产物不一致 |
| **P-OR-04** | ≥50 仍易导向整卷单文件心智 | 体积/失败/难发；未强化按章 |
| **P-OR-05** | 平台扩展靠散落 UI/CLI 参数 | 难记忆、难覆盖、难做 locale 投影 |
| **P-OR-06** | 若做「全自定义导出器」 | 范围爆炸，偏离 CHARTER「编辑」定位 |

### 1.4 核心判断

> **输出配置引擎 = 薄的意图→配方解析层，不是设置操作系统。**  
> `band(kept_n) × locale × user_override → OutputRecipe`  
> 策展/排版引擎继续只做一本游记；Recipe 只决定**怎么发行**。

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-OR-01** | `kept_n` 三档 Band 可解析，阈值可配置 | 单测 + AC-OR-01 |
| **G-OR-02** | Sparse（1–9）默认 **微信群单张/短长图**，不默认九宫格 | AC-OR-02 |
| **G-OR-03** | Ambiguous（10–30）首次导出前 **必须完成意图选择**（Phase A：二选一；Phase B：三选一） | AC-OR-03 |
| **G-OR-04** | Narrative（≥31）默认 **微信群按章长图**；`kept_n≥50` 强化按章建议 | AC-OR-04 |
| **G-OR-05** | 存在统一 `OutputRecipe` 合同与 `resolve_output_recipe` | AC-OR-05；schema 测试 |
| **G-OR-06** | 用户可 **临时覆盖** 本次导出；可选「记住对本档的偏好」 | AC-OR-06 |
| **G-OR-07a** | Phase A 意图：发群长图 · 朋友圈长图连读 | AC-OR-07a |
| **G-OR-07b** | Phase B 增补：朋友圈九宫格 · 小红书（诚实标注） | AC-OR-07b |
| **G-OR-08** | 主 CTA / publishGuide 随 Recipe 变化；Sparse/Narrative 不破坏无 pending 一键合同 | AC-OR-08 |
| **G-OR-09** | `locale=zh` 行为不破坏现网微信群主路径回归 | LNG2 + 导出门面回归 |
| **G-OR-10** | Recipe **可挂接** `instagram_carousel` preset（状态仅 `hook_only`）；**不**在 Overseas Discovery Go 前把 `locale=en` Narrative 默认切到 IG；**永不**用海外钩子改写 `locale=zh` 默认 | AC-OR-10；与 Overseas V2 对齐 |
| **G-OR-11** | 名实一致：点「九宫格」必出 grid 产物与对应 guide | AC-OR-11 |
| **G-OR-12** | 种子可观测复用：Ambiguous 用户 30 日内二次导出率可统计 | 埋点 §11 |

### 2.2 非目标（V1）

| 类别 | 非目标 |
|------|--------|
| **算法** | 不 fork 第二套 ingest/curate/narrate/layout |
| **真机发布** | 不一键发到微信/小红书/Instagram App |
| **全能自定义** | 不做任意 CSS/HTML 模板；不做无限尺寸自由画布；`custom` 整段属 Phase D |
| **全平台 UI** | V1 Studio 不开放微博/抖音/Stories 菜单（preset 可后端预留） |
| **管线预算大改** | Sparse 跳过重 narrate 等属后置；本主题以导出层为主 |
| **替换 LNG2** | 不废除 `wechat_moments` 切片；与九宫格并存并改名区分 |
| **营销改口** | 不对外宣称「支持一切社交」；对外仍是游记编辑 |
| **假过渡** | **禁止** Phase A 用 scroll 冒充九宫格（否决 OQ-OR-06） |
| **海外抢跑** | 不把切片假 Carousel 设为 en Narrative 默认 |

### 2.3 成功指标（种子期建议）

| 指标 | 目标 |
|------|------|
| Ambiguous 意图选择完成率（展示后 → 确认） | ≥85% |
| Sparse 默认采纳率（不改意图直接导出） | ≥70% |
| Narrative≥50 按章导出占比 | ≥60%（或明确覆盖为整卷的占比可观测） |
| 导出门面 C1（无 pending 一键）在 Sparse/Narrative | **不回归** |
| `moments_grid` 与 `wechat_moments` 导出成功后用户能说出差异 | 手测 ≥4/5（Phase B） |
| Ambiguous 用户 30 日二次导出率 | 可观测（种子手测亦可） |
| Narrative≥50 按章后真实发群 | 种子手测可勾选 |

---

## 3. 已拍板决策（D-OR-*）

| ID | 决策 | 结论 |
|----|------|------|
| **D-OR-01** | 分流指标 | 默认用 **`kept_n`**；`ingest_n` 仅性能提示 |
| **D-OR-02** | Band 划分 | **Sparse 1–9 · Ambiguous 10–30 · Narrative ≥31**；阈值为**可实验常量** |
| **D-OR-03** | Sparse 默认 | **`intent=chat_longshot`** · `layout=single`；**不**默认九宫格 |
| **D-OR-04** | Ambiguous UX | 无本 trip intent 时导出前 **必须显式意图**；禁止静默猜默认主产物 |
| **D-OR-05a** | Phase A Ambiguous 意图 | ① 微信群长图 ② 朋友圈 · 长图连读；卡片 **不等权**（发群优先） |
| **D-OR-05b** | Phase B Ambiguous 意图 | 增 ③ 朋友圈 · 九宫格（真 Writer）④ 小红书（弱权重 + 诚实标注）；排序建议：发群 > 九宫格 > 连读（▾/子项）> 小红书 |
| **D-OR-06** | Narrative 默认 | **`intent=chat_longshot`** · **`layout=by_chapter`** |
| **D-OR-07** | ≥50 强化 | 默认按章；整卷单文件为高级且须 **二次确认** + 风险文案 |
| **D-OR-08** | 朋友圈双形态 | **`moments_grid`** 与 **`moments_scroll`（=`wechat_moments`）** 并存；UI 分名 |
| **D-OR-09** | Recipe 位置 | 解析结果驱动 Job；preset 存 YAML；override 存 trip 或 local preference |
| **D-OR-10** | 覆盖优先级 | **显式 user_override > trip 已存 intent > band 默认**（Ambiguous 无 intent 时按入口矩阵） |
| **D-OR-11** | 自定义 | **Phase D**；V1 Phase A/B 不做 `intent=custom` UI |
| **D-OR-12** | 导出门面 | Sparse/Narrative：**L0 一键**；Ambiguous：意图卡 **「选择并导出」合并**（D-OR-18） |
| **D-OR-13** | 战略 | **聚焦叙事成书；Recipe 服务多发行**；不做拼图工具品类 |
| **D-OR-14** | 与 Overseas | preset 状态机含 `hook_only`；V1 仅 `hook_only`；zh 默认不被海外改写 |
| **D-OR-15** | 非法组合 | Sparse+grid 不灌水；未知 platform **400** |
| **D-OR-16** | 书架入口 | Ambiguous 无 intent：**不强制三选一**；fallback `chat_longshot` + 弱提示（关闭 OQ-OR-01） |
| **D-OR-17** | 名实一致 | **否决**「九宫格文案 → scroll 后端」；未交付 Writer → 入口禁用或「即将推出」不可点 |
| **D-OR-18** | 意图卡交互 | **选择并导出** 单按钮（关闭 OQ-OR-02）；另提供「先选不导出」次要链接 |
| **D-OR-19** | grid 画布 | **1:1 contain**（关闭 OQ-OR-04） |
| **D-OR-20** | 横三拼 | **横仅与横拼；竖图独立成格**（关闭 OQ-OR-05） |
| **D-OR-21** | 注意力优先级 | **`layoutPending` > `needs_intent` > `longshotStale`** |
| **D-OR-22** | 引擎分层 | `intent` → `preset_id` → `engine: chapter_capture \| platform_segment \| photo_grid`；`platform` 仅为 Job 兼容别名 |
| **D-OR-23** | ADR | `moments_grid` 走 **ADR-016 分支 D**（`photo_grid_pack`） |
| **D-OR-24** | Feature flag | `studio.output_recipe.enabled`；关则回退 D-LNG2-01 固定 `wechat_chat` 默认 |
| **D-OR-25** | 小红书预期 | V1 Intent = **现网长卷适配配图**，非笔记构图引擎；用户可见必须诚实标注 |
| **D-OR-26** | LNG2 默认修订 | D-LNG2-01「默认 platform=`wechat_chat`」修订为：**默认由 `resolve_output_recipe` 决定**（Sparse/Narrative 仍常为 chat） |
| **D-OR-27** | 客户端 `kept_n` 同源 | Studio 预览裁决 `needs_intent` / Band CTA **必须以服务端 `kept_n`（`GET /output-recipe` 或 preview 注入同源值）为准**；**禁止**单独用 DOM 估图数（如 `estimatePhotoCountFromDom`）决定是否弹意图卡。DOM 估数仅可用于非 Band 提示。交叉：[PRD-SHARE-READY-OPTIMIZATION-V1](./PRD-SHARE-READY-OPTIMIZATION-V1.md) · 评审 2026-07-17 |

---

## 4. 设计原则与战略边界

### 4.1 原则（P-OR-*）

| ID | 原则 |
|----|------|
| **P-OR-01** | 规模决定**仪式与默认发行**，不决定「是不是旅行」 |
| **P-OR-02** | 歧义带用**选择**消解，不用更重的自动 |
| **P-OR-03** | 配置空间可以丰富，**主路径认知必须简单** |
| **P-OR-04** | 同一 trip 可多次按不同 Recipe 再导出（一书多发行） |
| **P-OR-05** | Preset 扩展成本必须是 YAML 级，而非引擎级 |
| **P-OR-06** | 告诉用户：几张、什么形态、发到哪、下一步怎么点 |
| **P-OR-07** | **名实一致**：可见文案与产物形态不得撒谎 |

### 4.2 战略边界

```text
聚焦：对外品类与付费锚 = Narrative 游记成书（摄影/多日游）
多服务：发行场景 = 发群 / 九宫格 / 长图连读 / 小红书 /（海外 hook）IG
不服务：纯拼图、短视频工厂、非旅行修图、无限自定义排版
```

| 档位 | 商业角色 |
|------|----------|
| Sparse | 不流失、建立信任；非付费主战场 |
| Ambiguous | **复用与口碑**；高频轻场景 |
| Narrative | **品牌与付费**；主价值主张 |

---

## 5. Band 定义

### 5.1 `kept_n` 定义

| 项 | 规格 |
|----|------|
| **定义** | 当前 trip 中，策展保留且会进入长图/杂志渲染的照片数量（与现网 longshot `photo_count` 语义对齐；**IMPLEMENTATION 钉死单一函数**） |
| **非定义** | 文件夹原始文件数、视频卡片数（视频不计入分流，除非后续 OQ） |
| **重算时机** | 策展完成、用户改选片并应用版面后；导出前读取最新值 |
| **配置键** | `output_recipe.bands.sparse_max` 默认 `9`；`ambiguous_max` 默认 `30` |

### 5.2 三档语义

| Band ID | `kept_n` | 典型场景 | 默认策略 |
|---------|----------|----------|----------|
| **`sparse`** | 1–9 | 晚饭、随手拍、极短出游 | 强默认发群长图 |
| **`ambiguous`** | 10–30 | 近郊半天、周末一日 | **显式意图**（见 Phase 意图集） |
| **`narrative`** | ≥31 | 短途多日、深度游、摄影向 | 强默认按章长图；≥50 强化 |

### 5.3 与 LNG2 验收集的关系

| LNG2 术语 | 与 Band |
|-----------|---------|
| T-tiny 1–5 | ⊂ sparse |
| T-small 8–12 | sparse 上沿或 ambiguous 下沿；**产品默认跟 Band，切分降级仍跟 LNG2** |
| sparse_photo_hint_below 15 | 保留为选 scroll 时的 hint |
| T-large ≥80 | ⊂ narrative |

---

## 6. Output Recipe 数据合同

### 6.1 概念（分层 · D-OR-22）

```text
Intent（用户要干什么）
  → preset_id（YAML 配方）
    → engine: chapter_capture | platform_segment | photo_grid
      → OutputRecipe（本次 Job 完整解析结果）
        → platform（Job 兼容别名，可选）
```

### 6.2 `OutputRecipe` 字段（V1 最小可执行集）

| 字段 | 类型 | 说明 |
|------|------|------|
| `recipe_id` / `preset_id` | string | 如 `preset.chat_longshot_chapter` |
| `intent` | enum | 见 §7.1 |
| `engine` | enum | `chapter_capture` \| `platform_segment` \| `photo_grid` |
| `band` | enum | `sparse` \| `ambiguous` \| `narrative` |
| `kept_n` | int | 解析时快照 |
| `locale` | string | 影响默认 preset 与文案 |
| `platform` | string | Job 兼容：`wechat_chat` / `wechat_moments` / `xiaohongshu` / `instagram` / `moments_grid` |
| `layout` | enum | `single` \| `by_chapter` \| `content_balanced` \| `grid` |
| `count_policy` | object | `{ mode: auto\|fixed, n?, min?, max? }` |
| `geometry` | object | `{ mode: native_long\|fixed_aspect, width?, height?, aspect? }` |
| `pad_mode` | enum \| null | `letterbox` \| `smart_crop` \| null |
| `packing` | enum | `none` \| `h_triple_stitch`（仅 grid · Phase B1） |
| `quality` | object | `{ scale: 1\|2\|3 }` |
| `publish_guide_key` | string | 文案键 |
| `user_hints` | string[] | |
| `needs_intent` | bool | |
| `source` | enum | `band_default` \| `intent_choice` \| `trip_override` \| `session_override` |
| `instagram_preset_state` | enum \| null | 仅 IG：`hook_only`（V1 唯一合法） |

> Phase D 再扩：`caption`、`deliverable`、`custom` 字段。V1 A/B 可不实现。

### 6.3 Preset 注册

- 可新增 `config/output_recipe_presets.yaml` + `config/output_recipe_bands.yaml`  
- **或**在 `platform_profiles.yaml` 增 `recipes:` / `bands:` 段（键名须稳定）

每个 preset **必须**声明：`id`、`intent`、`engine`、`platform`（别名）、`layout` / `geometry` / `count_policy`、`phases`（`studio`\|`cli`\|`hidden`）、`publish_guide`。

### 6.4 非法与降级

| 情况 | 行为 |
|------|------|
| Ambiguous + 无 intent（预览） | `needs_intent=true`；拦截至选出 |
| Ambiguous + 无 intent（书架） | fallback `chat_longshot` + 弱提示（D-OR-16） |
| Ambiguous + 无 intent（CLI） | 须 `--intent` 或 `--platform`，否则非 0 退出 |
| Sparse + `moments_grid` 且 `kept_n<9` | 导出 N=`kept_n`；**UI 可见** hint「有几张发几张」；禁止灌水 |
| 未知 platform / recipe | API **400**；`E_OR_*` |
| 九宫格入口但 Writer 未上线 | UI **禁用**；不得改走 scroll |

---

## 7. 意图目录与默认矩阵

### 7.1 Intent 枚举

| Intent ID | 用户可见名（zh） | engine | Phase |
|-----------|------------------|--------|-------|
| `chat_longshot` | 微信群 · 长图 | `chapter_capture` | A |
| `moments_scroll` | 朋友圈 · 长图连读 | `platform_segment`（`wechat_moments`） | A |
| `moments_grid` | 朋友圈 · 九宫格 | `photo_grid` | **B** |
| `xiaohongshu` | 小红书 · 笔记配图（杂志页适配） | `platform_segment` | **B**（主卡）；A 可 CLI |
| `instagram_carousel` | Instagram · 轮播 | hook / 后续 native | **D 钩子**；状态 `hook_only` |

### 7.2 国内默认矩阵（`locale=zh`）

| Band | 默认 Intent | 默认 layout | 主 CTA（词表） | 次入口 |
|------|-------------|-------------|----------------|--------|
| sparse | `chat_longshot` | `single` | 导出长图 · 发微信群 | ▾ 其他（九宫格仅 Phase B 且 Writer 可用时） |
| ambiguous | — | — | （意图卡，无单一主 CTA） | 见 §7.3 |
| narrative | `chat_longshot` | `by_chapter` | 按章导出长图 · 发微信群 | ▾ 整卷（二次确认）/ 其他发行 |
| narrative · `kept_n≥50` | 同上 | `by_chapter` | 同上 + 副文「照片较多，已按章拆分」 | 整卷二次确认 |

### 7.3 Ambiguous 意图选项

#### Phase A（批准开工范围）

| 选项 | Intent | 权重 |
|------|--------|------|
| A | `chat_longshot`（推荐 `single`） | **主** |
| B | `moments_scroll` | 次 |

标题：「这趟精选了 N 张，你想怎么发？」  
主按钮：**选择并导出**（D-OR-18）

#### Phase B（Writer + xhs 就绪后）

| 选项 | Intent | 权重 |
|------|--------|------|
| A | `chat_longshot` | **主** |
| B | `moments_grid` | 次主（仅 Writer 可用） |
| C | `xiaohongshu` | 弱；副文：**杂志页适配为 3:4 配图，不是笔记重排版** |
| — | `moments_scroll` | 不占主位；作 B 的子项或 ▾ |

### 7.4 海外 locale（钩子）

| 项 | 规格 |
|----|------|
| `locale=zh` | **永不**被 Overseas 钩子改写默认 |
| `instagram_carousel` | preset 可注册；状态 **仅 `hook_only`** |
| en Narrative 默认切 IG | **须 Overseas Discovery Go + 单独产品决议**；本 PRD 不授权 |
| en Sparse | 默认建议 **archive longshot**（OQ-OR-03 建议；联席可改） |

### 7.5 `moments_grid` 最小规格（Phase B）

| 项 | 规格 |
|----|------|
| 目标张数 | `min(9, kept_n)`；不硬凑 |
| 选图 | 保留集；建议质量 Top-N；允许导出前剔除（P1） |
| 竖图 | **1:1 画布 contain**（D-OR-19） |
| 横图 | Phase B0：单张横图 letterbox；Phase B1：`h_triple_stitch`（D-OR-20） |
| 输出 | `{title}-moments-grid-{nn}.png` |
| publishGuide | 专用「九宫格」文案；**禁止**与连读共用 |
| 架构 | **ADR-016 分支 D**；输入 kept 列表；**不**依赖 full longshot capture；禁 P1；原子写盘 |

---

## 8. Studio / CLI 体验

### 8.1 交互层级

| 层 | 用户看见 | 何时 |
|----|----------|------|
| **L0** | 一个主按钮 | sparse / narrative 已解析 |
| **L1** | 意图卡 | ambiguous 且 `needs_intent`（且无更高优先级拦截） |
| **L2** | ▾ 高级 | 换意图、按章/整卷、清晰度、长图连读 |
| **L3** | 自定义 | **Phase D** |

### 8.2 点击预算

| 路径 | 预算 |
|------|------|
| sparse / narrative · 无 pending · 默认 Recipe | **1 次**（C1） |
| ambiguous · 「选择并导出」 | **1 次意图兼导出**（进入现有 Job 流程） |
| pending 拦截 | 沿用导出门面；**先于**意图卡（D-OR-21） |

### 8.3 Ambiguous 入口矩阵（P0-3 · 冻结）

| 入口 | 无 trip intent 时 |
|------|-------------------|
| **预览导出** | 强制 L1 意图卡；不可静默默认主产物 |
| **书架「保存长图」** | fallback `chat_longshot` + 弱提示「可到预览选择其他分享方式」 |
| **CLI** | 须 `--intent` 或 `--platform` |

### 8.4 注意力优先级（P0-4 · 冻结）

```text
layoutPending > needs_intent > longshotStale
```

失败态须展示意图可读名，并提供 CTA：**换种分享方式**（回到 L1/L2）。

### 8.5 意图卡 UI

- 标题：「这趟精选了 N 张，你想怎么发？」  
- 每卡：意图名 + 结果预期（张数/形态）  
- 主按钮：**选择并导出**  
- 次要：「先选不导出」（只写 intent）  
- 「记住偏好」默认 **关**；文案：「以后 10–30 张默认用这个」

### 8.6 Sparse 细节

- 主 CTA 固定词表「导出长图 · 发微信群」  
- `kept_n=9`：可选弱提示一次「想发朋友圈可在 ▾ 切换」（不阻断）  
- 选 grid（Phase B）时 hint **必须 UI 可见**

### 8.7 Narrative ≥50

- 主路径按章  
- 高级「整卷」：二次确认 Modal（预估风险 / 可能失败）后再导出  

### 8.8 CLI

```powershell
python -m travelogue export-longshot trips\demo --intent moments_scroll
python -m travelogue export-longshot trips\demo --platform wechat_moments
python -m travelogue export-longshot trips\demo --intent moments_grid
python -m travelogue resolve-output-recipe trips\demo
```

`--intent` 与 `--platform` 冲突 → 400 / 非 0。优先级表见 IMPLEMENTATION。

### 8.9 成功态

必须：产物类型名（词表）+ 文件数 + publish_guide。  
禁止：只说「导出成功」。

---

## 9. 与现有主题的边界

| 主题 | 本 PRD 做什么 | 不做什么 |
|------|----------------|----------|
| **Longshot 2.0** | 消费 Job；分支 D 增 grid；连读改名 | 不改 DP 核心 |
| **导出门面 V1** | CTA 随 Recipe；Ambiguous L1 | 平台大面板不进 Dock |
| **Overseas V2** | `hook_only` preset | 不替代 Discovery / 页角色 / 跨设备 |
| **SHARING.md** | 路径 A 扩展为 Recipe 发行 | 不改路径 B 隐私 |
| **CHARTER** | 编辑 → 多发行 | 不变成内容工厂 |

### 9.1 对 LNG2 的修订

| LNG2 | 本 PRD |
|------|--------|
| D-LNG2-01 默认 `wechat_chat` | **D-OR-26**：默认由 resolve 决定 |
| 朋友圈仅切片 | 增补 grid（Phase B）；切片 UI 名「长图连读」 |

交叉引用已写入 [SHARING.md](./SHARING.md) / [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) 头部。

---

## 10. 解析器、持久化、API

### 10.1 `resolve_output_recipe`

```text
输入: kept_n, locale, trip.output?, session_override?, cli_flags?, entrypoint?
输出: OutputRecipe

1. band ← from kept_n
2. if session/cli explicit → merge → return
3. if trip.output.intent|recipe_id → merge → return
4. if band == ambiguous and entrypoint == preview and no intent
     → needs_intent=true
5. if band == ambiguous and entrypoint == shelf and no intent
     → band_default chat_longshot + hint
6. else → band_default for locale
```

**客户端（D-OR-27 · 2026-07-17）**：预览 Dock / stale 重导出在展示意图卡前，须使用本 resolve 的 `kept_n`（API 或 bootstrap 注入），**不得**用版面 DOM 槽位数替代 `kept_n` 做步骤 1/4。

### 10.2 持久化

| 存储 | 内容 |
|------|------|
| `trip.json` → `output` | `intent`, `preset_id`, `layout`, `last_resolved`（可选字段；旧 trip 缺省即 resolve） |
| local prefs | `band_preferences[ambiguous]` |
| Job body | Recipe 或 intent/platform |

### 10.3 API（建议）

| 端点 | 行为 |
|------|------|
| `GET .../output-recipe` | resolve（含 `needs_intent`） |
| `PUT .../output` | 写 intent |
| `POST /longshot` | 先 resolve 再执行；可带 `intent` |

错误码：`E_OR_*`（IMPLEMENTATION 首周分配）。

### 10.4 模块边界

| 模块 | 职责 |
|------|------|
| `output_recipe/resolve.py` | 纯解析 |
| presets YAML | 配置 |
| `moments_grid` writer | 分支 D · Phase B |
| `platform_longshot.py` | 分支 B · scroll/xhs/ig |
| `longshot.py` | 路由 A/B/D |
| `longshot-export-panel.js` | L1/L2；禁止堆 toolbar；`estimatePhotoCountFromDom` **不得**裁决 Band（D-OR-27） |
| `preview-toolbar/longshot.js` | `startLongshotWithRecipe` 须先消费服务端 recipe / 注入 `keptN` |

---

## 11. 埋点与实验

| 事件 | 属性 |
|------|------|
| `output_recipe_resolve` | `band`, `kept_n`, `needs_intent`, `source`, `entrypoint` |
| `output_intent_shown` | `band`, `options[]`, `phase` |
| `output_intent_selected` | `intent`, `remember_pref` |
| `output_intent_dismissed` | |
| `longshot_export_start/success` | 增 `intent`, `recipe_id`, `band`, `layout`, `engine` |

可选实验：Ambiguous 文案 A/B；≥50 按章 vs 整卷警告（产品默认仍按章）。

---

## 12. 非功能需求

| ID | 要求 |
|----|------|
| **NFR-OR-01** | resolve P95 \< 50ms |
| **NFR-OR-02** | grid（≤20 源图）P95 ≤ 同机 moments scroll 的 150%（Phase B） |
| **NFR-OR-03** | 意图卡可键盘操作 |
| **NFR-OR-04** | YAML 损坏显式失败 |
| **NFR-OR-05** | Recipe 不含照片字节 |

---

## 13. 验收

完整步骤见 [ACCEPTANCE-OUTPUT-RECIPE-V1.md](./ACCEPTANCE-OUTPUT-RECIPE-V1.md)。P0 索引：

| ID | 项 | Phase |
|----|----|-------|
| AC-OR-01～06 | Band / 默认 / needs_intent / schema / 持久化 | A |
| AC-OR-07a | 发群 + 连读 | A |
| AC-OR-08 | 导出门面 C1 | A |
| AC-OR-10 | Overseas hook-only / zh 不被改写 | A |
| AC-OR-11 | 名实一致（无假九宫格） | A/B |
| AC-OR-07b / 09 / 12 | grid / xhs / 手测分名 | B |
| AC-OR-13 | feature flag 回退 | A |

---

## 14. 里程碑

| Phase | 主题 | 交付 | 预估 |
|-------|------|------|------|
| **A · 决策面（批准）** | Band + resolve + CTA 词表 + Ambiguous 二选一（发群/连读）+ 入口矩阵 + flag + C1 回归 | 可灰度行为 | 1–2 周 |
| **B · 真九宫格 + xhs 主卡** | 分支 D Writer（B0→B1）+ Ambiguous 扩卡 + 诚实 xhs 文案 | 普通发圈闭环 | 2–4 周 |
| **C · 持久化与偏好** | trip.output + band pref + API | 少重复选择 | 1 周 |
| **D · 自定义与海外钩子** | custom 白名单；IG `hook_only` 挂接 | 扩展 | 后置 |

**Go A→B**

- [ ] P0 Must-Fix 已关闭（本 v1.1）  
- [ ] AC-OR Phase A 绿 + 导出门面 C1 签字  
- [ ] 无「九宫格→scroll」任何残留文案  

**Go 发布（含 B）**

- [ ] AC-OR-07b、09、11、12 绿  
- [ ] ≥3 名非作者种子各完成 1 个 Ambiguous 真发出  

---

## 15. 风险与开放问题

### 15.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| R-OR-01 | 设置中心化 | L0/L1；Phase A 锁范围 |
| R-OR-02 | 双朋友圈混乱 | 分名 + 双 guide + AC-OR-11 |
| R-OR-03 | Ambiguous 打扰 | 选并导出；记住偏好默认关 |
| R-OR-04 | ≥50 要整卷 | 二次确认 |
| R-OR-05 | Overseas 抢主线 | hook_only |
| R-OR-06 | `kept_n` 漂移 | 单一计数函数 |
| R-OR-07 | 假九宫格信任债 | **D-OR-17 否决** |

### 15.2 开放问题

| ID | 状态 | 结论 / 残留 |
|----|------|-------------|
| OQ-OR-01 | **关闭** | 书架 fallback 发群 + 弱提示（D-OR-16） |
| OQ-OR-02 | **关闭** | 选择并导出（D-OR-18） |
| OQ-OR-04 | **关闭** | 1:1 contain（D-OR-19） |
| OQ-OR-05 | **关闭** | 横仅与横拼（D-OR-20） |
| OQ-OR-06 | **否决关闭** | 禁止假九宫格（D-OR-17） |
| OQ-OR-03 | **开放** | en Sparse 默认；建议 archive longshot；Overseas 联席 |
| OQ-OR-07 | **开放（非阻塞）** | trip.`output` 可选字段；IMPLEMENTATION 钉 |

---

## 16. 文档修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-07-14 | 初稿 |
| **v1.1.0** | **2026-07-14** | Conditional Go 回写：P0-1～8、Phase A 锁、分支 D、入口矩阵、G-OR-10 hook_only、词表、否决 OQ-OR-06 |

---

## 附录 A · 用户可见文案草案（zh）

见 **附录 C（权威）**；本附录保留可读摘录。

| 场景 | 文案 |
|------|------|
| Sparse 主 CTA | 导出长图 · 发微信群 |
| Sparse 成功 | 长图已保存。可发送到微信群。 |
| Ambiguous 标题 | 这趟精选了 N 张，你想怎么发？ |
| Ambiguous A | 微信群长图 — 整篇游记发到群里 |
| Ambiguous · 连读 | 朋友圈 · 长图连读 — 最多 9 段，滑动连读 |
| Ambiguous · 九宫格（B） | 朋友圈 · 九宫格 — 约 N 张 1:1 配图 |
| Ambiguous · 小红书（B） | 小红书配图 — 杂志页适配 3:4（非笔记重排版） |
| Narrative 主 CTA | 按章导出长图 · 发微信群 |
| Narrative≥50 副文 | 照片较多，已按章节拆成多张，方便发送 |

## 附录 B · 「输出配置引擎」对照

| 用户说法 | 落点 |
|----------|------|
| 按张数有默认 | Band → 默认 Recipe |
| 临时改默认 | session / trip override |
| 社交惯用规格 | Recipe Preset |
| 自定义 | Phase D 受限字段 |
| 别太复杂 | L0/L1/L2；Ambiguous 才强制选择 |

## 附录 C · 用户可见词表（单一真相源 · P0-7）

| 内部 ID | 用户可见名 | 禁止别称 |
|---------|------------|----------|
| `chat_longshot` | 微信群 · 长图 / 导出长图 · 发微信群 | 「一键发圈」 |
| `moments_scroll` / `wechat_moments` | 朋友圈 · 长图连读 | 「九宫格」「朋友圈配图」（易混） |
| `moments_grid` | 朋友圈 · 九宫格 / 九宫格配图 | 在 Writer 未上线时出现可点入口 |
| `xiaohongshu` | 小红书 · 笔记配图（杂志页适配） | 「小红书原生笔记排版」 |
| `instagram_carousel` | Instagram · 轮播 | 在 hook_only 阶段称「可发布原生轮播」若无 Overseas Go |

成功态必须带上表「用户可见名」之一 + 文件数 + 对应 publishGuide。
