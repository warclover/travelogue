# Studio 首页 v2 · Holdback 回滚 Runbook（M20-i / M20-j）

> 对照 [TELEMETRY.md](./TELEMETRY.md) §3–§4、[FEATURE-FLAG.md](./FEATURE-FLAG.md) §3–§4、PRD §17.2。  
> **Owner**：平台 / on-call（待指派，见 [OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md) `OQ-TELEMETRY`）。

---

## 1. 演练节奏

| 频率 | 动作 | 命令 |
|------|------|------|
| **每次发版前** | AC + v3 回归 | `pytest tests/test_studio_home_v2*.py tests/test_studio_p8_regression.py -q` |
| **Nightly** | 合并 holdback 报告 | GitHub Actions [`.github/workflows/nightly-holdback.yml`](../../.github/workflows/nightly-holdback.yml)（funnel 必过 + LCP×10 审计 artifact） |
| **Nightly（本地）** | 同上 | `python scripts/studio_homepage_m20i_drill.py --spawn --synthetic --lcp-runs 10 --out reports/holdback.json` |
| **10% 灰度期** | 读真实 jsonl + LCP | `python scripts/studio_homepage_m20i_drill.py --telemetry ~/.travelogue/telemetry/studio-homepage-events.jsonl --lcp-base http://127.0.0.1:8766 --out holdback.json` |
| **告警触发** | 按 §2 回滚 | 见下文 |

分步脚本（可选）：

```bash
# 漏斗聚合
python scripts/studio_telemetry_aggregate.py --out reports/funnel.csv

# LCP 分 variant
python scripts/studio_lcp_measure.py --base http://127.0.0.1:8766 --runs 10 --out reports/lcp.json

# 合并 §17.2 判据
python scripts/studio_holdback_report.py --telemetry ~/.travelogue/telemetry/studio-homepage-events.jsonl --lcp-json reports/lcp.json --out reports/holdback.json
```

**CI 门禁**：`holdback.json` 中 `should_rollback: true` 或脚本 exit code `1` → 阻塞放量。

---

## 2. §17.2 回滚判据（自动）

| 判据 | 阈值 | 数据源 |
|------|------|--------|
| import 转化率 | v2 较 v3 **↓>15%** | jsonl `import_success/import_start` |
| CTA 点击率 | v2 较 v3 **↓>20%**（按 PV） | jsonl `cta_click/homepage_view` |
| LCP P95 | v2 较 v3 **↑>30%** | Playwright LCP/FCP |
| JS error rate | v2 较 v3 **↑>2×** | jsonl `js_error/homepage_view` |

**禁止**：10% 阶段仅用历史 v3 baseline 自动回滚（必须 v2/v3 **同期** holdback）。

报告字段：`flags.classified.rollback` · `should_rollback`。

---

## 3. 回滚步骤（紧急 · `TRAVELOGUE_STUDIO_HOMEPAGE_V2=off`）

### 3.1 停止 v2 放量（< 5 min）

1. 设置环境变量 **`TRAVELOGUE_STUDIO_HOMEPAGE_V2=off`**（或 yaml `percent: 0`）。
   yaml 片段见 [`config-holdback.example.yaml`](./config-holdback.example.yaml)。
2. 重启 Studio 进程（`serve --studio` 或等价部署单元）。
3. 验证 **`GET /` → v3**（`studio.html`），**不** 302 到 `/v2`：

   ```bash
   curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://127.0.0.1:8766/
   ```

4. `GET /v2` 仍可 200（开发对照），但生产流量应仅命中 `/`。

### 3.2 用户态验证（< 15 min）

**一键自动化**（推荐）：

```bash
python scripts/studio_homepage_rollback_drill.py --out docs/acceptance-records/studio-homepage-v2-rollback-drill.json
```

在 loopback 或 staging 执行：

| 检查项 | 命令 / 路径 |
|--------|-------------|
| v3 首页 DOM 回归 | `pytest tests/test_studio_home_v2.py::test_studio_home_gate_off_serves_v3_at_root -q` |
| Import 续 poll | `/v2?dev=1&studioState=importing-resume&studioJob=running` → 刷新后 `#v2-import-cancel` 可见 |
| sessionStorage 未清 | `activeJobId` / `activePending` **不得** bulk 清除 |
| 书架 / FirstSuccess | harness `idle-returning` / `first-success` 走查 |

### 3.3 回滚后监控（24h）

1. 继续跑 `studio_telemetry_aggregate.py`，确认 v3 漏斗恢复。
2. 记录事件到 `docs/acceptance-records/`（rollout log JSON，模板可参考 phase6）。
3. 根因分析：区分 LCP / 转化 / JS error；修复后再走 **M20-j 放量 checklist**。

---

## 4. 恢复放量（M20-j checklist）

- [ ] `should_rollback: false` 连续 **3** 个 nightly
- [ ] 设计 demo 切图包 sign-off（非 PLACEHOLDER）
- [ ] AC 自动集全绿（`test_studio_home_v2_ac_playwright.py`）
- [ ] 门控 e2e 全绿（`test_studio_home_v2.py` gate 用例 + `test_studio_homepage_gate.py`）
- [ ] `TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto` + `PERCENT=10` 演练进组/对照 UA
- [ ] PM sign-off 10% → 100% 计划
- [ ] on-call 确认 Slack/邮件告警已接 jsonl 聚合

**门控冒烟**（不启动服务器）：

```bash
# 默认 off → / serve v3
python scripts/studio_homepage_gate_status.py

# 10% holdback · 进组 UA
TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT=10 \\
  python scripts/studio_homepage_gate_status.py --ua "M20jTest/5"

# 100% on → / serve v2（无 redirect）
TRAVELOGUE_STUDIO_HOMEPAGE_V2=on python scripts/studio_homepage_gate_status.py
```

**100% 切主站**：`TRAVELOGUE_STUDIO_HOMEPAGE_V2=on` → `GET /` 直接 v2；v3 迁 `GET /classic`。

---

## 5. 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| `INSUFFICIENT_DATA` | jsonl 无 v2/v3 同期 | 延长灰度窗口；检查 `meta.variant` |
| LCP 仅 FCP | headless 无 LCP 条目 | 报告 `metric=fcp`；用有头 Chromium 复测 |
| 误报 ROLLBACK | 样本过少 | `--lcp-runs` ≥10；24h 窗口聚合 |
| import 转化骤降 | pipeline 回归 | 查 `import_failed` / 后端 job store |

---

## 6. 相关文件

| 文件 | 说明 |
|------|------|
| `scripts/studio_homepage_m20i_drill.py` | 一键演练 |
| `scripts/studio_holdback_report.py` | 合并报告 |
| `scripts/studio_telemetry_aggregate.py` | 漏斗聚合 |
| `scripts/studio_lcp_measure.py` | LCP/FCP 采集 |
| `travelogue/web/studio_homepage_gate.py` | `TRAVELOGUE_STUDIO_HOMEPAGE_V2` |
| `scripts/studio_homepage_gate_status.py` | 门控决策冒烟（M20-j） |
| `scripts/studio_homepage_rollback_drill.py` | 回滚演练一键（§3.2） |
| `scripts/studio_ac_visual_capture.py` | 视觉 sign-off 截图 |
| `tests/test_studio_m20i_drill.py` | 演练脚本 CI |
