# Bookends Engine V1 · 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md) **v0.2.1**（实施母文档） |
| **ADR** | [adr/017-bookends-engine.md](./adr/017-bookends-engine.md) |
| **评审** | [acceptance-records/bookends-prd-review-2026-07-13.md](./acceptance-records/bookends-prd-review-2026-07-13.md) |
| **验收** | [ACCEPTANCE-BOOKENDS-ENGINE-V1.md](./ACCEPTANCE-BOOKENDS-ENGINE-V1.md)（待建；对齐 PRD §11） |
| **更新日期** | 2026-07-13 |

> **冲突裁决**：与 PRD / ADR 冲突时以 **PRD v0.2.1 + ADR-017** 为准。  
> **原则**：B1 禁止大搬家；B2a 先于 B2b；压字硬闸 B1 默认 off。

---

## 1. 范围门禁

| 做 | 不做（本 Phase） |
|----|------------------|
| `cover_engine.api` facade + Decision/锁 | B1 物理迁 `joint.py` |
| B2a：closing+pairing+唯一挂点+废除 cover 回退 | 完整 Admin |
| B2a：Colophon 无大图 DOM | 默认开 VL/MLLM |
| B2b：Studio「封面与封底」合页+级联 | 小程序书衣页 |
| 压字：B1 打标；B2a 硬闸 | Opening 五款重做 CSS |

---

## 2. 里程碑与预估

| Phase | 目标 | 预估 | 工程封板？ |
|-------|------|------|------------|
| **B0** | ADR（已）+ 本清单 + 金样 trip 列表 | 0.5d | — |
| **B1** | Opening facade + schema 锁 + 零回归 | 2–4d | 否（中间态） |
| **B2a** | Closing+Pairing+挂点+DOM+压字闸 | 3–5d | **是（主路径）** |
| **B2b** | Studio 面板 | 3–5d | 产品封板需要时 |
| **B3** | quiet / 实验室 / VL | 可选 | — |

---

## 3. 文件挂点

### 3.1 新增

| 文件 | 说明 | Phase |
|------|------|-------|
| `travelogue/cover_engine/api.py` | `resolve_opening` / `resolve_closing` / `resolve_bookends` / `repick_*` / `restore_auto` | B1→B2a |
| `travelogue/cover_engine/types.py` | 扩展 `BookendsDecision` / `BookendsLockState`（或并列文件） | B1 |
| `travelogue/cover_engine/lock.py` | 读写 `bookendsLock` 三字段同步 | B1 |
| `travelogue/cover_engine/closing/gate.py` | 候选闸口 | B2a |
| `travelogue/cover_engine/closing/scorer.py` | ClosingScorer v1 | B2a |
| `travelogue/cover_engine/pairing/policy.py` | PAIR-H* / S* | B2a |
| `travelogue/cover_engine/pairing/explain.py` | userOneLiner | B2a |
| `travelogue/cover_engine/opening/title_safe.py` | 压字标记 / 硬闸 | B1 标；B2a 闸 |
| `tests/unit/cover_engine/test_bookends_api_b1.py` | facade 零回归 | B1 |
| `tests/unit/cover_engine/test_bookends_closing_pairing.py` | H1/无图/挂点 | B2a |
| `tests/unit/cover_engine/test_bookends_lock.py` | 锁同步 | B1 |
| `docs/ACCEPTANCE-BOOKENDS-ENGINE-V1.md` | 验收追踪 | B1 起 |

### 3.2 修改

| 文件 | 变更 | Phase |
|------|------|-------|
| `travelogue/cover_engine/__init__.py` | 导出 api | B1 |
| `travelogue/curation/curate.py` | `sync_trip_covers` → `resolve_opening` | B1 |
| `travelogue/orchestrator/run.py` | layout 成功后调 `resolve_closing`（§4.5.1） | B2a |
| `travelogue/services/layout.py` | 若 curate 内 layout：返回后由 curate/orchestrator 调 closing（避免双调） | B2a |
| `travelogue/render/assemble.py` | 读持久 closing；缺键补算；显式 null 不重算；无图 Colophon | B2a |
| `travelogue/domain/closing_view.py` | thin re-export → api；删除 cover 回退成功路径 | B2a |
| `travelogue/render/cover_closing.py` | 委托 api | B2a |
| `travelogue/curation/moment_scoring.py` | 只 exclude，不写 closing | B2a |
| `schemas/trip.schema.json` | `bookendsLock` / `closingAssetId` null / explain… | B1 |
| `travelogue/config/*` | `bookends.*` 段 | B1 |
| `travelogue/web/serve.py` + handlers | `/api/trips/{id}/bookends*` | B2b（B1 可先不做 HTTP） |
| `travelogue/web/studio_entry.py` | 注入 bookends 摘要 | B2b |
| `templates/visual-journal/partials/cover-closing.hbs` | 无大图分支 | B2a |
| `templates/studio/preview-toolbar/*` | 「封面与封底」合页 | B2b |
| `tests/unit/domain/test_cover_closing.py` | 改写 cover 回退用例 | B2a |

### 3.3 明确不改（B1）

| 主题 | 原因 |
|------|------|
| `joint.py` 物理搬家 | R-BE-07 |
| Opening 五款 CSS | 非目标 |
| 默认 `opening_hard_gate=true` | R-BE-15 |

---

## 4. 任务拆解（可勾选）

### B0

- [x] ADR-017
- [x] 本 IMPLEMENTATION
- [x] 金样 trip 列表（V6 opening ≥3 + closing 相关 ≥3）记入 ACCEPTANCE
- [x] （并行）盲评旧 closing 导出脚本骨架（`scripts/bookends_closing_blind_export.py` + handbook）
- [x] DE-BE-01 成对正反例图例（`docs/acceptance-records/bookends-pair-examples-de-be-01.html`）
- [x] DE-BE-02 合页线框（`docs/wireframes/studio-bookends-panel-v1-wireframe.html`）

### B1 · Opening facade

- [x] **T-B1-01** `BookendsLockState` + lock sync helpers
- [x] **T-B1-02** `resolve_opening` 包装 `pick_cover_asset_id` / `pick_cover_style_and_asset` / `apply_joint_pick`
- [x] **T-B1-03** curate 改调 `resolve_opening`；行为金样 diff=0
- [x] **T-B1-04** schema：`bookendsLock`、`bookendsLocked`、可选 `closingAssetId`
- [x] **T-B1-05** config `bookends.*`；`opening_hard_gate=false`
- [x] **T-B1-06** title_safe **标记** API（不改 Top1）
- [x] **T-B1-07** re-export 兼容 + 单测
- [x] **T-B1-08** telemetry 壳（resolveOpeningMs）

**B1 DoD**：既有 V6 / cover_scoring_v2 相关 pytest 绿；无 AC-BE-14。

### B2a · Closing + 挂点（工程封板）

- [x] **T-B2A-01** `resolve_closing` + ClosingScorer + PAIR-H/S
- [x] **T-B2A-02** 废除 cover 回退；改写 `test_cover_closing*`
- [x] **T-B2A-03** orchestrator layout 末唯一主挂点（防双调）
- [x] **T-B2A-04** assemble：缺键补算 / 显式 null 跳过 / Colophon 无大图
- [x] **T-B2A-05** `opening_hard_gate` 默认 true + AC-BE-14 fixture
- [x] **T-B2A-06** moment exclude 只读接入
- [x] **T-B2A-07** dogfood ≥5 trip：degraded 率与无封面复用抽检（合成套件 `test_bookends_dogfood_b2a`；本地无真实 trip 目录）
- [x] **T-B2A-08** 建/更新 ACCEPTANCE 勾选 AC-BE-10..14、30..32

**B2a DoD**：工程封板；自动成书路径可用（自动化 AC）；合成 dogfood 已绿。

### B2b · Studio 面板（产品封板组件）

- [x] **T-B2B-01** HTTP bookends API（PRD §7.2）
- [x] **T-B2B-02** 合页预览 UI + 词表
- [x] **T-B2B-03** 换封面级联（R-BE-14）
- [x] **T-B2B-04** 换封底 + `closingUserPicked`
- [x] **T-B2B-05** 恢复自动挑选确认
- [x] **T-B2B-06** mobile 折叠说明
- [x] **T-B2B-07** AC-BE-20..25 半自动走查（`test_bookends_studio_ac_b2b`）；手工走查仍待真实 trip
- [x] **FE-BE-07** 低置信/弱收束状态条（`statusBanner` + `data-bookends-status`）
- [x] §14.3 错误码：`E_BOOKENDS_LOCKED` / `NO_CLOSING_CANDIDATE` / `LOW_CONFIDENCE`（payload/HTTP）
- [x] §6.6 `excludedByMoment` + moment soft warning（`bookendsSoftWarnings`）
- [x] 合页大图预览 + mobile 缩略 +「已固定」+ Top3 灰标 + pending 预览候选
- [x] 换版式经 bookends `repick-opening` 级联（R-BE-14 / FE-BE-05）

### B3（可选）

- [x] colophon-quiet CSS + `data-cover-closing` hook（`cover-closing.hbs` / `journal.css` / assemble）
- [ ] 实验室页
- [x] VL rerank 插件接口（默认 off；fail-open）

---

## 5. 测试命令（建议）

```bash
# B1
python -m pytest \
  tests/unit/curation/test_cover_styles_v6.py \
  tests/unit/curation/test_cover_styles_v6_joint.py \
  tests/unit/curation/test_cover_scoring_v2.py \
  tests/unit/cover_engine/test_bookends_api_b1.py \
  tests/unit/cover_engine/test_bookends_lock.py \
  -q

# B2a + B2b + B3 最小
python -m pytest \
  tests/unit/domain/test_cover_closing.py \
  tests/unit/cover_engine/ \
  tests/unit/web/test_studio_bookends_routes.py \
  -q
```

---

## 6. 风险与缓冲

| 风险 | 缓解 |
|------|------|
| curate 内 layout 与 orchestrator layout 双调 closing | IMPLEMENTATION 单入口函数 `maybe_resolve_closing_after_layout(trip)` |
| Studio 工期膨胀 | 工程封板不依赖 B2b |
| 压字闸误伤金样 | B2a 单独 PR；可配置回滚 `opening_hard_gate=false` |

---

## 7. 下一步（立即）

1. ~~DE-BE-01/02 · FE-BE-07 · 错误码 / excludedByMoment~~ 已完成  
2. Studio 手工走查 AC-BE-20..25（有真实 trip 时）  
3. 盲评：填 `bookends-closing-albums.json` → AC-BE-40..42，或签署 [产品封板 waiver](./acceptance-records/bookends-product-seal-waiver.md)  
4. （可选）B3 实验室页  
