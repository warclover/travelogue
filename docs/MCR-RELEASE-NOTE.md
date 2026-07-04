# MCR Release Note · 拼图 MCS 配置恢复

> **性质**：behavior fix（非新 SKU）  
> **版本**：MCR P0 + P1 · 2026-07-04  
> PRD：[PRD-MOSAIC-CONFIG-RESTORE.md](./PRD-MOSAIC-CONFIG-RESTORE.md)

## 标题

拼图 MCS 配置恢复 — 横图游记 hero 拼图重新可用

## 变更摘要

1. 修复 `config.yaml` **缺少 `mosaic:` 段**时 `enabled_window_sizes` 被 silent 缩成仅 `(5,)` 的配置加载 bug；缺段环境现回退 `MosaicConfig` dataclass 默认 `(4, 5, 6, 9)`。
2. `screen-mosaic-5-hero-3-2-plus-4` 写入 `MOSAIC_5_PATTERN_IDS`（policy + codegen 同步，行为等价，消除 orphan）。
3. 新增 `scripts/mosaic_config_diag.py`、`scripts/mcr_eval_recurate.py` 便于验收与排查。

## 用户须知

1. **需重新 curate / replan 才生效**；已有 `index.html` / 旧 `trip.json` 排版不会自动变化。
2. **仍不会出现**的历史版式（deprecated，不在 MCR 范围）：
   - `screen-mosaic-5-2p3l-equal`
   - `screen-mosaic-5-2portrait-3land-balanced`
   - `screen-mosaic-5-3portrait-2land-balanced`
   - `screen-mosaic-5-main-landscape-2portrait-2land`
3. **竖图为主相册**（如儿童年度册）修复后 **仍可能无** 五/六张拼图 — 属 1P+4L 几何 + 12s 连拍门槛，非故障。运行 `python scripts/mosaic_config_diag.py --trip trips/<id>` 查看 burst_fail / 竖图占比。
4. **横图为主相册** re-curate 后预期可出现 **主 hero + 配图** 拼图（1～3 屏量级），密度仍受 P21 `density_budget` 约束；不会满屏网格。
5. URO `usage_rules.enabled` 仍为 **false**；MCR 应先于 URO enabled=true 上线。

## 本地验收

```bash
pytest tests/test_mosaic_config_defaults.py tests/test_mosaic_*.py -q
python scripts/mosaic_config_diag.py --strict
python scripts/mcr_eval_recurate.py chuanzang-studio demo-80301df45c
python scripts/mosaic_config_diag.py --compare-baseline .cache/mcr-eval/chuanzang-studio.json
```

留档路径：`.cache/mcr-eval/`（gitignored）。

## P2 补充（2026-07-04）

| 项 | 交付 |
|----|------|
| MCR-P-07 | `GUIDE-PHASE16-layout-template-engine.md` §1.1 三层 mosaic 含义 |
| MCR-P-06 | `scripts/check_usage_consistency.py --family mosaic`；修正 `2portrait-3land-balanced` summary |
| D11 | `mosaic_config_diag.py --trip` 输出 MCS decision log 各窗 exposure（含 window 4） |
| D14 | `TRAVELOGUE_CONFIG_VERBOSE=1` 或 `TRAVELOGUE_VERBOSE=1` 时 `load_config` INFO 缺 `mosaic:` 段提示 |

```bash
python scripts/check_usage_consistency.py --family mosaic
TRAVELOGUE_CONFIG_VERBOSE=1 python -c "from travelogue.config import load_config; load_config()"
```

## 回滚

| 开关 | 效果 |
|------|------|
| `mosaic.enabled: false` | 整段回退 legacy planner |
| `mosaic.enabled_window_sizes: [5]` | 临时仅 5 窗（不推荐） |
| Git revert MCR PR | 恢复 bug 行为（禁止长期依赖） |
