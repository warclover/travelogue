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

## W3

| 项 | 状态 |
|----|------|
| 存量抽检 / Persona 复测 / 真人 N≥5 | ⏳ 见 ACCEPTANCE §5 |
