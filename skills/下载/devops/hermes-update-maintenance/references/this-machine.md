# 本机 Hermes 安装实况（2026-09-10 实测）

## 路径

- Hermes home: `C:\Users\使用者\AppData\Local\hermes`
- 源码 checkout: `C:\Users\使用者\AppData\Local\hermes\hermes-agent`（含 `.git`，**浅克隆**）
- venv: `<源码>/venv/Scripts/`（这个 venv **有 pip**，可用 `venv/Scripts/pip list`）
- 包本体装在 `venv/Lib/site-packages`（`hermes_agent-0.18.2.dist-info`），
  但 `hermes version` 报 `Install method: unknown` → 更新器认不出仓库
- 配置：`config.yaml`（model.default / agent.image_input_mode / updates.pre_update_backup=false）、
  `.env`（DEEPSEEK_API_KEY）
- 技能目录：`skills/<category>/<skill>/`

## git 远端

| 名字 | 地址 | 代理 |
|---|---|---|
| origin / mirror | `https://cnb.cool/hermesagent-cn/hermes-agent-cn-mirror.git` | **不需要**（国内） |
| 上游官方 | `https://github.com/NousResearch/hermes-agent` | 需要 `-x http://127.0.0.1:17890` |

浅克隆：`.git/shallow` 存在（41 行），本地可见历史 18936 个提交。

## 固定探测命令

```bash
G=/c/Users/使用者/AppData/Local/hermes/hermes-agent
P=http://127.0.0.1:17890

# 本地状态 + 是否浅克隆（关键）
cd "$G" && ls -la .git/shallow; git log -1 --format="%h %ad %s" --date=short HEAD | cat
cd "$G" && git rev-parse --short HEAD; git rev-list --count HEAD

# 拉镜像 refs（免代理）
cd "$G" && timeout 240 git fetch --all --tags 2>&1 | tail -3
cd "$G" && git log -1 --format="%h %ad %s" --date=short origin/main | cat

# 上游真实差距（走代理；本地 git 计数可能是假的）
curl -s -x $P "https://api.github.com/repos/NousResearch/hermes-agent/commits/main" | grep -oP '"sha":"\w+"' | head -1
curl -s -x $P "https://api.github.com/repos/NousResearch/hermes-agent/compare/<本地HEAD sha>...main" | grep -oP '"total_commits":\s*\d+'
curl -s -x $P "https://api.github.com/repos/NousResearch/hermes-agent/releases?per_page=8"

# PyPI 线
curl -s https://pypi.org/pypi/hermes-agent/json | grep -oP '"version":"[^"]+"' | head -1
```

## 2026-09-10 实测状态

- `hermes version` → `v0.19.0 (2026.7.20) · upstream ae43fd6d · local b7bed241 (+18936 carried commits)`，
  `Install method: unknown`，Python 3.13.5
- 本地 HEAD `b7bed2419` = **2026-08-19**
- 镜像 `origin/main` `ae43fd6df` = 2026-09-10；GitHub main `a6474766c` = 2026-09-10（镜像慢几小时）
- **compare `b7bed2419...main` → `total_commits: 9532`**
  （而本地 `git log --oneline HEAD..origin/main` 只返回 1 条 —— 浅克隆伪影）
- PyPI 最新 `0.19.0`（2026-07-20）
- 发行版时间线：v0.20.3(8-17) → v0.20.4(8-18) → v0.20.5(8-21) → v0.20.6(8-27) →
  **v0.21.0(8-31，大版本，body 39KB)** → v0.21.1(9-7，补丁汇总)
- v0.21.1 自述：自 v0.21.0 起 **5139 个非合并提交 / 4364 文件 / +601014 −768419 / 632 个已合并 PR**
- v0.21.0 亮点（挑与本机使用者相关的）：cron 有记忆 + `continuity` + **monitor 模式无变化时跳过 LLM（省钱）**、
  `delegate_task` 可中途 steer/提前停/显示本次成本 + 默认 250 轮 10 并发、
  桌面端 Bot Mode（多 agent 群聊/头像）、`hermes peer`（agent 互发消息）、
  启动与文件操作性能优化、MCP 授权与 cron 投递修复

## 本会话已完成 / 未完成

- 已完成（非破坏性）：`git config core.fileMode false`（脏文件 69 → 0）、`git fetch --all --tags`（对象已下载）
- **未做（等用户同意）**：`git reset --hard origin/main`、`venv/Scripts/pip install -e .`、`hermes config migrate`
- 更新前必须先退出 Hermes（本会话里 `hermes.exe` PID 25732 在跑，会撞文件锁）
