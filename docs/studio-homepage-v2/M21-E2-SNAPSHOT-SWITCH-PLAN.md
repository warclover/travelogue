# M21-e2 · `/classic` 冻结快照切换方案

> 目标：在不影响主路径 `/`（v2）的前提下，把 `/classic` 从“开发态 v3 文件”切到“冻结快照资产”，为后续删除 v3 源文件做准备。

## 1. 触发条件

- M21-e1 观察窗口完成（至少一个发布版本）。
- `studio_m21e2_preflight.py --observed-release` 仅剩可接受引用或无阻塞。

## 2. 切换策略（已实施）

1) 新增冻结快照目录：

- `templates/studio/legacy-freeze/studio.classic.html`
- `templates/studio/legacy-freeze/studio.classic.js`
- `templates/studio/legacy-freeze/studio.classic.css`

2) 路由切换：

- `handle_home()` 从 `studio.html` 改为 `legacy-freeze/studio.classic.html`。
- 根路径门控中的 v3 分支同步切到同一快照模板。
- URL 保持不变：`GET /classic`。

## 3. 阻塞项消解映射

- `travelogue/web/studio_handlers/static_handlers.py` 运行时引用 `studio.html`  
  → 已改为 `legacy-freeze/studio.classic.html`。
- `tests/test_studio_handlers_config_static.py` 的静态资产断言  
  → 已切换到 `studio-home-v2.css` 与行为断言。
- `tests/test_studio_home_v2.py` / `tests/test_studio_chrome.py` 的 v3 入口硬编码断言  
  → 已迁移到 v2 主路径或标记为 `legacy_homepage`。

## 4. 回归门禁

```bash
python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_classic_serves_v3"
python -m pytest tests/test_studio_handlers_config_static.py -q --tb=short
python -m pytest tests/test_studio_chrome.py -q --tb=short -k "studio_home_html"
python scripts/studio_m21e2_preflight.py --json
python scripts/studio_m21e2_preflight.py --observed-release --json
```

## 5. 回退策略

- 回退只需恢复 `handle_home()` 与根门控 v3 分支模板指向。
- 若快照资产异常，优先恢复 `/classic` 可用性，再处理内容差异。
