# Phase 9 · W1 PR 备忘录

| 属性 | 内容 |
|------|------|
| **分支** | `feat/phase9-quality-gate-w1` |
| **基准** | `master` |
| **远程** | https://github.com/warclover/travelogue.git |
| **创建 PR** | https://github.com/warclover/travelogue/compare/master...feat/phase9-quality-gate-w1?expand=1 |
| **W1 状态** | Done（G-P9-W1 已闭合） |
| **更新** | 2026-06-02 |

> **范围说明**：本 PR / Phase 9 **不包含** [PRD-PHASE10](../PRD-PHASE10-food-grid.md) food grid 实现；W3 subject 桥接仅为 Phase 10 铺路。

---

## PR 标题

```
feat(phase9): Quality Gate W1 — rules cull, Studio UX, golden signoff
```

---

## PR 正文（可直接粘贴）

## Summary

Phase 9 **Quality Gate (M30-W1)** — ingest-time photo cull with `cull.mode=rules` default, unified `layoutEligible` pool, Studio success toast second line (`cullUserLine`), and golden album signoff (mao/maomi).

**Out of scope:** Phase 10 food grid, CLI `travelogue cull`, `exposure_extreme` implementation (spike doc only).

### Core

- **`photo_cull.py`**: Pass 1–4, fail-open, `cullSummary` / schema fields
- **Pass 2 fix (PRD §4.1)**: skip duplicate cull on material-only groups — fixes mao golden regression (1 → 24 eligible)
- **`photo_cull_ml.py`**: pyiqa path with degrade-to-rules (W2, non-blocking)
- **`subject_tagging.py`**: W3 CLIP `subjectClass` bridge (unlocks Phase 10 planning only)
- **Ingest**: full-trip re-cull in `_finalize_ingest_assets`; cull stageHint + merged import progress copy
- **Studio**: `cullUserLine` / `cullWarn` on v1 + v2 success paths; bento shelf/preview + phone frame sync

### Docs & acceptance

- PRD P9-A～E, IMPLEMENTATION / ACCEPTANCE-PHASE9
- NR-P9-04: `phase9-golden-cull-signoff.json` (mao 24/29, maomi cull 27/33)
- `phase9-quality-gate.json`: **W1 Done**, full AC/NR index
- W2 ML script: `scripts/phase9_ml_acceptance.py` (skipped on CI without pyiqa)

## Commits (5)

| Commit | Description |
|--------|-------------|
| `1bc9c20` | W1 core: cull + Studio UX + PRD + tests |
| `7abf0be` | W2 UX hints, maxPhotos WARN, exposure spike |
| `39de26a` | Gap-fill: AC-P9-02/UX-05/06 tests, gate index, copy |
| `3850bbf` | Studio: v2 phone frame ↔ web carousel sync |
| `0068902` | W2 ML acceptance script (GPU skip gate) |

## Test plan

- [x] `pytest tests/test_photo_cull.py tests/test_photo_cull_ml.py tests/test_trip_schema_cull.py tests/test_subject_tagging_bridge.py tests/test_studio_phase9_cull_playwright.py tests/test_asset_quality.py` — **47+ passed**
- [x] `python -m travelogue demo verify` — OK
- [x] NR-P9-04 golden signoff (local albums mao/maomi)
- [ ] Optional manual: Studio import → toast 第二行 `经挑选 N 张进入排版`
- [ ] W2 GPU (follow-up, non-blocking): `pip install -e ".[cull-ml]"` + `python scripts/phase9_ml_acceptance.py --write docs/acceptance-records/phase9-ml-acceptance.json`

## W1 gate (G-P9-W1)

- [x] AC-P9-01～10
- [x] AC-P9-UX-01～06 (UX-01 implicit: no new route)
- [x] NR-P9-01～04
- [x] Appendix A §3.2 featured/cull alignment

## Review notes

- **maomi AC-P9-02**: cull layer 27/33 (81.8%); final 26/33 after `low_res` — documented in [maomi.md](./maomi.md)
- **Bundled Studio v2**: homepage shelf, bento preview, phone-strip — same branch, not Phase 10
- **InsightFace / portrait_face_aesthetic**: config key present, not consumed (W2+ deferred)

---

## 提交历史（分支相对 master）

```
0068902 test(phase9): add W2 ML acceptance script with GPU skip gate
3850bbf fix(studio): sync v2 phone frame height with web carousel block
39de26a docs(phase9): close W1 gap-fill — AC-P9-02/UX tests and gate index
7abf0be feat(phase9): complete W2 UX hints and remaining acceptance tests
1bc9c20 feat(phase9): Quality Gate W1 with rules cull and Studio UX
```

**变更规模**：63 files, +4837 / −96 lines（含 PRD 分册与 Studio v2  bundled 改动）

---

## Golden 签核摘要（NR-P9-04）

| trip | scanned | cull-on eligible | 保留率 | curate |
|------|---------|------------------|--------|--------|
| **mao** | 29 | 24 | 82.8% | 3 章 ✅ |
| **maomi** | 33 | 27→26（low_res×1） | cull 层 81.8% | 4 章 ✅ |

记录文件：

- [phase9-golden-cull-signoff.json](./phase9-golden-cull-signoff.json)
- [phase9-quality-gate.json](./phase9-quality-gate.json)
- [mao.md](./mao.md) · [maomi.md](./maomi.md)

---

## 关键修复备忘

**mao 仅 1 张 eligible 问题**：Pass 2 对 material-only 大组误杀（29 张同 `burstGroupId`）。按 PRD §4.1 改为 **ingest 已去重的纯 material 组 skip Pass 2**，重跑后 24 张。

---

## 验收命令速查

```powershell
# Phase 9 回归
pytest tests/test_photo_cull.py tests/test_photo_cull_ml.py tests/test_trip_schema_cull.py `
  tests/test_subject_tagging_bridge.py tests/test_studio_phase9_cull_playwright.py `
  tests/test_asset_quality.py -q

python -m travelogue demo verify

# Golden 重跑（本机相册）
python scripts/phase9_golden_cull_signoff.py --all `
  --write docs/acceptance-records/phase9-golden-cull-signoff.json

# W2 ML（需 GPU + pyiqa）
pip install -e ".[cull-ml]"
python scripts/phase9_ml_acceptance.py --write docs/acceptance-records/phase9-ml-acceptance.json
```

---

## 使用 GitHub CLI 创建 PR

本机若未安装 `gh`，可在浏览器打开上方 Compare 链接手动创建。

```powershell
# 安装并登录后（一次性）
gh auth login

gh pr create --base master --head feat/phase9-quality-gate-w1 `
  --title "feat(phase9): Quality Gate W1 — rules cull, Studio UX, golden signoff" `
  --body-file docs/acceptance-records/phase9-w1-pr-memo.md
```

> 注意：`--body-file` 会包含 front matter 表格；若需纯 PR 正文，复制本文「PR 正文」章节即可。

---

## 合并后待办（非阻塞）

| 项 | 说明 |
|----|------|
| W2 ML-02/04 | 有 GPU 环境跑 `phase9_ml_acceptance.py`，更新 `phase9-ml-acceptance.json` |
| InsightFace | PRD W2 规划，config 有键未实现 |
| demo golden sync | `travelogue demo golden --sync-reference`（demo verify 提示，非阻塞） |
| Phase 10 | 独立里程碑，依赖 W3 桥接已完成 |

---

## 相关文档

- [PRD-PHASE9.md](../PRD-PHASE9.md)
- [IMPLEMENTATION-PHASE9.md](../IMPLEMENTATION-PHASE9.md)
- [ACCEPTANCE-PHASE9.md](../ACCEPTANCE-PHASE9.md)
- [PHASE9-SPIKE-exposure-extreme.md](../PHASE9-SPIKE-exposure-extreme.md)
