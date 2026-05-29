# Travelogue · Phase 4 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.4.3-PHASE4 |
| **状态** | Draft · 开发准入（Intent + 极易用 · UX 规格冻结 · 负责人评审缺口已补） |
| **UX 线框** | [wireframes/studio-import-sheet-v1.html](./wireframes/studio-import-sheet-v1.html) |
| **Phase 4 代号** | 「编辑意图」— 杂志编辑心智 · 可选前置输入 · G1 产品化 |
| **前置条件** | [PRD-PHASE2.md](./PRD-PHASE2.md) M8–M10 可用；[PRD-PHASE3.md](./PRD-PHASE3.md) M12+ 建议已合入（聚类 hint 可叠加，非硬依赖） |
| **交付形态** | 用户**可选**提供书名、感受、双文件夹精选、旅行计划、章级记忆点 → Studio/预览**可见反馈** → 策展/叙事/版式**可解释消费**；**不**增加强制填表步骤 |
| **关联文档** | [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md)、[PRD-EXPERIENCE-附录A-精选上传.md](./PRD-EXPERIENCE-附录A-精选上传.md)、[AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md)、[DATA-MODEL.md](./DATA-MODEL.md)、[NARRATIVE-PROMPTS.md](./NARRATIVE-PROMPTS.md)、[智能排版V2.md](./智能排版V2.md)、[IMPLEMENTATION-PHASE4.md](./IMPLEMENTATION-PHASE4.md)、[ACCEPTANCE-PHASE4.md](./ACCEPTANCE-PHASE4.md) |
| **更新日期** | 2026-05-29 |

> **命名说明**
>
> - 本文 **产品 Phase 4** = 「编辑意图与 G1 体验」，聚焦 **杂志感 / 智能感叙事**，不是电子相册式「只选文件夹」。
> - [SHARING.md](./SHARING.md) 中的 **分享轨道 Phase 4**（小程序鉴权 HTML）为**独立规划**，**不在**本文范围；实施时称 **Phase 4-INTENT** 或 **P4-Intent**，避免与分享 Phase 4 混淆。

---

## 1. 背景与问题陈述

### 1.1 Phase 1–3 已解决什么

| 阶段 | 能力 | 用户价值 |
|------|------|----------|
| **MVP** | ingest → curate → narrate → render | 文件夹 → 杂志风 HTML |
| **Phase 2** | Studio + 服务端长图 + 非开发者入口 | 选文件夹 → 预览 → 微信长图 |
| **Phase 3** | geo/scene 聚类增强 curate | 章/屏序更贴旅程与场景 |

### 1.2 Phase 4 要解决的断裂点

| 断裂 | 现状 | Phase 4 目标 |
|------|------|--------------|
| **断裂 D · 入口心智** | Studio 默认 hidden `trip-title` / `trip-place`；用户以为「扫文件夹」 | 用户感到 **「在编一本有名字的杂志」** |
| **断裂 E · 意图未接通** | `userTier` 双文件夹、附录 A 规则 **已实现**，但 UI **未教会**用户 | 精选/素材语义可见；导入后有 **量化反馈** |
| **断裂 F · 感受只进文案** | `userNotes` / `memoryAnchors` 在 schema + narrate brief 中，**无 Studio/G1 UI**；**不参与** curate | 可选输入 → **叙事 + 少量可解释策展权重** |
| **断裂 G · G1 工程师化** | `structure_locked`、锚点、改章依赖 **手改 trip.json** | 预览内 **轻量 G1**：章解释 + 锚点 + 「结构 OK / 重生成」 |
| **断裂 H · 计划缺失** | 旅行前计划无法进入管线 | 可选 `.txt/.md` → **结构 hints**（非第二篇游记） |

### 1.3 战略定位（产品叙事）

> **相册帮你找到照片；Travelogue 帮你把一次旅行编成可转发的杂志。**  
> Phase 4 把用户的主观意图（书名、精选、感受、计划、记忆点）变成 **编辑部的简报（Intent Brief）**，让「智能」可被看见、可被推翻，而不是黑盒算法。

**三条原则**（继承 CTO 评审结论）：

1. **全部可选，但填了必有回报**（进度文案、成功页、预览侧栏可见）。  
2. **意图与像素分离**（文字/计划 → JSON；照片 → 文件夹 tier）。  
3. **先结构信号、后文学信号**（精选/计划 → curate；感受/锚点 → narrate；锚点可轻触达 peak 权重）。

### 1.4 与现有实现的关系

| 你的想法 | 代码/文档现状 | Phase 4 动作 |
|----------|---------------|--------------|
| 游记起名 | `meta.title` + import `title` 参数 | Studio **显性输入** |
| 精选 + 素材文件夹 | [附录 A](./PRD-EXPERIENCE-附录A-精选上传.md) · `user_tier.py` | **引导文案** + 成功反馈 + 预览升格 |
| 旅行感受 | `trip.userNotes` + brief 中 `meta.userNotes` | Studio 单行 + 预览可改 + 统一 brief 源 |
| 旅行计划 | 无 | 新增 `intent.travelPlan` + 轻解析 |
| 章级感受 | `chapters[].curation.memoryAnchors` | 预览 **G1 锚点 UI** |
| 地点 | `meta.places` | 可选「主地点」输入（与 title 并列） |

**不重复建设**：ingest 双目录、curate `featured_weight`、tier promote API、`GET /__travelogue/chapter-layout` 解释 — **扩展消费与 UI**，不重写管线。

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-P4-01** | 非开发者理解「精选文件夹」语义 | 5 人访谈：≥4/5 能复述「主图上传 vs 素材上传」 |
| **G-P4-02** | 导入完成页展示 **意图摘要**（书名、精选张数、分段数） | AC-P4-02 自动化 + 截图验收 |
| **G-P4-03** | 提供 `userNotes` 的 trip，hook/图说 **含用户词** 比例 ↑ | **评估协议 P-EVAL**（见下）：≥60% 章节命中 |
| **G-P4-04** | 预览内完成 **0–3 条/章** 记忆锚点并写回 | AC-P4-06 |
| **G-P4-05** | 双文件夹 golden：封面 ∈ featured 率保持 | 附录 A AC-DF-02 不回归 |
| **G-P4-06** | 端到端仍满足 G-P2-01（≤20 分钟成稿） | 意图层 **不增加** 强制步骤 |
| **G-P4-07** | 「不像电子相册」盲评 | **评估协议 P-EVAL**：同一相册无 intent vs 全 intent，胜率 ≥55% |

> **评估协议 P-EVAL（v0.4.3 补 · 统一口径）** — 解决 G-P4-03/07 与 UX-P4-02 口径不一致：
>
> | 项 | 规格 |
> |----|------|
> | **样本** | 3 个种子相册 × {无 intent, 全 intent} = 6 产物；锁定同一 commit 与 config |
> | **评委** | 5 名内部种子用户，**盲评**（不知哪份带 intent） |
> | **G-P4-07 判定** | 每相册 A/B 二选一「更像可转发的杂志」；6 对中 **全 intent 胜 ≥ 55%**（即 ≥ 3.3/6，取 ≥4 对） |
> | **G-P4-03 判定** | 脚本 `scripts/diff_curate.py --intent-keywords`：统计含 `userNotesKeywords` 的章占比 ≥ 60% |
> | **记录** | `docs/acceptance-records/phase4-intent.json`（M19-04）：每对得票 + 关键词命中率 |
>
> ACCEPTANCE 的 **UX-P4-02 改为引用 P-EVAL**，不再用「≥3/5 主观」独立口径。

### 2.2 已拍板产品决策（2026-05-28）

| 决策项 | 结论 | 配置/实现 |
|--------|------|-----------|
| **G1 默认模式** | **模式 A**：导入后自动 `structure_locked` + 继续 narrate/render（与 Phase 2 耗时一致） | `studio.g1_confirm_structure: false`（默认） |
| **G1 进阶模式** | **模式 B**：curate 后停 `structure_draft`，预览内确认后再 narrate | `studio.g1_confirm_structure: true`（设置页/高级） |
| **旅行计划上传** | **方案 A**：与 import 同请求 multipart 字段 `planFile` | 落盘 `source/intent/plan.txt` |
| **首页主路径** | **本机选文件夹 → 自动开始导入**（保留路径粘贴为次级） | 见 §6 |
| **Intent 必填** | **全部可选**；仅杂志名有软默认（文件夹名推断） | 见 §6.2 |
| **面板字段顺序** | **选夹优先（方案 A）**：先选文件夹 → 再确认杂志名 → 可选感受 → import | §6.3 |
| **视觉 Token** | Sheet 与 Hero **统一暖金 CTA**（`studio.css` `--accent`）；不引入 HOMEPAGE 绿色第二套 | §6.12 |
| **预览 IA** | 顶栏极简 + **编辑抽屉**（M16）；屏角 ★ 标精选 | §7.0 |

### 2.3 非目标（Phase 4 明确不做）

- 导入前 **逐张** 挑图 UI（用文件夹 + 预览升格代替）
- 计划 **PDF/截图 OCR**、复杂行程表解析
- **LLM 重排章序** 或 LLM 生成 DOM
- 多模板商城、自由拖拽排版
- 账号体系、云同步、协作
- 强制填写任一意图字段
- [SHARING.md](./SHARING.md) 小程序鉴权（分享轨道 Phase 4）
- 替换 Phase 3 聚类或智能排版 V2 核心算法（仅 **hints 消费**）

---

## 3. 目标用户与场景

### 3.1 Persona（延续 Phase 2）

**Persona A · 普通旅行者** — 愿花 30 秒起名 + 一句话感受；若已整理「精选」文件夹则愿意按引导放置。

**Persona B · 进阶创作者** — 双文件夹 + 计划 txt + 章级锚点；愿在 G1 确认结构后再锁文案。

### 3.2 User Stories

| ID | 作为… | 我想要… | 以便… |
|----|--------|---------|--------|
| **US-P4-01** | 旅行者 | 给游记起一个名字 | 封面与长图第一眼像「一本书」 |
| **US-P4-02** | 旅行者 | 知道可以建「精选」「素材」两个子文件夹 | 我最满意的照片优先上封面和章首 |
| **US-P4-03** | 旅行者 | 用一句话写感受（可跳过） | 标题和图说更像我的旅行 |
| **US-P4-04** | 旅行者 | 导入时看到「已识别 12 张精选 · 3 段行程」 | 感到系统真的「懂」 |
| **US-P4-05** | 旅行者 | 上传旅行计划 txt（可跳过） | 章序更贴近我当初的安排 |
| **US-P4-06** | 旅行者 | 预览里给某一章加 1–3 个记忆词 | 图说带上我的原话 |
| **US-P4-07** | 旅行者 | 预览里确认「章顺序像这次旅行」 | 不用改 JSON |
| **US-P4-08** | 旅行者 | 把某张图「标为精选」 | 重跑排版时优先上屏 |
| **US-P4-09** | 旅行者 | 打开预览直接看到某一章「高潮屏」 | 第一眼惊艳（非封面网格） |
| **US-P4-10** | 进阶用户 | 折叠区写更多备注 / 上传计划 | 不打扰主路径 |

---

## 4. 概念模型 · Intent Brief

### 4.1 `trip.intent`（建议新增对象 · v0.4）

与 `meta` 并存；Studio 写入；管线只读。迁移期 **双写** 兼容旧字段。

```json
{
  "intent": {
    "version": "1",
    "title": "雨后京都",
    "places": ["京都"],
    "userNotes": "带娃慢走，不要导游词",
    "travelPlan": {
      "format": "text",
      "filename": "plan.txt",
      "summary": "D1 大阪 → D2 京都 temple → D3 回程",
      "cities": ["大阪", "京都"]
    },
    "folders": {
      "featuredDetected": true,
      "featuredDir": "精选",
      "materialDir": "素材"
    },
    "submittedAt": "2026-05-28T12:00:00+08:00"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `intent.version` | const `"1"` | ✅ | |
| `intent.title` | string ≤20 | ❌ | 同步 `meta.title` |
| `intent.places` | string[] | ❌ | 同步 `meta.places` |
| `intent.userNotes` | string ≤200 | ❌ | 同步顶层 `userNotes` |
| `intent.travelPlan` | object? | ❌ | 见 §4.2 |
| `intent.folders` | object? | ❌ | ingest 后回填检测结果 |

**兼容规则**：

- 读取优先级：`intent.*` → `meta.*` / `userNotes`（旧 trip）  
- 保存时：Studio PATCH **同时** 更新 `intent` 与 `meta` / `userNotes`

**Schema 版本与迁移（P0 · v0.4.3 补）**：

| 项 | 规格 |
|----|------|
| schema 字段 | `intent` 为 **optional**；`intent.version` 当前固定 `"1"` |
| validate 行为 | 旧 trip **无 `intent` 不报错**（L1 放行）；存在 `intent` 时校验 `version`/`title≤20`/`userNotes≤200`/`places≤? ` |
| migrate-on-load | 复用 P3 `migrate-on-load` 机制（参考 M14-3 `curation.insights` strip）：加载旧 trip 时**不**自动构造 `intent`，仅在首次 Studio PATCH 时落盘，避免污染未编辑 trip |
| 双写收口 | 唯一写入口 `TripService.apply_intent()`（§14 风险缓解）：原子更新 `intent` + 镜像 `meta.title/places` + `userNotes`；**禁止** 其他路径直接写 `intent` |
| 一致性不变量 | `apply_intent()` 后必须满足 `intent.title == meta.title`、`intent.userNotes == trip.userNotes`、`intent.places == meta.places`（由 **AC-P4-09** 守护） |

### 4.2 旅行计划 `travelPlan`

| 项 | 规格 |
|----|------|
| **上传格式** | `.txt` / `.md`，≤ **32KB** |
| **存储** | `trips/{id}/source/intent/plan.txt` |
| **解析** | 规则：提取 ISO 日期、常见「城市/地点」行、列表项；**禁止** LLM 全文改写 |
| **写入** | `intent.travelPlan.summary` ≤200 字；`cities[]` ≤10 项 |
| **消费** | curate：章标题候选、segment 与 geo 冲突时 **用户城市序优先**（fail-open） |
| **叙事** | brief 仅注入 `summary`，禁止照抄计划当正文 |

**City 对齐算法（P1 · v0.4.3 补）** — `planCities[]` 与 geo segment 的 `meta.places` 对齐规则，按序短路：

1. **精确匹配**（去空白、`NFKC` 归一、大小写无关）
2. **别名表**：维护 `travelogue/data/city_aliases.json`（如 `Kyoto↔京都↔きょうと`、`Osaka↔大阪`）；中英/假名互映
3. **包含匹配**：plan city 是 place 子串或反之（如「京都市」⊇「京都」）
4. 全不命中 → 该 city **忽略**（fail-open，不报错）

| 指标 | 目标 |
|------|------|
| golden fixture 城市命中率 | ≥ **90%**（AC-P4-07 正向 fixture） |
| 解析异常（空文件/乱码/超 32KB） | **100% fail-open**，WARN 日志，`intentHints` 不写 city（AC-P4-07b 负向 fixture） |

> 别名表外的生僻地名不强求命中；目标是"对齐则点名、不对齐则静默"，绝不因 plan 导致 curate 失败。

### 4.3 章级 `memoryAnchors`（已有 schema）

| 项 | 规格 |
|----|------|
| 位置 | `chapters[].curation.memoryAnchors` |
| 数量 | 每章 **0–3** 条 |
| 长度 | ≤ **24** 字/条 |
| 消费 | Agent 2 brief（已有）；Phase 4b 可选 peak 权重 +0.05（§8.3） |

---

## 5. 端到端用户旅程

### 5.1 主路径（全部可选）

```
[Studio 首页]
  → 主 CTA「制作我的杂志」→ 打开导入面板
  → ① 选择照片文件夹（本机）
  → ② 确认杂志名（预填文件夹名，可改，约 2s 可跳过)
  → （可选）写给编辑的一句话 · 地点 · plan.txt · 精选说明
  → 自动开始导入（无需「开始」）
  → 面板关闭 · Hero 进入 Importing · 阶段 hint + intent 摘要行
  → 成功 overlay：精选/分段/书名反馈 + 打开预览
  → 预览默认深链 peak 屏（可配置）
  → （可选）G1 条：确认结构 · 填记忆锚点 · 标为精选
  → （可选）生成杂志文案 / 保存长图
[结束]
```

### 5.2 Wow 时刻（验收必测）

| 时刻 | 触发条件 | 用户可见 |
|------|----------|----------|
| **W1** | ingest 完成 | 「已为《雨后京都》识别 3 段行程 · 12 张精选将优先用于封面」 |
| **W2** | 打开预览 | 首屏为 **peak 屏** 或第一章高潮屏（非空白 cover） |
| **W3** | 展开「为什么这样分章？」 | 可读解释 + 与用户 plan 城市一致时点名 |
| **W4** | 保存锚点后 narrate | 图说出现锚点词（抽检） |

---

## 6. Studio 首页 · 极易用交互（M15 + M15-HP）

> 基线：[PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md) v3（影像优先 Hero）。  
> Phase 4 **不重做** v3 IA，而是：**一个主操作闭环 + 导入面板收拢复杂度 + Intent 嵌进主路径**。  
> 首页专项缺口见 HOMEPAGE **HP-GAP-15～20**（§6.9 对照）。

### 6.1 极易用设计原则（冻结）

| # | 原则 | 落地 |
|---|------|------|
| E1 | **一次只做一件事** | 首屏主按钮只有「制作杂志」语义，不出现三种导入并列 |
| E2 | **能点就不打** | 默认 `pick-folder` → 自动 import；路径粘贴收进「更多方式」 |
| E3 | **可选但不挡路** | 杂志名/感受在导入面板内，可跳过；缺省用文件夹名 |
| E4 | **每步有反馈** | Toast / 进度副行 / 成功摘要；禁用态可见（选择器已打开） |
| E5 | **回访 5 秒继续** | 最近一篇大卡「继续编辑」≥ Hero 次要 CTA 视觉权重 |

**衡量**：对齐 HOMEPAGE **G-HP-01**（10 秒理解）、**G-HP-02**（5 秒继续）。

### 6.2 信息架构（Phase 4 目标态）

**空态 IdleEmpty**

```
[Topbar]
[Hero 情感标题 + 一句产出承诺]
[主 CTA：制作我的杂志]  → 打开「导入面板」sheet（见 6.3）
[次级一行：试用示例 · 帮助]
[样例长图 E]
[页脚]
```

**回访态 IdleReturning**

```
[Topbar]
[Hero hybrid]
  左（≈60%）：继续编辑 · 最近 trip 大卡（封面 16:9 · stale→「更新长图」主钮）
  左下：+ 新建杂志（ghost）→ 打开导入 panel
  右（≈40%）：次近 2–3 张 trip 小卡（勿与「继续编辑」抢焦点）
[全部游记 F]
```

**路径输入框** 从 Hero 常驻 → 移入 panel **「其他导入方式」** `<details>`（HP-GAP-01/16）。

### 6.3 导入面板 · `studio-import-sheet`（核心交互 · M15-HP）

**权威线框**：[studio-import-sheet-v1.html](./wireframes/studio-import-sheet-v1.html)（Tab：空态 panel · 选夹后确认 · 回访大卡 · 错误态）。

**触发**：空态「制作我的杂志」、回访「+ 新建杂志」、样张「用我的照片做一篇」、试用示例（Intent 默认名，直达选夹）。

**形态**：

| 属性 | 规格 |
|------|------|
| 容器 | Hero 底部半屏 sheet，`max-height: min(72dvh, 520px)` |
| 背景 | `var(--paper)` #f7f4ee，顶缘圆角 16px |
| 遮罩 | `rgba(0,0,0,.45)`；Importing 时不可点穿关闭 |
| 把手 | 顶中 40×4px 装饰条（M15 不做拖拽关闭） |
| 标题 | `id="studio-sheet-title"`：**制作杂志** · `role="dialog"` `aria-modal="true"` |
| 关闭 | 右上 × · `Esc` · 焦点陷阱 |

**面板内顺序（方案 A · 选夹优先 · 冻结）**：

| 步骤 | 控件 | 说明 |
|------|------|------|
| **1** | **选择照片文件夹**（主按钮） | `pick-folder`；disabled 态「正在打开文件夹…」 |
| **2** | **确认区** `#studio-sheet-confirm`（选夹后显示） | 杂志名预填 · **开始制作** · 可选感受 |
| **3** | 精选 **一行摘要**（常显） | §6.4 |
| **4** | `<details>` **帮你排得更好（可选）** | 地点 · plan · 精选图示 |
| **5** | `<details>` **其他导入方式** | 路径 · 浏览 · 开始 · ≤200MB 上传 |

**确认区**：

| 控件 | 说明 |
|------|------|
| `trip-title` | **给这本杂志起个名字**；预填文件夹 basename（≤20） |
| **开始制作** | 触发 import |
| **跳过，用默认名** | 用预填名立即 import（等价主路径快捷） |
| `trip-feeling` | **写给编辑的一句话**（可选，≤200） |

> 选夹后 **不** 静默 import；用户点「开始制作」或「跳过」后进入 Importing（仍无需路径栏二次「开始」）。

**折叠**：全局最多 **2** 个 `<details>`（§6.5/6.6）。

### 6.3.1 导入 panel × 首页状态机（冻结）

| 首页状态 | panel | Hero |
|----------|-------|------|
| `IdleEmpty` / `IdleReturning` | 可打开 | 空态/回访 |
| `Importing` | **强制关闭** | `#studio-hero-importing` |
| `FirstSuccess` | 关闭 | Success overlay |
| `Failed` | 可打开（保留 Intent） | Failure |

取消导入 → 回 Idle + panel 恢复 Intent。

### 6.4 双文件夹 · 极易懂说明（M15-HP）

**常显一行**：

> 相册里若有 **「精选」** 和 **「素材」** 两个子文件夹，封面会优先用精选（建议 8–20 张）。

**树形图示**放在「帮你排得更好」展开区内（§6.5）。无子文件夹不阻断选夹。

### 6.5 「帮你排得更好」与计划（M15 / M18）

`<details summary="帮你排得更好（可选）">`：主地点 · `plan-file` · 精选树形图。  
文案：「行程单只帮我们分章，**不会公开发布**。」

### 6.6 主 CTA 与 pick-folder（M15-HP）

| 场景 | 行为 |
|------|------|
| **制作我的杂志** | 打开 panel |
| **选择照片文件夹** | pick-folder → 展开确认区 |
| **开始制作 / 跳过** | `startImport` → **关闭 panel** → Hero Importing |
| **+ 新建杂志** | 打开 panel |
| **继续编辑**（大卡） | `GET .../entry` → peak 深链预览 |
| **stale** | 大卡主钮 **更新长图** |

**Coach mark（F-P4-HP-06）**：① 高亮 Hero「制作我的杂志」② panel 内「选择照片文件夹」；`coachImportV1=2`；可跳过；`prefers-reduced-motion` 无脉冲动画。

### 6.7 Intent 数据流

- `blur` / panel 关闭 → `sessionStorage.studioIntent`（`title`、`place`、`feeling`）。  
- `startImport` body：`title`、`place`、`userNotes`（← feeling）、multipart `planFile`（若有）。  
- 去掉 hidden 的 `trip-title` / `trip-place`（迁到 panel）。

### 6.8 导入进度 · `stageHint` 增强（M15）

在现有 4 stage 下增加 **全局副行** `intentLine`（由 worker 在 ingest 完成后写入 Job.result）：

| 字段 | 示例 |
|------|------|
| `result.intentLine` | `《雨后京都》· 精选 12 张 · 行程 3 段` |
| `result.featuredCount` | number |
| `result.segmentCount` | number |
| `result.tierMode` | `auto \| single` |

前端：Importing overlay 在 `stage=curate` 后显示 `intentLine`。

### 6.9 首页极易用 · 增量需求表（M15-HP）

| 需求 ID | 描述 | 验收 |
|---------|------|------|
| **F-P4-HP-01** | 导入 panel sheet；主 CTA 打开 panel | 空态 10 秒测试能找到选文件夹 |
| **F-P4-HP-02** | 选夹 → 确认区 → 开始制作；无路径栏「开始」 | ≤4 次点击见进度（含系统选目录） |
| **F-P4-HP-03** | 路径栏收入「更多方式」 | G-HP-03 走查 |
| **F-P4-HP-04** | 杂志名从文件夹名预填 | pick 后 title 可见且可改 |
| **F-P4-HP-05** | 回访「继续编辑」大卡 + stale「更新长图」 | G-HP-02 |
| **F-P4-HP-06** | 两步 coach mark（Hero CTA → panel 选夹） | `coachImportV1` |
| **F-P4-HP-07** | `/trips` 加载骨架屏 | HP-GAP-08 |
| **F-P4-HP-08** | 试用后 panel +「现在用你的照片」 | HP-GAP-13 |
| **F-P4-HP-09** | panel 底「？」链到照片准备（附录 B） | HP-GAP-10 |
| **F-P4-HP-10** | panel 底：每文件夹一篇新游记 | HP-GAP-11 |
| **F-P4-HP-11** | Importing 时 panel 不可打开 | §6.3.1 |
| **F-P4-HP-12** | 字段行内错误（title 超长等） | 附录 B |

### 6.10 成功 Overlay 文案模板（M15）

| 条件 | `#studio-success-msg` 模板 |
|------|---------------------------|
| 有精选 | `《{title}》已生成 · {featured} 张精选已用于封面与章首` |
| 无精选 | `《{title}》已生成 · 可在预览中标记精选照片` |
| 有分段（`segmentCount ≥ 1`） | 追加 ` · {segmentCount} 段行程` |
| **无分段（`segmentCount == 0`，如无 GPS）** | **不追加行程段**；仅显示精选/默认句，**不**显示「0 段行程」 |

**视觉摘要条**（Success 内，可选）：chips `行程 3 段` · `精选 12 张`（来自 `result`）；**`segmentCount==0` 时不渲染行程 chip**。

**打开预览**（M15b）：

- URL：`GET /__travelogue/trips/{id}/entry` → `previewUrl` 含 `#screen-{peakScreenId}`  
- 主按钮文案：**先看杂志排版**（非泛泛「打开预览」）  
- **倒计时**：有 `intentLine` 时 **8s**；否则 5s；`localStorage.firstPreviewDone` 后默认 **不自动跳转**（仅手动）  
- 次按钮：**留在首页**

### 6.11 首页功能需求（汇总）

| 需求 ID | 描述 | 验收 |
|---------|------|------|
| **F-P4-STU-01** | 导入 panel 内 Intent 可编辑 | F-P4-HP-01/04 |
| **F-P4-STU-02** | import 携带 title/place/userNotes/planFile | trip.json 正确 |
| **F-P4-STU-03** | 双文件夹说明（折叠图示） | F-P4-HP 截图 |
| **F-P4-STU-04** | 成功页 intent 反馈 | AC-P4-02 |
| **F-P4-STU-05** | plan multipart 方案 A | plan.txt 落盘 |
| **F-P4-STU-06** | sessionStorage 恢复 intent | 刷新不丢 |
| **F-P4-STU-07** | 打开预览 peak 深链 | AC-P4-03 |
| **F-P4-STU-08** | 选夹 → 确认 → 开始制作 | F-P4-HP-02 |
| **F-P4-STU-09** | sheet 视觉符合 §6.12 | 对照线框 |

### 6.12 P4 视觉与组件规范（冻结）

与已实现 `templates/studio/studio.css` 对齐；**不**采用 [PRD-STUDIO-HOMEPAGE](./PRD-STUDIO-HOMEPAGE.md) §6.14 绿色 `#3d6b5a` 第二套。

| Token / 组件 | 值 | 用途 |
|--------------|-----|------|
| `--accent` | `#d2a657` | 主 CTA 填充 · Hero 与 sheet **一致** |
| `--accent-ink` | **见下（对比度定稿）** | 金钮**前景字**色 |
| `--paper` | `#f7f4ee` | sheet 背景 |
| `--ink` | `#0d0d0d` | sheet 正文 |
| 主按钮 | `studio-btn--primary` + `--shadow-btn` | 选夹 · 开始制作 |
| 回访大卡 | `--paper` 底 · 1px `--line` · 金点缀描边 | 视觉权重 > ghost 新建 |
| sheet 内输入 | 高 44px · radius `--radius-sm` | 触屏友好 |

> **⚠️ P0 对比度门禁（v0.4.3 补 · 阻塞 M15-HP）**
>
> `--accent #d2a657` 上**白字**实测对比度约 **1.9:1**，**远低于** §6.13 要求的 4.5:1，直接违反 a11y。开工金钮前**必须**二选一定稿（由 **AC-P4-A11Y-01** 守护）：
>
> | 方案 | 前景字 | 背景 | 实测对比 | 取舍 |
> |------|--------|------|----------|------|
> | **A（推荐）** | `--ink #0d0d0d` 深字 | `--accent #d2a657` | ≈ **9.6:1** ✅ | 保留暖金，改深色字 |
> | **B** | 白字 `#fff` | 加深金 `#8a6a1f` | ≈ **5.0:1** ✅ | 保留白字，金变暗 |
>
> 默认采用 **方案 A**（`--accent-ink: #0d0d0d`），既守暖金主视觉又过 4.5:1。其余正文/链接对比沿用 §6.13。

### 6.13 无障碍与键盘（M15-HP）

- `aria-labelledby` → `#studio-sheet-title`  
- 焦点顺序：§6.3  
- `#studio-stage` / `#studio-error` 保持 `aria-live`  
- 浅色 sheet 正文对比度 **≥ 4.5:1**；金钮白字需实测 **≥ 4.5:1**  
- `prefers-reduced-motion: reduce`：关闭 coach 脉冲与 bar 动画

### 6.14 微文案

权威表见 **附录 B**；实现不得自创 error 码英文面向用户。

---

## 7. 预览页 · Studio Chrome / Toolbar（M16–M17）

> 注入规则不变：仅 `index.html` / `index-mobile.html`；**不**注入 `index-longshot.html`。

### 7.0 预览信息架构（冻结 · M16 / M16b）

**顶栏（始终可见，≤4 项）**：

```
[← 工作台]  [杂志名 · 可编辑]  [保存长图 · 主]  [⋯]
```

**`⋯` 菜单 / 次栏 Tab（M16 二选一，推荐 drawer）**：

| 入口 | 内容 |
|------|------|
| **编辑**（drawer） | 写给编辑的一句话 · 记忆锚点 chip · 标为精选说明 |
| **结构**（drawer） | G1 条（模式 A 说明 / 模式 B 阻塞）· 为什么这样分章？ · 重新生成结构 |
| **生成文案** | 原 toolbar 项，从顶栏移至菜单或保留次位 |

**禁止**：顶栏同时堆 7 类能力（原 §7.1 草案）。

**屏级「标为精选」**：当前 `layout-screen` 焦点图 **右下角 ★**（`aria-label="标为精选"`）；**不用**右键菜单。点击 → `promote-tier` → toast → 可选「应用排版」。

### 7.1 组件分期

| 里程碑 | 交付 |
|--------|------|
| **M16** | 顶栏精简 · 杂志名 inline · ★ 精选 · peak 入口不变 |
| **M16b** | **编辑/结构 drawer**（复用 sheet 样式）· present「仅精选」 |

### 7.2 杂志名 inline 编辑（M16）

| 项 | 规格 |
|----|------|
| 展示 | `meta.title`；点击变 input |
| 保存 | `POST /__travelogue/save-copy` patches：`[{ "op": "replace", "path": "/meta/title", "value": "..." }]` 同时 patch `/intent/title` |
| 限制 | ≤20 字；校验失败 toast |

### 7.3 「标为精选」（M16）

| 项 | 规格 |
|----|------|
| 入口 | 屏角 **★**（§7.0）；drawer 内说明文案 |
| API | `POST /__travelogue/promote-tier` |
| 反馈 | toast「已标为精选 · 点应用排版后生效」 |
| 后续 | drawer/条内 **应用排版** → rerender |

### 7.4 G1 · 结构确认条（M17）

**显示条件**：`pipeline.status === structure_draft`（Studio 默认 pipeline 若自动 lock，则 **改为** `structure_draft` 停止并等待用户，见 §8.1）。

| 控件 | 行为 |
|------|------|
| **「章节顺序 OK」** | `PATCH` pipeline → `structure_locked`；启用 narrate（若尚未） |
| **「重新生成结构」** | 确认对话框 → `POST /__travelogue/curate` job（force） |
| **「为什么这样分章？」** | 已有 explain；补充 plan/geo 来源标签 |

### 7.5 章级记忆锚点（M17）

| 项 | 规格 |
|----|------|
| UI | 当前章 sidebar / 底部 drawer：3 个 chip input |
| 保存 | `save-copy` patch `/chapters/{i}/curation/memoryAnchors` |
| 提示 | 「短词即可，会写进图说，不会瞎编」 |
| narrate | 保存后可提示「重新生成文案」 |

### 7.6 全局感受编辑（M16）

| 项 | 规格 |
|----|------|
| 位置 | **编辑 drawer** → **写给编辑的一句话** |
| 控件 | textarea ≤200 |
| 保存 | patch `/userNotes` + `/intent/userNotes` |

### 7.7 预览功能需求

| 需求 ID | 描述 | 验收 |
|---------|------|------|
| **F-P4-PRV-01** | 杂志名 inline 保存 | title 更新并重渲染 |
| **F-P4-PRV-02** | ★ promote-tier | featured 标记 |
| **F-P4-PRV-03** | G1 结构（drawer/条） | 模式 A/B |
| **F-P4-PRV-04** | 记忆锚点 0–3/章 | schema 校验 |
| **F-P4-PRV-05** | chapter-explain 含 intent 来源 | plan/geo 标签 |
| **F-P4-PRV-06** | peak 深链入口 | 首屏非空 |
| **F-P4-PRV-07** | 顶栏 ≤4 项；编辑/结构进 drawer | M16b 走查 |

---

## 8. 后端与管线（M15–M19）

### 8.1 Pipeline 状态策略（M17 · 已拍板）

| 模式 | 行为 | 默认 |
|------|------|------|
| **A** | import 后自动 `structure_locked` + narrate + render | **`studio.g1_confirm_structure: false`** |
| **B** | curate 后停 `structure_draft`；预览 G1 确认后再 narrate | 高级设置开启 |

预览内 G1 条在模式 A 下为 **说明性**（「章节已按行程排好，可在预览中改字与锚点」）；模式 B 下为 **阻塞性**（未确认不可 narrate）。

### 8.2 Import API 扩展

**`POST /__travelogue/import`** JSON 增加：

| 字段 | 类型 | 说明 |
|------|------|------|
| `userNotes` | string? | ≤200 |
| `planText` | string? | 小文件可直接 POST；大文件用 multipart `planFile` |

Worker：写入 `intent` + `userNotes`；解析 plan → `intent.travelPlan` + `curation.intentHints`（见下）。

### 8.3 Curate 消费 intent（M18–M19）

新增只读 hints（curate 写入或 ingest 后写入）：

```json
"curation": {
  "intentHints": {
    "planCities": ["大阪", "京都"],
    "userNotesKeywords": ["带娃", "慢走"],
    "featuredBoost": true
  }
}
```

| 信号 | 规则消费 | fail-open |
|------|----------|-----------|
| `planCities[]` | 章 `title` 候选优先匹配；与 geo segment 冲突 → 城市序按 plan | 无 plan 则忽略 |
| `userNotesKeywords` | 含「高潮/最难忘/day N」→ 对应 segment `arcSegment=peak` 权重 +0.1 | 无匹配则忽略 |
| `featured` | 已有附录 A | — |
| `memoryAnchors` | M19：章内选图 +0.05 若 tags/place 命中锚点子串 | 无匹配忽略 |

**禁止**：LLM 重排 `chapters[].order`。

### 8.4 Narrate brief 统一（M15）

`build_meta_brief` / `build_chapter_brief`：

- `userNotes` 源：`trip.userNotes` ?? `intent.userNotes`  
- 增加 `intent.travelPlan.summary`（若有）  
- `memoryAnchors` 保持

### 8.5 新增 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/__travelogue/trips/{tripId}/entry` | `{ previewUrl, peakScreenId, intentSummary }` |
| `PATCH` | `/__travelogue/trips/{tripId}/intent` | 更新 intent/meta/userNotes（经 `apply_intent()`） |
| `PATCH` | `/__travelogue/trips/{tripId}/pipeline` | G1：`structure_locked` |
| `POST` | `/__travelogue/trips/{tripId}/curate` | 重新策展 Job（可选） |

**`peakScreenId` 来源与 fallback（P1 · v0.4.3 补）** — 解析链按序短路，**保证非空**：

1. **layout peak**：若某 `chapters[].screens[]` 标 `arcSegment == "peak"`（智能排版 V2 / curate arc），取其首个含图屏的 `screenId`
2. **scene cluster 高潮**：否则取最大 scene cluster（Phase 3）所属章的首个内容屏
3. **首个内容屏**：否则取全文第一个**非 cover、含图**的屏
4. **cover 兜底**：极端情况（仅封面）回退 cover 屏；此时 `entry.peakScreenId` 仍返回但前端深链等价于打开首屏

> 不依赖 Phase 3：无 scene cluster 时走 1→3→4，仍满足 W2「首屏非空白 cover」。`entry` 计算为**只读纯函数**，不改 trip.json。

### 8.6 Schema 变更

- `schemas/trip.schema.json`：`intent` 对象（optional）  
- `curation.intentHints`（optional）  
- `validate_trip` L1 同步

---

## 9. 阅读体验协同（Folio / Present）

| 项 | Phase 4 行为 |
|----|--------------|
| **featured-grid** | 有 featured ≥8 时，cover 后插入（附录 C 已有） |
| **present · 仅精选** | toolbar 增加「放映精选」；`featuredOnly=true`（PRD-EXPERIENCE E6 对齐） |
| **longshot** | 首屏 card 含 `meta.title` + hook；验收截图 |

---

## 10. 里程碑与交付顺序

| 里程碑 | 范围 | 依赖 |
|--------|------|------|
| **M15** | 导入 panel + Intent + 自动 import + 进度/成功反馈 | Phase 2 Studio |
| **M15-HP** | 首页极易用（路径折叠、回访大卡、coach、骨架屏） | M15 panel |
| **M16** | 预览：顶栏精简 · 杂志名 · ★ 精选 · peak 深链 | M15 |
| **M16b** | 预览：编辑/结构 drawer | M16 |
| **M17** | G1 结构条 + memoryAnchors UI + pipeline 模式 B | M16 |
| **M18** | plan.txt 上传 + 规则解析 + curate hints（城市） | M15 |
| **M19** | userNotes 关键词 + anchors → 轻权重；盲评 | M18 |

详见 [IMPLEMENTATION-PHASE4.md](./IMPLEMENTATION-PHASE4.md)。

---

## 11. 验收标准

完整条目见 [ACCEPTANCE-PHASE4.md](./ACCEPTANCE-PHASE4.md)。

| ID | 通过条件 |
|----|----------|
| **AC-P4-01** | 导入 panel 选夹→确认区可见；import 后 `meta.title` 一致 |
| **AC-P4-02** | 双文件夹 trip 成功页含精选张数 |
| **AC-P4-03** | 预览打开含 `#screen-*` peak 深链 |
| **AC-P4-04** | `userNotes` 进入 narrate brief 且 stub/LLM 输出含关键词（fixture） |
| **AC-P4-05** | 附录 A AC-DF-02/03 不回归 |
| **AC-P4-06** | 预览写入 memoryAnchors 持久化并通过 schema |
| **AC-P4-07** | plan.txt 城市序影响章标题（golden fixture，城市命中 ≥90%） |
| **AC-P4-07b** | plan 异常（空/乱码/超 32KB）100% fail-open，不写 city hints |
| **AC-P4-08** | `g1_confirm_structure: false` 时行为与 Phase 2 等价（NR-P4-01） |
| **AC-P4-09** | `apply_intent()` 后 `intent.title==meta.title` ∧ `intent.userNotes==trip.userNotes` ∧ `intent.places==meta.places`（双写一致性 · §4.1） |
| **AC-P4-A11Y-01** | 金钮前景/背景对比 ≥4.5:1（§6.12 定稿色）；sheet 正文 ≥4.5:1；焦点陷阱 + `Esc` 关闭 + `reduced-motion` 无脉冲（§6.13） |

---

## 12. 错误与边界

| 情况 | 行为 |
|------|------|
| 仅单文件夹 | 正常导入；提示可预览升格精选 |
| plan 解析失败 | WARN；忽略 hints |
| title 空 | 回退「我的旅途」 |
| title >20 | 字段下**行内红字**（附录 B）；截断 + 后端校验 |
| panel 打开时 Importing | 忽略 open；toast「正在制作中」 |
| G1 未确认即点 narrate | toast「请先确认章节顺序」 |
| structure_locked 后改锚点 | 允许；仅 patch 锚点，不自动 relayout |

---

## 13. 指标与 telemetry（本地）

写入 `trips/{id}/runs/studio-intent.json`（可选）：

| 字段 | 用途 |
|------|------|
| `hasUserNotes` | 漏斗 |
| `featuredCount` | 附录 A 采纳率 |
| `g1Confirmed` | G1 模式 B |
| `anchorCount` | 锚点使用 |
| `planUploaded` | 计划上传率 |

**不上传云端**（本地优先）。

---

## 14. 风险与缓解

| 风险 | 缓解 |
|------|------|
| G1 打断「3 分钟见预览」 | 模式 A 配置默认；模式 B 面向进阶 |
| 双写 intent/meta 不一致 | TripService 单一 `apply_intent()` |
| plan 解析错城 | fail-open；explain 显示「参考行程单」 |
| 意图层加重测试矩阵 | 2 套 intent golden + NR-P4-01 |

---

## 15. 文档与代码锚点

| 域 | 路径 |
|----|------|
| Studio UI | `templates/studio/studio.html` · `studio.js` · `studio.css` |
| 预览工具栏 | `templates/studio/preview-toolbar.js` |
| Import | `travelogue/web/studio_routes.py` · `studio_pipeline.py` |
| Tier | `travelogue/media/user_tier.py` · `web/tier_patch.py` |
| Brief | `travelogue/services/narrative_brief.py` |
| Curate | `travelogue/curation/curate.py` · `curate_scoring.py` |
| Explain | `travelogue/curation/chapter_explain.py` |
| Schema | `schemas/trip.schema.json` |

---

## 附录 A · UX 线框与交付物

| 交付物 | 路径 | Tab / 态 |
|--------|------|----------|
| 导入 panel v1 | [wireframes/studio-import-sheet-v1.html](./wireframes/studio-import-sheet-v1.html) | 空态 · 选夹后确认 · 回访大卡 · 错误 |
| 首页 v3（基线） | [wireframes/studio-homepage-photo-first-v3.html](./wireframes/studio-homepage-photo-first-v3.html) | 实现对照 |

M15-HP **完成定义**：panel 四态线框与 `studio.css` token 对照表签字（设计/产品）。

---

## 附录 B · 微文案与错误态（用户可见）

| 场景 | 文案 |
|------|------|
| 杂志名占位 | 给这本杂志起个名字 |
| 感受占位 | 写给编辑的一句话（可选） |
| 感受 label | 写给编辑的一句话 |
| 精选摘要 | 相册里若有「精选」和「素材」…（§6.4） |
| 计划说明 | 行程单只帮我们分章，不会公开发布 |
| 新建预期 | 每个文件夹会生成一篇**新的**游记，不会覆盖已有游记 |
| title 超长 | 杂志名最多 20 个字 |
| 路径为空 | 请填写照片文件夹路径，例如 D:\Photos\Kyoto2025 |
| pick 失败 | 无法打开选文件夹。请用下方「其他导入方式」粘贴路径 |
| Importing 再开 panel | 正在制作杂志，请稍候 |
| 标精选 toast | 已标为精选 · 点「应用排版」后生效 |
| 成功主钮 | 先看杂志排版 |
| G1 模式 A 条 | 章节已按行程排好 · 可改字与记忆词 |
| Coach ① | 从这里开始 · 照片留在本机 |
| Coach ② | 选一次旅行的文件夹即可 |
| 照片准备（panel 底「？」） | 同 [PRD-STUDIO-HOMEPAGE](./PRD-STUDIO-HOMEPAGE.md) §6.13.1 四条 bullet |

---

## 附录 C · 可用性测试脚本（5 人）

| 任务 | 成功标准 | 限时 |
|------|----------|------|
| T1 理解产品 | 能说出「做杂志长图、照片不上传」 | 10s 首屏 |
| T2 首篇导入 | 完成选夹→确认→见进度 | 3min |
| T3 复述精选夹 | 说清精选 vs 素材 | 访谈 |
| T4 回访继续 | 找到上次 trip 并打开预览 | 5s |
| T5 标精选 | 在预览为一张图加 ★ | 2min |

记录：卡点步骤、原话、是否愿推荐 vs 九宫格。

---

## 16. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.4.0 | 2026-05-28 | Phase 4 初稿：Intent Layer · Studio/Preview · G1 · plan · 管线消费 |
| v0.4.1 | 2026-05-28 | 拍板 G1 默认 A、plan 方案 A；§6 导入 panel 极易用规格 |
| v0.4.2 | 2026-05-28 | UX 修订：选夹优先 · 状态机 · 视觉/ a11y · 预览 drawer · 附录 A–C · 线框 v1 |
| **v0.4.3** | **2026-05-29** | **负责人评审补缺**：§4.1 schema 迁移+双写不变量 · §4.2 city 对齐算法+fail-open · §6.10 无分段降级 · §6.12 暖金对比度 P0 门禁 · §8.5 peakScreenId fallback · §2.1 P-EVAL 统一评估口径 · §11 新增 AC-P4-07b/09/A11Y-01 |
