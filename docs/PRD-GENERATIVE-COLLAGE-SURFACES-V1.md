# Travelogue · 生成式拼贴面与离线 SKU 工厂 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · Ready for Kickoff W0**（本轮不编码；编码另开） |
| **特性代号** | **GCS**（Generative Collage Surfaces） |
| **文档类型** | 版式旁路专项优化 PRD（导出海报面 + 离线 LTE SKU 工厂 · **非** MCS 主链） |
| **触发来源** | 开源对标 [stefanwayon/collage](https://github.com/stefanwayon/collage)（BRIC · Atkins ACM）；与 MGQ「禁 runtime 改 rect」及 P17-B「生成式 composite」对齐 |
| **前置条件** | Phase 16 LTE 默认路径稳定；MCS `pick_best_window` 为现网权威；Output Recipe Band/resolve 可用；LTE validator / admission 可复用；MGQ D-MGQ-02 已冻结 |
| **纲领上位** | [PRD-LAYOUT-QUALITY-STACK-V1.md](./PRD-LAYOUT-QUALITY-STACK-V1.md)（**LQS** · 统摄 MSR/MGQ/GCS 跨主题合同与排期） |
| **关联文档** | [PRD-MCS-GEOMETRIC-QUALITY-V1.md](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [PRD-MCS-SIGNATURE-ROUTING-V1.md](./PRD-MCS-SIGNATURE-ROUTING-V1.md) · [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md) · [PRD-PHASE17-research-stub.md](./PRD-PHASE17-research-stub.md) · [PRD-PHASE17-layout-strategy-engine.md](./PRD-PHASE17-layout-strategy-engine.md) · [LTE-ADMISSION-LAYOUT-TEMPLATES.md](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) · [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [观感提升-业内调研.md](./观感提升-业内调研.md) · [观感提升路线图.md](./观感提升路线图.md) |
| **评审纪要** | [acceptance-records/generative-collage-surfaces-v1-review-2026-07-18.md](./acceptance-records/generative-collage-surfaces-v1-review-2026-07-18.md)（**已结案** · Conditional Go · BLK-01～08） |
| **评审模板** | [acceptance-records/generative-collage-surfaces-v1-review-TEMPLATE.md](./acceptance-records/generative-collage-surfaces-v1-review-TEMPLATE.md)（备查） |
| **验收配套** | W0 可用本文 §9–§10；**W1 merge 前**须拆 `ACCEPTANCE-GENERATIVE-COLLAGE-SURFACES-V1.md`（BLK-08） |
| **实施清单** | Kickoff 时补 `IMPLEMENTATION-GENERATIVE-COLLAGE-SURFACES-V1.md`（先 B 后 A） |
| **更新日期** | 2026-07-18 |

> **v0.2.0 评审回写摘要（跨职能 Conditional Go）**
>
> - BLK-01：禁区 / MCS 失败口仍走 legacy — 已冻结  
> - BLK-02：轨 A = **轨道原生** guillotine/treemap；禁 BRIC 连续 rect→YAML 主路径  
> - BLK-03：OQ-01 = 仅 ▾「单屏海报」  
> - BLK-04：OQ-03 = 轨道模型；不合格丢弃  
> - BLK-05：强制 vendor MIT；热路径零新 pip；禁 GPL  
> - BLK-06：轨 B → export job sidecar；独立 Recipe intent/engine/platform  
> - BLK-07：AC 可测化 + golden/LRG W1 硬门 + 独立盲评码  
> - BLK-08：W1 前拆 AC/IMPL；实现 **先 B 后 A**  
> - **本轮不动代码**；Kickoff 另排期

> **定位**
>
> BRIC（Blocked Recursive Image Composition）证明：在「任意张数 + 任意宽高比 → 填满矩形、保原始 AR、统一 gutter」场景下，**二叉树递归切分**比手写模板库更省维护。  
> Travelogue 主链是 **LTE 固定 SKU + MCS 选版填槽 + 章内叙事节拍**；与 BRIC「先定片再切画布、无 hero / 无文案槽」哲学相反。  
> 本 PRD **不**把 BRIC 挂进 MCS 失败默认路径，**不** runtime 改写 `slots[].rect`；只交付两条旁路：  
> 1. **轨 A · 离线 SKU 工厂** — 在 LTE `stage.cols/rows` 上 guillotine/treemap 枚举 → validator → YAML admission（落实 P17-B）  
> 2. **轨 B · 导出海报面** — Output Recipe Writer：vendored BRIC `bric_compose` → 单屏填满拼贴（聚会 / 轻量分享）
>
> **一句话目标**：用算法扩大合法 LTE SKU、用隔离的海报 Writer 服务「快速单屏」；杂志章序列仍由 MCS/LTE 负责。

> **产品共识（五条铁律）**
>
> 1. **主链不动** — `pick_best_window` / solidify / CSS-from-YAML 合同不变；GCS 失败不得拖垮 curate。  
> 2. **禁止 runtime 连续分区进杂志屏** — 对齐 MGQ D-MGQ-02 / P16 NG-P16-04。  
> 3. **裁切哲学不混用** — 海报面走统一「保 AR 缩放（contain 系）」；禁止再套 slot `cover`+focal。  
> 4. **术语隔离** — 用户自制 `mediaClass=collage` ≠ GCS 生成拼贴；telemetry / patternId 分名；用户文案用「单屏海报」，禁称「九宫格」。  
> 5. **名实一致** — 用户可见「单屏海报」必须对应真 `poster_bric` Writer 产物，禁止用长图 scroll 顶替。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 冻结决策（D-GCS-*）与已关闭 OQ |
| §0.2 | v0.1→v0.2 变更摘要 |
| §1 | 对标结论、现网缺口、问题清单 |
| §2 | 目标 / 非目标 / 成功指标 |
| §3 | 与相邻主题边界 |
| §4 | 双轨架构与挂点 |
| §5 | 轨 A · 离线 SKU 工厂合同 |
| §6 | 轨 B · 导出海报面合同 |
| §7 | 数据 / API / 依赖策略 |
| §8 | 埋点与实验 |
| §9 | 里程碑 |
| §10 | 验收 AC 索引 |
| §11 | 风险 |
| 附录 | 对标摘要 · 版本记录 |

### 0.1 评审决策（D-GCS · **已冻结**）

| # | 决策项 | 冻结结论 |
|---|--------|----------|
| **D-GCS-01** | 落点轨 | **双轨并行**（交付可串行：先 B 后 A）：A=离线 SKU 工厂；B=Output Recipe Writer；**禁止**默认挂 MCS `used_legacy` |
| **D-GCS-02** | 与 MGQ | **遵守** D-MGQ-02：不得 runtime 改 slot `rect`；GCS 不进 `MosaicConfig` 评分路径 |
| **D-GCS-03** | 算法选型 | **轨 B**：强制 vendor MIT BRIC 核心（钉 commit/拷贝；`fit_pictures_balanced` 等价）；**轨 A**：在 LTE `stage.cols/rows` 上做 guillotine/treemap **原生枚举**；**禁止**以 BRIC 连续像素 rect 为主路径硬转 YAML。热路径与默认安装 **零新 pip** |
| **D-GCS-04** | PhotoCollage | **只读参考**；GPL-2.0 **禁止**进主依赖 / 发行包 |
| **D-GCS-05** | 裁切 | 海报面：**统一 contain 系缩放**（可 letterbox / 统一底色或 blur fill）；**禁止**与杂志 slot `cover` 混用 |
| **D-GCS-06** | 张数 | 轨 B：输入 **3–6 推荐**，硬上限 **9**；1–2 张走既有 full-frame / 单图 Writer，不调 BRIC |
| **D-GCS-07** | trip.json / 导出落点 | 轨 B 产物与诊断落 **export job sidecar**（或等价非杂志文档面）+ telemetry；**禁止**写入 `trip.json.screens[]`（含伪 `patternId`）；**默认禁止**向 `trip.json` 根写入未 schema 化的 `exportArtifacts` |
| **D-GCS-08** | SKU 入轨 | 经 LTE validator + admission（≥experimental）+ 人工/盲评 sign-off 后方可 beta/ga；YAML 须含可复现元数据：`generator` + `enum_params`（stage/gap/mix/算法版本/commit） |
| **D-GCS-09** | 确定性 | **轨 B**：同 `sizes+width+border+spacing+round_result` → 同 positions/canvas。**轨 A**：同 `(n, orientation_mix\|AR_bins, stage.aspect, gap, enum_params)` → 同**有序**拓扑候选序列。禁随机 shuffle；禁依赖 hash/dict 迭代序 |
| **D-GCS-10** | 发布门禁 | 轨 B：`features.gcs_poster_bric=false` 可先 merge；**默认对用户可见**须过 **AC-GCS-BLIND ≥55%**。轨 A：以代表 corpus 上 `used_legacy` **或** pattern-miss **相对冻结 baseline** 下降为准（阈值 W0/IMPL 定），非枚举次数/YAML 产量 |

| OQ | 冻结结论 |
|----|----------|
| **OQ-GCS-01** | **已关闭 · A** — 仅 ▾「单屏海报」次入口；**不**进 Sparse/Ambiguous/Narrative 主 CTA；不抢 `chat_longshot` |
| **OQ-GCS-02** | **已关闭 · A** — **不**默认绑 event-recap；仅可选意图 / CLI |
| **OQ-GCS-03** | **已关闭 · A** — 轨道模型原生枚举；无法入轨 → **丢弃**；禁止 BRIC 绝对 rect 硬塞 YAML |
| **OQ-GCS-04** | **已关闭 · A** — V1 统一 contain；face-aware letterbox → **V1.1** |

**总案一句话**：BRIC 作 **海报导出器**；轨道枚举作 **SKU 生成器**；**不作**杂志屏 runtime fallback。

### 0.2 v0.1.0 → v0.2.0 变更摘要（评审合入）

| 来源 | 合入要点 |
|------|----------|
| **BLK-01** | 禁区一字面冻结；MCS 失败口仍 legacy；AC-GCS-01 |
| **BLK-02** | 轨 A 搜索空间 = 轨道原生；禁 BRIC→YAML 主路径 |
| **BLK-03** | OQ-01 = ▾ only |
| **BLK-04** | OQ-03 = 轨道 + 丢弃 |
| **BLK-05** | 强制 vendoring；零新 pip；禁 GPL |
| **BLK-06** | job sidecar + Recipe intent/engine/platform 合同 |
| **BLK-07** | AC 可测步骤；LRG W1 硬门；盲评独立码 |
| **BLK-08** | W1 前拆文；实现先 B 后 A |
| **Should** | 关 hero 面积带（轨 A V1）；letterbox 默认待 IMPL；文案「单屏海报」 |

---

## 1. 背景与问题

### 1.1 对标结论（stefanwayon/collage · BRIC → Travelogue）

| BRIC / collage 能力 | Travelogue 现状 | 本 PRD 态度 |
|---------------------|-----------------|-------------|
| 任意 n、任意 AR → 填满矩形 | LTE 26 SKU + MCS 枚举；失败 → legacy 规则屏 | **轨 B 抄**；轨 A 用同族算法在**轨道上**枚举 |
| 保原始 AR，只缩小不放大 | 杂志槽默认 `cover`/`contain` 按主体 | 海报面 **抄保 AR**；杂志槽 **不改** |
| 统一 border / spacing | LTE gap / CSS 变量 | 海报面抄；SKU 工厂映射到 YAML gap |
| 无预定义模板 | 模板驱动是产品优势（hero/节拍/文案） | **保留模板主链**；用工厂补 SKU 空洞 |
| 无 hero / 无叙事 | ChapterScreenPlanner + mainSlotPolicy | **接受**海报面无 hero；杂志面禁止用 BRIC 冒充 |
| `fit_pictures_balanced` API | 无等价 runtime | **仅轨 B** Writer 核心 |
| MIT | PhotoCollage 曾被调研但 GPL | **强制 vendor** MIT；禁 GPL 依赖 |
| 像素 MIP 取整（`round_result`） | solidify 整数几何 | 轨 B 导出对齐；轨 A 入 YAML 前取整 |

### 1.2 与 gridwiggle / LTE 路线对比（已共识）

```text
gridwiggle / LTE（主路径）     轨 B BRIC（导出旁路）     轨 A（离线工厂）
  先定版式骨架                   先定照片尺寸             先定轨道舞台
  再填照片                       再递归切画布             再枚举可声明拓扑
  模板 / SKU 驱动                算法驱动海报             → 产出新 SKU YAML
```

MGQ 已明确：**抄 gridwiggle 的软罚与准入，不抄连续分区 solver**。  
GCS 把连续分区限制在 **离线工厂（轨道离散）** 与 **导出 Writer（像素 BRIC）**，不违反 D-MGQ-02。

### 1.3 现网权威链路（不可误映射）

```text
run_curate
  → ChapterScreenPlanner
      → mosaic.compose.pick_best_window     ← 杂志主链（MCS）
           → LTE YAML patterns
           → URO / MGQ 硬过滤
           → soft score → self-heal
           → used_legacy → legacy 规则屏   ← 现网失败口（非 BRIC · 冻结）
  → solidify → trip.json screens[]

export / Output Recipe
  → chat_longshot / moments_grid / …       ← 既有 Writer
  → [本 PRD] poster_bric Writer            ← 轨 B 唯一挂点（▾）
       → export job sidecar（非 screens[]）
```

### 1.4 用户可感知问题（本 PRD 要解决）

| ID | 问题 | 典型表现 | 根因分层 |
|----|------|----------|----------|
| **GCS-P-01** | SKU 空洞导致合法组合进 legacy | 混排观感跳水 | pattern 库覆盖不足 |
| **GCS-P-02** | 手写 YAML 扩 SKU 成本高 | 新组合靠人工画 rect | 缺枚举 + validator 工厂 |
| **GCS-P-03** | Sparse / 聚会场景仍走杂志长卷心智 | 3–6 张也要多屏叙事 | 缺「单屏海报」交付物 |
| **GCS-P-04** | 算法拼贴与用户 collage / 九宫格语义混淆 | 排查/埋点/文案串线 | 术语未隔离 |
| **GCS-P-05** | 若误把 BRIC 挂 MCS 失败口 | 章内突然无 hero、无文案槽 | 产品哲学冲突（**禁止**） |

### 1.5 P17-B 承接关系

[PRD-PHASE17-research-stub.md](./PRD-PHASE17-research-stub.md) 已占位生成式 composite。  
本主题 **拥有**轨 A 排期合同，并 **新增**轨 B；匈牙利匹配等 LSE 主线 **不在范围**。

---

## 2. 目标与非目标

### 2.1 目标（G-GCS-*）

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-GCS-01** | 冻结双轨边界与禁区 | 本纪要 + §0.1 | W0 ✅ |
| **G-GCS-02** | 轨 A：给定 mix/stage/gap 可枚举有序拓扑 | CLI + 确定性单测 | W1 |
| **G-GCS-03** | 轨 A：候选经 LTE validator；失败可解释 | ValidationReport + discard | W1 |
| **G-GCS-04** | 轨 A：≥3 个 experimental YAML 经 admission 入库 | PR + `enum_params` | W2 |
| **G-GCS-05** | 轨 B：`poster_bric` Writer 可导出 | 像素产物 + job 字段 | W1（优先） |
| **G-GCS-06** | 轨 B：Studio/CLI ▾ 可发现 | UI/CLI 合同 | W2 |
| **G-GCS-07** | 术语与 telemetry 隔离 | 事件名 / 字段单测 | W0–W1 |
| **G-GCS-08** | corpus 上 legacy/miss 相对 baseline ↓ | 报表 | W3 |

### 2.2 非目标

| # | 排除项 | 理由 |
|---|--------|------|
| **OUT-01** | MCS `used_legacy` 默认改调 BRIC | **已冻结禁止** |
| **OUT-02** | runtime 动态改写 `screens[].slots[].rect` | MGQ / P16 铁律 |
| **OUT-03** | 用 BRIC 结果再套 slot `cover`+focal | 裁切哲学混用 |
| **OUT-04** | PhotoCollage / GPL 依赖进主包 | 许可风险 |
| **OUT-05** | 章内文案槽 / hero 叙事由 BRIC 生成 | BRIC 无此语义 |
| **OUT-06** | 替换 `moments_grid` 九宫格 Writer | 海报 ≠ 九宫格 |
| **OUT-07** | 解冻 LSE 软乘子上量 | 归 LSE/MGQ |
| **OUT-08** | 用户 collage 检测重做 | 归 collage_routing |
| **OUT-09** | 修图 / 生成式改图像素 | 产品禁区 |
| **OUT-10** | 默认路径 shuffle 照片序 | 确定性 |
| **OUT-11** | 轨 A 以 BRIC 连续 rect 硬转 YAML | **BLK-02** |
| **OUT-12** | 轨 A V1 生成伪 hero 面积带 SKU | 避免撞 mainSlotPolicy |

### 2.3 成功指标（方向性）

| 指标 | 方向 | 备注 |
|------|------|------|
| MCS `plannerPath=legacy` 或 pattern-miss（代表 corpus） | ↓ vs baseline | 轨 A 主 KPI |
| 新 SKU admission 通过数（experimental→beta） | ↑ | 质量优先于数量 |
| 海报 Writer 导出成功率 | ≥ 99%（可重试） | 轨 B |
| 海报盲评「可发」率 | ≥ 55%（AC-GCS-BLIND） | 默认开启前 |
| 杂志 golden / LRG | 无回归 | **W1 硬门** |

---

## 3. 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) | **遵守 · 不抢** | 不改 `MosaicConfig`；不 runtime 改 rect |
| [LTE / P16](./PRD-PHASE16-layout-template-engine.md) | **消费 validator · 产出 YAML** | 轨 A 唯一入轨方式 |
| [LTE Admission](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) | **复用** | experimental→beta→ga |
| [P17-B stub](./PRD-PHASE17-research-stub.md) | **承接升格** | 本主题拥有轨 A 排期 |
| [LSE / P17](./PRD-PHASE17-layout-strategy-engine.md) | **不做** | 匈牙利 / 软乘子仍归 LSE |
| [URO](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) | **轨 A 入库后自动消费** | 新 SKU 须带合理 `usage` / eligibility |
| [Output Recipe](./PRD-OUTPUT-RECIPE-V1.md) | **扩展 Preset/Writer** | `intent=poster_bric` + 独立 engine/platform；▾ 次入口 |
| [导出门面](./PRD-PREVIEW-EXPORT-FACADE-V1.md) | **不弱化 80% 路径** | 不抢主 CTA（OQ-01 已关） |
| collage_routing | **术语隔离** | 用户 collage → full-frame；GCS → Writer / SKU |

---

## 4. 双轨架构

### 4.1 总览

```text
                    ┌──────────────────────────────────────┐
                    │  curate / MCS / LTE（杂志主链）         │
                    │  禁止 GCS runtime 改几何               │
                    └──────────────────────────────────────┘
                                      ▲
                                      │ 仅 GitOps YAML
                    ┌─────────────────┴────────────────────┐
                    │  轨 A · Offline SKU Factory            │
                    │  (n, mix, stage, gap) → 轨道枚举       │
                    │  → validator → admission → YAML        │
                    │  （禁止 BRIC 像素 rect 硬塞）            │
                    └──────────────────────────────────────┘

                    ┌──────────────────────────────────────┐
                    │  轨 B · Export Poster Writer（先交付）  │
                    │  kept assets (3–9) → bric_compose      │
                    │  → contain 贴图 → export job sidecar   │
                    │  不写入 screens[]                      │
                    └──────────────────────────────────────┘
```

### 4.2 明确禁止的挂点（可检）

| 挂点 | 状态 |
|------|------|
| `compose.pick_best_window` → `used_legacy=True` 之后调 BRIC | **V1 禁止**（AC-GCS-01） |
| `score_candidate` 内改 `rect` | **永久禁止**（MGQ） |
| 将 BRIC 屏伪装为既有 `screen-landscape-*` | **禁止** |
| 对 BRIC 叶节点再跑杂志 `cover` crop | **禁止** |
| BRIC 连续 rect → 入库 YAML 主路径 | **禁止**（BLK-02） |

### 4.3 交付顺序（BLK-08）

1. **先轨 B**：Writer + `features.gcs_poster_bric=false` → 狗粮  
2. **后轨 A**：枚举 CLI → ≥3 experimental（W2）  
3. 远期 runtime legacy alt：**另开 PRD**，不在 V1

---

## 5. 轨 A · 离线 SKU 工厂

### 5.1 输入 / 输出

| 方向 | 合同 |
|------|------|
| **输入** | photo-agnostic：`n`（2–9）、`orientation_mix` 或 AR bins、`stage.aspect`、`gap`、`enum_params`；**禁止**用单次具体 asset sizes 生成可入库 SKU |
| **过程** | ① 轨道上 guillotine/treemap 枚举 ② 规范化离散 `rect` ③ `validate_for_publish` ④ 不合格丢弃（discard 报表）⑤ 人工/盲评挑选 |
| **输出** | `screen-*.yaml` + CSS sync；`generator: gcs-track-v1` + `enum_params` |
| **非输出** | 运行时 trip.json 临时几何；伪 hero 面积带 SKU（V1） |

### 5.2 规范化要求

- 槽位数 ≤ 9；rect 不重叠、不越界；gap 一致  
- 必须可映射 `stage.cols/rows`  
- 声明默认 `fit`；`usage` / `constraints.eligibility` 不得空壳  
- **不得**为「填满」放宽 V-P16 硬约束  

### 5.3 成功定义

| 信号 | 解释 |
|------|------|
| ✅ | corpus 上 legacy/miss ↓ vs baseline |
| ✅ | 新 SKU 盲评不劣于邻近手写 SKU |
| ❌ | 仅工厂产量高但未入 ga / 未改善 miss |

### 5.4 工具落点（建议）

| 路径 | 角色 |
|------|------|
| `travelogue/layout_templates/gcs_factory/` 或 `scripts/gcs_sku_enumerate.py` | 枚举 CLI |
| 复用 `layout_templates/validator.py` | 几何门禁 |
| 复用 admission hook | 生命周期 |

---

## 6. 轨 B · 导出海报面（`poster_bric`）

### 6.1 产品叙事

| 用户意图（冻结文案） | 产物 |
|----------------------|------|
| 「单屏海报 · 发群」 | 一张填满矩形的拼贴图 |
| （次文）聚会 / 轻量分享 | Sparse / Ambiguous ▾ 可选 |

与 `moments_grid`（朋友圈九宫格）、用户 `collage` 素材 **分名**。

### 6.2 入口（OQ-01 已关）

- Studio / 导出门面：**仅 ▾**；不进主 CTA  
- Narrative：**不默认**  
- event-recap：**不默认绑**（OQ-02）  
- flag：`features.gcs_poster_bric` 默认 **false** 至 AC-GCS-BLIND  

### 6.3 输入选片

| 规则 | 说明 |
|------|------|
| 来源 | 策展后 `kept` / 代表图；推荐封面 + 3–6 张 |
| 排除 | `mediaClass=collage` 默认排除 |
| 排序 | curate 代表序或时间序；**禁止**随机 |

### 6.4 几何与渲染

```text
fitted, positions, canvas = bric_compose(
    sizes, width=W, border=B, spacing=S, round_result=True
)
# 统一 contain 系贴图 → 导出文件
# letterbox fill：solid 或 blur（默认值 IMPLEMENTATION 冻结二选一）
# 禁止 per-slot cover crop
```

| 参数 | V1 默认 |
|------|---------|
| `width` | 1080 |
| `border` | 16 |
| `spacing` | 8 |
| `round_result` | true |

### 6.5 Output Recipe 合同（BLK-06）

| 字段 | 冻结 |
|------|------|
| `intent` | `poster_bric` |
| `engine` | **独立** engine id（扩展现网 `EngineId`；不得复用并伪装 `photo_grid`） |
| `platform` | 独立 id；**禁止**冒充 `moments_grid` |
| Band | Sparse / Ambiguous：▾ 可选；Narrative：不默认 |
| 失败降级 | 明确错误；若用户从长图入口来可提示回退 `chat_longshot`；**禁止**静默用长图顶替并仍称海报 |

### 6.6 失败与降级

| 情况 | 行为 |
|------|------|
| n < 3 | 禁用入口；不调用 BRIC |
| n > 9 | 截断至 9 并 UI 提示，或禁用 |
| 构图失败 | 明确错误 + 可选回退长图提示 |
| 人脸贴边 | V1 接受 contain（OQ-04） |

---

## 7. 数据 / API / 依赖

### 7.1 内部 API（分家）

**轨 B**

```text
bric_compose(sizes, *, width, border=16, spacing=8, round_result=True)
  -> fitted_sizes, positions (x,y,w,h), canvas_size
```

**轨 A**

```text
enumerate_track_topologies(n, mix, stage_aspect, gap, enum_params)
  -> ordered list[TopologyCandidate]  # 全序可复现
```

### 7.2 依赖策略（BLK-05）

| 策略 | 要求 |
|------|------|
| Vendoring | V1 **强制**拷贝/钉 commit MIT 核心；CI 可离线单测 |
| 许可证扫描 | 禁止 GPL 传递依赖（AC-GCS-09） |
| pip | 热路径与默认安装 **零新依赖**；可选 extras 仅工具链且钉版本 |

### 7.3 字段隔离

| 概念 | 标识 |
|------|------|
| 用户自制拼图素材 | `mediaClass=collage` → `screen-full-frame` |
| GCS 海报导出 | `exportSurface=poster_bric` / recipe intent + **job sidecar** |
| GCS 工厂产物模板 | YAML `generator: gcs-track-v1` + `enum_params` |

---

## 8. 埋点与实验

| 事件 / 字段 | 用途 |
|-------------|------|
| `gcs_sku_enumerate` | 轨 A：候选数、validator pass/fail、discard |
| `gcs_sku_admitted` | 轨 A：template_id、lifecycle |
| `gcs_poster_export_start/ok/fail` | 轨 B：n、width、耗时、失败码 |
| `gcs_poster_cta_impression/click` | ▾ 发现性 |

Feature flag：

- `features.gcs_sku_factory`（工具链，开发默认可开）  
- `features.gcs_poster_bric`（用户面，默认 **false** 至 AC-GCS-BLIND）

---

## 9. 里程碑

| 波次 | 内容 | 出口 |
|------|------|------|
| **W0** | 评审已结案；拆 ACCEPTANCE 草案可选；IMPLEMENTATION 骨架；术语表；baseline 口径 | Kickoff 文档 |
| **W1** | **先**轨 B Writer + 单测/golden；轨 A 枚举 CLI + validator；AC 可测步骤齐 | 可狗粮；**LRG/golden 绿** |
| **W2** | 轨 A ≥3 experimental；轨 B Studio/CLI ▾；狗粮清单 | beta 可开关 |
| **W3** | legacy/miss 报表；AC-GCS-BLIND；默认露出决策 | GA 或保持 opt-in |

> **本轮**：评审 + PRD v0.2.0；**不编码**。

---

## 10. 验收 AC 索引

| AC | 陈述 | 波次 | 可测要点（BLK-07） |
|----|------|------|-------------------|
| **AC-GCS-01** | MCS 默认路径无 BRIC 调用 | W0/W1 | 静态/单测：`compose`/`legacy` 路径无 `bric_compose` |
| **AC-GCS-02** | 轨 A 两次枚举拓扑序列一致 | W1 | 固定 `enum_params` → 序列哈希相等 |
| **AC-GCS-03** | 非法候选被拒且报告可读 | W1 | 重叠/越界 fixture → reject + reason |
| **AC-GCS-04** | admission 未过不得标 ga | W2 | lifecycle 断言 |
| **AC-GCS-05** | 轨 B：3–6 张无重叠、保 AR、gutter 一致 | W1 | 几何/像素断言；无 per-slot cover |
| **AC-GCS-06** | 轨 B 后 `screens[]` 无伪 pattern | W1 | export 前后 screens diff |
| **AC-GCS-07** | 默认排除用户 collage 素材 | W1 | collage fixture 不进拼贴 |
| **AC-GCS-08** | 杂志 golden / LRG 无回归 | W1–W3 | **W1 硬门** |
| **AC-GCS-09** | GPL 依赖扫描通过 | W1 | CI 命令写入 ACCEPTANCE |
| **AC-GCS-BLIND** | 海报「可发」≥55% 方可默认露出 | W3 | Gate 码独立；可共用 trip 集 |
| **AC-GCS-10** | 用户文案不含「九宫格」顶替海报 | W2 | 文案/fixture 扫描 |

W1 merge 前须拆独立 ACCEPTANCE 细化命令与 fixture 路径。

**Fixture 最小集（评审冻结）**

- 轨 B：`n=3/6/9` 各 1（混 AR）+ `n=2` 禁用 + collage 排除 1  
- 轨 A：合法通过 1 + 重叠/越界拒绝 1  
- 回归：既有杂志 golden / LRG smoke 子集  

---

## 11. 风险

| 风险 | 缓解 |
|------|------|
| 当成 MCS 救场银弹 | OUT-01 + AC-GCS-01 + CR |
| BRIC→YAML 失真 | BLK-02：轨道原生 + 丢弃 |
| 海报工具感 | ▾ 入口 + 盲评门禁 |
| 依赖/许可 | 强制 vendor + 扫描 |
| 与九宫格/长图混淆 | 分名、分 Writer、AC-GCS-10 |
| 新 SKU 无 usage 不降 legacy | D-GCS-08 + URO 可消费字段 |

---

## 附录 A · 开源对标摘要（stefanwayon/collage）

| 项 | 内容 |
|----|------|
| 论文 | C. Brian Atkins, *Blocked Recursive Image Composition*（ACM） |
| 形态 | Python 库 + CLI |
| 核心 API | `fit_pictures_balanced(sizes, width, border, spacing, round_result)` |
| 硬约束 | 保 AR、不重叠、统一 gutter/border；**不做裁切** |
| 在本 PRD | **仅轨 B** 直接消费；轨 A 用同族思想做**离散轨道**枚举 |

## 附录 B · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-18 | 初稿：双轨；禁 MCS runtime fallback |
| **v0.2.0** | 2026-07-18 | 跨职能 Conditional Go：BLK-01～08；OQ 全关；轨 A 轨道原生；轨 B job sidecar；先 B 后 A |
