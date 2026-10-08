# Blender：安装、版本选择、装后自检（本机实测）

## 本机现状

| 项 | 值 |
|---|---|
| 已装 | `D:\Blender\blender-4.5.10-windows-x64\blender.exe`（4.5.10 LTS，build 2026-05-19，绿色解压版，883MB） |
| 桌面快捷方式 | `Blender 4.5.lnk` |
| 来源包 | `D:\网页下载\blender-4.5.10-windows-x64.zip`（380MB，使用者 8 月自己下的，一直没解压） |
| 备份/其它 | 无。4.5 与 5.x 的配置目录不互通（`%APPDATA%\Blender Foundation\Blender\<版本>\`） |

## 版本线怎么选

- **4.5 = LTS 长期支持版**（最稳，插件兼容期长）；4.5.x 是它的修订线。
- 截至 2026-09 官网稳定版是 **5.2.1**（功能最新）。
- 两个大版本**插件和设置都不互通**，让用户挑一条长期用；要新版就装到另一个目录共存。

## 国内下载（不用挂代理）

```
https://mirrors.tuna.tsinghua.edu.cn/blender/release/            # 镜像根，下面按 Blender<X.Y>/ 分目录
https://mirrors.tuna.tsinghua.edu.cn/blender/release/Blender5.2/blender-5.2.1-windows-x64.msi   # 实测 200
```

- 清华 TUNA、南大 NJU、阿里云都有 `/blender/` 镜像；**USTC 没有这个镜像**，别去试。
- 先用 `curl -s -o /dev/null -w "%{http_code}"` 验一个具体直链再给用户，别只给镜像首页。

## 官方配置要求 vs 本机（i5-10300H / 15.8G / GTX 1650 4G）

| | 官方最低 | 官方推荐 | 本机 |
|---|---|---|---|
| CPU | 4 核（SSE4.2） | 8 核 | 4 核 8 线程 ✓最低 |
| 内存 | 8 GB | 32 GB | 15.8 GB ✓最低 |
| 显卡 | 2 GB 显存，OpenGL 4.3 / Vulkan 1.3（GeForce 900+） | 8 GB 显存 | GTX 1650 4G，OpenGL 4.6 / Vulkan 1.3 ✓最低 |
| 系统 | Win 8.1 64 位 | Win 11 | Win 11 ✓ |
| 硬盘 | 约 1 GB | — | 解压后 883 MB，装 D 盘 |

结论话术：能跑，属于"学习 + 中小项目舒服"；**4 GB 显存是主要瓶颈**（大贴图、复杂几何、粒子/流体多会爆显存），16 GB 内存做流体大场景也不够。不用预先装运行库、不用改系统设置，驱动够新即可。

## 装后自检（三步，都要留证据）

1. **版本**：`"<exe>" --version`（后台模式可跑，退出码 0，输出 `Blender 4.5.10 LTS` + build 日期）
2. **内置 Python**：`"<exe>" -b --python-expr "import bpy,sys;print('PYOK', bpy.app.version_string, sys.version.split()[0])"`
3. **GPU 渲染能力**：跑 `scripts/blender_gpu_check.py`（枚举 CUDA/OptiX 设备 + 渲一张小图）。本机实测：
   认出 `[('CUDA','NVIDIA GeForce GTX 1650',True), ('CPU','i5-10300H',False), ('OPTIX','NVIDIA GeForce GTX 1650',True)]`，160×120 / 16 采样 Cycles GPU 渲染 **1.3 秒**出图。

⚠ **不要在 `-b` 里用 `gpu.platform.*` 验显卡** —— 后台模式没有绘图上下文，必然抛
`SystemError: GPU functions for drawing are not available in background mode`。要证明 GPU 能用，走 Cycles 的设备枚举 + 微渲染这条路。

## 首次打开让用户改的两处（Ctrl+, 打开 Preferences）

- 界面中文：Interface → Translation → Language 选「简体中文」
- 开 GPU 渲染：System → Compute Device 选 CUDA（或 OptiX）→ 勾选显卡；渲染设置里 Device 选 GPU
  （GTX 16 系没有光追核心，OptiX 提速不如 RTX，但比纯 CPU 快得多；两个设备都认）

## 命令速查

```bash
# 后台自检（不弹窗）
"D:/Blender/blender-4.5.10-windows-x64/blender.exe" --version
"D:/Blender/blender-4.5.10-windows-x64/blender.exe" -b --factory-startup --python <脚本.py>
# 解压绿色包（用 python zipfile，别用 unzip -o 一把梭：顺手把自检一起做）
python install_blender.py
```
