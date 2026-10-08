# 第三方技能在 Windows / git-bash 上的移植与验收

上游技能（尤其是 Claude Code / Codex 生态的）默认跑在 macOS + zsh。本机是 Windows + git-bash + PATH 上的 `D:\python\python.exe`。
装完先按下面的表把脚本改到能跑，再交付。

## 症状 → 改法（就地改，不要绕开）

| 上游写法 | 本机后果 | 改法 |
|---|---|---|
| `#!/bin/zsh` | 直接执行报 no such file | 改 `#!/usr/bin/env bash`；调用时也用 `bash <script.sh>` |
| `rsync -a --exclude ... src/ dst/` | git-bash 通常没有 rsync | 先 `if command -v rsync`，没有就 `cp -R src/. dst/` 再 `rm -rf` 掉 node_modules / build* / renders 这类重目录 |
| `sed -i '' 's/a/b/' f` | BSD 语法，GNU sed 不认 | `sed -i '' ... 2>/dev/null \|\| sed -i ...`（先试 BSD，失败退回 GNU） |
| zsh 数组切分 `${(s:,:)VAR}` | bash 语法错误 | `IFS=',' read -r -a ARR <<< "$VAR"` 后 `for x in "${ARR[@]}"` |
| 脚本里 `python3` | git-bash 里等于 PATH 上的 `D:\python\python.exe`（不是 Hermes venv） | 该 python 要装齐脚本依赖：`python -m pip install numpy edge-tts pillow scipy`（tts_build 要 numpy+edge-tts；frame_metrics 要 numpy+Pillow+scipy） |
| `npx` / `npm` / `ffmpeg` | 本机已有（node v24 / npm 11 / ffmpeg 8.1），不用改 | — |

改完把补丁留档，别只改工作区：

```bash
cd <技能目录> && git diff > local/local-patches.patch   # 记录改了哪些上游文件
```

`git pull` 之后若上游覆盖了这些脚本，照 patch 重打，或 `git stash` → `pull` → `git stash pop`。在没有 commit 权限/不想提交的 clone 里，这是最省事的办法。

## 本机 Windows 小坑（写辅助脚本时会撞上）

- **PowerShell `.ps1` 里有中文**：以 UTF-8 无 BOM 写入，Windows PowerShell 5.1 会按 ANSI 解析并报
  "字符串缺少终止符"。要么写成纯 ASCII，要么带 BOM。临时脚本优先纯 ASCII。
- **从 git-bash 启动 GUI 程序**：`cmd //c start "" app.exe` 只会开出一个交互式 cmd 而不启动程序；用
  `python -c "import subprocess; subprocess.Popen([r'<exe>'], creationflags=0x00000008)"`（DETACHED_PROCESS）最可靠。
- **长任务别在前台等**：`npm install`（Remotion 项目 270MB+）、首次渲染（要下 Chrome Headless Shell）动辄几分钟到十几分钟，
  用 `terminal(background=true, notify=true)` 起，期间继续干别的，回来 `process(action='poll')` 收结果。
- 路径给**原生 forward-slash 形式**（`D:/x/y`）给 npm/npx/node 这类原生程序；`/d/x/y` 只对 bash 内建有效。
- **验证命令里不要夹 `rm -rf`**：删缓存目录会触发审批框，用户没点整条命令就被拦下，验证半途停住（还会被判定为“未经同意”）。要重建产物就换新 tag / 新目录隔离，保持全程非破坏性。
- **要启动 GUI 程序做验证，先在回复里说一句**：窗口会在用户桌面上真的弹出来，他会注意到（也会问“你给我打开了？”）；跑完顺手告诉他可以随时关、以及现在跑的是哪个版本。

## 交付前的验收清单

- [ ] `hermes skills list | grep <name>` 能列出该技能（local / enabled）
- [ ] 技能的最小流程真跑过一遍，实测输出（命令 + 关键日志行）写进 `local/本机适配说明.md`
- [ ] 技能 SKILL.md 末尾有一节指向本机说明文件
- [ ] 脚本补丁留了 patch 文件，并写明 `git pull` 后怎么重打
- [ ] 若技能要写文件、占大空间（每项目 GB 级），在工作目录约定里写明放 D 盘
- [ ] 用**中文通俗**给用户交代：这是什么、能干什么、怎么触发、跑一次大概多久、有哪些前置依赖
