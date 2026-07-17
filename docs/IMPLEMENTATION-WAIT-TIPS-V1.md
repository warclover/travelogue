# IMPLEMENTATION · 导入等待教育 Wait Tips V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md) **v0.2.0** |
| **评审** | [跨职能](./acceptance-records/wait-tips-v1-review-2026-07-17.md) · Conditional Go · MF 已回写 |
| **验收** | [ACCEPTANCE-WAIT-TIPS-V1.md](./ACCEPTANCE-WAIT-TIPS-V1.md) |
| **手测狗粮** | [wait-tips-v1-dogfood-CHECKLIST.md](./acceptance-records/wait-tips-v1-dogfood-CHECKLIST.md) |
| **线框** | [wireframes/wait-tips-v1-wireframe.html](./wireframes/wait-tips-v1-wireframe.html) · F1–F5 |
| **文案润色** | [acceptance-records/wait-tips-v1-copy-workshop-2026-07-17.md](./acceptance-records/wait-tips-v1-copy-workshop-2026-07-17.md) |
| **更新日期** | 2026-07-17 |
| **状态** | **W0+W1 编码 ✅** · 手测狗粮待填 · W2（帮助重播）可选 |
| **估时** | W0 ≈ **1.5–2.5 人日** · W1 ≈ **0.5–1 人日** · W2（可选）≈ **0.5 人日** |

---

## 0. 波次摘要

| 波次 | 目标 | Go |
|------|------|-----|
| **Doc/Design** | PRD · 线框 · 三席文案 · 跨职能评审 · AC · 相邻脚注 | ✅ 2026-07-17 Conditional Go |
| **W0** | Importing 壳嵌入 6 卡 · 10s 轮播 · 关闭持久化 · 核心埋点 · 与 FST/Help 仲裁 | ✅ 2026-07-17 |
| **W1** | 短等待抑制（D-WT-07）· `prefers-reduced-motion` · 埋点补齐 | ✅ 同批合入 |
| **W2（可选）** | 帮助抽屉「重播等待提示」清 dismiss | ⏳ 非挡门 |

**所有权**

| 能力 | 所有者 |
|------|--------|
| Wait Tips 组件 · Importing 嵌入 · dismiss 持久化 · 埋点 | **本主题** |
| 导入进度主句 / 慢安抚 / FirstSuccess ≤1s | **First-Session Trust**（不改合同） |
| 忙碌态零 L1 / Help seen | **Help**（Tips **不写** Help seen；见 Help v1.1.3） |
| 能力卡 idle only | FTUE / Desktop LLM（Importing 时不展示；见 FTUE v1.1.2） |
| 长图 Dock 教育 | **不做**（D-WT-09） |

---

## 1. Doc / 评审波次

| ID | 任务 | 锚点 | 状态 |
|----|------|------|------|
| **DOC-WT-01** | PRD Outcome-first 六张 + 铁律 | `PRD-WAIT-TIPS-V1.md` → **v0.2.0** | ✅ |
| **DOC-WT-02** | 线框 F1–F5 | `wireframes/wait-tips-v1-wireframe.html` | ✅ |
| **DOC-WT-03** | 三席润色纪要 | `acceptance-records/wait-tips-v1-copy-workshop-2026-07-17.md` | ✅ |
| **DOC-WT-04** | README / 线框索引 | `docs/README.md` · `wireframes/README.md` | ✅ |
| **DOC-WT-05** | 本实施清单 | 本文 | ✅ |
| **DOC-WT-06** | 跨职能评审 Conditional Go | `wait-tips-v1-review-2026-07-17.md` | ✅ |
| **DOC-WT-07** | 拆 ACCEPTANCE + dogfood | `ACCEPTANCE-WAIT-TIPS-V1.md` · dogfood | ✅ |
| **DOC-WT-08** | Help D-HELP-08′ 脚注 | `PRD-HELP-ONBOARDING-V1.md` **v1.1.3** | ✅ |
| **DOC-WT-09** | FST 边界脚注 | `PRD-FIRST-SESSION-TRUST-V1.md` **v1.0.3** | ✅ |
| **DOC-WT-10** | FTUE 时段脚注 | `PRD-FTUE-OPTIMIZATION-V1.md` **v1.1.2** | ✅ |
| **DOC-WT-11** | 评审模板备查 | `wait-tips-v1-review-TEMPLATE.md` | ✅ |

**Doc 完成定义**

- [x] 跨职能 Conditional Go · MF 回写  
- [x] OQ-WT-01～05 已关闭  
- [x] §4 文案为唯一字符串源  
- [x] 相邻脚注齐  

---

## 2. 建议模块切分

| 模块 | 路径（建议） | 职责 |
|------|--------------|------|
| **Copy 表** | `templates/studio/homepage-v2/wait-tips-copy.js` | WT-01～06 = PRD §4 v0.2.0 · `COPY_VERSION` |
| **控制器** | `templates/studio/homepage-v2/wait-tips.js` | mount/unmount · 计时 · 暂停 · dismiss · 埋点 |
| **样式** | `templates/studio/homepage-v2/css/overlays.css` | 卡片次区 · 标签 tone · 窄屏 |
| **宿主钩子** | `templates/studio/homepage-v2/import-run.js` | 挂载点；终态/取消卸载 |
| **分析白名单** | `templates/studio/js/analytics.js` | `wait_tips_*` |
| **契约测试** | `tests/unit/web/test_wait_tips_v1_contracts.py` | 文案禁区 · dismiss · 不碰 Help seen |

**原则**：与 `import-run.js` 解耦；Tips 抛错不得影响进度轮询。

---

## 3. W0 任务卡（✅ 编码）

### 3.1 前端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-WT-01** | 冻结 COPY 表（字面=PRD §4） | `wait-tips-copy.js` | 0.2d | 09 | ✅ |
| **FE-WT-02** | `renderImportingPanel` 挂载 Tips（主句下 / 取消上） | `import-run.js` · overlays.css | 0.3d | 01 | ✅ |
| **FE-WT-03** | 轮播 10s（首张可 12s）· ‹ › · 圆点 | `wait-tips.js` | 0.4d | 02 | ✅ |
| **FE-WT-04** | 悬停/focus 暂停；取消 Modal 时暂停 | `wait-tips.js` | 0.2d | 03 | ✅ |
| **FE-WT-05** | × → localStorage dismiss；已 dismiss 不 mount | `wait-tips.js` | 0.2d | 04 | ✅ |
| **FE-WT-06** | ≥2s 显现；终态立刻 unmount | `import-run.js` | 0.3d | 05 | ✅ |
| **FE-WT-07** | 不写 Help seen；不触发 L1/能力卡 | 审查 | 0.1d | 06 | ✅ |
| **FE-WT-08** | A11Y：roledescription · live · 关闭可聚焦 | `wait-tips.js` | 0.2d | §7 | ✅ |
| **FE-WT-09** | 埋点 allowlist：show / manual_nav / dismiss | `analytics.js` | 0.2d | §6 | ✅ |
| **FE-WT-10** | 视觉对齐线框 F1 | overlays.css | 0.2d | F1 | ✅ |

### 3.2 测试

| ID | 任务 | 估时 | AC | 状态 |
|----|------|------|-----|------|
| **QA-WT-01** | 契约：六张字面 · 禁区词 · WT-02 标题 | 0.3d | 07 · 09 | ✅ `test_wait_tips_v1_contracts.py` |
| **QA-WT-02** | dismiss key 语义 | 0.2d | 04 | ✅ |
| **QA-WT-03** | 手测 dogfood F1–F5 | 0.3d | 01～06 | ⏳ |
| **QA-WT-04** |（建议）Playwright：Tips 出现与成功后消失 | 0.3d | 01 · 05 | ⏳ |

### 3.3 W0 完成定义

- [x] 线框 F1/F3 对照合入  
- [x] AC-WT-09 契约绿；01～06 待手测  
- [x] Tips 失败时进度壳完整（try/catch）  
- [x] **不**改 FST 进度 / FirstSuccess 合同  

---

## 4. W1 任务卡（✅ 编码）

| ID | 任务 | 估时 | AC | 状态 |
|----|------|------|-----|------|
| **FE-WT-11** | D-WT-07 短尾不 advance | 0.3d | 10 | ✅ `notifyWaitTipsJob` |
| **FE-WT-12** | prefers-reduced-motion 关自动播 | 0.2d | 08 | ✅ |
| **FE-WT-13** | 埋点 auto_advance / pause / suppress | 0.1d | §6 | ✅ |
| **QA-WT-05** | W1 手测 | 0.2d | 08 · 10 | ⏳ |

---

## 5. W2 任务卡（可选）

| ID | 任务 | 估时 | 状态 |
|----|------|------|------|
| **FE-WT-14** | Help 抽屉「重播等待提示」清 dismiss | 0.4d | ⏳ |
| **DOC-WT-12** | Help 重播入口非 L1 脚注 | 0.1d | ⏳ |

---

## 6. 埋点清单

| 事件 | W0 | 属性 |
|------|----|------|
| `wait_tips_show` | ✅ | `card_id`, `job_stage`, `elapsed_ms` |
| `wait_tips_manual_nav` | ✅ | `from_id`, `to_id`, `dir` |
| `wait_tips_dismiss` | ✅ | `card_id`, `viewed_count`, `elapsed_ms` |
| `wait_tips_auto_advance` | ✅ | `from_id`, `to_id` |
| `wait_tips_pause` | ✅ | `card_id`, `reason` |
| `wait_tips_suppress_short_wait` | ✅ | `job_stage` |

| Key | 值 |
|-----|-----|
| `travelogue.waitTips.dismissed` | `"1"` |
| `travelogue.waitTips.version` | 与 COPY 表同步 |

---

## 7. Kickoff 检查单

- [x] 跨职能 Conditional Go · MF 回写  
- [x] §4 文案无未决争议  
- [x] ACCEPTANCE / dogfood 已拆  
- [x] Help / FST / FTUE 脚注已回写  
- [ ] 分支 `feat/wait-tips-v1-w0`（编码时建）  
- [ ] 指定非实现者手测人  

---

## 附录 A · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-17 | 初版实施清单 |
| v0.2.0 | 2026-07-17 | Doc 波次收口 · Conditional Go · 对齐 PRD v0.2.0 · 可 Kickoff W0 |
| v0.3.0 | 2026-07-17 | W0+W1 编码：copy/ctrl/host/css/analytics/契约单测 |
