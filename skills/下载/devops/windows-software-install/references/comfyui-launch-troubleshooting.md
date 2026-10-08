# ComfyUI 打不开排查实录（2026-09，使用者机器）

## 机器环境
- i5-10300H / 16G RAM / GTX 1650 4GB（ComfyUI 识别为 NORMAL_VRAM 模式，可跑 SD1.5，出图慢）
- ComfyUI 位置: `D:\新建文件夹\comfyui`（git clone Comfy-Org/ComfyUI，0.34.0，2026-09-01 克隆）
- 启动器: `D:\新建文件夹\comfyui\启动_ComfyUI.bat`（chcp 65001 + venv activate + python main.py + pause）
- venv: `D:\新建文件夹\comfyui\venv`（Python 3.13.5，torch 2.13.0+cu126 / torchvision / torchaudio 都在）

## 症状
- 用户找不到打开方式（桌面无快捷方式，只有 ComfyUI 教程 docx）
- 浏览器打不开 http://127.0.0.1:8188 —— **根本原因是服务根本没在跑**

## 排查顺序（本次实证有效）
1. 端口探测: `curl -s http://127.0.0.1:8188/system_stats` → 无响应；8187/8188/8189/8190 全试（ComfyUI 端口被占会自动 +1）
2. 找安装位置: `find /d -maxdepth 3 -iname "*comfyui*"`；桌面 `*.lnk`
3. 找启动器: 项目目录 `ls *.bat` → 启动_ComfyUI.bat；`cat` 看内容确认启动方式（venv + main.py）
4. venv 完整性（只读检查，不急着跑）:
   - `cat venv/pyvenv.cfg` → home 指向 `C:\Users\使用者\AppData\Local\Programs\Python\Python313`（存在 = venv 有效）
   - `ls venv/Scripts/python.exe` 存在
   - site-packages 有 torch-2.13.0+cu126 → 依赖在
5. 后台启动验证: `terminal(background=true)` 跑 `cd /d/新建文件夹/comfyui && ./venv/Scripts/python.exe main.py > /tmp/comfy_start.log 2>&1`

## 首次启动慢（大坑）
新版 ComfyUI (0.34.0) 启动要经历：
- alembic 数据库插件加载（日志停在 "setup plugin alembic.autogenerate.*" 很久）
- comfy_kitchen 后端探测（eager 可用 / triton 缺模块 / hip 缺 / cuda disabled）
- 前端资源 + 模型目录扫描

实测从启动到日志出现 "To see the GUI go to: http://127.0.0.1:8188" 约 1.5~2 分钟。
**判断是否卡死看内存不看日志**：`tasklist | grep python` 观察主进程内存是否持续增长
（本次 551MB → 795MB → 970MB = 在加载，别 kill）。Python stdout 重定向到文件有缓冲，tail 不实时更新属正常。

## 建桌面快捷方式（用户找不到入口的解法）
git-bash 里跑 PowerShell（中文路径 OK，注意 `$` 要转义 `\$`）：
```bash
powershell.exe -NoProfile -Command "\$ws = New-Object -ComObject WScript.Shell; \$sc = \$ws.CreateShortcut('C:\Users\使用者\Desktop\ComfyUI.lnk'); \$sc.TargetPath = 'D:\新建文件夹\comfyui\启动_ComfyUI.bat'; \$sc.WorkingDirectory = 'D:\新建文件夹\comfyui'; \$sc.IconLocation = 'D:\新建文件夹\comfyui\启动_ComfyUI.bat,0'; \$sc.Save(); Write-Output 'done'"
```
输出乱码是 MSYS 编码映射问题（chcp），实际已成功。验证: `ls "/c/Users/使用者/Desktop/ComfyUI.lnk"`。

## 启动成功标志
- 日志出现: `[INFO] To see the GUI go to: http://127.0.0.1:8188`
- `curl http://127.0.0.1:8188/system_stats` 返回 JSON（comfyui_version: 0.34.0, required_frontend_version）

## 坑：模型目录空
`models/checkpoints/` 只有 `put_checkpoints_here` 占位文件 → **界面能打开但模型下拉为空，出不了图**。
找模型: `find models -iname "*.safetensors" -o -iname "*.ckpt"`。GTX 1650 4GB 建议放 SD1.5 (~4GB) 模型。
注意 `extra_model_paths.yaml` 不存在 = 模型没有外挂到别的盘。

## 其它观察
- 日志 WARNING: "If you are on nvidia 20 series and above it is required that you update your pytorch to cu130 or higher" —— **1650 是 16 系列，此警告可忽略**；20 系及以上才需要 cu130 的 pytorch。
- 用户可能拒绝 agent 直接跑 venv 里的 python 命令（本会话拒绝过一次 `-c "import torch"` 内联检查）——先做只读检查（ls/cat/curl），要跑服务前先说明意图；被 BLOCKED 的命令**不换法重试**，停下问用户。
