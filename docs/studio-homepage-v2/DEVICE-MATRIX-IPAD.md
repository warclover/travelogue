# iPad Safari 实机验收（iPadOS 17+）

> P3-20 · Playwright 视口模拟 **不能** 替代实机；本清单供 QA dogfood 签字。

---

## 1. 设备矩阵

| 设备 | OS | 浏览器 | 优先级 |
|------|-----|--------|--------|
| iPad Pro 11" 或等价 | **iPadOS 17+** | **Safari** | P0 |
| iPad Air | iPadOS 17+ | Safari | P1 |
| iPhone（对照） | iOS 17+ | Safari | P2 · 应显示 Unsupported |

---

## 2. 横屏（AC-HP2-12）

- [ ] 物理旋转至横屏，打开 dogfood `/v2`
- [ ] Bento **双列** grid（非三行堆叠）
- [ ] Carousel 横滑流畅；⤢ 可开 Lightbox
- [ ] 主 CTA ≥44px 触控目标（AC-HP2-21）
- [ ] 无横向溢出 / 地址栏遮挡 CTA

**Playwright 预检**：`test_ac_hp2_12_ipad_landscape_bento_grid`（1024×768）

---

## 3. 竖屏（AC-HP2-14）

- [ ] 竖屏打开 `/v2` → **Unsupported** 或旋转提示壳层
- [ ] 文案可读；无 Bento 误展示

**Playwright 预检**：`test_ac_hp2_14_ipad_portrait_rotate_hint`（768×1024）

---

## 4. Holdback 实机（可选）

- [ ] `auto` 10%：Safari 清除站点数据后多次打开 `/`，观察是否稳定 redirect 或留 v3
- [ ] Cookie `travelogue.studio.hp_bucket` 在设置→Safari→高级 中可见（HttpOnly 不可 JS 读，仅 Network 验证 Set-Cookie）

---

## 5. 记录

| 测试员 | 设备 | 日期 | 横屏 | 竖屏 | 备注 |
|--------|------|------|------|------|------|
| | | | | | |

归档至 `docs/acceptance-records/studio-homepage-v2-ipad-manual.json`（手填或 PM 模板）。

---

## 6. 已知限制

- 桌面 WebView2 壳层：**非 M20 阻塞**（OQ-WEBVIEW）。
- loopback L2 CDN 不触发：见 DATA-CONTRACT §4.2。
