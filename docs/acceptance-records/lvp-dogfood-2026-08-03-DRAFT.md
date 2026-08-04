# LVP · 三册狗粮记录（AC-LVP-06 / BLK-LVP-04）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-04 |
| **GUIDE** | [lvp-dogfood-GUIDE.md](./lvp-dogfood-GUIDE.md) |
| **状态** | **结案 · AC-LVP-06 通过（三册均「差异小」）** |
| **方法** | 同基线 `trip.json` → `unlock` → `set_trip_layout_vibe` → `apply_layout_to_trip(web/screens)`；对照 `magazine_default` vs `fit_photo_experimental`；指标见 [lvp-dogfood-metrics-2026-08-04.json](./lvp-dogfood-metrics-2026-08-04.json) |
| **前置自动门** | `test_layout_vibe` + `test_layout_vibe_m2` · **22 passed**（2026-08-04） |

## 结果表

| trip | 推荐页数 | 实验页数 | 有加权屏？ | 观感 / 版面 | 差异小？ |
|------|----------|----------|------------|-------------|----------|
| `demo-d6697c8dca` 昙华林 | 23 | 23 | 推荐/实验各 1（hero/sidebar 类） | 版面指纹 **相同**；`slot_adaptation` False→True | **是** |
| `demo-2025` 东澳岛 | 32 | 32 | 0 / 0 | 版面指纹 **相同**；开关正确翻转 | **是** |
| `demo-49cbe46479` 斯里兰卡 | 28 | 28 | 1 / 1 | 版面指纹 **相同**；开关正确翻转 | **是** |

## 合同核对

| 项 | 结果 |
|----|------|
| 实验 vibe 写入后 `slot_adaptation.enabled=true` | ✅ |
| 推荐 vibe ≡ GA（MTSO on · MEGC on · MSA off） | ✅ |
| 回滚到推荐 · vibe 与页数可复现 | ✅（同基线重跑 magazine 页数一致） |
| 确认文案含「页数/篇幅」+「改回推荐」 | ✅ `EXPERIMENTAL_CONFIRM_*` |
| UI options 无算法缩写 | ✅ |

## 观察（不阻塞 AC-06）

本三册在 **仅翻转 MSA 父开关** 时，screens/`patternId`/slot fit **字节级相同**。  
与 MSA「默认 hold off / 盲评未通过」一致；实验卡后果文案仍成立（**可能**变），本批样本落在「差异小」。  
若产品要实验卡「肉眼必变」，属 **MSA 效力** 另题，不属 LVP 映射/入口失败。

## 结论

- [x] AC-LVP-06 通过（三册均记「差异小」可接受）
- [x] BLK-LVP-04 关闭
- [x] BLK-LVP-03 文案合同核对通过（现网草案满足签字要件）
