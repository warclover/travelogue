# 备用页型库 · 设计收件箱

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-16 |
| **DOC-STATUS** | **active**（设计收件箱，不是活目录合同） |
| **正式合同** | [PAGE-PACKET-CATALOG.md](../PAGE-PACKET-CATALOG.md)（附录 A）· [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](../../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md) |
| **浏览** | [gallery.html](./gallery.html) · [preview.html](./preview.html)（2 星以上真图预览） |
| **总表** | [CATALOG.md](./CATALOG.md) · [catalog.yaml](./catalog.yaml) |
| **星级** | [stars.yaml](./stars.yaml)（权威；微缩页点星后「写入本库」） |
| **备忘** | [临时模板库管线讨论备忘录.md](./临时模板库管线讨论备忘录.md)（2026-08-17 · 试印与双管线） |

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

舞台默认 **16:9**。裁切默认 `relative-to-slot`（同比例铺满 / 更宽上下留白 / 更高左右留白 / 朝向不符禁入）。文案区可空，**不计入** `slotCount`。新脸默认 **无星**，不必改数据包。

---

## 优先级（本库）

选型用，不是引擎权重。**只写** [stars.yaml](./stars.yaml)。未列出的脸 = 无星。数据包 / 总表 / USAGE **不写**星级。

| 档 | 值 | 含义 |
|----|----|------|
| 无星 | `0` | 默认 |
| 1 星 | `1` | 偶尔用 |
| 2 星 | `2` | 常用 |
| 3 星 | `3` | **最常用** |

在 [gallery.html](./gallery.html) 每张卡片上点「无 / ★ / ★★ / ★★★」。再点同一档会取消。点完用工具条 **写入本库** 覆盖 `stars.yaml`（Chrome 会弹出保存框，请选本夹这个文件；其它浏览器会下载，把文件挪回本夹覆盖）。然后提交这一份文件即可。

2 星以上可用 [preview.html](./preview.html) 选本地照片文件夹，按 Web 游记预览那样竖翻 16:9 真图。照片只在浏览器里读，不进引擎、不导出。

镜像脸不自动继承，要升星请单点。

---

## 示意图色（本库）

黑 = 纸 · 红 = 竖槽 · 蓝 = 横槽 · 金 = 方槽 · 绿 = 文案。示意图原稿可仍是单色红框；`gallery.html` 微缩按槽朝向分色。
