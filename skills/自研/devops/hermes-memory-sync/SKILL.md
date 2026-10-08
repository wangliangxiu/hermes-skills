---
name: hermes-memory-sync
description: "Sync Hermes memory/skills across devices (private git repo)."
version: 1.0.1
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [hermes, memory, skills, sync, windows, git, junction]
    related_skills: [hermes-agent, hermes-desktop-troubleshooting]
---

# 跨设备同步 Hermes 记忆与技能（私有 Git 仓库方案）

## When to Use

- 使用者问"两台机器记忆怎么互通""记忆能不能同步"；
- 要在新机器（笔记本）上接入已有的 `hermes-brain` 仓库；
- `memories/` 或 `skills/` 看着像空目录 / 是链接 / 同步报冲突，需要定位；
- 排查完 Hermes 升级后记忆没跟上、或两台机器看到的内容不一致。

用户有两台以上机器（台式机 + 笔记本）时，让记忆和技能共用一份。
**官方 `hermes sync` 只管技能、且要登录 Nous Portal —— 不要拿它当记忆同步方案。**

## 本机（台式机 使用者）已搭好的结构

```
私有仓库  https://github.com/wangliangxiu/hermes-brain   (private)
本地副本  D:\hermes-sync\hermes-brain
目录链接  C:\Users\使用者\AppData\Local\hermes\memories  --JUNCTION-->  <repo>\memories
          C:\Users\使用者\AppData\Local\hermes\skills    --JUNCTION-->  <repo>\skills
一键同步  <repo>\同步.bat   （pull --rebase → add → commit → push）
笔记本说明 桌面\Hermes记忆同步-笔记本怎么做.txt
```

Hermes 仍然读写原来的 `%LOCALAPPDATA%\hermes\memories|skills` 路径，junction 透明；
实际文件在仓库里，改完双击 `同步.bat` 即可跨机。

## 仓库内约定

- `.gitattributes` = `* -text` 且仓库级 `core.autocrlf=false` —— **必须保持**，
  否则 Windows 的 CRLF 转换会让两台机器每次同步都产生成百上千行"假改动"。
- `.gitignore` 排除机器本地状态：`*.lock`、`skills/.usage.json`、`skills/.bundled_manifest`、
  `skills/.curator_*`、`skills/.archive/`。这些各机器各留一份，同步会互相打架。
- 仓库级（`--local`）设置：`user.name`、`user.email` 用 GitHub 匿名邮箱
  （`<id>+<login>@users.noreply.github.com`），不要把真实邮箱写进提交记录；
  `http.https://github.com.proxy=http://127.0.0.1:17890` 让 push/pull 走代理。
- git 凭据用 `gh auth setup-git` 装上的 helper，不要手动存 token。

## 新机器接入（笔记本）

1. 装 git + gh（gh 下 `cli/cli` release 的 windows_amd64.zip，解压把 `bin` 加进用户 PATH），
   `gh auth login --hostname github.com --git-protocol https --web --skip-ssh-key`
   （国内直连 github.com 会超时，先 `set HTTPS_PROXY=http://127.0.0.1:17890`），
   然后 `gh auth setup-git`。
2. `git clone` 到 `D:\hermes-sync\hermes-brain`，按上面"仓库级设置"配一遍。
3. 退出 Hermes，把原有目录**搬走备份**再建链接：
   `move "%LOCALAPPDATA%\hermes\memories" D:\hermes-sync\_旧备份\memories`
   `mklink /J "%LOCALAPPDATA%\hermes\memories" D:\hermes-sync\hermes-brain\memories`
   （skills 同理）。先 move 再 mklink，**不要**直接删原目录。
4. 双击 `同步.bat` 把该机独有的内容推上去；冲突让使用者拿给 Agent 解，别自己乱改。

## 坑

- **聊天记录（state.db）不要放进同步**：SQLite + WAL，两台同时写会坏库。
  要搬历史就用 Hermes 的迁移包单向搬。
- 建链接用 `mklink /J`（junction，普通用户权限即可）；
  用 `cmd //c` 从 git-bash 里调用时引号容易被吃掉，改从 python subprocess 调 `['cmd','/c','mklink','/J',link,target]`。
- 验证链接：`os.path.realpath(p)` + `cmd /c dir /AL`（应显示 `<JUNCTION>`）。
- `同步.bat` 末尾有 `pause`：非交互测试要么 `stdin=DEVNULL`，要么直接跑里面那三条 git 命令。
- 推送前扫一遍密钥：正则 `sk-…` 会误报 `task-…`/`risk-…` 这类词，
  命中要看"唯一字符数"——一片 x / 少于 3 种字符的基本都是文档占位符。
- 别把 `skills/.bundled_manifest` 一起同步：那份清单跟 Hermes 版本绑定。
