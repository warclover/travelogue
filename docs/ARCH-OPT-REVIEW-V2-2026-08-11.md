# 架构治理 PRD V2 评审报告 · 2026-08-11

> 评审对象：[PRD-ARCH-OPTIMIZATION-V2.md](./PRD-ARCH-OPTIMIZATION-V2.md)（v2.0.0 草案）
> 评审方式：架构 / 开发 / 算法 / 测试四位专家并行评审，均要求实际重跑命令、读代码核实证据，不接受纸面复述；评审后由主评审对四份报告的分歧点二次实测仲裁
> 配套文档：[ARCH-OPT-REVIEW-2026-07-09.md](./ARCH-OPT-REVIEW-2026-07-09.md)（上一轮评审）· [PRD-EQUAL-GRID-ADMISSION-V1.md](./PRD-EQUAL-GRID-ADMISSION-V1.md) · [ega-equal-grid-admission-v1-review-2026-08-04.md](./acceptance-records/ega-equal-grid-admission-v1-review-2026-08-04.md)

---

## 一、总体判断

**四位专家结论一致：有条件通过。** M2-A（P0 止血窗口）的核心证据——`chapter_titles.py` 分层违例、`pytest --fast` 41 failed 的分布、`tests/integration/p17/*` marker 早退根因——经四份独立评审逐条实测复核，**全部准确**，可以直接进入实施。

但四位专家**在同一个问题上高度收敛**：PRD §5.1（M2-B1）对 LSE 跨包边棘轮上调机制的技术描述与代码实际不符，提出的解药打不到真实发生过的漏洞。这本身是一个意味深长的案例——**PRD 试图治理"治理机制失效"，却在起草自己的治理机制时犯了同样的"证据未经复核"的错误**。此外还发现 §1.1 用来支撑"god-module 棘轮机制已验证有效"这一核心论点的对照数据本身有误（`curate.py` 当前实测正处于该棘轮的 REGRESSION 状态），以及若干范围外的新发现（`tsc:preview-toolbar` 门禁当前也是红的；`.trip.lock` 跨进程锁其实已经实现，`ARC2-11` 的问题描述是基于过期文档而非代码实况）。

**本报告已据评审发现完成对 PRD 的修订（v2.0.0 → v2.1.0）**，详见 §四。

---

## 二、四位专家评审摘要

| 专家 | 结论 | 核心贡献 |
|------|------|----------|
| 架构 | 有条件通过 | 精确定位 `--fast` marker 早退的代码根因（`conftest.py` 两个循环顺序颠倒）；发现 `services/narrative_brief.py` 是被 PRD 忽略的隐藏消费方；发现 `_asset_cities` 助手函数遗漏在下沉清单外；指出 M2-C1"mosaic 构造"命名与既有 `layout_engine/mosaic/` 包概念冲突 |
| 开发 | 有条件通过 | 发现 `.trip.lock` 跨进程锁（`_CrossProcessTripLock`）已经实现，ARC2-11 描述有误；发现 `tsc:preview-toolbar` 门禁当前也是红的（14 处错误，PRD 未提及）；发现 `secrets.json`/`studio-instance.json` 早已被 `.gitignore` 覆盖，不构成入库风险；核实 M2-C2 对 `homepage-v2/` 的 tsc 报错量级估算过低（实测 300+ 处） |
| 算法 | 有条件通过 | 把 18 个 `layout_engine` 失败的根因从"共享 fixture 漂移"重新定性为 EGA 等权宫准入功能变更（2026-08-03～08-05 落地）与既有不变量测试的真实交互缺口；发现 4 条 LSE 边是零风险转发 shim，可直接下沉消边；指出 `ingest_into_trip` 拆分的两处隐式状态/时序风险 |
| 测试 | 有条件通过 | 独立复现 41/4247 的完整分布并逐文件核对，确认 marker 早退是真实实现 bug；指出 4 个新增门禁脚本自身缺单测；指出 AC2-09 缺重放次数埋点；给出"golden 漂移 vs 真实回归"的可操作判定流程建议 |

四位专家**均独立发现**（未互相参考）同一处关键漏洞：`scripts/lint_lse_cross_import.py` 当前**没有** `--allow-growth` 参数（该参数只存在于 `lint_csc_god_module_ratchet.py`），LSE 基线历史上的上调是直接手改基线 JSON 文件完成的（`commit 68d8aafa`，一次性改写了 4 个治理基线文件），与 PRD 原文的机制描述不符。

---

## 三、主评审二次实测仲裁（存在专家间分歧或需裁定的点）

| 分歧点 | 各方说法 | 仲裁实测 | 结论 |
|--------|----------|----------|------|
| `curate.py` god-module 行数 | 架构/算法/开发/测试四方一致：实测已超基线（REGRESSION） | `python scripts/lint_csc_god_module_ratchet.py` → `REGRESSION: curate.py 1986 > 1974` | **确认**：PRD §1.1"未超基线"的结论错误，采纳 |
| `studio_pipeline.py` 行数 | 架构/算法/测试称实测 1181（与基线打平）；PRD 原文称 1034（优于基线） | 同上命令 → `studio_pipeline.py: 1181 lines (ceiling 1181)` | **确认**：1181 打平，PRD 的 1034 数字来源不明，予以订正 |
| `lint_lse_cross_import.py` 是否有 `--allow-growth` | 四方一致：不存在 | 读脚本源码 + `findstr /C:"allow-growth" /C:"allow_growth"` 全文无匹配 | **确认**：不存在，采纳 |
| `.trip.lock` 跨进程锁是否已实现 | 开发专家称已实现（`_CrossProcessTripLock`） | `travelogue/services/trip.py:133-176` 确认类存在，`update()` L541 内 `with thread_lock, _CrossProcessTripLock(path):` 包住 CAS 读-改-写区间 | **确认**：已实现，ARC2-11 原表述（基于 `ARCH-OPT-STATUS.md` 陈旧记录）有误，采纳并订正 |
| `tsc:preview-toolbar` 门禁现状 | 开发专家称当前也是红的（14 处错误） | 实测 `npm run tsc:preview-toolbar` → exit code 2，14 处 `TS2339`/`TS2307`，跨 5 个文件 | **确认**：采纳，新增 P0 问题 ARC2-13 |
| `config.yaml.example` 行数 | 算法/测试/开发三方称实测 757 行，与 PRD 787 行不符 | 用两种独立方法复核：`(Get-Content config.yaml.example).Count` 与 `python -c "len(open(...).readlines())"`，均得 **787**；`git log` 确认文件最后改动于 08-10，工作区无未提交差异 | **不采纳**：三位专家的 757 这一测量结果本次复核未能复现，**787 予以保留**，不修改 PRD 原数字 |
| LSE 边数历史轨迹 | 各方给出的序列不完全一致（"两次上调"／"8→7→18→5→13"） | `git log -p` 追溯 `lse-cross-import-baseline.json` 全部提交：`8aac50e2`(8)→`13afd833`(7)→`9522930c`(18)→`910933c0`(5)→`a5558467`(5)→`68d8aafa`(13) | **确认**：真实轨迹是 8→7→18→5→13，PRD 原文"两次上调（7→8→13）"表述不准确，采纳修订 |

---

## 四、PRD 修订处置摘要（v2.0.0 → v2.1.0）

| # | 评审发现 | 处置 |
|---|----------|------|
| 1 | M2-B1 对 LSE 棘轮上调机制的"作案手法"描述与代码不符 | **重写 §5.1**：明确脚本当前无 `--allow-growth`、`--update-baseline` 已会拒绝任何增长；真实漏洞是"基线 JSON 可被脚本外的手工编辑绕过校验"；解药改为"CI 内重算 edges 并与 committed baseline diff，检测非脚本产生的手改"，同时补一步"先下沉 4 条已确认零风险的边（`ltn_isolation.py`/`ltn_weekly.py` 改指向 `layout_contract`），把基线从 13 降到 9 再冻结" |
| 2 | §1.1 对照表 `curate.py`/`studio_pipeline.py` 数字有误，且 `curate.py` 当前正处于该棘轮的 REGRESSION 状态 | **订正 §1.1** 表格数字与结论方向；**新增 ARC2-12（P0）**纳入 M2-A（新增 M2-A4） |
| 3 | `tsc:preview-toolbar` 门禁当前也是红的（14 处错误），PRD 完全未提及 | **新增 ARC2-13（P0）**纳入 M2-A（新增 M2-A5） |
| 4 | ARC2-11 关于 `.trip.lock` "仍未处理"的描述基于陈旧的 `ARCH-OPT-STATUS.md` 记录，代码里已实现 | **订正 ARC2-11**：拆分为"`.trip.lock` 已实现（无需处理，仅需补充覆盖面审计）"与"仓库卫生真实项（仅 `README - 副本.md`，`secrets.json`/`studio-instance.json`/`__pycache__` 早已被 `.gitignore` 正确覆盖）"两部分；**M2-C3 改为审计而非新实现** |
| 5 | 18 个 `layout_engine` 失败根因定性错误（"共享 fixture 漂移" → 实为 EGA 功能变更交互缺口） | **重写 §1.3 与 M2-A2 A2b**：明确指向 2026-08-03～08-05 落地的 EGA 等权宫准入变更，要求逐条对照 `PRD-EQUAL-GRID-ADMISSION-V1.md` 评审纪要判断是否为预期副作用，不得批量重签 golden |
| 6 | M2-A1 消费方核查遗漏 `services/narrative_brief.py:121,138` 与助手函数 `_asset_cities` | **补充 §4.1 方案**：re-export 覆盖清单显式加入这两项 |
| 7 | M2-C1 "mosaic 构造"子模块命名与 `layout_engine/mosaic/` 包概念冲突 | **改名**为"经典 screen 构造器（grid5 variants）"，并注明与独立 MCS 引擎的关系 |
| 8 | `ingest_into_trip` 拆分存在闭包共享状态、`F-CLU-CACHE-04` 时序约束两处隐式风险 | **补充 M2-C1 验收要求**：并行 ingest 路径等价性测试 + 锁定/续传路径资产归属回归测试，不能只靠"改动 20 行配单测"的通用规则 |
| 9 | 4 个新增门禁脚本自身无单测要求 | **补充 §7 AC2-13**：对齐 `test_arch_opt_gates.py` 现有模式，每个新脚本各一组正反例 |
| 10 | AC2-09 缺重放次数埋点，无法写出机器可验证断言 | **补充 M2-C3 实现项**：`TripService.update` 暴露重放次数；**新增 AC2-14** |
| 11 | R2-02"golden 漂移 vs 真实回归"判定缺可操作流程 | **重写 R2-02**：补充 commit 定位 → 改前改后对照重跑 → revert 验证的判定步骤；新增 PR 模板锚点字段要求 |
| 12 | AC2-01 引用的验证命令（`python -m importlinter.cli lint-imports`）实测为失效命令（无 `__main__` 分发块，恒定退出码 0） | **订正 AC2-01 与文档头部"评审依据"**：改为 `lint-imports` 控制台脚本或 `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` |
| 13 | AC2-08 扫描口径模糊（全量扫描 vs 仅新增字段） | **明确为 §5.3 全量扫描 + warn-only**，并在 AC2-08 补充 warning 文本稳定子串与 exit code 约定 |
| 14 | M2-C2 对 `homepage-v2/` tsc 报错量级估算过低（实测 300+ 处，远超 `preview-toolbar/` 现有 14 处） | **拆分 M2-C2** 为"接入 CI（warn-only）"与"存量类型错误收敛（机会主义，工作量另计）"两个子项 |
| 15 | `config.yaml.example` 787 行 | 本次复核维持原数字，**不采纳**三位专家的 757 行说法（详见 §三仲裁表） |

四位专家均确认 **M2-A（原有 A1~A3）可以按 PRD 原方案立即执行，不受上述修订阻塞**；新增的 M2-A4/A5 与 M2-A1~A3 一并构成 M2-A 全集。

---

## 五、评审结论

**有条件通过。** M2-A 全部五项（A1~A5）证据扎实，批准立即执行；M2-B/M2-C 已按上表完成修订，形成 v2.1.0，无需重新走完整四方评审，但建议在 M2-A 完成后的下一次进度同步中确认修订内容无遗漏。

---

*评审与修订：Cursor Agent（架构/开发/算法/测试四位专家子代理并行评审 + 主评审二次实测仲裁）· 2026-08-11*
