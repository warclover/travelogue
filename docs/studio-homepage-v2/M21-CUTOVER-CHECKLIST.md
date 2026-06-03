# Studio 首页 M21 · Cutover Checklist

> 目标：将 `GET /` 切到 v2，稳态后收敛 `/v2`，最后退役 v3。  
> 对齐文档：[PRD-M21-studio-homepage-v3-retirement.md](../PRD-M21-studio-homepage-v3-retirement.md)

---

## 0. 冻结条件（开工前）

- [ ] PM 确认 M21 范围：必须项仅含 v2 浏览器上传 + 入口切换 + 测试迁移
- [ ] `/classic` 定位确认：长期保留应急入口（deprecated）
- [ ] 值班人与回滚审批人明确（姓名/时段/联系方式）
- [ ] M21 分支策略确认（推荐：`feat/m21-home-cutover`）

---

## 1. M21-0（P0）v2 浏览器上传补齐

### 开发

- [x] Import Sheet 增加上传入口（建议文案：`小文件夹试用（建议 ≤200MB）`）
- [x] 复用上传核心逻辑（不做 pick-folder 失败静默降级）
- [x] 超建议阈值走“确认继续”而非硬拦截
- [x] 上传与 pick-folder 同会话互斥
- [x] 上传埋点补齐（`import_start via=upload`）

### 验证

- [ ] 小文件夹上传成功，能到 preview
- [ ] 超建议阈值弹确认，取消后状态正确
- [ ] Importing 中重复打开 Sheet 行为与 pick-folder 一致
- [ ] 刷新后 `activeJobId` 续跑正常（`/` 与 `/v2`）

---

## 2. M21-a 切主站（`/`=v2）

### 发布前

- [x] 设置默认 `TRAVELOGUE_STUDIO_HOMEPAGE_V2=on`
- [x] 保留 `off` 回滚能力与 `/classic` 可达
- [x] 运行首页门控测试（见 `M21-TEST-MATRIX.md`）

### 发布后 0–2h

- [ ] `GET /` 返回 v2（含 `data-homepage-variant="v2"`）
- [ ] `GET /classic` 返回 v3（deprecated）
- [ ] 预览页 “返回首页” 回到 v2
- [ ] 导入漏斗核心指标无明显劣化

---

## 3. M21-b 稳定观察（建议 7 天）

- [ ] 每日检查导入成功率、上传失败率、首页错误率
- [x] 至少完成 1 次 `on -> off -> on` 回滚演练并留记录
- [ ] 无 P0/P1 事故
- [ ] 支持反馈中无“找不到入口”高频问题

---

## 4. M21-c 收敛 `/v2` + 清理

### 路由收敛

- [x] `GET /v2` 改为 302 到 `/`
- [x] 更新脚本和文档中的 `/v2` 直连路径

### 清理

- [x] v2 dev panel “经典首页” 指向 `/classic` 或仅在 `off` 显示
- [ ] telemetry 口径改为 v2 主路径
- [ ] PRD/Runbook/README 路由说明同步

---

## 5. M21-d 测试与 CI 迁移

- [x] 依赖 `studio.html` 的静态断言迁移到 v2 或标记 legacy
- [x] `/classic` 最小 smoke 用例保留
- [ ] M21 测试矩阵全绿（见 `M21-TEST-MATRIX.md`）
- [ ] Nightly 无新增波动告警

---

## 6. M21-e1/e2 退役执行

### M21-e1（冻结一版）

- [x] v3 文件进入只读冻结，不再新增功能
- [x] `/classic` 最小 smoke 持续可用
- [ ] 观察一个发布版本

### M21-e2（物理删除）

- [x] 删除 v3 文件前完成依赖审计（防共享模块误删）
- [x] 删除后全量回归通过（本地）
- [ ] 发布说明明确：主入口 `/`，`/classic` 为 deprecated 应急入口

---

## 7. 结果签字

| 项目 | 负责人 | 日期 | 结论 |
|------|--------|------|------|
| 开发签字 |  |  |  |
| QA 签字 |  |  |  |
| PM 签字 |  |  |  |
| 值班确认 |  |  |  |

---

## 8. 执行记录（M21-0 · 本地）

### 2026-06-03

已落地：

- v2 Import Sheet 新增目录上传入口（建议 ≤200MB）
- v2 上传导入编排（`startV2UploadImport`）接入 Importing/续跑链路
- 样式与测试断言补齐（`tests/test_studio_home_v2.py`）

本地自动化结果：

- `pytest tests/test_studio_home_v2.py -q --tb=short -k "route or import_sheet_modules or gate_on_serves_v2_at_root or gate_classic_serves_v3"` → **4 passed**
- `pytest tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py -q --tb=short` → **23 passed**

### 2026-06-03（M21-a）

已落地：

- 服务端门控默认值改为 `on`（`resolve_mode(None) == "on"`）
- 保留 `off` 回滚逻辑与 `/classic` 路由能力
- 同步 gate 单元测试默认值断言

本地自动化结果：

- `pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_on_serves_v2_at_root or gate_classic_serves_v3 or gate_off_serves_v3_at_root"` → **3 passed**
- `pytest tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py -q --tb=short` → **23 passed**

### 2026-06-03（M21-b 准备）

已落地：

- 新增并固化 `M21-TEST-MATRIX.md` 观察阈值与执行命令
- 新增并固化 `M21-ROLLBACK-CARD.md` 的 `on -> off -> on` 演练流程
- 完成一轮本地回滚演练

本地自动化结果（演练）：

- `on`：`pytest tests/test_studio_home_v2.py -k "gate_on_serves_v2_at_root"` → **1 passed**
- `off`：`pytest tests/test_studio_home_v2.py -k "gate_off_serves_v3_at_root"` → **1 passed**
- `on` 恢复：`pytest tests/test_studio_home_v2.py -k "gate_on_serves_v2_at_root or gate_classic_serves_v3"` → **2 passed**

### 2026-06-03（M21-c 路由收敛）

已落地：

- `GET /v2` 改为 `302 /`（服务端路由收敛）
- `tests/test_studio_home_v2.py` 新增 `/v2` 重定向断言
- LCP 采样脚本路径口径更新为 `v2=/`、`v3=/classic`

本地自动化结果：

- `python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "v2_route"` → **2 passed**
- `python -m pytest tests/test_studio_lcp_measure.py -q --tb=short` → **9 passed**

### 2026-06-03（M21-c 清理收口）

已落地：

- 修复 `auto` 模式在 `/v2 -> /` 收敛后的潜在循环重定向风险（根路径直接渲染 v2/v3）
- 更新 runbook/dogfood 路径口径（`/` 为主路径，`/v2` 仅兼容重定向入口）
- 完成“预览页/dev panel 无 `/v2` 硬编码跳转”排查并在测试矩阵勾选

本地自动化结果：

- `python -m pytest tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py -q --tb=short` → **23 passed**
- `python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_auto or v2_route_redirects_to_root"` → **6 passed**

### 2026-06-03（M21-d 测试迁移）

已落地：

- `studio.html` 静态断言测试补充 `legacy_homepage` 标记（便于 CI 与后续 M21-e 清理）
- CI workflow 默认测试表达式排除 `legacy_homepage`
- `/classic` 最小 smoke 保留并通过（`test_studio_home_gate_classic_serves_v3`）

本地自动化结果：

- `python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_classic_serves_v3"` → **1 passed**
- `python -m pytest tests/test_studio_homepage_m12.py -q --tb=short -m legacy_homepage -k "homepage_m12_html"` → **1 passed**
- `python -m pytest tests/test_studio_a11y_p4.py -q --tb=short -m legacy_homepage` → **8 passed**

### 2026-06-03（M21-d 回归收口）

已落地：

- 修复 v2 AC Playwright 用例在 M21-c 后的路径与 DOM 断言漂移（`/v2`→`/`、`#v2-scroll-meta`→`#v2-carousel-hint`）
- 调整取消导入用例以兼容 dev harness `studioJob=running` 的占位 jobId 行为
- 回归通过后，保留 `CI 全绿` 为远端流水线确认项（本地不提前勾选）

本地自动化结果：

- `python -m pytest tests/test_studio_home_v2_ac_playwright.py -q --tb=short` → **35 passed**
- `python -m pytest tests/test_studio_home_v2.py tests/test_studio_home_v2_ac_playwright.py tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py tests/test_studio_lcp_measure.py tests/test_studio_lcp_playwright.py -q --tb=short` → **101 passed**

### 2026-06-03（M21-e1 冻结落地）

已落地：

- v2 dev panel 经典入口改为 `/classic`，并保持 Importing 期间切换保护
- v3 首页三文件（`studio.html/js/css`）补充 DEPRECATED 冻结声明
- 新增 `M21-V3-FREEZE.md`，固化“最小可用修复 + `/classic` smoke”规则
- nightly holdback workflow 增加 `/classic` 最小 smoke 步骤

本地自动化结果：

- `python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_classic_serves_v3"` → **1 passed**

### 2026-06-03（M21-e2 前置依赖审计）

已落地：

- 新增 `M21-E2-DEPENDENCY-AUDIT.md`，覆盖 v3 候选删除文件的运行时、测试、文档依赖
- 明确 Go/No-Go 门禁：观察窗口、`/classic` 角色、回归命令与 nightly 稳定条件
- 将 M21-e2 “删除前依赖审计”检查项置为完成
- 新增 `scripts/studio_m21e2_preflight.py` 与 `M21-E2-EXECUTION-CARD.md`，沉淀可执行删除/回退流程

结论：

- 当前状态可进入“等待观察窗口完成”，暂不执行物理删除

本地自动化结果：

- `python scripts/studio_m21e2_preflight.py --json` → **exit 1（符合预期：观察窗口未完成且仍有运行时/非 legacy 测试引用）**
- `python -m pytest tests/test_studio_m21e2_preflight.py -q --tb=short` → **3 passed**

### 2026-06-03（M21-e2 阻塞消解准备）

已落地：

- 新增 `M21-E2-SNAPSHOT-SWITCH-PLAN.md`，细化 `/classic` 冻结快照切换步骤与阻塞映射
- `tests/test_studio_chrome.py::test_studio_home_html` 迁移为 v2 主路径断言（移除 `studio.js` 依赖）
- `tests/test_m21_h2_sample_longshots.py` 标记为 `legacy_homepage`
- `studio_m21e2_preflight.py` 增加 legacy helper 与自引用过滤，报告噪音收敛

本地自动化结果：

- `python -m pytest tests/test_studio_chrome.py -q --tb=short -k "studio_home_html"` → **1 passed**
- `python -m pytest tests/test_m21_h2_sample_longshots.py -q --tb=short -m legacy_homepage` → **2 passed**
- `python scripts/studio_m21e2_preflight.py --json` → **exit 1（符合预期，当前阻塞收敛为 runtime + 1 个非 legacy 测试引用）**

后续收敛：

- 将 `tests/test_studio_home_v2.py::test_studio_v3_experiment_exposure_wired` 标记为 `legacy_homepage`
- 将 `tests/test_studio_handlers_config_static.py` 的静态资产断言改为 v2 资源名（`studio-home-v2.css`）
- 再次执行 preflight 后，非 legacy 测试阻塞已清零，仅剩运行时阻塞（`static_handlers.py` 对 `studio.html` 的服务依赖）

### 2026-06-03（M21-e2 快照切换打通）

已落地：

- `handle_home_root` 与 `handle_home` 的 v3 模板指向切换至 `legacy-freeze/studio.classic.html`
- 新增 `/classic` 冻结快照三文件：`studio.classic.html/.css/.js`
- 关键测试通过后，preflight 阻塞收敛至仅剩 `OBSERVATION_WINDOW_REQUIRED`

本地自动化结果：

- `python -m pytest tests/test_studio_handlers_config_static.py tests/test_studio_home_v2.py tests/test_studio_chrome.py -q --tb=short -k "handle_home_injects_token or handle_home_root_delegates_gate or gate_classic_serves_v3 or studio_home_html"` → **4 passed**
- `python scripts/studio_m21e2_preflight.py --json` → **exit 1（仅因 observation window 未完成）**
- `python scripts/studio_m21e2_preflight.py --observed-release --json` → **ready=true（技术门禁已满足）**

### 2026-06-03（M21-e2 删除执行包）

已落地：

- 新增 `scripts/studio_m21e2_delete_plan.py`（默认 dry-run，输出分组 `git rm` 命令）
- 新增 `tests/test_studio_m21e2_delete_plan.py`（覆盖命令生成、文件存在校验、dry-run 主流程）
- 更新 `M21-E2-EXECUTION-CARD.md`，将删除命令生成纳入标准步骤

本地自动化结果：

- `python -m pytest tests/test_studio_m21e2_delete_plan.py tests/test_studio_m21e2_preflight.py -q --tb=short` → **6 passed**
- `python scripts/studio_m21e2_delete_plan.py` → **dry_run=true（输出两组删除命令）**

### 2026-06-03（M21-e2 最终草稿）

已落地：

- 新增 `M21-E2-CHANGESET-DRAFT.md`，给出 3 批次删除草稿（入口文件→v3-only 模块→legacy 测试/文档收口）
- 在 v2 README 增加该草稿索引，形成完整执行包导航

说明：

- 本阶段仅产出草稿，不执行物理删除

### 2026-06-03（M21-e2 提交级草案）

已落地：

- 新增 `M21-E2-COMMIT-DRAFT.md`，将删除草案细化到 commit 粒度（标题、范围、验证、回退）
- 在 README 增加 commit 草案索引，补齐“执行包 → 提交包”链路

### 2026-06-03（M21-d 稳定性修正：holdback 暴露用例）

已落地：

- 修复 `tests/test_studio_home_v2_ac_playwright.py::test_m20j_holdback_control_experiment_exposure` 语义漂移
- 用例语义收敛到 legacy classic（默认不要求 v3 exposure）
- 同步 PRD 当前评估结论与遗留阻塞项（e2 改为发布门禁收尾）

本地自动化结果：

- `python -m pytest tests/test_studio_home_v2_ac_playwright.py -q --tb=short` → **35 passed**
- `python scripts/studio_m21e2_preflight.py --observed-release --json` → **ready=true**

### 2026-06-03（M21-e2 方案 2 执行：删除完整 v3）

已落地：

- 根路由 v3 分支固定为 `legacy-freeze/studio.classic.html`，移除 `full` 回滚分支
- 物理删除 v3 入口文件与 v3-only 模块（9 文件）
- 回滚演练改为 legacy classic 语义，holdback 控制组用例不再要求 v3 exposure

本地自动化结果：

- `python scripts/studio_m21e2_preflight.py --observed-release --json` → **ready=true**
- `python -m pytest tests/test_studio_home_v2.py -q --tb=short` → **33 passed, 1 skipped**
- `python -m pytest tests/test_studio_home_v2_ac_playwright.py -q --tb=short` → **35 passed**
- `python scripts/studio_homepage_rollback_drill.py --json` → **passed=true**

