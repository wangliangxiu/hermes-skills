# `hermes update` — Windows Pitfalls

On Windows (git-bash / MSYS), `hermes update` has specific issues that don't
occur on Linux/macOS. This reference documents what to expect and how to
recover.

## Symptoms

### 1. CRLF warnings (cosmetic, safe)

```
warning: in the working copy of 'scripts/install.sh', LF will be replaced by CRLF the next time Git touches it
```

~50 such warnings during update. Caused by git's `core.autocrlf` on Windows.
The repo's `.gitattributes` normalizes on commit. **Safe to ignore.**

### 2. `hermes.exe` rename failure

```
Could not quarantine hermes.exe: [WinError 32] 另一个程序正在使用此文件
```

The running Hermes process holds a lock on its own `.exe`. Pip tries to
rename it during dependency update and fails. **Non-fatal** — pip still
installs the new packages; only the `.exe` stub rename fails. Next Hermes
start uses the correct binary.

### 3. Timeout on Rust/C extension compilation

```
[Command timed out after 300s]
```

`pydantic-core`, `cryptography`, `pywin32`, `pillow`, and
`google-api-python-client` compile C/Rust extensions during install. On a
laptop/i5 these can take 5-10 minutes. The `hermes update` default timeout
(300s) may not be enough.

**Workaround:** Run `hermes update` directly from a terminal (not through
the agent's `terminal` tool) so there's no timeout guard, or manually run
pip install afterward:

```bash
cd ~/AppData/Local/hermes/hermes-agent
source venv/Scripts/activate
pip install -e ".[all]"
```

### 4. Stash snapshot preserved

```
Saved working directory and index state On main: hermes-update-autostash-...
Stash ref: c376...
Your stashed changes are preserved — nothing is lost.
Restore your changes later with: git stash apply <ref>
```

The updater auto-stashes local changes before pulling, then pops them. If
the pop conflicts, the stash is left intact. Commands:

```bash
cd ~/AppData/Local/hermes/hermes-agent
git stash list                              # see all stashes
git stash apply <ref>                       # re-apply
git stash drop <ref>                        # clean up after confirming
```

### 5. Fork upstream prompt

```
Your fork is not tracking the official Hermes repository.
Add official repo as 'upstream' remote? [Y/n]:
```

On git-bash with non-ASCII username (使用者), this prompt may hang or
display garbled. Hermes auto-defaults to `Y` after a timeout. To add
upstream manually:

```bash
git remote add upstream https://github.com/NousResearch/hermes-agent.git
```

### 6. Divergent history → hard reset

```
Fast-forward not possible (history diverged), resetting to match remote...
```

If the local clone was from a mirror (e.g. `cnb.cool`) and the official
repo diverged, the updater does a hard reset to match the remote. Any
local commits are in the stash.

## Pre-update Snapshot

The updater creates a pre-update snapshot at
`<hermes_home>/pre-update-snapshots/<timestamp>/`. Contains:

- Full git diff (`git diff HEAD`)
- Untracked files list
- `config.yaml` and `.env` backups
- Installed packages list (`pip freeze`)

To restore: `hermes update` doesn't auto-restore; manual recovery from
the snapshot directory.

## Update Verification

After update, verify:

```bash
hermes --version                    # should show new version + "Up to date"
```

If the version didn't change, the pull may have failed. Check git log:

```bash
cd ~/AppData/Local/hermes/hermes-agent
git log --oneline -1                # newest commit hash
```

## 实测记录：`hermes update` 完全失效的一种装法（2026-09-10，本机）

### 症状

```
$ hermes version
Hermes Agent v0.19.0 (2026.7.20) · upstream ae43fd6d · local b7bed241 (+18936 carried commits)
Install method: unknown

$ hermes update --check          # 仓库目录里跑也一样
✗ Not a git repository — cannot check for updates.
```

### 根因（查出来的三层）

1. **跑的是 site-packages 副本，不是仓库源码。** 从任意非仓库目录执行
   `venv/Scripts/python.exe -c "import hermes_cli; print(hermes_cli.__file__)"`
   → 指向 `venv\Lib\site-packages\hermes_cli\__init__.py`（该装法是非可编辑安装，
   包文件被复制进 site-packages，且与仓库里的 md5 不一致）。
   **仓库里的代码根本没生效**——本机仓库已是 8-19 的代码，实际运行的是 7-27 装进去的旧副本。
2. 更新器用 `_m().PROJECT_ROOT / ".git"` 判断仓库（见 `hermes_cli/update_cmd.py`
   约 2712 行）。PROJECT_ROOT 由已安装模块位置推导 → 落在 site-packages，
   那里没有 `.git`，于是报"不是 git 仓库"。
3. 官方更新路径本身会把它转成 editable 安装（源码里写明
   `hermes update` 执行 `uv pip install -e .[all]`），editable 之后
   PROJECT_ROOT = 仓库，`hermes update` 才会恢复正常。

### 结论：这类装法只能手动更新

```bash
cd ~/AppData/Local/hermes/hermes-agent
git tag -f hermes-rollback HEAD          # 先留回滚点
git fetch --all --tags
git reset --hard origin/main
venv/Scripts/python.exe -m pip install -e ".[all]"   # 失败就退回 -e .
venv/Scripts/hermes.exe config migrate
venv/Scripts/hermes.exe --version
```

关键：**必须 `pip install` 一次**（并清掉 site-packages 里旧的包副本，
否则新旧两份并存会互相遮蔽），光 `git reset` 不会改变实际运行的代码。

### 其他实测要点

- 本机仓库跟踪的是**国内镜像** `cnb.cool/hermesagent-cn/hermes-agent-cn-mirror`
  （origin 和 mirror 同一地址）。**直连可用，不需要代理**——实测
  `env -u https_proxy -u http_proxy git fetch --dry-run origin main` 成功。
- 仓库工作区那批"改动"（几十个 .sh）全是权限位变化 `100755 → 100644`，
  `git diff --stat` 显示 0 行增删。`git config core.fileMode false` 一次搞定。
- **浅克隆陷阱**：`.git/shallow` 存在时 `git rev-list --count HEAD..origin/main`
  只会数出 1，严重低估差距。本机真实差距是 **9532 个提交**——用
  `api.github.com/repos/NousResearch/hermes-agent/compare/<local_sha>...main`
  或对比 release tag 才准。判断"要不要更新"前先确认不是浅克隆。
- 版本号判断也别只看 PyPI：PyPI 停在 0.19.0，但 main 上已经跑到 v0.21.x，
  差距看 GitHub releases（`/releases`，含结构化 changelog）。
