# M21 回滚速查卡（值班用）

> 适用：M21-a 及之后（`/` 已切到 v2）  
> 目标：在 5 分钟内把用户入口恢复到可用状态。

---

## 1) 何时触发回滚

满足任一条件可触发：

- 导入成功率在短窗内显著下降（相对近期基线）
- 首页出现持续不可用或高错误率
- 上传路径出现系统性失败
- PM/值班明确判定影响核心路径

---

## 2) 一级回滚（配置回滚，最快）

将首页入口切到 classic 应急页：

```bash
set TRAVELOGUE_STUDIO_HOMEPAGE_V2=off
```

在部署环境写入等价配置后重启 Studio 进程。

快速验证：

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8766/
curl -s http://127.0.0.1:8766/ | findstr /C:"data-studio-v=\"4\""
```

期望：

- `/` 返回 200
- `/` 呈现 v3 标记（`data-studio-v="4"`）
- `/classic` 仍可访问

---

## 3) 二级回滚（版本回滚）

当一级回滚无法恢复（例如新代码回归影响共享模块）：

1. 回退到上一稳定发布版本
2. 重启服务
3. 复核首页、导入、预览、长图四条主链路

---

## 4) 回滚后必做验证（10–15 分钟）

- [ ] 首页可打开（`/`）
- [ ] pick-folder 可发起导入
- [ ] 上传入口可见且不报错（若版本包含上传）
- [ ] preview “返回首页”可回到首页
- [ ] `activeJobId` 续跑不丢失

---

## 5) 标准演练（on -> off -> on）

建议每周至少一次，步骤如下：

1. `on` 状态验证（`/` 为 v2）
2. 执行一级回滚到 `off`（`/` 为 v3）
3. 恢复 `on`（`/` 回 v2）
4. 各阶段跑 1 轮核心 smoke：首页、导入、preview 返回

推荐命令（PowerShell）：

```powershell
# 1) on
$env:TRAVELOGUE_STUDIO_HOMEPAGE_V2 = "on"
python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_on_serves_v2_at_root"

# 2) off（应急回滚）
$env:TRAVELOGUE_STUDIO_HOMEPAGE_V2 = "off"
python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_off_serves_v3_at_root"

# 3) on（恢复）
$env:TRAVELOGUE_STUDIO_HOMEPAGE_V2 = "on"
python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_on_serves_v2_at_root or gate_classic_serves_v3"
```

---

## 6) 事件记录模板

| 字段 | 内容 |
|------|------|
| 触发时间 |  |
| 触发人 |  |
| 症状 |  |
| 回滚级别 | 一级 / 二级 |
| 完成时间 |  |
| 恢复结果 |  |
| 后续行动 |  |

---

## 7) 联系人与权限

| 角色 | 姓名 | 联系方式 |
|------|------|----------|
| On-call |  |  |
| 前端负责人 |  |  |
| 后端负责人 |  |  |
| PM |  |  |

