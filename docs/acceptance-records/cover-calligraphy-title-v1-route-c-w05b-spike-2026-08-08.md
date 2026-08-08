# Route C W0.5b 冲质量 Spike 结果

生成时间：2026-08-08T13:44:19+00:00

## 汇总

| 指标 | 数值 |
|------|------|
| 总行数 | 56 |
| 策略跳过 | 26 |
| 实际尝试 | 30 |
| 首次 OCR 通过率 | 0.8333 |
| ≤1 次重试后通过率 | 0.9 |
| AC-CAL-11（≥90%）达标 | True |

## 按 prompt_version

| version | n | first | after_retry |
|---------|---|-------|-------------|
| v2 | 30 | 0.8333 | 0.9 |

> AC-CAL-11 看 after_retry_rate（尝试子集）；skipped 含 D-CAL-21 生僻字 + 风险规则（除非 --include-risk）。未达标不得默认开启 route_c_enabled。

## 风险桶计数（E3）

```json
{
  "punctuation": 4,
  "repeated_char": 4,
  "uncommon_chars": 18
}
```

## 逐条

| # | 标题 | 类别 | 风格 | pv | skip | first | after_retry | risk |
|---|------|------|------|----|------|-------|-------------|------|
| 0 | 拾光 | baseline_control | cascade-seal | v2 | False | True | True |  |
| 1 | 拾光 | baseline_control | cascade-seal | v2 | False | True | True |  |
| 2 | 光 | extreme_short_1char | flowing-brush | v2 | False | True | True |  |
| 3 | 光 | extreme_short_1char | flowing-brush | v2 | False | True | True |  |
| 4 | 甪直古镇 | rare_char_place | loose-running-script | v2 | True | None | None |  |
| 5 | 甪直古镇 | rare_char_place | loose-running-script | v2 | True | None | None |  |
| 6 | 涠洲岛落日 | rare_char_place | bold-vigorous | v2 | True | None | None |  |
| 7 | 涠洲岛落日 | rare_char_place | bold-vigorous | v2 | True | None | None |  |
| 8 | 婺源篁岭 | rare_char_place | casual-handwritten | v2 | True | None | None |  |
| 9 | 婺源篁岭 | rare_char_place | casual-handwritten | v2 | True | None | None |  |
| 10 | 黟县宏村 | rare_char_place | cascade-seal | v2 | True | None | None |  |
| 11 | 黟县宏村 | rare_char_place | cascade-seal | v2 | True | None | None |  |
| 12 | 龟兹寻踪 | rare_char_place | flowing-brush | v2 | False | True | True |  |
| 13 | 龟兹寻踪 | rare_char_place | flowing-brush | v2 | False | True | True |  |
| 14 | 阆中古城 | rare_char_place | loose-running-script | v2 | True | None | None |  |
| 15 | 阆中古城 | rare_char_place | loose-running-script | v2 | True | None | None |  |
| 16 | 措浪日记 | rare_char_place | bold-vigorous | v2 | False | True | True |  |
| 17 | 措浪日记 | rare_char_place | bold-vigorous | v2 | False | True | True |  |
| 18 | 硇洲岛 | rare_char_place | casual-handwritten | v2 | True | None | None |  |
| 19 | 硇洲岛 | rare_char_place | casual-handwritten | v2 | True | None | None |  |
| 20 | 邺城旧梦 | rare_char_place | cascade-seal | v2 | True | None | None |  |
| 21 | 邺城旧梦 | rare_char_place | cascade-seal | v2 | True | None | None |  |
| 22 | 麤犇靐齉爩 | extreme_rare_stress | flowing-brush | v2 | True | None | None |  |
| 23 | 麤犇靐齉爩 | extreme_rare_stress | flowing-brush | v2 | True | None | None |  |
| 24 | 厦门老城区 | polyphone_place | loose-running-script | v2 | False | False | False |  |
| 25 | 厦门老城区 | polyphone_place | loose-running-script | v2 | False | True | True |  |
| 26 | 重庆火锅魂 | polyphone_place | bold-vigorous | v2 | False | True | True |  |
| 27 | 重庆火锅魂 | polyphone_place | bold-vigorous | v2 | False | True | True |  |
| 28 | 重走318国道 | digits_mixed | casual-handwritten | v2 | False | False | False |  |
| 29 | 重走318国道 | digits_mixed | casual-handwritten | v2 | False | False | False |  |
| 30 | 西藏骑行Vlog | latin_mixed | cascade-seal | v2 | False | True | True |  |
| 31 | 西藏骑行Vlog | latin_mixed | cascade-seal | v2 | False | False | True |  |
| 32 | 三亚Vlog | latin_mixed | flowing-brush | v2 | False | True | True |  |
| 33 | 三亚Vlog | latin_mixed | flowing-brush | v2 | False | True | True |  |
| 34 | 海边·日落 | punctuation | loose-running-script | v2 | True | None | None | punctuation |
| 35 | 海边·日落 | punctuation | loose-running-script | v2 | True | None | None | punctuation |
| 36 | 一路向西… | punctuation | bold-vigorous | v2 | True | None | None | punctuation |
| 37 | 一路向西… | punctuation | bold-vigorous | v2 | True | None | None | punctuation |
| 38 | 稻城亚丁行 | common_scenic | casual-handwritten | v2 | False | True | True |  |
| 39 | 稻城亚丁行 | common_scenic | casual-handwritten | v2 | False | True | True |  |
| 40 | 阿勒泰散记 | common_scenic | cascade-seal | v2 | False | True | True |  |
| 41 | 阿勒泰散记 | common_scenic | cascade-seal | v2 | False | True | True |  |
| 42 | 918公里 | digits_mixed | flowing-brush | v2 | False | True | True |  |
| 43 | 918公里 | digits_mixed | flowing-brush | v2 | False | False | True |  |
| 44 | 秋去秋又来 | repeated_char | loose-running-script | v2 | True | None | None | repeated_char |
| 45 | 秋去秋又来 | repeated_char | loose-running-script | v2 | True | None | None | repeated_char |
| 46 | 一茶一饭间 | repeated_char | bold-vigorous | v2 | True | None | None | repeated_char |
| 47 | 一茶一饭间 | repeated_char | bold-vigorous | v2 | True | None | None | repeated_char |
| 48 | 雾锁南迦巴瓦 | long_boundary_8char | casual-handwritten | v2 | True | None | None |  |
| 49 | 雾锁南迦巴瓦 | long_boundary_8char | casual-handwritten | v2 | True | None | None |  |
| 50 | 苔痕上阶绿 | poetic_phrase | cascade-seal | v2 | False | True | True |  |
| 51 | 苔痕上阶绿 | poetic_phrase | cascade-seal | v2 | False | True | True |  |
| 52 | 拾光记 | common_easy_extra | flowing-brush | v2 | False | True | True |  |
| 53 | 拾光记 | common_easy_extra | flowing-brush | v2 | False | True | True |  |
| 54 | 山海间 | common_easy_extra | loose-running-script | v2 | False | True | True |  |
| 55 | 山海间 | common_easy_extra | loose-running-script | v2 | False | True | True |  |