# M21-e2 执行卡（删除与回退）

> 目标：在满足 M21-e2 门禁后，执行 v3 物理退役，且可快速回退。

## A. 执行前（必须全部满足）

- [ ] 已完成一个发布版本观察窗口（M21-e1）
- [ ] `python scripts/studio_m21e2_preflight.py --observed-release --json` 返回 `ready=true`
- [ ] `/classic` 流量确认仅应急使用
- [ ] CI / Nightly 稳定（无新增关键告警）

## B. 执行步骤（建议顺序）

1) 产出 preflight 报告（留档）

```bash
python scripts/studio_m21e2_preflight.py --observed-release --json --out reports/m21-e2-preflight.json
```

2) 生成删除命令计划（dry-run）

```bash
python scripts/studio_m21e2_delete_plan.py
```

3) 切换 `/classic` 到冻结快照入口（若采用快照策略）

4) 删除 v3 候选文件（分批提交）：

- `templates/studio/studio.html`
- `templates/studio/studio.js`
- `templates/studio/studio.css`
- `templates/studio/js/navigation.js`
- `templates/studio/js/render.js`
- `templates/studio/js/sheet.js`
- `templates/studio/js/samples.js`
- `templates/studio/js/init.js`
- `templates/studio/js/viewport.js`

5) 清理 legacy 测试与文档引用（或标注 retired）

## C. 执行后验证

```bash
python -m pytest tests/test_studio_home_v2.py tests/test_studio_home_v2_ac_playwright.py tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py tests/test_studio_lcp_measure.py tests/test_studio_lcp_playwright.py -q --tb=short
```

## D. 回退点

- 回退点 1：仅恢复路由入口（`/classic` 指回冻结快照或旧入口）
- 回退点 2：恢复被删文件并重跑上述回归
- 回退点 3：按 `M21-ROLLBACK-CARD.md` 执行 `TRAVELOGUE_STUDIO_HOMEPAGE_V2=off`

## E. 发布说明模板

- 主入口：`/`（v2）
- 应急入口：`/classic`（deprecated）
- 兼容入口：`/v2`（302 到 `/`）
