# M21-e2 前置依赖审计（v3 物理删除前）

> 审计日期：2026-06-03  
> 目标：在执行 M21-e2 删除前，确认 v3 候选文件的运行时依赖、测试依赖、文档依赖与迁移动作。

## 1) 审计范围（候选删除）

按 PRD M21-e2 候选：

- `templates/studio/studio.html`
- `templates/studio/studio.js`
- `templates/studio/studio.css`
- `templates/studio/js/navigation.js`
- `templates/studio/js/render.js`
- `templates/studio/js/sheet.js`
- `templates/studio/js/samples.js`
- `templates/studio/js/init.js`
- `templates/studio/js/viewport.js`

## 2) 运行时依赖结论

### 2.1 当前不可删除（M21-e1 阶段）

- `GET /classic` 仍由 `travelogue/web/studio_routes.py` 分发到 `handle_home()`，最终返回 `studio.html`。
- `studio.html` 仍加载 `studio.css` 与 `studio.js`，三者构成 `/classic` 最小可用闭环。
- `studio.js` 仍直接 import `navigation.js`、`render.js`、`sheet.js`、`samples.js`、`init.js`、`viewport.js`。

结论：以上文件在 M21-e1 必须保留，不可物理删除。

### 2.2 与 v2 主路径解耦状态

- v2 主路径（`/`）使用 `studio-home-v2.html` + `homepage-v2/**`，不依赖 `studio.html/js/css`。
- v2 样式未引用 `studio.css`（`templates/studio` 内检索仅 `studio.html` 引用该 CSS）。

结论：v3 资产已与 v2 主路径解耦，可在观察窗口后进入删除窗口评估。

## 3) 测试依赖结论

### 3.1 已归档为 legacy 轨道

以下测试明确绑定 `studio.html` 或 v3 入口，已用 `legacy_homepage` 标记隔离：

- `tests/test_studio_a11y_p4.py`
- `tests/test_studio_p8_regression.py`
- `tests/test_studio_phase5_tier0.py`
- `tests/test_studio_p9_qa_matrix.py`
- `tests/test_studio_homepage_m12.py`
- `tests/test_studio_ux_p3.py`（v3 高级选项断言用例）

### 3.2 `/classic` 最小 smoke

- `tests/test_studio_home_v2.py::test_studio_home_gate_classic_serves_v3` 作为保底 smoke。
- nightly 已接入 `/classic` smoke（`nightly-holdback.yml`）。

结论：测试面已具备“主线 v2 + legacy v3 分轨”的删除前条件。

## 4) 文档与流程依赖

仍有大量历史文档描述 `studio.html/js/css`（Phase2~Phase5/ADR/实现记录），这些引用属“历史事实”，不构成运行时阻塞。  
M21-e2 删除时需同步追加“已退役”说明，避免新同学误读。

## 5) 删除前硬门禁（Go/No-Go）

执行 M21-e2 前必须满足：

1. 至少一个发布版本观察窗口完成（M21-e1）。
2. `/classic` 未承载常规流量，仅应急使用。
3. 以下回归通过：
   - `python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_classic_serves_v3"`
   - `python -m pytest tests/test_studio_home_v2.py tests/test_studio_home_v2_ac_playwright.py tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py tests/test_studio_lcp_measure.py tests/test_studio_lcp_playwright.py -q --tb=short`
4. Nightly 连续稳定（无新增关键波动告警）。

### 当前 preflight 状态（2026-06-03）

- 运行时阻塞：已清零（`/classic` 已切换到 `legacy-freeze/studio.classic.html`）。
- 非 legacy 测试阻塞：已清零。
- 剩余阻塞：`OBSERVATION_WINDOW_REQUIRED`（符合 M21-e1 阶段预期）。

## 6) M21-e2 执行建议（按顺序）

1. 先把 `GET /classic` 从 `studio.html` 切到“冻结快照”目录（或静态备份文件）。
2. 再删除 `studio.html/js/css` 与其仅 v3 依赖模块。
3. 最后清理 legacy 测试与文档，保留一份迁移说明。

附：可执行步骤与回退点见 `M21-E2-EXECUTION-CARD.md`；自动门禁脚本见 `scripts/studio_m21e2_preflight.py`。

---

审计结论：**当前可进入“等待观察窗口完成”状态，暂不执行物理删除。**
