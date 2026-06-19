# AA · 灰度放量 Runbook

> Sign-off：[SIGNOFF-M4.md](./SIGNOFF-M4.md)  
> 日志：[`aesthetic-alignment-rollout-log.json`](../acceptance-records/aesthetic-alignment-rollout-log.json)

---

## 前置

```bash
pip install -e ".[cull-ml]"   # nima / pyiqa
# .env：DEEPSEEK_API_KEY（文本）、DASHSCOPE_API_KEY（MLLM vision）
```

---

## G1 · ml + stratum（无 MLLM）

1. 将 [config-aesthetic-alignment.example.yaml](./config-aesthetic-alignment.example.yaml) **G1** 段落合并进 `config.yaml`。
2. 对目标 trip 执行 curate（Studio 或 CLI）。
3. 检查 `trip.json` → `quality.aesthetic.source` 应为 `rules+ml`；`signals.learnedAesthetic` 存在。
4. 对比封面/hero 是否与 rules-only 有变化；不满意则调 `stratum_blends` 或关 `portrait_lite_enabled`。

**回滚**：`ml_calibrate: false` → recurate。

---

## G2 · 作者 trip 开 MLLM

1. 在 G1 基础上设 `mllm.enabled: true`（见 example **G2**）。
2. recurate；观察 `trips/<id>/cache/aesthetic-mllm.json` 写入。
3. 短名单图 `signals.mllmScore` + `critique` 非空；`calls ≤ max_calls_per_trip`。
4. 二次 curate 应 **calls=0**（全缓存命中）。

**回滚**：`mllm.enabled: false` → recurate（保留 learned，去掉 MLLM blend）。

---

## 评测复跑

```bash
python scripts/aesthetic_learned_eval.py \
  --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json \
  --metric nima --use-stratum-blend \
  --stratum-blends docs/acceptance-records/aesthetic-m2-stratum.demo-2025-6.json

python scripts/aesthetic_mllm_eval.py \
  --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json \
  --provider dashscope --use-stratum-blend \
  --stratum-blends docs/acceptance-records/aesthetic-m2-stratum.demo-2025-6.json \
  --write docs/acceptance-records/aesthetic-m3-eval.demo-2025-6.json
```

---

## G3 · 全量（v4 waiver · 已生效）

> 权威：[SIGNOFF-G3-DEFAULT-ML.md](./SIGNOFF-G3-DEFAULT-ML.md) · [aesthetic-g3-signoff.v4.json](../acceptance-records/aesthetic-g3-signoff.v4.json)  
> Merge 准备：[MERGE-READINESS.v4.md](./MERGE-READINESS.v4.md)

**分层门禁（AC-SC-*）**：01/02/04/05/06 ✅ · 03 + 00 **waiver 接受** · AppConfig 默认已改。

### 联签前检查

- [x] AC-SC-01/02/04/05/06
- [x] AC-SC-03（v4-p3 waiver）
- [x] AC-SC-00（general/group waiver）
- [x] Pilot 配置冻结 v4
- [x] 三本 dogfood recurate（G3 默认）→ `aesthetic-g3-dogfood-recurate.v4.json`
- [ ] Studio cover/hero 人工抽检（merge 前）
- [ ] portrait 缺陷率 ≤ baseline（可选 · `aesthetic_portrait_defect_signoff.py`）

### 旧 AA 门禁（仅供参考，不阻塞 G3）

- AC-AA-02 pooled SRCC：健康检查 only（PRD-SC DS-5）
- AC-AA-03：由 AC-SC-03 purpose pairwise 承接
