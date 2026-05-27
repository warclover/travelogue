# PRD-EXPERIENCE · 附录 A · 精选上传（双文件夹）

| 属性 | 内容 |
|------|------|
| **主文档** | [PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) |
| **域** | L0 素材意图 · Agent 0 ingest · Agent 1 curate |
| **Epic** | E5（依赖 E2 Hybrid 最小包可选并行） |
| **ADR** | [003-experience-reading-modes.md](./adr/003-experience-reading-modes.md) · D4-1 去重 |
| **更新** | 2026-05-27 |

> 权威 **profile / 三模式 / 组合矩阵** 见主 PRD 与 [experience-matrix.yaml](./experience-matrix.yaml)。本文档只描述 `userTier` 与 ingest/curate。

---

## 1. 目的

用户通过 **主图上传（精选）** 与 **素材上传** 两个文件夹表达「我最满意的照片」；ingest 合并处理，curate 加权用于封面、章首 hero、Plate 屏与 present 精选放映。

---

## 2. 用户语义

| 文件夹 | `userTier` | 建议数量 | 说明 |
|--------|------------|----------|------|
| 主图上传 / 精选 | `featured` | **8–20 张** | 封面、章首、基调 |
| 素材上传 / 素材 | `material` | 其余 | 连拍、记录、补充 |

单目录上传 → 全部 `material`（与现版一致）。

### 2.1 目录布局

```
相册/
├── 主图上传/
└── 素材上传/
```

CLI（规划）：`--featured-dir` / `--material-dir`。

`config.yaml` 目录名映射：

```yaml
ingest:
  featured_dir_names: ["主图上传", "精选", "featured", "hero"]
  material_dir_names: ["素材上传", "素材", "material", "extras"]
  featured_priority_on_truncation: true
```

---

## 3. Ingest 规则（Agent 0）

1. 两源 **同一管线**：dedupe · WebP · layoutEligible  
2. 合并后按 `takenAt` 排序  
3. 同 `contentSig` 两文件夹都有 → **保留一条**，`userTier: featured`  
4. `max_photos`：先 featured 后 material 填充  
5. featured >30 张 → WARN（不硬拒）

### 3.1 Asset 字段

| 字段 | 值 |
|------|-----|
| `userTier` | `featured` \| `material` |
| `importSource` | `featured` \| `material` \| `legacy` |
| `userTierSource` | `ingest` \| `user`（G2 serve 升格） |

---

## 4. Curate 加权（Agent 1）

**原则**：乘性加权 `W_feat=1.35`；**不 bypass** layoutEligible / mediaClass。

| 决策点 | 规则 |
|--------|------|
| 封面 | `Pool_feat` 非空 → argmax `S_cover × W_feat` |
| 章首 hero | 章内 featured 优先；竖图 hero 不足 → fallback 素材 |
| coverCandidates | featured eligible≥2 → 至少 2/5 来自 featured |
| 章内首屏 | featured 优先入首屏主 slot |
| beam 开启 | featured 单图 +0.15；hero_separation 惩罚减半 |

配置：

```yaml
curate:
  featured_weight: 1.35
  featured_min_for_cover_pool: 2
  warn_featured_count_above: 30
```

### 4.1 与 Folio / Present 协同

| 能力 | 规则 |
|------|------|
| `screen-plate` | 优先 `userTier: featured` 或章 hero |
| `featured-grid` | 仅 featured；**正文 screens 排除同 asset**（ADR-003） |
| present `featuredOnly` | 仅放映 featured 屏；**保持原相对顺序** |

---

## 5. `curation` 汇总字段

```json
"curation": {
  "userTierSummary": { "featured": 12, "material": 219, "featuredInLayout": 11 },
  "featuredCoverPool": ["asset-003", "asset-012"],
  "featuredHeroByChapter": { "ch-01": "asset-003" }
}
```

---

## 6. 边界

| 情况 | 行为 |
|------|------|
| featured 全竖、web 要横封面 | fallback material；WARN |
| 无 featured | 与旧 trip bit-identical |
| structure_locked 后改 tier | 需 relayout 或 G1 解锁 |

---

## 7. 验收（附录 A）

| ID | 通过条件 |
|----|----------|
| AC-DF-01 | 双源 ingest；`userTierSummary` 正确 |
| AC-DF-02 | 封面 ∈ featured 且 `S_cover_eff` 最高 |
| AC-DF-03 | 章 hero ∈ 章内 featured（若 hero_score>0） |
| AC-DF-04 | 无 featured → 现版等价 |
| AC-DF-05 | 跨夹 dedupe → featured |
| AC-DF-06 | featured 全竖 → 封面 fallback + WARN |
| AC-DF-07 | schema 校验通过 |
| AC-DF-08 | 无 featured 回归 PASS |

→ 发布门禁映射 **AC-EXP-04、AC-EXP-05**。

---

## 8. Epic E5 任务

| 任务 | Owner |
|------|-------|
| ingest 子目录 / 双路径 | Agent 0 |
| `userTier` + 报告 | Agent 0 |
| cover/hero 加权 | Agent 1 |
| `userTierSummary` | Agent 1 |
| serve 升格 tier（可选） | G2 |

---

## 9. 实现锚点

`travelogue/media/ingest.py` · `curate_scoring.py` · `curate.py` · `screen_planner.py`

---

## 10. 开放问题（附录域）

1. 文件夹名是否固定中文 vs 仅 config 映射 → **config 映射**  
2. featured >50 硬拒 vs WARN → **WARN**（ADR 倾向）  
3. 章级子文件夹精选 → **本版否**
