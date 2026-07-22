# CSC W1 · 测评三题手测记录（CSC-W1-05）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **日期** | 2026-07-22 |
| **短文** | [csc-w1-happy-path-user-copy.md](./csc-w1-happy-path-user-copy.md) |
| **UI 挂点** | 帮助抽屉 **H0**；设置「导入与分析」→「默认这一趟做什么 →」；`?help=H0` |
| **L1 点击基线** | **≤2**（AC-CSC-13 · W0 钉定） |

---

## 三题协议

| # | 题 | 通过标准 | 结果 | 证据 |
|---|----|----------|------|------|
| **Q1** | 用自己的话解释「默认这一趟」做了什么、没做什么 | ≤3 分钟；无 LSE/MCS/Profile 等黑话（AC-CSC-09） | **Pass（桌面复述）** | 对照短文三节 + H0 四条 bullet；复述可落在「整理行程→挑片排版→预览/长图；不默认确认章节/实验排版/上传云」 |
| **Q2** | 首趟成册是否必须打开 Advanced / 实验选项 | Advanced 默认折叠；不影响主 CTA（AC-CSC-10 / F-CSC-1） | **Pass（代码检视）** | G1 / scoring 在 `#v2-settings-experimental` `<details>`；首页主 CTA 无 admin 链（见 Q3） |
| **Q3** | 首趟路由是否出现 admin | 0 次 `/templates-admin` · `/lse-flags-admin`（AC-CSC-14） | **Pass（静态）** | `studio-home-v2.html` / `homepage-v2/*` 无上述路径；admin 仅独立页 |

---

## 狗粮勾选（实机补签）

在本地 Studio（`python -m travelogue studio`）再跑一遍并勾选：

- [x] 空态/`?help=H0` 能看到 H0「默认这一趟做了什么」  
- [x] 设置 → 导入与分析 →「默认这一趟做什么 →」打开 H0  
- [x] 预览→长图：**未**打开实验选项也能完成（既有 demo 画册）  
- [x] 本测 L1 设置点击次数 = 0（≤2）  
- [x] Network/资源：无 `templates-admin` / `lse-flags-admin` 请求  

完整步骤与命令输出见 [csc-pre-merge-smoke-2026-07-22.md](./csc-pre-merge-smoke-2026-07-22.md)。
