# Git for Windows 安装实录 (2026-06-27)

## 用户环境
- 系统：Windows 11 中文版
- 安装盘：D 盘
- 用户：使用者 (甄der)
- 用户特征：中文用户，英文安装界面看不懂

## 下载地址
https://github.com/git-for-windows/git/releases/download/v2.48.1.windows.1/Git-2.48.1-64-bit.exe

也可以让用户访问 git-scm.com/download/win 自动下载

## 安装页面实录

| # | 页面英文标题 | 中文说明 | 操作 |
|---|-------------|---------|------|
| ① | Welcome to the Git Setup Wizard | 欢迎页 | Next（下一步） |
| ② | Select Destination Location | 选安装路径 | Browse → D:\Git → Next |
| ③ | Select Components | 选组件 | 默认不动 → Next |
| ④ | Select Start Menu Folder | 开始菜单文件夹 | 默认不动 → Next |
| ⑤ | Choosing the default editor | 选默认编辑器 | 默认不动（Vim）→ Next |
| ⑥ | Adjusting your PATH environment | 配置PATH | ⚠️ 实际遇到只有2个选项（Let Git decide / Override default branch），没有预期的3个选项。选"Let Git decide" → Next |
| ⑦ | Choosing HTTPS transport backend | HTTPS后端 | 选 OpenSSL（默认）→ Next |
| ⑧ | Configuring the line ending conversions | 换行符设置 | 选第一个（默认）→ Next |
| ⑨ | Configuring the terminal emulator to use with Git Bash | 终端模拟器 | 选 Use MinTTY（默认）→ Next |
| ⑩ | Choose the default behavior of `git pull` | git pull 行为 | 选 Default（默认）→ Next |
| ⑪ | Choose a credential helper | 凭据管理器 | 选 Git Credential Manager Core（默认）→ Next |
| ⑫ | Configuring extra options | 额外选项 | （可能没有这页）默认 → Next |
| ⑬ | Install | 安装 | 点 Install |
| ⑭ | Completing | 完成 | 勾选 Launch Git Bash → Finish |

## 遇到的 UI 差异

**第⑥页 Adjusting PATH：** 文档上说的3个选项和用户实际看到的2个选项不同。
- 用户说："我这边只有一个let git decide选项和override the default branch name for new repositories"
- 说明某些版本的 Git 安装器把 PATH 选项和分支名选项合并或分页了
- 应对策略：让用户描述他看到的选项，不要假设版本一致

## 安装后验证

打开 Git Bash，应看到提示符如：
```
使用者@LAPTOP-561D7E1Q MINGW64 ~
$
```

## git-bash 路径

安装到 `D:\Git` 的话，bash.exe 在 `D:\Git\bin\bash.exe`
git-bash.exe 在 `D:\Git\git-bash.exe`

## 路径查找方式

| 方式 | 命令/操作 | 结果 |
|------|-----------|------|
| cygpath -w /usr/bin/bash | 在 Git Bash 中运行 | `D:\Git\usr\bin\bash.exe` ✓ |
| cygpath -w / | 在 Git Bash 中运行 | `D:\Git\` |
| 开始菜单搜 Git Bash → 属性 | GUI 操作 | 看"目标"路径 |
| 用户直接拖拽附件 | 聊天窗口 | 用户自发行为，也有效 |

**实际验证：** 此用户环境（Git 2.48.1, D:\Git 安装），结果如下：
- `cygpath -w /usr/bin/bash` → `D:\Git\usr\bin\bash.exe`
- `cygpath -w /` → `D:\Git\`

## config.yaml 配置

在 `C:\Users\使用者\AppData\Local\hermes\config.yaml` 末尾添加（注意缩进）：

```yaml
  git_bash_path: D:\Git\usr\bin\bash.exe
```

**注意：** 必须在行首加**两个空格**缩进（YAML 格式要求），否则 agent 读取时会失败。

## 注意事项

- 装完后 Hermes Agent 需要配置 `HERMES_GIT_BASH_PATH` 环境变量才能使用 terminal 工具
- 如果用户通过开始菜单搜索能打开 Git Bash，但 agent 找不到，需要在 Hermes 的 .env 或 config.yaml 中设置 `HERMES_GIT_BASH_PATH=D:\\Git\\bin\\bash.exe`
- **路径确认技巧：** `which bash` 在 Git Bash 中输出 `/usr/bin/bash`，需要 `cygpath` 转换为 Windows 真实路径
