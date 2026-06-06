# ADR-012 · L1 语义标签：Phase 8 与 Phase 12 职责划分

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳 |
| **日期** | 2026-06-06 |
| **决策者** | 工程 / 文档对账 |
| **关联** | [PRD-PHASE8-photo-semantic-clustering.md](../PRD-PHASE8-photo-semantic-clustering.md) · [PRD-PHASE12.md](../PRD-PHASE12.md) · [PRD-PHASE9.md](../PRD-PHASE9.md) |

---

## 背景

- **Phase 8 PRD** 规划 11 类 L1 CLIP 标签 + 类内 HDBSCAN L2 子簇 + layout 集成 + Studio 标签 UI（W1–W6）。
- **Phase 12 PRD** 在 P9/P10 基线上复核后，将 **L1 语义映射** 与 **`category_coherence`** 纳入 W1/W2，并 **暂缓 L2 子簇** 与 **Studio 标签 UI**。

两文档并行存在时，实施者无法判断「谁拥有 L1 语义」与 Phase 8 是否仍应启动。

---

## 决策

1. **L1 11 类语义映射（asset `semanticTag.category` 或等价字段）**  
   - **权威实施阶段：Phase 12**（P12-W1/W2）。  
   - Phase 8 PRD 中 W1/W4 关于 L1 与 layout 集成的描述 **视为 Phase 12 子集**，不在 Phase 8 独立立项重复开发。

2. **L2 类内 HDBSCAN 子簇**  
   - **暂缓**（Phase 12 已拍板；个人开发者周期风险）。  
   - Phase 8 全文档 **降级为规划归档**：保留 11 类 taxonomy 参考，**不**作为近期里程碑。

3. **Studio 标签浏览 / override UI**  
   - **不纳入** P9/P12 零打扰原则；若未来做，**另立 PRD**（非 Phase 8 W5 默认范围）。

4. **`category_coherence` 与排版消费**  
   - **Phase 12 W2** 交付；与 Phase 8 §5 排版集成 **合并为同一实现路径**。

5. **Phase 8 文档状态**  
   - [PRD-PHASE8-photo-semantic-clustering.md](../PRD-PHASE8-photo-semantic-clustering.md) 标注 **Superseded by ADR-012 + Phase 12**（索引仍保留 taxonomy 与架构说明）。

---

## 后果

| 正面 | 负面 / 缓解 |
|------|-------------|
| 单轨实施，避免双 PRD 重复任务 | Phase 8 读者需读 ADR 理解归档原因 |
| P12 IMPLEMENTATION 为 L1/coherence 唯一任务清单 | L2 子簇能力延后，food grid 等仍用 subjectClass 桥接 |
| README / 新人路径以 Phase 9 → 10 → 12 为准 | 若将来恢复 L2，需新 ADR 或 Phase 8.1 PRD |

---

## 验收指针

- L1 / coherence：** [IMPLEMENTATION-PHASE12.md](../IMPLEMENTATION-PHASE12.md)** · [ACCEPTANCE-PHASE12.md](../ACCEPTANCE-PHASE12.md)（若存在）。
- 语义 taxonomy 参考：Phase 8 PRD §2 11 大类表（只读）。
