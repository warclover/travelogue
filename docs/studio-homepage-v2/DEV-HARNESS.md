# Studio 首页 v2 · Dev Harness 规格

> 呼应 PRD §16 全量 AC · 线框 v1.6 `review-bar` tab 的产品化延伸。

---

## 1. 启用条件

| 条件 | 说明 |
|------|------|
| `127.0.0.1` 或 `?dev=1` | 与 feature flag dev override 一致 |
| 或 `STUDIO_DEV=1` 服务端 boot | 注入 `#studio-dev-panel` |

**生产 build**：harness **不打包**（tree-shake / 动态 import dev-only）。

---

## 2. URL 参数（强制态）

| 参数 | 值 | 效果 |
|------|-----|------|
| `homepageVariant` | `v2` \| `v3` | 见 FEATURE-FLAG.md |
| `studioState` | 见下表 | 跳过正常 bootstrap 路由 |
| `studioFixture` | fixtures 名 | mock `GET /trips` |
| `studioJob` | job fixture 名 | mock `GET /status` |
| `studioOffline` | `1` | 模拟 offline |
| `studioSlowNet` | `1` | 触发 L2 懒加载 |
| `studioAssetsFail` | `1` | manifest 404 |
| `bentoPreviewTrip` | tripId \| `demo` \| `` | 预置 `localStorage` 预览 preference（D-14） |
| `preview` | tripId \| `demo` | 生产 deep link 同义；bootstrap 写入后清 URL |
| `bentoTabSession` | `mine` \| `demo` | D-13 session Tab（D-14 迁移测试） |
| `bentoTabSessionTrip` | tripId | 配合 `bentoTabSession=mine` |
| `bentoPreview404` | tripId \| `all` \| `1` | mock 指定 trip 的 `bento-preview` 404 |
| `studioCurate` | `succeed` | mock POST `/curate` + job 成功（AC-D14-08） |

### 2.1 `studioState` 枚举

| 值 | 对应态 |
|----|--------|
| `loading` | Loading skeleton |
| `idle-empty` | IdleEmpty Bento |
| `idle-returning` | Web 书架 |
| `importing` | Importing overlay |
| `importing-cold` | 冷启动 Importing（无 prior shell） |
| `failed` | Failed + Toast |
| `offline` | Offline 条 |
| `sheet-open` | IdleEmpty + Sheet |
| `first-success` | FirstSuccess |
| `unsupported` | UnsupportedViewport |

---

## 3. Trips Fixtures

**路径**：`templates/studio/fixtures/homepage-v2/trips/*.json`

| 名称 | 内容 |
|------|------|
| `empty.json` | `{ ok: true, trips: [], total: 0 }` |
| `single-stale.json` | 1 trip · `longshotStale: true` |
| `multi.json` | 5 trips · 混合 stale |
| `demo-only.json` | 仅 `demo-album` |
| `error.json` | HTTP 500 mock |

**activeJob fixtures**：`fixtures/homepage-v2/jobs/running.json` 等。

---

## 4. UI：Dev Panel

- 浮动面板 · 可折叠 · 列出 state / fixture / variant 下拉
- 「Copy repro URL」复制当前 query
- 与线框 tab 同序：Web 空态 · iPad · Sheet · Importing · 书架 · Unsupported

---

## 5. 实现里程碑

| 阶段 | 内容 |
|------|------|
| M20-g 前 | URL param `studioState` + fetch mock hook |
| M20-h | 全 fixture 集 + panel UI |
| M20-h | Playwright 用 harness 跑 AC 自动化 |

---

## 6. 测试入口（建议）

```bash
# 示例 repro URL
http://127.0.0.1:8766/?homepageVariant=v2&studioState=idle-empty&studioFixture=empty

# D-14 · 预览 preference + 404 边界
http://127.0.0.1:8766/?studioFixture=multi&bentoPreviewTrip=kyoto-rain&bentoPreview404=kyoto-rain

# D-14 · deep link（生产 URL 形态）
http://127.0.0.1:8766/?preview=kyoto-rain
```
