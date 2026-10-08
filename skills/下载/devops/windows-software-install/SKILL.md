---
name: windows-software-install
description: "Step-by-step Chinese-language guides for installing AND removing Windows software — tracing bundled/adware origins, .lnk analysis, finding install directories, identifying bundling sources (360 software管家, etc.). Handles English-only installers, Chinese user guidance, D: drive preference, and installer UI variations."
version: 1.2.0
author: Agent
metadata:
  triggers:
    - "安装"
    - "装"
    - "install"
    - "gh"
    - "GitHub CLI"
    - "登录 GitHub"
    - "下载并安装"
    - "installer"
    - "setup"
    - "怎么装"
    - "怎么安装"
    - "打不开"
    - "启动不了"
    - "找不到打开方式"
    - "卸载"
    - "删除"
    - "删掉"
    - "清除"
    - "捆绑"
    - "捆绑软件"
    - "adware"
    - "流氓软件"
    - "垃圾软件"
    - "360"
    - "安全卫士"
    - "全家桶"
    - "卸载360"
    - "清除干净"
platforms: [windows]
---

# Windows 软件安装 & 卸载指南 (中文)

这个 Skill 用于指导中文用户安装或卸载 Windows 下的软件。涵盖安装指引和追踪捆绑软件来源、分析快捷方式、查找安装目录、识别捆绑源（如 360 软件管家/游戏大厅）。

## 用户偏好（记录在 memory 中，此技能只记流程）

- 所有安装必须选 **D 盘**，不能装到 C 盘
- 用户看不懂英文，**每一步都要用中文说明"当前页面是什么、该点什么"**
- 用户需要知道每个按钮的中文意思，比如 "Next = 下一步", "Browse = 浏览"

## 通用流程

### 第一步：下载安装包

优先用浏览器下载，URL 可以直接给用户复制：

```
请打开浏览器，访问这个链接：
https://xxx

页面会自动下载安装包，等它下完。
```

如果 agent 环境有 curl/wget 且 git-bash 已装好，可以尝试终端下载到 D 盘：
```bash
curl -L -o /d/Downloads/installer.exe "https://..."
```

**⚠️ 大文件下载铁律（2026.8 实测教训）：**
- 先查文件大小：几百 MB 的安装包（如 Obsidian 311MB）**绝不要前台 curl 等它下完**——网速慢时会阻塞终端直到超时（600s），用户看着就像"卡死了"
- 正确做法：
  - 先 `curl -sIL` 看 Content-Length 估大小，<50MB 才考虑前台下载
  - 大文件必须 `terminal(background=true, notify_on_complete=true)` 后台下载，或直接引导用户浏览器下载（技能原文就是"优先用浏览器下载"）
- GitHub release 在国内直连可能只有几十 KB/s（实测 33KB/s，311MB 要 2.5 小时）——先测速，太慢就换镜像站/加速链接
- 下载中断留下的半截文件（如 25MB/311MB）要么清理要么明确告知用户，别默默留垃圾

### 第二步：逐步安装指引

**每页都用编号 + 中文说明的方式呈现：**

```
| 步骤 | 页面 | 操作 |
|------|------|------|
| ①   | Welcome（欢迎） | 点 Next（下一步） |
| ②   | 选路径          | 点 Browse（浏览）→ 选 D 盘 → 新建文件夹名 xxx → 确定 → Next |
| ③   | Select Components | 默认不动 → Next |
| ...  | ...             | ... |
```

**关键原则：**
- 每一页都要说清楚"默认不动"还是"改什么"
- 如果用户反馈看到的选项跟预期不一样，**不要假设用户看错了**——不同版本确实可能有不同 UI，让用户描述他看到的选项
- 对于不熟悉的页面，用选择题确认："你看到的是 A. xxx 还是 B. xxx？"

### 第三步：安装完成

```
装完记得勾选 "Launch xxx" 然后点 Finish（完成）
```

### 第四步：验证

```
装完打开 xxx，输入 xxxx，看看有没有显示版本号
```

### 第五步：查找 bash.exe 路径（Hermes Agent 需要）

装完 Git Bash 后，如果 agent 的 terminal 工具报错 `Git Bash not found`，需要配置路径。找到路径的方法：

**方法 1（推荐）：** 在 Git Bash 中运行：
```bash
cygpath -w /usr/bin/bash
```
这会输出类似 `D:\Git\usr\bin\bash.exe` 的 Windows 路径。

**方法 2：** 在 Git Bash 中运行：
```bash
cygpath -w /
```
确认 Git 安装根目录（如 `D:\Git\`）。

**方法 3：** 让用户在开始菜单搜 "Git Bash" → 右键属性 → 看"目标"路径。

**方法 4（用户自发方式）：** 用户可能直接拖拽文件到聊天窗口附件，这也会暴露真实路径。

找到 `bash.exe` 的 Windows 路径后，告诉 agent，agent 会指导配置到 config.yaml 中。

### 第六步：配置 Hermes Agent（config.yaml）

用记事本打开 `C:\Users\用户名\AppData\Local\hermes\config.yaml`，在文件末尾另起一行添加（注意格式——**行首两个空格，冒号后一个空格**）：

```yaml
  git_bash_path: D:\Git\usr\bin\bash.exe
```

保存后告诉 agent 验证。

**注意：** 添加后 agent 的 terminal 工具可能需要等待整个会话重启或 agent 进程重启才能生效。如果添加后仍报错，可能需要关闭当前 Hermes 会话重新打开。

## 常见软件安装要点

### Git for Windows

- **下载地址：** https://git-scm.com/download/win（自动识别系统）
- **安装路径：** `D:\Git`
- **注意页面：**
  - Select Components（选择组件）— 默认不动
  - Choosing the default editor — 默认不动（Vim 没问题）
  - Adjusting your PATH environment — 可能出现不同选项，让用户描述看到的选项。目标是让 git 能在命令行被找到。
  - Choosing HTTPS transport backend — 选 OpenSSL（默认）
  - Configuring line ending conversions — 选第一个（默认）
  - Configuring terminal emulator — 选 Use MinTTY（默认）
  - Choose the default behavior of `git pull` — 选 Default（默认）
  - Choose a credential helper — 选 Git Credential Manager Core（默认）
  - 之后一路 Next 直到 Install
- **UI 版本差异：** 不同版本（2.47 vs 2.48 vs 2.49）的页面数量和选项可能不同，不要让用户困惑，让用户描述他看到的

### Node.js（zip 便携版安装）

当 MSI 安装包损坏/下载不完整时，可用 zip 版替代（便携安装，无需管理员权限）：

**适用场景：** MSI 安装包报错 1619（损坏/不完整）、用户想完全控制安装位置

**步骤：**

1. **下载 zip 包**（约 36MB，比 MSI 小）：
   - 官网下载：https://nodejs.org（选 **Windows Binary (.zip)**）
   - 或用 curl 下载：`curl -L -o /d/网页下载/node-vXX.XX.X-win-x64.zip "https://nodejs.org/dist/vXX.XX.X/node-vXX.XX.X-win-x64.zip"`

2. **解压到目标目录**（如 D:\Nodejs）：
   ```
   unzip -o "/d/网页下载/node-vXX.XX.X-win-x64.zip" -d /d/Nodejs_temp
   rm -rf /d/Nodejs && mv /d/Nodejs_temp/node-vXX.XX.X-win-x64 /d/Nodejs
   ```

3. **验证安装**：
   ```
   /d/Nodejs/node.exe --version
   /d/Nodejs/npx --version
   ```

4. **添加用户环境变量 PATH（让全局可用）**：
   写一个纯英文 PowerShell 脚本（避免中文编码问题），用桌面临时 ps1 文件执行：
   ```
   $nodePath = "D:\Nodejs"
   $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
   if ($currentPath.Split(";") -contains $nodePath) {
       Write-Output "Already in PATH"
   } else {
       $newPath = $nodePath + ";" + $currentPath
       [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
       Write-Output "Added to user PATH"
   }
   ```
   然后用 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\用户名\Desktop\addpath.ps1"` 执行。

5. **当前会话使用（如需要立即跑 npx）**：
   ```
   export PATH="/d/Nodejs:$PATH"
   ```

**坑：**
- **写给 shell 的脚本文件必须是纯 ASCII（.ps1 尤其）**：PowerShell 5.1 按 ANSI 读 .ps1，文件里出现中文会直接 ParserError（"字符串缺少终止符"），脚本连第一行都跑不到，乱码报错还会被误判成权限问题。要展示中文提示就换载体（.bat 用 GBK + `chcp 936`，或 agent 直接说给用户）。
- **别把 PowerShell 写成 `-Command` 内联**：`$_`、`$env:` 会被 git-bash 先吃掉/改写，命令静默变形（报 `ProcessName : 无法将 ... 识别为 cmdlet`）。一律 `write_file` 成 .ps1，再 `powershell -NoProfile -ExecutionPolicy Bypass -File X.ps1`。
- **启动 Windows GUI 程序不要靠 `cmd //c start`**：本机 git-bash 下 `cmd //c <命令>` 常常只起一个交互式 cmd（打印版权横幅，目标程序没起）。用 python 更稳：
  `python -c "import subprocess;subprocess.Popen([r'D:\路径\a.exe'], cwd=r'D:\路径', creationflags=0x00000008)"`（DETACHED_PROCESS，不占当前终端）
- `setx PATH ... /M` 需要管理员权限且会截断过长的 PATH → 用 `[Environment]::SetEnvironmentVariable("Path", ... "User")` 更安全
- zip 版不像 MSI 自动添加 PATH，必须手动配

### npm 包安装（n8n、CLI 工具类）

- **国内挂镜像**：`npm install <包> --registry=https://registry.npmmirror.com --no-audit --no-fund`。走官方源在国内可能长时间无输出、既不报错也不结束（实测有跑了一个小时仍在半装的情况）。
- **后台装必须盯**：`terminal(background=true, notify_on_complete=true)` 起，中途 `process_manage(action='poll')` 看进度；超过十几分钟没完就 kill 重来，别让它挂着——挂着的进程一直占后台计数，还留着半装状态。
- **半装怎么认**：`node_modules/<包名>` 目录在、但 `node_modules/.bin/` 空或缺条目 → 安装被中断，此时 `./node_modules/.bin/<cli>` 与 `npx` 都报 `No such file or directory`。
- **验证绕过 .bin**：直接跑入口 `node node_modules/<包名>/bin/<cli> --version`，能打印版本才算真装上。
- **半装残留不用删**：带镜像重跑补齐比重下快；`rm -rf node_modules` 留作最后手段。
- 本机 npm 全局前缀在 `D:\Nodejs`（`npm config get prefix` 确认），全局装不会落 C 盘。
- 用户叫停或说“等低峰期再装”就记下停手：不自动挂定时任务、不换个命令继续试同一件事。

### Python

（待补充安装要点）

### Claude Code（AI 编程 CLI，含界面汉化）

- 安装：`npm install -g @anthropic-ai/claude-code`（装到 D:\Nodejs）
- 验证可用性：`claude --version`（版本）+ `claude auth status`
  （`loggedIn: false` = 未登录；没有 Claude 账号/API key 前用不了）
- **界面汉化**（官方无中文，用社区插件）：推荐 taekchef/claude-code-zh-cn
  （插件市场两条命令安装，vetted 项目，安全机制完善）——完整步骤、安全性
  说明、版本支持见 `references/claude-code-zh-localization.md`

### GitHub CLI（gh，便携 zip 安装 + 设备码登录）

**装（无需管理员、不占 C 盘）：**

```bash
TAG=$(curl -s -m 20 https://api.github.com/repos/cli/cli/releases/latest | grep -m1 '"tag_name"' | sed 's/.*"tag_name": *"v\?\([^"]*\)".*/\1/')
curl -sL -m 240 -o /d/tools/gh.zip -w "http=%{http_code} size=%{size_download}\n" \
  "https://github.com/cli/cli/releases/download/v${TAG}/gh_${TAG}_windows_amd64.zip"
cd /d/tools && unzip -q -o gh.zip -d gh_tmp && rm -rf gh && mv gh_tmp gh && rm -f gh.zip
/d/tools/gh/bin/gh.exe --version        # 自检：必须打印版本号
```

zip 约 15MB，前台下载即可，别当大文件夹在后台挂。**这类一次性下载/检查脚本不要用 `set -e` 开头**——顺手 `ls` 一个不存在的候选目录返回非 0 就把整段脚本掐断，前面的下载步骤白等（要么 `|| true`，要么别开 `set -e`）。装完落 `/d/tools/gh`；每次调用用绝对路径 `/d/tools/gh/bin/gh.exe`，或在同一条命令里 `export PATH="/d/tools/gh/bin:$PATH"`——**git-bash 的非交互调用不保证加载 ~/.bashrc**，想让 gh 到处都能直接敲，按上面 Node.js 一节的 PowerShell 方式写进用户级 Windows PATH。

**登录（设备码流程，用户只需输一个验证码）：**

```bash
export PATH="/d/tools/gh/bin:$PATH"
# 用 pty + background 起，再用 process_manage 驱动（见上一节）
gh auth login --hostname github.com --git-protocol https --web
```

1. 日志里出现 `? Authenticate Git with your GitHub credentials? (Y/n)` → `submit` 回 `Y`。选 Yes 才会顺带配好 git 凭据，之后 `git push/pull` 免密——**等于 gh 和 PAT 两条路一次办完，不需要再让用户手动生成 token**。
2. 继续读日志，拿到 `One-time code (XXXX-XXXX) copied to clipboard` → 把这个码原样报给用户，让他打开 https://github.com/login/device 输入并点授权。码约 15 分钟有效，过期就重跑一条命令换新码；码已自动进剪贴板，用户可以直接粘贴。
3. 用户授权后 `gh auth status` 验证，`gh api user` 看当前账号；`gh auth token` 能取到令牌，需要时 `export GITHUB_TOKEN=$(gh auth token)` 供 curl 用。

**没登录时能查到什么：** 匿名接口可以查公开库 `curl -s "https://api.github.com/users/<login>/repos?per_page=100"`。返回空数组 = 该号公开库为空，**不代表账号没内容**——私有库必须登录后 `gh repo list <login>` 才看得到（匿名 API 每小时 60 次限额）。另外别信 `git config user.name/email`：这台机器上是 `zhuDer` / `zhender@example.com` 这类占位值，登录后按用户真实账号确认身份。

### Arduino IDE

- **下载地址：** https://arduino.cc/en/software（官方，不要用 arduino-ide.org 等第三方站）
- **不要在官网选错版本：**
  - ✅ 正确：点 **"Win 10 and newer"** 大按钮 → 下载 `arduino-ide_x.x.x_Windows_64bit.exe`（NSIS 安装包，约 200MB+）
  - ❌ 不要选 **Win MSI installer**（不同安装器，不推荐）
  - ❌ 不要选 **Win ZIP**（绿色版，配置麻烦）
- **不要下成这些冒牌货：**
  - ❌ **Arduino PLC IDE 1.1.0** — 那是工业 PLC 编程工具，跟普通 Arduino/ESP32 开发无关
  - ❌ **ArduinoAppLab** — 不是 Arduino IDE，是另一个软件
  - ❌ 从 **arduino-ide.org** 下载 — 那是第三方中文镜像站，非官方
- **安装路径：** 问用户是否要改到 D 盘，如果用户说默认就放 C 盘
- **安装步骤：** 双击 NSIS 安装包 → 选择语言（中文）→ 一路下一步即可
- **装完后：** 需要配置 ESP32 板支持包（见 esp32-hardware-box skill）
- **可能出现的中文路径问题：** 如果 Windows 用户名是中文，Arduino IDE 本身不受影响（它不是通过 bash 读取路径的），但后续 ESP32 相关工具链可能遇到，参考 Git 的中文用户名路径坑

### Git for Windows（中文用户名路径坑）

- **关键坑：** 如果 Windows 用户名是中文（如「使用者」），git-bash 的 `$HOME` 环境变量会显示为乱码路径，导致 `git config --global` 读不到 `.gitconfig` 文件
- **解决方法：** 直接用 `write_file` 把 `.gitconfig` 写到正确的 Windows 路径 `C:\Users\中文用户名\.gitconfig`，或者显式指定 `HOME="/c/Users/中文用户名" git config --global xxx`
- **验证方法：** 用 `HOME="/c/Users/中文用户名" git config --global user.name` 检查配置是否生效
- **实际使用不受影响：** VS Code 等其他工具能正确读取 `C:\Users\中文用户名\.gitconfig`，只有 git-bash 终端里 `--global` 参数会因 $HOME 乱码而失灵

## 判断某软件是否已装（"这电脑有 X 吗"）

按顺序查，**别只看一处就下结论**：

1. `which X` / `where X`（在 PATH 上就能直接用）
2. 常规安装位：`ls -d "/c/Program Files"/*X* "/c/Program Files (x86)"/*X* /d/*X*`
3. 注册表卸载项（正规安装必有）：`Get-ItemProperty` 三个 Uninstall 键 | `Where DisplayName -like '*X*'`
4. `winget list --name X`
5. 快捷方式：桌面 + 两个开始菜单目录 `find ... -iname "*X*"`
6. 全盘 exe：`find /c /d -maxdepth 4 -iname "x*.exe"`
7. 配置/数据残留：`~/AppData/Roaming/<厂商>`、`~/AppData/Local/<软件>`

**两条最容易答错的判定**：
- **配置目录残留 ≠ 已安装**：Roaming 里有软件配置目录只说明"以前跑过"。本机 Blender 就是 Roaming 有 4.5 配置、全盘却没有 blender.exe → 正确结论是"装过，现在没装"。
- **下载目录里的安装包 ≠ 已安装**：`D:\网页下载\x.zip` 只是包，还要看解压没解压（同目录/附近有没有 exe）。

## 绿色 / 便携 zip 包安装 + 装后必做自检

**优先用使用者已经下好的包**（先翻 `D:\网页下载\`、Downloads、桌面）——省一次几百 MB 下载，也避免他重复下载。

流程（Blender 4.5.10 实测，同样适用于 Node zip 版等便携包）：

1. **解压用 python 脚本，不要 `unzip -o` 一把梭**：`write_file` 一个 .py，`zipfile.extractall` 到 D 盘，同时打印条目数/顶层目录、`os.walk` 找主 exe、统计占用。解压 380MB 包约 29 秒。
2. **版本自检**：`"<exe>" --version`（Blender 后台模式能跑，退出码 0 + 版本行）。
3. **能力自检**：创意/渲染类软件必须证明核心能力真的能用，不能只看版本号。Blender 用 `-b --factory-startup --python <脚本>` 枚举渲染设备 + 渲一张小图，见 `scripts/blender_gpu_check.py`。
4. **给快捷方式**（用户找不到入口时）：桌面 `X.lnk`，用 ASCII-only .ps1 + WScript.Shell 创建。
5. **汇报必须带实测证据**：版本字符串、设备清单、渲染耗时与产物路径 —— 别只说"装好了"。

Blender 的路径、版本选择（4.5 LTS vs 5.2.1）、清华镜像直链、本机配置对照、首次设置见 `references/blender-install.md`。

## 追踪捆绑/流氓软件来源

当用户说\"桌面上多了个 xxx，帮我删掉，查查是谁装的\"时，按以下流程操作：

### 第一步：找到快捷方式

```bash
ls -la /c/Users/<username>/Desktop/ | grep -i <关键词>
```

注意：中文 Windows 下桌面可能是 `Desktop` 或 `桌面/` 目录，都检查。

### 第二步：解析 .lnk 文件找出真实目标

Windows 的 `.lnk` 快捷方式文件记录了目标程序的真实路径。**不要在终端用 sed/grep/hexdump，用 Python 脚本解析：**

**方法 A（推荐，简单直接）：** 提取所有可打印 ASCII 路径字符串

```python
import re
with open('C:/Users/xxx/Desktop/xxx.lnk', 'rb') as f:
    d = f.read()
for m in re.finditer(rb'[\x20-\x7e]{8,}', d):
    s = m.group().decode('ascii', errors='replace')
    if ('\\\\' in s or ':' in s) and not s.startswith('--'):
        print(s)
```

这会直接打印出 `.lnk` 文件中所有看起来像路径的字符串，包括目标 exe 的完整路径。

**方法 B（完整解析 LNK header）：** 需要处理 shell link header 的二进制结构（更精确但更复杂）。通常方法 A 就够了。

### 第三步：识别捆绑源

常见的捆绑模式：

| 特征路径 | 捆绑源 |
|----------|--------|
| `*360se6*\\components\\seapp\\SeAppService.exe` | **360安全浏览器** 的软件管家 |
| `*360*\\gamehall\\*` | **360安全卫士** 游戏大厅 |
| `*360SoftMgr*` 或 `*SoftMgr*` | **360软件管家** |
| `SeAppService.exe` + `--config=base64` | 通过 360 软件管家服务启动的推广安装 |
| `*2345*` | 2345 全家桶系列 |
| `*pinduoduo*` 或 `*duo*` | 拼多多或同类推广 |
| `*LenovoVantage*` 或 `*LSC*` | 联想电脑管家 |

**360 的典型模式：** 快捷方式的 `TargetPath` 指向 `...\\SeAppService.exe`，带 `--config=<base64>` 参数。这个 config 包含要启动的程序名、下载地址等 json 信息。base64 解码后可看到推广软件的实际名称和下载链接。

### 第四步：查找真正的安装目录

顺着目标路径找安装目录。常见位置：

- `/c/Program Files/` — 64位软件
- `/c/Program Files (x86)/` — 32位软件
- `/c/Users/<用户名>/AppData/` — 用户级安装
- `/d/`, `/e/` 等其他盘符

用 `find` 命令搜索关键词：

```bash
# 在所有盘符搜索包含软件名的目录
find /c /d /e -maxdepth 3 -type d -iname '*关键词*' 2>/dev/null
```

### 第五步：检查注册表安装列表（可选）

```bash
# 列出所有已安装软件的 DisplayName
powershell -Command "Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*', 'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' | Where-Object { \$_.DisplayName } | Select-Object DisplayName, InstallLocation"
```

如果注册表里没有，说明该软件可能是通过游戏大厅/云游戏平台启动的，没有独立安装记录。

### 第六步：清除

1. **删除快捷方式：** `rm "桌面路径/xxx.lnk"`
2. **删除安装目录：** `rm -rf "安装目录"`
3. **如果是捆绑游戏且没有独立安装目录：** 只删快捷方式即可
4. **如果用户想彻底清理捆绑源头：** 先确认用户是想只删目标软件还是连捆绑源一起移除。如果用户选择连捆绑源一起移除，参考下面的「彻底移除360全家桶」流程。

**注意：** 对于 360 全家桶式安装（跨 C/D/E 多盘符），询问用户是想只删除目标软件，还是把整个 360 全家桶都移除。

### 第七步（扩展）：彻底移除 360 全家桶

当用户确认要移除整个 360 系列软件时，按以下步骤操作。360 软件通常分布在多个盘符，需要系统性地搜索和清除。

#### 7.1 全面扫描 360 相关目录

```bash
# 扫描所有常见盘符下的 360 目录
find /c /d /e -maxdepth 2 -type d -iname '*360*' 2>/dev/null | sort
```

常见的 360 目录分布（实际案例——使用者的电脑）：
| 盘符 | 目录 | 说明 |
|------|------|------|
| C:\ | `Program Files (x86)\360` | 空壳，实际文件在 D 盘 |
| C:\ | `ProgramData\360SD` | 360 安全卫士数据 |
| D:\ | `360Safe` | **360安全卫士本体**（主目录，含 uninst.exe 卸载程序） |
| D:\ | `360DrvMgr` / `360驱动大师目录` | 360驱动大师 |
| D:\ | `360zip` | 360压缩 |
| D:\ | `360Downloads` / `360安全浏览器下载` | 360下载 / 浏览器下载目录 |
| D:\ | `360游戏管家辉煌时刻` | 360游戏管家（可能为空文件夹） |
| E:\ | `360se6\Application\components\seapp` | 360安全浏览器软件管家（捆绑游戏元凶） |
| E:\ | `360se6\Application\components\gamehall` | 游戏大厅 |
| E:\ | `360se6\Application\components\gameplugin` | 游戏插件 |
| E:\ | `360se6\Application\components\gamespace` | 游戏空间 |

#### 7.2 先确认 360 进程是否在运行

```bash
powershell -Command "Get-Process -Name '*360*' -ErrorAction SilentlyContinue | Select-Object Name, Id | Format-List"
```

如果发现正在运行的 360 进程（如 `360huabao`、`360Safe`、`360tray` 等），先杀掉它们：

```bash
powershell -Command "Stop-Process -Name '*360*' -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2"
```

#### 7.3 尝试正规卸载（通过 360 自带的 uninst.exe）

```bash
# 查找 uninst.exe 位置
ls /d/360Safe/uninst.exe 2>/dev/null

# 尝试静默卸载（可能需要管理员权限，可能弹 UAC 窗口）
"D:/360Safe/uninst.exe" /quiet

# 常见的卸载参数变化：
# - /quiet /S /silent /verysilent /qb /qn 等
# 如果静默卸载失败，尝试用 cmd 启动让系统弹 UAC：
cmd.exe /c start /wait "" "D:\360Safe\uninst.exe"
```

**实际经验：** 360 的 uninst.exe 在 git-bash 下直接调用会报 `Permission denied`（因为 MSYS 下的权限映射问题）。破解方法：
1. 用 `cmd.exe /c start "" "D:\360Safe\uninst.exe"` 来启动
2. 或者直接用 `powershell` 调用
3. 如果用户点 UAC 确认后没反应/不静默卸载，直接走强制删除

#### 7.4 强制删除（当正规卸载失败或无交互时）

```bash
# 夺权：takeown + icacls
takeown /f "D:\360Safe" /r /d y 2>nul
icacls "D:\360Safe" /grant Administrators:F /T /Q 2>nul

# 安全卫士本体
rm -rf "/d/360Safe"

# 游戏相关
rm -rf "/d/360游戏管家辉煌时刻"
rm -rf "/e/360se6/Application/components/seapp"
rm -rf "/e/360se6/Application/components/gamehall"
rm -rf "/e/360se6/Application/components/gameplugin"
rm -rf "/e/360se6/Application/components/gamespace"

# 询问用户后决定是否删除的其他 360 组件
# rm -rf "/d/360zip"
# rm -rf "/d/360DrvMgr"
# rm -rf "/d/360Downloads"
```

**注意执行方式：** 大文件/多目录的递归删除建议用 `background=true` 执行，避免 timeout。

#### 7.5 处理被锁定的文件

如果删除时提示 `Device or resource busy`（文件被占用），按以下优先级尝试：

1. **查占用进程**（找到是哪个进程锁住了文件）：
```bash
powershell -Command "Get-Process | Where-Object { $_.Modules.FileName -like '*文件名*' } | Select-Object Name, Id"
```

2. **杀掉进程后重试**：
```bash
powershell -Command "Stop-Process -Id <PID> -Force"
```

3. **改名后删除**（文件被占用但允许改名）：
```bash
powershell -Command "Rename-Item '原路径' '新路径' -Force"
```

4. **安排重启后自动清除**（最后的办法，需要管理员权限）：
```bash
# 用 schtasks 创建一次性开机任务
# 注意：schtasks 在 git-bash 下可能因路径含中文报语法错误，建议用 PowerShell
powershell -Command "
schtasks /Create /SC ONSTART /TN 'CleanRemnant' /TR \"'cmd.exe /c del /f /q \`\"路径\`\" && rmdir /s /q \`\"路径\`\"'\" /F /RL HIGHEST
"
```

**坑：** schtasks 可能因权限问题提示"拒绝访问"。此时只需告知用户：这个文件暂无法删除，重启后通常会释放掉，后续可以手动删除。

**重要原则：** 如果只剩一个 .zip 或 .7z 等压缩包删不掉，不影响整体清理成效。告知用户即可，不要在单个文件上耗费大量时间。

#### 7.6 验证删除结果

```bash
# 逐项检查
echo "=== 360Safe ==="
ls /d/360Safe/ 2>/dev/null | wc -l
echo "=== 游戏管家 ==="
ls "/d/360游戏管家辉煌时刻/" 2>/dev/null | wc -l
echo "=== seapp ==="
ls /e/360se6/Application/components/seapp/ 2>/dev/null
echo "=== gamehall ==="
ls /e/360se6/Application/components/gamehall/ 2>/dev/null | wc -l
echo "=== gameplugin ==="
ls /e/360se6/Application/components/gameplugin/ 2>/dev/null | wc -l
echo "=== gamespace ==="
ls /e/360se6/Application/components/gamespace/ 2>/dev/null | wc -l
echo "=== 桌面快捷方式 ==="
ls "/c/Users/<用户名>/Desktop/xxx.lnk" 2>/dev/null
```

所有列数为 0 或无文件输出即表示清除成功。

#### 7.7 残留清理（注册表 + 快捷方式）

360 可能会在以下位置留下残留：
- 开始菜单的快捷方式：`C:\ProgramData\Microsoft\Windows\Start Menu\`
- 桌面快捷方式
- 注册表 `HKCU\Software\360` / `HKLM\Software\360Store` 等
- 快速启动栏和任务栏锁定

如果用户在意，可以搜索并清理桌面快捷方式：
```bash
find "/c/Users/<用户名>/Desktop" -name '*360*' -o -name '*游戏*' 2>/dev/null

## 检测 Electron 应用的来源（进阶）

当目标软件是基于 Electron 的桌面应用（如 WorkBuddy/CodeBuddy、VS Code、Notion、Discord 等），可以通过检查内部配置文件来识别实际的发行方和分发渠道：

### 查找 product.json

Electron 应用通常在 `resources/app.asar` 或 `resources/app.asar.unpacked` 中有 `product.json` 或类似配置文件：

```bash
# 查找 product.json
find "/d/目标软件/resources" -maxdepth 3 -name "product*.json" 2>/dev/null

# 查看内容
cat "/d/目标软件/resources/app.asar.unpacked/cli/product.json"
```

### product.json 中可识别的字段

| 字段路径 | 含义 |
|---------|------|
| `productName` | 软件实际名称 |
| `endpoint` / `officialEndpoints` | 后端 API 地址（可识别服务商） |
| `authentication.id` | 认证方案标识（如 `workbuddy-desktop`） |
| `authentication.platform` | 所属平台 |
| `links.officialWebsite` | 官方网站 |
| `updates.download.scene` | 更新分发渠道（如 `saas`） |
| `config.channelBranding.channels` | 渠道品牌合作方（如联通云等） |
| `applicationName` / `dataFolderName` | 应用名和数据目录名 |

### 查看 exe 的版本信息确认发行方

```bash
powershell -Command "(Get-Item 'D:\\路径\\主程序.exe').VersionInfo | Select-Object CompanyName, ProductName, FileDescription"
```

### 判断安装来源

- `CompanyName` = `Tencent Technology (Shenzhen) Company Limited` → 腾讯出品
- 安装目录创建时间与快捷方式创建时间相差在 1-2 分钟内 → 很可能是自主安装
- 注册表中没有卸载项 + 无安装日志 → 非 MSI 正规安装，可能是静默捆绑或用户手动解压

### 实际案例：WorkBuddy

在 user 使用者 的电脑上追踪到 WorkBuddy（腾讯 CodeBuddy 桌面端）：
- 安装路径：`D:\workbuddy\`
- 程序版本：5.1.6
- 发行方：Tencent Technology (Shenzhen) Company Limited
- product.json 显示 endpoint 为 `https://copilot.tencent.com`
- 安装时间：2026-06-25 15:48（与快捷方式创建时间差 1 分钟）
- 注册表无卸载项 → 非标准 MSI 安装
- 结论：可能是通过其他腾讯软件自动下载或使用者自主安装后遗忘

### 第八步：询问用户意图后再执行删除

**关键教训（WorkBuddy 误删事件）：** 
当用户说"删掉它"时，**必须先确认删的是什么**，特别是当上下文中有多个目标时：

1. 用户可能正在讨论"小程序桌面"，同时桌面上有 WorkBuddy 的快捷方式
2. 用户说"删掉他"时，"他"可能指上一个话题（小程序桌面），而不是当前正在调查的 WorkBuddy
3. **正确做法：** "使用者说的'它'是指刚刚查到的 WorkBuddy，还是之前说的那个小程序桌面呀？"
4. **错误做法：** 默认认为用户指最近一次分析的对象，直接执行删除

### 第九步：清理残留

删除后验证清理结果：

```bash
# 验证安装目录
test -d "/d/目标目录" && echo "还在" || echo "已删除"

# 验证快捷方式
test -f "/c/Users/<用户名>/Desktop/路径/xxx.lnk" && echo "还在" || echo "已删除"

# 验证 AppData 残留
test -d "/c/Users/<用户名>/AppData/Roaming/xxx" && echo "还在" || echo "无残留"
test -d "/c/Users/<用户名>/AppData/Local/xxx" && echo "还在" || echo "无残留"
```

## GitHub 开源 Python 项目手动安装（开发工具类）

用户从 GitHub 找到项目（README 给了 `git clone + pip install -r requirements.txt` 那套）时，按以下流程。用户问"代码贴到哪里"= 要帮他装，不是让他自己操作。

**流程：**
1. **先检查是否已装**：`which <命令名>`（很多工具之前用 winget 装过，已在 PATH，直接能用就不用装）。例：用户下载 ffmpeg，结果 `which ffmpeg` 显示已有 8.1.2。
2. **识别包格式**：`tar -tf 包名 | head` 看内容。有 `Makefile`/`*.c` = **Linux 源码包，Windows 不能直接装**；`.exe`/`.msi`/zip 编译版才是 Windows 用的。tar.xz/tar.gz 一律先怀疑是源码。
3. **clone**（GitHub 被墙时先 export 代理：`export https_proxy=http://127.0.0.1:17890 http_proxy=http://127.0.0.1:17890`，放 D 盘如 `/d/<项目名>`）。
4. **读 README** 确认前置要求（Python 版本、ffmpeg、系统包等）和完整配置项。
5. `pip install -r requirements.txt`（注意 Python 3.14 等新版本下 faiss-cpu 等包的 wheel 兼容性，能装上就没问题）。
6. `cp .env.example .env`，然后**把示例里的占位路径改成这台机器的真实路径**（如 FFMPEG_PATH 必须指向实际 ffmpeg.exe）。
7. **API Key 处理**：用户机器的 key **不存于** config.yaml（全空）、hermes 目录 .env（全是注释占位）、系统环境变量、scripts/cron 脚本——**搜一遍没找到就直接问用户要**，别反复翻文件浪费时间。需要多个 key 时一次性说清每个去哪个平台拿（DeepSeek 平台 / siliconflow.cn / 阿里云百炼等）。
8. **启动验证**：`terminal(background=true)` 起服务（如 `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`），再验证 HTTP 200。**Windows git-bash 下 `curl -o /tmp/...` 可能 write error（exit 23），改用 `python -c "import httpx; r=httpx.get(...)"` 验证更稳**；长内联 python 命令用户可能拒绝，复杂验证先 `write_file` 成 .py 脚本（放 `D:\Temp\UserTemp`，hermes-verify- 前缀）再执行，用完即删。
9. 服务可以挂着等用户填 key；汇报时把「还差什么」列清楚（缺 key 就是差 key）。

详细案例（帧知 FrameWise 安装全程）见 `references/github-python-app-install.md`。

## GitHub 克隆项目"打不开/找不到入口"排查（ComfyUI 实例 2026-09）

用户说"xx 打不开"时**先查服务是否在跑，再查入口，别急着重装**：

1. **端口探测**（本地 Web 服务类）：`curl -s http://127.0.0.1:8188/system_stats`；ComfyUI 端口被占会自动 +1，把 8187~8190 全试一遍。没响应 = 服务根本没起，浏览器自然打不开。
2. **找安装位置和启动器**：`find /d -maxdepth 3 -iname "*关键词*"`、桌面 `*.lnk`；项目目录里 `ls *.bat` 找启动脚本（如 启动_ComfyUI.bat），`cat` 看启动方式（通常 venv activate + python main.py）。
3. **venv 完整性只读检查**（先不动手跑）：
   - `cat venv/pyvenv.cfg` → home 指向的 Python 解释器是否还在（venv 失效头号原因）
   - `ls venv/Scripts/python.exe` 存在
   - `ls venv/Lib/site-packages/ | grep 关键包`（如 torch）
4. **后台启动验证**：`terminal(background=true)` 跑 `./venv/Scripts/python.exe main.py > /tmp/x.log 2>&1`，再轮询日志和端口。
5. **首次启动慢的坑**：新版 ComfyUI 首次启动 1.5~2 分钟（alembic 数据库插件 + comfy_kitchen 后端探测 + 前端资源），日志可能 30~60 秒不动——**Python stdout 有缓冲，tail 不实时**；判断死活看 `tasklist` 里 python 进程内存是否持续增长（涨 = 在加载，别 kill）。
6. **用户找不到入口 → 建桌面快捷方式**（PowerShell WScript.Shell，中文路径 OK，`$` 转义 `\$`），命令见 `references/comfyui-launch-troubleshooting.md`。
7. **启动成功标志**：日志 `To see the GUI go to: http://127.0.0.1:8188` + `curl system_stats` 返回 JSON。
8. **界面能开但出不了图**：`models/checkpoints/` 只有占位文件 → 模型目录空，需下载模型（4GB 显存放 SD1.5）。

**被 BLOCKED 的命令不换法重试**：用户拦截过一次 python 检查命令就停下说明意图/问用户，别换个命令达到同样目的。

## 处理交互式 CLI（安装 / 登录 / 设备码流程）

某些工具需要交互式输入（项目名、模板选择，或登录时的确认与验证码）。**当前 Hermes 的 terminal 是能交互的，别再写"agent 不支持交互输入"然后让用户自己敲：**

```
terminal(pty=true, background=true)          # 起交互进程
process_manage(action='log'|'poll')          # 读当前提示
process_manage(action='submit', data='Y')    # 送一行 + 回车
```

**Windows PTY 上必须用 `submit`（或 `write` 带 `\r`），只写 `\n` 不会当回车用**，子进程的提示会一直不回。多条提示就用 log→submit→log 循环，每轮都看日志确认提示真的变了再送下一句；不确定的选项先读全提示再答。

**pty 走不通时**（工具要真 TTY 之外的图形窗口、或交互内容随会话变化）才退回下面三条（安装类）：

1. **优先尝试传参数跳过交互**：查看文档是否有 `--yes`、`-y`、`--defaults` 等参数
2. **如果无法跳过**：直接在终端跑命令，它会停在等待输入的地方。然后告诉用户需要手动输入什么：
   - 如 `npx -y @taptap/maker init` 会停在"Enter project name" → 让用户在对应目录的终端/CMD 里自己跑一次命令
   - 给用户具体的路径和命令：「请在桌面的 xxx 文件夹打开 PowerShell/CMD，输这个命令：`npx @taptap/maker init`，然后在提示时输入项目名就行」
3. **或者用 `echo "project-name" | npx ...` 管道输入**（部分工具支持）

## 坑（Pitfalls）

1. **不要直接说"按 Next 就行"**——用户可能不确定哪个是 Next，要说"点 Next（下一步）"
2. **用户说"看不懂英文"时不要继续用英文术语**，用中文描述页面功能而不是翻译标题
3. **不同类型的软件安装器可能有不同 UI 布局**（MSI vs EXE, 新版 vs 旧版），如果用户反馈选项不对，不要争辩，让用户描述
4. **PATH 环境变量修改不一定会立即生效**——装完可能需要重启终端或整个系统
5. **用户可能忘记选 D 盘路径**——在第二步时强调，确认路径后再让用户点 Next
6. **不要叫用户截图/拍照来确认**——当前模型（DeepSeek flash）纯文字，看不见图。如果用户说"你看一下这个"，应回答自己不能用视觉并让用户文字描述。同时**不要自贬**（不说"我瞎""我看不见"等），应积极回应如"等你以后给我加了摄像头就能看了！"。未来如果换了多模态模型，可以更新此条。
8. **个人信息不要瞎填**——用户的邮箱、用户名等必须问清楚再填，不能随手编造占位。用户对"你瞎填"非常反感。
9. **用户打错字时主动确认**——能猜就猜，猜不太准时问"使用者你是不是想说XXX的意思？"，确认的同时也让用户感受到你在认真听、在关心。
10. **中文 Windows 路径执行脚本**——当需要运行 Python 脚本处理文件时，git-bash 可能因中文用户名路径乱码导致 `python -c "..."` 内联脚本引用混乱。**可靠方法：** 先用 `write_file` 写入完整 Windows 路径的 .py 文件到桌面，再用 `terminal(f'python "C:\\Users\\使用者\\Desktop\\_script.py"')` 执行。详见 `references/chinese-windows-path-workarounds.md`。
11. **装什么必须先跟用户确认，不能替用户选**——用户报的插件/软件名查不到（如"teach插件"）、名字不清或不确定时，先问清楚全名和来源（在哪看到的/谁推荐的）再动手；`clarify` 工具超时返回"用最佳判断"**不等于授权继续行动**，尤其涉及下载/安装/系统更改时，用户没回复就停手等他。2026.8 实例：使用者说"下载 teach 插件"，我猜是 Spaced Repetition 并擅自开始下载 311MB 的 Obsidian 安装包，被使用者"不是你选择了什么啊""先别搞"叫停——正确做法是停下先问"你说的插件具体叫啥"。
12. **装插件前先确认宿主软件是否已装**——Obsidian 等插件体系依附于本体，本体没装（程序/配置/库目录都没有）时插件无从谈起；先查清现状再规划，不要闷头开装。
13. **用户下载的包可能是 Linux 源码包**——`.tar.xz`/`.tar.gz` 不是 Windows 安装包（ffmpeg 9.0.1.tar.xz 案例：里面是 Makefile 和 .c 源码，Windows 装不了）。识别：`tar -tf` 看内容；ffmpeg 在 Windows 的正确装法是 `winget install ffmpeg`（gyan.dev 编译版）或官网 zip。先 `which` 检查是否已装，已装（winget 装的常在 PATH）就告诉用户不用重复装。
14. **配置第三方工具缺 API Key 时直接问用户**——这台机器上使用者的 API key 不存于任何本地文件（config.yaml 空、.env 全是注释占位、无环境变量、脚本里也没有），搜一遍确认没有就直接列出"去哪个平台拿 key"，不要继续翻文件。
