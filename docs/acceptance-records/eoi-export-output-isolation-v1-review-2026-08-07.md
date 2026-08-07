# PRD-EXPORT-OUTPUT-ISOLATION-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-EXPORT-OUTPUT-ISOLATION-V1.md](../PRD-EXPORT-OUTPUT-ISOLATION-V1.md)（**EOI** · 导出产物独立文件夹） |
| **关联** | [PRD-LONGSHOT-2.0.md](../PRD-LONGSHOT-2.0.md) · [PRD-BATCH-EXPORT-MULTISELECT-V1.md](../PRD-BATCH-EXPORT-MULTISELECT-V1.md) · [PRD-EXPORT-CARD-COMPOSE-V1.md](../PRD-EXPORT-CARD-COMPOSE-V1.md) |
| **评审版本** | PRD **v0.1**（含用户 2026-08-07 已拍板的 D-EOI-02「导出文件」+ D-EOI-05「老数据不处理」）→ Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-08-07 |
| **结论** | **有条件通过（Conditional Go）** |
| **编码** | ☑ **可 Kickoff Stage 1**（`PlatformExportWriter` 四调用点 + 分支 A 落盘路径切换）　□ Stage 2 挡 BLK-EOI-01～02　□ Stage 3 挡 BLK-EOI-04 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD §0～§7 · **对照现网代码**（`longshot.py` · `platform_longshot.py` · `collage_pack.py` · `poster_bric_pack.py` · `photo_grid_pack.py` · `pdf.py` · `packager.py` · `studio_handlers/export_handlers.py`/`common.py` · `tests/unit/export/test_longshot_current.py`） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-07 代码现状核查 + PRD v0.1） |
| **本纪要状态** | **已结案 · Conditional Go** · 待 PRD 回写 |

---

## 0. 会前宣读（主持人）

1. **切口**：本 PRD 只改导出产物的**落盘目的地**（从 `trip_dir` 根目录 → `trip_dir/导出文件/`），不改任何渲染/切分/合成逻辑，不改交互形态。
2. **已拍板，不重开**：子文件夹命名「导出文件」（D-EOI-02）；老游记（测试数据阶段）根目录残留旧产物不迁移、不清理（D-EOI-05）。本场只评估"这两个决策 + 剩余技术方案"是否可开工，不重新讨论命名或是否要迁移旧数据。
3. **本场必拍**：`EXPORT_OUTPUT_DIRNAME` 常量该放哪个模块（避免开发时随意决定造成 import 混乱）；`longshot-current.json` 迁移到子目录后，是否已被 PRD 低估了对既有单测的改动规模；子目录内除产物外仍会残留 `longshot-current.json` 这一个"用户看不懂的文件"，PRD 是否需要显式承认。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：用"改落盘目的地、不改渲染逻辑"收窄改动面的方向正确，`reveal_path_in_folder` 天然复用、无需改 reveal 本身的判断也成立；但 PRD 有两处技术遗漏——(1) 共享常量 `EXPORT_OUTPUT_DIRNAME` 该放在哪个模块未钉死，`platform_longshot.py`/`collage_pack.py`/`poster_bric_pack.py`/`photo_grid_pack.py` 已从 `longshot.py` import 多个符号，`packager.py`/`pdf.py` 目前**不** import `longshot.py`，若不明确落点会导致循环 import 隐患或各写各的重复常量；(2) `tests/unit/export/test_longshot_current.py` 现状是**直接对 `trip_dir` 根目录**做文件读写与路径断言（12+ 处），迁移到子目录不是"调用侧改一行"，是该测试文件的结构性重写，PRD 分阶段计划把它算成了顺带工作量，低估了。这两处不回写会导致实施阶段选错常量落点、或测试改动量估计不足导致排期延误。Stage 1（四个 `PlatformExportWriter` 调用点 + 分支 A 落盘路径）可立即开工；Stage 2 起步前须先关闭 BLK-EOI-01/02。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 用户已亲自拍板命名与老数据策略，产品层面无悬空问题；唯一要求是显式承认"子目录内仍会有 `longshot-current.json` 这一个非图片文件"，不能对外宣称"打开后只有图片"（技术上不完全准确），文案上说"只有你要的照片/文件，没有杂七杂八的工程文件"更准确 |
| **算法** | Go | 与算法逻辑无关，本次改动不触碰任何排版/评分/切分算法，无异议 |
| **架构** | Conditional Go | `EXPORT_OUTPUT_DIRNAME` 落点必须钉死：现状核查 `platform_longshot.py`/`collage_pack.py` 已经 `from travelogue.export.longshot import (...)`，`longshot.py` 未反向依赖 `packager.py`/`pdf.py`——建议常量放在 `longshot.py` 顶层，`pdf.py`/`packager.py` 新增一行 import 即可，方向单一、无循环风险；PRD 现在写"建议放 A 或新建 B"是留白，必须选一个 |
| **开发** | Conditional Go | 现状核查 `tests/unit/export/test_longshot_current.py`：`(trip_dir / "京都-长图.png").write_bytes(...)`、`(trip_dir / LONGSHOT_CURRENT_NAME).write_text(...)` 等 setup/断言全部假定"清单与产物在 trip_dir 根目录"，改动落地后这个测试文件里 12+ 处路径都要跟着挪——这不是 PRD §6 Stage 2 里"调用侧改一行"能覆盖的工作量，需要单独排期，且要检查是否有其它测试文件（`test_longshot_batch.py`/`test_card_bookends.py`/`test_export_zip_budget.py` 等）也有类似的路径假设，一并核查 |
| **测试 / QA** | Conditional Go | 同意开发席对测试规模的判断；补充 AC：Stage 3 回归时需要一条"reveal 后打开的目录里，文件清单 = {本次+历史产物} ∪ {`longshot-current.json`}，不含任何 `.js`/`.css`/`.html`"的端到端断言，而不是只测"文件写到了哪个路径"这种单元级断言——否则会出现"单测全绿但用户点开文件夹仍看到别的东西"的假绿 |
| **视觉 / 排版** | Go | 不涉及任何渲染/几何/裁切逻辑，与本席无关，无异议 |
| **用户体验 · 狗粮** | Conditional Go | 方向完全解决用户原始痛点（20+ 工程文件 → 0 个）；但要求 Stage 3 上线前**真机点一次「在文件夹中显示」**，肉眼确认子目录内容，而不是只看代码 diff——尤其要确认 `longshot-current.json` 残留是否真的"不打扰"（多数用户大概会直接忽略一个 json，但需要实测而非假设） |

**汇总**：**七席 7/7 Conditional Go/Go**（其中 5 席 Conditional Go，2 席 Go 无异议）。

- **Stage 1**：✅ 可立即 Kickoff（四个 `PlatformExportWriter` 调用点 + 分支 A 落盘路径切换，纯路径改动，无逻辑变化）。
- **Stage 2**：BLK-EOI-01/02 关闭前不批开工（常量落点未定、测试改动规模未预算）。
- **Stage 3**：BLK-EOI-04 关闭前不批合入宣称 Done。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **9** | 用户痛点→现网代码核查→修复点定位链条完整，reveal 逻辑复用判断准确 |
| 与既有系统边界 | **8** | 明确不改渲染/命名逻辑，边界清楚；唯一模糊点是常量落点未选定 |
| 工程可开工性 | **6** | Stage1 干净；但测试改动规模被低估，直接开工 Stage2 容易延期 |
| AC 可测性 / 防假绿 | **6** | AC-EOI-01～07 方向对，但缺"目录内容端到端断言"这一条，容易假绿 |
| 用户可感知一致性 | **8** | "只有产物、没有工程文件"基本成立，唯一瑕疵是 `longshot-current.json` 残留需显式承认 |

---

## 3. 事实核查（对照现网）

| # | 断言 | 会中核查 |
|---|------|---------|
| **F-01** | `platform_longshot.py`/`collage_pack.py` 已经 `from travelogue.export.longshot import (...)` 大量符号（`_BROWSER_POOL`/`LongshotExportError`/`_longshot_file_stem` 等） | ✅ 属实（`platform_longshot.py:30` 起、`collage_pack.py` 同类 import） |
| **F-02** | `packager.py` 当前**不** import `travelogue.export.longshot`，也不 import `PlatformExportWriter` | ✅ 属实（仅 `from travelogue.export.exif import write_asset_to_zip`） |
| **F-03** | `longshot.py` 未反向 import `packager.py` | ✅ 属实（grep 无匹配），常量放 `longshot.py` 顶层对 `packager.py`/`pdf.py` 是单向依赖，无循环风险 |
| **F-04** | `tests/unit/export/test_longshot_current.py` 的用例直接对 `trip_dir` 根目录写文件、断言 `LONGSHOT_CURRENT_NAME` 路径 | ✅ 属实，抽样：`(trip_dir / "京都-长图.png").write_bytes(...)`、`(trip_dir / LONGSHOT_CURRENT_NAME).write_text(...)`、`assert not (trip_dir / LONGSHOT_CURRENT_NAME).exists()` 等 12+ 处 |
| **F-05** | `reveal_path_in_folder`（`longshot.py:1331`）在 Windows 下用 `explorer /select, <路径>`，只依赖传入路径本身，不假设目录内容 | ✅ 属实，PRD"reveal 逻辑无需改"的判断成立 |
| **F-06** | `_LONGSHOT_UPLOAD_RESERVED_NAMES`（`longshot.py:454`）已包含 `longshot-current.json` | ✅ 属实，产物迁移到子目录后该校验按文件名匹配依旧生效，无需新增子目录专属保留名 |
| **F-07** | `handle_reveal`（`export_handlers.py:1063` 起）校验 `target.relative_to(trip_dir.resolve())` | ✅ 属实，子目录路径仍在 `trip_dir` 内，校验逻辑无需改 |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-08** | `PlatformExportWriter.commit()` 对同名文件采用"存在则 unlink 再 rename"覆盖式写入 | → 与本次改动无关（既有行为），确认迁到子目录后覆盖式写入语义不变，不会因为目录变化产生"新旧文件并存"的额外副作用 |
| **F-09** | 迁移后，子目录内除图片/PDF/zip 产物外，仍会有 `longshot-current.json` 这一个非产物文件 | → PRD 需在 §2 目标/§7 结论里显式承认这一点，不能宣称"绝对只有图片"，用户体验席已在 §2 提出对应要求 |

---

## 4. 全场共识

1. 本次改动是"换落盘目的地"，不是"重构导出管线"，方向和范围收窄都成立。
2. `reveal_path_in_folder`/`rel_to_trip`/`handle_reveal` 三处均**不需要改动**，只要写入路径本身正确即可，PRD 的判断经代码核查成立。
3. `EXPORT_OUTPUT_DIRNAME` 常量**钉死放在 `travelogue/export/longshot.py` 顶层**（与 `LONGSHOT_CURRENT_NAME` 相邻定义），`pdf.py`/`packager.py` 新增一行 import；不新建独立模块，减少一次不必要的文件拆分。
4. `tests/unit/export/test_longshot_current.py` 的改动是**结构性重写**，需要单独列入分阶段计划的工作量，不能算作"调用侧顺手改"。
5. 子目录内会残留 `longshot-current.json`，这是**已知且可接受**的瑕疵（1 个清单文件远好于 20+ 个工程文件），但 PRD 措辞不能夸大为"绝对纯净"。
6. D-EOI-02（命名「导出文件」）与 D-EOI-05（老数据不处理）均维持用户原拍板，本场不重开。

---

## 5. Must-Fix（阻塞）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-EOI-01** | `EXPORT_OUTPUT_DIRNAME` 常量落点 | PRD §3.1/§3.2 明确写死：常量定义在 `travelogue/export/longshot.py`（与 `LONGSHOT_CURRENT_NAME` 相邻），`pdf.py`/`packager.py` 新增 `from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME`；不新建独立模块 | Stage 2 | ⏳ 待回写 |
| **BLK-EOI-02** | `test_longshot_current.py` 改动规模显式化 | PRD §6 分阶段计划补一条：`tests/unit/export/test_longshot_current.py` 需结构性重写（全部路径 setup/断言迁移到子目录），并核查 `test_longshot_batch.py`/`test_card_bookends.py`/`test_export_zip_budget.py` 是否有同类路径假设，一并列入 Stage 2 工作量 | Stage 2 | ⏳ 待回写 |
| **BLK-EOI-03** | `longshot-current.json` 残留的措辞承认 | PRD §2 目标 G-EOI-02 / §7 验收标准补充说明："导出文件"子目录内除产物外仍会有 1 个 `longshot-current.json` 权威清单文件；这是已知设计，不算违反"只看到产物"的目标 | Stage 1 | ⏳ 待回写 |
| **BLK-EOI-04** | 端到端目录内容回归项 | AC-EOI-02 补充为可执行断言："reveal 后目标目录的文件列表 = 历史+本次产物 ∪ {`longshot-current.json`}，且不包含任意 `.js`/`.css`/`.html`/`trip.json`" | Stage 3 | ⏳ 待回写 |

**Should-Fix（不阻塞 Stage 1）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-EOI-01** | 分享 zip / PDF / 图片混在同一子目录，是否会让用户对"哪个文件发给谁"产生新的小困惑（如需要，可后续拆二级子目录） | 待上线后观察真实反馈，v1 不做 |
| **SHD-EOI-02** | Stage 3 上线前实机点一次「在文件夹中显示」，肉眼确认子目录内容（不仅是代码 diff / 单测通过） | 待 Stage 3 狗粮 |

---

## 6. 拍板 D / OQ（锁定）

| ID | 结论 |
|----|------|
| D-EOI-02（命名「导出文件」） | ✅ 维持（用户已拍板，本场不重开） |
| D-EOI-05（老数据不处理） | ✅ 维持（用户已拍板，本场不重开） |
| D-EOI-01（常量落点） | **本场钉死**：`travelogue/export/longshot.py`（BLK-EOI-01） |
| D-EOI-06（PDF/zip 纳入统一子目录） | ✅ 维持 |
| OQ-EOI-02（未来真实用户历史数据迁移脚本） | 未关闭，明确不阻塞本次实施，留待正式上线前重新评估 |
| OQ-EOI-03（子目录内说明文案） | 未关闭，非必需，留作后续小优化 |

---

## 7. 结论栏

| 项 | 结果 |
|----|------|
| **Conditional Go** | ✅ |
| **可 Kickoff Stage 1** | ✅ 立即（四个 `PlatformExportWriter` 调用点 + 分支 A 落盘路径切换） |
| **可 Kickoff Stage 2** | ❌ 待关闭 BLK-EOI-01/02 |
| **可 Kickoff Stage 3** | ❌ 待关闭 BLK-EOI-04 |
| **No-Go** | 无 |

---

## 8. 会后动作

1. 回写 PRD → **v0.2.0**（本纪要链接 · BLK-EOI-01～04 回写 · Conditional Go 状态）。
2. `docs/DOC-STATUS.md` / `docs/README.md` 补登记本评审记录。
3. Stage 2 开工前，工程侧先确认 BLK-EOI-01/02 已在 PRD 落字；Stage 3 前确认 BLK-EOI-04。
4. 不在本轮重开命名（D-EOI-02）或老数据处理策略（D-EOI-05）的讨论（均为用户已拍板）。

---

## 9. 签字栏（模拟联评）

| 席位 | 表决 | 日期 |
|------|------|------|
| 产品 | Conditional Go | 2026-08-07 |
| 算法 | Go | 2026-08-07 |
| 架构 | Conditional Go | 2026-08-07 |
| 开发 | Conditional Go | 2026-08-07 |
| 测试 / QA | Conditional Go | 2026-08-07 |
| 视觉 / 排版 | Go | 2026-08-07 |
| 用户体验 · 狗粮 | Conditional Go | 2026-08-07 |
