# 封面选型 PRD 评审会纪要

| 属性 | 内容 |
|------|------|
| **会议** | 封面选型方案 PRD 评审 |
| **日期** | 2026-06-04 |
| **文档** | [cover-selection-plan.md](../cover-selection-plan.md) v0.1 → v0.2 |
| **结论** | **有条件通过**，可进入 R0 基线；调参工程包纳入 S1 |

---

## 1. 参会与角色（模拟评审）

| 角色 | 关注点 |
|------|--------|
| **产品** | 首页第一印象、featured 意图、时间线不敏感 |
| **算法/开发负责人** | 可测、可配置、与现有代码/脚本一致 |
| **设计/内容** | 竖屏封面裁切、卷轴首屏与 mobile 池 |
| **QA** | 回归 NR-P9、盲评可复现、指标单一门禁 |

---

## 2. 议程与讨论摘要

### 2.1 目标与范围（一致通过）

- **共识**：本轮只优化 **封面 / 首页图**（`coverAssetId`、mobile/web 双布局），**不使用拍摄时间**；章分段、屏内排版、CLIP/beam 不在范围内。
- **争议**：章首 hero 是否一并测？  
  **决议**：**否**。hero 单独立项（Phase 2），避免稀释封面样本与调参轮次。

### 2.2 验收指标：7/10 vs Phase 6 的 60%（已对齐）

| 观点 | 结论 |
|------|------|
| 开发：PRD 写 A≥7/10，配置/脚本为 60%，易双标 | **对外门禁** = 人工盲评 **A≥7/10**（10 本相册） |
| 产品：7/10 是否过严 | **分两阶段**：里程碑 **M1：A≥6/10 且 A+B≥9/10**；发布 **M2：A≥7/10** |
| QA：proxy 相册 60% 保留 | **保留** `phase6_cover_blind_review.py --score-proxy` 作 **CI 回归下限**（合成相册，非发布门禁） |

### 2.3 盲评方法：top-3 从哪来（已修订）

- **问题**：`coverCandidates` 按画幅/日期多样性排序，不等于分数 Top-3，B 类判定会失真。
- **决议**：
  - 盲评表必须使用 **`scoreRankedTop3`**（全池按 `effective_cover_score` 降序）。
  - `coverCandidates` 仅作 Studio 备选展示，**不作为验收排序依据**。
  - 扩展 `scripts/phase6_cover_blind_review.py` 或新增 `scripts/cover_selection_blind_review.py` 导出字段（S0 交付）。

### 2.4 featured 子池策略（已对齐）

- **现状**：有 featured 时只在 featured 子池选封面。
- **决议**：
  - 10 本样本 **≥2 本 featured 导入、≥2 本无 featured**，**分开统计** A 率。
  - **不回退 material**：featured 池再差也尊重用户意图；若全不合格，靠 cull/导入质量解决，不在封面层偷偷换池。
  - 失败模式 `should_featured` 记入标签，走 R5 调 `featured_weight`，而非改池逻辑。

### 2.5 人像降权 vs 人脸加分（R1/R6）

- **争议**：`person_demote` 与 `face_bbox` 方向相反。
- **决议**：
  - 调参 **禁止同轮** 改 R1 与 R6。
  - **人像为主**相册（≥6/10 样本含「人像为主」标签）单独验收：**A≥5/6** 或触发 **方案 A**（见下）。

### 2.6 人像为主相册 — 方案 A 采纳（产品拍板）

当 trip 满足 **face/person 类 tag 的 asset 占比 ≥ 40%**（按 layout 可排版图计数）时：

- `person_demote` 系数改为 **1.0**（不降权）。
- 其余相册维持默认 **0.72**，R1 仅在「风景/建筑」样本上根据 `wrong_person` 标签下调。

> 阈值 40% 写入 PRD v0.2；R0 后用 1 本人像相册验证是否需改为 50%。

### 2.7 Studio / 分享用哪张封面（设计 + 产品）

- **决议**：
  - **分享、小程序、Studio  trip 卡片默认** = `coverAssetId`（**mobile 竖屏池** 选出）。
  - `exportLayout=auto` 时 **web 横图** 仅用于宽屏阅读页/导出，**不**作为首页盲评主指标。
  - 盲评主评 **mobile**；web 池 **单独记录** A 率，不阻塞 M1/M2。

### 2.8 前置：cull 与封面分工（开发主张，产品同意）

- R0 若 **≥3/10** 相册出现 `blur` 标签 → **先 0.5～1 天** 复盘 `photo_cull` 规则，再动封面乘子。
- PRD §4 仍「不改 cull 算法」，但允许 **阈值微调** 作为封面优化的 **依赖项**，需单独记 changelog。

### 2.9 工程化：因子配置化（开发必做项）

- **决议**：M1 前完成 **S1** — `config.yaml` → `curate.cover_scoring`（`person_demote`、`thirds_blend`、`sharp_ratio_cap/floor`、`featured_weight` 等），默认等于当前代码，保证零配置回归。
- `curation.coverExplain` / `coverExplainByLayout` **必须**随调参更新（已有实现，验收时抽查）。

### 2.10 不在本轮（再次确认）

时间序、geo、HDBSCAN、beam、Mosaic、CLIP/pyiqa、ingest 重写在案 **不动**。

---

## 3. 评审会决议清单（Action Items）

| ID | 事项 | 负责人 | 截止 |
|----|------|--------|------|
| **A1** | PRD 升版 **v0.2**（合并本节决议） | 产品 + 开发 | 已完成（见 cover-selection-plan.md） |
| **A2** | 冻结 **10 本**样本清单 JSON 路径 | 产品 | R0 前 |
| **A3** | 盲评导出：`scoreRankedTop3` + explain | 开发 | S0（≤1 人日） |
| **A4** | 跑 **R0** 基线表（A/B/C + 标签） | 产品/设计参评 | R0 |
| **A5** | **S1** 封面因子配置化 | 开发 | M1 前 |
| **A6** | 登记 `cover-selection-signoff.json` 模板 | QA | R0 后 |
| **A7** | hero 选型 backlog（不阻塞封面） | 产品 | 另排期 |

---

## 4. 对 PRD v0.1 的评审意见汇总（开发负责人书面意见）

| 类别 | 意见 | 评审会处理 |
|------|------|------------|
| 方向 | 封面+cull 前置，放弃时间序优化 | ✅ 采纳 |
| 指标双标 | 7/10 vs 60% | ✅ M1/M2 + proxy 分工 |
| top-3 定义 | coverCandidates ≠ 分数序 | ✅ scoreRankedTop3 |
| 常量调参 | 每轮改代码不可持续 | ✅ S1 配置化 |
| featured 回退 | 是否换 material 池 | ✅ 不回退 |
| 人像 demote | 缺自动策略 | ✅ 方案 A 40% |
| Studio 布局 | mobile/web 混评 | ✅ 主评 mobile |
| 通过线过严 | 一次 7/10 | ✅ M1 6/10 → M2 7/10 |

---

## 5. 风险登记（会后跟踪）

| 风险 | 缓解 |
|------|------|
| 人像为主样本 M1 不达标 | 方案 A + 单独 5/6 子指标 |
| featured 池质量差 | 导入/ cull 教育；不改池 |
| 评委主观不一致 | 双人 blind + 第三人对 C 类仲裁 |
| 调参过拟合 10 本 | M2 后加 3 本 hold-out 未参与调参 |

---

## 6. 下一步

1. 按 [cover-selection-plan.md](../cover-selection-plan.md) **v0.2** 执行 **R0**（只测不改）。  
2. S0/S1 与 R0 可并行，但 **R1 调参不得早于 S1 配置落地**（避免改常量发版）。  
3. R0 结论会议（30min）决定是否先动 cull 再动 R1。

---

## 7. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-04 | 封面选型 PRD 评审会纪要 |
