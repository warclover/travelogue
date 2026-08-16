# 备用页型库 · 设计收件箱

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-16 |
| **DOC-STATUS** | **active**（设计收件箱，不是活目录合同） |
| **正式合同** | [PAGE-PACKET-CATALOG.md](../PAGE-PACKET-CATALOG.md)（附录 A）· [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](../../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md) |
| **浏览** | [gallery.html](./gallery.html) |
| **总表** | [CATALOG.md](./CATALOG.md) · [catalog.yaml](./catalog.yaml) |

这里只收你画好、还没升附录 A / 还没进引擎的页型。引擎、MCS、系列 YAML、CI **不读**本目录。

---

## 和正式库的边界

| | 本库 `reserve/` | 附录 A | 现网 LTE |
|--|-----------------|--------|----------|
| 状态 | `sketch` → `reviewed` | `designed` | `experimental` / `beta` / `ga` |
| id | 新的诚实 `page-*` | 同左，升格后写入 | 旧 `screen-*` 或已入库 `page-*` |
| 谁读 | 人 + 本库 gallery | 选型 / 成册 / 图标投影 | 渲染旧 trip + 现网选型 |
| 改几何 | 改数据包即可 | 改合同 | 改 YAML 会影响旧 trip |

禁止：把本库路径加进 `layout_templates`、改现网 `screen-*` 冒充迁完、用示意图旧名当正式 id。

升格路径：`sketch` → 你审成 `reviewed` → 按附录 A 字段抄进正式目录（状态改 `designed`）→ 再谈入库代码。

---

## 怎么加一张

1. 新建夹 `docs/templates/reserve/<id>/`，`<id>` = 数据包 `id`。  
2. 放入 `packet.yaml`（权威）、`USAGE.md`（字段投影，不另写散文）、`sketch.png`（示意图）。  
3. 在 `catalog.yaml` 与 `CATALOG.md` 各加一行。  
4. 在 `gallery.html` 的 `FACES` 数组加一条（微缩按数据包算，不手绘第二套几何）。

舞台默认 **16:9**。裁切默认 `relative-to-slot`（同比例铺满 / 更宽上下留白 / 更高左右留白 / 朝向不符禁入）。文案区可空，**不计入** `slotCount`。

---

## 示意图色（本库）

黑 = 纸 · 红 = 竖槽 · 蓝 = 横槽 · 金 = 方槽 · 绿 = 文案。示意图原稿可仍是单色红框；`gallery.html` 微缩按槽朝向分色。
