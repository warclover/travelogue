# ADR-017 · Bookends Engine（封面–封底引擎）

| 属性 | 内容 |
|------|------|
| **状态** | **Accepted**（与 PRD v0.2.1 对齐；实施按 B1→B2a→B2b） |
| **日期** | 2026-07-13 |
| **决策者** | 开发负责人（执行决议已写入 PRD v0.2.1） |
| **影响范围** | `travelogue/cover_engine/`、`curation/curate.py`、`orchestrator/run.py`、`services/layout.py`、`render/assemble.py`、`domain/closing_view.py`、`schemas/trip.schema.json`、Studio handlers / preview-toolbar |
| **关联** | [PRD-BOOKENDS-ENGINE-V1.md](../PRD-BOOKENDS-ENGINE-V1.md) v0.2.1 · [PRD-COVER-STYLES-V6.md](../PRD-COVER-STYLES-V6.md) · [IMPLEMENTATION-BOOKENDS-ENGINE-V1.md](../IMPLEMENTATION-BOOKENDS-ENGINE-V1.md) · [acceptance-records/bookends-prd-review-2026-07-13.md](../acceptance-records/bookends-prd-review-2026-07-13.md) |

---

## 背景

1. V6 已交付 Opening 五款皮肤 + 图×样式联合选型（`cover_engine`），但封底仍在 `domain/closing_view.py` 独立启发式，且可在无候选时 **回退复用封面**。
2. 跨职能评审要求：成对约束、两阶段解析、锁字段唯一、Studio 级联；开发评审进一步要求 **唯一挂点**、**锁粒度**、**压字闸分期**、**B2a/B2b 拆分**。
3. 现网 `run_trip`：`curate`（常内嵌 layout）→ `layout` stage → `narrate` → `render/assemble`（此处调用 `resolve_closing_asset_id`）。若在 curate 持久化 closing，则 `unused_*` 因子无 screens 可用。

---

## 决策

### D1 · 扩展 `cover_engine`，不新建平行包

Bookends API 落在 `travelogue/cover_engine/api.py`。B1 仅 facade 包装现网 `pick_cover_*` / `joint`；B2a 增加 `closing/` + `pairing/`。

### D2 · 两阶段 + Closing 唯一挂点（PRD §4.5.1）

```text
# Opening — curate
resolve_opening(trip, layout, force=...) -> apply opening fields + bookendsLock.opening?

# After screens exist — ONLY:
#   A) orchestrator layout stage end (preferred for run_trip)
#   B) assemble before cover-closing IF key missing AND not lock.closing
# Studio preview: read-only / ephemeral resolve (no write by default)

if should_resolve_closing(trip, layout):
    if "closingAssetId" not in curation and not lock.closing:
        decide = resolve_closing(trip, layout=...)
        apply_closing(trip, decide)  # may set null
    elif curation.get("closingAssetId") is None and "closingAssetId" in curation:
        # explicit no-hero; do not recompute
        pass
```

**禁止**：curate 无 screens 写最终 closing；`moment_scoring` 持久化 closing。

### D3 · 锁模型

```json
"curation": {
  "bookendsLock": { "opening": true, "closing": false },
  "bookendsLocked": false,
  "coverJointLocked": true
}
```

- 写路径维护三者一致：`coverJointLocked == bookendsLock.opening`；`bookendsLocked == opening && closing`。
- 读路径：优先 `bookendsLock`；仅有旧 `coverJointLocked` 时回填 `opening`。

### D4 · 极小册与 DOM

- 无合法封底候选 → `closingAssetId: null`，`degraded: true`，**禁止**复用封面。
- 渲染：**保留 Colophon 文案，去掉封底大图**，预览弱提示。

### D5 · 压字硬闸分期

- B1：`bookends.title_safe.opening_hard_gate=false`（可打标，不改 Top1）。
- B2a：默认 `true`；AC-BE-14 生效。

### D6 · 交付拆分与封板

- **B2a**：引擎 + 挂点（自动成书价值）。
- **B2b**：Studio 合页面板。
- **工程封板** = B1+B2a 自动化 AC；**产品封板** = +B2b + 盲评或 waiver。

### D7 · 故意行为变更

废除 `_resolve_closing_allow_cover` 成功路径；改写对应单测。NFR fail-open 不得恢复「回退封面」。

---

## 后果

| 正面 | 代价 |
|------|------|
| 与 layout 信号一致；可升级 ClosingScorer | assemble 仍需「缺字段补算」分支 |
| V6 joint 锁兼容 | 三字段同步逻辑需单测 |
| B1 零回归可达成 | 压字改善延后到 B2a |
| 自动成书先受益 | Studio 面板可后置 |

---

## 不决定

- Opening quality v3 特征重做、mobile 竖版五皮肤、Admin CMS、默认开 VL。

---

## 合规检查清单（实施）

- [x] layout 末 / curate-内 layout 后只一处主写入 closing（`maybe_resolve_closing_after_layout`）  
- [x] 显式 `null` 与缺键区分  
- [x] `bookendsLock` 三字段同步  
- [x] cover 回退单测已改写  
- [x] B1 CI 不含「压字改 Top1」断言  
