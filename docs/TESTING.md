# Travelogue · 测试策略

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.3 |
| **原则** | 关键路径必测；不追求高覆盖率 |
| **关联** | `VALIDATION-RULES.md`、`DEFINITION-OF-DONE.md` · [PRD-STUDIO-FE-TEST-HARDENING-V1](./PRD-STUDIO-FE-TEST-HARDENING-V1.md) |
| **更新日期** | 2026-07-17 |

---

## 1. 测试金字塔

```
        ┌─────────────┐
        │ 3× 真实 trip │  AC / 人工
        ├─────────────┤
        │  e2e 脚本    │  CLI 一条龙
        ├─────────────┤
        │  集成测试    │  agent + 临时目录
        ├─────────────┤
        │  单元测试    │  validate / curate 规则
        └─────────────┘
```

### 1.1 Studio 前端测试金字塔（SFH）

完整约定见 [PRD-STUDIO-FE-TEST-HARDENING-V1](./PRD-STUDIO-FE-TEST-HARDENING-V1.md) · [IMPLEMENTATION](./IMPLEMENTATION-STUDIO-FE-TEST-HARDENING-V1.md)。

```text
        ┌──────────────────────┐
        │ 人工 / 真机 AC       │
        ├──────────────────────┤
        │ Playwright 跨层 e2e  │  kept_n→意图卡、导入恢复、导出成功面
        ├──────────────────────┤
        │ Python 合同 / 集成   │  API · schema · 服务端 resolve
        ├──────────────────────┤
        │ Node 纯逻辑单测      │  tests/js · *-logic.js（主反馈）
        └──────────────────────┘
```

| 层 | 允许 | 禁止 |
|----|------|------|
| Node | 返回值、状态转移、载荷映射 | `document`、真 HTTP |
| Python | handler/schema、服务端 recipe、短 `# ASH-CONTRACT` | 大段文案扫源码 |
| Playwright | 可见性、role、服务端注入后 UI | 无注释固定 sleep |

**约定**：Studio FE 新决策优先落 `*-logic.js` + `tests/js`；跨层行为本机补/跑 Playwright。

本机（**Go 证据 SSOT**；Actions 额度用尽期间不刷 CI）：

```powershell
npm run test:js
python -m pytest tests/unit/web/test_studio_home_v2.py -k v2_js_logic_node_units -q
```

- 唯一入口：`scripts/run-js-tests.mjs`（`package.json` → `test:js`）
- CI 合同：`.github/workflows/ci.yml` 的 `test-pr` 须跑 `npm run test:js`（额度恢复后生效）

---

## 2. Fixtures

| 文件 | 用途 |
|------|------|
| `schemas/fixtures/trip.example.json` | 通用样例 |
| `schemas/fixtures/trip.ingest_ready.json` | Agent 1 输入 |
| `schemas/fixtures/trip.structure_locked.json` | Agent 2 输入 |
| `schemas/fixtures/trip.copy_locked.json` | Agent 3 输入 |

**CI 必跑**（`.github/workflows/ci.yml`）：

```powershell
python -m pytest tests/ -q
python scripts/validate_trip.py schemas/fixtures/trip.example.json --level all
python scripts/validate_trip.py schemas/fixtures/trip.ingest_ready.json --level all
python scripts/validate_trip.py schemas/fixtures/trip.structure_locked.json --level all
python scripts/validate_trip.py schemas/fixtures/trip.copy_locked.json --level all
python scripts/validate_trip.py schemas/fixtures/trip.render_golden.json --level all
python -m travelogue demo verify
```

---

## 3. 单元测试（pytest）

目录：`tests/`（M-C2 起分批迁入子目录）

| 子目录 | 用途 | CI job |
|--------|------|--------|
| `tests/unit/` | 纯单测（自动 `@pytest.mark.unit`）；含 domain / web / media 等 | test-pr |
| `tests/unit/layout_engine/` | layout / mosaic / lte / lse / usage_rules 单测 | test-pr |
| `tests/unit/layout_templates/` | 模板引擎单测 | test-pr |
| `tests/integration/` | phase 验收 / studio server / p17 / demo（自动 `integration`） | test-integration |
| `tests/e2e/` | Playwright 浏览器测试（自动 `e2e`） | test-e2e |
| `tests/test_ingest.py` | **唯一**顶层 shim（`_album` 向后兼容）；禁止新增其他顶层 `test_*.py` | — |

**M-C2 batch1（2026-07-08）**：domain / orchestrator / lint / trip_migration → `tests/unit/`；trip CAS → `tests/integration/trip/`。

**M-C2 batch4（2026-07-08）**：studio handlers + curate + studio 单测 → `tests/unit/web/`；`scripts/quality_gate.py` REGRESSION_TESTS 路径已更新。

**M-C2 batch5（2026-07-08）**：export / render 单测 → `tests/unit/export/`、`tests/unit/render/`（11 文件）。

**M-C2 batch6（2026-07-08）**：layout 单测 → `tests/unit/layout_engine/`（13 文件）；`quality_gate` REGRESSION_TESTS 路径已更新。

**M-C2 batch7（2026-07-08）**：mosaic 单测 → `tests/unit/layout_engine/`（18 文件）；补删 batch6 遗留的顶层 layout 副本。

**M-C2 batch8（2026-07-08）**：mosaic 余量 21 文件 → `tests/unit/layout_engine/`（mosaic 顶层测试清零）。

**M-C2 batch9（2026-07-08）**：lte 单测 21 文件 → `tests/unit/layout_engine/`；`test_lte_studio_playwright.py` → `tests/e2e/`；CI registry parity 路径已更新。

**M-C2 batch10（2026-07-08）**：dual/screen/golden/editorial/subject/compare/beam 等 14 文件 → `tests/unit/layout_engine/`；`demo/verify.py` 与 phase gate 脚本路径已同步。

**M-C2 batch11（2026-07-08）**：lse + usage_rules（13）→ `tests/unit/layout_engine/`；template（15）→ `tests/unit/layout_templates/`；phase13 gate 脚本路径已更新。

**M-C2 batch12–finish（2026-07-08）**：剩余 **247** 顶层文件一次性迁入 `unit/*` / `integration/*` / `e2e/`；baseline 冻结为 `test_ingest.py`；`tests/_repo_root.py` 统一 repo 路径；`pytest --collect-only` **2714** 与迁移前一致。

新增测试请放入 `tests/unit/{包名}/`、`tests/integration/` 或 `tests/e2e/`，勿在 `tests/` 根目录新建 `test_*.py`（`lint_test_layout.py` CI 守护）。

| 模块 | 用例示例 |
|------|----------|
| `test_validate.py` | 超字数、缺 ref、封面视频 → 错误码 |
| `test_validate_limits.py` | VR-L07/L08、VR-M03 |
| `test_narrative_validate.py` | VR-N01/N02/N03、ingest 多旅程预检 |
| `test_curate.py` | 跨天分章、章数 3–5、多 segment 合册 |
| `test_compare_web_layout.py` | legacy vs screens A/B 渲染 |
| `test_narrate.py` | 规则 stub、禁用词 |
| `test_llm_narrate.py` | LLM narrate（mock chat） |
| `test_llm_client.py` | LLM provider 解析 |
| `test_pipeline_run.py` | 流水线顺序 |

```powershell
pip install pytest jsonschema pyyaml
pytest tests/ -q
```

---

## 4. 集成测试

| 场景 | 做法 |
|------|------|
| ingest | 临时目录 3 张 jpg → assets 存在 |
| render | `copy_locked` fixture 复制到 tmp → index.html 生成 |
| export | zip 内 index.html 可解析 |

使用 `tmp_path` fixture，不提交 `trips/`。

---

## 5. 视觉回归（轻量）

MVP **不强制** Percy；采用：

- [ ] `render` 后人工对照 `golden.html` checklist（`ACCEPTANCE.md` T-01～T-07）  
- [ ] 可选：保存 `tests/snapshots/dom-structure.txt`（仅标签+class 树）

---

## 6. E2E 脚本（目标）

`scripts/e2e_smoke.ps1`（待实现）：

1. `trip new e2e-test --from tests/data/mini_album`  
2. `curate` → `lock structure` → `narrate` → `lock copy`  
3. `render` → `export --confirm-privacy`  
4. 断言 zip 存在  

`tests/data/mini_album/`：3 张 **公版/自制** 小图（<100KB each）。

---

## 7. 手动测试清单（发版前）

- [ ] 微信内置浏览器打开 zip 内 HTML  
- [ ] `<audio>` 播放  
- [ ] 横滑 scroll 不撑破视口  
- [ ] `data-layout=mobile` 强制竖版  

---

## 8. CI（建议）

`.github/workflows/ci.yml`（P1）：

```yaml
# 示意
- pip install jsonschema pytest
- python scripts/validate_trip.py schemas/fixtures/*.json --level all
- pytest tests/
```

---

## 9. 断言约定（Assertion Style · ASH）

> 完整计划见 [PRD-ASSERTION-HARDENING-V1.md](./PRD-ASSERTION-HARDENING-V1.md)。  
> 原则：**渐进还债**——新代码遵守约定；旧债触达时顺手修，不要求全库回填。

### 9.1 生产代码（`travelogue/`）

- **禁止**用 Python `assert` 语句做运行时校验（`-O` / `PYTHONOPTIMIZE` 会剥离）。
- 不变量用显式 `raise XxxError(...)`，或既有命名 `assert_*` **领域守卫**（守卫内部亦不得写裸 `assert`）。
- CI：`python scripts/lint_no_runtime_assert.py`（AST 扫描 `ast.Assert`）。

### 9.2 单元 / 集成测试

- 优先断言**可观察行为**、返回值、错误码；避免大段 HTML/JS/CSS 源码字面量。
- 确需锁字面量时标注 `# ASH-CONTRACT`，并保持短小。
- `pytest.raises` 使用**具体异常类型**；业务错误建议 `match=` 错误码或关键子串。
- 浮点 / ML 分数使用 `pytest.approx`。
- 循环内 assert 须带循环变量上下文（id / index）。
- 新写断言**鼓励**带失败消息；不要求回填全库。

### 9.3 Playwright e2e

- 优先 `from playwright.sync_api import expect`（自动重试）。
- **禁止**无注释的 `page.wait_for_timeout`；例外须写 `# ASH-SLEEP: <理由>`。
- 定位优先级：role/label → `data-testid` → `#id` → 少量可见文案。
- 避免单测 assertion roulette：一个场景一个主断言簇。

---

## 10. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3 | 2026-07-17 | 增 §1.1 Studio FE Node 最短入口（SFH W0a） |
| v0.2 | 2026-07-16 | 增 §9 断言约定（ASH M0 · [PRD-ASSERTION-HARDENING-V1](./PRD-ASSERTION-HARDENING-V1.md)） |
| v0.1 | 2026-05-19 | 初稿 |
