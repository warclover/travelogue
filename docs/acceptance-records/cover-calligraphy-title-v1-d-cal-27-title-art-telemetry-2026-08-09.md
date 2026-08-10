# D-CAL-27 · title_art 漏斗埋点（路线 B/C 使用率 / 失败率可观测）

**日期**：2026-08-09  
**状态**：已落地  
**关联**：[PRD-COVER-CALLIGRAPHY-TITLE-V1](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)

## 1. 起因

`titleArt.enabled` 已默认开启（AC-CAL-BLIND / D-CAL-05），功能进入真实流量，但线上完全看不到：

- 用户有没有点「生成装帧标题」
- 走了路线 B 还是 C
- C 是否回退到 B
- 失败 / 不支持（disabled）比例是多少

产品负责人拍板补埋点作为默认开启后的首个可观测性收口。

## 2. 历史缺口（为什么看起来"已经埋了"其实没有）

`features.js` 在 v0.6.9（D-CAL-22 Studio 入口）落地时就写了：

```js
trackStudioEvent("title_art_resolve", { tripId, engine, routeCRequested, fallback });
```

但：

1. `templates/studio/js/analytics.js` 的前端 `ALLOWED` 集合**没收录** `title_art_resolve` → `trackStudioEvent` 开头 `if (!ALLOWED.has(event)) return Promise.resolve(false)` 直接丢弃；
2. `travelogue/domain/studio_events.py` 的后端白名单**也没收录** → 即便前端放行，`POST /__travelogue/studio-event` 也会 400；
3. 只在成功路径发一次，`disabled` / HTTP 错误 / 网络失败三条路径完全不发。

所以默认开启至今，jsonl 里实际是 0 条 title_art 事件。

## 3. 事件契约

| 事件 | 触发时机 | 关键 meta |
|---|---|---|
| `title_art_impression` | 服务端总闸开、面板真正展示时 | `tripId` · `coverOpeningStyle` · `routeCShown` |
| `title_art_resolve` | 每次点击「生成装帧标题」收口（含失败） | 见下 |

`title_art_resolve.outcome`：

| outcome | 含义 |
|---|---|
| `success` | `enabled=true`，贴纸已生成并刷新预览 |
| `disabled` | 版式/标题不支持，保持默认 CSS 标题（fail-open） |
| `error` | HTTP 非 200 / `ok=false` |
| `network` | fetch 抛错 |

其余字段：`engine`（`clean-pipeline-v1` / `diffusion-fixed-prompt-v1`）、`routeCRequested`、`routeCAllowedByConfig`、`fallback`（C→B 回退）、`ocrVerified`（有则带）、`enabled`、`coverOpeningStyle`。

## 4. 能算什么

本地 `~/.travelogue/telemetry/studio-homepage-events.jsonl` 聚合后：

- **入口转化**：`impression` → `resolve`（任意 outcome）
- **B/C 使用率**：`routeCRequested=true` 占比；`engine` 分布
- **C 回退率**：`routeCRequested ∧ fallback`
- **失败率**：`outcome ∈ {error, network}` / 全部 resolve
- **不支持率**：`outcome=disabled`（非白名单风格 / 空标题等）

不引入新后端存储或远端上报——复用既有 Studio homepage 漏斗通道。

## 5. 落地

- `travelogue/domain/studio_events.py`：白名单加 `title_art_impression` / `title_art_resolve`
- `templates/studio/js/analytics.js`：前端 `ALLOWED` 同步
- `templates/studio/preview-toolbar/features.js`：补 impression；`emitTitleArtResolve` 覆盖 success / disabled / error / network
- `tests/unit/web/test_title_art_frontend_wiring.py`：锁住前后端白名单 + outcome 覆盖面

## 6. 边界

- 不改引擎本身、不加服务端二次埋点（客户端 fire-and-forget 已够本地 dogfood 用）。
- 不记标题原文（隐私 / 体积），只记风格 id 与路线结果。
- CLI `title-art` 路径不在本条范围（Studio UI 漏斗优先）。
