# M21 测试矩阵（切主站与退役 v3）

> 目标：把 M21 的“能切、能回、能删”变成可执行门禁。

---

## 1. 必跑自动化（每个阶段）

```bash
pytest tests/test_studio_home_v2.py -q
pytest tests/test_studio_home_v2_ac_playwright.py -q
pytest tests/test_studio_homepage_gate.py -q
pytest tests/test_studio_homepage_gate_security.py -q
```

---

## 2. 分阶段门禁

## M21-0（v2 上传补齐）

- [ ] 新增/更新上传用例：小文件夹成功、超建议阈值确认、取消后状态收敛
- [ ] 导入续跑（刷新后）用例通过
- [ ] 不影响 pick-folder 既有路径

## M21-a（`/`=v2）

- [ ] `GET /` 返回 v2
- [ ] `GET /classic` 返回 v3
- [ ] preview 返回首页到 v2
- [ ] 回滚用例：`on -> off` 可恢复 v3

## M21-b（观察期）

- [ ] 每日 smoke 通过（首页、导入、预览）
- [ ] 至少一次回滚演练通过并记录（`on -> off -> on`）
- [x] Nightly 增加 `off + full` 回滚合同 smoke（`gate_off_serves_v3_at_root`）
- [ ] 无 P0/P1 事故

### M21-b 指标阈值（建议）

| 指标 | 观测窗口 | 建议阈值 |
|------|----------|----------|
| `import_success/import_start` | 24h 滚动 | 不低于近 7 天基线 90% |
| 上传失败率（upload 相关） | 24h 滚动 | 不高于近 7 天基线 + 5% |
| `js_error/homepage_view` | 24h 滚动 | 不高于基线 2x |
| `sheet_abandon/homepage_view` | 24h 滚动 | 不高于基线 + 20% |

建议命令（本地/狗食）：

```bash
python scripts/studio_telemetry_aggregate.py --out reports/m21-funnel.csv
python scripts/studio_lcp_measure.py --base http://127.0.0.1:8766 --runs 10 --out reports/m21-lcp.json
python scripts/studio_holdback_report.py --telemetry ~/.travelogue/telemetry/studio-homepage-events.jsonl --lcp-json reports/m21-lcp.json --out reports/m21-holdback.json
```

## M21-c（`/v2` 收敛）

- [x] `GET /v2` 302 到 `/`
- [ ] 旧书签可用
- [x] 文档与脚本路径更新完成

### M21-c 改造前置检查

- [x] `tests/test_studio_home_v2.py` 中所有 `/v2` 相关断言已区分“收敛前/收敛后”
- [x] runbook 与 dogfood 文档不再把 `/v2` 作为主路径
- [x] 预览页与 dev panel 不存在硬编码跳转到 `/v2`

## M21-d（测试迁移）

- [x] 所有 v3 静态断言已迁移或标记 legacy
- [x] `/classic` 最小 smoke 存在
- [ ] CI 全绿

## M21-e1（冻结）

- [ ] v3 文件冻结后 smoke 通过
- [ ] 一个发布版本内无 P0/P1

## M21-e2（删除）

- [ ] 删除后无共享模块断链
- [ ] 全量测试与 smoke 通过

---

## 3. 手工冒烟清单

| 场景 | 路径 | 预期 |
|------|------|------|
| 主入口 | `/` | v2 首页可交互 |
| 应急入口 | `/classic` | v3 可打开且可导入（最小保障） |
| 兼容入口 | `/v2` | M21-c 前 200；M21-c 后 302 `/` |
| 导入 | pick-folder / upload | 可发起并到 Importing |
| 续跑 | 刷新页面 | `activeJobId` 可恢复 |
| 预览返回 | trip preview | 返回 `/` 正常 |

---

## 4. 退出准则（Go / No-Go）

满足以下条件才可进入下一阶段：

- 自动化门禁全绿
- 手工冒烟全通过
- 回滚路径验证通过
- 指标未出现显著退化

否则：No-Go，停留当前阶段并修复。

