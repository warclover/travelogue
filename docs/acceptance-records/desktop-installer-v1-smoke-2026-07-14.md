# 桌面可安装版 V1 · 工程冒烟记录（ACCEPTANCE §1）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-14 |
| **产物版本** | `0.2.0-beta.1`（FileVersion `0.2.0.1`） |
| **分支** | `feat/desktop-installer-v1` |
| **环境** | Windows 11 · 干净临时目录解压/拷贝 onedir（非源码旁运行） |
| **执行方式** | `python scripts/smoke_studio_portable.py --dist dist/TravelogueStudio` |
| **安装模式附加** | `--mode install --skip-import`（`LOCALAPPDATA` 临时覆盖） |
| **关联** | [ACCEPTANCE-DESKTOP-INSTALLER-V1.md](../ACCEPTANCE-DESKTOP-INSTALLER-V1.md) · [IMPLEMENTATION](../IMPLEMENTATION-DESKTOP-INSTALLER-V1.md) |
| **结论** | **工程冒烟 SM-01～SM-09：PASS**（见下表备注）；可准备约 Gate A，**约人前须填实** `packaging/gate-a/SUPPORT-SOP.md` 反馈入口 |

---

## 1. 便携模式矩阵

| ID | 结果 | 证据 / 备注 |
|----|------|-------------|
| **SM-01** | PASS | onedir 含 exe、`_internal/`、`portable.flag`、`VERSION.txt`、`SHA256SUMS`、`使用说明.txt`、`gate-a/` |
| **SM-02** | PASS | SHA256SUMS 与所列文件一致 |
| **SM-03** | PASS | HTTP 200 · `console=False` · capabilities 可达 |
| **SM-04** | PASS | `./logs/studio.log` 含启动行 |
| **SM-05** | PASS | `POST useDemoAlbum` → trip `demo-album`；冻结子进程导入成功（已补 `collect_data_files(travelogue)`） |
| **SM-06** | PASS | 中文路径相册导入成功（`photoCullEnabled=false` 防 demo 近重复过裁） |
| **SM-07** | PASS* | `forceClient` → `fallback:client`；`longshot/upload` 写入 `smoke-longshot.png`。\*UI html2canvas 全链路仍建议 Gate A 手测一次 |
| **SM-08** | PASS | 二次启动 `second_exit=0`；主实例仍服务 |
| **SM-09** | PASS | `POST /shutdown` 后进程退出、端口释放 |
| **D-INS-10** | PASS | PE FileVersion = `0.2.0.1` |

脚本汇总行：`PASS`（2026-07-14 本机复跑）。

---

## 2. 安装模式（无 portable.flag）

| 检查 | 结果 |
|------|------|
| trips / logs / ownership 落在 `%LOCALAPPDATA%\Travelogue\`（冒烟用临时 LOCALAPPDATA） | PASS |
| SM-03/04/08/09 | PASS |

---

## 3. 本轮补齐项（相对 PRD 缺口）

| 项 | 状态 |
|----|------|
| T-0c-09 启动失败 MessageBox | Done · `travelogue/desktop/startup_feedback.py` |
| D-INS-10 FileVersion | Done · `scripts/gen_studio_version_info.py` |
| 打包漏 `lse_policy.yaml` 等导致导入失败 | Done · spec `collect_data_files("travelogue")` |
| T-A-02 邀请包 | Done · `packaging/gate-a/` |
| F-INS-REL-05 SOP | Done · 占位待填实后约人 |
| T-0c-10 高清组件说明草稿 | Done · P1 |

---

## 4. 手测残留（不挡脚本 PASS，建议 Gate A 前补一眼）

1. 双击 exe：浏览器自动打开首页（脚本用 `--no-open`）。  
2. 预览 UI「保存长图」→ html2canvas → Task Dock「在文件夹中显示」。  
3. 故意制造启动失败时 MessageBox 是否出现（可选）。  
4. `SUPPORT-SOP.md` 中 `TODO_GATE_A_FEEDBACK_CHANNEL` / `TODO_OWNER` 填实。

---

## 5. 出口判定

| 门禁 | 判定 |
|------|------|
| M-INS-0 冒烟出口（SM-01～09） | **PASS · 允许约 Gate A**（填实反馈入口后） |
| Gate A 真人 ≥4/5 | **未执行**（T-A-03/04） |
| 官网公开 CTA | **禁止** |
