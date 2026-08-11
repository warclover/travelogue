# Travelogue · 封面装帧打磨 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Draft · Implementing W1** |
| **DOC-STATUS** | **active** |
| **主题代号** | 「封面装帧打磨」— **CCF**（Cover Craft Focus） |
| **触发来源** | 2026-08-11 产品纠偏：封面观感仍偏普通；不要更多版式，只要 **2–3 款稳定出片**。此前 [PRD-COVER-EDITORIAL-COVENANT-V1](./PRD-COVER-EDITORIAL-COVENANT-V1.md)（CEC）偏「推荐/契约」，与该目标不对齐，**由本文取代** |
| **前置条件** | Cover Style Engine / `list_assignable_styles()` 可用；`trips/linzhi/journal.css` Opening pack 可改；CAL 路线 B 白名单含本主题三款主菜；[PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md](./PRD-COVER-STYLES-V6-ART-DIRECTION-DELTA.md) 为手法基线（**可分配集合以代码为准，不以 Delta「十款」过时表述为准**） |
| **关联文档** | [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) · [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md) · [PRD-COVER-TYPESETTING-CONTINUITY-V1.md](./PRD-COVER-TYPESETTING-CONTINUITY-V1.md)（CTS · 字数防翻车可并行，非本主题主角）· [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)（CAD · 下游；本主题不实现一键导演） |
| **验收** | Kickoff 后拆 `ACCEPTANCE-COVER-CRAFT-FOCUS-V1.md`；本文 §10 为源 |
| **实施清单** | Kickoff 后拆 `IMPLEMENTATION-COVER-CRAFT-FOCUS-V1.md` |
| **更新日期** | 2026-08-11（v0.2.0：FE-CCF + 一键撤回） |

> **定位**
>
> CCF 解决的是：**封面看起来不够像画册**，而不是「版式不够多」或「缺推荐列表」。  
> 策略 = **收到 2–3 款主菜 → 同 id 换手法打磨 → 选图更稳 → 艺术字只服务主菜**。  
> 不新开 Opening 皮肤，不拆 `cover-opening.hbs`，不默认文生图封面。
>
> **一句话目标**：用户打开预览时，默认封面在多数真实 trip 上「一眼像装帧过的旅行画册」，且只有少数版式可选、出片方差可控。
>
> **战略原则（拟冻结）**
>
> 1. **质感优先于选项** — 主路径只养 2–3 款；其余可渲染但不进新建/联合分配（retired 或权重归零）。  
> 2. **同 id 换手法** — 沿用 Delta：改 `journal.css` token 与伪元素，不新建模板、不扩 catalog。  
> 3. **真照片默认** — 主视觉来自 trip 资产；禁止 AI 整图假风景默认路径。  
> 4. **图进对皮肤** — 高级感一半在 fit；主菜的 `prefer`/`avoid` 必须比现网更可测。  
> 5. **点睛服务主菜** — CAL 只打磨三款白名单内表现；不借本主题扩艺术字到更多版式。  
> 6. **盲评出门** — 视觉升档须过偏好盲评，禁止「改完 token 自评好看」即默认全量。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语与主菜集合 |
| §0.2 | 相邻边界 |
| §1 | 背景与问题 |
| §2 | 目标 / 非目标 |
| §3 | 冻结决策 D-CCF-* |
| §4 | 主菜范围与可分配收缩 |
| §5 | Craft 打磨规格（CSS / 排版层级） |
| §6 | 选图 × 主菜 fit |
| §7 | CAL 在主菜上的收口 |
| §8 | Studio / 数据 |
| §8.1 | Studio 前端任务 FE-CCF-* |
| §8.2 | 一键撤回（cover_craft flag） |
| §9 | 里程碑 |
| §10 | 验收 AC-CCF-* |
| §11 | 风险与 OQ |
| §12 | 变更记录 |
| 附录 A | 相对 CEC / Punk 的去留 |
| 附录 B | 代码挂点 |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **主菜（Hero Set）** | 本主题全力打磨、且进入新建/联合分配的 Opening 集合，**默认 3 款**（§4） |
| **配菜** | 现网仍 `active` 但不进本轮打磨优先级的版式；本主题将其移出可分配或极低权重 |
| **Craft** | 同 style id 下的视觉手法升档（雾、纸、切线、字阶、边距、伪元素完成度） |
| **稳定出片** | 在 dogfood 真实 trip 样本上，默认分配到主菜时，主观「可用作分享封面」占比达标（§10） |

### 0.2 相邻边界

| 主题 | CCF 拥有 | CCF 不碰 |
|------|----------|----------|
| **V6 / Delta** | 主菜 CSS pack 再打磨；纠正「十款可分配」与代码不一致 | 不重开第 11 款；不复活已 retired 五款为分配池 |
| **CAL** | 三款主菜的贴纸观感/placement/字号微调 | 不扩白名单；路线 C 不升默认 |
| **CTS** | 可引用字数档作主菜排版约束 | 不重做 Spec 全文 / 身份线审计主题 |
| **CAD** | 为日后 Mode A 提供「更稳的默认封面」基线 | 不实现一键导演 / `artDirection` |
| **CEC** | 吸收其「真照片 / 不扩库 / 否决文生图」边界 | **不**交付 Recommend-3、全量 Style Covenant 引擎 |

---

## 1. 背景与问题

### 1.1 As-Is（代码事实）

| 项 | 事实 |
|----|------|
| 可分配 Opening | **5 款 active**：`veil-footer` / `folio-overlap` / `band-cut` / `scroll-head` / `contact-stamp`（`catalog.py`；另 5 款 `retired`） |
| 视觉实现 | **单** `cover-opening.hbs` + `trips/linzhi/journal.css` 分皮肤；差异已是装帧手法，不是纯挪字 |
| CAL | 路线 B 白名单含 `veil-footer` / `folio-overlap` / `band-cut` / `contact-stamp`（**无** `scroll-head`） |
| 文档漂移 | Delta / 部分索引仍写「十款 active」——**以 `list_assignable_styles()` 为准** |
| CEC 草案 | 主交付为契约字段 + 推荐 3 版式，**不改像素**，与「封面普通」痛点错位 |

### 1.2 问题陈述（P-CCF-*）

| ID | 问题 | 严重度 |
|----|------|--------|
| **P-CCF-01** | 默认封面「能用但不贵」：雾/纸/断带完成度与字阶仍偏模板感 | 阻塞 |
| **P-CCF-02** | 可分配 5 款分散打磨精力，出片方差大，用户难形成「这本相册的封面语言」 | 严重 |
| **P-CCF-03** | 主菜 `prefer`/`avoid` 偏弱启发式，好图配错皮肤 → 再精 CSS 也普通 | 严重 |
| **P-CCF-04** | CAL 点睛与原生标题/衬底在部分 trip 上仍「像贴上去」而非长在版式里 | 中等 |
| **P-CCF-05** | 若继续做 Recommend-3 / 扩契约，会占用本应打磨像素的排期 | 严重（路线风险） |

### 1.3 成功长什么样

> 打开一本新游记：**大概率**落在三款主菜之一；封面摄影清楚、题名层级干净、装帧细节经得起首屏 3 秒验货。  
> Studio 版式选择器**不再**鼓励在五六种普通皮肤间试错。

---

## 2. 目标与非目标

### 2.1 目标（In Scope）

| ID | 目标 |
|----|------|
| **G-CCF-01** | 冻结 **Hero Set = 3 款**：`veil-footer` · `folio-overlap` · `band-cut` |
| **G-CCF-02** | 将 `scroll-head` / `contact-stamp` 移出新建与联合分配（`retired` 或等价不可分配；旧 trip 仍可渲染） |
| **G-CCF-03** | 三款主菜完成一轮 **Craft 升档**（token + 伪元素 + 字阶/边距），附前后对照截图 |
| **G-CCF-04** | 收紧三款 **fit/avoid** 与联合选型权重，使默认分配「图皮相称」可测 |
| **G-CCF-05** | 三款主菜上 CAL 贴纸做一次 **观感收口**（placement/衬底/与面板关系），不扩白名单 |
| **G-CCF-06** | 盲评：升档后 vs 升档前，偏好 ≥55% 才可将新 craft 设为生产默认 |

### 2.2 非目标（Out of Scope · V1）

| ID | 非目标 | 理由 |
|----|--------|------|
| **NG-CCF-01** | 新增 Opening 皮肤 / 拆多套 HBS | 质感优先；Delta 已禁止多模板 |
| **NG-CCF-02** | Recommend-3 / 全量 Style Covenant 引擎（原 CEC 主交付） | 版式收到 3 款后推荐价值低；不解决「普通」 |
| **NG-CCF-03** | AI 整图替换用户封面 | 信任；CAD Mode D |
| **NG-CCF-04** | 复活 `type-monument` / `horizon-split` 等 retired 进分配池 | 扩大方差；与「2–3 款」冲突 |
| **NG-CCF-05** | 路线 C 默认化 / 开放 prompt | CAL 边界 |
| **NG-CCF-06** | CAD 一键导演全量 | 下游主题 |
| **NG-CCF-07** | 以社媒画幅为主路径重做封面 | 成册 Web/导出为主 |

---

## 3. 冻结决策（D-CCF-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CCF-01** | **Hero Set 锁定三款** | `veil-footer`（默认气质）· `folio-overlap`（纸本装帧）· `band-cut`（风景断带）。变更须产品书面改本表 |
| **D-CCF-02** | **配菜退出分配（可撤回）** | CCF 开启时 `scroll-head` / `contact-stamp` **不进** `list_assignable_styles()` / Studio / joint；catalog 仍保持 `active` 以便 `cover_craft.enabled=false` 一键恢复。已生成 trip **保持**原 `data-cover-opening` 渲染 |
| **D-CCF-03** | **打磨顺序** | W1 `veil-footer` → W1b `band-cut` → W2 `folio-overlap`（默认流量优先雾底/断带；纸栏次之） |
| **D-CCF-04** | **视觉真相源** | 生产以 `journal.css` 为准；每款升档须留「前/后」截图进 acceptance-records；线框仅参考 |
| **D-CCF-05** | **不拆模板** | 禁止为 craft 增加样式专属 DOM 分支；允许沿用 Delta 已有的最小 HBS 属性（`--cover-src` / focal 等） |
| **D-CCF-06** | **fit 可测** | 每款至少 3 条可单测的 prefer/avoid 金样（fixture 图或合成特征）；禁止只改文案 blurb |
| **D-CCF-07** | **CAL 范围** | 本主题只优化 Hero Set ∩ 现白名单（三款均已在白名单）；`contact-stamp` 随配菜退分配后，**不**在本主题继续扩其艺术字 |
| **D-CCF-08** | **盲评门禁** | 新 craft 默认合入生产须 AC-CCF-BLIND ≥55%；未过门可合入 flag 后默认关 |
| **D-CCF-09** | **窄屏** | `<1024px` 仍 CSS 回落 `veil-footer` 呈现；attribute 不变（承 V6） |
| **D-CCF-10** | **CEC 处置** | CEC PRD 标记 superseded → 本文；其附录「否决文生图」并入本文附录 A |
| **D-CCF-11** | **一键撤回** | 全部 CCF 运行时行为受 `cover_craft.enabled`（及环境变量 `TRAVELOGUE_COVER_CRAFT`）总闸控制；关闭后恢复五款可分配、不写 `data-cover-craft`、Studio 不走历史经典提示分支。见 **§8.2** |

---

## 4. 主菜范围与可分配收缩

### 4.1 Hero Set（打磨 + 可分配）

| id | studio 名 | 为何入选 |
|----|-----------|----------|
| `veil-footer` | 沉浸题签 | 默认向；大场面电影感；CAL 首发 |
| `folio-overlap` | 对页叠印 | 最强「书」感；纸栏装帧差异大 |
| `band-cut` | 切带题名 | 旅行风景高频；断带识别度高；CAL 已开 |

### 4.2 退出本轮分配

| id | 处置 | 理由 |
|----|------|------|
| `scroll-head` | CCF 开启时不可分配（catalog 仍 active，便于撤回） | 竖排/卷纸打磨成本高；不在 CAL 白名单；分散主菜精力 |
| `contact-stamp` | 同上 | 档案装饰易「玩票」；非首屏验货主语言 |

已 `retired` 的五款（`cameo-aperture` / `type-monument` / `portal-arch` / `horizon-split` / `diptych-seam`）**保持 retired**，本主题不复活。

### 4.3 分配后果

| 路径 | 行为 |
|------|------|
| 新建 / curate joint | 只在 Hero Set 三款中选 |
| hash 回落 | `hash % 3`（仅三款） |
| Studio 版式选择器 | 只展示三款（+ 当前 trip 若为历史配菜/retired，只读展示当前项，可提示「经典版式 · 可切换到现行三款」） |
| schema | `coverOpeningStyle` 枚举可仍接受历史 id 以便旧数据；**新写入**仅允许 Hero Set（或写时校验） |

---

## 5. Craft 打磨规格

### 5.1 总原则

相对现网 Delta 已落地手法，本轮不是「再发明一款」，而是把三款推到：**留白更敢、材质更真、字阶更稳、装饰更少却更准**。

每款交付必须包含：

1. Token 变更表（旧 → 新）  
2. ≥3 张真实 trip 前后对比（Web ≥1024）  
3. 无 hook / 长标题 / 有 titleArt 各至少 1 个边界样  

### 5.2 `veil-footer`（W1）

| 维度 | 打磨方向（产品语言） | 挂点 |
|------|----------------------|------|
| 雾与光 | 雾更分层、底更沉；暖光只服务题名，不糊成脏罩 | `--cover-veil-fog*` / `--cover-veil-glow` |
| 字阶 | 主标题更像书名而非 UI 标题；hook 永远弱一档 | `--cover-veil-title-size` / hook size |
| 面板 | 题名区克制宽度，避免「大白卡片」感回潮 | `--cover-veil-panel-max` |
| 层级 | 主标题 > hook > 身份线；艺术字开时原生题名不抢 | 现有 `[data-title-art="on"]` 规则微调 |

**完成定义**：盲评样本中「电影开场感」显著优于现网默认雾底；无大面积脏雾挡脸（配合 fit）。

### 5.3 `band-cut`（W1b）

| 维度 | 打磨方向 | 挂点 |
|------|----------|------|
| 切线 | 1px 切线稳定在约定窗内（承 Delta **60%–66%**，现网中线约 63%） | `--cover-band-center` |
| 标签 | 左缘纸签渐隐更像印刷标签，非通栏色带 | `--cover-band-*` / label max |
| hook | 出带文案压照片但不糊主体 | panel / hook 规则 |
| CAL | 贴纸贴在断带语言内，不溢出切线 | title-art CSS + whitelist rect |

**完成定义**：风景+天际线样本上「断带装帧」一眼可读；人物落切线的失败由 fit 挡住而非靠用户试错。

### 5.4 `folio-overlap`（W2）

| 维度 | 打磨方向 | 挂点 |
|------|----------|------|
| 纸栏 | 纸色/阴影/骑缝切开字更像对页，而不是左侧色块 UI | `--cover-folio-*` |
| 套印 | 红影/叠印克制，避免廉价滤镜感 | `--cover-folio-ghost` 等 |
| 竖题 | 字阶与纸栏宽度匹配；长标题降级策略清晰（承 Delta 空状态） | title size / 单色墨字回落 |
| CAL | 纸面栏上的贴纸衬底与纸色一致（已有 `assume_paper_bg` 方向） | title_art 渲染 |

**完成定义**：右景左纸样本上「像一本打开的书」；无厚白卡回潮。

### 5.5 明确不做的「高级感」套路

- 胶片颗粒全屏默认层、Ken Burns 自动推镜（Delta 已标非 P0）  
- 首屏徽章、统计条、促销贴  
- 巨型透视标题抢摄影（Punk `giant-perspective` 方向否决为默认）  

---

## 6. 选图 × 主菜 fit

### 6.1 目标

在 **仅三款** 的联合选型下，提高「打开即相称」比例；允许小幅加强 `prefer`/`avoid`，**不**重写 cover score 主公式。

### 6.2 每款最低信号（须可测）

| id | 加强方向（示例，Kickoff 定数值） |
|----|----------------------------------|
| `veil-footer` | 主体偏上；下半不宜过亮；压脸则罚 |
| `band-cut` | 天际线/上半场景；`band_safe_zone` 内不宜有人脸/主体 |
| `folio-overlap` | 右权重景；左 30% 不宜主体 |

### 6.3 解释（可选、克制）

Studio 换版式或首次分配后，可用**一句**现有 blurb/fit-hint；**不**做 Recommend-3 列表（NG-CCF-02）。

---

## 7. CAL 在主菜上的收口

| 项 | 要求 |
|----|------|
| 范围 | 仅 Hero Set 三款 |
| 内容 | placement 不压脸/不溢出装帧件；衬底与版式语言一致；字号不超过该风格安全区 |
| 非目标 | 新风格入库、路线 C、字体可读性算法（D-CAL-24） |
| 与 CTS | 长标题谨慎档可提示缩短；本主题不独自实现完整 CTS Spec |

---

## 8. Studio / 数据

| 面 | 行为 |
|----|------|
| 版式选择器 | 三选一；文案强调气质差异，不强调「更多模板」 |
| 历史 trip | 配菜/retired id 仍渲染；切换时写入 Hero Set id |
| telemetry | `coverOpeningStyle` 分配分布；craft 版本号（如 `coverCraftVersion: ccf-v1`）便于前后对比 |
| 文档纠偏 | 更新 Delta/README/schema 描述中「十款可分配」为「以 list_assignable 为准；CCF 后 = 3」 |

### 8.1 Studio 前端任务（FE-CCF-*）

主视觉升档在 `journal.css`；Studio 壳层只做**收口与历史提示**，不做 Recommend-3。

| ID | 任务 | 优先级 | 挂点 |
|----|------|--------|------|
| **FE-CCF-01** | 版式选项仍消费入口 `coverStyleOptions`；CCF 开启时断言仅 Hero Set | P0 | `studio_entry` → `features.js` `renderOptions` |
| **FE-CCF-02** | 当前 `coverOpeningStyle` ∉ Hero Set：展示经典提示（当前版式名 +「可切换到现行三款」）+ 仍可点选三款主菜写回 | P0 | `.preview-sheet__cover-legacy` |
| **FE-CCF-03** | 切换成功后预览 `data-cover-opening` 与 Sheet 选中态一致（沿用现 patch / refresh） | P0 | `syncCoverOpeningStyleInDom` + `aria-pressed` |
| **FE-CCF-04** | 无障碍：三款按钮保持 `aria-pressed`；经典提示进 `aria-describedby`（或等价可读关联） | P1 | `mountCoverStyleControls` |
| **FE-CCF-05** | **不做** Recommend-3 面板、不做第四款主入口 | 约束 | NG-CCF-02 |

验收映射：FE-CCF-01/02/03 → **AC-CCF-07** / **AC-CCF-10**；FE-CCF-05 → **AC-CCF-07**。

### 8.2 一键撤回（D-CCF-11）

| 项 | 合同 |
|----|------|
| **总闸** | `config.yaml` → `cover_craft.enabled`（默认 `true` 以启用本主题） |
| **环境覆盖** | `TRAVELOGUE_COVER_CRAFT=0` / `false` / `off` → 强制关闭（优先于 yaml） |
| **关闭后恢复** | ① `list_assignable_styles()` / Studio 选项恢复为五款 active（含 `scroll-head` / `contact-stamp`）② 渲染 HTML **不**写 `data-cover-craft` ③ Studio 不展示 FE-CCF-02 经典提示分支 ④ craft CSS 增量选择器不生效 |
| **不撤回** | 已写入 trip 的 `meta.coverOpeningStyle` 历史值；文档正文（需另改） |
| **操作** | 改配置或设环境变量后 **重启 Studio / 渲染进程** 即生效（进程内 config cache） |

```yaml
# 一键撤回 CCF（恢复实施前可分配五款 + 关闭 craft CSS 属性）
cover_craft:
  enabled: false
```

---

## 9. 里程碑

| 波次 | 交付 | 出门标准 |
|------|------|----------|
| **W0** | 本文评审；确认 Hero Set；配菜 retired 方案签字 | Conditional Go |
| **W1** | `veil-footer` craft + fit 金样；配菜退出分配；dogfood 截图 | ✅ 2026-08-11（见 acceptance-records/ccf-craft-focus-dogfood-2026-08-11.md） |
| **W1b** | `band-cut` craft token（模板 CSS）+ CAL 抽检待人工 | 🟡 token 已合入；Studio/CAL 手测可续 |
| **W2** | `folio-overlap` craft token（模板 CSS） | 🟡 token 已合入；盲评前可再微调 |
| **W3** | 三款汇总盲评；过门则默认生产 | 待办 |
| **W3b** | 文档/schema 描述纠偏；dogfood N≥5 | 🟡 schema + Delta 注记已改 |

---

## 10. 验收标准（AC-CCF-*）

| ID | 验收项 |
|----|--------|
| **AC-CCF-01** | `list_assignable_styles()` **恰好 3 款**且为 Hero Set；新建 trip 不会写入配菜 id |
| **AC-CCF-02** | 旧 trip 若为 `scroll-head`/`contact-stamp`/其他 retired，渲染不回归、不强制改写 |
| **AC-CCF-03** | `veil-footer` token/规则变更表 + ≥3 组真实前后截图入库 |
| **AC-CCF-04** | `band-cut` / `folio-overlap` 同上（各 ≥3 组） |
| **AC-CCF-05** | 三款各 ≥3 条 fit 金样单测通过 |
| **AC-CCF-06** | 三款 ×（无艺术字 / 有艺术字）各至少 1 个真实 trip 目视：贴纸不溢出装帧件、不挡脸 |
| **AC-CCF-07** | CCF 开启时 Studio 选择器仅三款；无 Recommend-3 新面板（FE-CCF-01/05） |
| **AC-CCF-08** | README / Delta 导读 / schema 描述不再宣称「十款可分配」 |
| **AC-CCF-BLIND** | 升档后 vs 升档前盲评偏好 ≥55%（协议可复用 CAL 盲评结构，样本须含三款） |
| **AC-CCF-09** | 抽查默认路径无「AI 生成风景封面」入口 |
| **AC-CCF-10** | 历史配菜 trip：经典提示可见；可一键切到 Hero Set 且预览 DOM 同步（FE-CCF-02/03） |
| **AC-CCF-11** | `cover_craft.enabled=false`（或 env=0）后：可分配恢复五款、无 `data-cover-craft`、无经典提示分支 |

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 收至 3 款后个别构图无好皮 | 加强 fit；允许用户换图优先于换已退场版式 |
| craft 改丑或过重 | 盲评门禁；flag 回滚 token |
| 与 CTS/CAL 排期争抢 | CCF 像素优先；CTS hint 可并行但不挡 W1 |
| 历史配菜用户困惑 | 只读提示 + 一键切到现行三款 |

### 11.2 开放问题（OQ-CCF-*）

| ID | 问题 | 默认倾向 |
|----|------|----------|
| **OQ-CCF-01** | 配菜用 `retired` 还是保留 active 但 `assignable=false`？ | **实施裁定：catalog 保持 active，运行时用 `cover_craft.enabled` 过滤可分配**（便于一键撤回；与「永久 retired」等价于用户面，但可回滚） |
| **OQ-CCF-02** | Hero Set 是否允许日后把 `contact-stamp` 换入替换某一款？ | 仅产品书面改 D-CCF-01；本 V1 不预留第四坑位 |
| **OQ-CCF-03** | 盲评评委人数 / 样本数 | Kickoff 定；建议 ≥12 对、单一评委协议可先对齐 CAL |
| **OQ-CCF-04** | `coverCraftVersion` 写入 trip 还是仅 telemetry？ | V1 仅 telemetry + CSS 注释版本，减少 schema churn |

---

## 12. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-08-11 | 初稿：取代 CEC；目标改为 3 款主菜 craft + fit + CAL 收口；否决扩版式与 Recommend-3 |
| **v0.2.0** | 2026-08-11 | 补 §8.1 FE-CCF-*、§8.2 / D-CCF-11 一键撤回；AC-CCF-10/11；OQ-CCF-01 裁定为 flag 过滤 |

---

## 附录 A · 相对 CEC / Punk 的去留

| 项 | 态度 |
|----|------|
| 真照片默认、禁止整图假风景 | **保留**（AC-CCF-09） |
| 不新增第 11 款皮肤 | **保留并强化**为只养 3 款 |
| Style Covenant 全字段 / Recommend-3 | **不做**（本文 NG-CCF-02） |
| `image_text_relationship` 作设计 brief | 可写在 craft 验收记录里，**不**先做引擎字段 |
| Punk 巨字透视 / 24 风格库 | **否决**为产品方向 |
| 标题三层 / 字数档 | **归 CTS**；CCF 只在主菜排版里遵守，不重开主题 |

---

## 附录 B · 代码挂点（实施备忘）

| 用途 | 路径 |
|------|------|
| 可分配集合 | `cover_engine/registry.py`（flag 过滤）· `cover_engine/craft.py`（Hero Set）· `catalog.py` |
| 一键撤回 | `config/cover_craft.py` · `config.yaml` `cover_craft.enabled` · `TRAVELOGUE_COVER_CRAFT` |
| 适图 | `travelogue/cover_engine/fit.py` · `joint.py` |
| 视觉主战场 | **`templates/visual-journal/journal.css`**（基线 token + `html[data-cover-craft="ccf-v1"]` 增量；`trips/linzhi/journal.css` 非 render 真相源） |
| DOM | `templates/visual-journal/partials/cover-opening.hbs`（尽量不改结构） |
| 艺术字 | `travelogue/cover_engine/title_art/{whitelist,engine,render_b}.py` |
| Studio 选择器 | `cover_engine/studio.py` · `templates/studio/preview-toolbar/features.js` |
| 装配 | `travelogue/render/assemble.py`（`data-cover-craft`）· `web/studio_entry.py` |
