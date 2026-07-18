# Travelogue · 版式质量栈 LQS V1 · 实施清单（瘦身版）

| 属性 | 内容 |
|------|------|
| **纲领** | [PRD-LAYOUT-QUALITY-STACK-V1.md](./PRD-LAYOUT-QUALITY-STACK-V1.md)（LQS） |
| **子主题 SSOT** | [MSR](./PRD-MCS-SIGNATURE-ROUTING-V1.md) · [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [GCS](./PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) |
| **依据** | [可行性与成本评估](./acceptance-records/layout-quality-stack-v1-feasibility-cost-2026-07-18.md) + 开发负责人代码审视（2026-07-18） |
| **版本** | v1.1 |
| **状态** | **部分废止** — S1 与 [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) W1 为同一批工作可执行；**S2 起任务卡废止，由 TPC v0.2.0 W2 承接**（TPC 评审 BLK-TPC-05 收口 · 2026-07-18） |
| **范围口径** | **瘦身版**：约 15–25 开发人日 / 4–5 周；相对子 PRD 全量的裁剪与触发条件见 §5 |
| **纪律** | 子 PRD 已冻结的**铁律与禁区照单全收**（禁改 rect · 禁 BRIC@legacy · LSE 冻结 · 硬过滤序）；裁剪只发生在「交付物范围与流程仪式」层 |
| **更新日期** | 2026-07-18 |

---

## 0. 核心原则（本清单与子 PRD 的差异声明）

1. **先测量、后建设**：任何硬筛 / 工厂 / soft 罚项动工前，必须先有 S1 基线报表数字。
2. **决策门制**：S2 起每个工作包有明确进入条件（§3），数字不达标即不做，不算失败。
3. **准入机制收敛**：MGQ `constraints.eligibility` 必须与现网 `mainSlotPolicy`（`main_eligibility.py`）收敛为一套语义，**禁止**并存第三套准入机制（对子 PRD 的设计补充，需回写 MGQ IMPLEMENTATION）。
4. **流程减重（偏差登记）**：
   - 三主题各自的 ACCEPTANCE 合并为一份 `ACCEPTANCE-LAYOUT-QUALITY-STACK-V1.md`（覆盖瘦身范围；子主题日后扩量再拆）——**偏差于各 BLK-08，需产品签核**（本轮已认可）。
   - GCS-B 海报默认露出门禁由「正式三方盲评 ≥55%」降为「狗粮自评 N≥5 敢发群」——**偏差于 D-GCS-10**；若日后对外默认开启，再补正式盲评。
   - MGQ 评分台（W2）不在 V1 范围；标定复用 `compare.html` 并排 + 手记。

---

## 1. 里程碑总览

| Sprint | 内容 | 开发人日 | 出口 |
|--------|------|----------|------|
| **S1**（第 1 周） | 守门修复 + 基线报表 + MSR shadow | 5–7 | **数字化决策依据**；G1 决策会 |
| **S2**（第 2–3 周） | （条件）MSR 硬筛 + MGQ eligibility（收敛版） | 6–10 | 硬层可 dogfood；golden/LRG 绿 |
| **S3**（第 3–4 周） | GCS-B 海报 Writer + 手写 SKU 补库 | 5–7 | 海报可狗粮；空洞 SKU 入 experimental |
| **S4**（第 5 周） | MGQ raw 特征 + 触发率分析 + 狗粮对比 | 3–4 | G2 决策会：soft 罚项 / caption prefer 是否进入 |
| **合计** | — | **19–28** | 全程 flag 默认 off；无默认开承诺 |

---

## 2. 任务卡

### S1 · 测量与还债（必做，无前置）

| ID | 任务 | 说明 | 估时 | 对应 AC |
|----|------|------|------|---------|
| **S1-1** | 修复硬过滤绕过（BLK-10） | `selfheal.drop_worst_asset` 重建 `WindowContext` 走 `generate_window_candidates_with_rejections`；`replan_screen(legacy)` 结果强制过硬过滤；分路径负例单测 | 3–4d | AC-MGQ-12 / AC-MSR-12 |
| **S1-2** | 基线报表脚本 | 读现有 `MosaicWindowLog` / `layout_metrics`（`planner_path`、`used_legacy`、`aspectPatternMatchRate`），在代表 trip 集上输出：legacy 率、方向错配窗占比、按 N 分布的失败原因 | 1d | 新增（G1 输入） |
| **S1-3** | MSR W0 shadow | 字母表 `L/P/S`（panorama→L、tall→P）+ 模板派生 + 窗口签名 + `shadow_log`；`enabled=false` 零行为差；输出**签名空洞清单 v0**（exact 无命中的签名 × 频次） | 2d | AC-MSR-01/02/13 |

**S1 出口 = G1 决策会材料**：legacy 率、错配率、空洞清单（按频次排序）。

### S2 · 硬层（进入条件见 §3 G1）

| ID | 任务 | 说明 | 估时 | 对应 AC |
|----|------|------|------|---------|
| **S2-1** | SignatureIndex + L1/L2/L3 硬筛 | registry load 构建一次；挂 `generate_window_candidates` 入口；L3 剔除 `direction_conflict`；`signature:*` taxonomy；与 `try_order_for_pattern` 分账（ordering 仅同签名内对齐） | 4–6d | AC-MSR-03～07/14 |
| **S2-2** | MGQ eligibility（收敛版） | `constraints.eligibility` 求值器接在 URO 之后；**吸收 `mainSlotPolicy` 语义**（AR 门禁迁移或桥接，二选一在实现时写死，不双轨）；未声明 ≡ 不参与硬拒绝；不进 `USAGE_RULE_UNDO_ORDER` | 3–4d | AC-MGQ-03/05/15 + BLK-11/12 |
| **S2-3** | 回归硬门 | 杂志 golden / LRG smoke 全绿；`enabled=false` 与 baseline 逐屏一致 | 含上 | AC-MGQ-01 / AC-MSR-01 |

### S3 · 旁路与补库（S3-1 可与 S2 并行）

| ID | 任务 | 说明 | 估时 | 对应 AC |
|----|------|------|------|---------|
| **S3-1** | GCS-B `poster_bric` Writer | vendor MIT BRIC 核心（钉 commit）；contain 贴图；export job sidecar；扩独立 `EngineId`/platform；`features.gcs_poster_bric=false`；n∈[3,9]、collage 排除 | 4–5d | AC-GCS-01/05/06/07/09 |
| **S3-2** | 手写空洞 SKU | 按 S1-3 空洞清单**手写** 2–3 个混向 YAML（role/mix/usage/eligibility 齐全）→ validator → admission experimental；**不建工厂** | 1–2d（含设计） | AC-GCS-04（准用） |
| **S3-3** | 图文 SKU | 手写 2 个带 `captionAreas` 的 SKU（为 caption prefer 备料） | 1d | AC-MSR-03（准用） |

### S4 · 特征与二次决策

| ID | 任务 | 说明 | 估时 | 对应 AC |
|----|------|------|------|---------|
| **S4-1** | MGQ raw 特征落 log | `heroProminenceRatio` / `heroCoverageRatio` / `cellAreaCv`（面积口径 `col_frac×row_frac`），只记录不惩罚 | 1–2d | AC-MGQ-04（raw 部分）+ BLK-09/13 |
| **S4-2** | 触发率分析 | 代表 trip 上三特征分布：若「越界屏」占比显著（阈值 G2 会上定），才排 soft 罚项 | 0.5d | G2 输入 |
| **S4-3** | 狗粮并排对比 | 复用 `lse_flags_curate_compare.py` / `compare.html`：MSR+eligibility on vs off；手记结论 | 1d | 代替评分台 |

---

## 3. 决策门

### G1（S1 末）· 硬层是否全量做

| 数字 | 结论 |
|------|------|
| legacy 率或方向错配率 **≥ 10%**（代表 corpus） | S2 全量（S2-1 + S2-2） |
| **3%–10%** | 只做 S2-2（eligibility 收敛）；S2-1 降级为 shadow 长跑 |
| **< 3%** 且空洞集中于个别签名 | 跳过 S2-1；只做 S3-2 手写补库 |

### G2（S4 末）· soft 罚项与 caption prefer 是否进入

| 数字 | 结论 |
|------|------|
| raw 特征越界屏占比显著 + 狗粮对比可感知 | 排 MGQ soft（+3–4d，阈值用已冻结值） |
| caption-active 窗占比可观且已有图文 SKU | 排 caption prefer（+2–3d） |
| 均不显著 | 保持只记录；把结论回写子 PRD 状态行 |

---

## 4. 与子 PRD 的 AC 映射（瘦身范围内必须满足）

| 来源 | 保留的硬性 AC |
|------|---------------|
| MGQ | AC-MGQ-01（off 一致）· 03 · 05 · 11（LSE 落点 CI）· 12（分路径守门）· 15 |
| MSR | AC-MSR-01 · 02 · 03 · 04 · 07 · 11 · 12 · 13 · 14 |
| GCS | AC-GCS-01（无 BRIC@MCS）· 05 · 06 · 07 · 08（golden/LRG W1 硬门）· 09（GPL 扫描） |
| 共同 | 硬过滤序一字面（LQS §4.1）；确定性（同输入同输出） |

**暂不承接**（随裁剪项挂起）：AC-MGQ-06/07/08/13/14（soft/评分台）、AC-MSR-05/06/08/09/10（caption/replan/page_group）、AC-GCS-02/03（工厂）、各 AC-*-BLIND。

---

## 5. 裁剪登记与重启触发条件

| 裁剪项 | 重启条件 |
|--------|----------|
| **GCS 轨 A 枚举工厂** | 空洞清单持续 **>10 个高频签名** 且手写补库跟不上滚动需求 |
| **MGQ 评分台（W2）** | 出现 ≥2 名固定标注人力，或单人手记无法支撑调权分歧 |
| **MGQ 三 soft 罚项** | G2 触发率显著 + 狗粮可感知 |
| **caption prefer / replan** | 图文 SKU ≥3 且 caption-active 窗占比可观（prefer 先行；replan 永远默认 off） |
| **page_group** | 连拍拆屏在狗粮中被反复点名 |
| **正式三方盲评（各 BLIND）** | 任一主题要**默认对用户开启**之前（不可跳过） |
| **拆分三份独立 ACCEPTANCE** | 子主题超出瘦身范围扩量时 |

---

## 6. 风险与守则

| 风险 | 守则 |
|------|------|
| S2 硬筛后 legacy 飙升 | L3 兜底保留；reject 看板先行；flag 可回滚 |
| eligibility 与 mainSlotPolicy 双轨 | S2-2 完成定义前**不合码**；实现方案二选一写死 |
| 海报与九宫格串词 | 文案冻结「单屏海报」；telemetry 分名 |
| 测量脚本口径漂移 | S1-2 脚本 + trip 集清单进仓库，作为后续所有对比的 SSOT |
| 瘦身被误读为「PRD 作废」 | 子 PRD 冻结决策全部有效；本清单只裁剪交付物与仪式，见 §0 |

---

## 7. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-18 | 首版：开发负责人瘦身方案经产品认可；S1–S4 任务卡 + G1/G2 决策门 + 裁剪登记 |
