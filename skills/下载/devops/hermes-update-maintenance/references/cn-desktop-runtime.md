# 桌面版（CN Desktop）内核：查版/换版/回滚

## 路径

```
APP   = D:\Hermesstudio\Hermes Agent CN Desktop
当前指向  APP\data\current.json          （runtimeVersion / kernelVersion / executablePath / previousRuntimeVersion）
内核目录  APP\data\versions\<ver>\        （exe + _internal\ + node\ + tui\ + manifest.json）
下载缓存  APP\data\downloads\<ver>.zip
命令行包装  APP\data\desktop-bin\hermes.bat|.cmd （写死了内核 exe 的完整路径，换内核要一起改）
捆绑内核  APP\bundled-runtime\stable-win32-x64.json + hermes-agent-cn-runtime-win32-x64.zip（启动时以此为准）
外壳日志  APP\data\hermes-home\logs\gui.log / agent.log
```

## 查版本

```bash
cat "APP/data/current.json"
powershell -NoProfile -Command "(Get-Item 'APP\hermes-agent-cn-desktop.exe').VersionInfo | fl ProductVersion"
# 官方源
curl -s https://desktop.hermesagent.org.cn/latest.json                      # 外壳最新版
curl -s -x http://127.0.0.1:17890 https://api.github.com/repos/Eynzof/Hermes-CN-Core/releases?per_page=5
```

## 换内核（复刻 install_runtime_zip，已验证可用）

1. 下载官方 zip + 该 tag 的 `stable-win32-x64.json`（走代理）：
   `https://github.com/Eynzof/Hermes-CN-Core/releases/download/runtime-v<ver>/hermes-agent-cn-runtime-win32-x64.zip`
2. 校验：zip 的 sha256 必须等于 manifest 里的 `sha256`；manifest 的 Ed25519 签名用外壳源码里的内置公钥验签
   （`src/process/runtime.rs` 的 `FALLBACK_PUBLIC_KEY_PEM`；payload = 12 个字段按 schemaVersion,channel,runtimeVersion,
   kernelVersion,runtimeFlavor,runtimeRevision,platform,arch,artifactUrl,sha256,sourceRepo,sourceCommit 用 `\n` 连接）。
   venv 里有 `cryptography`，可直接 `load_pem_public_key` + `verify`。
3. 解包 zip（4732 项，根目录即内核目录内容）→ `data\versions\<ver>\`（建议先解到 `versions\.staging-<ver>` 再改名），
   把 manifest 复制成该目录的 `manifest.json`。
4. 自检（外壳自己也这么干）：`<exe> dashboard --help`，cwd = 内核目录，
   环境 `HERMES_DISABLE_LAZY_INSTALLS=1`、`HERMES_DASHBOARD_PREWARM_AGENT=0`，180s 超时，退出码必须 0。
5. 写 `data\current.json`（camelCase，schemaVersion 2，platform=win32/arch=x64，source="update"，
   installedAt=RFC3339 UTC，sourceRepo/sourceCommit/artifactSha256/previousRuntimeVersion）。
6. 改 `data\desktop-bin\hermes.bat|.cmd` 指向新 exe；zip 复制进 `data\downloads\<ver>.zip`。

⚠ **只做上面这一步不够**：桌面版启动时会被 `bundled-runtime\` 里那份内核覆盖回去（见 SKILL.md 第七节）。
要让新内核留下，必须把 `bundled-runtime\stable-win32-x64.json` 和同名 zip 也换成新版（先备份原文件）。
换完直接启动桌面版：它会自己验签、解包、自检、激活，并把 `dashboard web_dist`、`bundled-skills`、
`bundled-plugins` 从外壳资源同步进新内核目录；`source` 会是 `bundled`。

## 回滚

- 还原 `bundled-runtime\` 备份 + 把 `data\current.json` 指回旧版本目录（或从 `current.json.bak-<旧ver>` 还原）。
- 外壳自身的运行时页面也有"回退"按钮，靠 current.json 里的 `previousRuntimeVersion`。
- 本机已放好一键脚本：`C:\Users\使用者\Desktop\Hermes更新\回滚桌面版内核.bat`。

## 启动/观察

```bash
# 启动（start / 直接 cmd start 在 git-bash 下会只开个 cmd 不启动 app）
python -c "import subprocess;subprocess.Popen([r'APP\hermes-agent-cn-desktop.exe'],creationflags=0x00000008)"
# 看它到底跑了哪个内核
python -c "import psutil;[print(p.pid,p.info['exe'],p.info['cmdline']) for p in psutil.process_iter(['pid','exe','cmdline']) if 'cn-runtime' in (p.info['name'] or '')]"
```
