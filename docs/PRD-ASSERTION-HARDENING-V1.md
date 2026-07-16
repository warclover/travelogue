# Travelogue · 断言硬化与测试诊断能力 PRD

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（核心管线 + Studio + e2e） |
| **文档版本** | **v1.0.0-ASH** |
| **状态** | **In Progress · M0–M3 Done（待结案记录）** |
| **特性代号** | **ASH**（Assertion Hardening） |
| **性质** | **工程还债 PRD**：生产不变量安全 + 断言可诊断性 + e2e 稳定性；**零 intentional 用户功能** |
| **触发来源** | 2026-07-16 全库断言专项审计（扫描证据见 §1 · 附录 B 可复现） |
| **目标分支** | `chore/assertion-hardening-v1` → `master`（建议） |
| **关联文档** | [TESTING.md](./TESTING.md) · [QUALITY-GATE.md](./QUALITY-GATE.md) · [DEFINITION-OF-DONE.md](./DEFINITION-OF-DONE.md) · [PRD-STABLE-QUALITY-HARDENING-V1.md](./PRD-STABLE-QUALITY-HARDENING-V1.md) · [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) |
| **验收配套** | 本文 §9；结案后补 `docs/acceptance-records/ash-closeout-YYYY-MM-DD.md` |
| **更新日期** | 2026-07-16 |

---

## 0. 文档说明

### 0.1 定位

本 PRD 把「断言写法债务」收敛为**可排期、可验收、可回滚**的工作包。不解决「测不够」问题，而解决：

1. **生产安全性债**：路径上用 Python `assert` 做不变量，`-O` / `PYTHONOPTIMIZE` 会剥离，错误变成更隐蔽的崩溃或坏数据。
2. **诊断能力债**：约 9205 条测试 `assert` 中仅 ~4% 带失败消息；失败时难以定位。
3. **e2e 稳定性债**：Playwright 套件 **0 次**使用官方 `expect()`，竞态依赖 `wait_for_timeout` 固定 sleep。
4. **契约耦合债**：部分单测断言 HTML/JS/CSS **源码字面量**，重构即碎、假安全感并存。

### 0.2 范围承诺

| 承诺 | 说明 |
|------|------|
| **零 intentional 用户功能** | 不改 Studio IA、管线算法、导出产物语义；仅改错误抛出方式、测试写法、文档约定 |
| **渐进式还债** | 不做全库 9000+ assert 回填；按里程碑改关键路径 + 约定前移 |
| **行为等价优先** | 生产 `assert` → `raise` 须保持同一失败语义（错误码 / 异常类型尽量不变或显式登记 DIFF） |
| **证据驱动** | 每里程碑：扫描命令 + pytest 证据 + 回滚说明 |
| **约定写入 SSOT** | `TESTING.md` 增「断言约定」节；新代码按约定执行，旧债机会主义偿还 |

### 0.3 非目标

| # | 排除项 | 理由 |
|---|--------|------|
| OUT-01 | 引入 soft-assert / pytest-check / hamcrest / assertpy | 增加依赖与风格分裂；现有 pytest 足够 |
| OUT-02 | 全库裸 assert 批量加消息 | 噪声大、冲突多；按触达文件顺手还 |
| OUT-03 | 引入 vitest/jest 前端测试栈 | 超出本期；前端仍由 Python 契约测 + Playwright 覆盖 |
| OUT-04 | 重写全部源码字符串单测（home_v2 / toolbar 全量） | 工作量大；M3 仅降噪热点 + 立约定 |
| OUT-05 | Percy / 全站视觉 CI | 归属视觉回归路线，非本 PRD |
| OUT-06 | 改变产品文案或 UI 结构「只为好测」 | 测试迁就产品真相，不反过来 |

### 0.4 术语

| 术语 | 含义 |
|------|------|
| **裸 assert** | `assert expr` 无失败消息 |
| **消息 assert** | `assert expr, "…"` 或 f-string 消息 |
| **领域守卫** | 命名 `assert_*` 函数，内部 `raise XxxError`（**不是** Python `assert` 语句） |
| **源码字符串断言** | `assert "export const …" in file_text` 一类对实现字面量的耦合 |
| **Playwright expect** | `from playwright.sync_api import expect` 的自动重试断言 API |
| **固定 sleep** | `page.wait_for_timeout(ms)` 无条件等待 |

---

## 1. 背景与扫描证据

### 1.1 全库扫描（2026-07-16）

扫描口径：行首 `assert `（`re.M`）；排除 `__pycache__`。

| 指标 | 数值 |
|------|------|
| 生产 `travelogue/` 裸 `assert` | **9 文件 / 11 处** |
| 测试 `assert` 总计 | **531 文件 / 9205 处** |
| └ unit | 444 / 7968 |
| └ integration | 68 / 770 |
| └ e2e | 16 / 459 |
| 带消息 assert（启发式 `assert …, "…"`） | **164 文件 / 365 处（~4%）** |
| `pytest.raises` | 57 / 101 |
| `pytest.approx` | 14 / 26 |
| e2e `from playwright…import expect` / `expect(` | **0 / 0** |
| e2e `wait_for_timeout` | **4 文件 / 17 处** |

### 1.2 问题总览

| ID | 问题 | 严重度 | 类型 |
|----|------|--------|------|
| **ASH-P-01** | 生产路径用 `assert` 做不变量，`-O` 可剥离 | **P0** | 正确性 / 运维安全 |
| **ASH-P-02** | e2e 零 `expect()` + 固定 sleep | **P1** | 稳定性 / flake |
| **ASH-P-03** | 热点单测源码字符串断言（home_v2 / toolbar） | **P1** | 可维护性 |
| **ASH-P-04** | 全库 ~96% 裸 assert，失败难诊断 | **P2** | DX |
| **ASH-P-05** | `pytest.raises(Exception)` 过宽 | **P2** | 测试质量 |
| **ASH-P-06** | `TESTING.md` 无断言写法约定 | **P2** | 治理 |
| **ASH-P-07** | 循环内 assert 缺上下文（主题循环等） | **P3** | DX |

### 1.3 好模式（本 PRD 推广对象）

| 模式 | 锚点 | 推广方式 |
|------|------|----------|
| 领域守卫抛异常 | `templating/lifecycle.py` · `assert_transition` | 生产不变量一律此风格 |
| 差异列表 AssertionError | `render/dom_compare.py` · `assert_dom_compatible` | 契约 helper 模板 |
| 错误码 + `match=` | `tests/unit/llm/test_llm_client.py` | raises 默认要求 |
| `pytest.approx` | `tests/unit/curation/test_photo_cull_ml.py` | 浮点/ML |
| 共享 contract helper | `assert_screen_order_contract` | M3 抽公共 helper |
| `page.expect_response` | settings observability e2e | 替代 sleep |
| `get_by_role` | import wizard a11 e2e | 抗文案漂移 |

---

## 2. 目标与成功度量

### 2.1 目标

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-ASH-01** | 生产代码 **零** Python `assert` 语句（`travelogue/`） | CI lint 或扫描脚本 = 0；见 §6.1 | **M1** |
| **G-ASH-02** | e2e **禁止新增** `wait_for_timeout`；存量清零或白名单 ≤3 且注明理由 | 扫描 + PR checklist | **M2** |
| **G-ASH-03** | 新增/改动的 e2e 用例优先使用 Playwright `expect()` | `TESTING.md` 约定 + 抽查 AC | **M2** |
| **G-ASH-04** | `TESTING.md` 写入断言约定；DoD 引用该节 | 文档合入 | **M0** |
| **G-ASH-05** | 热点源码断言降噪（home_v2 / toolbar 至少各减一簇） | 见 §7.3 AC | **M3** |
| **G-ASH-06** | 过宽 `pytest.raises(Exception)` 清零 | 全库扫描 = 0 | **M1** |

### 2.2 非成功指标（刻意不追）

- 全库消息 assert 占比升到某阈值（如 50%）——成本过高，改为「触达文件顺手补」。
- e2e 全部改写为 expect——存量允许渐进，**新增**强制。

### 2.3 用户/运维可感知差异（须登记）

| # | 差异 | 来源 | 沟通 |
|---|------|------|------|
| DIFF-ASH-01 | 某生产路径在 `-O` 下从「静默坏数据 / 二次崩溃」变为**显式业务错误** | M1 生产 assert 替换 | release note 开发者段（用户通常无感） |
| DIFF-ASH-02 | 极少数内部错误文案从 `AssertionError` 变为 `XxxError: …` | M1 | 仅日志/API 错误体；前端 toast 若依赖原文案须同步 |

---

## 3. 设计决策

| # | 决策 | 说明 |
|---|------|------|
| **D-ASH-01** | **生产禁止 Python `assert` 语句** | 不变量 → `raise XxxError(code, msg)` 或既有 `assert_*` 守卫；类型检查用 `isinstance` + raise，不用 `assert isinstance` |
| **D-ASH-02** | **保留并推广命名 `assert_*` 守卫** | 名字可含 assert，但实现必须是显式 raise；禁止守卫内部再写裸 `assert` |
| **D-ASH-03** | **e2e 断言契约：expect 优先** | 新文件/新用例默认 `expect(locator)…`；`wait_for_timeout` 需同行注释 `# ASH-SLEEP: <理由>` 且进白名单评审 |
| **D-ASH-04** | **行为断言 > 源码字面量** | 源码字符串断言仅允许「防漂移白名单」contract 测试，且集中、短小、有注释 `ASH-CONTRACT` |
| **D-ASH-05** | **raises 必带具体类型 + 建议 match** | 禁止 `pytest.raises(Exception)` / `BaseException`；业务路径优先错误码子串 |
| **D-ASH-06** | **不做 soft-assert 栈** | 多断言失败用拆用例或 helper 聚合消息一次 fail |
| **D-ASH-07** | **门禁轻量** | M1 用脚本/AST lint 挡生产 assert；不引入重型框架 |
| **D-ASH-08** | **机会主义还债** | M3 之后：改到某测试文件时顺手补消息 / 换 expect；无全库 deadline |

---

## 4. 生产 assert 施工清单（ASH-P-01）

> 目标：11 → 0。每处给出推荐替换策略；实现时选**该模块已有错误类型**，避免新造异常体系。

| # | 位置 | 现状 | 推荐替换 | 风险 |
|---|------|------|----------|------|
| R-01 | `llm/client.py:216` | `assert last_http is not None` 后读 body raise `LlmError` | 若 `last_http is None`: `raise LlmError("E_LLM_HTTP", "no HTTP response after retries")` | 低；覆盖「全重试无响应」理论路径 |
| R-02 | `cover_engine/joint.py:213` | `assert best is not None` | `raise CoverError` / 既有封面错误类型，或 fail-open 明确策略（与上段 `best_unsafe` 逻辑一致） | 中；须确认空候选时产品期望 |
| R-03 | `cover_engine/joint.py:396` | 同上（第二处） | 同 R-02 | 中 |
| R-04 | `export/output_recipe/resolve.py:418-420` | intent 集合 + `"九宫格" not in label` | `raise ValueError` / recipe 领域错误；文案用常量/intent 枚举，禁 magic string 散落 | 低 |
| R-05 | `export/platform_longshot.py:495` | `assert canvas_bytes and plan` | `raise LongshotExportError("E_LNG2_…", …)` | 低 |
| R-06 | `media/reexport.py:44` | `assert source_path is not None`（前已 catch missing） | `raise IngestError("E_MEDIA_SOURCE_MISSING", …)` 或 `RuntimeError` 不可达注释 + raise | 低 |
| R-07 | `media/ingest_parallel.py:156` | `assert isinstance(build_ctx, …)` | `if not isinstance(...): raise TypeError(...)` | 低 |
| R-08 | `layout_templates/legacy_bridge.py:274` | `assert isinstance(template, TemplateDef)` | 同 R-07 风格 | 低 |
| R-09 | `layout_templates/p17_research.py:54` | `assert best_perm is not None` | 空输入 early return / raise `ValueError`；research stub 可保留显式错误 | 低（research） |
| R-10 | `web/studio_lifecycle.py:71` | `assert last_err; raise last_err` | `raise last_err if last_err else OSError("bind failed")` | 低 |

**验收命令（M1）**：

```powershell
python scripts/lint_no_runtime_assert.py
# 或临时：python -c "..." 扫描 travelogue/ 行首 assert → 期望 0
```

（脚本在 M1 落地；见 §6.1。）

---

## 5. e2e 硬化清单（ASH-P-02）

### 5.1 固定 sleep 存量

| 文件 | 约计处数 | 改造策略 |
|------|----------|----------|
| `tests/e2e/test_studio_home_v2_ac_playwright.py` | 12 | 主题切换 / 可见性 → `expect(locator).to_be_visible()` / `to_have_attribute`；动画完成用 `expect.poll` 或 class 断言 |
| `tests/e2e/test_breath_lenis_scroll_playwright.py` | 3 | scroll 稳定用 `expect.poll` 对 `scrollY`；Lenis class 用 `to_have_class` |
| `tests/e2e/test_import_wizard_v3_playwright.py` | 1 | 步骤就绪 → expect 目标控件 |
| `tests/e2e/test_bsp_surface_playwright.py` | 1 | 同上 |

### 5.2 迁移模板（规范）

```python
from playwright.sync_api import expect

# 推荐
expect(page.locator("#studio-home-v2")).to_be_visible(timeout=10_000)
expect(page.get_by_role("button", name="开始导入")).to_be_enabled()

# 禁止（无注释）
page.wait_for_timeout(400)

# 例外（须注释）
page.wait_for_timeout(300)  # ASH-SLEEP: CSS transition 300ms, no stable selector yet
```

### 5.3 定位优先级（写入 TESTING.md）

1. `get_by_role` / `get_by_label`
2. `data-testid`（新增控件时优先补）
3. `#id`（现有稳定 id 可保留）
4. 可见文案（少量关键句；避免整页文案 roulette）

---

## 6. 工作包与里程碑

```text
M0 约定落地（0.5d）
  └─ TESTING.md 断言节 + DoD 勾选 + README 索引

M1 生产止血 + 过宽 raises（1–2d）
  ├─ R-01..R-10 生产 assert → raise
  ├─ lint_no_runtime_assert.py + CI（test-pr 或 lint job）
  └─ pytest.raises(Exception) → 具体类型

M2 e2e 现代化（2–3d）
  ├─ 清零 / 白名单 wait_for_timeout
  ├─ 热点 e2e 文件引入 expect()（home_v2 AC / wizard / breath）
  └─ PR 模板勾选「新 e2e 已用 expect」

M3 单测降噪 + helper（2–3d，可拆 PR）
  ├─ home_v2 / preview_toolbar 源码断言收敛为 contract 块
  ├─ 抽 1–2 个 assert_*_contract helper
  └─ 循环内 assert 补索引消息（触达文件）
```

| 里程碑 | 工期（估） | 依赖 | 可独立合并 |
|--------|-----------|------|------------|
| **M0** | 0.5 人日 | 无 | ✅ |
| **M1** | 1–2 人日 | M0（可并行写文档） | ✅ |
| **M2** | 2–3 人日 | M0；建议 M1 后 | ✅（可分子 PR） |
| **M3** | 2–3 人日 | M0；与产品改 UI 冲突时延后 | ✅ |
| **合计** | **约 6–9 人日** | | 建议 3–5 个小 PR |

### 6.1 M1 门禁脚本规格

**路径**：`scripts/lint_no_runtime_assert.py`

| 规则 | 说明 |
|------|------|
| 扫描根 | `travelogue/**/*.py` |
| 匹配 | 语句级 `assert`（AST `ast.Assert`），非名字含 assert 的调用 |
| 豁免 | 无；若未来测试辅助误入包内，用显式 `# ash: allow-assert` + 评审 |
| CI | 挂 `lint` 或 `test-pr`；失败输出文件:行 |
| 退出码 | 发现 ≥1 → 非 0 |

### 6.2 机会主义还债（M3 后持续）

触达测试文件时：

- 给**本函数内失败最难懂的 1–3 条** assert 补消息；
- e2e 改到的步骤优先换成 `expect`；
- 删除已无意义的源码字面量断言。

无全库 KPI、无强制 deadline。

---

## 7. 单测降噪策略（ASH-P-03 / M3）

### 7.1 热点文件

| 文件 | 约计 assert | 策略 |
|------|-------------|------|
| `tests/unit/web/test_studio_home_v2.py` | ~393 | 主题/模块存在性 → 集中 `ASH-CONTRACT` 块；行为留给 e2e；删重复 CSS 片段断言 |
| `tests/unit/web/test_preview_toolbar_v3.py` | ~304 | import 图改为「导出符号存在」或模块加载 smoke；路径字符串断言合并为表驱动一条 |

### 7.2 Contract 块模板

```python
# ASH-CONTRACT: homepage v2 theme registry — 故意锁字面量防漂移
def test_v2_theme_registry_contract() -> None:
    store = (STUDIO_DIR / "homepage-v2" / "store.js").read_text(encoding="utf-8")
    assert "V2_THEME_DEFAULT" in store, "theme default export missing"
    # 仅锁关键常量，不锁整段数组格式化空白
```

### 7.3 M3 验收（最低）

| AC | 口径 |
|----|------|
| AC-ASH-M3-01 | `test_studio_home_v2.py` 中「整行 `export const V2_THEME_IDS = […]`」类精确格式断言 **删除或改为字段级** |
| AC-ASH-M3-02 | `test_preview_toolbar_v3.py` 连续 import-path 字面量断言 **合并或删减 ≥30%**（相对开工基线行数/条数） |
| AC-ASH-M3-03 | 新增至少 1 个共享 helper，被 ≥2 测试引用 |

---

## 8. 文档交付：TESTING.md 断言约定（草案 · M0 合入）

> 以下内容作为 M0 补丁直接写入 [TESTING.md](./TESTING.md) 新章节（建议 §10）。

### 10. 断言约定（Assertion Style）

#### 10.1 生产代码

- **禁止**在 `travelogue/` 使用 Python `assert` 语句做运行时校验。
- 不变量使用显式 `raise` 或既有 `assert_*` 领域守卫（守卫内部亦不得用裸 `assert`）。
- CI：`python scripts/lint_no_runtime_assert.py`。

#### 10.2 单元 / 集成测试

- 优先断言**可观察行为**、返回值、错误码；避免大段 HTML/JS/CSS 源码字面量。
- 源码契约测试须标注 `# ASH-CONTRACT`，并保持短小。
- `pytest.raises` 使用**具体异常类型**；业务错误建议 `match=` 错误码。
- 浮点 / ML 分数使用 `pytest.approx`。
- 循环内 assert 须带循环变量上下文（id / index）。
- 新写断言**鼓励**带失败消息；不要求回填全库。

#### 10.3 Playwright e2e

- 使用 `from playwright.sync_api import expect` 做 UI 断言（自动重试）。
- **禁止**无注释的 `page.wait_for_timeout`；例外格式：`# ASH-SLEEP: <理由>`。
- 定位优先级：role/label → testid → id → 少量文案。
- 单测文件避免 assertion roulette：一个场景一个主断言簇。

---

## 9. 验收标准（Definition of Done）

### 9.1 里程碑门禁

| 里程碑 | 必过 |
|--------|------|
| M0 | `TESTING.md` 含 §断言约定；`docs/README.md` 索引本 PRD；DoD/QUALITY-GATE 有引用或勾选 |
| M1 | `lint_no_runtime_assert.py` = 0；生产 11 处已替换；`pytest.raises(Exception)` = 0；相关 unit 绿 |
| M2 | `wait_for_timeout` = 0 或白名单表（本 PRD §5.1 更新）；home_v2 / wizard / breath 至少各有 **1** 处 `expect(`；e2e job 绿 |
| M3 | §7.3 三条 AC 满足；无全库强制 |

### 9.2 回归命令（合并前）

```powershell
python scripts/lint_no_runtime_assert.py
python -m pytest tests/unit/llm tests/unit/cover_engine tests/unit/export tests/unit/media tests/unit/layout_templates tests/unit/web/test_studio_lifecycle.py -q
python -m pytest tests/e2e/test_breath_lenis_scroll_playwright.py tests/e2e/test_import_wizard_v3_playwright.py -q
# 完整 e2e 按 CI test-e2e
```

### 9.3 结案产物

- [ ] 本 PRD 状态 → **Done**
- [ ] `docs/acceptance-records/ash-closeout-YYYY-MM-DD.md`（扫描前后对比表）
- [ ] 若有 DIFF-ASH-*：release note 开发者段一行说明

---

## 10. 风险与回滚

| 风险 | 影响 | 缓解 | 回滚 |
|------|------|------|------|
| 封面 `best is None` 语义判断错 | 封面失败形态变化 | R-02/R-03 单测覆盖空候选；对照现网 fail-open | 单文件 revert |
| e2e 改 expect 后超时变多 | CI 变红 | 合理 timeout；先改 flake 最高文件 | 按文件 revert |
| lint 误伤（未来生成代码） | CI 堵 | AST + 显式豁免注释 | 豁免单点 |
| M3 与 UI 大改冲突 | 冲突成本 | M3 可延后；不堵 M1/M2 | 跳过 M3 |

---

## 11. 排期建议与 PR 切片

| PR | 内容 | 建议标题 |
|----|------|----------|
| PR-1 | M0 文档 | `docs: add assertion hardening conventions (ASH M0)` |
| PR-2 | M1 生产 assert + lint | `fix: replace runtime asserts; add lint_no_runtime_assert` |
| PR-3 | M1b raises 收窄 | `test: narrow pytest.raises(Exception) usages` |
| PR-4 | M2 e2e sleep→expect（可再拆） | `test(e2e): prefer Playwright expect; remove fixed sleeps` |
| PR-5 | M3 单测降噪 | `test: reduce source-string assertion coupling (ASH M3)` |

**与并行工作的关系**：可与功能 PR 并行；**M1 lint 合入后**，其他分支若新增生产 `assert` 会被挡住——属预期。

---

## 12. 开放问题

| # | 问题 | 默认假设 | 需谁拍板 |
|---|------|----------|----------|
| Q-01 | 封面无候选时：raise vs fail-open 占位图？ | 保持与当前 `best_unsafe` fail-open 一致；仅在双空时 raise | 算法 / 产品 |
| Q-02 | `wait_for_timeout` 是否允许「动画 300ms」白名单长期存在？ | M2 尽量清零；≤3 条临时白名单，90 天内清 | 测试负责人 |
| Q-03 | lint 挂 lint job 还是 test-pr？ | 挂现有 `lint` job（更快失败） | 工程 |
| Q-04 | M3 是否本季度必做？ | **Should**；不堵发布；WIP 紧张时可 parking lot | 产品排期 |

---

## 13. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.2-ASH | 2026-07-16 | M2：e2e 去固定 sleep（白名单仅 1 处 ASH-SLEEP 竞态）；引入 expect / wait_for_function |
| v1.0.1-ASH | 2026-07-16 | M0+M1 落地：TESTING §9、lint_no_runtime_assert、11 处生产 assert→领域 raise、raises(Exception) 收窄 |
| v1.0.0-ASH | 2026-07-16 | 初稿：全库扫描证据 + M0–M3 计划 + TESTING 约定草案 + 生产 10 项施工单 |

---

## 附录 A · 生产 assert 快速索引

```
travelogue/llm/client.py:216
travelogue/cover_engine/joint.py:213
travelogue/cover_engine/joint.py:396
travelogue/export/output_recipe/resolve.py:418
travelogue/export/output_recipe/resolve.py:420
travelogue/export/platform_longshot.py:495
travelogue/media/reexport.py:44
travelogue/media/ingest_parallel.py:156
travelogue/layout_templates/legacy_bridge.py:274
travelogue/layout_templates/p17_research.py:54
travelogue/web/studio_lifecycle.py:71
```

## 附录 B · 审计复现命令

```powershell
# 在仓库根目录
python -c @"
import pathlib, re
def count(pat, base):
    n=f=0
    for p in pathlib.Path(base).rglob('*.py'):
        if '__pycache__' in p.parts: continue
        t=p.read_text(encoding='utf-8')
        m=len(re.findall(pat,t,re.M))
        if m: f+=1; n+=m
    return f,n
print('prod', count(r'^\s*assert ', 'travelogue'))
print('tests', count(r'^\s*assert ', 'tests'))
print('msg', count(r'assert .*,\s*[\"\']', 'tests'))
print('expect', count(r'from playwright.*import expect|\bexpect\(', 'tests/e2e'))
print('sleep', count(r'wait_for_timeout', 'tests/e2e'))
"@
```
