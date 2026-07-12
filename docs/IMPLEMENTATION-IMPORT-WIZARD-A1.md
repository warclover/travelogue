# Import Wizard v3 + A.1 · 实施任务清单

| 属性 | 内容 |
|------|------|
| **基线 PRD** | [PRD-IMPORT-SHEET-v3-WIZARD.md](./PRD-IMPORT-SHEET-v3-WIZARD.md) v3.0.1 |
| **增量 PRD** | [PRD-IMPORT-WIZARD-A1-DELTA.md](./PRD-IMPORT-WIZARD-A1-DELTA.md) v1.0 |
| **线框** | [wireframes/import-wizard-v3.html](./wireframes/import-wizard-v3.html) · [wireframes/import-wizard-a1.html](./wireframes/import-wizard-a1.html) |
| **状态** | **Implemented · Sheet 已退役**（见 [IMPLEMENTATION-IMPORT-SHEET-RETIRE.md](./IMPLEMENTATION-IMPORT-SHEET-RETIRE.md)）；Wizard 唯一入口 |
| **预估** | v3 收口 ≈1～2d（若 AC 已绿可跳过）+ A.1 P0/P1 ≈ **2.5～3.5d** + 测试 1d |
| **更新日期** | 2026-07-12 |

---

## 0. 范围与默认决议

### 0.1 做什么

| 包 | 内容 |
|----|------|
| **V3-SHIP** | Wizard v3 已实现代码的发版收口（flag / AC / dogfood） |
| **A1-P0** | A1-01～05（与灰度同发） |
| **A1-P1** | A1-06～10（同里程碑） |
| **A1-P2** | A1-11～16（**本清单不排期**，单列 A.1.1） |

**不做**：方案 B（拖放 / 交付物插画 / 偏好后置）、Lightbox（Q-01）、拖拽文件夹（Q-03）。

### 0.2 评审默认值（未书面推翻则按此实施）

| 议题 | 默认 | 影响任务 |
|------|------|----------|
| R-A1-01 P0 与 v3 同发 | **同发** | 并入 M-A1-2/3 |
| R-A1-02 2b CTA「按这些偏好开始」 | **P1 做**（本清单含 A1-13 提前并入 P1） | IW-A1-13 |
| R-A1-03 关闭确认含 scrim | **仅 × 与 Esc**（scrim 若可关则同 Esc） | IW-A1-09 |
| R-A1-04 张数阈值 | **&lt;4 / &gt;300** | IW-A1-03 |

### 0.3 下游铁律（继承 v3 §16）

- 禁止 Wizard 直调 `POST /import`；必须 `closeImportSheet` → `startV2Import` / `startV2UploadImport`
- `buildWizardPayload` 字段契约见 PRD §16.3；`import_start.surface` 仍为 `v2_sheet`
- 旧 Sheet / `import_wizard_v3_enabled` **已删除**；无 flag 回退路径

---

## 1. 代码基线（As-Is）

| 模块 | 路径 | 状态 |
|------|------|------|
| Wizard DOM | `templates/studio/studio-home-v2.html` `#v2-wizard-root` | ✅ 有 |
| Wizard CSS | `templates/studio/homepage-v2/css/import-wizard.css` | ✅ 有 |
| Wizard JS | `templates/studio/homepage-v2/import-wizard.js` | ✅ 有（状态机 / 模式卡 / 抽屉 / 下游出口） |
| Flag | ~~`studio.importWizardV3Enabled`~~ → **已删除** | ✅ Sheet 退役 P2 |
| album-preview | `folderName` + thumbs + `photoCount` | ✅ 有 |
| E2E | `tests/e2e/test_import_wizard_v3_playwright.py` | ✅ 有 |
| **A.1 增量** | 头栏双返回、2b 平铺四分组、无张数提示/信任行/关闭确认等 | ✅ 已做（P0/P1） |

> 实施以 **A.1 增量改现有 wizard** 为主，勿新建第二套向导。

---

## 2. 里程碑总览

| 里程碑 | 目标 | 出口标准 | 预估 |
|--------|------|----------|------|
| **M-A1-0** | 基线核对 + 本清单 | v3 E2E 本地绿；缺口登记 | 0.5d |
| **M-A1-1** | A1-P0 壳与文案 | AC-A1-01/04/05/06 手工过 | 1d |
| **M-A1-2** | A1-P0 验货 + 2b 折叠 | AC-A1-02/03 + AC-IW-02 不回退 | 1d |
| **M-A1-3** | A1-P1 预填 / tip / 关闭 / 摘要 | AC-A1-07～10 | 1.25d |
| **M-A1-4** | 测试 + 埋点 + 下游回归 | AC-A1-* + AC-IW-DS-* 全绿 | 1d |
| **M-A1-5** | flag 灰度 + dogfood | 5 人走查 / 漏斗无跌 | 7d 观察 |

**开发合计 ≈ 4.75d**（不含 M-A1-5 观察）。若 M-A1-0 发现 v3 AC 缺口，另加收口工时。

```mermaid
flowchart LR
  M0[M-A1-0 基线] --> M1[M-A1-1 P0 壳文案]
  M1 --> M2[M-A1-2 验货+折叠]
  M2 --> M3[M-A1-3 P1]
  M3 --> M4[M-A1-4 测试]
  M4 --> M5[M-A1-5 灰度]
```

---

## 3. 改动文件地图

| 文件 | 预期改动 |
|------|----------|
| `templates/studio/studio-home-v2.html` | 去 Step2「重新选择」；信任行 DOM；张数 hint 节点；2b 进阶 `<details>`；模式卡副文案；2b CTA 文案 |
| `templates/studio/homepage-v2/css/import-wizard.css` | 信任行、warn 摘要、thumb tip、进阶 details、关闭确认无关（用 studio-modal） |
| `templates/studio/homepage-v2/import-wizard.js` | 核心逻辑：张数桶、失败展开、预填、关闭确认、摘要样式类、埋点、CTA 文案切换 |
| `templates/studio/homepage-v2/import-sheet.js` | **已删除**（RETIRE P3） |
| `travelogue/web/studio_handlers/import_handlers.py` | A1-07：preview 可选返回 `dateStart`/`dateEnd`（轻量扫描） |
| `travelogue/web/studio_pipeline.py` | `sample_album_preview_thumbs` 或并列 helper 产出日期范围 |
| `tests/e2e/test_import_wizard_v3_playwright.py` | 扩 AC-A1 用例（或新文件 `test_import_wizard_a1_playwright.py`） |
| `tests/unit/web/test_studio_home_v2.py` | DOM 冒烟：信任行 id、进阶 details、无 back-confirm |
| `docs/PRD-IMPORT-WIZARD-A1-DELTA.md` | 决议栏回填 |
| `docs/studio-homepage-v2/TELEMETRY.md`（若存在） | 新事件登记 |

---

## 4. 任务勾选

### M-A1-0 · 基线核对

| ID | 任务 | 文件 / 动作 | 依赖 | 状态 |
|----|------|-------------|------|------|
| IW-0a | 本地跑 `test_import_wizard_v3_playwright.py`，记录失败 AC | tests | — | ✅ |
| IW-0b | 对照 v3 PRD §12 / §16 列「已绿 / 缺口」表进本文件附录 | docs | IW-0a | ✅ |
| IW-0c | ~~确认 flag 默认 false~~ → **作废**（flag 已删） | config | — | ⛔ |
| IW-0d | 本清单 + A.1 PRD §8 决议按 §0.2 回填 | docs | — | ✅ |

### M-A1-1 · P0 壳与文案（A1-01 / 04 / 05 / 06 + A1-13）

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| IW-A1-01 | 移除 `#v2-wizard-back-confirm`；头栏改非 split；「更换」保留并 `aria-label` | html / css / js | — | ✅ |
| IW-A1-04 | Step 2 / 2b 主 CTA 下增加信任行 DOM + 样式 | html / css | — | ✅ |
| IW-A1-05 | 选夹/路径/上传失败：`#v2-wizard-more-import` 强制 `open` + focus 路径输入 | js | — | ✅ |
| IW-A1-06 | 模式卡副文案改为 A.1 表（快速/精细） | html | — | ✅ |
| IW-A1-13 | 2b 主 CTA 文案 →「按这些偏好开始 →」（mode 仍 fine_craft） | html / js | — | ✅ |
| IW-A1-01t | 单测/冒烟：DOM 无 `v2-wizard-back-confirm`；有信任行 id | unit | IW-A1-01/04 | ✅ |

### M-A1-2 · 验货提示 + 2b 进阶折叠（A1-02 / 03）

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| IW-A1-02a | 2b HTML：首屏仅名称/地点/一句话+chips；其余包进 `#v2-wizard-advanced` details | html | — | ✅ |
| IW-A1-02b | 进阶 toggle 埋点 `advanced_fields_toggle`；草稿恢复时若进阶字段非空可保持折叠（不强制展开） | js | IW-A1-02a | ✅ |
| IW-A1-02c | 视觉：折叠态仍满足 sticky 底栏；确认 AC-IW-02 不因 2b 回归（2b 允许滚） | css | IW-A1-02a | ✅ |
| IW-A1-03a | 验货区下 `#v2-wizard-count-hint`；`<4` / `>300` 文案；preview 中/超时不显示 | html / js | — | ✅ |
| IW-A1-03b | 埋点 `photo_count_hint_show`；**不** disable 开始按钮 | js | IW-A1-03a | ✅ |
| IW-A1-02t | 断言：默认 details 关闭；展开后密度/模板等字段仍在 DOM 且进 payload | unit / e2e | IW-A1-02a | ✅ |

### M-A1-3 · P1（A1-07 / 08 / 09 / 10）

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| IW-A1-07a | preview 响应增加可选 `dateStart`/`dateEnd`（ISO date；扫样或首尾 mtime/EXIF，**2s 预算内**，失败则省略） | py pipeline / handlers | — | ✅ |
| IW-A1-07b | 进 2b：名称←`folderName`（用户未改过才覆盖）；日期← preview 范围 | js | IW-A1-07a | ✅ |
| IW-A1-07c | 单测：preview JSON 含/不含日期；超时降级仍 200 | unit | IW-A1-07a | ✅ |
| IW-A1-08 | thumbs：`tabindex=0` + `title`/可见 tip（第 n 张 · basename）；click 无 Lightbox | html / css / js | — | ✅ |
| IW-A1-09a | 脏检查：2b 字段快照 diff **或** 照片开关非默认 | js | — | ✅ |
| IW-A1-09b | × / Esc → `studioModal` 确认；保留写 session 草稿 / 丢弃清草稿；**scrim 点击若关闭则走同一路径** | js | IW-A1-09a | ✅ |
| IW-A1-09c | 埋点 `close_confirm`：`keep` / `discard` / `cancel` | js | IW-A1-09b | ✅ |
| IW-A1-10 | 摘要行非默认加 `v2-wizard__photo-summary--warn`；文案按 A.1 表 | css / js | — | ✅ |

### M-A1-4 · 测试 · 埋点 · 回归

| ID | 任务 | 文件 | 依赖 | 状态 |
|----|------|------|------|------|
| IW-T-01 | E2E：AC-A1-01～05（头栏/折叠/张数/信任/失败展开） | e2e | M-A1-1/2 | ✅ |
| IW-T-02 | E2E：AC-A1-06～10（文案/预填/tip/关闭/warn 摘要） | e2e | M-A1-3 | ✅ |
| IW-T-03 | E2E：AC-IW-DS-01～07 回归（DS-08 作废） | e2e | M-A1-* | ✅ |
| IW-T-04 | ~~E2E：AC-IW-11 flag off → 旧 Sheet~~ → **作废** | e2e | — | ⛔ |
| IW-T-05 | 视口：AC-IW-01/02 + 信任行存在时 Step2 折叠态仍无滚（冲突则信任行改 CTA 内第二行，见 A.1 §5） | e2e | IW-A1-04 | ✅ |
| IW-T-06 | 埋点字段断言（或 harness spy） | e2e / unit | M-A1-3 | ✅ |
| IW-DOC | TELEMETRY / A.1 PRD 状态 → Approved（实施中）· README 链已存在则核验 | docs | — | ✅ |

### M-A1-5 · 默认开启（研发阶段跳过灰度观察）

| ID | 任务 | 动作 | 状态 |
|----|------|------|------|
| IW-G-01 | ~~默认 `import_wizard_v3_enabled: true`~~ → 已删 flag；Wizard 唯一入口 | config / RETIRE | ✅ |
| IW-G-02 | 漏斗 holdback 对比 | telemetry | ⛔ 跳过（研发） |
| IW-G-03 | 5 人走查 | 人工 | ⛔ 跳过（研发） |
| IW-G-04 | 默认 true 已落地；旧 Sheet 删除另立清理单 | 产品 | ✅ 默认 true / 清理另立 |

### A.1.1 · P2（A1-11 / 12 / 14 / 15 / 16）

| ID | 任务 | 状态 |
|----|------|------|
| IW-A1-11 | 2b 分组标题改决策问句 | ✅ |
| IW-A1-12 | chips 按下态 + 2 条高频扩展 | ✅ |
| IW-A1-14 | 回 Step2 CTA「继续编辑细节 →」 | ✅ |
| IW-A1-15 | Step1 首次弱提示（可关、一次） | ✅ |
| IW-A1-16 | 同名 trip 脚注（读 V2.trips） | ✅ |
| IW-T-A11 | E2E `test_import_wizard_a11_playwright.py` | ✅ |

---

## 5. AC ↔ 任务映射

| AC | 主任务 |
|----|--------|
| AC-A1-01 | IW-A1-01 · IW-T-01 |
| AC-A1-02 | IW-A1-02a/b · IW-A1-02t |
| AC-A1-03 | IW-A1-03a/b |
| AC-A1-04 | IW-A1-04 · IW-T-05 |
| AC-A1-05 | IW-A1-05 |
| AC-A1-06 | IW-A1-06 |
| AC-A1-07 | IW-A1-07a/b/c |
| AC-A1-08 | IW-A1-08 |
| AC-A1-09 | IW-A1-09a/b/c |
| AC-A1-10 | IW-A1-10 |
| AC-A1-DS | IW-T-03 |
| AC-IW-01/02 | IW-T-05 · IW-0a |

---

## 6. 建议开工顺序（单人）

1. **IW-0a～0d**（半天）— 确认 v3 不烂尾  
2. **IW-A1-01 + 04 + 06 + 13**（HTML/CSS 先改看得见）  
3. **IW-A1-05 + 03**（JS 容错与提示）  
4. **IW-A1-02***（2b 折叠，注意 payload 回归）  
5. **IW-A1-10 + 08**（易）→ **IW-A1-09***（关闭确认）→ **IW-A1-07***（含后端，可并行）  
6. **IW-T-*** 全绿 → **IW-G-01** 开 dogfood  

---

## 7. A.1.1 后备（已落地）

| ID | 来源 | 说明 | 状态 |
|----|------|------|------|
| IW-A1-11 | A1-11 | 分组标题改决策问句 | ✅ |
| IW-A1-12 | A1-12 | chips 按下态 + 文案扩展 | ✅ |
| IW-A1-14 | A1-14 | 回 Step2 CTA「继续编辑细节 →」 | ✅ |
| IW-A1-15 | A1-15 | 首次弱提示 | ✅ |
| IW-A1-16 | A1-16 | 同名 trip 脚注（读 V2.trips） | ✅ |

---

## 8. 风险

| 风险 | 应对 |
|------|------|
| 信任行撑破 AC-IW-02 | 降级为 CTA 按钮内第二行小字（A.1 §5） |
| EXIF 扫日期拖慢 preview | 预算 2s；超时省略日期，名称预填仍做 |
| 关闭确认过度打扰 | 仅脏状态触发；快速默认路径永不弹 |
| 与旧 Sheet 双维护 | **已消除**（Sheet 物理删除） |
| 2b 折叠漏字段导致 payload 缺键 | IW-A1-02t 强制全键断言 |

---

## 9. 附录 · v3 AC 基线记录（M-A1-0 填写）

> 记录时间：2026-07-12 · Sheet 退役后勘误 · Wizard 唯一入口

| AC | 结果 | 备注 |
|----|------|------|
| AC-IW-01 | ✅ 绿 | `test_ac_iw_01_step1_one_screen_1024x768` |
| AC-IW-02 | ✅ 绿 | `test_ac_iw_02_step2_one_screen_1024x768` |
| AC-IW-04 | ✅ 绿 | `test_ac_iw_04_default_no_visible_checkbox` |
| AC-IW-05 | ✅ 绿 | 抽屉摘要（附带） |
| AC-IW-09b | ✅ 绿 | `test_ac_iw_09b_first_visit_forces_quick_share` |
| AC-IW-11 | ⛔ 作废 | flag / Sheet 已删 |
| AC-IW-15 | ⛔ 作废 | 同上 |
| AC-IW-DS-01～07 | ✅ 绿 | DS-08 作废；其余下游衔接保留 |
| AC-IW-03/08/09 | ✅ 绿 | 验货区 / 日期校验 / 记住精细（本轮补齐） |
| DS-03 / DS-04 | ✅ 绿 | payload 契约 snapshot · Success→预览 200 |
| Flag | ⛔ 已删 | 无 `import_wizard_v3_enabled` / expose |

---

## 10. 版本历史

| 版本 | 说明 |
|------|------|
| **v1.0** | 首版：V3 基线说明 + A.1 P0/P1 任务拆解 + 默认决议 + 里程碑 |
| **v1.1** | Sheet 退役勘误：作废 flag/AC-IW-11/15/DS-08；附录与 §0.3 对齐唯一入口 |
