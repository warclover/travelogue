# Travelogue · 屏级文案区 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go**（[七席](./acceptance-records/scr-screen-copy-region-v1-review-2026-08-04.md) · 2026-08-04）· 可 Kickoff M0 · M1 合码前关 BLK-SCR-03～06 |
| **DOC-STATUS** | **active** |
| **主题代号** | 「屏级文案区」— **SCR**（Screen Copy Region） |
| **触发来源** | 2026-08-04 产品设计定调：拼图/排版观感已满意；下一焦点为「每屏合适位置预留文本框 · 可选填写 · 空则不显示 · 导出默认含字」 |
| **前置条件** | `layoutEngine=screens`；`inline-edit` / `save-copy` / `copy-display` 可用；`screens[].copy` schema 已存在；Share-Face「空优于假句」护栏有效 |
| **审查基线** | [4mix](./PRD-screen-editorial-4mix.md) · [2land](./PRD-screen-editorial-2land.md) · [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) · [COPY](./PRD-COPY-OPTIMIZATION.md) · [Refine](./PRD-PREVIEW-REFINE-V1.md) · [SFC](./PRD-SHARE-FACE-CLOSEOUT-V1.md) · [SFP](./PRD-SHARE-FACE-PURITY-V1.md) · [AIR](./PRD-AI-RETURN-V1.md) · [LVP](./PRD-LAYOUT-VIBE-PICKER-V1.md) · [TEMPLATE-SURFACES](./TEMPLATE-SURFACES.md) · [Moments 迟晒洞察](./INSIGHT-MOMENTS-LATE-SHARE-COPY-2026-07-23.md) |
| **先例结案** | [TPC W2 captionAreas spike · Defer](./acceptance-records/tpc-w2-caption-areas-spike-2026-07-18.md) |
| **评审纪要** | [scr-screen-copy-region-v1-review-2026-08-04.md](./acceptance-records/scr-screen-copy-region-v1-review-2026-08-04.md)（结案）· [模板](./acceptance-records/scr-screen-copy-region-v1-review-TEMPLATE.md) |
| **关联文档** | [ACCEPTANCE-SCREEN-COPY-REGION-V1.md](./ACCEPTANCE-SCREEN-COPY-REGION-V1.md) · [IMPLEMENTATION-SCREEN-COPY-REGION-V1.md](./IMPLEMENTATION-SCREEN-COPY-REGION-V1.md) |
| **更新日期** | 2026-08-04 |

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-08-04）**
>
> 1. **Conditional Go**：可 Kickoff M0；M1 合码前关闭 BLK-SCR-03～06。  
> 2. **OQ-01～04 关闭**；新增 **D-SCR-21/22**（首发 GA SKU · 长图 L1）。  
> 3. **F-09～13**：4mix 已 deprecated，不得作 M1 首发 GA；longshot 展平丢 copy → M1 必修插入 L1。  
> 4. **D-SCR-08/20 修订**：统一焦点显现；4mix 降为迁移/回归参考。  
> 5. **M3 默认延期**（AI / absorb）。

> **定位**
>
> 拼图与排版已进入「观感满意」阶段。本主题把 **屏级可选文案** 做成一等产品能力：  
> 模板合同声明 0～2 个文本区；用户可写可不写；空则读者面与导出均不占位；有字则按版式位置呈现；导出默认带走文字。  
> **不**重开选版算法，**不**强迫每图一句 caption，**不**把渠道配文灌进杂志版心。

> **一句话目标**：**在合适的屏、合适的位置，留下可空的文本框；写了像杂志，不写仍是干净画廊；导出默认含字且空不挡路。**

> **完成定义**

| 门 | 含义 | 不等于 |
|----|------|--------|
| **M0 Go** | 决策表锁定 · 与 4mix/TPC/COPY/Refine 所有权切清 · schema 增量定稿 · AC/IMPL 拆文 | 改 MCS 选版 · 强制 AI 填字 · unpark 4mix |
| **M1 Go** | 通用 Screen Copy 渲染闭环 + **`screen-landscape-1` GA** + **长图 flatten 含 L1** + 焦点显现 + 导出默认 full | 仅抽 4mix enrich 就算 Done · 全库 mosaic 挖洞 · 每屏必有框 |
| **M2 Go** | 覆盖面扩至约定 airy/editorial 子集 · Dock「本页文字」索引 · web↔长图对齐狗粮 | 全书自动配文 · caption-aware 选版 |
| **M3 Go**（可选 · **默认延期**） | 单屏「写一句」AI 候选 · absorb gap · 与 AIR 渠道包分家联调 | 默认 narrate 进 L1 · Moments 强制进图 |

---

## 0. 读者指南与所有权边界

### 0.1 与相邻主题（所有权）

| 主题 | 关系 | 本主题做什么 | 本主题不做什么 |
|------|------|--------------|----------------|
| [4mix](./PRD-screen-editorial-4mix.md) | **迁移参考 · 非 M1 首发 GA** | 把 4mix 的 `copy.kicker/body` enrich/空隐 **抽成通用 SCR**；强制 pattern 时回归焦点显现 | **不** unpark 4mix；不改棋盘几何 / 25% 面积 / 章内 composite≤1 |
| [2land](./PRD-screen-editorial-2land.md) | **合同预留 · M2+ 可选** | 复用 `copyCollapse` / intentionalGaps 作 `absorb` 先例 | V1 **不**强制交付 2land 进主路径 |
| [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) | **接管已 defer 的图文渲染切片** | 以 `textRegions` 交付 **渲染能力** | **不**实现 caption tie-break / 选版读 caption（**D-SCR-12**） |
| [COPY](./PRD-COPY-OPTIMIZATION.md) | **气质与体量上位** | 继承图主文辅、sparse、空优于凑 | 不重写 hook/lead/decorLine/caption 管线；不把 L1 默认交给 narrate |
| [Refine](./PRD-PREVIEW-REFINE-V1.md) / [UX 1.1](./PRD-PREVIEW-REFINE-UX-V1.1.md) | **编辑交互宿主** | SCR 走 inline + 立即 `save-copy`（**D-REF-05**）；不置 `layoutPending` | 不改 Dock IA / 导出拦截 / 「更新版面」；不做章标题 inline |
| [SFC](./PRD-SHARE-FACE-CLOSEOUT-V1.md) / [SFP](./PRD-SHARE-FACE-PURITY-V1.md) | **分享面护栏** | 空隐；禁假句；Share 只读 | 不改 FirstSuccess / stale 主词 |
| [AIR](./PRD-AI-RETURN-V1.md) / [迟晒洞察](./INSIGHT-MOMENTS-LATE-SHARE-COPY-2026-07-23.md) | **渠道出口分家** | L3 与 L1 **字段与入口分离** | 不把迟晒默认写入 `screens[].copy` |
| [LVP](./PRD-LAYOUT-VIBE-PICKER-V1.md) | **正交** | 无 | 不新增 vibe |
| [P21](./PRD-PHASE21-mosaic-density-budget.md) / MCS / MTSO / MSA / MEGC / EGA | **不抢拼图** | Overlay **不改**槽 AR / 密度预算 | 不为 SCR 改窗口漏斗 |

### 0.2 非目标

| ID | 非目标 | 理由 |
|----|--------|------|
| **N-SCR-01** | 每一屏强制预留文本框 | 毁 mosaic 满铺；诱导凑句 |
| **N-SCR-02** | 每张照片强制图注（L2） | COPY **D-COPY-05** |
| **N-SCR-03** | V1 默认 AI 生成屏文案 | 空优于假句；NAS；M3 延期 |
| **N-SCR-04** | MCS/TPC 为 caption/SCR 改选版 | 范围爆炸（**D-SCR-12**） |
| **N-SCR-05** | equal-grid（L4/L6）挖文案洞 | 满图节奏 |
| **N-SCR-06** | 渠道配文回流版心 | 迟晒洞察 |
| **N-SCR-07** | 全书批量填空向导 | sparse |
| **N-SCR-08** | 重开 LVP / 密度专题 | 拼图已满意 |
| **N-SCR-09** | 本主题 unpark / 重设计 4mix | 几何债归 4mix；SCR 不绑票（**F-09**） |

### 0.3 术语

| 术语 | 定义 |
|------|------|
| **SCR / Screen Copy Region** | 模板声明的屏级文本区；映射 `screens[].copy.*` |
| **L1 / L2 / L3** | 版心屏文案 / 图注 / 渠道出口 |
| **textRegion** | 模板合同单个文本区声明 |
| **band overlay** | 照片块外缘顶/底条；空则隐藏，不改槽几何 |
| **长图 L1 文本块** | flatten 路径按屏插入的非照片文案节点（**D-SCR-22**） |
| **焦点显现** | draft 仅焦点/「加字」时显示空占位 |
| **空隐** | 无合格文案 → 不输出可见节点 |

### 0.4 现网事实（含七席增补）

| ID | 事实 |
|----|------|
| **F-01** | Mosaic 无文本槽 |
| **F-02** | `copy.kicker/body` schema + patch 已通；enrich **硬编码** 4mix |
| **F-03** | draft 空 copy 仍 `hasCopy*`（常驻占位）— 将被焦点显现取代 |
| **F-04** | `assets[].caption` 不进 screens 主路径 |
| **F-05** | 导出默认 `full`；**朋友圈强制 photos** |
| **F-06** | 文案不置 `layoutPending`；Share 剥编辑 |
| **F-07** | TPC captionAreas defer；LTE 无该字段 |
| **F-08** | MCS 不读 caption — V1 接受 |
| **F-09** | **4mix `deprecated` · rollout 0 · PARKED** — 非 M1 首发 GA |
| **F-10** | **longshot 展平 media-card，不读 `screens[].copy`** — 导出含字未闭环 |
| **F-11** | `layout-screen.hbs` 已有 `.layout-copy` 钩子 |
| **F-12** | **`screen-landscape-1` = ga** — M1 第一 GA SKU |
| **F-13** | 4mix CSS 强绑定 pattern — landscape-1 须独立轻量样式 |

```text
L1 SCR  screens[].copy.*     ← 本主题 · textRegions
L2 Cap  assets[].caption     ← COPY / 长图卡
L3 Ch   shareCopyPack / 迟晒 ← AIR · 永不默认灌 L1
```

---

## 1. 设计公理

| # | 公理 | 来源 |
|---|------|------|
| **A-SCR-01** | 图主文辅 | COPY D-COPY-01 |
| **A-SCR-02** | 空优于假句 | SFC / SFP |
| **A-SCR-03** | 空不挡路 | 产品定调 |
| **A-SCR-04** | 导出默认带字（平台可强制纯图） | 产品定调 + 现网 |
| **A-SCR-05** | 模板声明位置，算法不猜 | 本主题 |
| **A-SCR-06** | 编辑立即保存；不置 layoutPending | Refine / Trust |
| **A-SCR-07** | 三层分家 | 本主题 + 迟晒 |

---

## 2. 决策表（D-SCR · **已冻结** · 七席拍板）

| # | 决策项 | 冻结结论 |
|---|--------|----------|
| **D-SCR-01** | 产品对象 | **SCR**；非每图 caption、非渠道包 |
| **D-SCR-02** | 数据载体 | 复用 `screens[].copy.{kicker,body}` + `copyMeta.*Source` |
| **D-SCR-03** | 模板声明 | LTE 可选 `textRegions[]`；无声明 = 0 region |
| **D-SCR-04** | 每屏容量 | 最多 **2** region → kicker + body |
| **D-SCR-05** | 覆盖策略 | 子集 SKU；**L4/L6 禁止**非空 textRegions |
| **D-SCR-06** | Mosaic 位置 | 若启用仅 `band-top`/`band-bottom` + `collapse=hide` |
| **D-SCR-07** | Editorial | 4mix overlay 可参考；`absorb` = M2+ |
| **D-SCR-08** | 空态 | 读者/share/export **空隐**；draft **焦点显现**（统一含原 4mix 路径） |
| **D-SCR-09** | 常驻虚线 | **否决** |
| **D-SCR-10** | AI | V1 不生成；**M3 延期** |
| **D-SCR-11** | 导出 | 默认含 L1；`photos`/Moments 折叠 |
| **D-SCR-12** | 选版 | **合码红线**：MCS/TPC **不**因 SCR/caption 改候选 |
| **D-SCR-13** | 与 L2 | Web screens 主路径只渲 L1 |
| **D-SCR-14** | 与 L3 | Channel Pack 永不默认写 L1 |
| **D-SCR-15** | 字数 | kicker≤30 · body≤80；软提示 body≤56 |
| **D-SCR-16** | 全书稀疏 | 有字屏目标 ≤约 30%（观测，非硬闸） |
| **D-SCR-17** | Patch | 白名单 `.screens.*.copy.*`；sanitize |
| **D-SCR-18** | 开关 | `screen_copy_region.enabled` 默认 **true**（dogfood）；false 时新 SKU 不挂 region |
| **D-SCR-19** | 字段名 | SSOT = **`textRegions`**（captionAreas = 历史别名文档映射） |
| **D-SCR-20** | 4mix 归属 | 几何归 4mix PRD；执行层归 SCR；**产品角色 = 迁移参考，非 M1 首发 GA** |
| **D-SCR-21** | M1 首发 GA | **`screen-landscape-1`**：单 region `mapTo=body` · `band-bottom` · `collapse=hide` |
| **D-SCR-22** | 长图 L1 | flatten 时按屏插入非空 copy 文本块；不要求复刻 mosaic DOM |

---

## 3. 目标与成功标准

| ID | 目标 |
|----|------|
| **G-SCR-01** | 声明了 region 的屏可加短文案；不加则与今日纯图一致 |
| **G-SCR-02** | 读者/分享零催填、零假句 |
| **G-SCR-03** | **Web 与长图**默认含已写 L1；无字不失败 |
| **G-SCR-04** | 焦点显现 + 立即保存；Share 只读 |
| **G-SCR-05** | 拼图槽 AR / 密度不被 SCR 改写 |

> 成功体感：翻到某一页点一下写下「傍晚的港口还没熄灯」；不写的页干净；**导出发群长图也带那句**；没字的页照旧好看。

---

## 4. 模板合同 · `textRegions`

### 4.1 字段（LTE）

```yaml
textRegions:
  - id: body
    role: moment          # eyebrow | moment | closing
    placement: band-bottom  # band-top | band-bottom | gap-in-grid | rail
    collapse: hide        # hide | absorb（absorb = M2+）
    maxChars: 80
    mapTo: body           # kicker | body
```

| 约束 | 规则 |
|------|------|
| 缺省 | 无 / `[]` ⇒ 0 region |
| 数量 | `maxItems: 2`；`mapTo` 唯一 |
| L4/L6 | **禁止**非空 textRegions（CI lint） |
| 密铺 | 仅 band + hide（V1） |

### 4.2 TPC

交付渲染能力；tie-break 仍 defer。TPC 文档加脚注指针（SHD-SCR-01）。

### 4.3 SKU 列车

| 里程碑 | Pattern | textRegions |
|--------|---------|-------------|
| **M1 必修 GA** | `screen-landscape-1` | body · band-bottom · hide |
| **M1 迁移** | `screen-editorial-4mix`（若强制/工具） | kicker+body；走通用 enrich；**不 unpark** |
| **M2** | 1× airy mosaic（设计师点名） | ≤1 band |
| **禁止** | `screen-landscape-4` / `-6` | — |

---

## 5. Schema 增量（trip）

| 字段 | 变更 |
|------|------|
| `copy.kicker` / `copy.body` | **保持** maxLength；description 泛化为 SCR |
| `copyMeta.*Source` | **保持**；用户 → `user`；空 → `empty` |
| `copyMeta.regionsApplied` | **可选**（SHD）；不挡 M1 |
| `export.copyDisplay` | **无改** |
| L2/L3/册章字段 | **不改** |

Patch：`chapters.{id}.screens.{screenId}.copy.{kicker|body}` + Share-Face sanitize。

---

## 6. 渲染与交互

### 6.1 Web（screens）

1. 读 pattern `textRegions`（无则跳过）  
2. 读 `screens[].copy.*`  
3. 非空且过护栏 → `.layout-copy`；否则读者/export 不输出  
4. draft + 焦点/加字 → 空占位；失焦空 → 隐藏  
5. `copyDisplay=photos` → 折叠 `.layout-copy`

### 6.2 长图（**D-SCR-22**）

| 条件 | 行为 |
|------|------|
| 屏 `copy` 均空 | 不插入文本块（≈今日） |
| kicker/body 非空 | 在该屏 flatten 卡片序列中插入 L1 文本块（顺序：kicker→照片槽→body，缺省侧跳过） |
| Moments / photos | 文本块一并折叠 |

> **不**要求 longshot 复刻 `layout-screen` mosaic DOM。

### 6.3 精修

| 态 | 行为 |
|----|------|
| 读者 / share | 有字显示；无字无痕；share 不可编 |
| draft 未聚焦 | 同读者 |
| draft 聚焦 / 加字 | 空 region 淡虚线 + 短占位 |
| 输入 | 立即 `save-copy` |
| Dock（M2） | 「本页文字」索引 |

SCR **不得**置 `layoutPending`。

---

## 7. 导出与平台

| 场景 | L1 |
|------|-----|
| 默认 longshot / 微信群等 | **含**（有则渲） |
| 纯照片勾选 | 折叠 |
| `wechat_moments` | **强制折叠**；话术走 L3 |
| 全书无 SCR | 导出成功 |

---

## 8. 里程碑

| 里程碑 | 范围 | 退出 |
|--------|------|------|
| **M0** | 决策冻结 · AC/IMPL · 边界会签 | Conditional Go ✅ |
| **M1** | 通用 enrich · landscape-1 · 长图 L1 · 焦点显现 · 4mix 迁入回归 | AC-SCR-01～10/06b；BLK-03～06 关 |
| **M2** | SKU 扩面 · Dock 索引 | AC-11～14 |
| **M3** | **延期** · AI / absorb | AC-15～17 |

估时（Kickoff 复核）：M0 1～2 人日；M1 **7～10**（含长图 L1）；M2 3～5；M3 4～6。

---

## 9. 验收标准（索引）

正式清单：[ACCEPTANCE-SCREEN-COPY-REGION-V1.md](./ACCEPTANCE-SCREEN-COPY-REGION-V1.md)。

| ID | 断言 | 门 |
|----|------|----|
| **AC-SCR-01** | 无 textRegions：无 SCR 节点 | M1 |
| **AC-SCR-02** | 有 region 且空：读者态无节点/无常驻虚线 | M1 |
| **AC-SCR-03** | draft 焦点显现；失焦空隐 | M1 |
| **AC-SCR-04** | 写入立即持久化；`*Source=user` | M1 |
| **AC-SCR-05** | 清空后空隐；导出无假句 | M1 |
| **AC-SCR-06** | 默认导出 **长图** 含非空 L1 文本块 | M1 |
| **AC-SCR-06b** | landscape-1 挂 textRegions 且可写可读 | M1 |
| **AC-SCR-07** | photos / Moments：L1 折叠 | M1 |
| **AC-SCR-08** | 全书无 SCR：导出成功 | M1 |
| **AC-SCR-09** | Share 不可编 | M1 |
| **AC-SCR-10** | overlay 不改槽 bbox（容差 0 px） | M1 |
| **AC-SCR-11～14** | L4/L6 lint · Dock · 双表面 · 不置 pending | M2 |
| **AC-SCR-15～17** | AI 确认制 · L3 不灌 · absorb | M3 |

---

## 10. 风险与已关闭 OQ

### 10.1 风险

| 风险 | 缓解 |
|------|------|
| 「每屏都能写」预期 | 只在有 region 屏可写；M2 Dock 列可写屏 |
| 长图与 web 字位不一致 | D-SCR-22 明示「文本块」非 DOM 复刻；狗粮对读 |
| Moments「导出丢字」误解 | 狗粮说明 + L3 入口 |
| 抽 enrich 打坏 4mix 工具链 | BLK-05 回归 |
| 范围滑向选版 / unpark 4mix | D-SCR-12 · N-SCR-09 |

### 10.2 OQ（已关闭）

| ID | 结论 |
|----|------|
| **OQ-SCR-01** | dogfood 默认 **on** |
| **OQ-SCR-02** | M1 = **`screen-landscape-1`** |
| **OQ-SCR-03** | 硬顶 80 · 软提示 56 |
| **OQ-SCR-04** | TPC **脚注指针**，不重开全文 |

---

## 11. 工程挂钩

| 层 | 路径 |
|----|------|
| Schema | `schemas/trip.schema.json` |
| LTE | `layout_template.schema.json` · `screen-landscape-1.yaml` |
| Enrich | `travelogue/render/context.py`（去 4mix 硬编码） |
| DOM | `layout-screen.hbs` · `.layout-copy` |
| 长图 | `chapter_items.py` / longshot 组装 · **新增 L1 文本块** |
| 显隐 | `copy-display.css` · `copy-toggle.js` |
| Patch | `copy_patch.py` · `share_face_copy.py` |
| 平台 | `platform_longshot.py` |

任务卡：[IMPLEMENTATION-SCREEN-COPY-REGION-V1.md](./IMPLEMENTATION-SCREEN-COPY-REGION-V1.md)。

---

## 12. 附录

### 12.1 Must-Fix 追踪（七席）

| ID | 状态 |
|----|------|
| BLK-SCR-01 D/OQ 回写 | ✅ v0.2.0 |
| BLK-SCR-02 拆 AC/IMPL | ✅ |
| BLK-SCR-03 landscape-1 GA | ⏳ M1 |
| BLK-SCR-04 长图 L1 | ⏳ M1 |
| BLK-SCR-05 4mix 迁入回归 | ⏳ M1 |
| BLK-SCR-06 焦点显现 | ⏳ M1 |

### 12.2 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-08-04 | 首稿 |
| **v0.2.0** | 2026-08-04 | 七席 Conditional Go · D-21/22 · F-09～13 · M3 延期 |
