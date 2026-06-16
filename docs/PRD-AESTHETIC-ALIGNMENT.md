# Travelogue · 人类审美对齐 PRD（Aesthetic Alignment）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.1.0-AESTHETIC-ALIGN |
| **状态** | Draft · 待评审 |
| **代号** | 「挑出人类认为的好照片」— 让自动选片对齐人类审美判断 |
| **前置条件** | PA 美学层（`aesthetic_score.py`、`quality.aesthetic`）已在；`photo_cull_ml.py` + pyiqa 管线可用；`pa_acceptance`（SRCC + 盲评）可用 |
| **关联文档** | [DESIGN-PHOTO-AESTHETIC-EVALUATION.md](./DESIGN-PHOTO-AESTHETIC-EVALUATION.md)、[PRD-PORTRAIT-CULL.md](./PRD-PORTRAIT-CULL.md)（人像质量 = 本 PRD 的 L1 输入）、[PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md)、[cover-selection-plan.md](./cover-selection-plan.md) |
| **实现模块（规划）** | `travelogue/curation/aesthetic_score.py`、`photo_cull_ml.py`、`pa_acceptance.py`、`travelogue/vision/aesthetic_mllm.py`（新建）、`config/aesthetic.py`、`scripts/aesthetic_blind_review.py` |
| **更新日期** | 2026-06-16 |

> **定位**
>
> - 核心目标：**自动挑出「人类认为的好照片」并重点展示**（封面/hero/高光池/决定性瞬间/拼图主图）。去除坏照片是必要的下限，但**不是**本 PRD 的主诉求。
> - 现状诊断：当前评分以**手写 CV 规则**为主（清晰/三分/曝光居中/鲜艳/人脸占比），优化的是「无瑕疵」，与人类审美只有弱相关 → 这是「挑不出好照片」的根因。
> - 本 PRD 用**学习型审美模型 + 人类标签校准 + 高价值图位 MLLM**，在不破坏「零打扰/fail-open/确定性」前提下，把选片**对齐到人类判断**，并用 SRCC/盲评**量化证明**。

---

## 0. 决策（已拍板）

| ID | 议题 | 裁定 | 来源 |
|----|------|------|------|
| **DA-1** | 人类标签 | **由作者本人盲评标注一批**（最可靠基准） | 用户 |
| **DA-2** | L3 内容/情绪模型 | **仅高价值图位（封面/hero/决定性瞬间）用 MLLM**；其余用本地模型 | 用户 |
| **DA-3** | 审美口径 | **先做通用大众审美**；个性化口味后置 | 用户 |
| **DA-4** | 交付物 | 先出本 PRD（含路线 A/B/C、评测口径、里程碑） | 用户 |

---

## 1. 设计原则（硬约束）

| ID | 原则 | 说明 |
|----|------|------|
| **AA-PR-01** | 可量化对齐 | 一切「对齐人类」必须以 **SRCC / 盲评胜率** 证明，禁止口号式上线 |
| **AA-PR-02** | 零打扰 | 不新增用户必经交互；标注是**离线**动作，不进主流程 |
| **AA-PR-03** | fail-open | 模型/网络不可用 → 回退现有规则分，导入不阻断 |
| **AA-PR-04** | 确定性可复现 | MLLM 非确定 → **结果按 `contentSig` 缓存 + 温度 0**；同输入同输出；tie-break 链不变 |
| **AA-PR-05** | 成本可控 | MLLM 仅对**候选短名单**（每 trip 几次调用），不全量 |
| **AA-PR-06** | 个人可维护 | 本地优先；外部依赖可关；不自建训练平台 |
| **AA-PR-07** | 不做修图 | 仅评分与选择，不改像素 |

---

## 2. 问题诊断（为什么现在挑不出好照片）

### 2.1 现状（代码事实）

- `AestheticConfig` 默认 `source="rules"`、`ml_calibrate=False` → **线上几乎纯规则**。
- 5 个维度 `composition/exposure/color/lighting/subjectClarity` 均为 **CV 代理**，衡量「技术不差」。
- 唯一学习信号 `topiq_nr` 默认关闭，且是 **IQA（技术画质）**，非「人类审美」。

### 2.2 「好照片」三层模型

| 层 | 内容 | 人类权重 | 现系统 |
|----|------|----------|--------|
| **L1 技术质量** | 清晰、曝光、不糊不闭眼 | 低（及格线） | ✅ 规则 + 人像 PRD |
| **L2 构图/光色美学** | 构图、光影层次、色调和谐 | 中 | ⚠️ 仅粗规则 |
| **L3 内容/情绪/瞬间** | 表情、决定性瞬间、故事、趣味 | **高（决定性）** | ❌ 几乎为零 |

> 差异根因：**系统判断力 90% 在 L1，人类偏好 80% 在 L2+L3。**

### 2.3 已具备的「对齐尺子」（关键资产）

| 工具 | 能力 | 现状 |
|------|------|------|
| `pa_acceptance.spearman_srcc` / `srcc_from_label_rows` | 算法分 vs 人类分相关性 | 在，未喂真人标签 |
| `export_pa_blind_review` | 盲评导出 | 在 |
| `cover_selection_blind_review.py` / `algorithm_v2_signoff.py` | 盲评签核（judgeVerdict A/B/C） | 在，synthetic 占位 |
| `feedback.py`（pairwise） | 人类两两偏好 | 在（个性化用，后置） |
| `photo_cull_ml.py` + pyiqa | 学习型模型推理 + 缓存 | 在，仅挂 topiq |
| `AestheticConfig.source` 含 `"mllm"` | 已预留 MLLM 来源枚举 | 在 |

> **缺的不是尺子，是「会量人类偏好的模型」+「人类标签」。**

---

## 3. 目标与非目标

### 3.1 目标

| ID | 目标 | 衡量 |
|----|------|------|
| **G-AA-01** | 量出当前差距 | 算法分 vs 作者盲评的 **SRCC 基线**（预期偏低） |
| **G-AA-02** | 提升整体审美对齐 | 新配置 SRCC 较基线显著上升（目标 ≥ +0.15 绝对值或达 ≥0.6） |
| **G-AA-03** | 高价值图位更「像人选的」 | 封面/hero/决定性瞬间**盲评胜率** vs 现状 ≥ 60% |
| **G-AA-04** | 坏照片仍被压制 | 闭眼/糊脸/废片不进重点位（继承 Portrait PRD） |
| **G-AA-05** | 成本与稳定可控 | MLLM 每 trip 调用数有上限；fail-open 通过；可复现 |

### 3.2 非目标

- 不做个性化口味（DA-3 后置）。
- 不做全量 MLLM 打分（仅短名单）。
- 不重写下游选型主框架（继续经 `purpose_overall` 注入）。
- 不做修图、不做用户必经标注 UI。

---

## 4. 总体架构（学习型审美主导 + 人类校准）

```text
asset
 ├─ L1 技术/人像（规则 + Portrait PRD）           → aesthetic.dims（含 subjectClarity）
 ├─ L2 学习型审美（本地：nima / clipiqa，AVA 训练） → aesthetic.signals.learnedAesthetic
 └─ L3 内容/情绪（MLLM，仅短名单高价值图位）        → aesthetic.signals.mllmScore + critique
                         │
        人类标签校准（作者盲评 → SRCC / 权重拟合）
                         ▼
   aesthetic.overall = blend(rules_dims, learnedAesthetic, mllmScore)
                         ▼
   purpose_overall(asset, purpose) → 封面 / hero / solo / 决定性瞬间 / 拼图主图
```

**三档信号、统一出口**：无论本地学习分还是 MLLM 分，最终都汇入 `aesthetic.overall` / `subjectClarity`，下游消费者**零改动**（与 Portrait PRD §5.6 同一注入哲学）。

---

## 5. 实施路线（A→B→C，复用现有地基）

### 5.A 路线 A · 本地审美模型（低成本、立即）

- 在 `photo_cull_ml.py` 的 pyiqa 管线里，新增/切换 **审美训练模型**：`nima`（AVA 人类评分）或 `clipiqa+`。同一缓存、同一设备探测逻辑。
- 写入 `quality.aesthetic.signals.learnedAesthetic`（[0,1]）。
- 开 `ml_calibrate`，把 learned 分 blend 进 `overall`（初始 blend 低，校准后调）。
- **产出**：一个真正「学过人类审美方向」的分，替代纯规则主导。

### 5.B 路线 B · 人类标签 + 量化对齐（关键，必做）

1. `scripts/aesthetic_blind_review.py`（基于 `export_pa_blind_review`）：导出 N 张（建议 ≥150，覆盖人像/风景/食物/合影）给作者**盲评**（1–5 分或两两比较）。
2. 跑 `spearman_srcc`：得到 **rules / rules+learned / 各配置** vs 人类的 SRCC。
3. 用人类标签**拟合 blend 权重 与 purpose 权重**（小规模网格搜索，非训练）。
4. **门槛**：只有 SRCC 实测上升的配置才允许成为默认（A/B）。

### 5.C 路线 C · MLLM 高价值图位（触及 L3，仅短名单）

- 新建 `travelogue/vision/aesthetic_mllm.py`，复用现有 LLM 客户端模式（参考 `narrative_brief.py` / `chapter_titles.py` 的 deepseek 接入），换**视觉可用模型**。
- **仅对短名单调用**：每 trip 取 cover/hero/决定性瞬间各自的 **top-K 候选**（如 K=5），送 MLLM 打分 + 一句话点评（通用大众审美 rubric）。
- 写入 `quality.aesthetic.signals.mllmScore` + `critique`；按 `contentSig` 缓存、温度 0（AA-PR-04）。
- `source="mllm"` 时，`overall` 对短名单融合 MLLM 分；非短名单仍走本地。

---

## 6. 评测方法论（本 PRD 的灵魂）

| 方法 | 工具 | 用途 |
|------|------|------|
| **SRCC（序相关）** | `spearman_srcc` | 整体分布对齐度，主指标 |
| **盲评胜率** | `aesthetic_blind_review` + `algorithm_v2_signoff` | 高价值图位 A/B（新 vs 旧选择） |
| **缺陷率** | Portrait PRD AC-PC-D* | 坏照片是否被压制 |
| **覆盖/降级率** | telemetry | learned/MLLM 命中与回退 |

> **铁律（AA-PR-01）**：每个里程碑出口都必须给出「SRCC 或盲评胜率」的实测数字，否则不上线。

---

## 7. 数据模型

```jsonc
"quality": {
  "aesthetic": {
    "source": "rules+ml",            // rules | rules+ml | mllm（已有枚举）
    "overall": 0.74,
    "dims": { "composition": 0.7, "exposure": 0.66, "color": 0.8,
              "lighting": 0.55, "subjectClarity": 0.78 },
    "signals": {
      "learnedAesthetic": 0.71,      // 路线 A · nima/clipiqa
      "learnedMetric": "nima",
      "mllmScore": 0.83,             // 路线 C · 仅短名单
      "mllmModel": "<vision-model>",
      "mllmShortlist": "cover"       // 该图因哪个图位进了短名单
    },
    "critique": "孩子大笑的决定性瞬间，逆光轮廓干净。"  // MLLM 一句话（可空）
  }
}
```

- 所有新字段**允许缺失**；缺失即回退上一层（mllm→learned→rules）。
- `critique` 可被 Studio 换图面板或封面解释复用（非必需）。
- schema：`aesthetic.signals` 已是开放 `number|null` map（见 `trip.schema.json`），`critique` 已存在；**新增字段大多无需改 schema**，仅 `learnedMetric`/`mllmModel`/`mllmShortlist` 字符串需补白名单。

## 8. 配置规格

```yaml
aesthetic:
  enabled: true
  source: rules+ml              # 路线 A 后默认；路线 C 上线后高价值图位走 mllm
  ml_calibrate: true            # 路线 A：开启 learned 融合
  ml_calibrate_blend: 0.4       # 由路线 B 人类标签拟合后回填
  use_purpose_presets: true

  learned:
    metric: nima                # nima | clipiqa+ | topiq_nr(旧)
    device: auto
    allow_cpu: true

  mllm:
    enabled: false              # 路线 C 默认关，灰度开
    shortlist_purposes: [cover, hero, moment]
    shortlist_k: 5              # 每图位候选数
    max_calls_per_trip: 20      # 成本闸（AA-PR-05）
    temperature: 0.0            # 确定性（AA-PR-04）
    cache: true                 # 按 contentSig 缓存
    rubric: universal           # 通用大众审美（DA-3）
```

## 9. 里程碑

| 里程碑 | 内容 | 出口（必须有数字） |
|--------|------|--------------------|
| **M0** | `aesthetic_blind_review.py` + 作者盲评 ≥150 张 + 冻结标签集 | 标签集入库 |
| **M1（路线 A）** | 接入 nima/clipiqa，写 `learnedAesthetic`，开 ml_calibrate | learned 推理跑通；缓存生效 |
| **M2（路线 B）** | SRCC 基线 + 网格拟合 blend/purpose 权重 | **SRCC：rules vs rules+learned 对比表**；G-AA-01/02 |
| **M3（路线 C）** | `aesthetic_mllm.py`，短名单 MLLM 打分 + critique，确定性缓存 | 高价值图位**盲评胜率**；G-AA-03 |
| **M4** | 默认配置切换 + dogfood + 回归 | 全 AC 通过；与 Portrait PRD 合并 signoff |

## 10. 验收标准

| ID | 条件 |
|----|------|
| **AC-AA-00** | 作者盲评标签集冻结（≥150，覆盖多题材），可复跑 SRCC |
| **AC-AA-01** | `learnedAesthetic` 在标签集上 SRCC > 现 rules 主导基线 |
| **AC-AA-02** | 拟合后 `overall` SRCC ≥ 0.6 或较基线 +0.15（取先达） |
| **AC-AA-03** | 封面/hero/决定性瞬间：新选择盲评胜率 ≥ 60%（不劣于旧 ≥ 90%） |
| **AC-AA-04** | MLLM 不可用/超额 → 回退 learned/rules，导入成功率不变 |
| **AC-AA-05** | MLLM 同图同配置二次运行结果一致（缓存 + 温度 0） |
| **AC-AA-06** | 每 trip MLLM 调用 ≤ `max_calls_per_trip` |
| **AC-AA-07** | 坏照片（闭眼/糊脸/废片）不进重点位（继承 AC-PC-D*） |
| **AC-AA-08** | 关闭 `mllm`/`ml_calibrate` 可逐位回到现网行为 |

## 11. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 自标注样本偏作者口味 | DA-3 限定「通用大众审美」rubric；样本覆盖多题材；个性化后置 |
| 标签量小、SRCC 不稳 | ≥150 起步，可增量；用两两比较降低打分噪声 |
| MLLM 非确定/漂移 | 温度 0 + contentSig 缓存 + 仅短名单；模型版本写入字段 |
| MLLM 成本 | `max_calls_per_trip` + 仅 cover/hero/moment + 缓存命中复用 |
| 隐私（图出本地） | mllm 默认关；可只用本地路线 A/B；文档显著标注 |
| 学习模型权重过猛 → 风格单一 | blend 由 SRCC 拟合，灰度上调；保留 rules 兜底 |
| 与 Portrait PRD 口径冲突 | 人像质量作为 L1 输入并入 `subjectClarity`，不双算 |

## 12. 与 Portrait PRD / Phase 12 关系

| 文档 | 角色 |
|------|------|
| **本 PRD** | L2/L3 学习型审美 + 人类对齐（主收益：挑出好照片） |
| [PRD-PORTRAIT-CULL.md](./PRD-PORTRAIT-CULL.md) | L1 人像质量（睁眼/清晰）→ 本 PRD 的 `subjectClarity` 输入 + 废片下限 |
| [PRD-PHASE12.md](./PRD-PHASE12.md) | 分支化评分骨架 |

> 实施顺序建议：**先并行做 Portrait M1（拿到人脸信号）与本 PRD M0（人类标签）**，再进 M1/M2，避免返工。

## 13. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-06-16 | 初稿：诊断「规则优化无瑕疵≠人类好照片」；三层模型；复用 pyiqa + pa_acceptance + MLLM；DA-1~4 已拍板；路线 A/B/C + SRCC/盲评评测 + 里程碑/AC |
