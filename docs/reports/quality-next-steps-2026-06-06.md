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
| P1-3 | 人工：小文件夹上传 → preview | ☐ | 见 `RUNBOOK-DOGFOOD.md` §M21-0 |
| P1-4 | 人工：发布后 `/` v2、`/classic` 应急、漏斗指标 | ☐ | 见 `M21-CUTOVER-CHECKLIST.md` §1–2 |
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
