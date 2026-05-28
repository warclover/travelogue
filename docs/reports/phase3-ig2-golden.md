# M13 · I-G2 黄金样本报告

| 属性 | 内容 |
|------|------|
| **阶段** | M13 · P3-Full |
| **指标** | `subject_run_score` · `time_inversion_rate` · `aspect_pattern_match_rate` · `burst_integrity_violations` |
| **机器可读记录** | [phase3-m13-ig2.json](../acceptance-records/phase3-m13-ig2.json) |
| **性能记录** | [phase3-m13-bench.json](../acceptance-records/phase3-m13-bench.json) |

---

## 1. 对比方法

对每条样本跑三种模式（Phase 3 beam + `v2_adaptive` arc）：

| 模式 | clustering | vision | 说明 |
|------|------------|--------|------|
| **baseline** | off | off | NR-P3-01 · 等同 Phase 2 章界 |
| **P3-Lite** | on | off | geo events + run_aware |
| **P3-Full** | on | on | + scene clusters（CLIP 或启发式降级） |

**通过标准（AC-P3-C02/C03/C09）**：

- P3-Full `subjectRunScore` ≥ baseline（I-G2）
- P3-Full `timeInversionRate` ≤ baseline（I-G1 不劣化）
- P3-Full `burstIntegrityViolations` ≤ baseline；CI fixture 无 burst 时为 0
- P3-Full `aspectPatternMatchRate` ≥ baseline

---

## 2. CI Golden Fixtures

| Trip | 张数 | baseline subject_run | P3-Full subject_run | burst | 结论 |
|------|------|----------------------|---------------------|-------|------|
| golden-mixed-scenes | 18 | 见 JSON | 见 JSON | 0 | ✅ CI gate |
| golden-kyoto-gps | 18 | 见 JSON | 见 JSON | 0 | ✅ CI gate |

```bash
pytest tests/test_layout_golden.py -q -m "not vision"
python scripts/phase3_ig2_report.py golden-mixed-scenes golden-kyoto-gps --fixture
```

---

## 3. 本地黄金样本（可选）

当仓库外存在 `trips/mao`、`trips/maomi`、`trips/linzhi` 时：

```bash
python scripts/phase3_ig2_report.py mao maomi linzhi
pytest tests/test_layout_golden.py -q -k "ig2_local"
```

---

## 4. CLIP 真实路径

```bash
pip install -e ".[clip]"
pytest tests/test_layout_golden.py -m vision -q
python scripts/phase3_cluster_bench.py --assets 400 --vision
```

当前 CI 无 torch 时使用 **启发式 embedding**（`ClipEncoder` 降级）。本地 `[clip]` 验收：

```bash
python scripts/phase3_clip_acceptance.py
pytest tests/test_clip_real.py -m vision -q
```

**2026-05-28 实测**（模型已缓存）：12 张 · ViT-B/32 · embed **~8s** · 2 scene clusters → [`phase3-m13-clip.json`](../acceptance-records/phase3-m13-clip.json)

---

## 5. 性能（PF-P3-02 / AC-P3-C05）

400 张 synthetic GPS 相册 · 模型/缓存 warm 后计时：

```bash
python scripts/phase3_cluster_bench.py --assets 400
```

结果写入 `docs/acceptance-records/phase3-m13-bench.json`（soft cap **480s**）。

---

## 6. 签字

| 项 | 结果 | 日期 |
|----|------|------|
| I-G2 subject_run（CI fixture） | ✅ Go | 2026-05-28 |
| AC-P3-C03 time guard | ✅ Go | 2026-05-28 |
| AC-P3-C09 burst/aspect guard | ✅ Go（≤ baseline） | 2026-05-28 |
| AC-P3-C05 400 张 bench | ✅ Go（CI 启发式路径） | 2026-05-28 |
| **真实 CLIP forward** | ✅ Go · 12 张 · ViT-B/32 | 2026-05-28 |
