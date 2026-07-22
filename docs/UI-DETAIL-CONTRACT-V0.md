# UI Detail Contract v0 · Studio 弹窗家族

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **frozen**（Wave1–10 样式落地完成；Wave11 起仅扩运行时抽检 / 回潮门禁） |
| **日期** | 2026-07-22 |
| **范围** | Studio 工具 UI 弹窗 / 浮层文字与按钮（不含作品预览艺术排版） |
| **用途** | 细节审计基线；偏差记缺陷。样式变更须对照 D-UID-* 并复跑 `--wave all` |

---

## 1. 确认框（`studioModal` / `.studio__modal`）

以 `templates/studio/studio-modal.css` 为**唯一规范源**（首页与全站确认框）。

| 角色 | 字号 | 字重 | 行高 | 颜色 |
|------|------|------|------|------|
| 标题 `h3` | 17px | 600 | 1.35 | `#14110d`（继承面板） |
| 正文 `.studio__modal-body` | 14px | 400 | 1.55 | `rgba(20,17,13,.72)` |
| 帮助链 | 13px | 600 | — | `#3d6b5a` |
| 按钮 | 13px | 600（ghost 500） | — | primary `#14110d` / ghost muted / danger `#a33b36` |

几何：

| 项 | 值 |
|----|-----|
| 面板宽 | `min(100%, 400px)` |
| 面板 padding | `22px 24px 20px` |
| 圆角 | `10px` |
| 标题下边距 | `8px` |
| 正文下边距 | `20px` |
| 按钮 min-height | `40px` |
| 按钮圆角 | `6px`（非 pill） |
| backdrop padding | `24px` |
| backdrop 色 | `rgba(6,5,4,.52)` |

对齐：标题与正文左缘对齐；默认按钮行右对齐；stacked 时按钮等宽满宽。

---

## 2. 深色结果浮层（FirstSuccess / Failure / Importing）

允许深色主题，但**同一面板内**字号阶梯不得超过下列集合：

| 角色 | 允许字号 |
|------|----------|
| 眉题 / 标签 | 10–11px |
| 主标题 | 18–20px |
| 正文 / 引导 | 12–13px |
| 辅助 / countdown | 12px |
| 主 CTA | 14px |
| 次链 / dismiss | 12px |

颜色角色（每屏语义色 ≤ 4）：

1. 主文字（ink）
2. 次文字（muted）
3. 强调 / accent（含成功金或失败珊瑚，二选一）
4. CTA 前景（深色字压在金底上）

禁止：同屏再叠 cyan / green / blue / orange tip-tone。Import 暗玻璃 wait-tips 标签只允许 gold / cream / white 浓淡变化（语义靠文案）。

---

## 3. Import Wizard

| 角色 | 允许字号 |
|------|----------|
| 标题 | 21px |
| 主按钮文案 | 14px |
| 正文 / hint | 12–13px |
| 辅助 small / chip | 10–12px |
| 关闭 × | 图标可 24px，不计入正文阶梯 |

对齐：标题与关闭钮同一水平带；主 CTA 与 demo 按钮同宽左缘对齐。

---

## 4. 通用违规判定（审计用）

| ID | 规则 | 严重度 |
|----|------|--------|
| D-UID-01 | 同一选择器在多文件定义且关键属性冲突（双标准） | P0 |
| D-UID-02 | 确认框运行时字号/颜色偏离 Contract §1 | P0 |
| D-UID-03 | 单面板可见文本字号种类 > 5（不含图标） | P1 |
| D-UID-04 | 单面板可见文本颜色种类 > 4（语义色） | P1 |
| D-UID-05 | 标题与正文左缘差 > 1px | P1 |
| D-UID-06 | 同角色按钮高度差 > 2px 或圆角体系混用（6px vs pill） | P1 |
| D-UID-07 | 硬编码色/字号离散度高（静态直方图离群） | P2 |
| D-UID-08 | Settings 与 Preview sheet 声称对齐但色族/标题阶梯不一致 | P1 |
| D-UID-09 | Preview chrome / Help 仍含裸 `#1a2f28` / 蓝灰 hex（未挂 panel token） | P1 |
| D-UID-10 | wait-tips / import source 仍用 cyan/green/blue/orange tip-tone（未收敛 gold 族） | P1 |
| D-UID-11 | Capability / narrow-gate / lightbox 偏离 panel·cream（森林双色或 rem 字阶） | P1 |
| D-UID-12 | Bench 浅色面板 / Wizard 空主题 cyan / carousel 点 slate | P1 |
| D-UID-13 | 首页裸 `:root` 仍为 sky cyan，或组件硬编码 sky cyan（不跟主题 token） | P1 |
| D-UID-14 | Shelf 菜单 / Dev 暗玻璃 / Loading shimmer 偏离 panel·cream 或 chip 小于 11px | P1 |
| D-UID-15 | Unsupported / Failure auth / Toast 仍用薄荷森林色或 brand 10px | P1 |
| D-UID-16 | Wizard 10px / Help 森林底 / Dock·Longshot 薄荷橙 tip 回潮 | P1 |

---

## 5. Settings + Preview sheet（Wave2 · 已落地）

共享 token（`studio-modal.css` `:root`）：

| Token | 值 | 角色 |
|-------|-----|------|
| `--studio-panel-ink` | `#14110d` | 标题/正文 |
| `--studio-panel-muted-solid` | `#5c574f` | 次要 |
| `--studio-panel-accent` | `#3d6b5a` | 强调 / CTA |
| `--studio-panel-title-size` | `15px` | 面板标题 |
| `--studio-panel-label-size` | `11px` | 标签 |
| `--studio-panel-chip-size` | `11px` | badge（禁 9px） |

Settings：`--v2-set-*` → panel；Sheet：`--sheet-*` → panel。禁止再引入 slate（`#0f172a`）或蓝灰 muted（`#546e7a` 系）作文案色。

---

## 5b. Import wait-tips（Wave4 · 已落地）

暗玻璃 token（挂在 `.v2-import-panel`）：`--wt-ink` / `--wt-muted` / `--wt-gold` / `--wt-gold-soft` / `--wt-cream`。  
标签字号 11px；`data-tone` 仅用金/奶油/白底透明度区分。禁止 `#90e0ef` source 与彩虹 tip-tone。

---

## 5c. Capability + Narrow gate + Lightbox（Wave5 · 已落地）

- Capability：`capability-card.css` 挂 `--studio-panel-*`；标题 15px；禁止 JS 内联旧森林色。
- Narrow gate：暗底 + cream ink（`--ng-ink: #f5f0e8`）；字阶 px（20 / 13 / 14）；主按钮 ink 压 accent-strong。
- Lightbox：滚动底/占位暖褐系；caption 11px。

---

## 5d. Bench + Wizard empty + Carousel（Wave6 · 已落地）

- Advanced popover / preview combobox：`--v2-adv-*` / `--v2-combo-*` → `--studio-panel-*`；禁 slate/cyan focus。
- Wizard 空主题（legacy sky）：cream 族，禁 `#90e0ef`。
- Carousel dots：`border-color: var(--studio-panel-ink)`。

---

## 5e. Homepage tokens + 主题感知硬编码（Wave7 · 已落地）

- 裸 `:root` = mist 默认；cyan 仅 `:root[data-v2-theme="sky"]`。
- `theme-boot` / `applyTheme`：sky 写 `data-v2-theme="sky"`，不再 `removeAttribute`。
- Bench / bento / carousel / phone：chip/阴影/focus 走 `--v2-*`，禁止硬编码 `rgba(72,202,228)` / `#0077b6`。

---

## 5f. Shelf + Dev + Loading（Wave8 · 已落地）

- Shelf 菜单：`--studio-panel-ink/border`；resume 底 `--v2-surface`。
- Dev panel：`--dev-ink/muted/surface` cream 暗玻璃；字号 ≥11px；`--studio-font-ui`。
- Loading shimmer：跟 `--v2-border` / `--v2-surface`；禁 `rgba(189,230,240)`。

---

## 5g. Unsupported + Failure + Toast（Wave9 · 已落地）

- Unsupported：`--un-ink/muted`；brand 11px；主按钮 cream 压 accent-strong（圆角 8px）。
- Failure auth：禁 `#9ec5b8` 薄荷；echo ≥11px。
- Preview toast 与 `studio__toast` 同 cream 暗底（禁 `#f5fbf8` / `rgba(26,47,40)`）。

---

## 5h. Wizard + Help + Closeout（Wave10 · 已落地）

- Wizard：辅助文案 ≥11px。
- Help 抽屉：surface/ink/border → `--studio-panel-*`；标题 15px。
- Task dock / Longshot：cream + gold warn；禁 mint `#a8dcc8` / cyan `#81d4fa` / 橙 tip。
- 全波次 `--wave all`：D-UID-09 不扫 token 源 `studio-modal.css`；D-UID-10 仅扫含 wait-tips 标记的文件。

---

## 5i. Runtime closeout（Wave11 · 已落地）

- 静态：`python scripts/studio_ui_detail_static_audit.py --wave all` → P0/P1 = 0。
- 运行时：`tests/e2e/test_studio_ui_detail_wave11_runtime_playwright.py` 抽检 Help / Capability / Toast / Unsupported。
- 合同本文 **frozen**：不再扩表面清单，除非新产品壳层。

---

## 6. 非目标

- 杂志/卷轴作品页艺术字号
- 完整 Design Token 重构（已有薄层 `--studio-panel-*` 即可）
