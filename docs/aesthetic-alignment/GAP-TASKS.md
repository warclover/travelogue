# PRD 差距任务清单（Aesthetic Alignment）

> 对照：[PRD-AESTHETIC-ALIGNMENT.md](../PRD-AESTHETIC-ALIGNMENT.md) v0.2.0 · **[PRD-STRATIFIED-CURATION.md](../PRD-STRATIFIED-CURATION.md) v1.0.0**  
> 基线实现清单：[TASKS.md](./TASKS.md) · **分层路线**：[TASKS-STRATIFIED.md](./TASKS-STRATIFIED.md) · 验收：[SIGNOFF-M4.md](./SIGNOFF-M4.md)  
> 更新：2026-06-18 · 分支 `feat/aesthetic-alignment`

---

## 0. 路线说明（2026-06-18）

**v1 主路线**已切换至分层精选（AC-SC-*）。本文档 GAP-* 中未达标项，按 [TASKS-STRATIFIED.md](./TASKS-STRATIFIED.md) P0–P4 承接：

| 原 GAP | 分层承接 |
|--------|----------|
| GAP-02 pooled SRCC | P2-1 统一 stratum blend + **AC-SC-02** 加权分层 Δ |
| GAP-03 图位盲评 | P0-7 / P2-8 + **AC-SC-03** |
| GAP-04 purpose 权重 | P2-4 stratum × purpose 网格 |
| landscape/food 语料缺 | **P1-2 / P1-3** |

---

## 1. 里程碑完成度（PRD §9）

| PRD 里程碑 | 出口要求 | 现状 | 差距 |
|------------|----------|------|------|
| **M0** | ≥150 张盲评 + 冻结标签 + SRCC 可复跑 | 109 张已冻结；SRCC=0.2548 | **缺 41+ 张**；多 trip / 多题材不足 |
| **M1** | nima/clipiqa + learned + 缓存 | ✅ 代码 + demo 实测 | clipiqa+ SRCC 更差，未作默认 |
| **M2** | SRCC 对比表 + **blend & purpose 拟合** | blend/stratum 网格 ✅ | **purpose 权重未拟合**；AC-AA-02 未达标 |
| **M3** | MLLM 短名单 + **高价值图位盲评胜率** | API 8/8 + cache ✅ | **AC-AA-03 未做**（TASKS 误标完成） |
| **M4** | 默认切换 + dogfood + 全 AC | G1+G2 dogfood ✅ | **G3 阻塞**；8 项 AC 中 3 项未过 |

---

## 2. 目标差距（PRD §3.1）

| 目标 ID | 衡量 | 现状 | 任务 |
|---------|------|------|------|
| **G-AA-01** | SRCC 基线 | ✅ 0.2548 | 扩语料后重跑基线 |
| **G-AA-02** | SRCC +0.15 或 ≥0.6 | ❌ 最好 +0.037（oracle） | 见 §4 P0 |
| **G-AA-03** | 封面/hero/瞬间盲评胜率 ≥60% | ❌ 未测 | **GAP-03** |
| **G-AA-04** | 坏片不进重点位 | ⚠️ 继承 cull；Portrait 未做 | **GAP-07** + P-1 |
| **G-AA-05** | MLLM 成本/可复现 | ✅ cache + 上限 | 补 telemetry（**GAP-11**） |

---

## 3. 验收标准 AC-AA（PRD §10）

| AC | 状态 | 遗漏 / 说明 |
|----|------|-------------|
| **AC-AA-00** | ✅ | **163** 张（109+54）已冻结 |
| **AC-AA-01** | ✅ | learned blend SRCC 0.2855 > rules |
| **AC-AA-02** | ❌ | 未达 +0.15；**禁止改 AppConfig 默认**（正确） |
| **AC-AA-03** | ❌ | 需 A/B pairwise，非 SRCC；cover 仍为 asset-102，MLLM 首推 asset-104 |
| **AC-AA-04** | ⚠️ | 单元测试有；**缺 ingest 成功率 E2E 回归** |
| **AC-AA-05** | ✅ | 二次 curate cached=8 |
| **AC-AA-06** | ✅ | 8≤20 |
| **AC-AA-07** | ❌ | 依赖 Portrait PRD M1（睁眼/糊脸）；仅 portrait_lite 启发式 |
| **AC-AA-08** | ✅ | 开关回退测试 |

---

## 4. 遗漏任务（按优先级）

### P0 · 阻塞 G3 全量 / PRD 主出口

| ID | 任务 | PRD 依据 | 状态 | 建议产出 |
|----|------|----------|------|----------|
| **GAP-01** | 扩充人类标签语料至 **≥150 张**（多 trip：人像/风景/食物/合影） | M0、AC-AA-00、§5.B | [x] | **163** 张 · `aesthetic-human-labels.merged.v2.json` |
| **GAP-02** | 达标 SRCC：**+0.15 或 ≥0.6**（扩样后重跑 M2 校准） | G-AA-02、AC-AA-02、§5.B.4 | [~] | pooled 未达标 → **AC-SC-02** · `TASKS-STRATIFIED` P2 |
| **GAP-03** | **高价值图位盲评**：rules vs G1+G2 的 cover/hero/moment **pairwise 胜率 ≥60%** | G-AA-03、AC-AA-03、§6、M3 出口 | [x] | v4-p3 **3/5 strict** · [waiver](../acceptance-records/purpose-pairwise-waiver.v4.json) 接受 |
| **GAP-04** | **purpose 预设权重网格拟合**（cover/hero/moment 的 5 维权重，非仅 blend） | §5.B.3 | [x] | `grid_search_purpose_weights()` + `scripts/aesthetic_purpose_calibrate.py` |

### P1 · PRD 明示但未实现 / 未完成

| ID | 任务 | PRD 依据 | 状态 | 说明 |
|----|------|----------|------|------|
| **GAP-05** | **AppConfig 默认 G3 pilot** | §8、M4、G3 signoff | [x] | v4 waiver · [aesthetic-g3-signoff.v4.json](../acceptance-records/aesthetic-g3-signoff.v4.json) |
| **GAP-06** | **Portrait PRD M1**（MediaPipe 睁眼/脸锐度 → subjectClarity L1） | §12、AC-AA-07、P-1 | [ ] | 替换/增强 `portrait_lite`；见 PRD-PORTRAIT-CULL |
| **GAP-07** | AC-AA-07 **dogfood 度量**：重点位闭眼/糊脸率 vs 基线 | G-AA-04、AC-PC-D* | [x] | `aesthetic_portrait_defect_signoff.py` |
| **GAP-08** | **封面选型与 aesthetic 对齐**：MLLM 高分图未成为 cover（asset-104 vs 102） | §4 架构、dogfood 观察 | [x] | `cover_logit_v2` MLLM cover 短名单 +0.12·score tie-break |
| **GAP-09** | **拼图主图 / solo** 图位 SRCC & 盲评（PRD §4 提到拼图主图） | §4、§3.1 | [x] | eval/blind 导出 `predictedSolo` / `blendedSolo` |
| **GAP-10** | **ingest 阶段** optional aesthetic（现仅 curate hook） | §5.A 低成本 | [x] | `aesthetic.warm_learned_on_ingest` → ingest 后 warm learned cache |
| **GAP-11** | **telemetry**：learned/MLLM 命中率、fail-open 降级率 | §6 覆盖/降级率 | [x] | `trip.curation.aestheticAlignment` + algorithmProfile 字段 |
| **GAP-12** | **AC-AA-04 E2E**：MLLM 不可用 / stub 时 ingest+curate 成功率不变 | AC-AA-04 | [x] | `tests/test_aesthetic_failopen_e2e.py` |
| **GAP-13** | **两两比较盲评**（降噪声，PRD §5.B.1 / §11） | §5.B、风险 | [x] | `--export-pairwise` on `aesthetic_blind_review.py` |
| **GAP-14** | **config 规格补全**：`learned.device` 映射到 cull ML device | §8 | [x] | `aesthetic.learned.device` → `CullConfig.ml_device` |
| **GAP-15** | **PRD 文档状态**：v0.1.0 仍为 Draft | 元数据 | [ ] | 评审通过后改 Approved + 修订记录 |

### P2 · 体验 / 文档 / 工程债

| ID | 任务 | PRD 依据 | 状态 | 说明 |
|----|------|----------|------|------|
| **GAP-16** | Studio **展示 `critique` / mllmScore**（换图面板，非必需） | §7 | [x] | P4-1 · preview-toolbar 审美抽屉 |
| **GAP-17** | **algorithm-inventory / DESIGN** 同步 AA 模块 | 实现模块 § | [ ] | 文档与代码一致 |
| **GAP-18** | trip **schema / render 校验**：`screenId` 等既有问题 | dogfood | [ ] | demo render 需 `--no-validate` |
| **GAP-19** | **clipiqa+ 二次实验**（扩语料后） | §5.A | [ ] | M1-5 已证 nima 更优；可复验 |
| **GAP-20** | **portrait_lite 调参 / 可关默认**：demo 上略降 SRCC | M2 观察 | [~] | A/B：`portrait_lite_enabled: false` |
| **GAP-21** | **多作者 / 外部盲评**（降低自标偏差） | §11 风险 | [ ] | 后置；DA-3 个性化更后置 |
| **GAP-22** | **合并 PRD signoff**：Portrait + AA 联合签字 | M4、§12 | [ ] | 等 GAP-06 进展 |

---

## 5. 已实现但 TASKS 需更正

| 条目 | 原状态 | 更正 |
|------|--------|------|
| M0 出口 AC-AA-00 | 标完成 | **部分完成**（109/150） |
| M3-3 盲评胜率 | [x] | 应为 **[~]**：仅 API 成功，**未测 pairwise 胜率** |
| M2-3 默认配置 | [~] | 保持；GAP-02 未达标 |

---

## 6. 建议实施顺序

```text
GAP-01 扩语料 ──► GAP-02 重校准 ──► GAP-04 purpose 权重
        │                                    │
        └──────────────► GAP-03 盲评胜率 ◄──┘
                              │
        GAP-06 Portrait M1 ──► GAP-07 缺陷率
                              │
        GAP-08 cover 权重 ──► GAP-03 复测
                              │
        全部 AC 过 ──► GAP-05 G3 改默认 + GAP-15 PRD Approved
```

**可并行**：GAP-11 telemetry、GAP-12 fail-open E2E、GAP-16 Studio UI、GAP-10 ingest 预热。

---

## 7. 快速命令（差距相关）

```bash
# 新 trip 语料
python scripts/aesthetic_blind_review.py --init-corpus docs/acceptance-records/aesthetic-alignment-corpus.v2.json

# 合并语料 M2 验收（GAP-02）
python scripts/aesthetic_merged_eval.py --corpus docs/acceptance-records/aesthetic-alignment-corpus.v2.json --labels docs/acceptance-records/aesthetic-human-labels.merged.v2.json --write docs/acceptance-records/aesthetic-m2-merged.v2.json

# purpose 权重网格（GAP-04，需 pyiqa）
python scripts/aesthetic_purpose_calibrate.py --trip-dir trips/demo-2025-6 --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json

# 图位盲评 signoff 模板 + 自动化 proxy（GAP-03）
python scripts/aesthetic_purpose_blind.py --trip-dir trips/demo-2025-6 --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json --ml-calibrate

# pairwise 导出（GAP-13）
python scripts/aesthetic_blind_review.py --srcc docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json --export-pairwise

# 自动化 signoff 门禁（填 verdict 后）
python scripts/algorithm_v2_signoff.py --from-json docs/acceptance-records/aesthetic-cover-blind.json
```

---

## 8. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-18 | 锡兰之旅 +54 标签；merged v2=163；M2 双 trip 校准 + `aesthetic_merged_eval.py` |
| 2026-06-18 | **PRD-STRATIFIED-CURATION v1** + TASKS-STRATIFIED P0–P4 + RUBRICS-v1 + corpus v3 模板 |
