# 架构优化 · 里程碑状态追踪

> 配套 [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) v1.1 · 执行提示词见 [PROMPTS-ARCH-OPTIMIZATION.md](./PROMPTS-ARCH-OPTIMIZATION.md)

**当前分支**: `arch/optimization-ws1`  
**最后更新**: 2026-07-08

## 里程碑总表

| 里程碑 ID | 状态 | 完成日期 | 证据摘要 | 遗留项 |
|-----------|------|----------|----------|--------|
| M-A0 | done | 2026-07-08 | `python scripts/_m_a0_config_equivalence_check.py` 全绿；无重复顶层键；load_config 与合并前后段生效值一致 | — |
| M-A1a | done | 2026-07-08 | `pytest tests/test_trip_service_update.py` 7 passed | — |
| M-A1b | done | 2026-07-08 | handlers 14 处 + serve.py 2 处改 svc.update；409 E_TRIP_CONFLICT + http.js 重试；`pytest tests/test_studio_handlers_trip.py` 等 41 passed | — |
| M-A1c | done | 2026-07-08 | studio_pipeline 5 处 + studio_narrate 1 处改 update；`tests/test_trip_cross_process_update.py` spawn 集成测试通过 | 文件锁补强（.trip.lock）跳过 |
| M-A1d | done | 2026-07-08 | render/engine.py + orchestrator/run.py + CLI/export 收口 persist_trip_snapshot | — |
| M-A1e | done | 2026-07-08 | `scripts/lint_trip_save_calls.py` + CI；AC-ARC-01/02 测试；`test_trip_concurrent_save.py` 改写 | — |
| M-A2 | done | 2026-07-08 | 重复键 ConfigError（含行号）；未知键单条 warning / strict 报错；`pytest tests/test_config_fail_loud.py` 5 passed；example 零告警回归 | — |
| M-A3 | done | 2026-07-08 | `.gitignore` 增加 registry.cache.json / trips/.cache/；registry.cache 移出索引；import-wizard.js 索引无正反斜杠重复 | — |
| M-B5 | done | 2026-07-08 | `scripts/lint_trip_json.py` + CI validate/lint；`e2e_trip_acceptance` 接入；13 fixtures + `pytest tests/test_lint_trip_json.py` 6 passed | — |
| M-B0 | done | 2026-07-08 | `scripts/arch_equivalence_check.py` 自反性冒烟；`lint-imports` 26 豁免全绿；CI lint+validate；TECH-ARCH §18 | grimp 未解析的 media→curation 等 AST 违例留 M-B1 |
| ADR-015 | accepted | 2026-07-08 | ADR 已批准；cross-import 51→44（B4a 后） | M-B4b 可启动 |
| M-B4a | done | 2026-07-08 | kernel→layout_contract；adapter 收敛；mosaic ContextVar；render_fingerprint；equivalence 全绿 | B4b 目标 cross-import ≤10（现 44） |
| M-B2 | todo | — | — | 需 G-WIP-01 |
| M-B3 | todo | — | — | 需 M-B2 Go + G-WIP-01 |
| M-C4 | todo | — | — | — |
| M-B4b | todo | — | — | ADR-015 已批；待启动 |
| M-B1 | todo | — | — | — |
| M-B6 | todo | — | — | — |
| M-C1 | todo | — | — | 触发：新增 Studio API |
| M-C2 | todo | — | — | 触发：与 M-B4b 错开 |
| M-C3 | todo | — | — | 触发：Phase 验收完成 |
| M-C5 | todo | — | — | 需 G-WIP-02 |
| M-C6 | todo | — | — | GLOSSARY 立即可做；改名需 G-WIP-03 |
| M-D1 | todo | — | — | 开关满 4 周 DoD |

## 开关台账

| 开关 | 上线日期 | 4 周 DoD 到期 | 备注 |
|------|----------|---------------|------|
| `pipeline.orchestration` | — | — | M-B3 登记 |
| `layout.planner_impl` | — | — | M-B4b 登记 |

## 发现问题

（范围外问题仅记录，不在当前里程碑修复）

---

## WS1 执行顺序

P-00 ✓ → … → P-10 (ADR-015) ✓ → P-14 (M-B4a) ✓ **WS2 进行中**
