# TPC W4 · poster_bric Writer + layout_compare

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-18 |
| 关联 | [PRD-TEMPLATE-CONTRACT-V1](../PRD-TEMPLATE-CONTRACT-V1.md) §5.2 / AC-TPC-07 / AC-TPC-08；继承 GCS 轨 B |
| 状态 | **flag 默认关可狗粮** · 默认用户可见须过盲评（AC-GCS-BLIND） |

## 交付

| 项 | 路径 / 说明 |
|----|-------------|
| Composer stub | `travelogue/export/bric_compose.py`（shelf packer；签名对齐 MIT BRIC；可替换实现） |
| Writer | `travelogue/export/poster_bric_pack.py` |
| Flag | `features.gcs_poster_bric.enabled`（或 `studio.gcs_poster_bric`）默认 **false** |
| Recipe | `intent/engine/platform=poster_bric`；▾「单屏海报」；禁串「九宫格」 |
| Compare CLI | `scripts/layout_compare.py`（template_contract on vs off → JSON + HTML） |
| Studio | `longshot-export-panel.js` 次入口，仅 flag=on 时出现 |

## 合同核对（AC-TPC-07）

- n∈[3,9]；n=1–2 拒（`E_GCS_POSTER_N`）
- `mediaClass=collage` 排除
- contain 贴图；border=16 / spacing=8
- 导出后 `screens[]` fingerprint 不变；sidecar `runs/gcs-poster-bric.json`
- 不经 Playwright / 不写杂志屏

## 校验

```bash
pytest tests/unit/export/test_poster_bric_pack.py tests/unit/layout_engine/test_template_contract_w4_compare.py -q
python scripts/layout_compare.py --trip-dir trips/<id>
```

狗粮开启示例（config.yaml）：

```yaml
features:
  gcs_poster_bric:
    enabled: true
```

## GPL / vendor

本波使用自研 shelf packer stub（MIT 友好），**未** vendor MIT BRIC 源码；后续钉 commit 替换 `bric_compose` 体即可（D-GCS-05）。合入默认开前跑许可证扫描。

## 未做（刻意）

- 默认对用户可见 / 主 CTA 抢占
- MIT BRIC 源码 vendor
- AC-TPC-11 P95 全量测（可本周狗粮后补）
