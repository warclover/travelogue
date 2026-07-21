# IMPLEMENTATION · 敢发面一致性 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-SHARE-FACE-INTEGRITY-V1.md](./PRD-SHARE-FACE-INTEGRITY-V1.md) **v0.2.2** |
| **评审** | [跨职能](./acceptance-records/share-face-integrity-v1-review-2026-07-21.md) · Conditional Go · BLK-SFI-01～10 已回写 |
| **验收** | [ACCEPTANCE-SHARE-FACE-INTEGRITY-V1.md](./ACCEPTANCE-SHARE-FACE-INTEGRITY-V1.md) |
| **手测狗粮** | [share-face-integrity-v1-dogfood-CHECKLIST.md](./acceptance-records/share-face-integrity-v1-dogfood-CHECKLIST.md) |
| **线框** | [wireframes/share-face-integrity-v1-wireframe.html](./wireframes/share-face-integrity-v1-wireframe.html) · F0–F5 |
| **试用底稿** | [persona-blogger-trial-2026-07-21.md](./acceptance-records/persona-blogger-trial-2026-07-21.md) · [persona-deep-trial-2026-07-21.md](./acceptance-records/persona-deep-trial-2026-07-21.md) |
| **相邻硬化** | [PRD-SHARE-FACE-CLOSEOUT-V1.md](./PRD-SHARE-FACE-CLOSEOUT-V1.md)（执行层接管 · 存量兑现） |
| **更新日期** | 2026-07-21 |
| **状态** | **W2 编码中**（F4/F5 已再签）· W0/W1 工程收口 · `feat/share-face-integrity-w0` |
| **估时** | Doc ✅ · W0 ≈ **3–5 人日** · W1 ≈ **4–6 人日**（含 E0）· W2 ≈ **2.5–4 人日**（可砍） |

---

## 0. 波次摘要

| 波次 | 目标 | Go |
|------|------|-----|
| **Doc/Design** | PRD v0.2.0 · 线框 F0–F5 · AC · IMPL · README 索引 | ✅ 2026-07-21 |
| **评审** | 跨职能 Conditional Go；BLK-SFI-01～10 回写 | ✅ 2026-07-21 |
| **W0** | context 过滤 · 存量重渲 · 命名 supersede · 调试串出读者面 | ✅ |
| **W1** | origin 字段 · 刷新替换升级 · 离群双根因 · 分章行内改名 | ✅ 工程收口；手测/狗粮仍开 |
| **W2** | 紧凑档（真实册归因）· 清晰度 · 署名两处同源 · 小红书文案包 | ⏳ 可砍 · DES-SFI-01 ✅ |
| **完成宣布** | 真人 N≥5（观察法协议） | ⏳ AC-SFI-15 |

**所有权**

| 能力 | 所有者 |
|------|--------|
| 禁词实例 / `_WEAK_ENUM` 实现 | **SFC**（`domain/share_face_copy.py`）；本主题 **context 调用 + decorLine 旁路** |
| displayTitle / humanize | **SFC/FST 已合入**；本主题 **存量重渲 + 回归** |
| 章名禁「续」 | **SFC/FST**；本主题回归断言 |
| 导出文件命名（人话） | **本主题**（supersede FTUE D-FTUE-05 / ADR-018） |
| 文案刷新入口 | **本主题**（替换既有 llm 动作）；章名权威归 **Chapter Naming**；sparse 归 **Copy** |
| 时间离群 / 附录章 | **本主题**（不改 ADR-007 章 cap） |
| 成功面栈 / 意图卡 / Recipe | FST / Share-Ready（本主题只回归） |
| 影楼机构 | **不做** |

---

## 1. Doc 波次

| ID | 任务 | 锚点 | 状态 |
|----|------|------|------|
| **DOC-SFI-01** | PRD v0.2.0（评审回写） | `PRD-SHARE-FACE-INTEGRITY-V1.md` | ✅ |
| **DOC-SFI-02** | ACCEPTANCE + fixture | `ACCEPTANCE-SHARE-FACE-INTEGRITY-V1.md` | ✅ |
| **DOC-SFI-03** | IMPLEMENTATION 本文件 | `IMPLEMENTATION-SHARE-FACE-INTEGRITY-V1.md` | ✅ |
| **DOC-SFI-04** | 线框 F0–F5 | `wireframes/share-face-integrity-v1-wireframe.html` | ✅ |
| **DOC-SFI-05** | 狗粮清单 | `acceptance-records/share-face-integrity-v1-dogfood-CHECKLIST.md` | ✅ |
| **DOC-SFI-06** | README / wireframes 索引 | `docs/README.md` · `wireframes/README.md` | ✅ |
| **DOC-SFI-07** | 跨职能评审纪要 | `share-face-integrity-v1-review-2026-07-21.md` | ✅ |
| **DOC-SFI-08** | FTT 侧脚注认可本主题为敢发支线 | `PRD-FINISH-THIS-TRIP-V1.md` **v0.2.1-FTT** · §4.2 / 附录 C | ✅ 2026-07-21 |

---

## 2. W0 任务卡（P0 · 不出糗）

### 2.1 后端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-SFI-01** | `assemble.build_context` 调用 `share_face_copy`；覆盖 decorLine / lead / caption；对象级 `edited` 粗豁免；`stub_hits` 埋点 | `render/assemble.py` · `render/chapters.py` · `domain/share_face_copy.py` | 0.8d | 01·04 | ✅ |
| **BE-SFI-02** | 空图注时不输出 overlay 渐变条；导出态零 inline-edit 占位 | `render` · longshot 模板 | 0.3d | 04 | ✅ |
| **BE-SFI-03** | 导出命名统一 `resolve_display_title`；supersede `{tripId}` stem；含按章 / 平台长图 / 九宫格 / 海报 / **zip 文件名** | `export/longshot.py` · `platform_longshot.py` · `photo_grid_pack.py` · `poster_bric_pack.py` · zip 路径 | 1.0d | 02 | ✅ |
| **BE-SFI-04** | 书架缩略图 glob + `longshot_outputs_stale` 跟新命名；旧产物清理/迁移 | `web/studio_trips.py` | 0.4d | 02·10 | ✅ |
| **BE-SFI-05** | 存量 13 册批量重渲脚本（或首次打开强制重渲门禁）；失败保留旧 HTML | `scripts/sfi_rerender_trips.py` | 0.6d | 01·02 | ✅ |

### 2.2 前端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-SFI-01** | 轨 2 客户端回传命名与 BE 同一规则 | `title-humanize.js` · `longshot-client-fallback.js` | 0.4d | 02 | ✅ |
| **FE-SFI-02** | 精修态 `Plate` / `screen-*` 仅 `?debug=1`；对照帧对齐线框 F0 | `shell.css` · `preview-mode.js` | 0.3d | 03 | ✅ |
| **FE-SFI-03** | W0 间隙期：设置面板「AI 文案」弱化为「已连接 · 新生成的册子将使用 AI 文案」 | `llm-settings.js` | 0.2d | — | ✅ |

### 2.3 测试 / 数据

| ID | 任务 | 估时 | AC | 状态 |
|----|------|------|-----|------|
| **QA-SFI-01** | 抽检脚本：13 册读者面禁入句 = 0（含 decorLine） | `scripts/sfi_share_face_scan.py` · 0.5d | 01 | ✅ 13 册重渲后 scanned=39 hit=0 |
| **QA-SFI-02** | fixture：武大脏名重渲后四处同源；FX-SFI-01～04 | 单测 + demo 抽检 · 0.4d | 02 | ✅ 武大/京都抽检绿；导出名单测绿 |
| **QA-SFI-03** | 回归：SFC AC-SFC-01/03/07/11；stale 主词不回退；FST 忙碌态**前置核验** | 0.4d | 10·11 | ✅ `test_sfi_qa03_contracts.py`（产品手测仍开） |

### 2.4 W0 完成定义

- [x] 线框 F0 对照合入（Plate 门禁 · CSS `data-debug=1`）  
- [x] AC-SFI-01～04 · 10·11 **工程列**绿（产品手测仍开）  
- [x] 武大 / 京都示例分享面抽检无「白天，傍晚」/「示例游记」/ 封面 `--`  
- [x] 导出文件名人话；zip 无 `trip-{id}`（单测）  
- [x] **不**宣称主题完成；设置文案处于间隙期弱化态  

---

## 3. W1 任务卡（P0/P1 · 兑现承诺）

### 3.0 前置（可与 W0 并行）

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-SFI-00** | schema：字段级 `origin: user\|stub\|llm`；修 meta/chapter `edited` 漂移；存量布尔迁移 | `schemas/trip.schema.json` · `copy_patch.py` · `llm_narrate.py` · `domain/copy_origin.py` | 1.0d | 05 | ✅ |

### 3.1 刷新替换升级

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-SFI-04** | 替换「生成杂志感文案」→「重新生成文案」；入口提到整本信息区；确认句按 §4；去掉 LLM/hook 工程词 | `preview-toolbar-v3-sheet.js` · `core.js` | 0.5d | 05 | ✅ |
| **FE-SFI-05** | 提示条并入 task dock；排序 copyRefresh > longshotStale；册级 dismiss；导出/成功面不出 | `preview-toolbar-v3-task-dock.js` · `core.js` · `init-v3.js` | 0.5d | 05 | ✅ |
| **BE-SFI-06** | 刷新：章名走 CN 规则链；图说/开头一句走 Copy sparse；`origin=user` 永不覆盖；全缓冲一次落盘 | `llm_narrate.py` · `chapter_titles.py` · `studio_narrate.py` | 1.0d | 05 | ✅ CN + `scope=frame` 锁定；跳过附录章名 |
| **FE-SFI-06** | E4 落地后恢复设置「已就绪」文案（结束间隙期） | settings | 0.1d | 05 | ✅ |

### 3.2 时间离群

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-SFI-07** | 合并环节硬断言：离群不得并回；`bucket_day_span` 排除离群日期 | `bucket_planning.py` · `chapter_titles.py` | 0.8d | 06 | ✅ |
| **BE-SFI-08** | `_curate_preflight` 打 `timeOutlier`；自适应阈值；多段豁免；附录章不计 cap；coverage 排除 | `curate.py` · `time_outlier.py` · moment/封面池 | 1.0d | 06·09 | ✅ peel + 册尾附录「往年 · 旧照 · N」；长图 CSS 默认不含 |
| **BE-SFI-09** | 读者面 `dateConfidence=low` / 与章 `daySpan` 矛盾时抑制绝对年份 | `render/moment_exif.py` | 0.3d | 07 | ✅ 含 D-SFI-06 矛盾抑年 |
| **FE-SFI-07** | 附录知情：章头 N 张 · 分章列出 · 移回原章 · 导出「未含」提示可勾 | chapter-panel · refine sheet · export · longshot | 0.6d | 09 | ✅ 分章整章移回 + 精修单张「移回原章」；导出 `includeAppendix` |

### 3.3 分章

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-SFI-08** | 分章行内改名 +「重新分章」改名 + 解释句；删死句 | `chapter-panel.js` · `copy_patch` 章名路径 | 0.6d | 08 | ✅ |

### 3.4 W1 测试

| ID | 任务 | 估时 | AC | 状态 |
|----|------|------|-----|------|
| **QA-SFI-04** | 仙本那 / 武大回归 fixture；刷新手改保护；dock 仲裁 | 0.6d | 05～09 | ✅ `tests/fixtures/sfi/*` + demo/refresh/dock 单测 |
| **QA-SFI-05** | LTN 回归：离群后章数变化不破三读法合同 | 0.3d | — | ✅ `test_sfi_ltn_appendix_contract.py` |

### 3.5 W1 完成定义

- [ ] 线框 F1–F3 对照合入（手测）  
- [x] AC-SFI-05～09 工程列：核心单测绿；附录 compose / 导出勾选已接（真人手测仍开）  
- [x] 无并列第二刷新按钮；无裸「重新生成」歧义（「重新分章」/「重新生成文案」）  
- [x] QA-SFI-04/05 工程回归绿  
- [ ] **不**宣称主题完成（W2 / 真人门仍开）  

---

## 4. W2 任务卡（可独立砍）

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **DES-SFI-01** | **前置**：真实照片册长图归因表签字（非 demo-album） | 验收记录附件 | 0.3d | 12 | ✅ 仙本那基线 10.4% · [签字记录](./acceptance-records/share-face-integrity-v1-des01-attribution-2026-07-21.md) |
| **FE-SFI-09** | 紧凑档：章头瘦身 / 封面去重 / moment 折叠；进 B3 双预览；不跳 B2 | `longshot.css` · density · chapter_items | 1.0d | 12 | ✅ `export.longshotDensity` + CSS/折叠；导出面板切换→save-copy 重渲 |
| **FE-SFI-10** | 清晰度档位参数与产物换算一致 | export settings UI | 0.3d | 13 | ✅ 标准·856 / 更清晰·1284（428×scale） |
| **FE-SFI-11** | 署名三态册级字段；同步 `cover-closing` + `longshot-boundary-footer` | 精修·这本 · 模板 | 0.5d | 13 | ✅ `worksBrandMode/Text` 同源 |
| **FE-SFI-12** | 小红书成功面文案包（dock 展开）；无 Key = 标题+话题 | task-dock · OQ-2 | 0.5d | 13 | ✅ dock「复制文案包」；无正文时仅标题+话题 |
| **QA-SFI-06** | 像素占比脚本 + 盲评记录模板 | 0.4d | 12 | ✅ `--baseline` 对比 + [盲评模板](./acceptance-records/share-face-integrity-v1-compact-blind-TEMPLATE.md) |

### W2 完成定义

- [x] 线框 F4–F5 再签（2026-07-21 产品同意）  
- [x] 归因表已签（DES-SFI-01 · 仙本那）；AC-SFI-12·13 **产品手测/盲评**仍开  

---

## 5. 主题完成门

| ID | 任务 | 状态 |
|----|------|------|
| **DOG-SFI-01** | 真人 N≥5 按 ACCEPTANCE 操作化协议执行 | ⏳ |
| **DOC-SFI-08** | FTT 脚注认可 | ✅ 2026-07-21 |

---

## 6. 非目标 / 禁区（编码纪律）

- 不新建第三套禁词表；不 LLM invent 章名；不改 ADR-007 章 cap（附录不计）。  
- 不重开成功面 / 意图卡 / Recipe。  
- 不做影楼批量 / 白标 / 锁模板。  
- W0 过滤器禁止对最终 HTML 全文多模式回溯正则。  
- 离群 layout 重排耗时不记入「识别 <2s」预算。  

---

## 7. 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.6 | 2026-07-21 | W2：FE-09～12 + QA-06；F4/F5 再签；紧凑档/署名/清晰度诚实标宽/小红书文案包 |
| v0.1.5 | 2026-07-21 | 补漏：rerender 真写 longshot · 精修单张移回 · D-SFI-06 矛盾抑年 · §6/§7 · QA-SFI-03；[gapfill 记录](./acceptance-records/share-face-integrity-v1-gapfill-2026-07-21.md) |
| v0.1.4 | 2026-07-21 | DES-SFI-01：仙本那真实册长图归因签字（基线非照片 10.4%）；`sfi_longshot_attribution.py` |
| v0.1.3 | 2026-07-21 | QA-SFI-04/05：瘦 fixture 回归；实质多段豁免；章名禁拼回离群日；sparse scope 尊重 origin=user |
| v0.1.2 | 2026-07-21 | W1 收口：BE-06～09 · FE-07/08 · 附录章 + 长图默认不含 + 移回豁免 · 离群核心中位数邻域 |
| v0.1.1 | 2026-07-21 | W0 编码开工：BE-01～05 · FE-01～03 · 抽检/重渲脚本 · 武大/京都抽检绿 |
| v0.1.0 | 2026-07-21 | 首版 · 对齐 PRD v0.2.0 · Doc 包齐 · Ready for Kickoff W0 |
