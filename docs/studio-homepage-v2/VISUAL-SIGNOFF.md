# 视觉 Sign-off 清单（AC-03 / 08 / 12 / 17 / 18）

> P3-19 · 设计 + QA 人工签字 · 自动化截图由脚本预采集。

---

## 1. 采集命令

```bash
pip install -e ".[dev,playwright]" && playwright install chromium
python scripts/studio_ac_visual_capture.py
```

默认输出：`docs/acceptance-records/studio-homepage-v2-visual/*.png`

| 文件 | AC | 检查点 |
|------|-----|--------|
| `01-demo-same-trip-desktop.png` | HP2-03 | 16:9 scroll + 9:16 longshot 同源京都 trip；demo-flag 可见 |
| `02-odd-tail-carousel.png` | HP2-08 | 末 spread 左对齐、右槽留白；dots 与 manifest 一致 |
| `03-ipad-landscape-bento.png` | HP2-12 | 1024×768 双列 Bento，非三行堆叠 |
| `04-importing-cold-static-bg.png` | HP2-17 | Importing 冷启动：静帧背景、无 Ken Burns |
| `05-first-success-shelf-shell.png` | HP2-18 | FirstSuccess overlay 下仍见书架壳层 |

**PLACEHOLDER 阶段**：截图仅作布局参考；设计切图到位后 **必须重采** 并递增 `manifest.version`。

---

## 2. Sign-off 表

| AC | 设计 ✓ | QA ✓ | 日期 | 备注 |
|----|--------|------|------|------|
| HP2-03 | | | | |
| HP2-08 | | | | |
| HP2-12 | | | | |
| HP2-17 | | | | |
| HP2-18 | | | | |

---

## 3. 切图到位后的视觉 diff（AC-03 扩展）

设计交付 WebP 后：

1. 替换 `templates/studio/assets/demo-showcase/` 下文件。
2. 重跑 `python scripts/generate_demo_placeholders.py` **勿**覆盖真实切图。
3. `pytest tests/test_studio_home_v2.py::test_demo_showcase_manifest_valid -q`
4. 重采截图；可选 Percy / 手工 side-by-side 与线框 v1.6 对比。

---

## 4. 自动化对照

以下 AC 已有 Playwright 断言，sign-off 以截图 + 自动绿为准：

- HP2-08 → `test_ac_hp2_08_odd_tail_left_align`
- HP2-12 → `test_ac_hp2_12_ipad_landscape_bento_grid`
- HP2-17 → `test_ac_hp2_17_importing_cold_static_background`
- HP2-18 → `test_ac_hp2_18_first_success_shelf_shell`
