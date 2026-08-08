# Route C W0.5 完整 Spike 结果

生成时间：2026-08-08T02:37:08+00:00

## 汇总

| 指标 | 数值 |
|------|------|
| 样本总数 | 26 |
| 生成成功数 | 26 |
| 生成成功率 | 1.0 |
| OCR 回读通过率（生成成功中） | 0.5769 |
| 失败原因分布 | {} |
| 延迟 avg/min/max/p95 (ms) | {'avg': 18016.1, 'min': 15285, 'max': 28303, 'p95': 19213} |

## 分类别通过率

| 类别 | 总数 | OCR 通过 |
|------|------|----------|
| baseline_control | 1 | 0 |
| extreme_short_1char | 1 | 1 |
| rare_char_place | 9 | 5 |
| extreme_rare_stress | 1 | 0 |
| polyphone_place | 2 | 1 |
| digits_mixed | 2 | 2 |
| latin_mixed | 2 | 1 |
| punctuation | 2 | 1 |
| common_scenic | 2 | 2 |
| repeated_char | 2 | 1 |
| long_boundary_8char | 1 | 1 |
| poetic_phrase | 1 | 0 |

## 逐条明细

| # | 标题 | 类别 | 风格 | 生成 | OCR匹配 | OCR识别文本 | 延迟(ms) | 失败原因 | 图片 |
|---|------|------|------|------|---------|--------------|----------|----------|------|
| 0 | 拾光 | baseline_control | cascade-seal | ✓ | False | 拾玖 | 15285 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\00-cascade-seal-baseline_control.png |
| 1 | 光 | extreme_short_1char | flowing-brush | ✓ | True | 光 | 15601 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\01-flowing-brush-extreme_short_1char.png |
| 2 | 甪直古镇 | rare_char_place | loose-running-script | ✓ | False | 直古镇 | 15427 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\02-loose-running-script-rare_char_place.png |
| 3 | 涠洲岛落日 | rare_char_place | bold-vigorous | ✓ | False | 涠州岛落日 | 18964 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\03-bold-vigorous-rare_char_place.png |
| 4 | 婺源篁岭 | rare_char_place | casual-handwritten | ✓ | False | 渡洒桦洛 | 15511 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\04-casual-handwritten-rare_char_place.png |
| 5 | 黟县宏村 | rare_char_place | cascade-seal | ✓ | True | 黟县宏村 | 19094 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\05-cascade-seal-rare_char_place.png |
| 6 | 龟兹寻踪 | rare_char_place | flowing-brush | ✓ | True | 龟兹寻踪 | 28303 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\06-flowing-brush-rare_char_place.png |
| 7 | 阆中古城 | rare_char_place | loose-running-script | ✓ | False | 阆台城 | 18554 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\07-loose-running-script-rare_char_place.png |
| 8 | 措浪日记 | rare_char_place | bold-vigorous | ✓ | True | 措浪日记 | 18898 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\08-bold-vigorous-rare_char_place.png |
| 9 | 硇洲岛 | rare_char_place | casual-handwritten | ✓ | True | 硇洲岛 | 15450 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\09-casual-handwritten-rare_char_place.png |
| 10 | 邺城旧梦 | rare_char_place | cascade-seal | ✓ | True | 邺城旧梦 | 15515 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\10-cascade-seal-rare_char_place.png |
| 11 | 麤犇靐齉爩 | extreme_rare_stress | flowing-brush | ✓ | False | 桀騏駜犼 | 15699 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\11-flowing-brush-extreme_rare_stress.png |
| 12 | 厦门老城区 | polyphone_place | loose-running-script | ✓ | False | 厦门三殷老城区 | 18632 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\12-loose-running-script-polyphone_place.png |
| 13 | 重庆火锅魂 | polyphone_place | bold-vigorous | ✓ | True | 重庆火锅魂 | 18991 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\13-bold-vigorous-polyphone_place.png |
| 14 | 重走318国道 | digits_mixed | casual-handwritten | ✓ | True | 重走318国道 | 18564 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\14-casual-handwritten-digits_mixed.png |
| 15 | 西藏骑行Vlog | latin_mixed | cascade-seal | ✓ | False | 西藏骑行日目Vlog | 18935 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\15-cascade-seal-latin_mixed.png |
| 16 | 三亚Vlog | latin_mixed | flowing-brush | ✓ | True | 三亚Vlog | 15371 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\16-flowing-brush-latin_mixed.png |
| 17 | 海边·日落 | punctuation | loose-running-script | ✓ | True | 海边·日落 | 18618 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\17-loose-running-script-punctuation.png |
| 18 | 一路向西… | punctuation | bold-vigorous | ✓ | False | 一路向西 | 18999 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\18-bold-vigorous-punctuation.png |
| 19 | 稻城亚丁行 | common_scenic | casual-handwritten | ✓ | True | 稻城亚丁行 | 15357 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\19-casual-handwritten-common_scenic.png |
| 20 | 阿勒泰散记 | common_scenic | cascade-seal | ✓ | True | 阿勒泰散记 | 15294 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\20-cascade-seal-common_scenic.png |
| 21 | 918公里 | digits_mixed | flowing-brush | ✓ | True | 918公里 | 19213 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\21-flowing-brush-digits_mixed.png |
| 22 | 秋去秋又来 | repeated_char | loose-running-script | ✓ | True | 秋去秋又来 | 18688 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\22-loose-running-script-repeated_char.png |
| 23 | 一茶一饭间 | repeated_char | bold-vigorous | ✓ | False | 一茶大饭间 | 22079 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\23-bold-vigorous-repeated_char.png |
| 24 | 雾锁南迦巴瓦 | long_boundary_8char | casual-handwritten | ✓ | True | 雾锁南迦巴瓦 | 18676 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\24-casual-handwritten-long_boundary_8char.png |
| 25 | 苔痕上阶绿 | poetic_phrase | cascade-seal | ✓ | False | 台瞑上晚绿 | 18700 |  | docs\acceptance-records\attachments\cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08\25-cascade-seal-poetic_phrase.png |

> DashScope 响应不含计费字段；请用 generation_success 张数对照阿里云百炼控制台『用量/账单』页面核算实际总价，再除以张数得单价。