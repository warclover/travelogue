# Travelogue · Phase 12 产品需求文档（PRD · 静默自治选片增强）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.12.2-PHASE12 |
| **状态** | In Progress |
| **Phase 12 代号** | 「静默自治选片增强」— 零打扰后台评分与编排质量提升 |
| **前置条件** | [PRD-PHASE9.md](./PRD-PHASE9.md) 已上线（Quality Gate）；[PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md) 已上线（mundane grid） |
| **关联文档** | [PRD-PHASE8-photo-semantic-clustering.md](./PRD-PHASE8-photo-semantic-clustering.md)、`photo_cull.py`、`subject_tagging.py`、`layout_scoring.py` |
| **更新日期** | 2026-06-03 |

> **定位**
>
> - Phase 12 不新增任何用户决策交互，继续坚持「选文件夹后全自动」。
> - 仅做后台选片/分组/排序能力升级，不做修片（不改像素）。
> - 目标是在个人开发者可承载成本下，提升自动结果质量与稳定性。

---

## 1. 设计原则（硬约束）

| ID | 原则 | 约束说明 |
|----|------|----------|
| **P12-PR-01** | 零打扰 | 不新增用户确认、复核、挑选 UI |
| **P12-PR-02** | 全后台自治 | 导入后后台自动完成评分、筛选、聚类、排版 |
| **P12-PR-03** | 不做修片 | 不做曝光/颜色/降噪/锐化/重绘等像素改动 |
| **P12-PR-04** | 保守可逆 | 不确定样本默认保留；异常 fail-open |
| **P12-PR-05** | 个人可落地 | 优先低复杂度高收益改动，避免大模型重训 |

---

## 2. 背景与问题

Phase 9/10 已覆盖基础去重、质量闸口与 mundane grid，但仍存在以下结构性缺口：

1. 人像质量仍偏粗粒度（缺少眼睛睁开/眼睛清晰等弱监督信号）。
2. 语义层仍以 8 类粗标签为主，未完成 Phase 8 的 11 类 L1 落地。
3. 排版评分缺少 `category_coherence` 维度，主题连续性奖励不足。
4. 部分规划项（如标签 UI）与「零打扰」产品原则冲突。

---

## 3. 目标与非目标

### 3.1 目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-P12-01** | 在零交互前提下降低误杀 | 黄金集误杀率下降（相对 P9 基线） |
| **G-P12-02** | 提升人像场景自动选片稳定性 | 人像数据集 Top-K 命中率提升 |
| **G-P12-03** | 提升语义连续性与编排一致性 | 新增 coherence 指标并进入评分 |
| **G-P12-04** | 保持主流程稳定与可用 | fail-open 保持生效，导入成功率不下降 |

### 3.2 非目标

- 不新增 Studio 标签编辑/人工复核 UI。
- 不做 L2 子簇全量上线（本 Phase 仅规划，不纳入交付范围）。
- 不做任何图片像素级增强、修图或生成式改图。
- 不做重型个性化模型训练平台。

---

## 4. 能力项复核与纳入决策

> 本表用于回答「未优化项是否纳入下一步」。

| 能力项 | 当前状态 | Phase 12 决策 | 决策理由 |
|--------|----------|---------------|----------|
| 人像质量细粒度（眼睛睁开/眼睛清晰） | 部分优化（仅有人脸信号） | **纳入（P12-W1）** | 纯后台增强，收益高，改动可控 |
| 11 类 L1 语义映射 | 未完整落地 | **纳入（P12-W1/W2）** | 为 coherence 与后续排序提供基础输入 |
| L2 子簇（类内 HDBSCAN） | 未落地 | **暂缓（P12 之外）** | 复杂度高，个人开发者周期风险大 |
| Studio 标签 UI | 未落地 | **不纳入** | 与零打扰原则冲突 |
| `category_coherence` 评分 | 未落地 | **纳入（P12-W2）** | 纯后端评分，直接提升编排质量 |

---

## 5. 功能规格（Phase 12 交付范围）

## 5.0 分支化评分总流程（权威）

```text
照片库
  -> 场景分流（人像/风光）
  -> 分支评分（人像质量分 / 风光美学分）
  -> 融合总分（含现有 sharpness、mediaClass 权重）
  -> 组内择优（burstGroupId / dedupeGroupId）
  -> Top-K / 阈值筛选
  -> layoutEligible 池
```

分流规则（MVP）：

- 人像分支：有人脸且 `face_ratio >= 阈值`（默认 0.15）
- 风光分支：无人脸或 `face_ratio < 阈值`，且由 `subjectClass/aspectKind` 辅助判定
- 灰区：保守落到风光分支并降低剔除强度（避免误杀）

## 5.1 P12-A · 人像细粒度质量信号（后台）

在不引入重模型的前提下，新增轻量信号并进入 cull 排序：

- `portraitEyesOpenScore`（可空）
- `portraitEyeFocusScore`（可空）
- `portraitFaceQualityScore`（可空）

策略：

1. 仅对有人脸资产生效；无人脸资产走现有评分逻辑。
2. 新信号默认低权重（防止改变过大）。
3. 信号不可用时自动降级，不影响导入完成。

实现位置（建议）：

- `travelogue/curation/photo_cull.py`
- `travelogue/config.py`（新增权重与开关）
- `travelogue/media/ingest.py`（透传信号）

补充说明（来源于调研结论）：

- 本 Phase 不直接引入重型 FIQA 作为主依赖。
- CR-FIQA / DN-PIQA 保留为 W3 可选实验项，不纳入 W1/W2 交付门槛。

## 5.2 P12-B · 11 类 L1 语义映射（后台）

目标：将现有 8 类粗标签映射/扩展为 11 类 L1 可解释类别（不做 L2）。

策略：

1. 复用现有 `subjectClass` + tags + 规则映射输出 `semanticTag.category`。
2. 不要求新 UI 编辑；仅作为内部评分与编排输入。
3. 对低置信度样本保守回落到 `general`。

实现位置（建议）：

- `travelogue/curation/subject_tagging.py`
- `travelogue/vision/clip_encoder.py`（仅必要时补充 prompt/映射）

## 5.3 P12-C · `category_coherence` 评分（后台）

在 layout scoring 中引入主题一致性分：

- 同屏/相邻屏同类语义给予正向奖励；
- 过度切换给予轻惩罚；
- 权重默认低于核心清晰度和结构项。

实现位置（建议）：

- `travelogue/curation/layout_scoring.py`
- `travelogue/config.py`（权重配置）

## 5.4 统一决策伪代码（实现口径）

> 目标：避免实现阶段出现「各模块各算各的」分叉。

```python
def select_assets(assets):
    scored = []
    for a in assets:
        # 0) 硬约束与硬剔除（不含 featured）
        if is_featured(a):
            hard_excluded = False
        else:
            hard_excluded = media_hard_exclude(a) or blur_hard_exclude(a)
        if hard_excluded:
            mark_excluded(a, reason=resolve_reason(a))
            continue

        # 1) 分流（portrait / landscape / gray）
        branch = route_branch(a)  # portrait | landscape | gray

        # 2) 分支打分（可缺省，缺省回退）
        portrait_s = portrait_score(a) if branch in ("portrait", "gray") else None
        landscape_s = landscape_score(a) if branch in ("landscape", "gray") else None

        # 3) 分支仲裁（gray 保守）
        if branch == "portrait":
            branch_s = fallback_to_rules(a, portrait_s)
        elif branch == "landscape":
            branch_s = fallback_to_rules(a, landscape_s)
        else:
            # gray: 保守取 max，减少误杀
            p = fallback_to_rules(a, portrait_s)
            l = fallback_to_rules(a, landscape_s)
            branch_s = max(p, l)

        # 4) 融合总分（保留现有 cull 主体权重）
        final_s = fuse_score(
            rules_score(a),          # sharpness/mediaClass 等现有分
            branch_s,                # 分支分
            coherence_hint(a),       # 可选：轻权重提示
        )
        scored.append((a, final_s))

    # 5) 组内择优（先 burst 再 dedupe）
    scored = keep_best_per_group(scored, key="burstGroupId")
    scored = keep_best_per_group(scored, key="dedupeGroupId")

    # 6) 全局筛选：先阈值，后 Top-K，最后地板兜底
    pool = [x for x in scored if x.score >= SCORE_THRESHOLD]
    pool = top_k(pool, K_RATIO_OR_COUNT)
    pool = enforce_keep_floor(pool, floor_ratio=KEEP_RATIO_FLOOR, min_keep=MIN_KEEP)
    return mark_layout_eligible(pool)
```

固定 tie-break 链（deterministic）：

1. `final_score`（高优先）
2. `quality.sharpness`
3. `takenAt`（更早优先，稳定复现）
4. `assetId`（字典序）

---

## 6. 模型选型与引入策略

## 6.1 主线模型（纳入交付）

| 能力域 | 主线方案 | 纳入波次 | 说明 |
|--------|----------|----------|------|
| 风光美学/质量 | `pyiqa: topiq_nr`（主）+ `musiq`（备） | W1 | 复用现有 `photo_cull_ml.py` 管线，优先低接入成本 |
| 人像质量 | 轻量信号（face ratio + face sharpness + 曝光） | W1 | 无重依赖，CPU 可运行，稳定优先 |
| 分支融合 | 现有 cull 规则 + 分支权重融合 | W1/W2 | 保持可解释与可降级 |

## 6.2 候选模型（试点，不作为主线依赖）

| 方案 | 决策 | 原因 |
|------|------|------|
| CR-FIQA / DSL-FIQA / DN-PIQA | 可选试点（W3） | 潜在收益高，但算力和集成复杂度更高 |
| AestheticSigLIP | 离线对照 | 先与 `topiq_nr` 做离线对比，不直接替换主线 |
| Facet 整体引入 | 不纳入主线 | 依赖面过大，降低当前管线可控性；可用于离线 benchmark |

---

## 7. 数据模型与配置

## 7.1 资产字段（可选新增）

```json
{
  "quality": {
    "portraitEyesOpenScore": 0.0,
    "portraitEyeFocusScore": 0.0,
    "portraitFaceQualityScore": 0.0
  },
  "semanticTag": {
    "category": "food"
  }
}
```

> 字段均允许缺失；缺失即回退现有逻辑。

## 7.2 配置建议

```yaml
cull:
  portrait_quality_enabled: true
  score:
    portrait:
      eyes_open_weight: 0.08
      eye_focus_weight: 0.10
      face_quality_weight: 0.07

layout:
  scoring:
    weights:
      category_coherence: 0.06
```

> 最终键名以实现为准；默认保持保守权重。

## 7.3 参数默认表（MVP）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `face_ratio_portrait_min` | `0.15` | 人像分支阈值 |
| `face_ratio_gray_low` | `0.10` | 灰区下界 |
| `face_ratio_gray_high` | `0.20` | 灰区上界 |
| `score_threshold` | `0.00` | 全局阈值（默认关闭，按地板语义兜底） |
| `score_topk_ratio` | `1.00` | Top-K 比例（默认关闭，按地板语义兜底） |
| `keep_ratio_floor` | `0.90` | 继承 P9 地板语义 |
| `min_keep` | `15` | 继承 P9 语义 |
| `score_branch_weight_portrait` | `0.15` | portrait 分支融合权重（其余由 rules 承担） |
| `score_branch_weight_landscape` | `0.15` | landscape 分支融合权重 |
| `layout.scoring.weights.category_coherence` | `0.00` | coherence 权重（默认关闭，灰度开启） |

---

## 8. 降级与时延策略（新增）

| 场景 | 策略 |
|------|------|
| 无 GPU / pyiqa 不可用 | 自动回退 rules（沿用 Phase 9 降级语义） |
| 人像信号不可用 | 仅使用现有 cull 信号，不阻断导入 |
| 模型输出低置信 | 回退 `general` 或灰区保留，不作为硬剔除依据 |
| 全局异常 | fail-open（保持主流程成功） |

降级分级（必须打点）：

- **L1（模型级）**：单模型不可用 -> 回退 rules 分
- **L2（分支级）**：portrait/landscape 分支异常 -> 回退全局 rules
- **L3（流程级）**：关键阶段异常 -> fail-open

落地 telemetry（当前实现口径）：

- `trip.curation.cullSummary.branchPortraitRatio`
- `trip.curation.cullSummary.branchLandscapeRatio`
- `trip.curation.cullSummary.branchGrayRatio`
- `trip.curation.cullSummary.mlFallbackRateL1`
- `trip.curation.cullSummary.branchFallbackRateL2`
- `trip.curation.cullSummary.branchFallbackByReasonL2`
- `trip.curation.cullSummary.failOpenRateL3`
- `trip.curation.cullSummary.cpuMs`

并同步到 `ingest_stats`：

- `cull_l1_ml_fallback_rate`
- `cull_l2_branch_fallback_rate`
- `cull_l3_fail_open_rate`
- `cull_l2_<reason>`（例如 `cull_l2_gray_zone`、`cull_l2_face_signal_missing`）

时延预算（MVP 目标）：

- CPU-only：200 张新增评分时延 `+20~45s`（P50），`<70s`（P95）
- GPU 可用：200 张新增评分时延 `+8~20s`（P50），`<35s`（P95）
- 若超过预算：优先降低模型调用比例，不降低稳定性

---

## 9. 流水线位置（权威）

```text
scan -> dedupe -> asset build
     -> photo_cull (含 portrait 轻量信号)
     -> low-res gate
     -> clustering / subject tagging (含 L1 category)
     -> layout scoring (含 category_coherence)
```

说明：

- 仍保持 Phase 9 的 fail-open 与全 trip re-cull 语义。
- 不新增用户可见中断节点。

---

## 10. 验收标准（建议）

| ID | 验收条件 |
|----|----------|
| **AC-P12-01** | 人像测试集 Top-K 命中率优于 P9 基线 |
| **AC-P12-02** | 误杀率不高于 P9 基线，且 fail-open 用例通过 |
| **AC-P12-03** | `semanticTag.category` 在样本集可稳定产出（含回退） |
| **AC-P12-04** | `category_coherence` 已进入评分并可在 explain 中观测 |
| **AC-P12-05** | 无新增用户交互步骤；导入主流程时延在可接受范围 |
| **AC-P12-06** | 风光测试集 Top-K 命中率优于 P9 基线 |
| **AC-P12-07** | `burstGroupId` / `dedupeGroupId` 组内仅保留最高分样本（规则一致） |
| **AC-P12-08** | 分支覆盖率与回退率 telemetry 可出报表（L1/L2/L3） |
| **AC-P12-09** | CPU-only 与 GPU 两档时延预算均满足 |

---

## 11. 风险与降级

| 风险 | 缓解策略 |
|------|----------|
| 人像信号噪声大导致误杀 | 信号低权重 + 双阈值保守策略 + 灰区保留 |
| 11 类映射不稳定 | 低置信回退 `general`，不做硬剔除依据 |
| coherence 误导排版 | 初期权重低，A/B 对比后逐步调高 |
| 个人开发者维护压力 | W1/W2 分波次，L2 子簇暂缓 |

---

## 12. 里程碑计划（个人开发者版）

| 波次 | 周期 | 内容 |
|------|------|------|
| **P12-W1** | 1 周 | 人像细粒度信号接入 cull（保守权重）+ 回归用例 |
| **P12-W2** | 1 周 | 11 类 L1 映射落地 + `category_coherence` 评分上线 |
| **P12-W3（可选）** | 0.5–1 周 | 参数校准与离线评测脚本固化 |

---

## 13. 明确排除项

- Studio 标签管理 UI
- L2 子簇 HDBSCAN 线上化
- 用户手工挑片/确认/恢复
- 任何修片能力（参数修图或生成式改图）

---

## 14. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.12.2 | 2026-06-03 | 对齐实现口径：参数命名、默认值、L1/L2/L3 telemetry 字段与验收汇总链路 |
| v0.12.1 | 2026-06-03 | 增补分支化评分流程、模型选型矩阵、Facet/CR-FIQA 引入决策、降级与时延策略 |
| v0.12.0 | 2026-06-03 | 初稿：基于 P9/P10 现状复核，固化「纳入/暂缓/不纳入」决策与零打扰原则 |

