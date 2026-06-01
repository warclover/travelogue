# M20-j · 切主站 Sign-off 与观察窗

> P2 交付物 · 对照 [RUNBOOK-HOLDBACK.md](./RUNBOOK-HOLDBACK.md) §4、[FEATURE-FLAG.md](./FEATURE-FLAG.md) §3。  
> **当前默认**：`TRAVELOGUE_STUDIO_HOMEPAGE_V2=off`（故意保持，直至本清单全部 ✅ + PM 签字）。

---

## 1. 三阶段放量

| 阶段 | 环境变量 / 配置 | `/` 行为 | 最短观察窗 |
|------|-------------------|----------|------------|
| **Dogfood** | `auto` + yaml `percent: 10` | 10% 302→`/v2` | 7 天 |
| **Holdback** | `auto` + `percent: 10`（生产） | 同上 | **14 天** |
| **M20-j 切主站** | `on` | 200 serve v2；v3→`/classic` | 7 天 post-cutover |

观察窗内 **禁止** 升 `percent` 或切 `on`，除非 nightly `should_rollback: false` 连续 3 次且 PM 书面批准。

Rollout 日志模板：[`../acceptance-records/studio-homepage-v2-rollout-log.json`](../acceptance-records/studio-homepage-v2-rollout-log.json)

---

## 2. PM + 工程联合 Sign-off 清单

### 2.1 自动化（工程 Owner 签字）

- [ ] `pytest tests/test_studio_home_v2_ac_playwright.py -q` 全绿
- [ ] `pytest tests/test_studio_home_v2.py -k gate -q` 全绿
- [ ] Nightly holdback funnel 连续 **3** 天绿（GitHub Actions artifact）
- [ ] `python scripts/studio_homepage_rollback_drill.py` → exit 0
- [ ] `python scripts/studio_homepage_m20i_drill.py --spawn --synthetic --lcp-runs 10` 无 `should_rollback`（或 LCP 人工复核）

### 2.2 素材与体验（设计 / PM 签字）

- [ ] demo-showcase **非 PLACEHOLDER** WebP（[DEMO-ASSETS-BRIEF.md](./DEMO-ASSETS-BRIEF.md)）
- [ ] 视觉 sign-off 五张截图（[VISUAL-SIGNOFF.md](./VISUAL-SIGNOFF.md)）
- [ ] AC-01 可用性 **5/5** 被试（[USABILITY-AC01.md](./USABILITY-AC01.md)）
- [ ] iPad Safari 实机（[DEVICE-MATRIX-IPAD.md](./DEVICE-MATRIX-IPAD.md)）

### 2.3 运维（On-call 签字）

- [ ] Telemetry Owner 已指派（[OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md) OQ-TELEMETRY）
- [ ] Slack/邮件告警接 jsonl 聚合（[TELEMETRY.md](./TELEMETRY.md) §3）
- [ ] Dogfood 部署按 [RUNBOOK-DOGFOOD.md](./RUNBOOK-DOGFOOD.md) 验证
- [ ] 回滚 Runbook 值班演练记录写入 rollout log

### 2.4 切主站操作（M20-j · `on`）

1. 设 `TRAVELOGUE_STUDIO_HOMEPAGE_V2=on`，重启 Studio。
2. 验证 `GET /` → v2 HTML；`GET /classic` → v3。
3. 跑 `python scripts/studio_homepage_gate_status.py --json` 确认 `root_variant=v2`、`redirect_root_to_v2=false`。
4. 24h 监控 §17.2 判据；异常立即 §3 回滚。

**Editor 内链**：见 [EDITOR-LINKS-M20J.md](./EDITOR-LINKS-M20J.md)（结论：`href="/"` 在 `on` 模式下 **无需修改**）。

---

## 3. 签字栏（模板）

| 角色 | 姓名 | 日期 | 阶段 |
|------|------|------|------|
| PM | | | G1 holdback / G2 cutover |
| 工程 Lead | | | G0 / G2 |
| 设计 | | | 切图 + 视觉 |
| QA | | | AC + 实机 |
| On-call | | | 告警 + 回滚演练 |

---

## 4. 相关命令速查

```bash
# 回滚演练（生产前必跑）
python scripts/studio_homepage_rollback_drill.py --out docs/acceptance-records/studio-homepage-v2-rollback-drill.json

# 视觉截图归档
python scripts/studio_ac_visual_capture.py

# 门控决策
TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT=10 \\
  python scripts/studio_homepage_gate_status.py --ua "M20jTest/5" --json
```
