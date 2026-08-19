# 设计工坊 · 页型收件箱

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-19 |
| **DOC-STATUS** | **active**（设计工坊现场，不是现网活目录） |
| **工坊总合同** | [PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md](../../PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md)（**TDV**） |
| **现网合同** | [PAGE-PACKET-CATALOG.md](../PAGE-PACKET-CATALOG.md)（附录 A）· [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](../../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md)（TSU） |
| **样例柜** | [PRD-RESERVE-SERIES-CABINET-V1.md](../../PRD-RESERVE-SERIES-CABINET-V1.md)（**RSC** · W1 已落地 · 成册细则） |
| **浏览** | [gallery.html](./gallery.html)（页型 / 成册） · [preview.html](./preview.html)（真图试印） · [GROUP-LOCK-GUIDE.md](./GROUP-LOCK-GUIDE.md)（一组一页） |
| **打开** | 双击 [serve.cmd](./serve.cmd)（或 `python serve.py`）。不要双击 HTML。不要走 Studio「版式」。 |
| **成册** | [series/folio-16-standard.yaml](./series/folio-16-standard.yaml)（16 页正对照本）。其它本同夹 `series/<id>.yaml`。 |
| **总表** | [CATALOG.md](./CATALOG.md) · [catalog.yaml](./catalog.yaml) |
| **未收角色** | [PROMOTE-ROLE-MAP.md](./PROMOTE-ROLE-MAP.md)（只收附录 B 没有的试验角色） |
| **星级** | [stars.yaml](./stars.yaml)（权威；页型 tab 点星后「写入星级」） |
| **备忘** | [后台模板设计验证工具备忘录.md](../../后台模板设计验证工具备忘录.md)（2026-08-19）· [临时模板库管线讨论备忘录.md](./临时模板库管线讨论备忘录.md)（2026-08-17 · 试印与双管线） |

这里只收你画好、还没升附录 A / 还没进引擎的页型。引擎、MCS、现网系列、CI **不读**本目录。试好的页型和角色系列经 **升格包** 交给现网，不是同步盘。

---

## 今日开工（运营）

1. 双击 [serve.cmd](./serve.cmd) 打开设计工坊。不要走 Studio「版式」，不要双击 HTML。  
2. 页型 tab：看微缩、点星、按下方「怎么加一张」加脸。状态由你标 `reviewed` / `promote-ready`。  
3. 成册 tab：编样例。「写入系列」只存工坊自己的本。  
4. 试印：按星级 = **未锁组 · 只测几何**。按系列若相册下备齐 `01`…`NN` 则**已锁组**（一组一页）；没子夹仍只测几何。备夹与手记见 [GROUP-LOCK-GUIDE.md](./GROUP-LOCK-GUIDE.md)。  
5. 认为敢给现网用：先标 `promote-ready`，再「导出升格」（线框见 TDV F1/F2）。点完不是已同步。薄柜未建，升格未闭环。

合同：[PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md](../../PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md) **v0.2.0**。

---

## 和正式库的边界

| | 本库 `reserve/` | 附录 A | 现网 LTE |
|--|-----------------|--------|----------|
| 状态 | `sketch` → `reviewed` → `promote-ready` | `designed` | `experimental` / `beta` / `ga` |
| id | 新的诚实 `page-*` | 同左，升格后写入 | 旧 `screen-*` 或已入库 `page-*` |
| 谁读 | 人 + 本库 gallery | 选型 / 成册 / 图标投影 | 渲染旧 trip + 现网选型 |
| 改几何 | 改数据包即可 | 改合同 | 改 YAML 会影响旧 trip |

禁止：把本库路径加进 `layout_templates`、改现网 `screen-*` 冒充迁完、用示意图旧名当正式 id。

升格路径：运营标 `reviewed` → `promote-ready` → 导出升格包（机器标未准入脸）→ 现网收下后附录 A 才写 `designed`。不是同步盘。

---

## 怎么加一张

日常用页型 tab **新建页型**（须 `serve.cmd`）：写入新夹 + `packet.yaml` + `USAGE.md` + 总表一行，微缩由扫夹均分草案投影，**免手加 `faces.js`**。示意图可后补；导出页型包仍必须有。

也可手建，按 TDV §7.1 七步。W3 已扫夹时第 7 步可免；未扫夹则缺第 7 步微缩墙不出现：

1. 新建夹 `docs/templates/reserve/<id>/`，`<id>` = 数据包 `id`。  
2. 放入 `packet.yaml`（权威）。  
3. 放入 `USAGE.md`（字段投影，不另写散文）。  
4. 放入 `sketch.png`（示意图；导出页型包必须有）。  
5. 在 `catalog.yaml` 加一行。  
6. 在 `CATALOG.md` 加一行。  
7. 在微缩数据源加一条（现为 `faces.js` / gallery `FACES`；微缩按数据包算，不手绘第二套几何）。

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

在 [gallery.html](./gallery.html) **微缩** tab 每张卡片上点「无 / ★ / ★★ / ★★★」。再点同一档会取消。点完用工具条 **写入星级** 覆盖 `stars.yaml`（Chrome 会弹出保存框，请选本夹这个文件；其它浏览器会下载，把文件挪回本夹覆盖）。然后提交这一份文件即可。

真图试印：[preview.html](./preview.html)。**按星级**仍铺 2 星以上各脸（朝向轮转）= **未锁组 · 只测几何**。**按系列**铺柜里已写入的本。相册下有 `01`…`NN` 子夹则第 n 页只吃该夹（**已锁组**）；没有则按朝向消耗（**未锁组 · 只测几何**）。密页未锁组时顶栏琥珀「装错不代表脸差」。照片只在本机读，不进引擎。建议张数跟该本 `photo_span` 下限走。备夹与「组对了 / 组错了 / 脸错了」手记见 [GROUP-LOCK-GUIDE.md](./GROUP-LOCK-GUIDE.md)。

试印手记（不进工坊、不进升格包）按页三栏：**组对了 / 组错了 / 脸错了**。组错了先改夹，脸错了攒一批再改包。

镜像脸不自动继承，要升星请单点。

---

## 成册（样例柜）

合同：[PRD-RESERVE-SERIES-CABINET-V1.md](../../PRD-RESERVE-SERIES-CABINET-V1.md)。**日常双击 [serve.cmd](./serve.cmd)**，不要双击 HTML。`file://` 只保证金样 16 页仍能看见。

[gallery.html](./gallery.html) 第二个 tab。一本 = 一份 `series/<id>.yaml`。金样 [folio-16-standard.yaml](./series/folio-16-standard.yaml) 禁止新建占用；打开该本后仍可写入迭代。书衣沿用现网默认，**不**画封面封底砖。

- **新建**：默认空轨，可选从已有本复制。页数任意。写入前试印目录没有这本。
- **写入系列** 只覆盖当前 id 的 YAML，不动 `stars.yaml`，不写 `trip.json`。引擎不读。
- **导出升格系列** 另存 `magazine-{页数}-{密度}` 角色包 + 检查单。禁止任何 `folio-*` 正式 id。点完不是已同步。
- 左栏库存 = 本库全部脸，按槽数分组；星级只作排序。5 槽以上标慎用，仍可拖。
- 拖到轨的空隙 = 插入；拖到已有砖 = 只换同族同槽数的脸；朝向或家族不符拒收。
- 检查器可改纲领和弹性位。邻页双密页、opener 连 opener、closer 在中段（≤ 目标页数 − 2）会红灯。
- 「按本序试印」打开 [preview.html](./preview.html#series=folio-16-standard)，下拉选本。一组一页：子夹 `01`…`NN`（NN = 该本页数），见 [GROUP-LOCK-GUIDE.md](./GROUP-LOCK-GUIDE.md)。

---

## 示意图色（本库）

黑 = 纸 · 红 = 竖槽 · 蓝 = 横槽 · 金 = 方槽 · 绿 = 文案。示意图原稿可仍是单色红框；`gallery.html` 微缩按槽朝向分色。
