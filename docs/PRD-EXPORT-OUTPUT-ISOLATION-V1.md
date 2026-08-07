# PRD-EXPORT-OUTPUT-ISOLATION-V1 · 导出产物独立文件夹

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v0.5.0 |
| **状态** | Stage 1+2+3 **已全部实施完成** + 收尾复查已修复 1 处真实缺口（2026-08-07，见 §7 实施记录） |
| **模块代号** | EOI（Export Output Isolation · 导出产物文件夹隔离） |
| **前置条件** | [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md)（长图导出主线，`PlatformExportWriter`/`_write_output` 落盘逻辑来源）· [PRD-BATCH-EXPORT-MULTISELECT-V1.md](./PRD-BATCH-EXPORT-MULTISELECT-V1.md)（多平台批量导出）· [PRD-EXPORT-CARD-COMPOSE-V1.md](./PRD-EXPORT-CARD-COMPOSE-V1.md)（小红书/公众号/画册 Compose 管线）· [PRD-ALBUM-EXPORT-BOOKENDS-V1.md](./PRD-ALBUM-EXPORT-BOOKENDS-V1.md)（画册封面封底） |
| **更新日期** | 2026-08-07 |

---

## 1. 背景与问题

用户反馈（2026-08-07）：导出长图后点「在文件夹中显示」/「打开长图文件夹」，Windows 会用 `explorer /select,` 打开这本游记的**工程根目录**（`trips/{tripId}/`）。这个目录除了刚导出的图片外，还混着十几到二十几个渲染引擎需要的工程文件——对不理解前端/HTML 的普通用户来说，这些文件毫无意义，只会制造"是不是导出错了""这些文件能不能删"的疑惑。

现状核实（真实游记目录 `trips/linzhi/`，未做任何导出前）：

```
index.html / index-mobile.html / index-longshot.html
journal.css / journal-screens.css / longshot.css / screenplay.css / copy-display.css / inline-edit.css
longshot.js / longshot-bridge.js / screenplay.js / screenplay-hash.js / screenplay-bookmarks.js /
breath.js / breath-gsap.js / breath-image.js / breath-lenis.js / breath-highlight.js /
inline-edit.js / scroll-nav.js / share.js / copy-toggle.js
README.md
```

一旦导出长图，产物会**直接落进同一层**，与上述文件并排显示。

代码层核实——所有面向用户的导出产物写盘目的地都是 `trip_dir` 本身：

| 导出类型 | 落盘函数 / 位置 |
|------|------|
| 微信群整卷/按章长图（分支 A） | `_write_output(_tracked)`（`travelogue/export/longshot.py`），路径 `trip_dir / default_longshot_output_name(...)` |
| 客户端兼容模式上传（P2） | `write_longshot_upload`（`travelogue/export/longshot.py:495`），路径 `trip_dir / safe_name` |
| 朋友圈/Instagram/微博/抖音封面/自定义（分支 B） | `PlatformExportWriter(trip_dir, prefix, ...)`（`travelogue/export/platform_longshot.py:516`） |
| 小红书/公众号/画册拼贴 | `PlatformExportWriter(trip_dir, prefix, ...)`（`travelogue/export/collage_pack.py:447`） |
| 单屏海报 | `PlatformExportWriter(trip_dir, prefix, ...)`（`travelogue/export/poster_bric_pack.py:207`） |
| 朋友圈九宫格 | `PlatformExportWriter(trip_dir, prefix, ...)`（`travelogue/export/photo_grid_pack.py:129`） |
| 权威导出清单 | `trip_dir / "longshot-current.json"`（`travelogue/export/longshot.py:25,288,298`） |
| 打印 PDF | `trip_dir / f"{title}-print.pdf"`（`travelogue/export/pdf.py:61`） |
| 分享 zip | `trip_root / default_zip_name`（`travelogue/export/packager.py:143`） |

「在文件夹中显示」本身的实现很干净——`reveal_path_in_folder`（`travelogue/export/longshot.py:1331`）在 Windows 下就是 `explorer /select, <文件路径>`，即"打开该文件所在的目录并选中它"。**它不关心目录里还有什么**，只是忠实地把用户带到文件所在的那层目录。也就是说：只要产物的落盘目的地本身是干净的子目录，reveal 出来的窗口自然就是干净的，不需要改 reveal 逻辑，只需要改"写到哪"。

---

## 2. 目标 / 非目标

| 编号 | 目标 | 说明 |
|------|------|------|
| G-EOI-01 | 所有面向用户的导出产物统一写入 trip 工程目录下一个专属子文件夹 | 覆盖：长图整卷/按章、平台配图（朋友圈/小红书/Instagram/微博/抖音/自定义）、画册、单屏海报、九宫格、PDF、分享 zip |
| G-EOI-02 | 用户打开该子文件夹时，只看到导出产物本身，看不到任何 `.js`/`.css`/`.html`/`trip.json` 等工程文件 | 对应用户原始反馈；**七席回写（BLK-EOI-03）**：子目录内除产物外仍会保留 1 个 `longshot-current.json` 权威清单文件，这是已知设计取舍，不算违反本目标（20+ 工程文件 → 0 个是真实收益，1 个清单文件不影响体感） |
| G-EOI-03 | 「在文件夹中显示」/「打开长图文件夹」等入口零感知升级——用户点击行为不变，打开的窗口内容变干净 | 复用现有 `reveal_path_in_folder`，只改传入路径 |
| G-EOI-04 | `longshot-current.json` 权威清单迁移后继续正确工作 | 与产物同层是既有设计原则，迁移到子目录内即可，不改数据结构 |
| G-EOI-05 | 渲染引擎（Playwright 加载 `index.html`/`index-longshot.html`）不受影响 | 只改变"写出"目的地，不改变"读入"的工程文件位置 |
| G-EOI-06 | 老游记（本次上线前已导出、散落在 trip 根目录的产物）不产生用户可见的"文件消失了"或报错 | 迁移/清理策略需拍板，见 D-EOI-05 |

| 编号 | 非目标 | 说明 |
|------|--------|------|
| NG-EOI-01 | 不改变导出触发流程、Job 进度条、平台选择 UI 的交互形态 | 只改变文件落盘位置与"打开文件夹"指向的路径 |
| NG-EOI-02 | 不改变各导出管线本身的渲染/切分/合成逻辑与文件命名规则 | `{展示名}-长图[-nn].ext` 等命名沿用现状（D-SFI-07），只是目录前缀变化 |
| NG-EOI-03 | 不清理/迁移 trip 根目录下与导出无关的既有工程文件 | `index.html` 等本就该留在根目录，不受影响 |

---

## 3. 方案设计

### 3.1 拍板决策

| 编号 | 决策 | 说明 |
|------|------|------|
| D-EOI-01 | 新增跨模块共享常量 `EXPORT_OUTPUT_DIRNAME`，所有落盘点从 `trip_dir` 改为 `trip_dir / EXPORT_OUTPUT_DIRNAME` | **七席回写（BLK-EOI-01）钉死落点**：常量定义在 `travelogue/export/longshot.py`（与 `LONGSHOT_CURRENT_NAME` 相邻），不新建独立模块——现状核查 `platform_longshot.py`/`collage_pack.py` 已经 `from travelogue.export.longshot import (...)` 多个符号，`longshot.py` 未反向依赖 `packager.py`/`pdf.py`，放这里对下游是单向依赖、无循环风险；`pdf.py`/`packager.py` 各新增一行 `from travelogue.export.longshot import EXPORT_OUTPUT_DIRNAME`。各写入点原有的 `mkdir(parents=True, exist_ok=True)` 逻辑不用新增，只改传入路径本身（`PlatformExportWriter.write`/`_write_output` 已自带 mkdir） |
| D-EOI-02 | 子文件夹命名——中文可读、跨平台文件名安全、语义覆盖"图片+PDF+zip"全部产物类型 | **已拍板：「导出文件」**（用户 2026-08-07 确认）。语义中性，覆盖全部产物类型；不用英文 `exports/`，普通用户认不出 |
| D-EOI-03 | 「在文件夹中显示」/「打开长图文件夹」不改前端交互与调用方式，只改后端返回的 `relPath` 天然带子目录前缀 | `rel_to_trip(trip_dir, out_path)` 计算相对路径时，`out_path` 本身已经在子目录下，返回值自然变成 `导出文件/示例游记-长图.png`；`handle_reveal` 拼接 `trip_dir / rel_path` 逻辑不用改（`travelogue/web/studio_handlers/export_handlers.py:1063` 起） |
| D-EOI-04 | `longshot-current.json` 迁移到子目录内（`trip_dir / EXPORT_OUTPUT_DIRNAME / longshot-current.json`） | 保持"清单与产物同层"的既有设计原则；`write_longshot_current`/`read_longshot_current` 调用侧改传子目录路径即可，数据结构不变 |
| D-EOI-05 | 老游记迁移策略——首次在该游记下发起新导出时，如何处理 trip 根目录下残留的旧产物 | **已拍板：不处理**（用户 2026-08-07 确认：当前均为测试数据，无真实用户，无需迁移/清理成本）。新导出统一走新子目录；trip 根目录下的旧产物原地保留、不迁移、不清理，也不扩展 `cleanup_legacy_longshot_outputs` 的清理范围。若未来上线后出现真实用户历史数据，再单独评估是否需要一次性迁移脚本（见 OQ-EOI-02） |
| D-EOI-06 | PDF (`export_trip_pdf`) 和分享 zip (`packager.py`) 是否纳入同一子目录 | 用户已确认"全部导出类型统一"，纳入范围：`{title}-print.pdf`、`{trip_root.name}-分享.zip` 落盘路径同样加上 `EXPORT_OUTPUT_DIRNAME` 前缀 |
| D-EOI-07 | `_LONGSHOT_UPLOAD_RESERVED_NAMES`（`longshot.py:454`，防止客户端上传覆盖 `trip.json`/`index.html` 等）是否需要同步调整 | 这些保留名原本防的是"落在 trip 根目录"的场景；产物迁到子目录后，理论上碰不到这些文件了，但建议保留原校验作为纵深防御，不删除 |

### 3.2 涉及改动点（后端）

| 文件 | 改动 |
|------|------|
| `travelogue/export/platform_longshot.py:516` | `PlatformExportWriter(trip_dir, ...)` → `PlatformExportWriter(trip_dir / EXPORT_OUTPUT_DIRNAME, ...)` |
| `travelogue/export/collage_pack.py:447` | 同上 |
| `travelogue/export/poster_bric_pack.py:207` | 同上 |
| `travelogue/export/photo_grid_pack.py:129` | 同上 |
| `travelogue/export/longshot.py`（`_write_output`/`_write_output_tracked`/`write_longshot_upload`/`default_longshot_output_name` 调用侧） | 输出路径前缀加 `EXPORT_OUTPUT_DIRNAME` |
| `travelogue/export/longshot.py`（`LONGSHOT_CURRENT_NAME` 读写：`write_longshot_current`/`read_longshot_current`） | 调用侧改传子目录路径 |
| `travelogue/export/pdf.py:61` | `out_path` 前缀加子目录 |
| `travelogue/export/packager.py:143` | `zip_path` 前缀加子目录（注意：`legacy_zip` 清理逻辑仍指向旧位置，需要同时清） |
| `travelogue/web/studio_handlers/common.py:32`（`rel_to_trip`） | 逻辑不用改，天然生效 |
| `travelogue/web/studio_handlers/export_handlers.py`（`handle_reveal`） | 逻辑不用改，`relPath` 校验（`target.relative_to(trip_dir)`）天然覆盖子目录 |

### 3.3 涉及改动点（前端，确认无需改动的原因）

- `templates/studio/js/longshot-export-panel.js`、`templates/studio/preview-toolbar/longshot.js`、`templates/studio/homepage-v2/shelf-longshot.js` 里"在文件夹中显示"/"打开长图文件夹"都是把后端返回的 `outputs[]`（即 `rel_to_trip` 算出的相对路径）原样传给 `/__travelogue/reveal`；只要后端返回值已经带上子目录前缀，前端零改动。
- 唯一需要人工过一遍的是：确认没有前端代码"猜测"或硬编码产物路径（而非直接使用后端返回值）——已检索未发现此类硬编码。

---

## 4. 与既有系统的关系

| 现有组件 | 影响 |
|----------|------|
| `PlatformExportWriter`（原子 `.part`→rename 写入） | **不改内部逻辑**，只改构造时传入的 `directory` 参数 |
| `reveal_path_in_folder` | **不改**——本身就是"打开文件所在目录"，子目录变化后天然生效 |
| `rel_to_trip` | **不改**——只是计算出的相对路径字符串多了一层前缀 |
| Playwright 渲染（读取 `index.html`/`index-longshot.html`） | **不改**——读入路径不受影响，只有写出目的地变化 |
| `cleanup_legacy_longshot_outputs` | 若采用 D-EOI-05 选项 A，需要扩展其 glob 范围到"trip 根目录下的旧产物"，与"子目录内的新产物"分开处理 |
| 各平台文件命名规则（`file_prefix_for_platform`/`default_longshot_output_name`） | **不改**——只是目录前缀变化，文件名本身不变 |

---

## 5. 验收标准

| 编号 | 内容 |
|------|------|
| AC-EOI-01 | 导出微信群长图（整卷/按章）、任一平台配图、画册、单屏海报、九宫格后，产物均出现在 `trip_dir / EXPORT_OUTPUT_DIRNAME` 下，trip 根目录不再新增图片文件 |
| AC-EOI-02 | 点击「在文件夹中显示」/「打开长图文件夹」，Explorer 打开的窗口里只有本次（及历史）导出产物 + `longshot-current.json`，没有任何 `.js`/`.css`/`.html`/`trip.json`。**七席回写（BLK-EOI-04）**：需有可执行断言校验"目标目录文件列表 = 历史+本次产物 ∪ {`longshot-current.json`}，且不含任意 `.js`/`.css`/`.html`/`trip.json`"，不能只测"文件写到了某路径"这种单元级断言 |
| AC-EOI-03 | `longshot-current.json` 在子目录内可被正确读写，批量导出/单平台导出后清单内容与实际文件一致 |
| AC-EOI-04 | PDF、分享 zip 同样落在子目录内，下载/回归行为不变 |
| AC-EOI-05 | 老游记（子目录改动上线前已导出过）再次发起新导出，不报错、不阻断；根目录残留旧产物原地保留不动（D-EOI-05） |
| AC-EOI-06 | 客户端兼容模式（P2）上传长图后，产物同样落在子目录内，保留名/后缀黑名单校验依旧生效 |
| AC-EOI-07 | 渲染/预览（Web 预览、`index-longshot.html`）在改动前后行为完全一致（回归） |

---

## 6. 分阶段计划

1. **Stage 1**：新增 `EXPORT_OUTPUT_DIRNAME` 常量 + 落地 D-EOI-05/06/07 拍板；改造 `PlatformExportWriter` 的四个调用点（`platform_longshot.py`/`collage_pack.py`/`poster_bric_pack.py`/`photo_grid_pack.py`）与分支 A（`longshot.py` 的 `_write_output`/`write_longshot_upload`），单测覆盖 AC-EOI-01/02/06。
2. **Stage 2**：迁移 `longshot-current.json`（`write_longshot_current`/`read_longshot_current` 调用侧），单测覆盖 AC-EOI-03；改造 `pdf.py`/`packager.py`（含 legacy zip 清理路径同步），覆盖 AC-EOI-04。**七席回写（BLK-EOI-02）**：`tests/unit/export/test_longshot_current.py` 现状是直接对 `trip_dir` 根目录做文件读写与路径断言（12+ 处），需结构性重写，不是"调用侧改一行"；同时核查 `test_longshot_batch.py`/`test_card_bookends.py`/`test_export_zip_budget.py` 是否有同类路径假设，一并列入本阶段工作量，单独预算人日。
3. **Stage 3**：老游记回归 + 前端 reveal 全链路人工核对（真实游记走一遍每种导出类型，点「在文件夹中显示」核对窗口内容），覆盖 AC-EOI-05/07；补齐 AC-EOI-02 的端到端目录内容断言（BLK-EOI-04）。**已完成，见 §7.4。**

---

## 7. 实施记录（2026-08-07 · Stage 1+2+3）

Stage 1（落盘改造）与 Stage 2（`longshot-current.json` 迁移 + PDF/zip 改造 + 测试重写）合并一次性实施，因为二者共享同一批调用点、拆开反而增加中间不一致窗口。

### 7.1 落盘改造（覆盖 §3.2 全部改动点）

- `EXPORT_OUTPUT_DIRNAME = "导出文件"` 定义在 `travelogue/export/longshot.py`（按 D-EOI-01 拍板）。
- 四个 `PlatformExportWriter` 调用点（`platform_longshot.py`/`collage_pack.py`/`poster_bric_pack.py`/`photo_grid_pack.py`）与分支 A 三处 `_write_output_tracked` 调用点、`write_longshot_upload`，全部改写入 `trip_dir / EXPORT_OUTPUT_DIRNAME`。CLI/Job 层若显式传入 `--output`/`output=` 路径，仍原样尊重（不强制改写用户指定的绝对路径）。
- `write_longshot_current`/`read_longshot_current`/`resolve_complete_segment_batch`/`maybe_write_longshot_current_after_upload` 全部改为读写子目录；`resolve_complete_segment_batch` 采用"子目录存在则优先用子目录，否则回退 trip_dir 根目录"策略，兼容老游记。
- `pdf.py`/`packager.py` 输出路径加子目录前缀，并补上 `parent.mkdir(parents=True, exist_ok=True)`（此前依赖 trip_dir 必然已存在，子目录首次导出时需要显式建目录）。

### 7.2 实施中发现的未在评审范围内的真实缺口（本次已一并修复）

七席评审聚焦"改哪几个写入点"，但实际动手改代码时发现：**首页书架卡片预览（`shelf.js`/`bento-preview-picker.js`）与手机框长图滚动预览（`studio_bento_preview.py`）从未通过 `PlatformExportWriter`/`longshot.py` 的公开函数读取产物，而是直接对 `trip_dir` 做 `glob("*-长图*.png")` 等裸目录扫描**（`travelogue/web/studio_trips.py::_longshot_files/_pick_preview/longshot_reveal_rel_path`，`travelogue/web/studio_bento_preview.py::_glob_export_images` 及其调用方）。若只改写入点不改这层，产物迁到子目录后**首页预览图会静默失效**（找不到最新导出的长图），比原问题更糟。

修复方式（已实施，非新增决策，是既有 D-EOI-01 常量在读侧的自然延伸）：

- 上述扫描函数统一改为「trip_dir 根目录 + `EXPORT_OUTPUT_DIRNAME` 子目录」两处都扫（子目录不存在时静默跳过），对外返回值从裸文件名改为 `path.relative_to(trip_dir).as_posix()`，使老游记（产物在根目录）与新游记（产物在子目录）都能被正确发现和拼接 URL。
- `longshot-current.json` 里存的"清单文件名"设计上一直是裸文件名（约定"与清单同层"），迁移后含义变为"与清单同层的子目录内"；`studio_bento_preview.py`/`studio_trips.py` 里从清单取文件名拼 URL/relPath 的三处调用点相应补回 `EXPORT_OUTPUT_DIRNAME/` 前缀。
- 分享 zip 的下载链接（`render/context.py::has_share_zip`、`render/assemble.py` 里的 `shareZipFile`/`share.js::downloadZip`）同理：`has_share_zip` 改查子目录；`shareZipFile` 改为带子目录前缀的相对路径，否则渲染出的"下载分享包"按钮会指向一个不存在的根目录文件。

### 7.3 测试改动（对应 BLK-EOI-02 预估）

`test_longshot_current.py` 按预估做了结构性重写（清单与产物一起搬进子目录场景）；另有 `test_collage_pack.py`/`test_longshot_batch.py`/`test_photo_grid_pack.py`/`test_poster_bric_pack.py`/`test_output_recipe_cli_handlers.py`/`test_studio_handlers_longshot_batch.py`（评审时未点名，实测确认同类路径假设）改用 `EXPORT_OUTPUT_DIRNAME` 前缀断言产物位置；`test_longshot_share.py`（分享 zip 下载链接）、`test_studio_bento_preview.py`/`test_studio_m10.py`（书架预览/reveal 兜底路径）补充子目录场景断言。`tests/unit/export`、`tests/unit/web/handlers`、`tests/unit/render`、`tests/unit/web/test_studio_bento_preview.py`/`test_studio_m10.py` 全量跑过，除两个与本改动无关的既有环境问题外（网络依赖的 LLM 集成用例超时；`test_studio_export_zip` 章节数校验在 baseline 上同样失败；`test_longshot_smoke` 因本机 Playwright Sync/asyncio 冲突失败），全部通过。

### 7.4 Stage 3：老游记真实回归 + reveal 人工核对 + AC-EOI-02 端到端断言（2026-08-07）

**老游记真实回归**：把仓库里已有真实产物的老游记 `trips/demo-album/`（根目录混着 `index.html` 等工程文件 + 4 张此前导出的 `*-album-*.png`）复制到隔离临时目录，走 CLI 真实跑了一轮（非 mock）：九宫格（`moments_grid`）、小红书拼贴（`xiaohongshu`）、画册跨页（`album_spread`）、分享 zip（含真实 Playwright 渲染 `index.html`）、打印 PDF（真实 Playwright 起本地 server 截 PDF）。结果：

- 5 种类型全部成功落盘到 `导出文件/` 子目录，根目录不再新增任何图片/PDF/zip。
- 根目录里 4 张老 `*-album-*.png` 的 mtime/字节内容全程未变——D-EOI-05「不处理」在真实数据上验证成立。
- 新导出的同名前缀产物（如新的 `*-album-01.png`）与旧产物文件大小不同、和而不冲突，说明子目录隔离确实避免了新旧产物混淆。
- 唯一 2 处失败均确认与本改动无关：`--intent wechat_official` 不在该 CLI 命令支持的意图枚举里（既有限制，`export_collage_pack(platform=...)` 本身是支持的，只是没接到这个 `--intent` 入口）；`--platform wechat_chat` 分支 A 在这条 demo 数据上于 `page.wait_for_function` 阶段超时（发生在任何文件写入之前，是该条 demo 数据/index-longshot.html 就绪信号的兼容性问题，不是路径改动引入的）。

**reveal 人工核对**：直接复用生产同一份 `reveal_path_in_folder`（不是重新写一段模拟逻辑），对着上面新导出的一个小红书拼贴 PNG 触发，在开发者本机真实弹出了 Explorer 窗口，窗口打开的正是 `导出文件/` 子目录——与 AC-EOI-02/G-EOI-03 描述的体验一致。

**AC-EOI-02 端到端断言**：补充了 `tests/unit/export/test_export_output_isolation.py`，混合跑九宫格 + 小红书拼贴两种产物 + 写一次权威清单后，断言「导出文件」子目录的文件全集恰好等于「全部产物 ∪ {`longshot-current.json`}」，且逐一检查没有任何 `.js`/`.css`/`.html`/`trip.json`；另一条用例专门验证 D-EOI-05（老游记根目录旧产物在新导出后字节/mtime 均不变）。这条断言比 Stage 1/2 里"文件写到了某路径"的单元级断言更贴近用户真实会看到的东西，直接对应七席回写的 BLK-EOI-04。

### 7.5 收尾复查（2026-08-07 · 对照 PRD 逐条排查遗漏）

三阶段完成后，对照 §2/§3/§5 逐条重新核对实施与文档，额外发现并修复 1 处真实缺口、补齐 1 处验收覆盖：

- **真实缺口（本次修复）**：`templates/studio/homepage-v2/shelf-longshot.js::resolveShelfLongshotRevealRel` 直接 `fetch("/" + tripId + "/longshot-current.json")`——这是 §3.3 声称"已检索未发现硬编码产物路径"时漏掉的一处：它不经过后端 `relPath`/`longshotRevealRelPath` 字段，而是自己拼了一条不含 `EXPORT_OUTPUT_DIRNAME` 前缀的静态文件 URL。清单迁移子目录后，这条请求对新游记必定 404（该函数原有的"清单 → `/__travelogue/trips` 兜底"三级兜底链兜住了，不影响最终能否打开文件夹，但白白多打一次必 404 的请求，且语义上是"猜路径"而非"用后端返回值"，属于本 PRD 明确要防的硬编码）。修复：该文件内新增本地常量 `EXPORT_OUTPUT_DIRNAME = "导出文件"`（并注释标注需与 `travelogue/export/longshot.py` 的同名常量保持一致），fetch URL 与解析出的文件名都补上子目录前缀。已用引用该文件源码做契约断言的既有测试（`test_ftue_w1_contracts.py`/`test_output_recipe_guards.py`/`test_studio_home_v2.py`/`test_ftue_telemetry.py`，共 67 例）验证未破坏既有契约。
- **验收覆盖补齐**：`tests/unit/export/test_cqa_longshot_upload.py::test_write_longshot_upload_ignores_client_filename` 此前只断言产物文件名正确、且没落到"客户端猜的文件名"下，并未显式断言产物落在 `EXPORT_OUTPUT_DIRNAME` 子目录——AC-EOI-06 需要的"落子目录"这一点其实没有可执行断言直接覆盖（旧断言在改动前后都成立，测不出回退）。补充 `assert out.parent == trip / EXPORT_OUTPUT_DIRNAME` 与 `assert not (trip / out.name).exists()`。
- **排查过但确认无问题（记录以避免重复排查）**：`packager.py` 打包 zip 时用的 `collect_asset_paths` 只按 `trip.json` 里 `assets[]` 精确取文件，不是目录 walk，因此不会把 `导出文件/` 子目录内容误打包进分享 zip；`test_card_bookends.py`（纯内存渲染卡片，不涉及路径）与 `test_export_zip_budget.py`（全程用返回值 `result.zip_path`，无硬编码路径，且是 `pytest.mark.integration` 网络依赖用例，与本改动无关）经检查均不需要改动；`_LONGSHOT_UPLOAD_RESERVED_NAMES`/`cleanup_legacy_longshot_outputs` 按 D-EOI-07/D-EOI-05 原样保留、仍只作用于 trip 根目录，未被误扩展或误收窄。
- 复查后再次跑 `tests/unit/export` 全量（270 passed）与 `tests/unit/render` + `tests/unit/web/test_studio_m10.py` + `tests/unit/web/test_studio_bento_preview.py` + `tests/unit/web/handlers`（380 passed / 6 skipped / 1 failed），唯一失败项是 §7.3 已记录过的既有基线问题 `test_studio_export_zip`（章节数校验，baseline 上同样失败，与本改动无关）。

---

## 8. 开放问题

| 编号 | 问题 | 备注 |
|------|------|------|
| OQ-EOI-01 | ~~子文件夹最终命名~~ | **已关闭**：D-EOI-02 拍板为「导出文件」 |
| OQ-EOI-02 | 未来出现真实用户历史数据后，老游记是否需要一次性迁移脚本 | 当前 D-EOI-05 拍板为"不处理"（测试数据阶段），留待正式上线前重新评估，不阻塞本次实施 |
| OQ-EOI-03 | 是否需要在子文件夹内额外放一个极简说明（如「这里是导出的图片，可以直接分享」的 txt/说明），进一步降低用户困惑 | 非必需，可作为后续小优化 |

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.5.0 | 2026-08-07 | 收尾复查（见 §7.5）：对照 PRD 逐条排查，发现并修复 §3.3"前端无硬编码路径"结论的一处漏检——`shelf-longshot.js` 直接 fetch 未带子目录前缀的 `longshot-current.json`，已修复并保留三级兜底；补齐 `test_cqa_longshot_upload.py` 对 AC-EOI-06"落子目录"的显式断言。其余对照项（打包 zip 资产收集、`test_card_bookends.py`/`test_export_zip_budget.py`、legacy 清理范围）核查后确认均无问题 |
| v0.4.0 | 2026-08-07 | Stage 3 完成（见 §7.4）：用仓库里真实的老游记 `trips/demo-album/` 走 CLI 真实跑通九宫格/小红书/画册/PDF/分享zip，验证 D-EOI-05 在真实数据上成立；复用生产 `reveal_path_in_folder` 真实弹出 Explorer 人工核对；补齐 `tests/unit/export/test_export_output_isolation.py` 的 AC-EOI-02 端到端目录内容断言（BLK-EOI-04）。三阶段全部完成 |
| v0.3.0 | 2026-08-07 | Stage 1+2 实施完成（见 §7）：落盘改造 + `longshot-current.json`/PDF/zip 迁移 + 测试重写；额外修复评审未覆盖的书架/首页预览裸目录扫描、分享 zip 下载链接两处真实缺口 |
| v0.2.0 | 2026-08-07 | [七席评审](./acceptance-records/eoi-export-output-isolation-v1-review-2026-08-07.md) **Conditional Go**，回写 BLK-EOI-01～04：①常量 `EXPORT_OUTPUT_DIRNAME` 钉死放 `longshot.py`；②`test_longshot_current.py` 等测试改动规模显式列入 Stage 2 工作量；③承认子目录内残留 `longshot-current.json` 不算违反"只看到产物"目标；④AC-EOI-02 补端到端目录内容断言。用户同日拍板 D-EOI-02（命名「导出文件」）/D-EOI-05（老数据不处理）已在本版落字 |
| v0.1 | 2026-08-07 | 初稿：基于用户反馈"导出文件夹混着工程文件"落笔，核实全部导出类型的落盘点，提出统一子文件夹方案；D-EOI-05/06 待拍板，尚未实施 |
