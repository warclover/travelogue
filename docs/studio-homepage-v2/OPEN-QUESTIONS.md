# Studio 首页 v2 · Open Questions 日志

> 不闭环则 M20-a 起跑即卡 · 每项需 **Owner + Due**。

| ID | 问题 | 阻塞 | Owner | Due | 状态 |
|----|------|------|-------|-----|------|
| OQ-MANIFEST | 京都 trip 最终章数是否为 3（5 半页） | M20-a 素材 | 产品/设计 | 2026-06-01 | 🟢 示例已按 3 章冻结 |
| OQ-DEMO-ASSETS | demo-showcase WebP 切图包交付 | M20-a dogfood | **设计 · @PM 指派** | **2026-06-15** | 🔴 |
| OQ-FLAG-DEFAULT | 各环境 `TRAVELOGUE_STUDIO_HOMEPAGE_V2` 默认值 | M20-a | 工程 | 2026-06-01 | 🟢 见 FEATURE-FLAG.md · 生产 intentionally `off` |
| OQ-TELEMETRY | holdback 看板 + LCP/error 聚合 + Slack 告警 | **M20-i/j** | **平台/SRE · @PM 指派** | **2026-06-08** | 🔴 脚本就绪 · [RUNBOOK-DOGFOOD.md](./RUNBOOK-DOGFOOD.md) |
| OQ-WEBVIEW | 桌面壳 WebView2 最低版本 | 壳层发布 | 桌面 | 非 M20 | ⚪ |
| OQ-SHELF-PAGE | trips>20 分页是否进 M20-e | M20-e | 产品 | 2026-05-01 | 🟢 M20 不做，§8.2 已写 |
| OQ-L2-LOOPBACK | L2 在 loopback 不触发 — 验收范围 | QA | 工程 | 2026-06-01 | 🟢 见 DATA-CONTRACT §4.2 |
| OQ-USABILITY | AC-01 五名被试窗口 | G2 切主站 | 产品/UX · @PM | **2026-06-08** | ⚪ [USABILITY-AC01.md](./USABILITY-AC01.md) |
| OQ-VISUAL-SO | 视觉 sign-off AC-03/08/12/17/18 | G2 切主站 | 设计/QA | **2026-06-12** | ⚪ [VISUAL-SIGNOFF.md](./VISUAL-SIGNOFF.md) |
| OQ-IPAD-MANUAL | iPad Safari 实机 | G1 dogfood | QA | **2026-06-10** | ⚪ [DEVICE-MATRIX-IPAD.md](./DEVICE-MATRIX-IPAD.md) |

**更新规则**：闭环后改 Status 为 🟢 并链到 PR/文档 commit。

**Escalation**：OQ-DEMO-ASSETS、OQ-TELEMETRY 若 Due 前 3 天仍 🔴 → 升级 PM 砍 scope 或推 M20-i。

**Rollout 日志**：[`../acceptance-records/studio-homepage-v2-rollout-log.json`](../acceptance-records/studio-homepage-v2-rollout-log.json)
