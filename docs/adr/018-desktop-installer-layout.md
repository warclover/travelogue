# ADR-018 · 桌面可安装版布局、数据目录、进程与长图双轨

| 属性 | 内容 |
|------|------|
| **状态** | **Accepted**（PRD v1.1.0 Conditional Go · 2026-07-14） |
| **日期** | 2026-07-14 |
| **决策者** | 产品 + 架构 + Windows 桌面工程 |
| **关联 PRD** | [PRD-DESKTOP-INSTALLER-V1.md](../PRD-DESKTOP-INSTALLER-V1.md) v1.1.0 |
| **关联实施** | [IMPLEMENTATION-DESKTOP-INSTALLER-V1.md](../IMPLEMENTATION-DESKTOP-INSTALLER-V1.md) · [ACCEPTANCE-DESKTOP-INSTALLER-V1.md](../ACCEPTANCE-DESKTOP-INSTALLER-V1.md) |
| **补充/修订** | [ADR-004](./004-studio-hub-server.md)（Studio 单进程）· [ADR-005](./005-longshot-server-side.md)（安装版 P2 升为自动轨 2）· [ADR-008](./008-trip-storage-boundaries.md)（用户数据目录） |
| **不取代** | ADR-005 服务端 P0/P1 捕获顺序；本 ADR 仅定义**安装版**在 Playwright 不可用时的产品主路径 |

---

## 背景

1. Phase 2 M11 交付了 PyInstaller 骨架（onefile · `console=True` · exe 旁 trips），不能称为可分发产品。
2. PRD-DESKTOP-INSTALLER-V1 跨职能评审（2026-07-14）结论为 **Conditional Go**：批准 M-INS-0，不批准 Gate A 外发，直至路径/子进程/长图双轨/退出生命周期闭合。
3. 现有实现与 PRD 在五处系统性不一致：onedir、`bundle_root` 收口、LocalAppData、Studio 长图自动降级、端口/单实例/退出。
4. 若不先冻结架构契约，实施期极易在「碰巧能跑」与「干净机可验收」之间反复返工。

---

## 决策

### D1 · 主产物 = PyInstaller onedir

| 项 | 决定 |
|----|------|
| 形态 | **onedir**（`TravelogueStudio/` + `_internal/`）；**不做** onefile 主产物 |
| 入口 | `TravelogueStudio.exe` → `travelogue.desktop.launcher:main` |
| console | `console=False`；stdout/stderr → 文件日志 |
| UPX | 默认 **关闭**；若重新开启须单独评审误报风险 |
| 排除 | 默认不捆 Torch / open-clip / cull-ml / Chromium |
| 必备 datas | `templates/**` · `schemas/**` · Studio 静态资源 · demo-album · `config/platform_profiles.yaml` · `config.yaml.example` · experience-matrix 等运行时策略文件；缺 P0 资源则构建失败 |

便携 zip 与 Inno Setup 均基于**同一** onedir 目录树。

### D2 · 资源根 vs 用户数据根分离

| 根 | frozen 含义 | 开发态含义 |
|----|-------------|------------|
| **`resource_root()` / `bundle_root()`** | `_MEIPASS`（只读捆绑资源） | 仓库根 / 包内资源 |
| **`user_data_dir()`** | 见 D3 | 默认 `ROOT/trips` 的父策略由 config 决定，但 API 形状与安装版一致 |
| **`exe_dir()`** | exe 所在目录（便携旁路、日志旁路） | 一般不使用 |

**契约**：

1. 凡读取模板、schema、Studio 静态、experience-matrix、platform_profiles 等**捆绑资源**，必须经 `resource_root()` / `bundle_root()`。
2. 生产代码**禁止新增**裸 `paths.ROOT` 读取捆绑资源；存量债务在 M-INS-0b 收口。
3. 用户 trips、config、logs、cache **禁止**写入 `_MEIPASS`。

### D3 · 安装模式与便携模式

#### 安装模式（默认 · Gate B）

```text
%LOCALAPPDATA%\Programs\Travelogue\     # 程序（卸载可删）
%LOCALAPPDATA%\Travelogue\
  ├── .travelogue-ownership              # ownership marker（卸载安全删除门禁）
  ├── trips\
  ├── config.yaml
  ├── logs\
  └── cache\
```

#### 便携模式（Gate A 主形态）

判定：**仅**当 exe 同级存在 `portable.flag`（固定文件名，大小写不敏感）时进入便携模式。

```text
<解压目录>\
  ├── TravelogueStudio.exe
  ├── portable.flag
  ├── _internal\ …
  ├── trips\
  ├── config.yaml
  ├── logs\
  └── 使用说明.txt
```

| 规则 | 决定 |
|------|------|
| 环境变量 `TRAVELOGUE_USER_DATA` / `TRAVELOGUE_TRIPS_DIR` | 仅覆盖路径；**不**改变便携/安装模式判定；**不**扩大卸载删除范围 |
| 首启配置 | 从捆绑 `config.yaml.example` 拷贝到用户配置路径；用户无需手改 yaml |
| V1 互转 | **不做**安装版 ↔ 便携版自动互转（OQ-INS-05 已关闭） |

### D4 · 进程模型：单实例 + 端口 + 退出

继承 ADR-004：Studio = 单进程 `serve --studio`，默认 `127.0.0.1`，安装版禁止默认 `--allow-lan`。

| 能力 | 决定 |
|------|------|
| 单实例 | Windows 命名 mutex（建议名 `Local\TravelogueStudio`）+ 端口状态文件（写在 `user_data_dir`） |
| 第二次启动 | 打开已有实例 URL；**不**启动第二套写进程 |
| 端口占用 | 优先复用已有实例；否则尝试下一端口（有限次数），失败则中文失败页 + 日志路径 |
| 退出 | 产品内可发现「退出 Studio」；停止 HTTP/Job、刷新日志、释放端口与 mutex |
| 升级/卸载 | 检测到运行实例时提示并安全退出后再继续；禁止静默覆盖运行文件 |
| 托盘 | Gate A **不做**；Gate B 视反馈（OQ-INS-02） |

### D5 · Frozen 子进程契约

| 路径 | 决定 |
|------|------|
| `multiprocessing` spawn（导入管线） | launcher / `__main__` 必须调用 `freeze_support()`；onedir 干净机必须通过 |
| 选文件夹 worker | **禁止**依赖源码式 `sys.executable -m travelogue.desktop.pick_folder_worker` 作为唯一方案 |
| 推荐实现 | launcher 识别专用 argv（如 `--pick-folder-worker`）进入 worker；或独立 worker 入口在同一 onedir 内可执行 |
| 失败文案 | 安装版不得出现 `pip install`；中文说明 + 日志路径 |

### D6 · 安装版长图双轨（修订 ADR-005 安装附录）

| 轨 | 条件 | 行为 |
|----|------|------|
| **轨 1** | 检测到可用 Playwright Chromium | 服务端 longshot（ADR-005 P0/P1） |
| **轨 2** | Playwright 缺失或启动失败 | **自动**切 html2canvas；用户无需二次选择；文案不提 pip |

**安装版产品合同（对 ADR-005 P2 的加强）**：

1. Studio 预览工具栏不得因 `data-preview-toolbar=on` 屏蔽客户端捕获。
2. `E_LNG_PLAYWRIGHT` **不是**终态错误；应触发轨 2。仅轨 2 也失败时才显示中文失败结论与重试/反馈。
3. 轨 2 产物**优先回传 Studio 写入 trip 输出目录**（D-INS-09）；浏览器直接下载仅作回传失败兜底。
4. 成功态必须保持：文件名/分段元数据一致、Task Dock「长图已保存」、发群三要素、「在文件夹中显示」。
5. 轨 2 质量可能低于轨 1；UI 可用一次人话提示「已使用兼容模式」，不得恐吓用户。

### D7 · 版本与发布身份

| 项 | 决定 |
|----|------|
| 产品版本 | `0.2.0-beta.N` |
| Git tag | `v0.2.0-beta.N` |
| Windows FileVersion | `0.2.0.N` |
| 单一版本源 | Portable / Setup / `VERSION.txt` / Release / 安装器属性共用 |
| pyproject `0.1.0` | 可暂不跟安装版同步；禁止混用 `0.2.0-ins.N` |
| Inno AppId / Publisher | Gate B 前冻结；许可未定前不得公开 Release |

### D8 · 卸载与安全删除

1. 默认保留 `%LOCALAPPDATA%\Travelogue\`（trips / config / logs / cache）。
2. 勾选删除时：显示绝对路径 + 二次确认。
3. 只删除存在 `.travelogue-ownership` marker 的默认用户目录。
4. 不跟随 junction/symlink；不删除环境变量指向的外部目录。
5. 便携包：删除解压目录即卸载。

---

## 后果

### 正面

- Gate A 可用干净机验收，避免「本机碰巧能跑」。
- 安装版与开发版共享编排内核，不引入新桌面壳。
- 长图在无 Chromium 机器上仍可完成产品成功定义。
- 卸载与数据边界可审计，降低误删风险。

### 代价 / 风险

- M-INS-0b/0c 工期长于原 PRD 估计（见 IMPLEMENTATION）。
- html2canvas 质量与体积弱于 Playwright，需文案管理预期。
- frozen worker 与 windowed 日志是 Windows 特有坑，必须有冒烟脚本与真机矩阵。

### 明确不做（V1）

- Tauri / Electron 重写、自动更新、Microsoft Store、macOS/Linux 首版并行。
- 捆绑完整 Chromium / Torch 重量依赖。
- 安装版默认公网暴露 Studio。

---

## 实施顺序（与 PRD §12 对齐）

1. **M-INS-0a**：onedir · console=False · 日志基础 · datas/VERSION/SHA256  
2. **M-INS-0b**：resource_root 收口 · user_data/portable · freeze_support/worker · 干净目录 HTTP 200  
3. **M-INS-0c**：长图自动降级 · 去 pip 文案 · 端口/单实例/退出 · windowed 失败反馈  
4. 冒烟通过后进入 Gate A（5 人定向，≥4 完成）

---

## 验收挂钩

| 决策 | 主要 AC |
|------|---------|
| D1 | AC-INS-A01/A02/A06 · NF01/NF02 |
| D2/D3 | AC-INS-A06 · B03/B07/B10 |
| D4 | AC-INS-A08/A09 · B08 |
| D5 | AC-INS-A04/A10 |
| D6 | AC-INS-A05 |
| D7 | AC-INS-B06 · C01/C04 |
| D8 | AC-INS-B04/B05/B07 |

完整步骤见 [ACCEPTANCE-DESKTOP-INSTALLER-V1.md](../ACCEPTANCE-DESKTOP-INSTALLER-V1.md)。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-14 | 首版 Accepted：固化 onedir、资源/数据根、portable.flag、单实例退出、frozen worker、安装版长图自动轨 2 |
