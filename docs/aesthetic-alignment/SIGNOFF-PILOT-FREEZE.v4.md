# AC-SC · 分层精选 pilot 配置冻结（v4）

> 归档日期：2026-06-19 · 分支 `feat/aesthetic-alignment`  
> 前置：v3 冻结 · v4 语料扩充 · purpose waiver · G3 默认开启

## 关联 signoff

| 文档 | 路径 |
|------|------|
| 分层 SRCC | [aesthetic-stratified-signoff.v4.json](../acceptance-records/aesthetic-stratified-signoff.v4.json) |
| Purpose pairwise | [purpose-pairwise-signoff.v4-p3.json](../acceptance-records/purpose-pairwise-signoff.v4-p3.json) |
| Waiver | [purpose-pairwise-waiver.v4.json](../acceptance-records/purpose-pairwise-waiver.v4.json) |
| G3 | [aesthetic-g3-signoff.v4.json](../acceptance-records/aesthetic-g3-signoff.v4.json) |
| Profile 模板 | [aesthetic-purpose-profiles.v4.json](../acceptance-records/aesthetic-purpose-profiles.v4.json) |
| 配置快照 | [aesthetic-pilot-config.freeze.v4.yaml](../acceptance-records/aesthetic-pilot-config.freeze.v4.yaml) |

## v4 相对 v3 的变化

1. **语料**：7 本 v4 相册（522 张校准 + 恩施 hold-out）
2. **Purpose**：AC-SC-03 strict 3/5 · waiver 接受 · 聚合 58.9%
3. **Profile**：4 类全局模板（portrait / mixed / landscape / underwater）+ `tripKindMap`
4. **G3**：`AppConfig.aesthetic.ml_calibrate=true` 已改默认

## Purpose profile 解析（DS-3）

```text
trip.curation.purposeProfileKind  →  profileTemplates[kind]
         ↑ 缺省则 tripKindMap[tripId]
         ↑ 再缺省则 albumProfile + stratumPreference 推断
```

## 放量检查清单

- [ ] `pip install -e ".[cull-ml]"` 本机可用
- [ ] `python scripts/aesthetic_dogfood_recurate_g3.py` 三本 dogfood
- [ ] Studio 抽检 cover/hero 是否漂移
- [ ] AC-SC-00：补标 [sc00-recruit HTML](../acceptance-records/aesthetic-blind-review.sc00-recruit.v4.html)（**+6 general 已合并** · 仍缺 general 10、group 1）

## 回滚

见 [SIGNOFF-G3-DEFAULT-ML.md](./SIGNOFF-G3-DEFAULT-ML.md) §6。
