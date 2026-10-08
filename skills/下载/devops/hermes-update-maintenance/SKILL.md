---
name: hermes-update-maintenance
description: 判断Hermes是否需要更新并安全更新源码安装。触发：hermes更新、更新hermes、落后多少提交、新版有什么。
---

# Hermes 更新维护（源码安装 / Windows）

用户问"hermes 是不是要更新了""更新了什么""落后多少"时走这套流程。

本机是**手工搭建的源码 checkout**：不是安装脚本装的、也不是 PyPI 更新器管的，
所以内置 `hermes update` 在这里**是用不了的**（见第二节）。必须先量差距，再手动更新。

## 一、先量差距，绝不凭感觉下结论

三个数据源都要看：

1. **PyPI 版本号**（出厂版本线）
   ```bash
   curl -s https://pypi.org/pypi/hermes-agent/json   # info.version + releases 各版发布时间
   ```
2. **源码仓库与上游的提交差距**（真正决定"更新量大不大"）
   → 用 GitHub compare API 拿 `total_commits`，固定命令见 `references/this-machine.md`
   最快的一版：先 `git ls-remote origin main` 只取镜像 sha（几秒、不下载对象），再
   `curl -s "https://api.github.com/repos/NousResearch/hermes-agent/compare/<本地HEAD完整sha>...<镜像sha>"`。
   镜像会滞后于 GitHub 官方 main 一两个提交，报数字时说清是跟哪个 sha 比的。
3. **发行说明**（"更新了什么"的最佳来源）
   ```bash
   curl -s "https://api.github.com/repos/NousResearch/hermes-agent/releases?per_page=8"
   ```
   每个 release 的 `body` 带 `## ✨ Highlights` 和各模块小节，按标题列表决定读哪段

⚠ **最大的坑：浅克隆会让本地 git 撒谎。**
`.git/shallow` 存在时，`git rev-list --count HEAD..origin/main` 与 `git log HEAD..origin/main`
只会在浅边界内数，可能报"落后 1 个提交"，而真实差距是几千个。
实证：本地 HEAD 2026-08-19、上游 main 2026-09-10，本地 git 说 **1**，compare API 说 **9532**。
**先 `ls .git/shallow` 判断，用 API 量，再向用户报数字。**报错了要立刻自己纠正并说清原因。

## 二、诊断内置更新器是否可用

```bash
hermes --version        # 看 "Install method: "（本机没有 hermes version 子命令，会报 invalid choice）
hermes update --check
```

若报 `✗ Not a git repository — cannot check for updates.` 且 `Install method: unknown`，
说明这套是手工搭的 checkout，更新器认不出仓库位置 → **只能手动更新**。
不要反复试 `hermes update` 或 `hermes update --check` 换目录重跑，它认的是安装路径不是当前目录。

## 三、安全准备（非破坏性，可以先做，做完再问用户）

这两步不碰工作区、不换代码，做完让后续更新快很多，随时可退：

```bash
cd ~/AppData/Local/hermes/hermes-agent
git config core.fileMode false      # 消除 Windows 丢执行位造成的假改动
git status --porcelain | wc -l      # 应从几十变成 0
git fetch --all --tags              # 只下载对象，不动工作区，代码还是旧版
```

**报备规则**：`git fetch --all` 这种几十秒以上的命令，**开跑前说一句"现在在跑 X"，
跑完报一句结果**（本机使用者会在长时间静默后问"现在你在跑什么"）；短查询不必逐条汇报。
破坏性步骤**停下等他明确同意**再做——本机使用者不喜欢自作主张。

## 四、破坏性步骤（必须用户同意 + 先退出 Hermes）

顺序不能换，`reset --hard` 之后才是 pip：

```bash
cd ~/AppData/Local/hermes/hermes-agent
git reset --hard origin/main        # ← 从这一步开始才真正换代码
venv\Scripts\pip install -e .       # 只有依赖变了才需要
hermes --version
hermes config migrate               # 跨版本后补新增配置项
```

更新前先备份：`hermes backup`（或 `hermes update --backup`，其 `pre_update_backup` 本机为 false）。

## 五、Windows 特有的坑

| 坑 | 表现 | 处理 |
|---|---|---|
| exe 被锁 | pip 替换 `hermes.exe` 报 WinError 32 | 更新前**退出所有 Hermes 进程**（含 gateway/desktop） |
| 编译超时 | pydantic-core/cryptography 编译 5-10 分钟 | 走 agent 的 terminal 工具会被 300s 砍掉 → 让用户在真终端跑，或写 `.bat` 让他双击 |
| 假改动 | `git status` 几十个 modified，但 `git diff --stat` 显示 0 行增删 | 就是权限位 100755→100644，`git config core.fileMode false` 一次解决 |
| 拉取来源 | 本机 origin 是国内镜像 cnb.cool | 拉代码**不需要挂代理**；抓 GitHub 官方 API 前先各探 1 秒（`curl -s -m 8 -o /dev/null -w "%{http_code}" <url>`，直连与 `-x http://127.0.0.1:17890` 各跑一次；代理没监听时 curl 退 7、http=000）。**别默认必须挂代理，也别默认代理一定在跑**——直连常常就是通的 |
| 报错顺序 | 先报"1 个提交"再改成"9532 个" | 量错就当场纠正，说明是浅克隆所致，不要含糊过去 |

## 六、验证

```bash
hermes --version
cd ~/AppData/Local/hermes/hermes-agent && git log -1 --format="%h %ad %s" --date=short | cat
hermes config migrate               # 应提示无新增项
hermes doctor
```

**代码来源判据（最能说明问题的一条）**：从任意非仓库目录跑
`venv/Scripts/python -c "import hermes_cli; print(hermes_cli.__file__)"`，应指向
`hermes-agent\hermes_cli\__init__.py`；若指向 `venv\Lib\site-packages\...`，说明旧副本还在遮蔽，
更新等于没生效。也可以在 execute_code 里直接 `import hermes_cli` 打印 `__file__` —— 那是 live 进程，
能证明"当前这个会话跑的就是新代码"。site-packages 里残留 `hermes_cli` 目录 = 旧副本必须清掉；
只剩一个 262 字节的 `hermes` 启动器文件是无害的。

**重装/更新的落点证据**：`venv/Scripts/hermes.exe` 的 mtime、`site-packages/hermes_agent-<ver>.dist-info`、
`config.yaml` 的 `_config_version` 是否等于代码里 `DEFAULT_CONFIG['_config_version']`（可在 venv 里 import 比对）。

## 七、桌面版（Hermes Agent CN Desktop）是另一套，别混在一起

本机同时装了两份 Hermes，**互不相通**：

| | 命令行这份（主用） | 桌面版 |
|---|---|---|
| 位置 | `C:\Users\<user>\AppData\Local\hermes` | `D:\Hermesstudio\Hermes Agent CN Desktop` |
| 自己的一份 home | `hermes` | `data\hermes-home`（config/记忆/skills 都是独立一套） |
| 版本查法 | `hermes --version` | 外壳 `(Get-Item '<exe>').VersionInfo.ProductVersion`；内核 `cat data\current.json` |

- 桌面版是 Tauri 外壳 + **managed runtime**（内核）：外壳在安装根目录，内核在 `data\versions\<ver>\`，
  当前指向记在 `data\current.json`（`runtimeVersion`/`kernelVersion`/`executablePath`）。
- **内核与外壳是绑定的，别只换内核。** 启动时 `install_bundled_runtime_if_needed` 只在「内核号相同且修订更高」
  时保留已装内核，其余情况一律用**包内捆绑内核**（`bundled-runtime\stable-<platform>-<arch>.json` + zip）覆盖回装。
  实证：把 `data\versions` 换成 0.20.0-cn.9 并写好 current.json，桌面版一启动就把 current.json 改回
  `source: bundled` 的 0.19.0-cn.7（还顺手把 0.20.0 记成 previousRuntimeVersion）。
- 要给桌面版上新内核，唯一硬路径 = 替换 `bundled-runtime\` 里的 manifest+zip（同名同源，app 照样
do Ed25519 验签 + sha256 校验 + 自检），属于跨外壳版本混搭、作者未声明支持 → **先问用户再动**。
- 官方更新源：外壳 `https://desktop.hermesagent.org.cn/latest.json`（国内直连，不用代理）；
  内核 `https://github.com/Eynzof/Hermes-CN-Core/releases/latest/download/stable-win32-x64.json`（GitHub，走代理 `127.0.0.1:17890`）。
- **一版外壳只配一条内核线**：外壳 0.7.0 ↔ 内核 0.19.0-cn.7；内核 0.20.0-cn.9 配的是只有 staging 原型包的 0.8.x。
  所以"桌面版能不能升级"要看**外壳**版本号，不是看内核 channel 里有没有新版本。
- **外壳自动回滚后不会收拾桌面版自己的包装文件**：2026-09-10 实测，手工换内核时改过的
  `data\desktop-bin\hermes.bat|.cmd` 会一直指着已被弃用的新内核 exe；外壳回滚只改 `current.json`。
  回滚后必须手动把 `desktop-bin\hermes.bat|.cmd.bak-<旧ver>` 复制回去，否则命令行会拉起一个"当前并未激活"的内核。
- 2026-09-10 完整实测时间线：09:40 命令行那份更新成功（0.21.1 / HEAD ae43fd6）；09:53 用户说"给它也升级了吧"
  → 09:57 下载 0.20.0-cn.9 → 10:03 解包+改 current.json → 10:05:55 桌面版启动即用 bundled 内核回装 → 10:07:28
  current.json 被改回 0.19.0-cn.7。结论：外壳 0.7.0 只吃自查过签的 bundled 内核，手工换内核必被回滚。
- 下载/替换内核的完整可复刻脚本：`references/cn-desktop-runtime.md`。
- **历史查询要跨三份会话库**：桌面版自己一份 `data\hermes-home\state.db`，另外还有 `C:\Users\<user>\.hermes-web-ui\hermes-web-ui.db`。用户问"我是不是给你发过 X""你还记得吗"时 `session_search` 只覆盖当前 profile 那份，必须再直接查这三份库的 `messages` 表（`WHERE role='user' AND content LIKE '%关键词%'`，多试几个近义关键词），否则会答错"没发过"。
- **把技能装到 D 盘不要走 junction**：本机 `New-Item -ItemType Junction`（PowerShell）与 `mklink /J` 建 C:→D: 都会 Access denied（git-bash 里 `cmd //c mklink` 还会被吃成交互式 cmd）。正确做法是外部技能目录：`hermes config set skills.external_dirs '["D:/a2e-skills"]'`，布局 `<external_dir>/<skill名>/SKILL.md`；改完**新会话**才生效，`hermes skills list` 能看到（显示 local/enabled）。

## 参考

- `references/this-machine.md` — 本机实测数据：路径、镜像地址、版本时间线、固定探测命令
- bundled 的 `hermes-agent` skill 里有 `references/update-windows-pitfalls.md`，
  但那份**假设 `hermes update` 能用**（讲的是 CRLF 警告、stash、超时），本机不适用，以本 skill 为准
