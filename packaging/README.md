# Travelogue Studio · Windows 打包（Desktop Installer V1）

## 产物

| 形态 | 路径 | 说明 |
|------|------|------|
| onedir | `dist/TravelogueStudio/` | 主产物（exe + `_internal/`） |
| 便携 zip | `dist/TravelogueStudio-portable-<version>.zip` | Gate A 分发形态 |

版本号单一来源：`packaging/VERSION`（写入产物 `VERSION.txt`）。

## 一键构建

```bat
pip install -e ".[desktop]"
scripts\build-studio-exe.bat
```

脚本会：

1. 生成 Windows FileVersion 资源（`scripts/gen_studio_version_info.py`）
2. 运行 PyInstaller（`packaging/travelogue-studio.spec`）
3. 注入 `portable.flag`、`使用说明.txt`、`VERSION.txt`、`gate-a/` 邀请材料
4. 生成 `SHA256SUMS` 并打 zip

也可只做收尾（已有 onedir 时）：

```bat
python scripts/package_studio_portable.py
```

## 明确不捆绑（excludes）

V1 安装版 **不** 打入：

- `torch` / `torchvision` / `torchaudio`
- `open_clip` / `open_clip_torch`
- `pyiqa`（cull-ml）
- `tensorflow` / `tensorboard` / `jax`
- `playwright`（V1 不捆 Chromium；长图走轨 2）
- `pytest` / IPython / Jupyter（开发噪声）

缺失时相关能力降级，用户文案不得出现 `pip install`（见 ADR-018 / PRD）。

> 说明：本机若已安装 sklearn / scipy / opencv 等，PyInstaller 仍可能因可选 import 图把它们收进 `_internal`（体积膨胀）。后续可在不破坏主路径的前提下继续收紧 excludes；Gate A 不以「最小体积」为硬门槛，但应避免 Torch。

## UPX

默认 **关闭**（降低误报）。勿在未评审情况下打开 `upx=True`。

## 必备 datas（缺则构建失败）

- `templates/**`（含 Studio 静态与 demo-album）
- `schemas/**`
- `docs/experience-matrix.yaml`
- `config/platform_profiles.yaml`
- `config.yaml.example`
- `travelogue` 包内数据（`collect_data_files`：含 `lse_policy.yaml` / layout templates 等）

## 冒烟（干净临时目录）

```bat
python scripts/smoke_studio_portable.py --dist dist\TravelogueStudio
python scripts/smoke_studio_portable.py --dist dist\TravelogueStudio --mode install --skip-import
```

期望：SM-01～SM-09 PASS；安装模式 trips/logs 落在 LocalAppData。记录见 `docs/acceptance-records/desktop-installer-v1-smoke-*.md`。

## 相关文档

- [ADR-018](../docs/adr/018-desktop-installer-layout.md)
- [IMPLEMENTATION-DESKTOP-INSTALLER-V1](../docs/IMPLEMENTATION-DESKTOP-INSTALLER-V1.md)
- [PRD-DESKTOP-INSTALLER-V1](../docs/PRD-DESKTOP-INSTALLER-V1.md)
