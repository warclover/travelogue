# 敢发净化 V1 · 实施清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-SHARE-FACE-PURITY-V1.md](./PRD-SHARE-FACE-PURITY-V1.md) |
| **验收** | [ACCEPTANCE-SHARE-FACE-PURITY-V1.md](./ACCEPTANCE-SHARE-FACE-PURITY-V1.md) |
| **分支** | `feat/share-face-purity-v1` |
| **日期** | 2026-07-24 |

## W0

| 包 | 状态 | 主改动 |
|----|------|--------|
| BE-SFP-01 | ✅ | `chapter_titles.py` Sequence Pass · `narrative_validate` 闸 · 弱桶 `merge_weak_same_day_followups` |
| BE-SFP-02 | ✅ | `title_humanize` 数字日期噪声 · 择优 · `migrate_share_face_purity_on_open` @ `handle_entry` |
| BE-SFP-03 | ✅ | stub 回声宁空 · `share_face_copy` 日期·题名 · 弱标签 ≥3 抑制 |
| FE-SFP-06 | ✅ | chapter-panel ↔ export popover 互斥 · z=520 |

## W1

| 包 | 状态 | 主改动 |
|----|------|--------|
| BE-SFP-04 | ✅ | `sort_chapters_by_temporal_key` @ curate 写盘前 |
| FE-SFP-05 | ✅ | 「可更新」→「可重排」· tooltip · Help H3b |

## W2

| 包 | 状态 | 主改动 |
|----|------|--------|
| FE-SFP-07 | ✅ | 导出设置「复制文案包」· 成功面 NAS 提示 |
| QA-SFP-08 | ✅ | `tests/unit/domain/test_share_face_purity.py` · dogfood |

## 收口补丁（P1）

| 项 | 状态 |
|----|------|
| `chapter_explain` 跨年 / 弱合并 COPY | ✅ |
| L2「可重排」中性徽标 CSS | ✅ |
| AC-SFP-06 Playwright | ✅ `tests/e2e/test_sfp_chapter_panel_playwright.py` |

## 收口补丁（P2）

| 项 | 状态 |
|----|------|
| 线框 F4/F5 产品签核 | ✅ 2026-07-24 |
| pipeline 收尾 migrate | ✅ `_finalize_pipeline_result` |
| curate 后序号腔闸 | ✅ `enforce_no_ordinal_face_titles` |
| `sfp_*` 五事件埋点 | ✅ BE allowlist + FE analytics + emit |

## 收口补丁（P3 · PRD 缺口）

| 项 | 状态 |
|----|------|
| 点号日期链 noise +「精选2」软剥 | ✅ `title_humanize` · FE 同律 |
| D-SFP-08② 跨年章名带年 | ✅ 生成 + open migrate |
| QA fixture 加载测 | ✅ `trip.sfp_same_day_dirty_title.json` |

## 热修 · 印章假阳性

| 项 | 状态 |
|----|------|
| 打开预览 no-op 仍 bump revision →「预览需更新」 | ✅ `handle_entry` 仅变更时 persist + 重盖章；漂移修复 |

## W3

| 项 | 状态 |
|----|------|
| 存量抽检（打开后 0 序号 / 0 脏题名） | ✅ 见 [w3-gate](./acceptance-records/share-face-purity-v1-w3-gate-2026-07-24.md) |
| Persona E2–E8 + P1–P5 | ✅ |
| 真人 N≥5 | ⏳ |
