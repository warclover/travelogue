# 架构决策记录（ADR）

| ID | 标题 | 状态 | 日期 |
|----|------|------|------|
| [001](./001-delivery-and-media.md) | 交付形态、媒体体积、视觉标签、状态机、封面 | 已采纳 | 2026-05-19 |
| [002](./002-smart-layout-v2-integration.md) | 智能排版 V2 融合（补强非替代、灰度、黄金样本） | 已采纳 | 2026-05-26 |
| [003](./003-experience-reading-modes.md) | 三阅读模式 · Hybrid · `export.reading.profile` · Epic E0–E8 | 已采纳 | 2026-05-27 |
| [004](./004-studio-hub-server.md) | Studio = `serve --studio` 单进程（v0.2 撤销双 Hub） | 已采纳 | 2026-05-27 |
| [005](./005-longshot-server-side.md) | 长图 P0/P1 fallback；scale=1；高度分段 | 已采纳 | 2026-05-27 |
| [006](./006-media-engines-integration.md) | 媒体引擎集成 | 已采纳 | — |
| [007](./007-native-clustering.md) | 原生聚类 | 已采纳 | — |
| [010](./010-tech-debt-sprint.md) | Phase 5 后架构还债：handlers、AppContext、render 分层 | 已采纳 | 2026-05-30 |
| [011](./011-import-strategy.md) | 延迟 import 策略（循环依赖 / 热循环） | 已采纳 | 2026-05-30 |
| [012](./012-semantic-tagging-p8-p12-split.md) | L1 语义：Phase 8 归档 · Phase 12 权威实施 | 已采纳 | 2026-06-06 |
| [013](./013-layout-strategy-approval-semantics.md) | LSE L2 审批语义：operator + ≥2 approvers（非字面双人） | 已采纳 | 2026-06-07 |
| [008](./008-trip-storage-boundaries.md) | trip.json 存储边界 · Document/Blob 分离约定 | **Accepted** | 2026-06-11 |

新建 ADR 请使用 `00N-简短英文名.md`，并在本表登记。
