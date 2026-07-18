# Travelogue · 狗粮修复包 V1 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-DOGFOOD-UX-FIXPACK-V1.md](./PRD-DOGFOOD-UX-FIXPACK-V1.md) **v0.2** |
| **评审** | [acceptance-records/dogfood-ux-fixpack-v1-review-2026-07-18.md](./acceptance-records/dogfood-ux-fixpack-v1-review-2026-07-18.md) |
| **验收** | 落地后补 `ACCEPTANCE-DOGFOOD-UX-FIXPACK-V1.md`（对照 PRD §9） |
| **状态** | **M1–M3 主路径 ☑ · e2e 可补** |
| **更新** | 2026-07-18 |

---

## 落地原则

1. **修断链，不扩面**：不改导出门面结构、不碰 TPC/mosaic/cover scoring、不做 R5.1。  
2. **输出域 ≠ 叙事 intent**：平台确认只写 prefs / resume /（可选）`trip.output`；服务端 Recipe 复核。  
3. **标题防噪不可破坏**：用户改名同写；读取仍走 `resolve_display_title()`。  
4. **M1 可独立合入**：出口看跨层四断言（payload · job · 产物 · screens[]）。  
5. **测试隔离**：临时 `trips_dir`、`_free_port()`、显式 `gcs_poster_bric`；勿依赖本机 8766 / 用户 `config.yaml`。

---

## 摸底结论（开工前已知）

| 发现 | 含义 |
|------|------|
| `longshot.js` 已有 `_applyDraft` → `writeExportPrefs` → `syncLongshotCtaLabel` | P-DFX-01 更可能是 **poster_bric 未进映射/CTA 表** 或 **startExport 未读 confirmed prefs**，而非完全没有确认写入 |
| 后端 `export_handlers` / `longshot.py` 已支持 `platform=poster_bric` → BRIC，且有 screens 指纹校验 | M1 后端旁路基本可用；重点修前端确认→提交贯通 + flag 双拒 |
| `first-success.js` 将主/次按钮都设为同一 `url` | P-DFX-06 根因明确：次按钮需改点击处理器，而非改文案 |
| `resolve_display_title()` 承担防噪 | D2 迁移必须带噪声判定，禁止盲覆写 |
| 按章导出中途 PNG→JPG | R1.4 须在 `longshot.py` 做 job 级 format，不能只改扩展名 |

---

## 里程碑总览

| 里程碑 | 目标 | 估时 |
|--------|------|------|
| **M1** | 海报所选即所得 + 弹层可完成（含 Sheet） | 1.5～2.5 人日 |
| **M2** | 改名传播 + 成功态 + 格式统一 | 2～3 人日 |
| **M3** | 移动门面 + FTUE + 提示打磨 | 1.5～2 人日 |

---

## M1 · P0 止血

### 文档 / 合同

| ID | 任务 | 状态 |
|----|------|------|
| DOC-DFX-01 | PRD v0.2 + 本清单 + 评审纪要回写 | ☑ |
| DOC-DFX-02 | M1 合入后补 ACCEPTANCE 中 AC-01～04 签字栏 | ☐ |

### 前端 · 平台贯通

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| FE-DFX-01 | 审计 `PLATFORM_TO_INTENT` / `ctaLabelForPlatform` / 平台卡是否含 `poster_bric`；补齐映射与文案「导出单屏海报」 | `preview-toolbar/longshot.js` · `output-recipe.js` | ☑ |
| FE-DFX-02 | 钉死 confirmed SSOT：确定只写 prefs；导出只读 prefs（popover 关闭后禁止读 draft） | `longshot.js` `resolveExportPlatform` / start export | ☑ |
| FE-DFX-03 | 设置入口展示「当前将导出：…」；drafting 时主按钮保持上一 confirmed | 导出 popover UI | ☑ |
| FE-DFX-04 | fail-closed：confirmed ≠ payload → 阻止 + `export_platform_mismatch` | `longshot.js` | ☑ |
| FE-DFX-05 | `gcs_poster_bric` off：不渲染海报卡（以 `/config` 或 recipe API 为准） | popover 平台列表 | ☑ |

### 前端 · 弹层适配

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| FE-DFX-10 | popover `max-height` + 内容 `overflow-y:auto` + 底栏 sticky | 预览工具栏 CSS | ☑ |
| FE-DFX-11 | `<560px` 全屏 Sheet；焦点陷阱、Esc、背景滚动锁 | `longshot.js` + CSS | ☑ |
| FE-DFX-12 | 确定按钮始终可点；确定后断言 prefs.platform 已变 | 同上 | ☑ |

### 后端 · 复核

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-DFX-01 | `poster_bric`：flag off → 明确错误码；on → BRIC；screens 指纹导出前后一致（加固现有） | `export_handlers.py` · `poster_bric_pack.py` | ☑ |
| BE-DFX-02 | Recipe resolve 与请求 `platform`/`intent` 不一致时拒绝或纠偏（选 **拒绝 + 日志**） | `export_handlers.py` | ☑（既有 CONFLICT + 前端 intent 同步） |

### 测试 · M1 门禁

| ID | 任务 | 状态 |
|----|------|------|
| QA-DFX-01 | Node：平台↔intent↔CTA 映射（含 poster） | ☑ `tests/js/longshot-export-panel.test.mjs` |
| QA-DFX-02 | pytest：poster on/off、PNG+sidecar、screens 指纹（扩展现有 `test_poster_bric_pack.py`） | ☑ + `E_GCS_POSTER_DISABLED` handler 测 |
| QA-DFX-03 | Playwright：选海报→确定→导出→四层断言；1272×675 + 1280×800 + `<560` | ☐ 手测/后续补 e2e |
| QA-DFX-04 | 至少 1 个非海报平台反向回归（确认 wechat_chat 不误走海报） | ☑ 映射互逆 + CTA 默认仍「发微信群」 |

**M1 出口**：AC-DFX-01～04 全绿；QA-DFX-01～04 过；手测分享达人脚本「选海报得海报」。

---

## M2 · 一致性

### 命名

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-DFX-10 | 改名保存路径同写 `title`+`displayTitle`；副标题规则不含旧 title | `apply_intent` / `save-copy` | ☑ |
| BE-DFX-11 | 渲染面统一用 resolve 后的展示名；覆盖 mobile/present/longshot/`<title>`/alt | 既有 `assemble.resolve_display_title`；写路径修复后自动跟随 | ☑ |
| BE-DFX-12 | 存量迁移：§0.3 判定 + 保存落盘 + decision_log 幂等；预览不静默写盘 | `migrate_stale_display_title` + `rename_propagation_migrated` | ☑ |
| FE-DFX-20 | 「一句话」IME 安全保存 + ✓ 反馈 + 去向文案 + 热刷新 | `drawers.js` · `inline-edit.js` · `features.js` | ☑ |

### 成功反馈 / 格式

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| FE-DFX-30 | succeeded：Dock/主按钮 done/书架徽标刷新 + toast + reveal；文案含「此游记文件夹」 | `longshot.js` · task-dock | ☑（书架徽标：发 `travelogue:longshot-export-ready`） |
| FE-DFX-31 | failed：原因 + 重试；不改 confirmed platform | 同上 | ☑ |
| BE-DFX-20 | job 级 `outputFormat`；容量回退整批重捕；取消清理半成品 | `export/longshot.py` | ☑ |
| BE-DFX-21 | 海报固定 PNG 不受 D6 JPG 默认影响 | `poster_bric_pack.py` | ☑ |

### 测试 · M2

| ID | 任务 | 状态 |
|----|------|------|
| QA-DFX-10 | Playwright：改名后各 HTML 面 + trip.json；cover asset/screens 不变 | ☐ 手测/后续补 e2e |
| QA-DFX-11 | pytest：迁移判定正/负例；decision_log 幂等 | ☑ `test_display_title_rename_migration.py` |
| QA-DFX-12 | Playwright：成功/失败/retry/reveal（mock job） | ☐ 手测/后续补 e2e |
| QA-DFX-13 | pytest：同 job 扩展名唯一；取消无半成品 | ☑ `test_longshot_job_format.py` + poster PNG |

**M2 出口**：AC-DFX-05～09 全绿。

---

## M3 · 门面收尾

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| FE-DFX-40 | 拦截页 QR：修资源路径；能力开关；onerror 降级；无能力删位 | `unsupported.js` · `viewport-logic.js` | ☑（无资产删位；有资产仍 onerror 降级） |
| FE-DFX-41 | `<768` 预览需更新条 ≤48px + safe-area | `task-dock.css` · `showPending` | ☑ |
| FE-DFX-42 | 版式差异 tip：5s、每 trip、**版本化** localStorage | `share.js` | ☑ |
| FE-DFX-43 | FTUE「保存长图」：点击触发默认 wechat_chat 导出续跑（query/session） | `first-success.js` · `consumeAutoExport` | ☑ |
| FE-DFX-44 | 示例入口先判重再 import；消除 409；查 studio-event 400 | `import-wizard` · allowlist 同步 | ☑ |
| FE-DFX-45 | 帮助抽屉去掉可见「H1 ·」前缀 | `help-drawer.js` | ☑ |
| FE-DFX-46 | 精修 tip 文案补「点完成退出」（若未落地） | `preview-mode.js` | ☑ |

### 测试 · M3

| ID | 任务 | 状态 |
|----|------|------|
| QA-DFX-20 | Playwright：QR 正常 + 404 降级双路径 | ☐ 手测/后续补 e2e |
| QA-DFX-21 | Playwright：AC-11～14；FTUE 网络无失败 import | ☐ 手测/后续补 e2e |
| QA-DFX-22 | 人工：390 真机截图；Windows reveal 烟测 | ☐ |

**M3 出口**：AC-DFX-10～14 全绿。R5.1 不验收。

---

## 建议最小回归命令（本机）

```text
# Node 映射（路径以实装为准）
npm run test:js -- <platform-mapping-spec>

# pytest 合同
pytest tests/unit/export/test_poster_bric_pack.py -q
pytest <rename-migration / longshot-format 新增> -q

# Playwright（隔离配置注入 gcs_poster_bric）
# 覆盖：海报全链路 · 双/三视口 · 改名 · FTUE 保存长图
```

Actions 额度不足时以本机输出为 M1 证据。

---

## 非目标（再次冻结）

- R5.1 全局 sticky / 章节间距 / screen planner  
- TPC / mosaic template contract / BRIC 选片参数  
- cover scoring / 资产重选  
- 首页书架 IA（P-DFX-16）  
- 移动端完整只读 Studio  

---

## 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-07-18 | 初版实施清单 · 对齐 PRD v0.2 · M1～M3 任务拆解 |
