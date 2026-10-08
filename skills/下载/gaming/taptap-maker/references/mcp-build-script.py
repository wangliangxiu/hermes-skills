# TapTap Maker MCP Build Script (Python)

本文件包含完整的 Python 脚本，用于在 Windows 上通过 MCP JSON-RPC 协议触发 TapTap Maker 云端构建。

## 完整构建脚本

```python
import subprocess, json, os, time, threading

project_dir = r"C:\Users\使用者\Desktop\合成大西瓜"  # 改为你的项目路径

# 1. 创建短路径（绕开中文编码问题）
subprocess.run(["cmd.exe", "/c", "subst", "S:", project_dir], capture_output=True)

# 2. 启动 MCP server
proc = subprocess.Popen(
    ["cmd.exe", "/c", "npx.cmd", "-y", "@taptap/maker"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    cwd="S:\\", text=True, bufsize=0
)

# 3. 后台线程收集输出
received = []
lock = threading.Lock()
def reader(stream):
    while True:
        try:
            line = stream.readline()
            if not line: break
            with lock: received.append(line.strip())
        except: break

t = threading.Thread(target=reader, args=(proc.stdout,), daemon=True)
t.start()

time.sleep(4)  # 等 npx 下载/启动

# 4. MCP 初始化握手（必须！）
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "hermes", "version": "1.0"}
    }
}) + "\n")
proc.stdin.flush()
time.sleep(3)

# 5. 触发构建
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {
        "name": "maker_build_current_directory",
        "arguments": {
            "target_dir": "S:\\",
            "entry": "main.lua",
            "scriptsPath": "scripts",
            "timeout_ms": 600000
        }
    }
}) + "\n")
proc.stdin.flush()

# 6. 等待结果（最多 120 秒）
for i in range(120):
    time.sleep(1)
    poll = proc.poll()
    if poll is not None:
        print(f"Process exited (code={poll})")
        break

# 7. 输出构建结果
with lock:
    for msg in received:
        try:
            p = json.loads(msg)
            if "result" in p and "content" in p["result"]:
                for c in p["result"]["content"]:
                    if c["type"] == "text":
                        print(c["text"])
        except:
            pass

proc.terminate()
proc.wait(timeout=3)
```

## 状态查询脚本

```python
# 在 initialize 之后，不调 build 而调 status:
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {
        "name": "maker_status_lite",
        "arguments": {"target_dir": "S:\\", "skip_remote_sync": False}
    }
}) + "\n")
```

## 关键参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `protocolVersion` | `2024-11-05` | MCP 协议版本，硬编码 |
| `target_dir` | `S:\\` | 项目根目录（用 subst 短路径） |
| `entry` | `main.lua` | 游戏入口脚本名 |
| `scriptsPath` | `scripts` | 脚本目录名 |
| `timeout_ms` | 600000 | 云端构建超时（10分钟） |

## 注意事项

1. **subst 映射需在每次脚本运行前创建**，不跨 session 持久
2. 构建成功后，TapTap 会自动启动日志 watcher（每 5 秒拉一次运行时日志）
3. 运行时日志在 `.maker/logs/runtime/` 目录下
4. 如果远端有新的 commit，构建前会自动 pull
5. 构建触发的 commit 消息固定为 `chore: wake maker build server`
