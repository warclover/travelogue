# TPC · PRD 缺口收口清单（2026-07-18）

| 属性 | 内容 |
|------|------|
| 关联 | [PRD-TEMPLATE-CONTRACT-V1](../PRD-TEMPLATE-CONTRACT-V1.md) |
| 状态 | **进行中** · 代码缺口本批收口；**质量审查收口见下**；corpus/盲评/默认开仍阻塞 |
| 本机手测 | [tpc-local-dogfood-GUIDE.md](./tpc-local-dogfood-GUIDE.md) · [config-tpc-dogfood.example.yaml](../config-tpc-dogfood.example.yaml) |
| 质量收口 | [quality-review-remediation-2026-07-18.md](./quality-review-remediation-2026-07-18.md) · PRD TPC §12 / GCS §12 / SFC §12 **全部必修** |

## 质量审查收口（2026-07-18 · 全部必修）

| 项 | AC | 说明 |
|----|-----|------|
| 近景硬门默认关 | AC-TPC-15 | `near_scene_clone_gate` 默认 false；硬拒不得改写 off 路径 |
| shadow 默认 off | AC-TPC-16 | 仓库 `shadow_log=false`；狗粮显式开 |
| debt p95 诚实 | AC-TPC-17 | merge 不用 p50 伪造 |
| eligibility 单点 | AC-TPC-18 | normalize 唯一实现 |
| GPL 闭包扫描 | AC-GCS-09 | CI 扫运行时闭包 |
| trip.json 保全 | AC-SFC-13 | 忙锁回退不丢数据 |
| displayTitle 同源 | AC-SFC-12 | FE/BE 日期兜底一致 |

## 本批已做

| 项 | 落点 |
|----|------|
| AC-TPC-10 raw 几何 log | `geometry_features.py` → `MosaicWindowLog` |
| squareRelaxed + `contract:infeasible_mix` | `evaluator._fallback_feasible` / candidates reject |
| `eligibility_canvas_ar` / `eligibility_count_scale` | evaluator |
| YAML `mainSlotPolicy` → `eligibility` | 4 个 hero 模板；validator 接受 eligibility |
| AC-TPC-05/13 单测 + hero-70 CSS 检查 | `test_template_contract_gap_closeout.py` |
| AC-TPC-11 脚本 | `scripts/layout_contract_perf.py` |
| GPL 扫描 | `scripts/license_gpl_scan.py` |
| compare 手记模板 | 见下方 |

## 仍阻塞默认开（人工 / corpus）

| 项 | 说明 |
|----|------|
| **AC-TPC-12** | 需 BQP/`URO_GOLDEN` 本地齐备 → `readyToEnable=true` |
| **AC-TPC-04② 删模块** | YAML 键已清；`main_eligibility.py` 仍承载 AR 算术（off 路径）；全删需狗粮后另 PR |
| **狗粮周签核** | 版式手测见 [tpc-mosaic-dogfood-2026-07-18.md](./tpc-mosaic-dogfood-2026-07-18.md)（F1–F6 开发期通过；可开 PR） |
| **正式盲评** | D-TPC-10 对外默认开前置 |
| **MIT BRIC vendor** | ✅ `travelogue/export/_vendor/collage` @ `76f8888`（float path；shelf 回退） |
| **AC-TPC-11 实测** | ✅ `docs/acceptance-records/tpc-curate-perf.json`（warm-up + P95 Δ -9.79% ≤ +10%） |

## 狗粮手记模板

`.cache/tpc-layout-compare/<tripId>/dogfood-notes.jsonl` 每行一例：

```json
{"tripId":"…","tag":"mix_hole|hero70|regressed|ok","note":"自由文本","prefer":"on|off|tie"}
```

## 命令

```bash
pytest tests/unit/layout_engine/test_template_contract_*.py -q
python scripts/layout_contract_shadow_diff.py --golden --out docs/acceptance-records/tpc-w1-shadow-diff.json
python scripts/layout_compare.py --trip-dir trips/<id>
python scripts/layout_contract_perf.py --fixture golden-mixed-scenes --repeats 5 --write
python scripts/license_gpl_scan.py --all-installed
```
