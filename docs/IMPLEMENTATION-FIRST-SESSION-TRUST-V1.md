# IMPLEMENTATION · 首访可信体验优化 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-FIRST-SESSION-TRUST-V1.md](./PRD-FIRST-SESSION-TRUST-V1.md) **v1.0.2** |
| **评审** | [跨职能](./acceptance-records/first-session-trust-v1-review-2026-07-17.md) · [用户联席](./acceptance-records/first-session-trust-v1-user-panel-2026-07-17.md) · Conditional Go |
| **验收** | [ACCEPTANCE-FIRST-SESSION-TRUST-V1.md](./ACCEPTANCE-FIRST-SESSION-TRUST-V1.md) |
| **手测狗粮** | [first-session-trust-v1-dogfood-CHECKLIST.md](./acceptance-records/first-session-trust-v1-dogfood-CHECKLIST.md) |
| **线框** | [wireframes/first-session-trust-v1-wireframe.html](./wireframes/first-session-trust-v1-wireframe.html) · F1–F5 |
| **更新日期** | 2026-07-17 |
| **状态** | **W0–W2 工程已合入** · 真人手测 / AC-FST-15 未签 · **不得对外宣布主题完成** |
| **估时** | W0 ≈ **2–3.5 人日** · W1 ≈ **2–4 人日** · W2 ≈ **0.5–1 人日**（工程已交付） |

---

## 0. 波次摘要

| 波次 | 目标 | Go |
|------|------|-----|
| **Doc/Design** | 评审 · 线框 · AC · 相邻 PRD 脚注 | ✅ 2026-07-17 |
| **W0** | 可等：进度诚实 · 终端切换 · 导出进度 · 成功面稳定（不教微信 · 不自动弹文件夹） | ✅ 工程 · 手测待签 |
| **W1** | 敢秀：stub 底线 · EXIF · 章名 · 封面/书架回退名 | ✅ 工程 · 手测待签 |
| **W2** | 封底中文化 · 张数同源 | ✅ 工程 · 手测待签 |
| **完成宣布** | 真人 N≥5 | ⏳ AC-FST-15 |

**所有权**

| 能力 | 所有者 |
|------|--------|
| 导入/长图进度诚实 · 终端 UI 切换 | **本主题** |
| 默认长图成功面 COPY（已保存 · 主钮打开文件夹 · 禁教学 · 禁自动 reveal） | **本主题**（supersede FTUE §3.3 发群主句 / Help 默认必现） |
| 发群操作说明（H4 / 帮助抽屉） | **Help**（按需查阅，非默认成功面） |
| 「换种分享方式」入口 | **Share-Ready**（成功面动作区可挂；不改本主题主句合同） |
| 空态 / 示例入口 | FTUE（本主题不重开） |
| 真图样品 / 意图卡 / `kept_n` | Share-Ready |
| stub 深度润色 / 章名算法全案 | Copy / Chapter Naming；本主题只定敢秀底线 |

---

## 1. Doc 波次（可与编码并行 · 部分已做）

| ID | 任务 | 锚点 | 状态 |
|----|------|------|------|
| **DOC-FST-01** | FTUE §3.3 / G-FTUE-04 脚注：默认成功面以本主题 D-FST-04 为准 | `PRD-FTUE-OPTIMIZATION-V1.md` **v1.1.1** | ✅ |
| **DOC-FST-02** | Share-Ready「落盘≠完成」脚注 | `PRD-SHARE-READY-OPTIMIZATION-V1.md` **v1.0.3** | ✅ |
| **DOC-FST-03** | Help：发群说明改为按需查阅 | `PRD-HELP-ONBOARDING-V1.md` **v1.1.2** | ✅ |
| **DOC-FST-04** | README / 线框索引 | `docs/README.md` · `wireframes/README.md` | ✅ |
| **DOC-FST-05** | Share-Ready IMPLEMENTATION / ACCEPTANCE 成功面指针 | `IMPLEMENTATION-SHARE-READY-…` · `ACCEPTANCE-SHARE-READY-…` | ✅ |
| **DOC-FST-06** | 手测狗粮清单 F1–F5 | `acceptance-records/first-session-trust-v1-dogfood-CHECKLIST.md` | ✅ |

---

## 2. W0 任务卡

### 2.1 前端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-FST-01** | 导入轮询：`stage` → 主句映射；N/N 后强制切 curate/narrate/render 文案；慢安抚仅次行 | `homepage-v2/import-run.js` · `import-run-logic.js` | 0.5d | 01～03 | ✅ |
| **FE-FST-02** | `succeeded` 回调内先关忙碌 + `showFirstSuccess`；`refreshTrips` 不阻塞（并行/后置） | `import-run.js` · `first-success.js` | 0.5d | 04～05 | ✅ |
| **FE-FST-03** | 长图进度：禁假 0%；indeterminate + 人话主句；无工程词 | `preview-toolbar/longshot.js` · task-dock busy | 0.4d | 06～07 | ✅ |
| **FE-FST-04** | Task Dock 成功面 COPY §4.4；剥离默认 `publishGuide` 教学句；主钮实心「在文件夹中显示」 | `preview-toolbar-v3-task-dock.js` · `longshot-client.js` | 0.5d | 08 · 08c · 13 | ✅ |
| **FE-FST-05** | **去掉自动 reveal**；仅点击主钮；成功面 ≥3s / 关闭前保持 | task-dock · `shelf-longshot.js` · longshot success 路径 | 0.3d | 08 · 08b | ✅ |
| **FE-FST-07** | 无障碍：忙碌 `aria-busy`；成功面 focus 主钮 | import-run · task-dock · first-success | 0.2d | §8 | ✅ |
| **FE-FST-08** | PRD §7 建议埋点接入 | analytics · import-run · task-dock | 0.3d | §7 | ✅ |

### 2.2 后端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-FST-01** | import job 在 narrate/render 段更新 `stage`/`stageHint`（避免长期 ingest 计数语义） | `studio_pipeline.py` | 0.4d | 01～03 | ✅ |
| **BE-FST-02** | longshot job 进度字段可用，或契约标明「无进度」→ 前端 indeterminate | FE：`pct == null` → indeterminate（契约已合） | 0.2d | 06 | ✅ |

### 2.3 测试（BLK-06）

| ID | 任务 | 估时 | AC | 状态 |
|----|------|------|-----|------|
| **QA-FST-01** | **e2e 必锁**：示例导入 `succeeded` → FirstSuccess 可见且忙碌壳关闭（≤1s / 同轮询） | 0.5d | **04** | ✅ `test_first_session_trust_w0_playwright.py` |
| **QA-FST-02** | 单测/契约：成功面 COPY 无发群教学句；无自动 reveal | 0.3d | 08b · 13 | ✅ |
| **QA-FST-03** | Playwright：长图成功面 ≥3s；主钮文案「在文件夹中显示」 | 0.3d | 08 · 08c | ✅ 同上 |

### 2.4 W0 完成定义

- [x] 线框 F1–F4 对照合入（进度诚实 · 终端切换 · 成功面 · 禁自动 reveal）  
- [x] AC-FST-04 e2e 绿  
- [x] 成功面无发群教学句 · 无自动 reveal（契约单测已绿）  
- [x] **不**宣称主题完成（真人未做）  

---

## 3. W1 任务卡

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-FST-03** | stub/L0 narrate：禁说明书腔；宁可空（OQ-FST-03） | `narrate.py` stub hook/caption/epilogue | 0.5d | 09 | ✅ |
| **BE-FST-04** | 读者面剥离 camera Make/Model 可见图注 | `moment_exif.format_moment_exif_line` | 0.3d | 10 | ✅ |
| **BE-FST-05** | 章名禁「续」；时段 / （2）（3）一字面 | `chapter_titles.py` | 0.4d | 11 | ✅ |
| **BE-FST-06** | 目录名噪音 → `displayTitle`；同步封面 · FirstSuccess · 书架 | `title_humanize` · pipeline · assemble · trips | 0.5d | 12 | ✅ |
| **FE-FST-06** | FirstSuccess / L0 文案勿承诺杂志级（USR-03） | `help-onboarding.js` · capability-card | 0.2d | — | ✅ |
| **QA-FST-04** | 单测：stub 禁词 / EXIF /「续」/ 回退名 | unit | 0.4d | 09～12 | ✅ |
| **QA-FST-05** | 手测狗粮 N≥5（完成宣布见 AC-15） | [dogfood CHECKLIST](./acceptance-records/first-session-trust-v1-dogfood-CHECKLIST.md) | 0.5d | 15 | ⏳ |

### 3.1 W1 完成定义

- [x] 线框 F5 对照（工程底线已合）  
- [x] AC-FST-09～12 工程列绿（手测仍待）  
- [x] 回退名三处一致（封面 / FirstSuccess / 书架同源 `resolve_display_title`）  

---

## 4. W2 任务卡

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-FST-07** | 封底「Colophon」→「辑封」；张数与精选/版面同源 | `cover-closing.hbs` · `build_epilogue_stats` · kept_n | 0.4d | 14 | ✅ |
| **QA-FST-06** | 封底文案 / 张数契约单测 | `test_first_session_trust_w2_colophon.py` · epilogue stats | 0.2d | 14 | ✅ |

---

## 5. 埋点（已接入 · PRD §7）

| 事件 | 用途 | 状态 |
|------|------|------|
| `import_ui_terminal_ms` | 挡 P-FST-02 | ✅ |
| `import_stage_stall` | 挡 P-FST-01（主句 >8s 无变化） | ✅ |
| `longshot_progress_mode` | 挡假 0%（percent \| indeterminate） | ✅ |
| `longshot_success_visible_ms` | 挡成功面闪失 | ✅ |
| `longshot_reveal_auto_blocked` | 断言未自动 reveal | ✅ |
| `share_surface_blocked` | W1：`folder_title` 回退时 | ✅（folder_title） |

---

## 6. 风险（实现时）

| 风险 | 缓解 |
|------|------|
| 与 Share-Ready / FTUE 分支改同一 task-dock | 成功面 COPY 以本主题 §4.4 为准；「换种分享」作次要动作挂载，不改主句 |
| `refreshTrips` 慢拖死 FirstSuccess | FE-FST-02：成功面优先，刷新并行 |
| 自动 reveal 现网多入口 | Dock · 书架 · share · 已禁自动；zip 仍为确认后 reveal |
| stub 改空被评「太素」 | OQ-FST-03 已关闭；空优于假句 |

---

## 7. 签字

| 项 | 日期 | 结论 |
|----|------|------|
| 实施清单初稿 | 2026-07-17 | ✅ 文档 |
| 编码 Kickoff | 2026-07-17 | ✅ W0–W2 工程合入 |
| 真人完成门 AC-15 | — | ⏳ 见 dogfood CHECKLIST |
