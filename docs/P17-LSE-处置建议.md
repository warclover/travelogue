# P17 LSE 处置建议

| 属性 | 内容 |
|------|------|
| **文档类型** | 工程处置 / 产品结论 |
| **范围** | Phase 17 Layout Strategy Engine（LSE）及 9 项 capability |
| **版本** | v1.0 |
| **日期** | 2026-06-08 |
| **状态** | **已采纳：代码保留现状，能力默认关闭，不作产品卖点** |
| **关联** | [PRD-PHASE17-layout-strategy-engine.md](./PRD-PHASE17-layout-strategy-engine.md)、[PRD-智能排版开关页.md](./PRD-智能排版开关页.md)、[acceptance-records/lse-flags-admin.md](./acceptance-records/lse-flags-admin.md) |
| **证据脚本** | `scripts/lse_flags_curate_compare.py`、`scripts/lse_flags_preview_ablate.py` |

---

## 1. 结论（TL;DR）

**不能判定为「代码没作用、应删除」；应判定为「对用户观感尚未证明有效，当前产品价值接近零」。**

| 维度 | 判定 |
|------|------|
| 技术接线 | ✅ 已接通：`capabilityFlags` → mosaic/beam 打分链，非 dead code |
| 成稿离散变化 | ⚠️ 极少：真实 trip 上多为 0%～2% 屏级 pattern 变化 |
| 肉眼观感提升 | ❌ 并排预览无本质差异，dogfood 未观察到可感知提升 |
| **处置** | **保留代码与开关页；生产默认 LSE 关；不推广、不承诺效果；后续按验收门槛再决定是否加强或降级** |

---

## 2. 依据摘要

### 2.1 真实相册 A/B（LSE 关 vs 能力全开）

| 相册类型 | 代表 trip | 屏变更率 | 备注 |
|----------|-----------|----------|------|
| 东澳岛 / 竖图单张为主 | `demo-2025`、`demo-80301df45c` 等 | **0%** | mosaic 路径参与少 |
| 川藏 / 横竖混排 | `demo-1506104ebf` | **~1.4%**（72↔72 对齐） | 1 屏 mosaic-6→mosaic-5 |
| 林芝 / Studio | `linzhi`、`chuanzang-studio` | **~1.5%～2%** | 个别 landscape↔mosaic |
| 年会横图集 | `demo-2019` | **~3.8%** | 多为 mosaic-6↔mosaic-5 |

> **注意**：若 baseline 与 caps 屏数不一致（如 72→73），按索引对比会**夸大**变更率（曾出现 34% 假象）。评估时应优先看 **pattern 签名对齐** 或固定屏数下的 diff。

### 2.2 单能力消融（川藏线 · 2026-06-08）

报告：`.cache/lse-flags-compare/demo-1506104ebf/ablation_report.json`

| 能力 | 相对 baseline 屏变更 |
|------|---------------------|
| `hungarian_assignment` | **1/72（1.39%）** — 唯一可单独复现 caps 全开时的变化 |
| 其余 7 项（saliency、tone、beat 等） | 0/72 |

说明：多数能力当前以 **beam/mosaic 内软乘子** 存在，很少翻转离散 template 选择。

### 2.3 与竞品差距的关系

观感差距的主因仍在于：**选片质量、模板库丰富度、trip 级全局编排**，而非「9 个 bool 开关是否打开」。LSE 在现有架构（局部贪心 + 有界 beam）下，难以单独拉齐 Apple/Google/Shutterfly 级体验。

---

## 3. 处置决定（v1.0 · 2026-06-08）

### 3.1 代码与配置：**保留现状**

- **不删除** P17 模块、策略包、rollout、telemetry、开关页与相关测试。
- **不修改** 生产默认：`layout.strategy_engine.enabled=false`，`lse_policy.yaml` 维持 `stage: dogfood`、`traffic_percent: 0`。
- **开关页**（`/lse-flags-admin`）保留，供内部实验与 dogfood；不对普通用户暴露为「智能升级」卖点。

### 3.2 产品对外

- 不对用户承诺「开启 LSE = 排版明显变好」。
- 营销/Studio 文案中避免将 P17 capability 列为已交付的差异化能力。

### 3.3 研发优先级

- **冻结** capability 权重调参、逐项加开关类工作，除非满足 §5 复评门槛。
- **优先** 选片、模板库、folio/breath 硬约束、全局编排等更直接影响观感的项（详见 [观感提升路线图.md](./观感提升路线图.md)）。
- **Program 执行**： [ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md) · Phase 18 BQP（约 7–8 个月，5 个 Integration Gate）。

### 3.4 文档与验收

- 本文件作为 P17 阶段性结论；开关页验收记录见 [lse-flags-admin.md](./acceptance-records/lse-flags-admin.md)。
- 手测项（LAN 403、UI 与磁盘一致）可补完，但不改变「默认关闭」处置。

---

## 4. 三条后续路线（暂不执行，供复评时选用）

| 路线 | 含义 | 适用条件 |
|------|------|----------|
| **A · 维持实验** | 保持现状，仅 dogfood / 脚本 A/B | 无专人投入 P17；默认 |
| **B · 加强集成** | 提高权重或将 beat/folio/tone 升为**硬否决**；扩大 beam；生产小流量 | 有明确 hypothesis + 通过 §5 门槛 |
| **C · 架构降级** | 将 LSE 收束为日志/telemetry 层，排版回 P16 主路径 | 复评仍无增益且维护成本过高 |

**当前选择：路线 A。**

---

## 5. 复评门槛（满足任一才考虑重新上量或路线 B）

在 **≥3 类真实相册**（竖图为主 / 横图混排 / 大集 mosaic 多）上，强制 LSE 全开且引擎开，需同时满足：

1. **屏级 pattern 对齐 diff ≥ 10%**，且变更屏中 **≥50% 为 pattern 变化**（非纯错位 artifact）。
2. **盲评**：≥5 名内部评审，caps_full 对 baseline **胜率 ≥ 60%**（同脚本 `phase6_cover_blind_review` 范式可借用）。
3. **代理指标不劣化**：`aspectPatternMatchRate` 不降；`timeInversionRate` 不升超过 +0.02。
4. **性能**：curate P95 增幅 ≤ 已文档化的 P17 perf budget（见 `docs/acceptance-records/p17-curate-perf.json`）。

未达标 → 继续路线 A，不扩大 rollout。

---

## 6. 内部实验操作速查

```powershell
# 批量 A/B
python scripts/lse_flags_curate_compare.py demo-1506104ebf demo-5a7c161a12

# 并排 HTML + 单能力消融
python scripts/lse_flags_preview_ablate.py demo-1506104ebf

# 本地预览（需 HTTP）
python -m http.server 8767
# → http://localhost:8767/.cache/lse-flags-compare/demo-1506104ebf/preview/compare.html
```

开关页：`http://127.0.0.1:8766/lse-flags-admin`（写 `config.yaml` 后下次 curate 生效）。

---

## 7. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-08 | 初版：dogfood 真实 trip 结论 + 保留代码、默认关闭、路线 A |
