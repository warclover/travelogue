# ASH · 结案记录（2026-07-16）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-ASSERTION-HARDENING-V1](../PRD-ASSERTION-HARDENING-V1.md) → **Done** |
| **合入** | 直合 `master`（见下方提交链；Actions 配额耗尽期间以本地门禁为准） |
| **下一波** | 机会主义还债（D-ASH-08）；无新 ASH 里程碑 |

## 1. 交付提交

| 提交 | 里程碑 |
|------|--------|
| `84a9ada` | M0：PRD + TESTING §9 + lint 脚本 + DoD/QG/README |
| `af3bd33` | M1：生产 runtime assert → 领域 raise；`pytest.raises(Exception)` 收窄 |
| `c1b46f2` | M2：e2e 去固定 sleep；引入 `expect` / `wait_for_function` |
| `549e645` | M3：`_ash_source_contracts`；home_v2 / toolbar 源码断言降噪 |
| `9045937` | PRD 标记 M0–M3 完成（待本结案） |

## 2. 扫描前后对比

| 指标 | 开工基线（§1.1） | 结案 |
|------|------------------|------|
| `travelogue/` 运行时 `assert`（AST） | 9 文件 / 11 处 | **0**（`lint_no_runtime_assert.py` OK） |
| e2e `wait_for_timeout` | 4 文件 / 17 处 | **0**（`tests/e2e`） |
| e2e `expect(` | 0 | home_v2 / wizard / breath 等已引入 |
| `pytest.raises(Exception)` | 存在 | **0**（`tests/`） |
| M3 主题精确格式行 | 整行 `export const V2_THEME_IDS = […]` | 字段级 `assert_exported_*` |
| M3 toolbar import-path | 约 11 条散落 | 合并为 contract 块（约 −36%） |

## 3. 本地门禁证据（2026-07-16 · 无远程 CI）

```text
python scripts/lint_no_runtime_assert.py
→ lint_no_runtime_assert: OK

python -m pytest tests/unit/llm tests/unit/cover_engine tests/unit/export `
  tests/unit/media tests/unit/layout_templates -q
→ 409 passed, 3 skipped, 1 failed
  失败：tests/unit/export/test_export_zip_budget.py::test_share_zip_within_config_budget
  原因：Demo 路径 LLM HTTP 401（本地 API key），与 ASH 改动无关
```

e2e Playwright 全量未在本机重跑（耗时长 + Actions 配额用尽）；M2 改动已合入并以静态扫描（零 `wait_for_timeout`）验收。

## 4. 可感知差异（开发者）

| # | 说明 |
|---|------|
| DIFF-ASH-01/02 | 生产路径在 `-O` 下由静默失败改为显式 `XxxError` / `ValueError` 等；用户面通常无感，日志/API 错误体可能从 `AssertionError` 变为领域错误 |

## 5. 明确未做 / 后置

| 项 | 去向 |
|----|------|
| 全库裸 assert 补消息 | D-ASH-08 机会主义；无 KPI |
| unit 内 Playwright `wait_for_timeout`（toolbar / cover v5） | 非 e2e 范围；触达时再换 |
| 远程 CI 再验 | Actions 恢复后跑 lint + test-pr / e2e |

## 6. 结案声明

ASH V1 **主交付关闭**（M0–M3）。后续仅按 TESTING §9 约定执行；勿再向本 PRD 追加范围。
