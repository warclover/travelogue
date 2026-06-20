# screen-portrait-3-editorial

- displayName: portrait · 3 · editorial
- status: beta
- stage: 16:9（LTE/probe 占位；web render 为视觉 intrinsic，见 PRD §3.1）

> **probe 参考态 ≠ web render 态**  
> Web 面不写 `--screen-aspect`；真实行宽/gap/脚线对齐由 `data-pattern="screen-portrait-3-editorial"` overlay 控制。  
> Probe baseline（LTE 参考态）：`layout_templates/probes/baselines/screen-portrait-3-editorial-contain.png` 与 `-cover.png`；更新命令见下。

```bash
python scripts/lte_probe_regress.py --screenshot --update-baselines
pytest tests/test_editorial_probe.py -q
```

Dogfood 并排对比页：

```bash
python scripts/compare_editorial_portrait_row.py path/to/trip.json
# → <trip>/editorial-compare/index-editorial-compare.html
```

| slot | role | displayAspect |
|------|------|---------------|
| 0 | portrait | derived（行宽三等分 · 样本竖图 native AR） |
| 1 | portrait | derived |
| 2 | portrait | derived |
