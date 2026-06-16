# Travelogue · 人像质量与下游择优 PRD（Portrait Quality Gate）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.3.0-PORTRAIT-QG |
| **状态** | Reviewed · Ready for M1（架构评审已合入 F1–F4） |
| **代号** | 「人像质量与下游择优」— 一份人像信号，服务封面/封底/高光池/决定性瞬间/拼图主图 |
| **文档别名** | `PRD-PORTRAIT-CULL.md`（路径不变，便于链接） |
| **前置条件** | [PRD-PHASE9.md](./PRD-PHASE9.md)（Quality Gate）、[PRD-PHASE12.md](./PRD-PHASE12.md)（分支化评分；**本 PRD 为 Phase 12 §5.1 权威实现规格**）、[DESIGN-PHOTO-AESTHETIC-EVALUATION.md](./DESIGN-PHOTO-AESTHETIC-EVALUATION.md)（PA 美学层） |
| **关联文档** | [PRD-PHASE9-A-quality-gate-algorithm.md](./PRD-PHASE9-A-quality-gate-algorithm.md)、[PRD-PHASE9-C-data-model.md](./PRD-PHASE9-C-data-model.md)、[PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md)、[cover-selection-plan.md](./cover-selection-plan.md) |
| **实现模块（规划）** | `travelogue/media/portrait_analyze.py`（新建）、`travelogue/media/ingest.py`、`travelogue/curation/photo_cull.py`、`travelogue/curation/aesthetic_score.py`、`travelogue/config/cull.py`、`schemas/trip.schema.json` |
| **更新日期** | 2026-06-16 |

> **定位（v0.3 重定向）**
>
> - 在 **零打扰、全自动** 前提下，提取一份 **人像质量信号**，并让它服务于**两类消费者**：
>   1. **选片闸口**（`photo_cull`）：连拍/相似择优、缺陷降权；
>   2. **下游择优**（统一经 `aesthetic.subjectClarity` + `purpose_overall`）：**封面、封底、高光池、决定性瞬间、拼图主图**。
> - **核心收益在下游**：用户的真实诉求是「挑出睁眼、清晰、正脸的人像」去当封面/hero/主图——这条链路**不依赖** `photo_cull` Pass 2，而是经 PA 美学层传播（见 §4、§6）。
> - **不做修图**（不改像素）；仅提取信号并被消费。
> - **与 Phase 12 分工**：本 PRD 落地 P12 §5.1 人像细粒度信号 + Pass 1' 规则；不含 `category_coherence`、11 类 L1。

---

## 0. 评审决议与拍板（v0.3 · 已全部裁定）

### 0.1 产品/早期评审决策（v0.2 沿用）

| ID | 结论 |
|----|------|
| **D1** | featured 不参与 `duplicate_group` 淘汰（与 P9 既有语义一致） |
| **D2** | Shadow mode 在 M1.5 启用（以 **trip 数** 计，见 S10），telemetry 达标再开 Pass 2 PK |
| **D3** | 检脸：Haar gate + landmarks；bbox 扩边 20% |
| **D4** | 对外命名「人像质量选片」 |

### 0.2 架构评审决策（v0.3 新增 · 我作为首席架构师拍板）

| ID | 议题 | **裁定** | 理由 |
|----|------|----------|------|
| **D5** | F1 注入点 | **C 起步 + A 路线 + 下游为主**：①ingest burst/phash 替换判据由「纯 sharp」改为 `tiebreak(sharp, eyesOpen轻量)`；②`photo_cull` 对**多成员 burst 组**开启人像 PK；③**主收益走下游 `aesthetic.subjectClarity`**，与 ingest 去重解耦 | 既修正「连拍择优发生在 ingest」的事实，又把用户要的封面/hero/主图收益放在更稳的 PA 层 |
| **D6** | F2 MediaPipe | **检测器抽象 + 多后端**：`FaceLandmarkBackend` 抽象；优先 `mediapipe`，缺 wheel 时回退 `onnxruntime`（106 点），都不可用则 skip。CI vision job 锁 **Py 3.11** | 本地 Py 3.13/3.14 上 mediapipe 无 wheel，不能让主线依赖单一后端 |
| **D7** | F4 基线一致 | **A**：所有 portrait 引起的权重/分支变化，**门控在「该 asset 有 portrait 信号」**；无信号资产分数与序与 P9 基线逐位一致 | 保住 AC-PC-02 可证伪性 |
| **D8** | 总体 | F1 由「致命」降级为「已解决」；**有条件通过 → v0.3 进入 M1** | F1–F4 已在本版落地 |

**评审结论**：v0.2 有条件否决（F1 致命）→ **v0.3 合入 F1–F4 与下游集成 → Ready for M1**。

---

## 1. 设计原则（硬约束）

| ID | 原则 | 约束说明 |
|----|------|----------|
| **PC-PR-01** | 零打扰 | 不新增用户确认、复核、挑图 UI；敏感度仅 yaml 配置 |
| **PC-PR-02** | 保守可逆 | 不确定样本默认保留；低置信不作 hard_exclude 依据 |
| **PC-PR-03** | fail-open | 分析失败不阻断导入；cull 回退 P9/P12 既有逻辑 |
| **PC-PR-04** | 不做修图 | 不做人像美颜、曝光修复、生成式改图 |
| **PC-PR-05** | 个人可落地 | W1 CPU 轻量（MediaPipe）；重型 FIQA 仅 W3 试点 |
| **PC-PR-06** | 可解释 | `cullExplain` / debug 模式保留中间量 |
| **PC-PR-07** | 确定性 | 同 asset 元数据 + config → 同 cull 结果；tie-break 链不变 |
| **PC-PR-08** | 信号分层 | **ingest 写原始/局部归一**；**cull 写批内归一与淘汰决策**（见 §4.4） |

---

## 2. 背景与问题

### 2.1 竞品参考（附录 · 非承诺指标）

商业产品（如像素蛋糕 AI 挑图）典型流程：缺陷检测 → 正向精选 → 场景 preset → 组内对比。官方说明见 [使用手册](https://wiki.pixcakeai.com/guide/9391.html)。

**本产品的承诺指标**：连拍组内优选命中率、闭眼/糊脸召回、封面/章英雄缺陷率下降（§3.1），**不**承诺「达到像素蛋糕同等精选率」。

### 2.2 Travelogue 现状差距

| 能力 | 现状 | 缺口 |
|------|------|------|
| 人脸检测 | Haar → `faceCount` / `faceRatio` / `salientBox` | 无关键点，无法判断睁眼 |
| 人像评分 | faceRatio + 整图 sharp + meanLuma | 无人脸区域清晰、睁眼维度 |
| Pass 1 | 整图 blur + mediaClass | 无人脸模糊、闭眼 |
| Pass 2 | `_preliminary_score` | 连拍组未用人像专项 PK |
| 数据字段 | P12 已规划扁平字段 | **尚未实现** |

---

## 3. 目标与非目标

### 3.1 目标

> **主目标群（下游择优 · 用户诉求所在）**

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-PC-D1** | **封面/封面分端**含闭眼/糊脸人像比例下降 | dogfood 3 人像 trip：`coverAssetId` / `coverByLayout` 选中图缺陷率 vs 基线 |
| **G-PC-D2** | **章英雄 hero** 优先睁眼清晰正脸 | hero 选中人像的 `eyesOpenScore` 中位数↑；糊脸比例↓ |
| **G-PC-D3** | **高光池 + 决定性瞬间**不选闭眼名场面 | `momentPoolIds` / `momentAssetId` 命中人像的缺陷率↓ |
| **G-PC-D4** | **拼图主图 / solo** 人脸更优 | `pick_main_for_pattern` / `solo_score` 选中人像缺陷率↓ |
| **G-PC-D5** | **封底**避免误用闭眼人脸 | `resolve_closing_asset_id` 若选人像，不为闭眼（封底本就偏风景，约束为「不踩坑」） |

> **支撑目标群（选片闸口 · 数据与稳健）**

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-PC-01** | 连拍/相似择优更优 | ingest tiebreak + 多成员 burst 组命中率 vs 基线（AC-PC-00） |
| **G-PC-02** | 降低闭眼、糊脸进入排版池 | 标注集召回；`layoutEligible` 池缺陷率 |
| **G-PC-03** | 误杀率可控 | 黄金集误杀率 ≤ P9；fail-open 通过 |
| **G-PC-04** | 时延可接受 | §9（注明人脸占比与丢弃帧假设） |
| **G-PC-05** | 信号可解释 | `cullExplain` + `aesthetic.signals` 含人像因子 |

### 3.2 非目标

- Studio 挑图 UI、商业 10 场景下拉、方糖级大模型、全量 CLIP 聚类、人像修图。
- W2 前：**全身姿态、Pass 1' 全局 penalize、hard_exclude**。
- **不重写**封面/hero/solo/moment 的选型主框架；仅通过 `aesthetic.subjectClarity` 与 purpose 权重**注入人像因子**（§6）。

### 3.3 与商业交付产品的差异

| 商业交付 | Travelogue |
|----------|------------|
| 闭眼可硬删 | M4 前禁止默认 hard_exclude；W2 起 penalize |
| 用户调敏感度 | yaml `weak/standard/strong`，默认 weak |
| 精选张数严格控制 | 服从 P9 `keep_ratio_floor`，保留有故事感抓拍 |

---

## 4. 总体架构

### 4.0 一份信号，两类消费者（v0.3 核心）

```text
                    ┌────────────────────────────┐
                    │  ingest: portrait_analyze   │
                    │  quality.portrait.*（权威）  │
                    └──────────────┬─────────────┘
                                   │
              ┌────────────────────┴─────────────────────┐
              ▼                                           ▼
   【消费者 A · 选片闸口】                      【消费者 B · 下游择优（主收益）】
   ingest burst/phash tiebreak                aesthetic.dims.subjectClarity 注入
   photo_cull Pass 1'/Pass 2                  + aesthetic.signals.portrait*
   → layoutEligible 池                         → purpose_overall(asset, purpose)
                                                 ├─ cover     (U-COVER)
                                                 ├─ hero      (U-HERO)
                                                 ├─ solo      (U-SOLO)
                                                 ├─ moment    (peak_moment_score)
                                                 └─ mosaic main(pick_main_for_pattern)
```

**关键判断（修正 F1）**：用户要的「挑睁眼清晰人脸当封面/hero/主图」属于 **消费者 B**，由 PA 美学层传播，**不经** `photo_cull` Pass 2。消费者 A 只负责「别把好片在去重时丢了 / 连拍择优 / 废片降权」。两者共享同一份 `quality.portrait`。

### 4.1 三层信号（ingest）

```text
L0  Haar gate（faceCount>0 才继续）
L1  portrait_analyze：eyesOpenScore、faceSharpness、eyeFocusRaw、confidence（W1）
L2  frontalFaceScore / poseScore / FIQA（W2/W3，可空）
→ 写入 quality.portrait.*（权威）
→ 同步刷新 quality.aesthetic.dims.subjectClarity（消费者 B 的入口，§6.3）
```

### 4.1b 选片闸口注入点（消费者 A · 修正 F1）

| 注入点 | 现状（代码事实） | 本 PRD 改动 |
|--------|------------------|-------------|
| **ingest burst 替换** | `sharp > prev_sharp` 二选一，败者**直接丢弃** | 改为 `tiebreak_score = sharp_norm + λ·eyesOpenLite`（λ 默认 0.15）；需对**将被丢弃的帧**先算轻量 EAR（§5.1.4） |
| **ingest phash 近重复** | 同上，sharp-only | 同上 tiebreak |
| **photo_cull Pass 2** | 纯素材组默认 `continue` 跳过（`recalc_strict_groups=False`） | 新增 `portrait.burst_pk`：对**多成员 burst 组**（同 `burstGroupId` 且成员>1）启用人像 PK，独立于 `recalc_strict_groups` |
| **photo_cull Pass 1'** | 无 | 闭眼/糊脸 penalize（M3） |

> **dedupeGroupId 单图组**：`dhash:<本图>` 天然单成员，Pass 2 对其无效——这是 ingest 已去重的结果，**不在本 PRD 强行恢复**（避免存储膨胀）。连拍择优靠 ingest tiebreak + burst 组 PK。

### 4.2 流水线位置（权威）

```text
scan -> dedupe -> asset build (+ portrait_analyze)
     -> photo_cull
     -> low-res gate
     -> clustering / subject tagging
     -> curate / layout scoring
```

### 4.3 `photo_cull` 内 Pass 顺序（权威）

```text
1. _reset_for_recull（若 recalc）
2. 写入 cullBranch（portrait / landscape / gray）— 全图一次性，供后续只读
3. Pass 1：_pass1_hard_exclude
4. Pass 1'：_pass1_portrait_defects（W2+；penalize 不修改 layoutEligible）
5. Pass 2：_pass2_group_winners（shadow mode 下仅写 shadowPick*，不 exclude）
6. Pass 3–4：不变
```

### 4.4 信号写入与消费分层（R1）

| 阶段 | 写入字段 | 归一化 |
|------|----------|--------|
| **ingest** | `eyesOpenScore` [0,1]（单图 EAR 映射） | 单图 sigmoid，**不依赖 trip 批统计** |
| **ingest** | `faceSharpness`（拉普拉斯原始值） | 无 |
| **ingest** | `eyeFocusRaw`（眼部 ROI 拉普拉斯原始值） | 无；可选同步 `eyeFocusScore` 为单图局部 [0,1] |
| **cull** | 消费时 `norm_face_sharp(batch)`、`norm_eye_focus(batch)` | **批内** P5–P95 或中位数比 |
| **cull** | `_portrait_quality_score` 输出 | 始终 [0,1] |

> **禁止**：在 ingest 中依赖「全 trip 百分位」写死 [0,1] 分（增量 ingest 会导致旧资产分数漂移）。

### 4.5 分支分流（继承 Phase 12）

| 分支 | 条件 | W1 人像规则 |
|------|------|-------------|
| `portrait` | `faceRatio >= 0.15` | 评分 + Pass 2 PK（shadow 后） |
| `landscape` | 低于人像阈值 | 仅 P9 逻辑 |
| `gray` | 0.10–0.20 | Pass 1' 仅 penalize（W2）；分支分取 max |

### 4.6 增量 ingest 与 recalc（R7）

| 场景 | portrait 信号 |
|------|----------------|
| **新 ingest** | 当场跑 `portrait_analyze` |
| **旧资产无 `quality.portrait`** | cull 回退旧 `_portrait_quality_score`；`cullBranchFallbackReason=face_signal_missing` |
| **`travelogue cull --recalc`** | **不**自动重跑 landmarks（避免 recalc 变慢）；可选 `--reanalyze-portrait` 触发按 asset 重分析 |
| **同图 re-ingest** | 若 `contentSig` 未变且 `portrait.version` 一致，**跳过** analyze（对齐 ingest 缓存策略） |

---

## 5. 功能规格

### 5.0 波次与里程碑（修订）

| 波次 | 交付 | 出口 |
|------|------|------|
| **M1 / PC-W1** | 检测器抽象（mp/onnx/null）+ `portrait_analyze`（睁眼+脸锐度）+ schema + **fixtures + baseline** | AC-PC-00~03、08、11 |
| **M1.5** | **下游集成（§6.3 subjectClarity）** + ingest tiebreak + Shadow mode（闸口侧） | AC-PC-D1~D4（dogfood）、AC-PC-10 |
| **M2 / PC-W1b** | `_portrait_quality_score` + 多成员 burst PK（关 shadow） | AC-PC-04、05、07、09 |
| **M3 / PC-W2** | Pass 1' penalize + 3 preset + frontalFace + purpose 权重校准 + dogfood | AC-PC-06、D5、G-PC-D1~D5 |
| **M4 / PC-W3** | hard_exclude 灰度、曝光极端、FIQA 试点、`portrait_cull_acceptance.py` | 硬剔子集 AC |

> **顺序要点（D5）**：下游主收益（M1.5 的 §6.3）**先于** 闸口 Pass 2 PK 出价值；即使 Pass 2/Pass 1' 全关，封面/hero/主图也已因 `subjectClarity` 改善。

---

## 5.1 M1 · ingest 人像信号（`portrait_analyze.py`）

### 5.1.1 W1 范围（R2 · 写死）

**纳入 W1**：`eyesOpenScore`、`faceSharpness`、`eyeFocusRaw`、`confidence`。

**推迟 W2**：`frontalFaceScore`、`poseScore`、`faceQualityScore`（FIQA）。

### 5.1.2 模块职责

- 输入：`PIL.Image`、Haar `faces[]`
- 对每张脸：bbox **扩边 20%** 后送 MediaPipe Face Landmarker（D3）
- 输出：`PortraitAnalyzeResult` → `quality.portrait`
- `faceCount == 0` 或不适用的场景 → 不调用（见 §5.1.5）

### 5.1.3 W1 信号定义

| 信号 | ingest 字段 | 算法 |
|------|-------------|------|
| 睁眼 | `eyesOpenScore` | EAR → 单图 sigmoid 映射 [0,1]；双眼取 min；**高=睁眼** |
| 人脸清晰 | `faceSharpness` | 主脸 ROI 拉普拉斯方差（原始值） |
| 眼部清晰 | `eyeFocusRaw` | 双眼 ROI 拉普拉斯方差（原始值） |
| 置信 | `confidence` | landmarks 完整度 × 脸尺寸因子 |

**分数语义对照表**（防实现反转）：

| 字段 | 1.0 含义 | 0.0 含义 | Pass 1' 触发（W2） |
|------|----------|----------|-------------------|
| `eyesOpenScore` | 睁眼 | 闭眼 | **低于** 阈值 T → 风险 |

EAR 阈值 **不得写死**于代码；默认配置 `weak: 0.35, standard: 0.55, strong: 0.70` 指 **eyesOpenScore** 而非原始 EAR。上线前用 `fixtures/portrait/eyes/` **校准**（≥200 张或开源集混合）。

### 5.1.4 检测器抽象与 landmarks（R3 + D6）

**后端抽象**：`FaceLandmarkBackend`（协议），实现按可用性探测：

| 优先级 | 后端 | 依赖 | 适用 |
|--------|------|------|------|
| 1 | `MediaPipeBackend` | `mediapipe` | Py 3.11/3.12 有 wheel |
| 2 | `OnnxBackend` | `onnxruntime` + 106 点模型 | Py 3.13/3.14 等无 mp wheel 时的回退 |
| 3 | `NullBackend` | 无 | 都不可用 → `confidence: 0`，全程 fail-open |

> CI 的 `vision+mediapipe` job 锁 **Python 3.11**；`onnxruntime` job 验证回退路径；`vision-only`（无两者）验证 NullBackend。

**对齐流程**：

```text
Haar 检出 face bbox
  → 扩边 bbox_pad_ratio（默认 0.20，clamp 至图像界）
  → backend.landmarks(crop)
  → 成功：算 EAR/faceSharpness/eyeFocusRaw
  → 失败：confidence=0，eyesOpenScore=null
```

### 5.1.4b ingest 去重 tiebreak 的轻量 EAR（D5 · 修正 F1）

ingest 的 burst/phash「保留/丢弃」决策发生在**全套 analyze 之前**，且会作用于**将被丢弃的帧**。为控成本：

- tiebreak 仅算 **轻量 EAR**：在 Haar bbox 内用 backend 的「快速眼部模式」（或仅眼区关键点），**不**算 faceSharpness/eyeFocus。
- `tiebreak_score = sharp_norm + λ · eyesOpenLite`，`λ = portrait.ingest_tiebreak_eyes_weight`（默认 0.15，保守）。
- backend 不可用 → `λ=0`，**退回纯 sharp**（与现网逐位一致，保 D7）。
- 被保留下来的帧，之后再跑**完整** `portrait_analyze`。

> 该步把「连拍里清晰但闭眼」误留的概率降低，是 G-PC-01 的真正杠杆。

### 5.1.5 不适用场景（R3）

以下情况 **只写 `confidence: 0`**，不参与 portrait 评分与 Pass 1'：

- 墨镜/遮挡导致眼部 landmarks 不可用
- 人脸短边 < 48px（与 `face_min_size_px` 对齐）
- 强逆光剪影、侧脸过大（landmarks 完整度 < 0.6）
- 背影无人脸（`faceCount == 0`）

### 5.1.6 多人脸聚合

| 用途 | 策略 |
|------|------|
| 主脸 | 最大 bbox 面积 |
| 睁眼（评分） | `primary × 0.7 + mean(others) × 0.3` |
| 睁眼（硬剔 W3） | 默认 `primary` 闭眼即触发 |
| 模糊（W2） | `require_all_faces_blurred: false` → 任一脸清晰则不标糊 |

### 5.1.7 落盘策略（S4）

| 字段 | 默认落盘 |
|------|----------|
| `portrait.eyesOpenScore`、`faceSharpness`、`confidence` | **是** |
| `portrait.perFace[]` | **否**（仅 `ingest.debug_portrait_per_face=true`） |
| `portrait.signals`（EAR、yaw 等） | **否**（仅 debug） |

### 5.1.8 扁平字段兼容

| 扁平字段 | 来源 |
|----------|------|
| `quality.portraitEyesOpenScore` | `portrait.eyesOpenScore` |
| `quality.portraitEyeFocusScore` | cull 批内归一后的消费分（W2）；W1 可空 |
| `quality.portraitFaceQualityScore` | W3 FIQA |

**权威结构**：`quality.portrait`；长期仅保留嵌套（扁平为过渡）。

---

## 5.2 M2 · 人像质量评分与 Pass 2

### 5.2.1 `_portrait_quality_score` 归一化公式（R6）

```python
# 1) 特征项，每项 ∈ [0,1]；权重 w_i 之和 = 1.0（W1 不含 frontal/pose）
features = {
  "face_ratio": face_ratio,
  "eyes_open": coalesce(p.eyesOpenScore, 0.5),
  "face_sharp": norm_face_sharp(p.faceSharpness, batch_stats),
  "eye_focus": norm_eye_focus(p.eyeFocusRaw, batch_stats),
  "exposure": exposure_center,
}
base = sum(w_i * features[k] for k, w_i in active_weights.items())
base = clamp01(base)

# 2) 软惩罚（W2+；有上限）
penalty = min(penalty_cap, p_eyes + p_blur)   # 默认 penalty_cap = 0.25
return clamp01(base - penalty)
```

**W1 默认权重**（和=1.0）：

| 键 | W1 | W2 可加 |
|----|-----|---------|
| `face_ratio` | 0.40 | |
| `eyes_open` | 0.25 | |
| `face_sharp` | 0.20 | |
| `eye_focus` | 0.10 | |
| `exposure` | 0.05 | |
| `frontal` | — | 0.06（从 face_ratio 等比例让出） |

缺省回退：`portrait` 缺失 → legacy 公式（faceRatio×0.55 + sharp×0.30 + exposure×0.15）。

### 5.2.2 Shadow mode（D2 · M1.5）

```yaml
cull:
  portrait:
    shadow_mode: true          # M1.5 默认 true
    shadow_mode_days: 7
```

| shadow_mode=true | 行为 |
|------------------|------|
| Pass 2 | 计算「若启用会保留谁」，写入 `quality.shadowPickWin`、`shadowPickLose` |
| `layoutEligible` | **不变** |
| Pass 3 配额 | **不变** |

telemetry：`cullSummary.portraitShadowWouldChangeCount`（would exclude 数量）。

### 5.2.3 Pass 2 组内择优

- 组内存在 `cullBranch==portrait` 时，PK 键：`portrait.group_pick_score`（默认 `cull`）
- **featured（D1）**：含 featured 的组仍按 P9——featured 全部保留，**仅 material 互 PK**
- 受益组：`burstGroupId`、`dedupeGroupId`

### 5.2.4 `cullBranch` 写入时机

在 `run_photo_cull` 评分循环之前，对全图写入 `quality.cullBranch`；Pass 2 **只读**，不重复计算。

---

## 5.3 M3 · Pass 1' 人像缺陷（PC-W2）

### 5.3.1 规则表

条件：`branch==portrait` 且 `confidence >= min_confidence`（0.5）。

| ID | 条件 | excludeReason | M3 默认 |
|----|------|---------------|---------|
| R-PC-01 | `eyesOpenScore < T(sensitivity)` | `eyes_closed` | `penalize`（软曲线，非阶跃） |
| R-PC-02 | 批内 `norm_eye_focus` 低且 `faceSharpness` 低 | `face_blur` | **`off`**（仅 Pass 2 排序；顾问建议默认不全局 penalize） |
| R-PC-03 | 曝光不可修复 | `exposure_extreme` | `off`（M4 灰度） |

**penalize**：不改 `layoutEligible`；扣减分 ≤ `penalty_cap`；写 `cullExplain`。

**hard_exclude**：M4 前 **禁止为默认**；featured 豁免（`featured_exempt`）。

### 5.3.2 闭眼软惩罚曲线

```text
penalty_eyes = penalty_max * sigmoid((T - eyesOpenScore) / temperature)
```

避免眯眼笑被阶跃阈值误伤；`temperature` 默认 0.08。

### 5.3.3 豁免（W2）

| 豁免 | 条件 |
|------|------|
| featured | 跳过 hard_exclude |
| 大合影 | `faceCount >= 6` → R-PC-01 跳过或惩罚减半 |
| 大笑 | `mouthOpenScore > T` → 跳过 R-PC-01（W2 可选） |

---

## 5.4 M3 · 场景 preset（S2 · 3 个）

| preset | 触发 | 权重倾向 |
|--------|------|----------|
| `general` | 默认 | 均衡 |
| `solo_portrait` | `faceRatio >= 0.25` | ↑face_sharp、↑eyes_open |
| `group_portrait` | `faceCount >= 3` | ↑eyes_open；主脸权重降低 |

**children / wedding**：不单独 preset；通过 `tags` 含 `child` 时提高 `face_blur` 组内排序权重（仍在 `group` 或 `general` 下）。

---

## 5.5 相似组增强（W2/W3）

1. `burstGroupId`：**多成员**组内人像 PK（M2，`portrait.burst_pk`）。
2. 可选：同 `dedupeGroupId` 内 `face_crop_embedding` 余弦 > 0.92 再子组 PK。

---

## 5.6 下游消费者集成（主收益 · D5-B）

所有图位**不改主选型框架**，仅消费 §6.3 的 `subjectClarity`。集成点与验收对应：

| 图位 | 模块 / 函数（代码事实） | 人像因子如何起作用 | 目标 |
|------|------------------------|--------------------|------|
| **封面 / 分端封面** | `cover_score` · `cover_score_v2` · `effective_cover_score`（已有 `_face_bbox_feature` 消费 `salientBox`+sharp） | `aesthetic_multiplier` 经 `purpose_overall("cover")` 反映睁眼/脸清晰；闭眼脸降权 | G-PC-D1 |
| **章英雄 hero** | `hero_score` · `effective_hero_score` · `hero_score_v2`（用 `PA overall×composition×subjectClarity`） | `subjectClarity`↑ 直接抬升睁眼清晰人像 | G-PC-D2 |
| **高光池 / 决定性瞬间** | `build_moment_pool` · `peak_moment_score`（内部 `purpose_overall(asset,"moment")`） | `moment` 用途分含 `subjectClarity`；闭眼名场面被压低 | G-PC-D3 |
| **拼图主图** | `pick_main_for_pattern`（landscape 按清晰度选）· `mosaic/scorer.score_candidate`（有 `_main_quality_penalty`、人脸裁切惩罚） | 主图候选用 `QualityFeatures.aesthetic_pct`（经 `aesthetic_overall`）；人像主图反映睁眼清晰 | G-PC-D4 |
| **单张强调 solo** | `solo_score`（`purpose_overall(asset,"solo")`） | 同上 | G-PC-D4 |
| **封底** | `resolve_closing_asset_id`（偏低饱和/黄昏/未用） | 仅「闭眼避坑」：若候选为人像且闭眼，施加下限约束，不主动加权 | G-PC-D5 |

**统一性保证**：闭眼/糊脸的**惩罚曲线**在「闸口 penalize」（§5.3.2）与「下游 subjectClarity 扣减」（§6.3）**复用同一函数**，避免两套口径打架。

**`QualityFeatures` 路径**：`build_quality_pool` 的 `aesthetic_pct` 源自 `aesthetic_overall`；只要 §6.3 让 `subjectClarity` 进入 overall，拼图主图/ hero 的 trip 内百分位即自动反映人像质量（无需改 `quality_features.py`）。

---

## 6. 数据模型

### 6.1 `quality.portrait`（权威 · W1 即入 schema）

```json
{
  "quality": {
    "faceCount": 2,
    "faceRatio": 0.18,
    "portraitEyesOpenScore": 0.92,
    "portrait": {
      "version": "pc-v1",
      "eyesOpenScore": 0.92,
      "faceSharpness": 1240.5,
      "eyeFocusRaw": 318.2,
      "confidence": 0.88,
      "preset": null
    }
  }
}
```

**Schema（R4）**：M1 同步更新 `schemas/trip.schema.json` 的 `quality.properties.portrait`；`excludeReason` 枚举 M3 再扩。

### 6.2 `cullSummary` / shadow 扩展

| 字段 | 说明 |
|------|------|
| `portraitAnalyzeRate` | 成功分析比例 |
| `portraitAnalyzeSkipRate` | 跳过（含不适用场景） |
| `portraitShadowWouldChangeCount` | shadow 下 would exclude 数 |
| `excludedByReason.eyes_closed` | M3+ |
| `portraitPresetCounts` | M3+ |

### 6.3 消费者 B 入口 · `aesthetic.dims.subjectClarity` 注入（主收益）

下游所有图位都经 `purpose_overall(asset, purpose)` 读取 `quality.aesthetic.dims`。其中 **`subjectClarity`** 是人像因子的天然落点。

**现状**（[DESIGN-PHOTO-AESTHETIC-EVALUATION.md](./DESIGN-PHOTO-AESTHETIC-EVALUATION.md) §3.2e）：

```text
subjectClarity = 0.7·normSharp + 0.3·subjectContrast
```

**本 PRD 改动**（仅当该 asset 有 `portrait.confidence >= min_confidence` 时生效，否则原样——保 D7）：

```text
subjectClarity_portrait =
    w_sc_facesharp · norm_face_sharp(faceSharpness, batch)   # 人脸区域清晰，而非整图
  + w_sc_eyes      · eyesOpenScore
  + w_sc_frontal   · frontalFaceScore          # W2+，缺则均摊
  + w_sc_base      · normSharp                 # 保留整图项兜底
默认权重 = {facesharp .40, eyes .30, frontal .15, base .15}（和=1）

# 闭眼软扣减（与 cull 同曲线，避免下游与闸口口径不一致）
subjectClarity_portrait -= min(sc_penalty_cap, penalty_eyes)   # cap 默认 0.2
```

并写入可解释中间量：

```jsonc
"aesthetic": {
  "dims": { "subjectClarity": 0.78, ... },
  "signals": {
    "portraitEyesOpen": 0.93,
    "portraitFaceSharpPct": 0.81,
    "portraitApplied": true        // 是否被人像因子改写（审计/回退）
  }
}
```

> **传播即免费**：因为 cover/hero/solo/moment 已各自用 purpose 权重重算 overall，`subjectClarity` 一旦反映人像质量，**五个下游图位同时受益，无需各自改代码**。

### 6.4 purpose 权重（按图位差异化）

`resolve_aesthetic_weights(cfg, purpose)` 已支持每用途独立权重。本 PRD 建议（仅调 `subjectClarity` 相对权重，不动主框架）：

| purpose | `subjectClarity` 取向 | 说明 |
|---------|----------------------|------|
| `cover` | ↑ | 封面人像要睁眼清晰正脸 |
| `hero` | ↑ | 章入口同理 |
| `solo` / `moment` | 中-↑ | 决定性瞬间重叙事，但闭眼仍扣分 |
| `mosaic main` | ↑ | 主图位是视觉锚点 |
| `closing`（封底） | 低 | 封底偏风景；人像因子仅做「闭眼避坑」下限约束 |

> 实际权重值为 M3 校准产物；W1/M2 先用「不改 purpose 权重、仅让 subjectClarity 反映人像」最小集。

---

## 7. 配置规格

```yaml
ingest:
  portrait_analyze: true
  portrait_analyze_max_edge: 1280
  portrait_backend: auto            # auto | mediapipe | onnx | off（D6）
  debug_portrait_per_face: false

cull:
  portrait_quality_enabled: true
  # F4/D7：仅在 asset 有 portrait 信号时，分支权重才偏移到该值；无信号 → 用 P9 的 0.15
  score_branch_weight_portrait: 0.20

  portrait:
    enabled: true
    gate_changes_on_signal: true     # D7：无 portrait 信号资产逐位等于 P9 基线
    shadow_mode: true                # M1.5
    shadow_mode_trips: 5             # S10：按 trip 数而非天数
    min_confidence: 0.5
    bbox_pad_ratio: 0.20
    ingest_tiebreak_eyes_weight: 0.15  # D5：burst/phash 去重 tiebreak 的 λ
    burst_pk: true                   # D5：多成员 burst 组启用人像 PK
    group_pick_score: cull
    penalty_cap: 0.25

    score_weights:                   # 闸口人像分（和=1）
      face_ratio: 0.40
      eyes_open: 0.25
      face_sharp: 0.20
      eye_focus: 0.10
      exposure: 0.05

    # 消费者 B：注入 aesthetic.subjectClarity（§6.3）
    subject_clarity_weights:
      face_sharp: 0.40
      eyes: 0.30
      frontal: 0.15
      base: 0.15
    subject_clarity_penalty_cap: 0.20

    eyes_closed:
      mode: off                      # M3 改为 penalize
      sensitivity: weak
      thresholds: { weak: 0.35, standard: 0.55, strong: 0.70 }
      temperature: 0.08

    face_blur:
      mode: off

    multi_face:
      eyes_blend_primary: 0.7
      require_all_faces_blurred: false
```

---

## 8. 降级策略

| 级别 | 场景 | 行为 |
|------|------|------|
| L0 | mediapipe 未安装 | 跳过 analyze |
| L1 | landmarks 失败 / 不适用 | `confidence: 0` |
| L2 | portrait 分支不可用 | 回退 legacy 公式 |
| L3 | cull 异常 | fail-open |

---

## 9. 时延预算

假设（S7 修正）：**200 张留存 + 约 60 张连拍/近重复被丢弃帧**；留存中约 40% 含可分析人脸。

| 阶段 | 成本来源 | P50 | P95 |
|------|----------|-----|-----|
| ingest tiebreak | 被丢弃帧的**轻量 EAR**（仅眼区） | +5~12s | <20s |
| 完整 analyze | 留存人脸帧 landmarks | +12~30s | <50s |
| 下游 subjectClarity | 纯计算，复用已存 dims | <1s | <2s |
| **合计（CPU）** | | **+18~42s** | **<70s** |

超限降级：关 tiebreak（λ=0）→ 缩边 → 提高 `faceRatio` 门槛 → onnx 换更小模型 → skip。

---

## 10. 实现位置

| 模块 | 变更 |
|------|------|
| `travelogue/media/portrait_analyze.py` | **新建** · 后端抽象 + EAR/faceSharpness |
| `travelogue/media/portrait_backends.py` | **新建** · `MediaPipeBackend` / `OnnxBackend` / `NullBackend`（D6） |
| `travelogue/media/subject_detect.py` | **必需**（F3）：`analyze_subject` 额外返回 `faces[]` |
| `travelogue/media/ingest.py` | 调用 analyze；burst/phash tiebreak 注入；`contentSig` 缓存 |
| `travelogue/curation/aesthetic_score.py` | **§6.3 注入** `subjectClarity` 人像因子 + `signals.portrait*`（消费者 B 主收益） |
| `travelogue/curation/photo_cull.py` | `_pass1_portrait_defects`、人像评分、多成员 burst PK、shadow |
| `travelogue/config/cull.py` · `config/ingest.py` | `PortraitCullConfig`、backend、tiebreak、gating |
| `schemas/trip.schema.json` | **M1** 增加 `quality.portrait` + `aesthetic.signals.portrait*` |
| `docs/acceptance-records/portrait-cull-baseline.json` | **M1 阻塞**（AC-PC-00） |
| `fixtures/portrait/` | **M1 阻塞** |
| CI | **mediapipe(Py3.11)** / **onnx** / **vision-only** 三 job（D6/S5） |

> **不改**：`cover_scoring*.py`、`curate_scoring.py`、`moment_scoring.py`、`mosaic/scorer.py`、`solo_scoring.py`、`quality_features.py` —— 全部经 `aesthetic_score` 间接受益（§5.6）。这是 D5-B「下游零改动」的核心约束。

---

## 11. 验收标准

**下游主收益（消费者 B · dogfood 3 人像 trip）**

| ID | 条件 |
|----|------|
| **AC-PC-D1** | `coverAssetId` / `coverByLayout` 选中人像的闭眼/糊脸率较基线下降；无回归到更差封面 |
| **AC-PC-D2** | 章 hero 选中人像 `eyesOpenScore` 中位数 ↑；糊脸 hero 数 ↓ |
| **AC-PC-D3** | `momentAssetId` 不为闭眼人像；`momentPoolIds` 缺陷率 ↓ |
| **AC-PC-D4** | 拼图主图 / `solo` 选中人像缺陷率 ↓ |
| **AC-PC-D5** | `resolve_closing_asset_id` 若选人像则非闭眼 |
| **AC-PC-D6** | **下游模块零改动**：`cover/hero/moment/mosaic/solo` 源码 diff 为空，仅 `aesthetic_score.py` 改动 |

**闸口与基建（消费者 A）**

| ID | 条件 |
|----|------|
| **AC-PC-00** | 冻结 `portrait-cull-baseline.json`（P9 输出 + commit/config hash + trip 列表） |
| **AC-PC-01** | 可分析人脸中 `confidence > 0` ≥ **80%**（排除墨镜等不适用后） |
| **AC-PC-02** | **任一后端缺失**：ingest 100% 成功；**无 portrait 信号资产** cull 序与 AC-PC-00 逐位一致（D7） |
| **AC-PC-03** | 睁眼/闭眼集：**AUC ≥ 0.85** 或 top/bottom 20% `eyesOpenScore` 分离度 ≥ 0.25 |
| **AC-PC-04** | 多成员 burst 组命中率优于基线（shadow 关闭后） |
| **AC-PC-05** | ingest tiebreak：构造「清晰闭眼 vs 略糊睁眼」连拍对，启用后保留睁眼比例显著上升 |
| **AC-PC-06** | 黄金集误杀率 ≤ 基线；`cullExplain` 含 `eyes_open`、`face_sharp` |
| **AC-PC-07** | 200 张 × 40% 人脸占比 + 被丢弃连拍帧 tiebreak 开销，满足 §9 |
| **AC-PC-08** | schema 校验通过（M1：`portrait` + `aesthetic.signals.portrait*`；M3：`excludeReason`） |
| **AC-PC-09** | featured 不参与 material PK；hard_exclude 不作用于 featured |
| **AC-PC-10** | shadow：`portraitShadowWouldChangeCount` 有打点；`layoutEligible` 与基线一致 |
| **AC-PC-11** | 三后端矩阵（mediapipe / onnx / null）CI 全绿 |

### 11.1 Fixtures（M1 阻塞 · R5）

| 路径 | 内容 |
|------|------|
| `fixtures/portrait/eyes/` | 睁眼/闭眼/半闭眼/眯眼笑 各 ≥20 |
| `fixtures/portrait/burst/` | 5–10 组连拍 + 人工标最佳 |
| `fixtures/portrait/golden/` | 扩展 P12 黄金集 |

---

## 12. 与 Phase 12 变更对照（R8）

| Phase 12 条目 | 本 PRD |
|---------------|--------|
| §5.1 人像细粒度信号 | **全文权威** |
| §5.2 11 类 L1 | 仍归 P12 |
| §5.3 category_coherence | 仍归 P12 |
| AC-P12-01/02 人像命中率 | 由 AC-PC-04/D1~D4 承接 |
| AC-P12-06 风光命中率 | 仍归 P12；D7 门控保证风光权重不变 |
| 下游图位择优（封面/封底/高光池/决定性瞬间/拼图主图） | **本 PRD §5.6 / §6.3 新增**（P12 未覆盖） |

---

## 13. 风险与缓解

| 风险 | 缓解 |
|------|------|
| EAR 眯眼/大笑误判 | 软惩罚曲线；weak 敏感度；大笑豁免 |
| Haar 漏检 | landscape 回退；不误杀 |
| Shadow 掩盖问题 | 累计 `shadow_mode_trips` 后必须关或书面延期（S10） |
| JSON 膨胀 | perFace/signals 默认不落盘 |
| **下游过度偏向人脸** | `subjectClarity` 仅在有 portrait 信号时改写；风景/食物分数不变（D7）；purpose 权重灰度 |
| **mediapipe 无 wheel（Py3.13/3.14）** | onnx 后端回退；NullBackend 全程 fail-open（D6） |
| **闸口与下游口径不一致** | 闭眼惩罚曲线两侧复用同一函数（§5.6） |
| **ingest tiebreak 拖慢导入** | λ 仅触发轻量 EAR；可 λ=0 关闭（§9 降级） |

---

## 14. 明确排除项

Studio 挑图 UI、商业 10 场景 UI、方糖级大模型、L2 HDBSCAN 全量聚类、人像修图、W1 的 pose/正脸/hard_exclude。

---

## 15. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3.0 | 2026-06-16 | **架构评审合入 F1–F4 + 下游重定向**：①F1 注入点修正（ingest tiebreak + 多成员 burst PK，主收益走 PA `subjectClarity`）；②D6 检测器后端抽象（mp/onnx/null）；③F3 `analyze_subject` 返回 faces；④D7 变更门控在信号存在；⑤新增 §4.0 一份信号两类消费者、§5.6 下游集成表、§6.3 subjectClarity 注入、§6.4 purpose 权重、G-PC-D1~D5、AC-PC-D1~D6/11；⑥§9 计入丢弃帧 tiebreak 开销 |
| v0.2.0 | 2026-06-16 | 评审合入：W1 收窄、信号分层、Haar 扩边、shadow mode、schema M1、baseline/fixtures、归一化公式、featured Pass2、3 preset、AC 加强、P12 对照表 |
| v0.1.0 | 2026-06-16 | 初稿 |
