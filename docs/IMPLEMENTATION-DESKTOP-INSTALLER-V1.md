# IMPLEMENTATION · 桌面可安装版 V1（Windows）

| 属性 | 内容 |
|------|------|
| **文档版本** | v1.0.0 |
| **日期** | 2026-07-14 |
| **状态** | **M-INS-0a Done** · 进入 M-INS-0b（路径 / portable / worker） |
| **关联 PRD** | [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md) v1.1.0 |
| **关联 ADR** | [ADR-018](./adr/018-desktop-installer-layout.md) |
| **关联验收** | [ACCEPTANCE-DESKTOP-INSTALLER-V1.md](./ACCEPTANCE-DESKTOP-INSTALLER-V1.md) |
| **工时锚点** | 约 **28–42 人日**（含 Gate A 准备；含 Gate B 安装器；不含证书采购等待） |

---

## 0. 原则

1. **先契约后代码**：ADR-018 与 ACCEPTANCE 已冻结；实施不得静默改门禁阈值。  
2. **只批准 M-INS-0**：未过冒烟不得约 Gate A 用户；未过 Gate A 不得做公开下载。  
3. **干净机为准**：本机源码旁「能跑」不算完成。  
4. **小步合并**：0a → 0b → 0c；每阶段有可演示产物与回滚点。  
5. **文案零 pip**：安装版用户可见路径禁止 `pip install` / 堆栈主文案。

---

## 1. 里程碑总览

```text
M-INS-0a  打包骨架（onedir / windowed / datas / 版本指纹）
    ↓
M-INS-0b  路径与进程（resource_root / user_data / portable / freeze_support / worker）
    ↓
M-INS-0c  产品闭环（长图双轨 / 单实例 / 退出 / 失败反馈）
    ↓
Smoke     ACCEPTANCE §1 干净机冒烟
    ↓
Gate A    5 人定向 ≥4 完成
    ↓
M-INS-1   Inno Setup + 卸载安全 + 升级
    ↓
Gate B    N≥15 邀请制量化门禁
    ↓
M-INS-2   签名 + Release + 官网 CTA
    ↓
Gate C    公开下载
```

| 里程碑 | 人日（估） | 退出条件 |
|--------|------------|----------|
| **M-INS-0a** | 3–5 | onedir 产物可启动；有 VERSION/SHA256；console=False |
| **M-INS-0b** | 8–12 | 干净目录无源码可 HTTP 200；导入路径不依赖 `paths.ROOT`；worker/freeze_support 通过 |
| **M-INS-0c** | 6–10 | 无 PW 可出 PNG；单实例+退出；无 pip 文案 |
| **Smoke + Gate A 准备** | 3–5 | SM-01～09 PASS；说明文案与邀请材料就绪 |
| **M-INS-1（Gate B）** | 6–8 | Setup 安装/卸载/升级 AC 通过 |
| **M-INS-2（Gate C）** | 2–4 + 证书前置 | 签名 Release + 官网 CTA |

---

## 2. M-INS-0a · 打包骨架

### 2.1 目标

把现有 `packaging/travelogue-studio.spec` 从 **onefile + console** 改为 **onedir + windowed**，并固定 datas / 排除清单 / 版本指纹。

### 2.2 任务拆解

| 任务 ID | 内容 | 主要文件 | 依赖 |
|---------|------|----------|------|
| **T-0a-01** | spec 改为 onedir；`console=False`；关闭 UPX | `packaging/travelogue-studio.spec` | — |
| **T-0a-02** | 显式 datas：templates、schemas、studio 静态、demo-album、`platform_profiles.yaml`、`config.yaml.example`、experience-matrix 等；缺则 fail | 同上 + 构建脚本 | ADR D1 |
| **T-0a-03** | excludes：Torch / open-clip / cull-ml 等；维护依赖清单文档片段 | spec + `packaging/README` 或脚本注释 | F-INS-PACK-04/11 |
| **T-0a-04** | 构建脚本一键产出；写入 `VERSION.txt`（`0.2.0-beta.N`）与 `SHA256SUMS` | `scripts/build-studio-exe.bat`（或后继） | F-INS-PACK-07/08 |
| **T-0a-05** | 打包后注入/拷贝 `portable.flag` 与 `使用说明.txt` 到 zip 根 | 构建脚本 + `packaging/portable.flag` + 说明文案 | ADR D3 |
| **T-0a-06** | launcher 启动即挂文件日志（即便携临时路径），保证 windowed 下可诊断 | `travelogue/desktop/launcher.py` | F-INS-UX-01 |

### 2.3 完成定义（DoD）

- [x] spec / 脚本 / sidecar 文案已改（onedir · `console=False` · UPX off · datas fail-loud）  
- [x] 构建产出 `dist/TravelogueStudio/` onedir（`0.2.0-beta.1` · 本机已验证）  
- [x] 双击无黑窗；本机冒烟 HTTP **200**（路径深债留给 0b）  
- [x] `VERSION.txt` / `SHA256SUMS` / `portable.flag` / `使用说明.txt` 由 `package_studio_portable.py` 注入  
- [x] 构建脚本可重复调用（`build-studio-exe.bat`）  
- [x] launcher 启动创建 `logs/studio.log`（已修 root WARNING 过滤 INFO）  

### 2.4 回滚

恢复旧 spec / 脚本；不删除旧 onefile 文档说明直至 0b 稳定。

### 2.5 本阶段落地文件（2026-07-14）

| 文件 | 变更 |
|------|------|
| `packaging/travelogue-studio.spec` | onedir + windowed + UPX off + excludes + P0 datas 校验 |
| `packaging/VERSION` | `0.2.0-beta.1` |
| `packaging/portable.flag` · `packaging/使用说明.txt` · `packaging/README.md` | 便携 sidecar |
| `scripts/build-studio-exe.bat` · `scripts/package_studio_portable.py` | 一键构建 + zip |
| `travelogue/desktop/launcher.py` | 启动即挂 `logs/studio.log`（windowed stdout 重定向） |

---

## 3. M-INS-0b · 路径与进程收口

### 3.1 目标

干净机、无源码树：Studio HTTP 200；导入/选文件夹不崩；用户数据落在正确根。

### 3.2 任务拆解

| 任务 ID | 内容 | 主要文件 | 验收挂钩 |
|---------|------|----------|----------|
| **T-0b-01** | 实现/统一 `resource_root()` / `bundle_root()` / `user_data_dir()` / `exe_dir()` / 便携判定（仅 `portable.flag`） | `travelogue/paths.py` 或 `travelogue/desktop/runtime_paths.py` | A06 · ADR D2/D3 |
| **T-0b-02** | 审计并替换捆绑资源读取点：禁止新增裸 `paths.ROOT`；修存量 P0 | 全库 grep `paths.ROOT` / 模板加载 | F-INS-PATH-01/06 |
| **T-0b-03** | `default_trips_dir`：安装模式 → LocalAppData；便携 → exe 旁 `trips/` | paths + config 引导 | PATH-02 |
| **T-0b-04** | 首启从 example 生成用户 `config.yaml`；写 ownership marker | launcher / config bootstrap | PATH-03 · B03 |
| **T-0b-05** | 日志目录：安装 → `%LOCALAPPDATA%\Travelogue\logs\`；便携 → `./logs/` | logging 初始化 | PATH-04 |
| **T-0b-06** | `multiprocessing.freeze_support()` 进入 launcher/`__main__` | desktop launcher · 导入入口 | PATH-07 · A10 |
| **T-0b-07** | 选文件夹 worker：argv 子命令或同包可执行入口；去掉脆弱的 `-m` 唯一路径 | `pick_folder_worker` · launcher | A10 · ADR D5 |
| **T-0b-08** | 干净目录冒烟脚本（解压到 temp、启服、curl 首页、杀进程） | `scripts/smoke-studio-portable.*` | PATH-05 · SM-* |

### 3.3 完成定义（DoD）

- [ ] 无源码干净目录：启动 + 首页 200  
- [ ] 中文路径选文件夹成功  
- [ ] 便携模式 trips/logs 在 exe 旁  
- [ ] （开发态）不设 portable.flag 时行为与开发约定兼容，不破坏日常 CLI  

### 3.4 回滚

用 feature flag / 环境变量临时回退到「开发态 ROOT」；不得带着半收口路径进 Gate A。

---

## 4. M-INS-0c · 长图双轨 · 单实例 · 退出

### 4.1 目标

无 Playwright 机器上完成产品成功定义；进程生命周期可预期。

### 4.2 任务拆解

| 任务 ID | 内容 | 主要文件 | 验收挂钩 |
|---------|------|----------|----------|
| **T-0c-01** | Studio：Playwright 不可用时**自动**启用客户端 html2canvas；不因 preview-toolbar 屏蔽 | Studio 前端 + longshot API 契约 | A05 · ADR D6 |
| **T-0c-02** | `E_LNG_PLAYWRIGHT` 非终态；触发轨 2；轨 2 失败才中文终态 | 错误码映射 · UI 文案 | D-INS-05 |
| **T-0c-03** | 轨 2 回传写入 trip 输出目录（D-INS-09）；失败才浏览器下载兜底 | Studio API + 前端 upload | A05 |
| **T-0c-04** | Task Dock / 发群三要素 /「在文件夹中显示」与轨 1 对齐 | Studio UI | A05/A07 |
| **T-0c-05** | 清除安装版 pip 文案（导入、长图、依赖缺失） | 文案表 / i18n / 错误模板 | A11 |
| **T-0c-06** | 命名 mutex + 端口状态文件；二次启动打开已有 URL | launcher | A09 · ADR D4 |
| **T-0c-07** | 端口占用策略：复用或有限重试下一端口 | launcher · serve | UX-03 |
| **T-0c-08** | 产品内「退出 Studio」：停 HTTP/Job、刷日志、释端口/mutex | Studio UI + shutdown API/信号 | A08 |
| **T-0c-09** | windowed 启动失败：写日志 + 可选本地 HTML/MessageBox 指向日志 | launcher | SM-04 |
| **T-0c-10** | （P1）帮助中「安装高清长图组件」说明草稿 | 帮助文案 | D-INS-04 |

### 4.3 轨 2 技术冻结（实施时写入代码注释/配置）

| 项 | V1 冻结建议 | 备注 |
|----|-------------|------|
| 最大画布高度 | 与现有 html2canvas / 平台切片策略对齐；超限分段 | 实施时对照现网常量，禁止静默改产品语义 |
| 内存失败 | 降分辨率或减段重试一次 → 仍失败则中文结论 | NF-INS-03 |
| 文件名 | 与轨 1 同一命名函数 | D-INS-09 |
| 回传 | `POST` 到本机 Studio，写入 trip 输出目录 | 需 CSRF/本机 origin 既有策略 |

### 4.4 完成定义（DoD）

- [ ] 干净机无 PW：A05 工程自测 PASS  
- [ ] 单实例 + 退出自测 PASS  
- [ ] 全文案扫描：安装相关路径无 `pip install`  

---

## 5. Smoke → Gate A

| 任务 ID | 内容 |
|---------|------|
| **T-A-01** | 执行 ACCEPTANCE §1；填写 `docs/acceptance-records/desktop-installer-v1-smoke-*.md` |
| **T-A-02** | 准备 5 人邀请包：zip + 半页说明 + 反馈表（含版本/OS/是否完成找文件） |
| **T-A-03** | 指定环境覆盖：Win10、Win11、中文路径、至少一台真干净机 |
| **T-A-04** | Gate A 结束后写验收记录；≥4 完成才开 M-INS-1 |

**禁止**：冒烟未过约用户；Gate A 未过上官网下载按钮。

---

## 6. M-INS-1 · 安装包（Gate B）

| 任务 ID | 内容 | 主要产物 |
|---------|------|----------|
| **T-1-01** | Inno Setup 脚本：每用户目录、开始菜单、可选桌面快捷方式 | `packaging/inno/TravelogueStudio.iss` |
| **T-1-02** | 冻结 AppId / Publisher / 版本映射 `0.2.0.N` | iss + 版本源 |
| **T-1-03** | 卸载保留数据；勾选删除 → 路径展示 + 二次确认 + ownership marker | iss + 可选 helper |
| **T-1-04** | 运行中检测：提示退出（F-INS-UX-06） | iss / 安装前检查 |
| **T-1-05** | 覆盖升级保留 LocalAppData 用户树 | 手工 AC-B07 |
| **T-1-06** | 构建流水线：同一 onedir → Setup + Portable 双产物 | CI/脚本 |
| **T-1-07** | Gate B 邀请制投放与指标统计表 | 运营表 + 验收记录 |

---

## 7. M-INS-2 · 签名与公开（Gate C）

| 任务 ID | 内容 |
|---------|------|
| **T-2-01** | 代码签名证书就位；签署 Setup 与关键 exe |
| **T-2-02** | GitHub Release（或选定渠道）上传 Setup + zip + VERSION + SHA256SUMS |
| **T-2-03** | 官网 `/install` 主 CTA「立即下载」仅此时打开 |
| **T-2-04** | 许可/定价文案与 README 对齐（消除 MIT/待定冲突） |
| **T-2-05** | 误报/失败反馈入口与日志指引 |

---

## 8. 风险与依赖

| 风险 | 缓解 |
|------|------|
| frozen worker 选文件夹仍失败 | 0b 提前真机；备选：tkinter 同进程（体验差）仅作紧急兜底并记债 |
| html2canvas 大长图 OOM | 分段 + 文案；不把轨 1 当唯一路径 |
| SmartScreen 阻断 | Gate B 收集证据；Gate C 签名；临时侧载说明 |
| 路径漏改导致「本机能跑」 | 强制干净目录 smoke 脚本进 DoD |
| 许可文案冲突 | Gate C 前法务/产品书面冻结 |

---

## 9. 建议编码顺序（下一会话直接开干）

1. **先做 T-0a-01～06**（改 spec + 构建脚本 + 基础日志）  
2. 再 **T-0b-01～08**（路径与 worker）  
3. 再 **T-0c-01～09**（长图与生命周期）  
4. 跑 **T-A-01** 冒烟；通过后再约人  

当前状态：**M-INS-0a 完成**；下一会话从 **T-0b-01**（`resource_root` / `user_data_dir` / `portable.flag`）开始。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-07-14 | 首版：0a/0b/0c → Gate A/B/C 任务拆解与 DoD |
