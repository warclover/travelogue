# IMPLEMENTATION · Studio AI Surface V1（SAS）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v1.0.0** |
| **对应 PRD** | [PRD-STUDIO-AI-SURFACE-V1.md](./PRD-STUDIO-AI-SURFACE-V1.md) **v0.2.1** |
| **评审** | [acceptance-records/sas-studio-ai-surface-v1-review-2026-08-10.md](./acceptance-records/sas-studio-ai-surface-v1-review-2026-08-10.md) |
| **验收** | [ACCEPTANCE-STUDIO-AI-SURFACE-V1.md](./ACCEPTANCE-STUDIO-AI-SURFACE-V1.md) |
| **分支** | `feat/studio-ai-surface-v1-w1` → `feat/studio-ai-surface-v1-w2` |
| **更新日期** | 2026-08-10 |

## 0. 切拍

| 波次 | 范围 | 状态 |
|------|------|------|
| **W0** | 七席+1 Conditional Go · BLK 回写 v0.2 | ✅ |
| **W1** | Dock「AI」+ Sheet 壳 · 未开闸 · 装帧 · 杂志现网 narrate · 本机连接 · allowlist | ✅ |
| **W2** | 意图卡 · 排版建议 · Dock 徽标 · 旧入口深链 · 窄屏 | ✅ |
| **W3** | COPY-SAS-08 · ACCEPTANCE 勾选 · 狗粮/埋点收口 | ✅ 文档；狗粮见记录 |

## 1. 关键路径

| 区域 | 路径 |
|------|------|
| Sheet 主逻辑 | `templates/studio/preview-toolbar/ai-sheet.js` / `ai-sheet.css` |
| 挂载 | `templates/studio/preview-toolbar/init-v3.js`（精修后、导出前） |
| Dock 互斥 / 窄屏 | `templates/studio/preview-toolbar/dock.css` |
| 精修旧入口 | `templates/studio/preview-toolbar-v3-sheet.js` |
| Entry 意图摘要 | `travelogue/web/studio_entry.py` → `intentBriefUi` |
| 埋点 | `templates/studio/js/analytics.js` · `travelogue/domain/studio_events.py` |
| 接线单测 | `tests/unit/web/test_sas_ai_sheet_wiring.py` |

## 2. 分动作门控（D-SAS-15）

| 动作 | surface | 其它 |
|------|---------|------|
| 杂志文案 narrate | 要 | Key；`structure_draft` 时 CTA 禁用 |
| 装帧 title-art | 不强制 surface（CAL） | Sheet 主入口；精修次入口保留 |
| Intent / Critic UI | 要 | 后端 Agent 自带 fallback |
| 本机连接 | 关闸仍可配 | `allowWhenSurfaceOff` |

## 3. SHD 回写

| ID | 决议 / 落地 |
|----|-------------|
| SHD-SAS-01 | narrate CTA：`g1Pending` →「请先确认分章」 |
| SHD-SAS-02 | AI 用 `preview-ai-sheet-open`；精修用 `preview-sheet-open`；Dock 对 AI/精修保持可点 |
| SHD-SAS-03 | 建议文案 clip ≤36（优先 28） |
| SHD-SAS-04 | 确认框含覆盖提示 |
| SHD-SAS-05 | ≤720 隐藏文件夹；AI 仅图标 |
| SHD-SAS-06 | 关闸「了解如何开启」内联说明（禁 NAS 帮助禁词，不用死链 H7） |

## 4. OQ 拍板（实施默认）

| ID | 默认 |
|----|------|
| OQ-SAS-02 | localhost 显示「高级」；正式包可后续藏 |
| OQ-SAS-03 | **保留**精修装帧次入口 |
| OQ-SAS-04 | 徽标仅未处理排版建议 |

## 5. 非范围

- AIR 三语气 / 渠道包 UI（AC-SAS-08b）
- 正式发版默认 `aiSurfaceEnabled=true`（OQ-AIR-01）
- 展示 Agent 工程名
