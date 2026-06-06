# 质量后续任务清单 · 2026-06-06

> 来源：P2 完成后的代码质量负责人建议。状态在本会话自动化验证中更新。

## P0 · CI 与仓库卫生

| ID | 任务 | 状态 | 备注 |
|----|------|------|------|
| P0-1 | 确认远端 CI 全绿 | ◐ | 仓库私有无法 API 拉取；推送后请在 GitHub Actions 确认 |
| P0-2 | 处理 `trips/linzhi` 脏文件 | ☑ | 仅为 export 缓存版本号变更，已 `git restore` |

## P1 · M21 dogfood 验收

| ID | 任务 | 状态 | 备注 |
|----|------|------|------|
| P1-1 | 门控单元测试 `test_studio_home_v2.py` | ☑ | 37 passed |
| P1-2 | 上传/续跑 Playwright（HP2-16、retry upload、pending 清理） | ☑ | 3 passed |
| P1-3 | 人工：小文件夹上传 → preview | ☐ | 手测：[M21-MANUAL-SMOKE.md](../studio-homepage-v2/M21-MANUAL-SMOKE.md) §1 |
| P1-4 | 人工：发布后 `/` v2、`/classic` 应急、漏斗指标 | ◐ | 路由：`m21_deploy_smoke.py --base URL`；漏斗 telemetry 仍手测 · [M21-MANUAL-SMOKE.md](../studio-homepage-v2/M21-MANUAL-SMOKE.md) |
| P1-5 | 更新 `studio-homepage-v2-rollout-log.json` | ☑ | 已写入自动化验证条目 |

## P1 · 算法 V2 盲评

| ID | 任务 | 状态 | 备注 |
|----|------|------|------|
| P1-V1 | `algorithm_v2_signoff --from-json` 自动化 gate | ☑ | `ok: true`（aM1/aM7） |
| P1-V2 | 10 本 album 填 `judgeVerdict` A/B/C | ☐ | 需人工盲评；当前为 synthetic fixture |
| P1-V3 | 落地真实 trip（`trips/mao` 等）替换 signoff albums | ☐ | `trips/mao` 尚未入库 |
| P1-V4 | 盲评工具 | ☑ | `scripts/cover_selection_blind_review.py` + `scripts/algorithm_v2_signoff.py` |

**盲评操作顺序：**

```bash
# 1. 真实 trip 就绪后初始化 albums
python scripts/cover_selection_blind_review.py --trip-dir trips/mao --export-layout mobile

# 2. 刷新 signoff 自动化分
python scripts/algorithm_v2_signoff.py --score-automated --write

# 3. 人工填 judgeVerdict 后验证
python scripts/algorithm_v2_signoff.py --from-json docs/acceptance-records/algorithm-v2-signoff.json
```

## P2 · Mosaic legacy 审计

| ID | 任务 | 状态 | 备注 |
|----|------|------|------|
| P2-1 | `legacy.py` 不含退役 pattern 分支 | ☑ | size=5 仅 main-portrait-3land；退役由 `pattern_policy` 拦截 |
| P2-2 | `append_legacy_window` 拒绝退役 patternId | ☑ | 新增回归测试 |
| P2-3 | self-heal `degrade_stable_pattern` 路径 | ☑ | 新增单元测试 |

## P3 · 质量基建

| ID | 任务 | 状态 | 备注 |
|----|------|------|------|
| P3-1 | CI ruff 扩展至 `travelogue/web/studio_handlers` | ☑ | lint job 已更新 |
| P3-2 | 全仓 ruff 门禁 | ☐ | 暂缓（~1100 E501 等） |
| P3-3 | coverage `--cov-fail-under` 提至 65% | ☑ | CI 已改为 65（本地 ~69%） |
| P3-4 | CI ruff 扩展至 `travelogue/curation` | ☑ | 50 处 auto-fix，lint 全绿 |
| P3-5 | mosaic `state.py` / `selfheal` 补测 | ☑ | `test_mosaic_state.py` + self-heal 单元测试 |

## P1 · M21 / 算法 V2（已暂缓）

人工 dogfood 与盲评签核暂不推进；发布前再打开 `M21-CUTOVER-CHECKLIST` / `algorithm-v2-signoff.json`。

## 方向 B · M21 文档债（2026-06-06）

| ID | 任务 | 状态 |
|----|------|------|
| B1 | [M21-ROUTING.md](../studio-homepage-v2/M21-ROUTING.md) 路由权威 | ☑ |
| B2 | [M21-RELEASE-NOTES.md](../studio-homepage-v2/M21-RELEASE-NOTES.md) 发版模板 | ☑ |
| B3 | TELEMETRY / FEATURE-FLAG / Runbook 同步 | ☑ |
| B4 | 根 README Studio 路由表 | ☑ |
| B5 | gate_status · audit_v2_scroll 脚本口径 | ☑ |

---

## Wave 4–5 收口（2026-06-06）

| 项 | 状态 | 命令 / 备注 |
|----|------|-------------|
| Algorithm V2 signoff `--extended` | ☑ | A-M1/A-M7/D-M1 LOO；A-M4 8/10 信息项 |
| Phase 15 延后项文档 | ☑ | epilogue / replan 移出延后表 |
| `phase15_unified_gate` | ☑ | `PASS unified_mode gate` |
| Phase 6 基线 JSON | ☑ | `python scripts/phase6_metrics_baseline.py --summary --write` |
| Phase 13 回滚演练 | ☑ | `docs/acceptance-records/phase13-rollback-drill.json` |
| P5 layout sprint 合成记录 | ☑ | `docs/acceptance-records/phase5-layout-sprint.json` |
| Phase 4 自动化 gate | ☑ | unit：`--skip-integration`（CI validate）；integration：全量（CI test-integration） |
| M21 dogfood gate | ☑ | `--skip-e2e` 60 passed；全量 63 + rollback 4 |
| Recasa 只读对比 | ☑ | `recasa_readonly_compare.py --fixture golden-mixed-scenes` → `not_integrated`（预期） |
| IMPLEMENTATION 对账 | ☑ | Phase 4/7/15 头表 · 2026-06-06 |

**Wave 5 剩余（可选）：** M21 手测签字（§1 上传→preview）、telemetry 漏斗 24h 观察。
