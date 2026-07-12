# M21 手测冒烟清单 · P1-3 / P1-4

> 自动化已覆盖部分见 `scripts/m21_dogfood_gate.py` · `scripts/m21_deploy_smoke.py`。  
> 本清单仅保留 **必须真人/真相册** 的步骤。

---

## 0. 准备（5 min）

| 项 | 要求 |
|----|------|
| 环境 | `pip install -e ".[dev,playwright]"` |
| 启动 | `travelogue serve --studio ./trips --host 127.0.0.1 --port 8766` |
| 门控 | 生产 dogfood：`TRAVELOGUE_STUDIO_HOMEPAGE_V2=on`（或 holdback `auto` + percent） |
| 样册 | 10–30 张 JPG 的小文件夹；可选子目录 `精选/` + `素材上传/` |
| 浏览器 | Chrome/Edge 最新 · 窗口 ≥1280px |

**自动化预检（通过后再手测）：**

```powershell
python scripts/m21_dogfood_gate.py --skip-e2e
python scripts/m21_deploy_smoke.py --base http://127.0.0.1:8766
```

---

## 1. P1-3 · 小文件夹上传 → preview（AC-M21-0-01）

| # | 操作 | 预期 | ☐ |
|---|------|------|---|
| 1 | 打开 `http://127.0.0.1:8766/` | v2 Bento 首页；`data-homepage-variant="v2"` | |
| 2 | 点「制作我的杂志」→ Import Wizard（默认） | Wizard 打开；可见上传 / 选文件夹入口 | |
| 3 | 选本地小文件夹（<50MB）并开始制作 | 进入 Importing；进度文案更新 | |
| 4 | 等待 FirstSuccess | 成功 overlay；主文案含书名/张数 | |
| 5 | 点「打开卷轴预览」或倒计时自动进入 | 预览 URL 可打开；首屏为内容屏 | |
| 6 | 预览顶栏「返回首页」 | 回到 `/` v2，非 `/classic` | |

**负向（可选）：**

| # | 操作 | 预期 | ☐ |
|---|------|------|---|
| 7 | 超大文件夹 → 确认弹窗点「取消」 | 不发起 import；导入 UI 仍可操作 | |
| 8 | Importing 中再次打开导入 UI | toast「正在制作中」 | |
| 9 | Importing 中刷新页面 | 仍显示 Importing（`activeJobId` 续跑） | |

记录：`trips/<tripId>` · 截图 FirstSuccess + 预览首屏。

---

## 2. P1-4 · 发布后路由与应急（M21-a §2）

**HTTP（可脚本）：**

```powershell
python scripts/m21_deploy_smoke.py --base https://YOUR_HOST
curl -s https://YOUR_HOST/ | findstr data-homepage-variant
curl -sI https://YOUR_HOST/v2 | findstr Location
```

| # | 检查 | 预期 | ☐ |
|---|------|------|---|
| 1 | `GET /` | 200 · v2 标记 | |
| 2 | `GET /classic` | 200 · deprecated classic | |
| 3 | `GET /v2` | 302 → `/` | |
| 4 | 预览页返回首页 | `/` v2 | |

**漏斗（部署后 24h，需 telemetry）：**

```powershell
python scripts/studio_telemetry_aggregate.py --out reports/m21-funnel.csv
python scripts/studio_holdback_report.py --telemetry ~/.travelogue/telemetry/studio-homepage-events.jsonl --out reports/m21-holdback.json
```

对照 [M21-TEST-MATRIX.md](./M21-TEST-MATRIX.md) §M21-b 阈值。

---

## 3. 签字

| 项 | 负责人 | 日期 | 结论 |
|----|--------|------|------|
| P1-3 上传→preview | | | |
| P1-4 路由/应急 | | | |
| P1-4 漏斗 24h | | | |

通过后更新 [`../acceptance-records/studio-homepage-v2-rollout-log.json`](../acceptance-records/studio-homepage-v2-rollout-log.json) `observationWindow.startedAt`。
