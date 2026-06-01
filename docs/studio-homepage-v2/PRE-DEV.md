# Studio 首页 v2 · 开工前清单

> 团队 A/B/C/D 项落地索引 · 与 [OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md) 联动。

---

## A. 阻塞项（写第一行代码前）

| # | 项 | 状态 | 文档 |
|---|-----|------|------|
| A1 | manifest + API 最小契约 | ✅ 已冻结 | [DATA-CONTRACT.md](./DATA-CONTRACT.md) |
| A2 | Feature flag 机制与 v3 共存 | ✅ 已冻结 | [FEATURE-FLAG.md](./FEATURE-FLAG.md) |
| A3 | demo-showcase 设计派单 | ⏳ owner/due 待填 | [DEMO-ASSETS-BRIEF.md](./DEMO-ASSETS-BRIEF.md) |
| A4 | M20-i 前 telemetry 聚合 | ✅ 脚本+Runbook（告警 Owner 待填） | [TELEMETRY.md](./TELEMETRY.md) · [RUNBOOK-HOLDBACK.md](./RUNBOOK-HOLDBACK.md) |

---

## B. 强烈建议（第一周）

| # | 项 | 动作 |
|---|-----|------|
| B5 | Lightbox 手势 spike | Week1 · pointer/touch 双轨 · `DRAG_THRESHOLD` 10px / 8px |
| B5 | Carousel spread spike | Week1 · clamp + 奇数尾页 + dots 映射原型 |
| B6 | Dev harness | [DEV-HARNESS.md](./DEV-HARNESS.md) · M20-g 起 |
| B7 | 浏览器/性能矩阵 | 见 §1 |
| B8 | sessionStorage 护栏 | v2 不改既有键；M20-i 回滚演练 |
| B9 | 线框 reconcile | v1.6 已对齐 PRD v2.0.3（⤢ · demo-flag · clamp · sidebar） |

---

## §1. 目标浏览器 / 设备矩阵

| 目标 | 内核 | M20 验收 |
|------|------|----------|
| Windows 桌面 | **系统默认浏览器**（Edge Chromium / Chrome） | ✓ 主 |
| macOS 桌面 | Safari / Chrome | ✓ |
| iPad 横屏 | **Safari iPadOS 17+** | ✓ |
| iPad 竖屏 / 手机 | Unsupported 轻提示 | ✓ |
| Studio 嵌入式 WebView | **WebView2**（若桌面壳分发） | 壳层另测；M20 以浏览器为准 |

**兼容探针**（M20-a 前跑一遍）：

- `aspect-ratio` · `scroll-snap` · `backdrop-filter` · `pointerrawupdate`

**LCP 测量**：

- 本地：`python scripts/studio_lcp_measure.py --base http://127.0.0.1:8766 --runs 5`
- 合并 holdback：`python scripts/studio_homepage_m20i_drill.py --spawn --synthetic --out holdback.json`
- CI：Playwright · 分 variant（`tests/test_studio_lcp_playwright.py`）
- 回滚判据：见 [TELEMETRY.md](./TELEMETRY.md) §4 · [RUNBOOK-HOLDBACK.md](./RUNBOOK-HOLDBACK.md)

---

## §2. 技术 Spike 交付标准

### Lightbox（§6.4）

- [x] `DRAG_THRESHOLD_PX = 10`（mouse）/ `8`（touch）· `lightbox-logic.js`
- [x] carousel 横拖与 9:16 内滚不互抢（AC Playwright HP2-07）
- [x] ⤢ 按钮始终可点（AC Playwright HP2-06）

### Carousel（D-10）

- [x] `goTo(i)` clamp 单测（`carousel-logic.test.mjs`）
- [ ] 5-page 尾页留白截图 → [VISUAL-SIGNOFF.md](./VISUAL-SIGNOFF.md) `02-odd-tail-carousel.png`
- [x] dots ↔ index 一致（AC Playwright）

---

## §3. 里程碑依赖（显式）

| 里程碑 | 硬前置 |
|--------|--------|
| M20-a | DATA-CONTRACT · FEATURE-FLAG · demo 素材 **或** dev SVG fallback |
| M20-b | manifest.pages · spread spike |
| M20-c | Lightbox spike |
| M20-h | DEV-HARNESS · AC-VERIFICATION 自动化项 |
| **M20-i** | **TELEMETRY 聚合 + holdback 报告 + LCP/error 管道** | ✅ 脚本/单测/e2e/nightly |
| M20-j | M20-i 演练 + 门控 e2e + on-call 签字 | ⏳ 见 [SIGNOFF-M20J.md](./SIGNOFF-M20J.md) · 默认仍 `off` |

---

## §4. 正式开发顺序（PRD）

`M20-a → d → b → c → e → f → g → h → i → j`

Spike（B5）与 M20-a **并行**，不阻塞 a 的 Slogan/布局，但 **阻塞** b/c 合并。
