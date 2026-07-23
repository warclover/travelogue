# Travelogue · 拼图槽位自适应 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · M0～PR-C 已落地**（[七席](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md) · 默认仍 off · **AC-09 实册盲评开放**） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「拼图槽位自适应 V1」— **MSA**（Mosaic Slot Adaptation） |
| **调研来源** | 2026-07-23 实机狗粮：单反 3:2 横图进 16:9 扁槽高度不够 / cover 裁切过重；用户画像（全单反 / 全手机 / 混排）与 AR 分布补充；业界 BRIC / SoftCollage / 消费级拼贴对照 |
| **审查基线** | 现行 LTE YAML 固定 `cols/rows` + MCS 默认 `fit=cover` + MTSO 选型合同（选型与本主题正交） |
| **关联文档** | [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [P15 MCS](./PRD-PHASE15-photo-mosaic-evolution.md) · [P16 LTE](./PRD-PHASE16-layout-template-engine.md) · [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) · [6 张拼图](./PRD-6张拼图优化.md) · [DESIGN-PHASE15](./DESIGN-PHASE15-mosaic-system.md) |
| **评审纪要** | [acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md)（结案）· [模板](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-TEMPLATE.md) |
| **验收** | [ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md](./ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md) · [IMPLEMENTATION-…](./IMPLEMENTATION-MOSAIC-SLOT-ADAPTATION-V1.md)（BLK-05 ✅）· 摘要见本文 §10 |
| **更新日期** | 2026-07-23 |

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-07-23）**
>
> 1. **O-04 关闭**：`trackOverride` + `slots[].fit` **持久化进 screen**；preview/export/重渲染共用。  
> 2. **mobile 变体**：每个激活 `stage.variants` **各自求解**；失败则该 variant 回退静态轨并打点（非只解 web 16:9）。  
> 3. **峰判定硬化**：单一梯子占比 ≥0.60、梯子容差 0.08 进合同/AC。  
> 4. **contain 底色**：默认杂志纸色；M2 前出最低视觉合同（BLK-06）。  
> 5. **Conditional Go**：可 Kickoff M0；M1/M2 合码挡 BLK 如上。

> **定位**
>
> 现网拼图在 **选型与调度**（MTSO）上已走向「选对脸」；但落到屏上仍是 **固定轨道度量 + cover 塞图**。单反横图 3:2、手机横图 4:3 与大量接近舞台 16:9 的 landscape 槽冲突，导致「高度不够、主体被砍」——这是 **几何合同问题**，不是再调 `base_weight` 能根治的。
>
> 本 PRD 把拼图从「固定格子塞图」升级为 **「杂志拓扑不变 · 轨道权重按窗自适应 · 高风险槽允许合法留白」**，在不改槽位数、不改主从叙事样式的前提下，兼容单反 / 手机 / 混排。

> **一句话目标**：**舞台仍 16:9；模板拓扑不变；槽位长宽比跟着照片走；宁留白不毁构图；混设备同一屏一种气质。**

> **完成定义**

| 门 | 含义 | 不等于 |
|----|------|--------|
| **M0 Go** | 决策表锁定 + 术语/边界与 MTSO 切清 + 合成 fixture 度量合同 | 改默认 GA 几何 |
| **M1 Go** | 窗级 AR profile + 轨道求解进候选路径；主槽目标贴窗峰；父开关默认 off | 学习型拓扑；全库手调 YAML |
| **M2 Go** | crop_risk → 条件 contain；主/辅分权评分；混峰轨道；漏斗可解释 | SoftCollage / GA 搜树 |
| **M3 Go** | 三类画像狗粮 + 盲评；默认 on 另决策；acceptance-records 闭环 | 舞台改 3:2 |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **正交** | MTSO = **选哪张脸（模板族）**；MSA = **脸的五官比例（同族内度量）**。禁止把 MSA 塞进 MTSO PR-D 转正指标 |
| [P16 LTE](./PRD-PHASE16-layout-template-engine.md) | **继承 SSOT** | YAML 仍定义拓扑与角色；MSA 输出的是 **实例级轨道权重覆盖**，不是另起一套模板库 |
| [P15 MCS](./PRD-PHASE15-photo-mosaic-evolution.md) | **继承候选/打分壳** | 在 compose/build 路径插入 profile→solve→fit；不重写 MCS-11 活跃集政治 |
| [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) | **互补** | MGQ 记几何特征；MSA 用特征驱动轨道与 crop_risk |
| [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) | **不替代** | mix/eligibility 仍权威；轨道自适应不得制造静默空候选 |
| [P21](./PRD-PHASE21-mosaic-density-budget.md) | **继承硬上限** | 不放宽 dense/相邻/large；轨道变化不绕过配额 |
| [QFX](./PRD-QUALITY-FIXPACK-V1.md) / [NAS](./PRD-NO-AI-SURFACE-V1.md) | **正交** | 不碰合入门禁 / AI 表面 |

### 0.2 非目标（明确不做）

| ID | 非目标 | 理由 |
|----|--------|------|
| **N-01** | 把整本舞台从 16:9 改为 3:2 | 长图 / Web / mobile 变体契约成本过高 |
| **N-02** | 为每种设备复制整套 YAML | 组合爆炸；混排无法用「设备标签」二分 |
| **N-03** | M1–M2 引入 SoftCollage / GA 搜拓扑树 | 与杂志品牌一致性、可验收回归冲突 |
| **N-04** | 全页强制 `contain` | 破坏满幅杂志感；仅高 crop_risk 合法留白 |
| **N-05** | 用 EXIF「相机型号」做主路由 | 不可靠、隐私差；以 **窗级 AR 直方图** 为准 |
| **N-06** | 放宽朝向硬门（竖进宽槽等） | 已用血泪换来的及格线；MSA 加强而非回退 |
| **N-07** | 改变槽位数或主从叙事拓扑 | 产品约束：样式不变；只变量度与 fit |

### 0.3 代码事实（2026-07-23 · 讨论基线）

| ID | 事实 |
|----|------|
| **F-01** | LTE `stage.cols/rows` 为模板静态权重；`displayAspect = (col_frac/row_frac)×stageAR` |
| **F-02** | 舞台默认 **16:9**；大量 landscape 槽 `displayAspect≈1.6–1.8` |
| **F-03** | mosaic builders / LTE adapter 对 landscape / main 默认 **`fit=cover`**；竖槽有 `portrait_fit` 分支 |
| **F-04** | 存在 `preferLadder` / `main_ar_guard` / `f_aspect_fit` 雏形，但 **不改轨道**，主要影响「谁能进主槽」 |
| **F-05** | 单反横 **3:2≈1.50**、手机横 **4:3≈1.33** 与扁槽 1.78 的 cover 裁切分别约 **15% / 25%**（相对照片短边量级） |
| **F-06** | MTSO 已落地选型/硬拒/实验门；**不**解决同模板内槽 AR 与照片 AR 错配 |

### 0.4 用户可感知问题 → 落点

| ID | 问题 | 严重度 | 落点 |
|----|------|--------|------|
| **Q1** | 单反横图进扁槽，上下被砍，地平线/脚/头顶受伤 | **P0** | D-03 · D-04 · S-02 |
| **Q2** | 手机 4:3 裁切更狠，大众用户「说不清哪里不对」 | **P0** | D-03 · D-05 |
| **Q3** | 混排时一套固定槽两头不讨好 | **P0** | D-05 · S-03 |
| **Q4** | 拼图「整齐但不高级」——缺装裱感与少毁构图纪律 | **P1** | D-06 · D-08 · S-04 |
| **Q5** | 调模板堆 SKU 无法覆盖 AR 连续谱 | **P1** | D-01 · D-02 |

---

## 1. 背景与根因

### 1.1 三层 AR 被错误绑死

```text
舞台 AR（16:9，交付契约）
    ↓ 不应被照片绑架
拓扑（槽数、角色、邻接 = 杂志样式）
    ↓ 应稳定
轨道权重 → 槽 displayAspect（应对齐照片）
    ↓
fit（cover / contain）→ 裁切或留白
```

**现状**：舞台 AR 通过静态轨道几乎直接决定槽 AR，再用 cover 强迫照片服从槽——把「杂志页比例」与「相机底片比例」混为一谈。

### 1.2 为什么现网只到及格

| 能力 | 贡献 | 上限 |
|------|------|------|
| 朝向硬门 / 主 AR ladder | 挡住最离谱错向 | 不修「横图进略扁横槽」 |
| MTSO 选型 | 选对主从模板 | 同族内度量仍固定 |
| cover + sharpness | 满幅整齐 | 对摄影向构图不友好 |
| 固定 YAML 几何 | 可回归 | 无法服务 1.33–1.78 连续谱 |

**产品判断**：继续加 YAML 变体 **不能**根本解决；必须把 **度量**从模板静态字段提升为 **窗级求解结果**。

---

## 2. 目标与成功标准

### 2.1 目标

| ID | 目标 | 衡量 |
|----|------|------|
| **G-01** | 同拓扑下槽 AR 按窗自适应 | 主槽 \(|r_{slot}-r^*|\) 中位显著下降（§10） |
| **G-02** | 单反 / 手机 / 混排均可读 | 三类画像盲评 ≥ 基线，无「一刀切毁主体」 |
| **G-03** | 合法留白优于毁构图 | 高 crop_risk 槽 contain；整页 whitespace ≤ 预算 |
| **G-04** | 可解释、可回归 | 日志含 profile / 轨道 / fit 决策；父开关 OFF = 基线逐屏一致 |
| **G-05** | 与 MTSO 解耦 | MSA OFF 时 MTSO 行为不变；MSA ON 不改模板生命周期 |

### 2.2 成功北星（人话）

> 打开一本单反游记：主图像「装进合适画框」而不是「塞进宽银幕条」；手机游记同样舒服；混设备时一页一种气质，而不是每张图各打各的仗。

---

## 3. 术语

| 术语 | 定义 |
|------|------|
| **拓扑（topology）** | 槽数、角色、邻接与 `rect` 格子归属；**MSA 不改** |
| **轨道权重（track weights）** | `stage.cols[]` / `stage.rows[]`；决定各槽面积与 displayAspect |
| **模板族（family）** | 同一拓扑契约下的 YAML id（如竖主 1P4L）；可有多个 **参数实例** |
| **窗级 AR profile** | 对候选窗照片朝向与 \(r=w/h\) 的统计标签（§6.1） |
| **目标主槽 AR \(r^*_{hero}\)** | 求解器希望主槽达到的显示比（通常取窗横峰） |
| **crop_risk** | 在给定 fit=cover 下，预计裁切强度 × 主体受损代理（脸/focal 靠边等） |
| **whitespace_budget** | 整屏因 contain/letterbox 产生的非影像面积占比上限 |
| **参数实例（parametric instance）** | 拓扑 id + 求解后的轨道权重 + 每槽 fit；渲染与日志以此为准 |

### 3.1 素材 AR 梯子（工程常量 · 可配置）

| 标签 | 标称 \(r\) | 典型来源 |
|------|-----------|----------|
| `land_3_2` | 1.50 | 单反/无反横 |
| `land_4_3` | 1.333… | 手机横默认 |
| `land_16_9` | 1.777… | 手机宽银幕 / 视频截帧 |
| `port_2_3` | 0.666… | 单反竖 |
| `port_3_4` | 0.75 | 手机竖 |
| `other` | — | 方图、超宽、超竖；不进峰标签，单独处理 |

---

## 4. 用户画像与兼容策略

| 画像 | 概率（产品假设） | 窗横峰 | 默认 \(r^*_{hero}\) | 备注 |
|------|------------------|--------|---------------------|------|
| **A 全单反** | 低·质量最高 | `land_3_2` | **1.50** | 主槽禁贴 16:9 |
| **B 全手机** | **最高** | `land_4_3`（偶发 `land_16_9`） | **1.33**；若 ≥阈值比例为 16:9 则切 **1.78「电影轨」** | 大众路径 |
| **C 混排** | 中 | 双峰或宽峰 | **窗内横图 median**（夹在 \[1.30, 1.60\]） | **同一屏共用一套轨道**；不为单张极端化 |

**禁止**用「文件来自 iPhone/Canon」作为主信号；可用作 telemetry，不可作硬路由。

---

## 5. 已拍板决策（七席锁定 · v0.2.0）

> 下列决策经 [七席评审](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md) 锁定。数值可在 AC/盲评内微调，但 **D-01/D-02/D-07 架构选择** 若推翻需重写本 PRD。

| 决策 | 锁定结论 |
|------|----------|
| **D-MSA-01 分层合同** | 舞台 AR 稳定 16:9（及既有 mobile 变体）；**拓扑稳定**；**轨道权重与 fit 可变**。 |
| **D-MSA-02 参数实例** | MSA 不新增「平行模板库」；对已选 `patternId` 生成 `trackOverride` + `slotFits[]`。**持久化进 screen**（建议挂 `layoutGeometry.trackOverride` + 每槽 `fit`）；preview / 长图导出 / 重渲染 **必须复用同一实例**（七席 BLK-02）。 |
| **D-MSA-03 主槽目标** | \(r^*_{hero}\) 取窗级横峰梯子（§4）；**禁止**默认把主槽目标设为舞台 16:9。主槽面积 / prominence 合同 **不得因自适应而跌破** 模板声明下限（继承 MTSO/MGQ 阈值；缺省 main≥0.55、prominence≥3 仅适用于声明为 extreme hero 的族）。 |
| **D-MSA-04 辅槽纪律** | 辅槽可略扁/略方以消化剩余空间；但 **强构图横图不得分到窗内最扁辅槽**（分配约束）。 |
| **D-MSA-05 混峰策略** | 混排用 median 夹逼；整屏一套轨道；禁止「每槽各算各的极端 AR」。 |
| **D-MSA-06 留白合法** | 仅当 `crop_risk ≥ θ` 时该槽允许 `contain`（或等价 letterbox）；整页 `whitespace_ratio ≤ W_max`（默认建议 **0.08**）。超预算则回退 cover 或重求解轨道。 |
| **D-MSA-07 开关** | `mosaic.slot_adaptation.enabled` 默认 **false** 至 M3；父 OFF ⇒ 子项无效，行为 = 今日基线（AC-10 对齐精神）。 |
| **D-MSA-08 与 MTSO** | MSA 在 **模板已选定之后** 作用；不改变 lifecycle / experiments / mixed_routing。日志分字段，验收分文档。 |
| **D-MSA-09 求解失败** | 无可行轨道 ⇒ **保持模板静态轨道** + 记录 `msa_solve_miss`；**禁止**静默空屏或改拓扑。 |
| **D-MSA-10 可观测性** | raw 日志必含：`msaProfile`、`rHeroTarget`、`trackOverride`、`slotFits`、`cropRisk[]`、`whitespaceRatio`、`msaOutcome`。 |
| **D-MSA-11 非学习拓扑** | M1–M2 **禁止** SoftCollage/GA 搜树；M3 仅当盲评证明轨道自适应仍不足时另立 spike。 |
| **D-MSA-12 成功指标** | 主：主槽 AR 误差中位下降；辅：高 crop_risk 槽的毁主体投诉/盲评项下降；约束：whitespace 超标率≈0、父 OFF 基线一致、dense/朝向红线不回退。 |

### 5.1 配置合同（草案）

```yaml
mosaic:
  slot_adaptation:
    enabled: false                 # 父开关；仓库默认 false 至 M3
    whitespace_max: 0.08           # 整页非影像面积上限
    crop_risk_contain_threshold: 0.55
    hero_target_clamp: [1.30, 1.60]  # 混峰 median 夹逼
    land_peaks:
      three_two: 1.50
      four_three: 1.3333
      sixteen_nine: 1.7778
    # 电影轨：窗内 land_16_9 占比 ≥ 此值才切 r*=1.78
    wide_peak_fraction: 0.50
    solve:
      max_iters: 32
      track_weight_min: 0.5
      track_weight_max: 24.0
```

---

## 6. 系统性方案（架构）

### 6.1 总览

```text
窗资产 → [MTSO/MCS 选 patternId + 粗排序]
              ↓
         MSA profile（朝向 + AR 峰）
              ↓
         轨道求解（拓扑固定 · 权重可变）
              ↓
         分配精修（主/辅 · 禁最扁槽喂强图）
              ↓
         crop_risk → fit（cover | contain）
              ↓
         渲染（CSS grid 用 override 权重）
```

### 6.2 窗级 AR profile（S-MSA-01）

**输入**：窗内 `assetIds` + `aspects` + `width/height`。  
**输出**（写入日志 `msaProfile`）：

| 字段 | 含义 |
|------|------|
| `nLand` / `nPort` / `nOther` | 计数（std 朝向；square/tall 入 other） |
| `landPeak` | `three_two` \| `four_three` \| `sixteen_nine` \| `mixed` \| `none` |
| `portPeak` | `two_three` \| `three_four` \| `mixed` \| `none` |
| `landMedianR` | 横图 \(r\) 中位数 |
| `rHeroTarget` | 决策后的 \(r^*_{hero}\) |

**峰判定（七席锁定 · AC 可测）**：

1. 收集横图 \(r\)；映射到最近梯子（**容差 = 0.08**）。  
2. 若单一梯子占比 **≥ 0.60** → 该峰；  
3. 否则若 `land_16_9` 占比 ≥ `wide_peak_fraction`（默认 0.50）→ `sixteen_nine`；  
4. 否则 → `mixed`，\(r^*=clamp(median, hero_target_clamp)\)。

### 6.3 轨道求解（S-MSA-02 · 核心）

**给定**：

- 模板拓扑：`cols` 段数、`rows` 段数、每槽 `rect`  
- 约束：主槽面积 / prominence 下限（来自模板 eligibility 或族默认）  
- 目标：主槽 displayAspect → \(r^*_{hero}\)；辅槽 AR 落入可接受带；权重有界

**输出**：`trackOverride: { cols: number[], rows: number[] }`

**求解策略（M1 建议）**：

1. **解析/启发式**（优先）：对常见族（左主右轨、上主下带、三列竖主从）用闭式或少量牛顿迭代调「主列 vs 辅列」权重，使 main AR 命中。  
2. **小规模数值搜索**（通用后备）：在权重盒约束内随机/网格搜索，目标函数：

\[
L = w_1(r_{main}-r^*)^2 + w_2\sum_i \mathrm{hinge}(r_i \notin Band_i)^2 + w_3\mathrm{hinge}(A_{main}<A_{min})
\]

3. 失败 → D-09 回退静态轨道。

**族白名单（M1）**：先覆盖曝光最高的 hero 族（5/6 图横主、竖主 1P4L/2P3L、4 图 hero sidebar）；平铺 dense 可 M2。

### 6.4 分配精修（S-MSA-03）

在拓扑 ordering 之后、finalize 之前：

| 规则 | 说明 |
|------|------|
| 主槽 | 保持 MCS/MTSO 主图选择；若主图 \(r\) 与 \(r^*\) 仍大偏差，优先 **重求解** 而非换主图（避免叙事抖动） |
| 辅槽 | 横图按「质量 × (1−扁槽惩罚)」分配；**窗内最扁槽**不得接收 crop_risk 最高的横图 |
| 竖槽 | 继续朝向诚实；不在此放开竖进宽槽 |

### 6.5 fit 与留白（S-MSA-04）

对每槽：

```text
if fit 已由 portrait_fit 等特殊路径指定 → 尊重
else if crop_risk >= θ and whitespace 预算允许 → contain
else → cover
```

**crop_risk 代理（M1）**：

\[
\mathrm{crop\_risk} = \mathrm{clip}_{0..1}\Big(\alpha\cdot\big|1-\tfrac{\min(r_p,r_s)}{\max(r_p,r_s)}\big| + \beta\cdot\mathbb{1}_{face/focal\_near\_edge}\Big)
\]

M2 可接人脸框×槽 IoU（承接 DESIGN-PHASE15 D-MCS-14 几何版）。

**留白表现**：contain 时使用与杂志页一致的底（纸色/暗角策略另开视觉任务）；**禁止**花哨相框贴纸。

### 6.6 渲染合同（S-MSA-05）

| 层 | 要求 |
|----|------|
| CSS | 实例轨道写入 inline style 或生成临时 grid-template；**不得**改写仓库静态 YAML 默认 |
| screen JSON | **必写**：`layoutGeometry.trackOverride`、`slots[].fit`、`slots[].displayAspect`（实渲）；重渲染只读复用 |
| 长图/导出 | 与预览同一实例；禁止导出路径丢掉 override |
| **stage.variants** | **每个激活 variant（如 web 16:9 / mobile 9:16）各自求解**；某 variant 求解失败 → 该 variant 回退模板静态轨 + `msa_solve_miss`（分 variant 打点）；禁止只优化 web |

### 6.6.1 contain 视觉底线（M2 · BLK-06）

| 项 | 合同 |
|----|------|
| 底色 | 默认 **杂志纸色**（与页背景一致）；禁止花哨相框/贴纸 |
| 适用范围 | 仅 `crop_risk≥θ` 且未超 `whitespace_max` 的槽 |
| 竖槽 | 可继续复用既有 `portrait_fit→contain` 语义，避免第二套 fit 方言 |

### 6.7 评分跃迁（S-MSA-06 · 从及格到优秀）

在现有 MCS 分上增加/升权（可开关）：

| 信号 | 作用 |
|------|------|
| `aspect_fit`（主权重大 / 辅权重小） | 少错配 |
| `crop_risk_penalty` | 毁主体惩罚 |
| `whitespace_penalty` | 超预算惩罚 |
| `track_solve_bonus` | 成功命中 \(r^*\) 小奖励（防过拟合可关） |

**审美原则（写进狗粮评分表）**：

1. 一张英雄，其余陪衬（面积已有合同）  
2. 朝向诚实  
3. 少毁构图  
4. 时间/burst 邻近  
5. 混设备时整页气质统一  

---

## 7. 业界对照与定位

| 路线 | 代表 | 优势 | 劣势 | 与 MSA |
|------|------|------|------|--------|
| **固定模板 + cover** | 多数消费级 App、现网 Travelogue | 可控、快、品牌稳 | AR 错配裁切 | **起点** |
| **BRIC 递归剖分** | Atkins 等 | 保照片 AR、混尺寸友好 | 难保证固定杂志拓扑与 CSS 库 | **借鉴度量求解，不替换拓扑** |
| **GA / SoftCollage** | 学术 / 部分产品 | 覆盖率与信息量 | 不可解释、难回归、品牌漂移 | **M3+ spike only** |
| **MSA（本 PRD）** | — | 拓扑品牌 + 照片友好 + 可验收 | 需求解放束求解器工程 | **选定路线** |

**竞争叙事**：不做「又一个自由拼贴器」；做 **「会量体温的杂志排版」**——设计师定骨相，算法量五官。

---

## 8. 里程碑与 PR 列车

| 里程碑 | PR 建议 | 退出 |
|--------|---------|------|
| **M0** | 文档 + 决策评审 | 本文 v0.1 → Conditional Go；拆 ACCEPTANCE/IMPL |
| **M1** | PR-A：profile + 族白名单求解 + 日志 + 父开关 | AC-01～05；父 OFF 基线一致 |
| **M2** | PR-B：crop_risk contain + 分配精修 + 混峰 + 评分项 | AC-06～08；whitespace 预算 |
| **M3** | PR-C：三类画像狗粮 + 盲评 + 默认 on 决策 | AC-09～11；记录转正/保持 off |

**合并规则**：M0 未 Go 不开码；M1 未绿不得合 M2；**禁止**单 PR 塞满 M1–M3。

---

## 9. 触点清单（实施时展开）

| 触点 | 动作 |
|------|------|
| `travelogue/config/mosaic.py` | `SlotAdaptationConfig` + 解析 |
| `travelogue/layout_engine/mosaic/msa_profile.py`（新） | 窗级 profile |
| `travelogue/layout_engine/mosaic/msa_solve.py`（新） | 轨道求解 |
| `travelogue/layout_engine/mosaic/compose.py` / `builders.py` / `lte_adapter.py` | 接入实例覆盖与 fit |
| `travelogue/render/*` | grid 权重 / contain 底 |
| `travelogue/layout_engine/mosaic/log.py` | D-10 字段 |
| `tests/unit/layout_engine/test_msa_*.py` | 合成单反/手机/混峰 |
| `docs/config-msa-dogfood.example.yaml` | 本机狗粮 |
| `docs/acceptance-records/msa-*-2026-*.md` | 基线·盲评 |

---

## 10. 验收（AC）

| AC | 条件 |
|----|------|
| **AC-MSA-01** | `slot_adaptation.enabled=false` 时固定 corpus 与基线逐屏一致（patternId、asset 序、静态几何）；嵌套子开关无效 |
| **AC-MSA-02** | 全单反横窗 fixture：求解后主槽 \(|r-1.50|≤0.08\)（或文档约定容差）；main 面积/prominence 不跌破合同 |
| **AC-MSA-03** | 全手机 4:3 横窗：主槽贴 1.33±容差 |
| **AC-MSA-04** | 混峰窗：`landPeak=mixed`，\(r^*\) 落在 clamp 内；整屏单一 `trackOverride` |
| **AC-MSA-05** | 求解失败 → 静态轨道 + `msa_solve_miss`；无空屏 |
| **AC-MSA-06** | 高 crop_risk 槽 → contain；整页 whitespace ≤ `whitespace_max` |
| **AC-MSA-07** | 最扁辅槽不接收窗内 crop_risk 最高横图（分配约束单测） |
| **AC-MSA-08** | raw 日志含 D-10 全字段；禁止只读展示层验收 |
| **AC-MSA-09** | 三类画像狗粮：盲评「主体完整性」优于基线；无朝向/dense 红线回退 |
| **AC-MSA-10** | MTSO 开关组合回归：MSA ON/OFF × experiments/SO 不交叉破坏 lifecycle |
| **AC-MSA-11** | 默认 on 决策前：独立盲评记录；不通过则保持默认 off |

---

## 11. 风险与回滚

| 风险 | 缓解 | 回滚 |
|------|------|------|
| 轨道求解不稳定 / 闪烁 | 权重盒约束；同窗缓存；失败回退静态 | 关 `slot_adaptation` |
| 留白过多像贴图板 | `whitespace_max`；超预算禁 contain | 提高 θ 或关 contain 子开关 |
| 与 CSS/长图不一致 | 实例几何单一路径进 render/export | 关 MSA |
| 性能 | M1 仅白名单族 + 迭代上限 | 缩白名单 |
| 指标与 MTSO 搅合 | 分文档分漏斗字段 | — |

**回滚顺序**：`slot_adaptation.enabled=false` →（可选）清 screen 上 override 字段 → **保持 MTSO/P21 不变**。

---

## 12. 狗粮与对照语料

| 语料 | 关注 |
|------|------|
| 合成：6× 3:2 横 | 主槽贴 1.5；裁切量 |
| 合成：6× 4:3 横 | 主槽贴 1.33 |
| 合成：3×3:2 + 3×4:3 | mixed + 统一轨道 |
| 合成：含 16:9 手机宽图过半 | 电影轨 |
| 实册：摄影向单反行程 | Q1 |
| 实册：纯手机大众行程 | Q2 |
| 实册：团队混设备 | Q3 |

对照：同一 trip `slot_adaptation` on/off + 截图盲评表（主体完整性 / 杂志感 / 气质统一）。

---

## 13. 开放项

| # | 问题 | 状态 |
|---|------|------|
| **O-MSA-01** | `whitespace_max` 默认 0.08 | **暂定 0.08** · M3 盲评可 ±0.02 |
| **O-MSA-02** | contain 底色 | **默认杂志纸色** · M2 前出样（BLK-06） |
| **O-MSA-03** | M1 族白名单最终列表 | **开放** · 候选：横主 5/6 hero、竖主 1P4L/2P3L、4-hero-sidebar |
| **O-MSA-04** | screen 是否持久化 override | **已关（持久化）** · 见 D-02 / BLK-02 |
| **O-MSA-05** | 默认 `enabled=true` 时机 | **Hold off** · 见 [决策 2026-07-23](./acceptance-records/msa-default-on-decision-2026-07-23.md)；AC-09 签核前保持 false |

---

## 14. Must-Fix / 评审挡门（草案）

| ID | 挡 | 说明 |
|----|----|------|
| **BLK-MSA-01** | M0 | ✅ D-01/D-02 确认不推翻 |
| **BLK-MSA-02** | M1 | ✅ 持久化 · PR-A 已实现 |
| **BLK-MSA-03** | M1 | ✅ 峰判定 · PR-A fixture 已锁 |
| **BLK-MSA-04** | M1 | ✅ variant 各自求解 · PR-A 已实现 |
| **BLK-MSA-05** | M1 | ✅ 已拆 [ACCEPTANCE](./ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md) / [IMPLEMENTATION](./IMPLEMENTATION-MOSAIC-SLOT-ADAPTATION-V1.md) |
| **BLK-MSA-06** | M2 | ✅ [contain 纸色合同](./acceptance-records/msa-contain-visual-contract-BLK06.md) · PR-B |
| **BLK-MSA-07** | M1 | ✅ 面积/prominence 硬断言进 AC |
| **BLK-MSA-08** | M1 | ✅ 日志字段进 AC-08 |

---

## 15. 系统解法摘要（给评审一页纸）

| ID | 解法 | 对应决策 |
|----|------|----------|
| **S-MSA-01** | 窗级 AR profile（峰/混峰/电影轨） | D-03 · D-05 |
| **S-MSA-02** | 拓扑固定下的轨道权重求解 | D-01 · D-02 · D-09 |
| **S-MSA-03** | 分配精修（最扁槽保护） | D-04 |
| **S-MSA-04** | crop_risk → 条件 contain + 留白预算 | D-06 |
| **S-MSA-05** | 渲染/导出同一参数实例 | D-02 · D-10 |
| **S-MSA-06** | 可解释美学分升权 | D-12 |
| **S-MSA-07** | 默认 fail-closed 开关 | D-07 |

---

## 16. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-23 | 首稿：实机 3:2 vs 16:9 槽问题 + 三画像 +「拓扑固定·轨道可变」根本路线 + BRIC/SoftCollage 对照；Draft Ready for Review |
| **v0.2.0** | 2026-07-23 | 七席 Conditional Go 回写：持久化实例 · variant 各自求解 · 峰判定硬化 · contain 纸色底线 · 可 Kickoff M0 |
| **v0.2.0+M0** | 2026-07-23 | BLK-05：拆 ACCEPTANCE/IMPLEMENTATION；DOC-STATUS/README 挂链（文档列车，无语义变更） |
