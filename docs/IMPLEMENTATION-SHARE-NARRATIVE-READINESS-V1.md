# Travelogue · 敢发叙事就绪 V1 实施清单（IMPLEMENTATION）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **PRD 源** | [PRD-SHARE-NARRATIVE-READINESS-V1.md](./PRD-SHARE-NARRATIVE-READINESS-V1.md) §6 / §10 |
| **验收** | [ACCEPTANCE-SHARE-NARRATIVE-READINESS-V1.md](./ACCEPTANCE-SHARE-NARRATIVE-READINESS-V1.md) |
| **主题代号** | **SNR** |
| **状态** | **W3 Agent 狗粮通过** · PRD 遗漏补全卡已落 · 欠真人 N≥5 / AC-SNR-08 真 Key 手测 |
| **更新日期** | 2026-08-10 |

---

## W0 · 交互债与 CTA（先修踩脚的）

| 卡 | 任务 | 建议触点 | AC |
|----|------|----------|-----|
| **W0-1** | 线框 F1–F8 HTML | `docs/wireframes/share-narrative-readiness-v1-wireframe.html` **✅ 已签核 2026-08-10** | 签核 |
| **W0-2** | 互斥全集（AI↔导出↔分章↔精修） | `longshot.js` 开导出关 AI/精修 · `ai-sheet.js` closePeers **✅** | AC-SNR-07 |
| **W0-3** | AI Sheet × 命中区 / Esc / 导出区 pointer-events | `ai-sheet.js` · `ai-sheet.css` · `dock.css` **✅** | AC-SNR-06 |
| **W0-4** | Dock 金色 CTA 人话标签（D-SNR-11） | `longshot-export-panel.js` **✅**（`导出小红书` / `导出 · {主}等 N 项`） | AC-SNR-11 |
| **W0-5** | 契约单测 | `tests/unit/web/test_snr_w0_contracts.py` **✅** | AC-SNR-06/07/11 |

---

## W1 · 姿态诚实 + 往年 + 禁词

| 卡 | 任务 | 建议触点 | AC |
|----|------|----------|-----|
| **W1-1** | `narrativePosture` 纯函数 + 单测 | `travelogue/domain/narrative_posture.py` + `tests/unit/domain/test_narrative_posture.py` **✅** | AC-SNR-01 |
| **W1-2** | API/预览注入 posture | `studio_entry.build_entry` → `narrativePosture`；`handle_entry` 传 AI/LLM 门控 **✅** | AC-SNR-01 |
| **W1-3** | 姿态条 UI + upgrade CTA | `narrative-posture.js/css` · `init-v3` 挂载 · CTA → AI Sheet `focus=narrate` **✅** | AC-SNR-02 |
| **W1-4** | 长图/可见层禁「旅行照片」 | `alt_text` 回退空 · `share_face_copy` caption/alt 禁词 **✅** | AC-SNR-03 |
| **W1-5** | 往年离群抑制（角标/自动图注） | `format_moment_exif_line(..., trip_primary_year=)` →「往年 · 时段」**✅** | AC-SNR-05 |
| **W1-6** | 全库扫描脚本（文字层禁词 + dirty title 零回退） | `scripts/snr_narrative_readiness_scan.py` **✅** | AC-SNR-03/12 |

---

## W2 · 薄章名 + AI diff + 文案包 L1

| 卡 | 任务 | 建议触点 | AC |
|----|------|----------|-----|
| **W2-1** | 薄章名优先级（D-SNR-03）+ 非手改 refresh | `chapter_titles._pick_thin_chapter_title` · SFP open migrate 调 `refresh_chapter_titles_on_trip` **✅** | AC-SNR-04 |
| **W2-2** | Chapter Naming / SFP 脚注指针 | `PRD-CHAPTER-NAMING.md` SNR 脚注 **✅** | — |
| **W2-3** | AI 状态文案 COPY-SNR-S01 + diff 条 | `ai-sheet.js` 状态机（生成中/失败可重试）· `narrate-diff.js` · job `diffSummary` **✅** | AC-SNR-08/09 |
| **W2-4** | shareCopyPack L1 body 拼装 + UI 次级「仅标题话题」 | `share_copy_pack.py` · export panel L0/L1 **✅** | AC-SNR-10 |
| **W2-5** | 埋点对齐 PRD §8 | `snr_posture_impression` · `snr_upgrade_cta_click` · `snr_diff_show/jump` · `snr_copy_pack` · `snr_panel_mutex` · `snr_cta_label` **✅** | — |
| **W2-6** | COPY-SNR-T02 分章解释 | `chapter_explain.ensure_snr_outlier_explain` **✅** | AC-SNR-05 |
| **W2-7** | `resolve_visible_caption` alt 回退 | `share_face_copy` · `alt_text` **✅** | AC-SNR-03 |
| **W2-8** | 章眉副日期 `dateLabel` | `studio_entry` + `chapter-panel.js` **✅** | F2 |

---

## W3 · 狗粮与收口

| 卡 | 任务 | AC |
|----|------|-----|
| **W3-1** | Persona 复测脚本对照 C1–C8 | [snr-w3-dogfood-2026-08-10.md](./acceptance-records/snr-w3-dogfood-2026-08-10.md) 关闭表 **✅** |
| **W3-2** | 喜欢项零回退清单手签 | AC-SNR-12 · `test_snr_w3_contracts.py` + 扫描闸 **✅** |
| **W3-3** | 真人 N≥5（可与 SFP 队列合并） | **开放** · 不挡 Agent Done |

---

## 依赖与顺序

```text
W0（互斥/关闭/CTA）──独立可合
        │
        ▼
W1（姿态/往年/禁词）──不依赖 AI Key
        │
        ▼
W2（薄章名/diff/文案包）──diff 依赖 SAS 生成成功回调
        │
        ▼
W3 狗粮
```

**禁止**：W1 为凑 lead 引入 stub 假句；W0 只改文案不修命中区。

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-08-10 | 初稿任务卡，对齐 PRD v0.1.0 |
| v0.1.1 | 2026-08-10 | 线框签核；W0-2～W0-5 源码落地 + 契约单测 |
| v0.1.2 | 2026-08-10 | W1-1～W1-5：姿态/禁词/往年 + 姿态条 UI + 契约单测 |
| v0.1.3 | 2026-08-10 | W2：薄章名 / diff 条 / 文案包 L1 + 契约单测 |
| v0.1.4 | 2026-08-10 | W3：扫描闸 + Persona 关闭表 + 喜欢项契约；欠真人 N≥5 |
| v0.1.5 | 2026-08-10 | 遗漏补全：T02 / S01 状态机 / caption 回退 / §8 埋点 / dateLabel；OQ-01/02/04 关单 |
