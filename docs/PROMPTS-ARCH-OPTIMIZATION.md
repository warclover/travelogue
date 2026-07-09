# 架构优化 PRD 执行提示词集（配套 PRD-ARCH-OPTIMIZATION.md v1.1）

> 用法：每个新窗口执行**一个**里程碑，按顺序复制对应提示词粘贴给 Agent。
> 每条提示词自包含：Agent 会先读 PRD 与状态文件，不依赖历史对话。
> 执行顺序与门禁见 PRD §8.2；WS2 各条受产品 WIP 门禁约束（§8.1），启动前先确认门禁满足。

---

## 0. 通用前置模板（每条提示词已内嵌，无需单独粘贴；如需自由指挥时可单独使用）

```text
你是本项目的架构优化执行工程师。项目：Travelogue（本地照片转 HTML 游记，Python 3.11+，
Studio 为 ThreadingHTTPServer + 原生 ESM 前端，状态存 trips/{id}/trip.json）。

开始任何工作前，按顺序完成：
1. 通读 docs/PRD-ARCH-OPTIMIZATION.md（v1.1），重点 §0.2 范围承诺、§3.2 等价性守护、§3.3 开关删除 DoD。
2. 读 docs/ARCH-OPT-STATUS.md（若不存在则本次创建），确认前置里程碑均为 done。
3. 运行 git status 确认工作区状态，若有与本里程碑无关的未提交改动，先向我报告再继续。

全程硬性约束：
- 零 intentional 功能变更；可接受差异仅限 PRD §0.2 的 DIFF-01~05。
- 改动合并前必须通过：pytest --fast -q 全绿；触碰核心管线时另跑 PRD §3.2 对应门禁层。
- 禁止顺手重构本里程碑范围外的代码；发现范围外问题记入 ARCH-OPT-STATUS.md 的 "发现问题" 区。
- 每完成一个里程碑：更新 docs/ARCH-OPT-STATUS.md（状态、证据命令与输出摘要、遗留项），
  并用一段话向我汇报结果与证据。
- 未经我确认不要 git commit。
```

---

## WS1 · P0 专项窗口（立即执行，顺序：P-00 → P-01 → P-02/03/04 → P-05）

### P-00 · 初始化状态追踪（一次性，1 分钟）

```text
读取 docs/PRD-ARCH-OPTIMIZATION.md（v1.1）§8.2 里程碑总表，创建 docs/ARCH-OPT-STATUS.md：
- 表格列：里程碑 ID | 状态(todo/in-progress/done/blocked) | 完成日期 | 证据摘要 | 遗留项
- 初始所有里程碑为 todo；附 "发现问题" 空区块和 "开关台账" 空区块（记录
  pipeline.orchestration / layout.planner_impl 开关的上线日期，用于 §3.3 的 4 周 DoD 计时）。
完成后把文件内容展示给我确认。
```

### P-01 · M-A0：配置即时修复（0.5d，独立 PR）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-A0（见 §4.2 第一行与 §0.4 ARC-02）。
先读 PRD 相关章节与 docs/ARCH-OPT-STATUS.md 确认状态，再动手。

任务：
1. config.yaml.example 存在两个顶层 `curate:` 键（约 L28 与 L426），PyYAML 后者覆盖前者。
   合并为一段：逐键核对两段内容的归属与默认值，对照 travelogue/config/ 下各 *_from_dict
   工厂确认每个键的真实消费位置；不确定归属的键单独列出问我。
2. 统一 deterministic_strict 双源优先级：mosaic.deterministic_strict 与
   clustering.deterministic_strict 并存（mosaic/trip.py 约 L57 有取值逻辑）。查清当前实际
   生效语义，在 config.yaml.example 注释与 docs 中写明优先级规则，勿改运行时行为。
3. 若用户本地 config.yaml 也有重复键，一并提示我（不要直接改我的 config.yaml）。

验收：
- python -c "import yaml; yaml.safe_load(open('config.yaml.example', encoding='utf-8'))" 通过，
  且全文件无重复顶层键（写个临时脚本检测）。
- pytest --fast -q 全绿。
- load_config() 加载合并后的 example 与合并前的“后段生效值”逐字段一致（写一次性对比脚本验证，
  证明本次合并没有改变实际生效配置——这是零行为变更的证据）。

完成后更新 ARCH-OPT-STATUS.md 并汇报。硬性约束：零 intentional 功能变更；范围外问题只记录不修。
```

### P-02 · M-A1a：TripService.update + revision 字段（1.5d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-A1a（见 §4.1.1 与 §4.1.4）。
先读 PRD §4.1 全节、docs/adr/008-trip-storage-boundaries.md §3（revision 乐观锁已 Accepted）、
travelogue/services/trip.py、travelogue/util/datetime_.py，以及 ARCH-OPT-STATUS.md。

任务：
1. TripService 新增 update(trip_json_path, mutator, *, max_retries=3) 原子接口：
   - per-trip threading.Lock 注册表：key = os.path.normcase(str(path.resolve()))，
     模块级锁保护 double-checked 插入，注册表进程全局（不绑实例）。
   - CAS 语义：锁内 load → 记录 meta.revision（缺省视为 0）→ mutator(trip) → revision+1 → save；
     save 时磁盘 revision 与快照不一致则重放 mutator，重试耗尽抛 TripConflictError。
   - updatedAt 统一在 save 内赋值（用 util.datetime_.utc_now_iso）。
2. schemas/trip.schema.json 增加 meta.revision（integer，可选，缺省 0），确认
   additionalProperties 约束下新字段合法。
3. 单测：CAS 重放、重试耗尽抛错、revision 单调递增、路径大小写归一（Windows）、
   注册表并发插入。放 tests/test_trip_service_update.py。

不改任何现有调用方（那是 A1b-d 的事）。验收：pytest --fast -q 全绿 + 新单测全绿 +
python scripts/validate_trip.py 对 fixture 全量通过（revision 字段不破坏 schema）。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-03 · M-A1b：handlers + serve.py 收口（1.5d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-A1b（见 §4.1.2 改造清单）。
前置：M-A1a 已 done（查 ARCH-OPT-STATUS.md）。先读 PRD §4.1、travelogue/web/serve.py、
travelogue/web/studio_handlers/ 下全部 handler。

任务：把以下裸 load+save 全部改为 svc.update(path, mutator)：
1. studio_handlers/trip_intent_handlers.py 6 处（L66/119/225/266/288/333 附近）。
2. studio_handlers/ 其余 8 处：trip_pipeline / trip_list / trip_replan / trip_moment /
   asset_media / template_handlers；其中 trip_moment_handlers.py L59-61 自写 updatedAt 的
   逻辑删除（update 内统一赋值）。
3. web/serve.py save-copy（L226 附近）与 promote-tier（L257 附近）：改 svc.update 并删除
   模块级 _trip_write_lock；关键要求——现在锁内做的 rerender 必须移出临界区
  （先 update 写回，再在锁外 rerender），这是 PRD 评审明确的延迟回归风险点。
4. mutator 内只放合并逻辑，禁止在 mutator 内做 render / 网络 / 耗时计算。

409 前端契约（PRD §4.1.5 DIFF-01）：TripConflictError → HTTP 409 E_STUDIO 错误码体系
（参考 web/studio_errors.py 现有模式）；前端 js/http.js 的 PATCH 封装对 409 E_TRIP_CONFLICT
自动重试 1 次，仍失败 toast 提示（参考 withJobBusyRetry 现有实现风格）。

验收：pytest --fast -q 全绿；跑 tests/ 中 studio handler 相关测试（-k "intent or moment or
replan or tier or copy"）全绿；手动冒烟——启动 studio，inline edit 与 intent PATCH 均正常。
完成后更新 ARCH-OPT-STATUS.md 并汇报（列出每处改动的文件与行号）。
```

### P-04 · M-A1c：pipeline / on_persist / 子进程 CAS（1.5d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-A1c（见 §4.1.2 与 §1.2 第三行跨进程场景）。
前置：M-A1a/b 已 done。先读 travelogue/web/studio_pipeline.py（重点 L566-736 的 5 处 save 与
on_persist 回调）、travelogue/web/studio_subprocess.py、travelogue/web/studio_narrate.py。

任务：
1. studio_pipeline.py 5 处 save + on_persist partial ingest 写路径改 svc.update。
   注意：on_persist 是 ingest 中途高频写，是 CAS 竞争最激烈路径；mutator 设计为
   "合并本批新增 assets 与 ingest 进度字段"，可安全重放。
2. studio_narrate.py 1 处收口。
3. 子进程 CAS 验证：import 走 multiprocessing spawn（studio_subprocess.py），确认子进程内
   TripService 锁注册表独立无碍（CAS 跨进程生效靠 revision，不靠线程锁）；写一个集成测试：
   subprocess worker 循环 update 期间，主进程并发 PATCH 同一 trip，断言双方写入均不丢失、
   冲突方正确重放或 409（这是 AC-ARC-02 的测试雏形，标 @pytest.mark.integration）。
4. 长事务约定自查：ingest/curate 全程不持锁，仅写回窗口进临界区（PRD §4.1.2 末段）。

可选（时间允许）：.trip.lock 文件锁补强 import 写窗口，规格严格按 PRD §4.1.1 表格
（子进程独立 open、msvcrt.locking 锁第 0 字节、LK_NBLCK + 指数退避 ≤2s、stale >10min 弃、
不可用时回退纯 CAS 不得静默降级）。若做不完就跳过并在 STATUS 记录，CAS 本身已是完整保护。

验收：pytest --fast -q 全绿；新集成测试在本机通过；完整跑一次 studio import 流程
（可用 tests/fixtures 下小相册）成功且 trip.json revision 单调递增。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-05 · M-A1d+e：render/orchestrator 收口 + lint + 压测（2.5d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-A1d 与 M-A1e（见 §4.1.2/4.1.3/§7 AC-ARC-01）。
前置：M-A1a/b/c 已 done。先读 travelogue/render/engine.py（L697-705 update_pipeline 写 status）、
travelogue/orchestrator/run.py（L87-88 save 闭包）。

任务：
1. render/engine.py 与 orchestrator/run.py 的 save 收口为 svc.update；CLI 零散 save 顺手收口。
2. 写 scripts/lint_trip_save_calls.py（AST）：`svc.save(`/`.save(trip` 仅允许出现在
   services/trip.py 内部；附正反例 fixture 测试；接入 .github/workflows/ci.yml 的 lint job。
3. 并发压测实现 AC-ARC-01：16 线程 × 200 次 svc.update，每个 mutator 写唯一键
   mutations.{thread}.{seq}，最终集合比对（非时序断言）；支持 --stress-iterations 参数；
   标 @pytest.mark.integration；同时把 M-A1c 的跨进程测试完善为 AC-ARC-02 正式用例。
4. 检查现有 tests/test_trip_concurrent_save.py：它用的是 PRD 要消灭的裸 load+save 反模式，
   改写为走 svc.update（保留原子写文件的断言）。

验收：AC-ARC-01/02 测试通过（本机 Windows 上必须跑过——PRD 明确 CI 是 ubuntu，Windows 语义
要本地验证）；lint 脚本对当前仓库全绿（证明收口彻底）；pytest --fast -q 与
pytest -m integration -q 全绿。
完成后更新 ARCH-OPT-STATUS.md（M-A1 整体标 done）并汇报，附压测输出摘要。
```

### P-06 · M-A2：配置 fail-loud（1d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-A2（见 §4.2，M-A0 已完成 example 修复部分）。
前置：M-A0 done。先读 travelogue/config/loader.py 与 config/ 下各 *_from_dict 工厂。

任务：
1. 重复键检测：自定义 yaml.SafeLoader 子类（构造映射时发现重复键抛 ConfigError，消息含键名
   与行号），load_config 启用。
2. 未知键告警：各 *_from_dict 消费后收集剩余键，load_config 末尾聚合为单条
   logger.warning("config: unknown keys: ...")；新增 config.strict 布尔配置（默认 false），
   true 时未知键升级抛 ConfigError。phase6、template_admin 等动态子键段声明 allow_extra 豁免。
3. 注意 camelCase/snake_case 双轨键（patch_config_file 有映射表）：双轨合法键不得误报。

验收（对应 AC-ARC-03/04）：
- 构造含重复键的临时 yaml → ConfigError 含行号（写成单测）。
- 含未知键 curate.fooo → 单条聚合 warning；strict=true 抛错（单测）。
- 存量 config.yaml.example 在 strict=false 下零告警（回归单测，评审要求）。
- pytest --fast -q 全绿。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-07 · M-A3：仓库卫生（0.5d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-A3（见 §4.3）。

任务：
1. .gitignore 增加 travelogue/layout_templates/registry.cache.json 与 trips/.cache/。
2. 排查 git status 中 templates/studio/homepage-v2/import-wizard.js 同时出现正斜杠与反斜杠
   两个条目的问题（疑似 git index 路径异常）：用 git ls-files 核实，修复索引。
   注意：该文件是 Import Wizard v3 开发热区，只修 git 索引，绝不动文件内容。
3. 根目录遗留 log/PNG（pytest-full.log、studio-import-error.log 等）：核对 ignore 规则，
   未覆盖的补规则；已提交的历史文件不动。

验收：git status 干净可读（无生成物噪音）；git check-ignore 验证新规则生效；不产生任何
源码 diff。完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-08 · M-B5：lint_trip_json 落地（1d，提级进 WS1）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-B5（见 §4.4）。
先读 docs/adr/008-trip-storage-boundaries.md（denylist 分类与体积阈值的原始出处）。

任务：
1. 写 scripts/lint_trip_json.py：
   - Denylist：embedding 向量、全量 decision log、base64 blob 等字段模式（按 ADR-008 分类表）。
   - 体积：单 trip.json warn 512KiB / fail 2MiB。
   - 输出机器可读 JSON + 人读摘要，exit code 语义清晰。
2. 接入 CI：.github/workflows/ci.yml validate job 对 tests/fixtures 全量 trip fixture 跑；
   scripts/e2e_trip_acceptance.py 增加对真实 trip 的调用点。
3. 单测覆盖 AC-ARC-11：注入超体积字段 → warn/fail 分级正确；注入 denylist 字段 → fail。

验收：现有全部 fixture 通过 lint（若有存量违规，列清单问我如何处置，不要自行改 fixture）；
pytest --fast -q 全绿；CI yaml 语法有效。
完成后更新 ARCH-OPT-STATUS.md 并汇报。WS1 至此全部完成，请在汇报中给出 WS1 总结。
```

---

## WS2 · P1 结构收敛（启动前必须逐条确认 §8.1 产品 WIP 门禁）

### P-09 · M-B0：等价门禁 + 分层基线 + TECH-ARCH 增量（2d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-B0（见 §3.2 与 §5.3.3、§5.4）。
先读 PRD §3.2 全节（含 3.2.2 实现规格表——这是逐条实现清单）、scripts/phase7_nr_collect.py、
tests/_golden/helpers.py 的 layout_snapshot、travelogue/render/dom_compare.py。

任务：
1. 写 scripts/arch_equivalence_check.py，严格按 PRD §3.2.2 规格：
   - 规范化 profile（deterministic_strict、parallel_embed=false、batch_size=0、
     fixture 预置 embedding cache 或 heuristic-only）。
   - trip.json 剔除字段清单（updatedAt、pipeline.timings.*、runs[].startedAt/finishedAt、
     embedStats.elapsedMs、decision log wall-clock、LSE weightsHash——按 PRD 表逐条）。
   - 浮点 round(x,6) / isclose(rel_tol=1e-9)；json sort_keys=True；列表不重排。
   - L3b 复用 layout_snapshot + dom_signature；禁止 HTML 逐字节。
   - 输出 JSON diff 报告 + exit code。
2. 接入 CI validate job（PR 级 warn：continue-on-error，对齐 phase17 warn/block 模式）；
   核心 fixture 集至少含 trip.render_golden.json + golden-mixed-scenes。
3. import-linter 基线：pyproject.toml 增 [tool.importlinter] 契约（分层按 PRD §5.3.1 DAG），
   §5.3.2 违例清单全量登记为显式豁免；lint-imports 进 CI lint job，当前必须全绿（靠豁免）。
4. TECH-ARCHITECTURE.md 追加 v0.9 增量章节：现行分层图 + PRD 目标图 + 开关台账链接。

验收：arch_equivalence_check 对同一 fixture 跑两次管线（同路径）diff 为空（自反性冒烟）；
lint-imports 全绿；CI yaml 有效；pytest --fast -q 全绿。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-10 · ADR-015：LSE 迁移决策文档（1d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的前置项 ADR-015（见 §5.2.0）。
先读：docs/PRD-PHASE17-layout-strategy-engine.md 的 R-P17-04、docs/adr/010（D5）、
docs/adr/ 现有 ADR 的格式惯例，以及 layout_engine/ 与 curation/screen_planner* 的现状。

任务：写 docs/adr/015-lse-planner-migration.md：
1. 声明对 R-P17-04（MCS 留 curation）与 ADR-010 D5（渐进+adapter 薄包装）的 supersede 范围。
2. 量化判据：先实测当前 layout_engine ↔ curation 的 cross-import 边数（写脚本统计并附结果），
   写明 "迁移后须下降 ≥80%，kernel 抽取后测算达不到则维持 adapter 方案、关闭 M-B4b"。
3. 两步路线（§5.2.1/5.2.2 摘要）、回退路径（layout.planner_impl 开关）、compose_trip 与
   layout_search.py 的归属裁定（PRD Q-06，给出你的分析与建议）。
4. 状态标 Proposed，向我汇报等待批准——ADR 未获我批准前 M-B4b 不得启动（M-B4a 可以）。

验收：ADR 格式与既有 13 篇一致；cross-import 统计脚本与数据附在 ADR 或 scripts/ 下。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-11 · M-B2：编排差异矩阵 + StudioProfile 设计（5-7d，Go/No-Go 门禁）

```text
【启动前确认】PRD §8.1 G-WIP-01：Import Wizard v3 全量 AC 已通过？未通过则停止并告知我。

执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-B2（见 §5.1 全节）。
先读：travelogue/web/studio_pipeline.py 全文、travelogue/orchestrator/run.py 全文、
travelogue/orchestrator/studio_hooks.py、docs/AGENT-ARCHITECTURE.md 中关于
run_trip 不跑聚类的章节、PRD §1.3 已知 12 项差异清单。

任务分两个交付物：
1. S1 差异矩阵（写入 docs/ARCH-ORCH-DIFF-MATRIX.md）：
   - 逐项盘点 studio_pipeline.py 手写编排 vs run_trip 的全部差异（以 PRD §1.3 的 12 项为
     起点，源码逐行核对补全，特别是 ingest 参数组：parallel embed / featuredDir / resume /
     generate_crops / keep_near_duplicates / rollout 解析）。
   - 每项标类别：Studio 特化（吸收进阶段机）/ 漂移（以 Studio 为准修正 CLI——注意基准是
     Studio 不是 CLI，PRD §5.1.1）/ telemetry（等价性检查中可剔除）。
   - 矩阵完成后停下来向我做 Go/No-Go 汇报：若存在 G1/LSE rollout 级深度分歧，建议延期 M-B3。
2. 我确认 Go 后，做 S2 设计与实现：
   - StudioProfile dataclass（ingest 选项组、clustering 开关、G1 分支、preview 产物开关）。
   - StudioHooks 扩展（进度/计时/阶段回调，按矩阵需求定），现有仅 1 个 on_stage 回调。
   - run_trip 阶段序加入 clustering 一等 stage（内部调 run_clustering_layer，参数可关）。
   - 新 hook 与 profile 的单测（progress 回调、timing 上报为最低用例）。
   - 本里程碑不切换 studio_pipeline 调用路径（那是 M-B3）。

验收：差异矩阵经我确认；pytest --fast -q 全绿；run_trip 带 clustering stage 后对 fixture
的产物与 "手动前置 run_clustering_layer + 旧 run_trip" 一致（用 arch_equivalence_check 验证）。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-12 · M-B3：编排切换 + legacy 开关（3-5d）

```text
【启动前确认】M-B2 已 done 且我已 Go；G-WIP-01 仍满足。

执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-B3（见 §5.1.2 S3/S4 与 §3.3）。

任务：
1. studio_pipeline.py 切换为 run_trip(from_stage="ingest", profile=StudioProfile(...),
   hooks=...)；旧手写路径完整保留，挂 pipeline.orchestration: unified|legacy 开关
  （默认 unified）。
2. 等价验证按 AC-ARC-06v2 两阶段：
   - 第一阶段：同一 fixture，legacy Studio 路径 vs unified 路径，arch_equivalence_check
     L3a/b/c 全部通过。
   - 第二阶段：unified vs CLI travelogue run，同样全过。
   两阶段报告都贴进汇报。
3. 约束自查：进度事件类型/顺序/payload schema 不变（DIFF-05 仅允许时间间隔变化）；
   pipeline.timings 与 embedStats schema 不变；G1 分支与 preview jpg 行为不变。
4. CI：默认只跑 unified；新增每周定时 job 双跑对比（PRD §3.3）。
5. 在 ARCH-OPT-STATUS.md 开关台账登记 pipeline.orchestration 上线日期（4 周 DoD 计时起点）。
6. 跑全量：pytest --fast、-m integration、studio 相关 e2e（含 import 全流程 Playwright）。

完成后更新 ARCH-OPT-STATUS.md 并汇报。若任何等价性 diff 非空，停止切换、保持 legacy 默认，
把 diff 报告给我。
```

### P-13 · M-C4：领域视图层（2d，与 M-B2 同期可拉起）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-C4（见 §6.1，注意评审已提级：
应在 M-B3 前或同期完成）。前置：M-A1 done。
先读 travelogue/services/pipeline_state.py、travelogue/domain/pipeline.py。

任务：
1. domain/ 下建三个视图模块（函数集 + TypedDict，不持状态、不缓存，输入输出仍是 trip dict）：
   - pipeline_view.py：status 读写、runs[] 追加、阶段断言——把 services/pipeline_state.py
     的逻辑迁入并在原位置留 re-export（这同时完成 §5.3.2 curation→services 违例的一半）。
   - assets_view.py：按 id 索引、tier 读写、featured 提升。
   - chapters_view.py：chapters/screens 遍历与常用查询。
2. 防半吊子约束：扩展 scripts/lint_trip_save_calls.py（或新 lint）：handlers/services 内
   对 trip["pipeline"] 等高频路径的直接下标赋值报错，必须走视图函数；存量违规登记豁免清单
   渐进清零（本次至少把 M-A1 已收口的文件改干净）。
3. 视图层单测：状态转换边界、revision 协同。

验收：pytest --fast -q 全绿；lint 对新代码生效；import-linter 无新违例。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-14 · M-B4a：kernel 抽取 + adapter 收敛 + mosaic ContextVar（3d）

```text
【启动前确认】ADR-015 已提交（我批准与否只影响 M-B4b，本项可先行）。

执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-B4a（见 §5.2.1）。
先读：travelogue/layout_contract/、travelogue/layout_engine/adapter.py、
travelogue/curation/mosaic/runtime.py（L9-43 全局 override）、mosaic/hook.py（L21-22 的
ContextVar 既有模式）、curation/screen_planner_attach.py。

任务：
1. kernel 抽取：AspectKind、layout_constraints、screen_layout_state 等 planner 与 LSE
   双向依赖的共享原语抽入 layout_contract/（保持纯类型+纯函数，无状态）；原位置留 re-export。
2. adapter 收敛：ChapterPlanRequest DTO 扩为规划入口完整参数面；
   screen_planner_attach ↔ adapter 三角依赖改单向（attach 经 adapter）。
3. mosaic ContextVar（必选）：runtime.py 的 _mosaic_cfg_override 与 _disabled_pattern_ids
   由模块级 global 改 ContextVar，与 hook.py 模式对齐；curate.py 中 try/finally 设置点同步改。
   附并发单测：deterministic_strict=True 下双线程各跑 run_curate，断言 override 不串扰
  （PRD 评审 M-02 要求，迁移前基线）。
4. render_contract.py 改名 render_fingerprint.py（原名留 re-export shim）。

硬性验收（AC-ARC-09）：arch_equivalence_check 对 golden fixture 前后 diff 为空；
scripts/phase17_golden_metrics.py 全绿；mosaic decision log 签名一致；并发单测过；
pytest --fast 与 -m mosaic 全绿。任何 diff 非空即停，报告给我。
完成后更新 ARCH-OPT-STATUS.md 并汇报（附 cross-import 边数变化）。
```

### P-15 · M-B4b：planner 物理迁移（4-5d，需 ADR-015 获批）

```text
【启动前确认】ADR-015 已获我批准；M-B4a done；与 M-C2（tests 迁移）无同期进行（PRD R-04）。

执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-B4b（见 §5.2.2）。

任务：
1. git mv：curation/screen_planner.py、screen_planner_stages.py、screen_planner_attach.py
   → layout_engine/planner/（保持三文件边界）；curation/mosaic/ → layout_engine/mosaic/；
   compose_trip 与 layout_search.py 按 ADR-015 裁定处置。
2. 迁移约束「算法语义不变」：允许 import 结构调整（底部 E402 延迟 import、双向 lazy import
   必须重排消解）；禁止改 PATTERN_GRID_CLASS 等常量表顺序、任何 sorted key、float 累加顺序。
3. shim：curation.screen_planner 等原路径留完整 re-export（含 screen_planner.py L24-35 的
   ScreenLayoutPlannerState 等既有 re-export 符号，逐一核对）+ DeprecationWarning；
   layout.planner_impl: layout_engine|curation 开关（默认 layout_engine）。
4. 消费方改指新路径：layout_engine/adapter.py（不再 import curation）、render/surface.py、
   web/studio_handlers/trip_replan_handlers.py 等（grep 全量核对）。
5. CI 不得把 DeprecationWarning 升级为 error（DIFF-04）。
6. 开关台账登记 layout.planner_impl 上线日期。

硬性验收（AC-ARC-08v2 + AC-ARC-09）：
- grep 验证 curation/ 不再持有规划实现（shim 除外）。
- cross-import 边数达 ADR-015 判据（附统计输出）。
- golden 三重门禁全绿（arch_equivalence_check + phase17_golden_metrics + mosaic 签名）。
- pytest 全量四档（fast/integration/mosaic/e2e 抽 studio 相关）全绿。
任何门禁失败即停并回退，报告给我。完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-16 · M-B1：分层违例清零（2d）

```text
【启动前确认】M-B4a/b done。

执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-B1（见 §5.3.2 违例清偿表——逐行执行）。

任务：按表逐条清偿并从 import-linter 豁免清单移除：
1. media/ingest.py → curation：默认下沉方案（apply_layout_eligibility_marks 等入
   media/quality.py，media_classify 随迁）；若发现下沉有 curation 内部依赖走不通，
   停下来给我 hook 备选方案的评估（PRD 明确 hook 仅过渡且需产物一致性 CI 断言）。
2. media/ingest_report.py → layout_contract 符号下沉。
3. render/assemble.py 的 resolve_cover_asset_id 下沉 domain/。
4. templating/roles.py 的 is_loopback_host 移 util/net.py（web/studio_auth 同步改引）。
5. layout_engine/sandbox.py 的预览回调改参数注入。
6. services/cover_opening_style.py → telemetry 摘要函数下沉。
7. curation/bucket_planning.py、chapter_titles.py 的 copy_subject 纯函数下沉。
8. services/trip_factory.py ↔ templating 环：先出方案（接口注入 vs 上移）给我确认再动。
9. export→render 已在分层图白名单，登记即可。

验收（AC-ARC-10）：lint-imports 豁免清单为空且全绿；pytest --fast 与 -m integration 全绿；
arch_equivalence_check 对 golden fixture diff 为空（ingest 标记下沉是算法敏感点，
PRD 评审 I-04：layoutEligible 缺标会改变 curate 资产池）。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-17 · M-B6：schema 演进策略（1.5d）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-B6（见 §5.5）。前置：M-A1 done。
先读 travelogue/curation/trip_migration.py、schemas/trip.schema.json 的 version 字段。

任务：
1. trip.version 升级规则写入 docs（新增可选字段不 bump；语义变更/删除 bump minor；
   meta.revision 属新增可选字段）。
2. trip_migration.py 扩展为 MIGRATIONS: list[(from_version, migrate_fn)] 注册表，
   TripService.load 按序应用；现有 strip_legacy_curation_fields 纳入注册表。
3. 兼容窗口：向后兼容一个 minor；超窗 load 报可读错误。
4. lint_trip_json.py 增加 version 字段合法性校验。
5. 单测覆盖 AC-ARC-16：旧 version fixture 正确迁移；超窗版本报错可读。

验收：pytest --fast -q 全绿；全 fixture validate 通过。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

---

## WS3 · P2 机会主义还债（无 deadline，触发条件满足时执行）

### P-18 · M-C1：声明式路由表（3d · 触发：下次需要新增 Studio API 时顺带做）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-C1（见 §6.4）。
先读 travelogue/web/studio_routes.py 全文、web/serve.py L77-144（注意 L96-117 有 trip 级
POST 第二分发入口——save-copy/promote-tier/rerender，必须一并收编）、studio_handlers/paths.py。

任务（分 3 个 PR：GET / POST / PATCH+DELETE）：
0. 先落路由枚举快照测试：遍历现有 dispatch 分支，固化 (method, path_or_matcher, handler)
   三元组清单。
1. 写 web/studio_router.py（约 100-150 行）：Route 元组表 + 分发器，支持 exact / prefix /
   match_* capture / per-route auth / startswith 异构 matcher；handler 函数零改动。
2. 逐 method 迁移，每个 PR 断言快照 diff 为空（AC-ARC-13）；serve.py 第二入口收编进表；
   studio_trip_parts 静态 fallback 标注非路由表管辖。

验收：快照 diff 为空 × 3；pytest --fast 与 studio 相关 e2e 全绿。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-19 · M-C2：tests/ 目录分层（2d · 触发：与 M-B4b 错开的空窗期）

```text
【启动前确认】M-B4b 不在进行中（两者都是大规模文件移动，PRD R-04 要求错开）。

执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-C2（见 §6.2）。
先读 tests/conftest.py（自动打标逻辑 L34-50）、scripts/quality_gate.py（L22-29 硬编码
REGRESSION_TESTS 路径）、pyproject.toml markers。

任务：分批 git mv（每批一个域 10-30 文件）到 tests/unit/{包名}/、tests/integration/、
tests/e2e/；fixtures/_golden/js 不动。每批执行 PRD §6.2 的四项核对：
1. pytest --collect-only -q 总数一致；
2. test-pr / test-integration / test-e2e 三条 -m 表达式各自 --collect-only 数一致；
3. quality_gate.py REGRESSION_TESTS 路径同步更新；
4. 抽样 5 个文件 marker 与迁移前快照一致。
conftest 自动打标改按目录判定（文件名判定保留过渡）；重写 docs/TESTING.md 反映现状
（含 marker 体系与 CI 分层，评审指出旧版严重过时）。

验收：AC-ARC-12v2 四项全过 × 每批；CI 全量绿。分批提交，每批单独汇报。
完成后更新 ARCH-OPT-STATUS.md。
```

### P-20 · M-C3：脚本/文档归档机制（1.5d · 触发：任一 Phase 验收完成后）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-C3（见 §6.3）。

任务：
1. 写 scripts/gen_scripts_registry.py：扫描 .github/workflows/*.yml 与 docs/ 引用，
   生成 scripts/README.md registry（脚本 | 状态[CI引用/现役/可归档] | 引用方）。
2. 建 scripts/archive/phase{N}/ 与 docs/archive/；按退役规则（Phase 验收满一个版本周期且
   零 CI/docs 引用）给出首批可归档清单——先列清单给我确认，确认后执行 git mv。
3. docs/README.md 增「现行有效文档」索引区：主 PRD / ADR / 运行手册 / 历史归档四类。

验收：归档后 CI 全量绿（证明无引用断裂，PRD 评审 I-04 的 AC）；registry 与实际一致。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-21 · M-C5：前端拆分 + 类型检查（4-5d · 触发：Homepage v2.2 M23 全部交付后）

```text
【启动前确认】PRD §8.1 G-WIP-02：Homepage v2.2 M23 系列已交付？未交付则停止。

执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-C5（见 §6.5）。分两阶段，
第一阶段完成并 merge 前禁止开始第二阶段：

第一阶段（硬性前置）：补 Playwright 冒烟 AC-ARC-14a-d——
a 翻页 / b inline edit / c 导出长图 / d 分享面板，用带真实 assets 的 fixture trip
（现有 test_preview_toolbar_v3.py 用空 trip 种子页，不触达这些流程，不可复用）。
merge 进 CI e2e job，跑绿留基线。

第二阶段：
1. templates/studio/preview-toolbar.js（3,428 行）按功能域拆 ESM 模块（toolbar 壳/章节导航/
   inline-edit/分享面板/v3-sheet 桥接），入口文件同名同 URL import 聚合——
   travelogue/web/studio_chrome.py 必须零改动；只做物理移动不改逻辑。
2. 根目录 jsconfig.json + devDependency typescript，tsc --checkJs --noEmit；
   存量文件 @ts-nocheck 渐进；tsc 进 CI validate job。
3. studio-home-v2.css（3,985 行）按区块拆 + @import 聚合，选择器不改；
   验证 SimpleHTTPRequestHandler 的 CSS MIME 与相对路径正常。

验收：AC-ARC-14a-d 拆分前后均绿；tsc --noEmit 通过；studio_chrome.py 零 diff；
预览页手动冒烟全功能正常。完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-22 · M-C6：命名消歧（0.5d，分两段）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-C6（见 §6.6）。

第一段（立即可做）：
1. 写 docs/GLOSSARY.md 一页：登记三个 "v3" 的指代（classic 旧首页 / Import Wizard v3 /
   Preview v3 sheet），链接各自 PRD。
2. 清理 templates/studio/homepage-v2/store.js L4-5 引用已删除 navigation.js 的过期注释。

第二段（【启动前确认】G-WIP-03：Import Wizard v3 已全量稳定）：
3. studio_homepage_gate.py 的 variant "v3" 改名 "classic"（兼容读取旧值），
   相关测试与 docs 同步。

验收：pytest --fast -q 全绿；第二段需 studio homepage gate 相关测试全绿。
完成后更新 ARCH-OPT-STATUS.md 并汇报。
```

### P-23 · M-D1：开关删除收尾（1d · 触发：开关满足 §3.3 DoD 全部四条）

```text
执行 docs/PRD-ARCH-OPTIMIZATION.md v1.1 的里程碑 M-D1（见 §3.3 与 §8.2）。

启动前核对 ARCH-OPT-STATUS.md 开关台账，对每个开关逐条验证 §3.3 删除 DoD：
① 上线满 4 周；② 每周双跑 diff 全部为空（翻 CI 定时 job 记录）；③ 无切回反馈；
④ legacy 配置零出现。任一不满足则停止并报告。

任务：
1. 删除 pipeline.orchestration legacy 路径（studio_pipeline.py 旧手写编排）+ 开关键 + 对应测试；
   config 残留 legacy 值时启动 warning 不阻断。
2. 删除 layout.planner_impl 开关与 curation.screen_planner shim（DeprecationWarning 期结束）。
3. 删除每周双跑 CI job。
4. TECH-ARCHITECTURE.md 全量更新至收敛后现状（替换 v0.9 增量章节）。
5. ARCH-OPT-STATUS.md 全表终审：所有里程碑 done，输出 PRD 收尾总结（含 G-ARC-07v2
   北极星与代理指标的首轮读数）。

验收：CI 全量绿；grep 无 legacy 残留引用；最后一轮双路径 E2E 已在删除前跑过（留证据）。
完成后向我提交收尾报告。
```

---

## 附：执行顺序速查

| 阶段 | 顺序 | 门禁 |
|------|------|------|
| WS1（立即） | P-00 → P-01 → P-02 → P-03 → P-04 → P-05 → P-06 → P-07 → P-08 | 无 |
| WS2 | P-09 → P-10 →（P-11 → P-12 与 P-13、P-14 可穿插）→ P-15 → P-16 → P-17 | P-11/12 需 Import Wizard v3 AC 通过；P-15 需 ADR-015 获批 |
| WS3 | P-18 ~ P-22 按触发条件任意顺序 | 各条内注明 |
| 收尾 | P-23 | 开关满 4 周 DoD |

并发上限（PRD §3.1）：最多 1 个 WS2 里程碑在途 + 1 个 WS1/WS3 小任务。
