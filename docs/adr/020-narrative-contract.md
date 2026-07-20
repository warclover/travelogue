# ADR-020 · Narrative Contract（三模式叙事合同）

| 属性 | 内容 |
|------|------|
| **状态** | **Accepted**（字段合同冻结；longshot 渲染改写见实现清单 B2） |
| **日期** | 2026-07-20 |
| **决策者** | 产品 + 架构（依据 [PRD-LAYOUT-TRUST-NARRATIVE-V1](../PRD-LAYOUT-TRUST-NARRATIVE-V1.md) §6 / 峰会 D4） |
| **影响范围** | `schemas/trip.schema.json` · `layoutScreen`、`travelogue/layout_contract/narrative_contract.py`、curate/planner 默认推导、longshot 渲染（B2）、present 章界（B4） |
| **关联** | [PRD-LAYOUT-TRUST-NARRATIVE-V1](../PRD-LAYOUT-TRUST-NARRATIVE-V1.md) · [ADR-003](./003-experience-reading-modes.md)（修订 D2 长图行）· [ADR-016](./016-longshot-platform-export.md) · LTN B3 双预览（已提前） |
| **验收** | AC-B-01（本 ADR 入库）；AC-B-02/04 随 B2；AC-B-03 已由 B3 覆盖 |

---

## 背景

1. 三阅读模式（scroll / present / longshot）共用 `chapters[].screens[]`，但 [ADR-003 D2](./003-experience-reading-modes.md) 规定 longshot **按 slot 展平**，把 mosaic 组边界抹成一串单卡——网页满意、微信长图「不是同一部作品」（LTN-P-02）。
2. 这是**合同行为**而非实现 bug；修体验必须先冻结 Narrative Contract，再改 longshot 渲染（R-B2）。
3. `layoutScreen` 现有 `patternId` / `slots` / `role`(P23 peak) / `breathLabel` 等，**没有**组感字段；schema `additionalProperties: false`，须显式扩字段（H1）。

---

## 决策

### D1 · Canonical SSOT

`trip.chapters[].screens[]` 仍是唯一屏序与叙事合同源。  
scroll / present / longshot = **同一合同的三种 View**：允许像素密度与版式不同，**禁止无提示地抹掉组边界**。

### D2 · 字段最小集（均可选；缺失可推导）

挂在 `layoutScreen`（与现有 `role` **并存且语义分离**）：

| 字段 | 类型 | 含义 |
|------|------|------|
| `narrativeRole` | enum | 版式叙事角色（见 D3） |
| `groupId` | string | 连作 / 拼图组 ID；默认同 `screenId`（一屏一组） |
| `preserveGroup` | boolean | 导出/长图是否保持组感 |
| `exportHints` | object | 表面提示（不得与 `preserveGroup` 静默冲突） |
| `representativeAssetId` | string | 组代表作（折叠 / 徽标 / present 缩略） |

**边界**：

- 现有 `screen.role` ∈ `{moment, peak}` = P23 peak pool，**不是** `narrativeRole`。
- 资产侧 `burstGroupId` = 连拍检测信号，**不**替代 `groupId`。

### D3 · `narrativeRole` 枚举（可迭代）

| 值 | 典型 pattern |
|----|----------------|
| `plate` | 单图/常规板式默认 |
| `hero_single` | `*-1` / `full-frame` 强调单图 |
| `stack` | `portrait-3` 等竖向叠 |
| `pair` | `portrait-2` / `landscape-2` / `portrait-2-landscape-2` |
| `mosaic_hero` | 含 `main` 角色的 mosaic |
| `mosaic_flat` | 无 main 的 mosaic / 等权 dense |
| `breath` | `screen-breath-pause` |

未识别 pattern → `plate`。枚举可加值，**禁止**静默改已持久化值的含义。

### D4 · 默认值与迁移（不强制重 curate）

应用层 `ensure_narrative_contract(screen)`（见实现）：

| 字段 | 默认推导 |
|------|----------|
| `preserveGroup` | `patternId` 含 `mosaic` **或** 模板声明 main 角色 → `true`；breath / 单槽 → `false` |
| `narrativeRole` | 按 D3 表从 `patternId` + slots 推导 |
| `groupId` | 缺省 = `screenId` |
| `representativeAssetId` | main 槽 asset → 否则首槽 asset；无槽则省略 |
| `exportHints` | 缺省 `{}`；若 `preserveGroup=true` 则不得含 `longshotMode=flatten`（冲突 → 丢弃该 hint 并记日志，B2 落地） |

**迁移**：旧 trip 缺字段时**读时/写时推导**即可，不要求用户重新 curate。显式写入的字段优先于推导。

### D5 · 修订 ADR-003 D2 长图行（合同层）

| 模式 | ADR-003 原文 | 本 ADR 修订 |
|------|----------------|-------------|
| longshot | screens 按 slot 展平 | **默认尊重 `preserveGroup`**；仅当显式 `preserveGroup=false` 时允许按 slot 拆屏 |

窄幅（~428px）**三级降级**（R-B2 实施，本 ADR 冻结语义）：

1. **保组换排**（竖向组排 + 组标记）— 默认  
2. **代表图 + N**（`representativeAssetId` + 徽标）  
3. **拆屏** — 仅显式 `preserveGroup=false`（AC-B-04：打日志）

B2 可另开实施 PR / 补充 ADR 细节，但不得回退到「mosaic 无提示 flatten」。

### D6 · `exportHints` 冲突规则

- 权威布尔：`preserveGroup`。  
- `exportHints.longshotMode` 建议枚举：`preserve_stack` \| `representative_badge` \| `flatten`。  
- `preserveGroup=true` 且 hint 要求 `flatten` → **fail-loud 或丢弃 hint + 日志**，禁止静默拆组。  
- `preserveGroup=false` 仅显式场景（用户/策略写入），自动推导不得主动写 `false` 去「优化长度」。

### D7 · 非目标（本 ADR / B1）

- 不实现 longshot 三级降级渲染（→ **B2**）。  
- 不实现双预览（→ **B3**，已提前交付）。  
- 不改 present `chapter-separator` 选择器（→ **B4**）。  
- 不改 ADR-016 平台切分算法内核（边界输入改为「组」后由 B2 对接）。

---

## 后果

**正面**

- 三模式共享可检验的组感合同；B2/B4 有锚点。  
- 旧 trip 可渐进获得字段，无需强制重跑。

**负面 / 成本**

- schema 扩字段；golden / longshot「一卡一 slot」断言将在 B2 改为组守恒。  
- 保组会使部分长图变长 → 双预览（B3）诚实展示；允许显式 `false`。

---

## 实现清单

### B1（本 ADR 同期）

- [x] 本文件入库 + [README](./README.md) 登记  
- [x] `schemas/trip.schema.json` · `layoutScreen` 五字段  
- [x] `travelogue/layout_contract/narrative_contract.py` · `ensure_narrative_contract`  
- [x] planner `append_screen` 写入时推导  
- [x] 单测：默认 mosaic → `preserveGroup=true`；显式值不被覆盖  

### B2（已落地 · 2026-07-20）

- [x] `screens_to_longshot_items` + `resolve_chapter_items_for_render`  
- [x] 窄幅三级降级（preserve-stack media-row / representative badge / 显式 flatten）  
- [x] `preserveGroup=false` 日志（AC-B-04）  
- [ ] dogfood AC-B-02（人工目视）  

### B4（已落地 · 2026-07-20）

- [x] present `AUX_SELECTOR` 含 `chapter-separator`（`skipAuxBlocks` 仍可关）  

---

## 修订 ADR-003 的阅读指引

阅读 [ADR-003](./003-experience-reading-modes.md) D2 长图行时，以 **本 ADR D5** 为准：  
「按 slot 展平」降级为**显式拆组选项**，不再是 mosaic 的隐含默认。
