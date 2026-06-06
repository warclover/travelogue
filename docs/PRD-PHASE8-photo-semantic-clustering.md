# Travelogue · Phase 8 产品需求文档（PRD · 照片语义聚类）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.8.0-PHASE8 |
| **状态** | Draft · **Superseded by [ADR-012](./adr/012-semantic-tagging-p8-p12-split.md) + Phase 12**（taxonomy 只读参考） |
| **Phase 8 代号** | 「语义标签与类内聚类」— 11 大类 L1 + HDBSCAN L2 |
| **前置条件** | [PRD-PHASE9.md](./PRD-PHASE9.md) Quality Gate 已上线；Phase 3 CLIP embed 可用 |
| **规划来源** | `proud-dancing-haven.md` |
| **更新日期** | 2026-06-02 |

> **定位**：将 CLIP 8 类粗标签升级为 **11 个可解释大类**，并在 **类内** 发现 3–5 个语义子簇，为智能排版 V2 的 `subject_run`、`category_coherence`、章 pattern 提供精细输入。  
> **与 Phase 3 `sceneClusterId` 分工**：sceneCluster 为 **无标签视觉相似**；Phase 8 为 **有标签语义类 + 类内子类**（见 PRD-PHASE3 §4.7）。

---

## 1. 背景

| 问题 | 说明 |
|------|------|
| 粒度太粗 | `landscape` 混合山川/海洋/日落 |
| 标签扁平 | heuristic tags 与 subjectClass 无层级 |
| 子类缺失 | 全局 HDBSCAN 淹没「山景 vs 海景」差异 |

---

## 2. 11 大类（L1）

| ID | 大类 | 概括 | 旧 8 类映射 |
|----|------|------|-------------|
| scenery | 风光/自然景观 | 山水林田湖草沙、天象 | landscape |
| portrait | 人像 | 自己与同伴 | person |
| architecture | 建筑/人文景观 | 古今建筑、街巷古镇 | architecture, street |
| food | 美食/餐饮 | 吃到、看到、市场 | food |
| animal | 动物 | 野生动植物、宠物 | **新增** |
| transport | 交通/出行 | 交通工具与沿途 | **新增** |
| culture | 文化/活动 | 节庆、演出、展览 | temple 扩展 |
| plant | 植物/园艺 | 花卉、草原 | **新增** |
| night | 夜景/光影 | 夜间与特殊光线 | **新增** |
| signage | 文字/标识/纪念 | 路牌、门票、纪念品 | **新增** |
| detail | 生活细节/氛围 | 住宿、休闲、氛围 | indoor, mixed |

**向后兼容**：`legacy_class_from_category()` 映射回旧 `subjectClass` 8 类。

---

## 3. 架构

```text
单次 CLIP forward（G-P3-C05）
  → embedding（sceneCluster 用）
  → L1 11 类 logits → semanticTag.category

每 L1 桶内（≥15 张）
  → HDBSCAN → L2 子簇 semanticTag.subClusterId
  → 命名：LLM 2–4 字（失败则模板「风光·变体1」）

叠加：timeContext · locationContext（GPS/城市）
```

**聚类能否覆盖 11 大类？**  
- **不能**靠全局 HDBSCAN 直接产出 11 类。  
- **能**靠 CLIP 零样本 L1 + **类内** HDBSCAN L2。

---

## 4. 数据模型（摘要）

| 字段 | 说明 |
|------|------|
| `semanticTag.category` | L1 枚举 |
| `semanticTag.subClusterId` | L2 |
| `semanticTag.label` | 人读标签 |
| `semanticTag.timeContext` | 早晨/白天/傍晚/夜景 |
| `semanticTag.locationContext` | 城市或 GPS 网格 |
| `curation.semanticClustering` | 批摘要 |

完整 schema 见实施波次 W1。

---

## 5. 排版集成（W4）

| 项 | 说明 |
|----|------|
| `category_coherence` | layout_scoring 新维度 · 同屏同类奖励 |
| `arc_pattern_bonus` | 类目感知 peak（风光多图 / 人像 grid） |
| `subject_run` | 4 桶 → 11 类 |

---

## 6. Studio UI（W5 · 可选延后）

| 功能 | 说明 |
|------|------|
| `GET /__travelogue/tags` | 分类摘要 |
| `POST /__travelogue/tags/override` | 用户修正 |
| 分类浏览面板 | 左栏类目 + 网格 + 子簇 tab |

**与 Phase 9 关系**：Phase 9 **不展示被筛图**；Phase 8 UI 仅浏览 **layoutEligible** 资产。

---

## 7. 实施波次

| 波次 | 交付 |
|------|------|
| W1 | schema + L1 11 类 CLIP |
| W2 | 类内 HDBSCAN + 命名 |
| W3 | 时间/位置叠加 |
| W4 | layout_scoring / arc |
| W5 | Studio 标签 UI |
| W6 | 性能与验收 |

**性能预算**（200 张）：L1 复用 embed + HDBSCAN ≤3s 增量。

---

## 8. 关键文件（规划）

`clip_encoder.py` · `semantic_clusters.py`（新）· `semantic_labels.py`（新）· `layout_scoring.py` · `trip.schema.json`

---

## 9. 文档拆分建议

Phase 8 实施时可再拆：

- PRD-PHASE8-A-semantic-taxonomy.md（11 类与 prompt）
- PRD-PHASE8-B-subclustering.md
- PRD-PHASE8-C-layout-integration.md
- PRD-PHASE8-D-studio-tags-ui.md

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.8.0 | 2026-06-02 | 自 planning doc 升格索引 PRD |
