# SNR W3 狗粮复测 · 敢发叙事就绪（2026-08-10）

| 属性 | 内容 |
|------|------|
| **主题** | [PRD-SHARE-NARRATIVE-READINESS-V1.md](../PRD-SHARE-NARRATIVE-READINESS-V1.md) |
| **对照底稿** | [persona-feedback-trial-2026-08-10.md](./persona-feedback-trial-2026-08-10.md) |
| **方式** | 全库扫描闸 · 契约单测 · Playwright 实机（`demo-album` · `TRAVELOGUE_AI_SURFACE=1` · 1280×900） |
| **性质** | **Agent 狗粮复测**；**不能替代**真人 N≥5（W3-3，可与 SFP 队列合并） |
| **扫描** | `python scripts/snr_narrative_readiness_scan.py --refresh-titles --fail-on alt,ordinal,dirtyResolved,bareRatio` → **exit 0** |
| **契约** | `test_snr_w0/w1/w2/w3_contracts.py` + `test_snr_gap_contracts.py` |

---

## 1. 全库扫描（15 trips · 49 chapters）

| 指标 | 试用前（08-10 底稿） | W3 复测 | 判 |
|------|---------------------|---------|----|
| `alt="旅行照片"` | 1338 | **0**（全 surfaces 重渲后） | ✅ AC-SNR-03 |
| 序号腔章名 | 0（SFP 已清） | **0** | ✅ |
| 脏 resolved displayTitle | 0 | **0** | ✅ AC-SNR-12 |
| 裸日期章名占比（磁盘） | ~63%（31/49） | 57.1%（未 migrate 落盘） | — |
| 裸日期章名占比（薄章名 refresh 后） | — | **8.2%（4/49）** | ✅ AC-SNR-04（≤30%） |
| 高光/图注上下文四位年点号泄漏 | 有（武大高光） | **0**（meta 行程起止年不计） | ✅ AC-SNR-05 |

> 注：磁盘章名仍偏日期腔属存量；打开预览 SFP/SNR migrate 会 idempotent refresh。扫描闸以 `--refresh-titles` 对照 AC-SNR-04。

---

## 2. C1–C8 关闭表

| ID | 试用槽点 | 复测证据 | 状态 |
|----|----------|----------|------|
| **C1** | 成片叙事空壳无解释 | 姿态条可见「纯照片成册 · 可生成杂志感文案」；lead 空仍合法；禁「旅行照片」文字层 | **关闭**（诚实空，非灌 stub） |
| **C2** | 章名日期腔 | refresh 后裸日期 ≤30%；`demo-album` entry 见「京都雨季漫游 · 下午」等 | **关闭** |
| **C3** | 往年 EXIF 泄漏 | 离群路径 →「往年 · 时段」；扫描高光/图注年点号 0 | **关闭** |
| **C4** | 「可生成」≠ 已好看 | AI Sheet 状态「可生成」；正文**无**「杂志文案已完成」；成功路径有 diff 暂存 | **关闭**（diff 需真实 narrate 成功一次手测补强） |
| **C5** | AI × 被 Dock 挡 | Playwright 真实 mouse click × → `closedByX=true`（命中 40×40） | **关闭** |
| **C6** | AI ↔ 导出叠开 | 开导出 caret → `ai=false` 且 export popover 在场 | **关闭** |
| **C7** | 文案包半成品 | L0 hint「标题和话题已备好…」；upgrade 链「生成杂志感后可带正文」可见；L1 规则拼装单测绿 | **关闭** |
| **C8** | CTA「N 个模式」 | Dock 主钮「小红书等2项」 | **关闭** |

---

## 3. 喜欢项零回退（AC-SNR-12）

| 项 | 证据 | 判 |
|----|------|----|
| 六平台选项仍在 | `longshot-export-panel.js` 含 wechat_chat / moments / xiaohongshu / official / poster_bric / album_spread | ✅ |
| 窄屏 gate 文案 | `narrow-gate.js`「返回首页制作」「复制电脑打开地址」 | ✅ |
| 脏题名 0 | 扫描 dirty_resolved=0 | ✅ |
| AI「不自动消耗」 | `ai-sheet.js` 仍含「不自动消耗」信任句 | ✅ |
| 本地隐私 / 示例 / 精修 | 未改入口合同；无本主题回退 diff | ✅ 手签 |

---

## 4. Playwright 现场摘要（demo-album）

```text
postureText = 纯照片成册 · 可生成杂志感文案
cta         = 小红书等2项
closedByX   = true
export→AI   = ai closed, popover open
narrateStatus = 可生成
has「杂志文案已完成」= false
pack hint   = 标题和话题已备好 · 正文可粘贴后自填
upgrade     = 生成杂志感后可带正文（visible）
```

---

## 5. 书面降级 / 开放项

| 项 | 说明 |
|----|------|
| **W3-3 真人 N≥5** | 未跑；建议与 SFP 队列合并，不挡本轮 Agent Done |
| **narrate 成功 diff 条** | 代码路径 + 契约齐（含「生成中/失败可重试」）；**AC-SNR-08 真 Key 手测仍开放** |
| **磁盘章名落盘** | 依赖用户打开预览 migrate；全库可另跑 refresh 脚本批量落盘（非门禁） |
| **OQ-SNR-01/02/04** | 已关单：精修不加往年小标；书架无小点；薄章名允许极短场景词 |

---

## 6. 结论

> **SNR W0–W2 工程债与 C1–C8 槽点在 Agent 狗粮维度可关闭。**  
> 主题 Done 门仍欠 **真人 N≥5**；其余 AC-SNR-01～12（除真人）有扫描 / 契约 / Playwright 证据。
