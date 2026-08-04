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
| [014](./014-mosaic-proximity-window-order.md) | 拼图连拍门槛 `mixed_proximity_seconds` 与 MCS `window_order` 默认值 | **Draft · LRG-W1** | 2026-07-05 |
| [015](./015-lse-planner-migration.md) | LSE 与 Screen Planner 两步渐进迁移（supersede R-P17-04 / ADR-010 D5 部分） | **Accepted** | 2026-07-08 |
| [016](./016-longshot-platform-export.md) | 平台化长图导出：三分支 Pipeline · full capture 切分 · 禁 P1 · 原子 Job | **Accepted** | 2026-07-08 |
| [017](./017-bookends-engine.md) | Bookends Engine：两阶段挂点 · 锁粒度 · 压字分期 · B2a/B2b · 禁封面回退 | **Accepted** | 2026-07-13 |
| [018](./018-desktop-installer-layout.md) | 桌面可安装版：onedir · 资源/数据根 · portable.flag · 单实例退出 · frozen worker · 长图自动轨 2 | **Accepted** | 2026-07-14 |
| [019](./019-desktop-user-data-llm-secrets.md) | Desktop LLM secrets（复用 ADR-018 `user_data_dir` · L0/L1） | **Accepted** | 2026-07-15 |
| [020](./020-narrative-contract.md) | Narrative Contract：三模式组感字段 · 修订 ADR-003 longshot 展平默认 | **Accepted** | 2026-07-20 |
| [021](./021-export-compose-dual-engine.md) | 导出双引擎：Slice 叙事切片 + Compose 固定画布（A4 / 3:4 / 2.8:1）· Studio 下线九宫格 | **Accepted** | 2026-08-04 |

新建 ADR 请使用 `00N-简短英文名.md`，并在本表登记。
