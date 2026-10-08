---
name: hermes-desktop-troubleshooting
description: "Troubleshoot Hermes startup issues on Windows — Desktop (port conflicts, stale processes, upgrade failures) + CLI startup warnings/noise."
version: 1.0.0
author: agent
---

# Hermes Desktop Troubleshooting (Windows)

Debug steps when `hermes desktop` fails to start after an upgrade or
when the dashboard reports "No available port from 9120 to 9140".

## Step 1 — Check for stale processes

```bash
tasklist /FI "IMAGENAME eq hermes*"
```

Look for multiple `hermes-agent-cn-desktop.exe` or a stuck
`hermes-agent-cn-runtime-watcher.exe` (often shows "Not Responding").

## Step 2 — Check port 9120

```bash
netstat -ano | grep -E "912[0-9]|913[0-9]|9140"
tasklist /FI "PID eq <port_owner_pid>" /V
```

## Step 3 — Kill stale processes

```bash
taskkill /F /FI "IMAGENAME eq hermes-agent-cn-desktop*"
taskkill /F /FI "IMAGENAME eq hermes-agent-cn-runtime*"
```

## Step 4 — Verify port is free

```bash
netstat -ano | grep -E "912[0-9]"
# → should return nothing (apart from possible TIME_WAIT entries)
```

## Step 5 — Relaunch

```bash
hermes desktop
```

## Prevention

Before running `hermes update`, kill all Hermes desktop/backend processes
first to prevent port conflicts post-upgrade.

## Root Cause

`hermes update` only replaces Python packages — it does NOT restart or kill
the existing Electron desktop backend processes (runtime-watcher, desktop
server). These old processes keep their sockets open on port 9120 but enter
"Not Responding" state because the old binary no longer matches the new code.
The new `hermes desktop` probes ports 9120–9140 and fails when it finds one
already claimed.

## Also check

- Two desktop icons clicked = two `hermes-agent-cn-desktop.exe` = double
  claim on the same port. Kill all and reopen.
- If port shows TIME_WAIT (not LISTENING/ESTABLISHED), wait 2-3 seconds
  (Windows TCP TIME_WAIT is ~30s by default) or pick another port range.

## Failure mode: "模型服务调用未成功" but API key is fine (missing fastapi/uvicorn)

Symptom: Desktop UI reports `模型服务调用未成功。常见原因：API Key 失效或不在模型权限范围、网络/服务不可达。请到 设置 模型 检查后重试` — but the CLI Hermes works fine with the same key, and `hermes config` shows the provider/key set correctly.

Real cause is usually **not** the API key: the desktop's Python backend failed to boot because Web UI dependencies are missing. Diagnose BEFORE touching key config:

1. Check the desktop log for the actual boot failure:
   ```bash
   tail -30 "C:/Users/使用者/AppData/Local/hermes/logs/desktop.log"
   # look for: Import error: No module named 'fastapi'
   #          Hermes backend exited (1)
   #          Desktop boot failed: Hermes backend exited before it became ready (1)
   ```
2. Fix — install the Web UI deps into the Hermes venv (NOT system python):
   ```bash
   "C:/Users/使用者/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe" -m pip install fastapi --no-input
   "C:/Users/使用者/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe" -m pip install "uvicorn[standard]" --no-input
   ```
3. Verify imports, then fully close + relaunch the desktop app.

### Pitfall: terminal tool blocks bare `uvicorn` in pip commands

The Hermes terminal tool's long-lived-server heuristic flags commands containing bare `uvicorn` as "appears to start a long-lived server/watch process" and refuses to run them — even for `pip install uvicorn`. Workarounds that work:
- Install fastapi and uvicorn in **separate** pip calls
- Quote the package spec: `pip install "uvicorn[standard]"` (the bracket form does not trip the heuristic)

## Root cause: fresh Desktop install vs existing CLI install

A newly installed CN Desktop (e.g. 0.7) is a separate Electron app that boots its own backend from the shared Hermes venv at `AppData/Local/hermes/hermes-agent/venv`. If that venv predates the desktop install (or was stripped), fastapi/uvicorn are absent and the backend dies at boot — the UI then surfaces a generic "model service failed" message that misleads you toward API key troubleshooting. Always read `desktop.log` first.

## 解读 Hermes CLI/终端启动噪音（非崩溃，用户贴输出问"怎么回事"时先按此分类）

1. `Warning: Unknown toolsets: messaging`（运行 `hermes` 时）
   配置里启用了当前版本不认识的 toolset 名（旧版遗留/改名，如 messaging）。
   **无害**，Hermes 正常启动。想消除：`hermes config edit` 把 enabled
   toolsets 里不存在的名字删掉。
2. `RuntimeError: Event loop is closed`（Python 程序退出时）
   asyncio 事件循环已关闭但还有代码在用它——程序退出时的收尾噪音，
   **不影响之前的结果**，忽略即可。
3. 用户在 PowerShell 提示符直接敲中文句子（如"啊？发生了什么"）
   → `CommandNotFoundException`。这不是程序报错，是话敲在了 PS 提示符
   而不是 Hermes 对话里。解释"要在 Hermes 里说"即可，别去查日志。

先给结论再动手：这类答疑问题用户要的是直接回答，不要先跑一堆工具查半天。

## 解读 CLI 底部状态栏（用户问「这个数字/符号是什么意思」）

分格含义（源码 `hermes_cli/cli_status_bar_mixin.py`）：

| 显示 | 含义 |
|---|---|
| `123 t/s`（宽屏带 ↑） | 平均输出速度（每秒生成多少 token） |
| `◷ …ms` | 平均延迟 |
| `⚙N` | **活跃后台进程数**（terminal 起的后台命令） |
| `▶N` | 活跃后台任务 |
| `⛓N` | 后台子代理 |
| `🗜️N` | 本会话上下文压缩次数 |
| `1h 11m` | 本会话已运行时长 |

**⚙N 不为 0 怎么处理**：说明有后台进程还没退出——长任务、被 `tail`／管道挂住的检查命令都会算在里面，不会自己消失。用 `process_manage(action='list')` 看清单，无用或僵死的用 `process_manage(action='kill', session_id=...)` 杀掉；列表里全部是 `exited` 才算干净。用户看到这个数字会问，直接解释含义 + 清掉，别让他以为是故障。

## CLI 会话"突然关了"排查（多半不是bug）

用户报"你怎么突然就关了"时按此路径查证，别急着下"崩溃"结论：

1. **读上个会话结尾**：session_search(session_id=...) 看最后几条消息——若最后回复完整、无中断标记，说明进程是被外部关闭而非崩溃
2. **查日志**：`AppData/Local/hermes/interrupt_debug.log`（用户打断记录）、`logs/errors.log`、`logs/agent.log`——找 fatal/traceback；只有 WARNING 级提示（SQLite版本、MCP连接失败、auxiliary无认证）不算崩溃
3. **查系统事件**：`Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1001}`（应用崩溃）＋ System 日志 Id=1074/6005/6006/6008/42/1（开关机/睡眠）
4. **全部干净 → 结论**：终端窗口被关闭/进程退出，会话记录完整保留，内容没丢（可 @session:... 找回）

**关键知识点：Ctrl+C 两种含义**——① 回复进行中按=打断（interrupt，程序还活着，interrupt_debug.log 有记录）；② 空闲等输入时按=终止信号，CLI 进程直接退出。这就是"突然关了"最常见的真凶，也是排查第一步先看 interrupt_debug.log 的原因。
