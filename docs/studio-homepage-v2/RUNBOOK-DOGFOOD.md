# Dogfood · Studio 首页 v2 Holdback 部署

> P4-23 · 10% 灰度前 staging / 团队内测环境配置。

---

## 1. 前置

- [ ] 设计切图包已替换 PLACEHOLDER（或团队接受占位图内测）
- [ ] Telemetry jsonl 目录可写：`~/.travelogue/telemetry/studio-homepage-events.jsonl`
- [ ] On-call 已读 [RUNBOOK-HOLDBACK.md](./RUNBOOK-HOLDBACK.md)

---

## 2. 配置

### 2.1 环境变量

```bash
# holdback 10%（推荐 dogfood 起点）
export TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto
# percent 优先 env；也可仅用 yaml
export TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT=10
```

回滚：`export TRAVELOGUE_STUDIO_HOMEPAGE_V2=off`

### 2.2 config.yaml（可选，与 env 二选一）

合并 [`config-holdback.example.yaml`](./config-holdback.example.yaml)：

```yaml
studio:
  homepage:
    v2_bento:
      percent: 10
```

启动时传入 config：

```bash
travelogue serve --studio ./trips --config config.yaml --host 0.0.0.0 --port 8766
```

---

## 3. 部署后验证（5 min）

```bash
# 门控决策（进组 / 对照）
TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT=10 \\
  python scripts/studio_homepage_gate_status.py --config config.yaml --ua "M20jTest/5" --json

# 根路径：200 serve v2 或 classic（M21-c 后无 302 → /v2）
curl -s http://HOST:8766/ | findstr data-homepage-variant

# 兼容入口（302 → /）
curl -sI http://HOST:8766/v2 | findstr Location

# 回滚演练
python scripts/studio_homepage_rollback_drill.py
```

---

## 4. 观察期

- 每日：检查 nightly holdback artifact（GitHub Actions）
- 每周：`studio_homepage_m20i_drill.py --telemetry ... --lcp-base http://HOST:8766`
- 更新 [`../acceptance-records/studio-homepage-v2-rollout-log.json`](../acceptance-records/studio-homepage-v2-rollout-log.json) `observationWindow.startedAt`

---

## 5. 团队入口

| URL | 用途 |
|-----|------|
| `/` | 主入口（`on` → v2；`auto` → 分桶 v2/classic；`off` → classic） |
| `/v2` | 302 → `/`（旧书签） |
| `/classic` | deprecated 应急 classic |
| `/?dev=1&studioFixture=multi` | loopback 状态切换 |

---

## 6. 告警（待 Owner 接线）

见 [TELEMETRY.md](./TELEMETRY.md) §3 · [OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md) OQ-TELEMETRY。

建议阈值与 §17.2 一致；Slack webhook 由平台组配置，本仓库仅提供聚合脚本。
