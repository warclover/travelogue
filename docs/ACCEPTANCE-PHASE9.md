# Travelogue · Phase 9 验收标准

> **单轨入口建议**：[ACCEPTANCE.md](./ACCEPTANCE.md)

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE9.md](./PRD-PHASE9.md) v0.9.1 及 P9-A～E |
| **关联实施** | [IMPLEMENTATION-PHASE9.md](./IMPLEMENTATION-PHASE9.md) · 里程碑 **M30** |
| **前置验收** | Phase 7 ingest 基线已登记；Phase 2 Studio Job 可用 |
| **代号** | P9-QualityGate |
| **更新日期** | 2026-06-02 |
| **W1 状态** | **Done**（G-P9-W1 已闭合 · 2026-06-02） |

---

## 1. 验收环境与档位

### 1.1 通用

- `pip install -e ".[dev]"`（W1 · P0 路径）
- W2 验收另需 `pip install -e ".[dev,vision]"` + pyiqa 可用环境
- 启动：`python -m travelogue studio` 或 CLI ingest

### 1.2 发布波次

| 波次 | 范围 | 门禁 |
|------|------|------|
| **M30-W1** | P0 rules cull + UX + layoutEligible 统一 | **本文件 §2–§5 必过** |
| **M30-W2** | P1 ml（可选发版） | §6 追加 |
| **M30-W3** | subject 桥接 | §7 追加 |

**默认发版**：W1 独立发布（`cull.mode=rules`）；W2 不阻塞 W1 上线。

---

## 2. 功能验收（W1 · 必过）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-P9-01** | `layout_eligible_assets()` 排除 `layoutEligible=false`（含 cull） | `tests/test_photo_cull.py` |
| **AC-P9-02** | mao fixture：非 featured 保留率 ≥ 0.80 × N_scan，或 Pass 1–2 后池已 &lt; floor 且 Pass 3 跳过（见 P9-A §3.4） | fixture + 登记 |
| **AC-P9-03** | 双文件夹 fixture：featured **100%** eligible | pytest |
| **AC-P9-04** | featured 低清仍 eligible；可选 `quality.lowResSuspected` | pytest |
| **AC-P9-05** | `cull.enabled=false` 行为等同 Phase 7（±新字段缺失） | pytest |
| **AC-P9-06** | ingest 结束 `curation.cullSummary` 存在 | trip.json |
| **AC-P9-07** | clustering 不对 culled 资产 embed | pytest / mock |
| **AC-P9-08** | 增量 ingest：**全 trip re-cull** | pytest |
| **AC-P9-09** | cull 异常 fail-open：Job 成功 + 全员 eligible + `cullSummary.error` | pytest |
| **AC-P9-10** | 被筛 asset 仍保留 source/WebP 文件 | `tests/test_photo_cull.py::test_culled_assets_retain_source_files` |

---

## 3. UX 验收（W1）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-P9-UX-01** | Importing 无新 route/modal | 人工 / Playwright |
| **AC-P9-UX-02** | Job 成功 toast **第二行**展示 `cullUserLine` | Playwright |
| **AC-P9-UX-03** | DOM 无被筛图入口 | Playwright |
| **AC-P9-UX-04** | `maxPhotosExceeded` WARN 非阻断 | pytest + Playwright |
| **AC-P9-UX-05** | cull 失败 Job 仍 success + 无 cullUserLine | Playwright · pytest |
| **AC-P9-UX-06** | compact 390px toast 不溢出 | Playwright |
| **AC-P9-UX-文案** | 用户可见文案用「挑选/不参与排版」 | ingest_report · asset_quality |

---

## 4. 非回归（NR-P9）

| ID | 条件 |
|----|------|
| **NR-P9-01** | `clustering.enabled=false` + `cull.enabled=true` → curate smoke 通过 |
| **NR-P9-02** | `travelogue demo verify` 通过 |
| **NR-P9-03** | schema validate 含 cull 字段 fixture |
| **NR-P9-04** | **cull-on 为新 golden 基线**：mao/maomi 人工签 off 一次（不要求与 cull-off bitwise 一致） |

---

## 5. W1 发布闸门（G-P9-W1）

全部满足方可标记 W1 Done：

1. §2 AC-P9-01～10 自动化绿  
2. §3 AC-P9-UX-01～03 绿  
3. NR-P9-01～03 绿  
4. NR-P9-04 登记（`docs/acceptance-records/` 或 PR 说明）  
5. [PRD-EXPERIENCE-附录A](./PRD-EXPERIENCE-附录A-精选上传.md) §3.2 修订已合并  

**签核记录**（2026-06-02）：`docs/acceptance-records/phase9-quality-gate.json` · `phase9-golden-cull-signoff.json` · mao/maomi.md Phase 9 小节。

---

## 5.1 P12 指标扩展（兼容口径）

> Phase 12 在不改变 P9 发布闸门的前提下，扩展了 cull telemetry 字段。  
> 本节用于固定「实现字段名 ↔ 验收产物字段名」映射，避免口径漂移。

### 运行时字段（trip / ingest）

| 维度 | 运行时字段 |
|------|------------|
| L1 回退率 | `trip.curation.cullSummary.mlFallbackRateL1` |
| L2 回退率 | `trip.curation.cullSummary.branchFallbackRateL2` |
| L2 回退分因 | `trip.curation.cullSummary.branchFallbackByReasonL2` |
| L3 回退率 | `trip.curation.cullSummary.failOpenRateL3` |
| 分支覆盖率 | `trip.curation.cullSummary.branchPortraitRatio` / `branchLandscapeRatio` / `branchGrayRatio` |
| cull CPU 时延 | `trip.curation.cullSummary.cpuMs` |
| ingest 透传（L1/L2/L3） | `ingest_stats.cull_l1_ml_fallback_rate` / `cull_l2_branch_fallback_rate` / `cull_l3_fail_open_rate` |
| ingest 透传（L2 分因） | `ingest_stats.cull_l2_<reason>`（如 `cull_l2_gray_zone`） |

### 验收汇总字段（baseline）

| 聚合维度 | `docs/acceptance-records/phase9-eval-baseline.json` |
|----------|-----------------------------------------------------|
| L1 回退 | `l1_ml_fallback_rate.avg/max` |
| L2 回退 | `l2_branch_fallback_rate.avg/max` |
| L2 分因 | `l2_branch_fallback_by_reason` |
| L3 回退 | `l3_fail_open_rate.avg/max` |

### 生成命令（P12 兼容）

```bash
python scripts/phase9_golden_cull_signoff.py --all --write docs/acceptance-records/phase9-golden-cull-signoff.json
python scripts/phase9_eval_baseline.py --golden docs/acceptance-records/phase9-golden-cull-signoff.json --quality docs/acceptance-records/phase9-quality-gate.json --write docs/acceptance-records/phase9-eval-baseline.json
```

---

## 6. W2 追加验收（P1 ML · 可选）

| ID | 条件 |
|----|------|
| **AC-P9-ML-01** | pyiqa 缺失 → 自动 P0，不抛错 |
| **AC-P9-ML-02** | 同 fixture 保留率 ≥ P0 − 2% |
| **AC-P9-ML-03** | `cull.mode=auto` 无 GPU → rules |
| **AC-P9-ML-04** | 250 张 GPU aesthetic 增量 ≤ 90s（S2 登记） |

---

## 7. W3 追加验收（桥接）

| ID | 条件 |
|----|------|
| **AC-P9-E-01** | `subjectClass=food` → bucket `food` |
| **AC-P9-E-02** | CLIP 优先于冲突 tags |
| **AC-P9-E-03** | 无 subjectClass 时与现网 identical |

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.3 | 2026-06-03 | 新增 P12 指标扩展口径：L1/L2/L3 telemetry 字段映射与 baseline 聚合字段 |
| v0.9.2 | 2026-06-02 | G-P9-W1 闭合 · NR-P9-04 mao/maomi signed_off |
| v0.9.1 | 2026-06-02 | Kickoff 修订：W1 独立发版 · NR-P9-04 golden |
