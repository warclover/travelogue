# 人类审美对齐 · 任务清单

> 分支：`feat/aesthetic-alignment`  
> PRD：[PRD-AESTHETIC-ALIGNMENT.md](../PRD-AESTHETIC-ALIGNMENT.md) · **[PRD-STRATIFIED-CURATION.md](../PRD-STRATIFIED-CURATION.md)**  
> **分层任务**：[TASKS-STRATIFIED.md](./TASKS-STRATIFIED.md)（P0–P4）  
> **PRD 差距清单**：[GAP-TASKS.md](./GAP-TASKS.md)（遗漏任务 / AC 未过项）  
> 状态键：`[ ]` 待做 · `[~]` 进行中 · `[x]` 完成

---

## M0 · 人类标签 + SRCC 基线（demo-2025-6 已完成）

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| M0-1 | 创建分支 `feat/aesthetic-alignment` | [x] | git branch |
| M0-2 | 任务清单（本文档） | [x] | `docs/aesthetic-alignment/TASKS.md` |
| M0-3 | 核心模块：分层抽样 + 盲评导出 + SRCC 报告 | [x] | `travelogue/curation/aesthetic_blind_review.py` |
| M0-4 | CLI：`scripts/aesthetic_blind_review.py` | [x] | init-corpus / export / init-labels / srcc |
| M0-5 | 语料模板 | [x] | `docs/acceptance-records/aesthetic-alignment-corpus.template.json` |
| M0-6 | 单元测试 | [x] | `tests/test_aesthetic_blind_review.py` |
| M0-7 | demo-2025-6 语料 + 导出 109 张 | [x] | `aesthetic-alignment-corpus.demo-2025-6.json` |
| M0-8 | 作者盲评 + 冻结标签集 | [x] | `aesthetic-human-labels.demo-2025-6.json` |
| M0-9 | SRCC 基线 rules=**0.2548** | [x] | `aesthetic-baseline.demo-2025-6.json` |

**M0 出口（AC-AA-00）**：109/109 冻结 ✅ · **≥150 张未达** ⚠️（见 GAP-01）

---

## M1 · 路线 A · 本地审美模型

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| M1-1 | `photo_cull_ml` 支持 `nima` / `clipiqa+` metric 切换 | [x] | 归一化 + `learnedAesthetic` 写入 |
| M1-2 | 写入 `quality.aesthetic.signals.learnedAesthetic` | [x] | 数据模型 |
| M1-3 | 开 `ml_calibrate` blend 进 `overall` | [x] | `aesthetic_score` + config |
| M1-4 | 缓存与 fail-open 回归 + SRCC 对比脚本 | [x] | demo-2025-6 实测见 baseline JSON |
| M1-5 | demo 实测（nima / clipiqa+） | [x] | 最佳 blend0.4 nima SRCC=**0.281** |

---

## M2 · 路线 B · 人类标签校准

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| M2-1 | 网格搜索 **blend**（purpose 权重见 M2-6） | [x] | `scripts/aesthetic_calibrate.py` |
| M2-2 | SRCC 对比表（rules vs rules+learned） | [x] | `aesthetic-m2-calibrate.demo-2025-6.json` |
| M2-3 | 达标后更新默认配置 | [~] | 推荐 blend=0.35（未达 +0.15 门槛，暂不改默认） |
| M2-4 | 按 stratum 分层 blend 网格 | [x] | `--by-stratum` + `aesthetic-m2-stratum.demo-2025-6.json` |
| M2-5 | Portrait L1 lite（subjectClarity 启发式） | [x] | `travelogue/curation/portrait_lite.py` |
| M2-6 | purpose 预设权重网格拟合 | [ ] | PRD §5.B.3 · [GAP-04](./GAP-TASKS.md#p0--阻塞-g3-全量--prd-主出口) |

**M2 分层（demo-2025-6）**：uniform 0.2808 → stratum **0.287**（+0.0062）。

**M2 全栈（stratum + portrait_lite）**：overall SRCC **0.2726**（portrait_lite 在此语料略降分，待更多样本验证）。

**M3 真实 MLLM（qwen-vl-max × 8 张短名单）**：overall **0.2744**，hero **0.2796**（`aesthetic-m3-eval.demo-2025-6.json`）。oracle 上界 overall 0.2913 / hero 0.3017。

**M2 出口（AC-AA-01/02）**：learned SRCC > rules；overall SRCC ≥ 0.6 或 +0.15（未达标）。

---

## M3 · 路线 C · MLLM 高价值图位

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| M3-1 | `travelogue/vision/aesthetic_mllm.py` | [x] | 短名单打分 + critique |
| M3-2 | contentSig 缓存 + max_calls_per_trip | [x] | `cache/aesthetic-mllm.json` |
| M3-3 | 封面/hero/决定性瞬间盲评胜率 | [~] | API 8/8 ✅；**pairwise 胜率未测**（GAP-03） |
| M3-4 | `scripts/aesthetic_mllm_eval.py` | [x] | `--dry-run` / `--oracle-stub` / 全量 SRCC |
| M3-5 | curate 集成 `apply_aesthetic_alignment` | [x] | ml + portrait_lite + mllm 统一 hook |

---

## M4 · 合并 signoff

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| M4-1 | 与 Portrait PRD 联调（subjectClarity 不双算） | [x] | `portrait_lite` 仅乘数；`signals.subjectClarityBase` 防重复 |
| M4-2 | 全 AC-AA-* 通过 + dogfood | [~] | [SIGNOFF-M4.md](./SIGNOFF-M4.md) · G0 通过，AC-AA-02/03 未全过 |
| M4-3 | 默认配置切换（灰度 → 全量） | [~] | G1+G2 已在 demo-2025-6 应用 · G3 仍阻塞 |

### M4 文档

| 文件 | 说明 |
|------|------|
| [GAP-TASKS.md](./GAP-TASKS.md) | **PRD 差距 / 遗漏任务**（22 项 GAP-*） |
| [TASKS-STRATIFIED.md](./TASKS-STRATIFIED.md) | **分层精选 P0–P4**（v1 主路线） |
| [RUBRICS-v1.md](./RUBRICS-v1.md) | 分类盲评 rubric |
| [SIGNOFF-M4.md](./SIGNOFF-M4.md) | AC 矩阵 + SRCC 汇总 + 签字栏 |
| [ROLLOUT.md](./ROLLOUT.md) | G1/G2/G3 灰度步骤 |
| [config-aesthetic-alignment.example.yaml](./config-aesthetic-alignment.example.yaml) | 可复制 config 片段 |

---

## 并行轨 · Portrait PRD（L1）

| ID | 任务 | 状态 | 备注 |
|----|------|------|------|
| P-1 | Portrait M1 人脸信号 | [ ] | 见 [PRD-PORTRAIT-CULL.md](../PRD-PORTRAIT-CULL.md) |
| P-2 | 与 AA subjectClarity 注入对齐 | [x] | `portrait_lite` 乘数（M2 前 lite 版） |

---

## 快速命令（M0）

```bash
# 1. 初始化语料模板
python scripts/aesthetic_blind_review.py --init-corpus docs/acceptance-records/aesthetic-alignment-corpus.json

# 2. 编辑 corpus：填入 tripDir，调整 strata 配额

# 3. 导出盲评包（打乱顺序，含 predictedOverall）
python scripts/aesthetic_blind_review.py --export-corpus docs/acceptance-records/aesthetic-alignment-corpus.json --write docs/acceptance-records/aesthetic-blind-export.json

# 4. 生成标签模板（填 humanScore 1–5 或 0–1）
python scripts/aesthetic_blind_review.py --init-labels docs/acceptance-records/aesthetic-blind-export.json --write docs/acceptance-records/aesthetic-human-labels.json

# 5. 盲评完成后算 SRCC
python scripts/aesthetic_blind_review.py --srcc docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json --compare-purposes
```

## 快速命令（M1 · learned 模型对比）

```bash
# 安装 pyiqa（一次性，体积较大）
pip install -e ".[cull-ml]"

# 对 demo-2025-6 跑 nima 并对比 SRCC（vs M0 基线 0.2548）
python scripts/aesthetic_calibrate.py --trip-dir trips/demo-2025-6 --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json --metric nima --write docs/acceptance-records/aesthetic-m2-calibrate.demo-2025-6.json
```

## 快速命令（M2 · blend 网格）

```bash
python scripts/aesthetic_calibrate.py \
  --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json \
  --metric nima --blend-max 0.6 --blend-step 0.05 \
  --write docs/acceptance-records/aesthetic-m2-calibrate.demo-2025-6.json
```

## 快速命令（M2 · 分层 blend）

```bash
python scripts/aesthetic_calibrate.py \
  --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json \
  --metric nima --by-stratum \
  --write docs/acceptance-records/aesthetic-m2-stratum.demo-2025-6.json

python scripts/aesthetic_learned_eval.py \
  --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json \
  --metric nima --use-stratum-blend \
  --stratum-blends docs/acceptance-records/aesthetic-m2-stratum.demo-2025-6.json
```

## 快速命令（M3 · MLLM 短名单）

```bash
# 预览短名单（不调 API）
python scripts/aesthetic_mllm_eval.py \
  --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json \
  --dry-run

# 需 DASHSCOPE_API_KEY
python scripts/aesthetic_mllm_eval.py \
  --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json \
  --provider dashscope \
  --write docs/acceptance-records/aesthetic-m3-eval.demo-2025-6.json

# 离线 oracle 上界（人类标签注入短名单，验证融合链路）
python scripts/aesthetic_mllm_eval.py \
  --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json \
  --oracle-stub --use-stratum-blend \
  --stratum-blends docs/acceptance-records/aesthetic-m2-stratum.demo-2025-6.json \
  --write docs/acceptance-records/aesthetic-m3-oracle.demo-2025-6.json
```

启用 learned 审美（curate 时写入并 blend）的 config 片段：

```yaml
aesthetic:
  ml_calibrate: true
  ml_calibrate_blend: 0.4
  learned:
    metric: nima
    allow_cpu: true
```
