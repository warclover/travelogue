# UI Detail · Surface Inventory v0（弹窗家族试点）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **日期** | 2026-07-22 |
| **对照** | [UI-DETAIL-CONTRACT-V0.md](./UI-DETAIL-CONTRACT-V0.md) |

---

## 试点范围（本波必扫）

| ID | 表面 | 触发路径 | 主样式 | 备注 |
|----|------|----------|--------|------|
| S-MODAL | `studioModal` 确认框 | `window.studioModal(...)`；导入覆盖确认、书架删除、LLM 确认等 | `studio-modal.css` | 规范源 |
| S-MODAL-PREVIEW | 同上（预览页） | 预览工具栏内确认 | `studio-modal.css`（`modal-chrome.css` 已 stub） | 2026-07-22 已统一 |
| S-FS | FirstSuccess | Import 成功 overlay `#v2-first-success` | `homepage-v2/css/overlays.css` | 深色 |
| S-FAIL | Failure | Import 失败 `#v2-failure` | `overlays.css` | 深色 / alertdialog |
| S-IMP | Importing | `#v2-importing` 进度面板 | `overlays.css` | 含 wait-tips |
| S-WIZ | Import Wizard | CTA → `#v2-import-wizard` | `homepage-v2/css/import-wizard.css` | 全屏 sheet |
| S-SET | Settings popover | 顶栏设置 | `bento.css` → `--studio-panel-*` | Wave2 已对齐 Sheet |
| S-TOAST | Toast | `studio-toast.js` | `studio-modal.css` 后半 | 轻量，抽检 |

## 调用点（S-MODAL）

| 文件 | 用途（摘要） |
|------|----------------|
| `homepage-v2/import-run.js` | 导入冲突 / 覆盖确认 |
| `homepage-v2/import-wizard.js` | Wizard 内确认 |
| `homepage-v2/shelf-menu.js` | 书架危险操作 |
| `homepage-v2/shelf-longshot.js` | 自建长图弹层（复用 class） |
| `js/llm-settings.js` | 引擎配置确认 |
| `js/output-recipe.js` | 配方相关弹层（自建 backdrop） |
| `preview-toolbar/shell.js` | 预览侧确认桥接 |

## Wave2（Settings + Preview sheet · 已修）

| ID | 表面 | 触发路径 | 主样式 | 状态 |
|----|------|----------|--------|------|
| S-SET | Settings popover | `#v2-settings-toggle` | `bento.css` → `--studio-panel-*` | 已对齐 |
| S-SHEET | Preview refine sheet | Dock「精修」 | `sheet.css` → `--studio-panel-*` | 已对齐 |

审计：`scripts/studio_ui_detail_static_audit.py --wave settings-sheet`  
运行时：`tests/e2e/test_studio_ui_detail_wave2_playwright.py`  
结果：`acceptance-records/ui-detail-wave2-settings-sheet-2026-07-22.md`

## Wave3（Preview chrome + Help · 已修）

| ID | 表面 | 主样式 | 状态 |
|----|------|--------|------|
| S-DOCK-CHROME | shell / longshot / dock / v3-bar / task-dock | `preview-toolbar/*.css` → `--preview-*` | 已对齐 |
| S-DRAWER | Preview drawers | `drawers.css` → `--preview-*` | 已对齐 |
| S-HELP | Help drawer | `help-drawer.css` → `--studio-panel-*` | 已对齐 |
| S-COHORT | Cohort picker | `cohort.css` | 已对齐 |

审计：`python scripts/studio_ui_detail_static_audit.py --wave preview-chrome`

## Wave4 · wait-tips tip-tone（已收敛）

| ID | 表面 | 主样式 | 状态 |
|----|------|--------|------|
| S-WAIT | wait-tips + import source | `overlays.css` | gold/cream 族；D-UID-10 |

审计：`python scripts/studio_ui_detail_static_audit.py --wave wait-tips`

## Wave5 · Capability + Narrow + Lightbox（已收敛）

| ID | 表面 | 主样式 | 状态 |
|----|------|--------|------|
| S-CAP | Capability card | `capability-card.css` | panel tokens；D-UID-11 |
| S-NARROW | Narrow gate | `shell.css` | cream/px；D-UID-11 |
| S-LIGHTBOX | Homepage lightbox | `chrome.css` | 暖褐；D-UID-11 |

审计：`python scripts/studio_ui_detail_static_audit.py --wave cap-narrow-lightbox`

## Wave6 · Bench + Wizard empty + Carousel（已收敛）

| ID | 表面 | 主样式 | 状态 |
|----|------|--------|------|
| S-BENCH | Adv popover + combobox | `bench.css` | panel；D-UID-12 |
| S-WIZARD-ACCENT | Wizard 空主题 | `import-wizard.css` | cream；D-UID-12 |
| S-CAROUSEL | Carousel dots | `carousel.css` + classic | panel-ink；D-UID-12 |

审计：`python scripts/studio_ui_detail_static_audit.py --wave bench-wizard-carousel`

## Wave7 · Homepage tokens + theme-aware hardcodes（已收敛）

| ID | 表面 | 主样式 | 状态 |
|----|------|--------|------|
| S-HOME-TOKENS | 裸 `:root` / sky 块 | `tokens.css` | mist 默认；sky 显式；D-UID-13 |
| S-BENCH-MAIN | recent card / stale chip | `bench.css` | `--v2-*`；D-UID-13 |
| S-PHONE | Phone strip | `phone.css` | token 阴影/dot；D-UID-13 |

审计：`python scripts/studio_ui_detail_static_audit.py --wave home-tokens`

## Wave8 · Shelf + Dev + Loading（已收敛）

| ID | 表面 | 主样式 | 状态 |
|----|------|--------|------|
| S-SHELF | Shelf 菜单/resume | `shelf.css` | panel；D-UID-14 |
| S-DEV | Dev panel | `dev-panel.css` | cream dark；D-UID-14 |
| S-LOADING | Loading shimmer | `bento.css` | 主题边框；D-UID-14 |

审计：`python scripts/studio_ui_detail_static_audit.py --wave shelf-dev-loading`

## Wave9 · Unsupported + Failure + Toast（已收敛）

| ID | 表面 | 主样式 | 状态 |
|----|------|--------|------|
| S-UNSUPPORTED | Unsupported gate | `chrome.css` | cream；D-UID-15 |
| S-FIRST-SUCCESS | FirstSuccess / Failure | `overlays.css` | fs token；auth 无薄荷；D-UID-15 |
| S-TOAST | studio + preview toast | `studio-modal.css` / `drawers.css` | cream 对齐；D-UID-15 |

审计：`python scripts/studio_ui_detail_static_audit.py --wave overlay-toast`

## Wave10 · Wizard + Help + Closeout（已收敛）

| ID | 表面 | 主样式 | 状态 |
|----|------|--------|------|
| S-IMPORT-WIZARD-UI | Wizard 字阶 | `import-wizard.css` | ≥11px；D-UID-16 |
| S-HELP-COPY | Help 抽屉 | `help-drawer.css` | panel；D-UID-16 |
| S-CLOSEOUT | Dock / Longshot + `--wave all` | task-dock / longshot / audit | cream+gold；误报已修；D-UID-16 |

审计：`python scripts/studio_ui_detail_static_audit.py --wave wizard-help-closeout`  
全量：`python scripts/studio_ui_detail_static_audit.py --wave all`

## Wave11 · Runtime closeout + Contract freeze（已落地）

| ID | 表面 | 门禁 | 状态 |
|----|------|------|------|
| S-RUNTIME | Help / Cap / Toast / Unsupported | `test_studio_ui_detail_wave11_runtime_playwright.py` | 运行时字色阶硬闸 |
| S-DOC-FREEZE | Contract v0 | `UI-DETAIL-CONTRACT-V0.md` | **frozen** |

审计：静态 `--wave all` + Wave11 e2e。

## 扩面候选（仅新产品壳层时开波）

| ID | 表面 | 主样式 |
|----|------|--------|
| S-NEW-SHELL | 未来新 Studio 壳层 | TBD |

## 已知高风险

1. ~~`.studio__modal*` 双标准~~ → **已修**（`modal-chrome.css` stub）。
2. ~~Settings / Sheet / preview chrome `#1a2f28`~~ → **已挂** `--studio-panel-*` / `--preview-*`。
3. ~~wait-tips tip-tone~~ → **已收敛** gold/cream（D-UID-10）。
4. ~~Capability / narrow / lightbox 森林双色~~ → **已收敛**（D-UID-11）；并恢复 `:root --studio-panel-*`。
5. ~~Bench 浅色面板 / wizard cyan / carousel slate~~ → **已收敛**（D-UID-12）。
6. ~~Homepage 裸 `:root` cyan + 组件硬编码~~ → **已收敛**（D-UID-13）。
7. ~~Shelf / Dev / Loading cyan shimmer~~ → **已收敛**（D-UID-14）。
8. ~~Unsupported / Failure auth / Toast 薄荷森林~~ → **已收敛**（D-UID-15）。
9. ~~Wizard 10px / Help 森林 / Dock·Longshot tip 回潮~~ → **已收敛**（D-UID-16）；全波次 P1 门禁误报已修。
10. ~~运行时抽检缺口 / 合同未冻结~~ → **Wave11 已补**。
