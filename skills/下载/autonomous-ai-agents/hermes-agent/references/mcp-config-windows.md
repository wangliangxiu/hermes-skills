# Windows MCP 服务器配置参考

## 背景

在 Windows 中文系统上，`hermes mcp add` 命令存在两个问题：
1. **`StdioServerParameters` 未定义** — 连接测试阶段报 `NameError`，但可以跳过（回答 `y` 保存）
2. **交互式提示卡死** — `Save config anyway (y/N):` 在非交互式终端中无法自动处理

### 推荐做法：直接编辑 config.yaml + /reload-mcp 热加载

- `hermes mcp add` 的 `StdioServerParameters` bug 仅影响测试，配置会保存。但更稳定的做法是直接编辑 config.yaml
- 编辑完用 `/reload-mcp` 在会话中热加载，无需退出重启
```
C:\Users\<用户名>\AppData\Local\hermes\config.yaml
```

添加格式：
```yaml
mcp_servers:
  your-server-name:
    command: D:\Path\to\executable.exe   # 使用完整路径，避免 PATH 问题
    args:
    - -y
    - "@scope/package"
    enabled: true
  # ... 已有服务器保持不变
```

## 故障排除：当内置诊断命令不可靠时

`hermes mcp test` 和 `hermes mcp list` 在 Windows 上都有已知 bug，不能依赖它们来验证 MCP 工具是否正常。以下是**不依赖 CLI 命令的手动验证流程**：

### 步骤 1：确认依赖就绪

MCP 服务器通过子进程启动。先验证子进程自身能否独立运行：

```python
import subprocess, json

# tapmaker 示例：直接启动 npx 看能否跑起来
result = subprocess.run(
    ["D:\\Nodejs\\node.exe", "D:\\Nodejs\\node_modules\\npm\\bin\\npx-cli.js", "-y", "@taptap/maker", "--help"],
    capture_output=True, text=True, timeout=30
)
print(result.returncode, result.stdout[:500], result.stderr[:500])
```

**不要仅凭** `hermes mcp test` 报错就判断 MCP 配置有问题——那个命令本身有 bug。

### 步骤 2：直接用 Python 调用 MCP 包

如果 `mcp` Python 包已安装（`pip install mcp`），可以直接验证连接：

```python
import asyncio, json
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    params = StdioServerParameters(
        command="D:\\Nodejs\\node.exe",
        args=["D:\\Nodejs\\node_modules\\npm\\bin\\npx-cli.js", "-y", "@taptap/maker"]
    )
    async with stdio_client(params) as (read, write):
        # 发送 initialize 请求
        write.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n")
        write.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}
        }}) + "\n")
        await asyncio.sleep(2)
        print(await read.read())

asyncio.run(test())
```

返回带 `tools` 字段的 JSON → 配置正确。

### 步骤 3：软重启

修改 config.yaml 后，用 `/reload-mcp` 在会话中热加载，无需退出：

```
/reload-mcp
```

然后用 Hermes 的实际工具调用测试新 MCP 工具是否出现在可用工具列表中。

### 步骤 4：确认进程是否正常

如果 MCP 工具在会话中依然不可见，检查子进程是否成功启动：

```python
import psutil
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if any('tapmaker' in str(c).lower() for c in proc.info['cmdline'] or []):
            print(f"PID {proc.info['pid']}: {' '.join(proc.info['cmdline'][:3])}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
```

如果找不到 MCP 子进程，说明 Hermes 内部的 MCP 客户端无法启动它——通常是 `command` 路径或参数问题。

### 总结：诊断金字塔

| 现象 | 可能原因 | 验证方法 |
|------|----------|----------|
| `hermes mcp test` 报 `StdioServerParameters` 错 | CLI 命令 bug，无关配置 | 跳过，用步骤 2 直接测试 |
| `hermes mcp list` 报 `AttributeError` | CLI 命令 bug，无关配置 | 跳过，忽略该报错 |
| 直接运行 npx 命令失败 | node/npx 不在系统 PATH | 步骤 1，改绝对路径 |
| 步骤 2 连不上 | 包名错误或 MCP 服务器挂了 | 检查网络/包名 |
| 步骤 2 能连但 Hermes 里看不见 | 需要 reload 或 reset | 步骤 3 |
| 步骤 3 后还看不见 | 子进程没启动或 crash | 步骤 4 |

## 关键要点

### 命令路径用绝对路径
- 在 git-bash/MSYS 环境中，`npx`、`node` 等命令可能不在系统 PATH 中
- Hermes 的 MCP 子进程使用系统环境变量，不是 git-bash 的 PATH
- **解决方案**：在 `command` 字段写完整路径，如 `D:\\Nodejs\\npx.cmd`

### 当 npx.cmd 还是找不到 node 时的终极方案

即使 `command` 用了 `npx.cmd` 的绝对路径，`npx.cmd` 内部依然会去系统 PATH 找 `node.exe`。如果系统 PATH 里没有 Node.js 目录，MCP 子进程启动就会静默失败（Hermes 里表现为 "No MCP tools available"）。

**解决方案：直接指定 node.exe，绕过 npx.cmd 的 PATH 问题**

```yaml
mcp_servers:
  tapmaker:
    command: D:\Nodejs\node.exe                    # 直接用 node.exe
    args:
    - D:\Nodejs\node_modules\npm\bin\npx-cli.js    # npx 的 JS 入口
    - -y
    - '@taptap/maker'
    env:
      PATH: 'D:\Nodejs;%PATH%'                     # 显式传给子进程的 PATH
    enabled: true
```

原理：
1. `command` 直接指向 `node.exe`，不依赖 PATH 查找
2. 把 `npx-cli.js` 作为参数传给 node——这是 `npx.cmd` 内部做的事情，只是我们用绝对路径显式调用
3. `env.PATH` 确保 node 本身在子进程的 PATH 里，供 npx 内部脚本使用

**验证方法**：手动跑同样的命令看能否正常工作
```bash
"D:\Nodejs\node.exe" "D:\Nodejs\node_modules\npm\bin\npx-cli.js" -y @taptap/maker --help
```

**注意**：`node_modules\npm\bin\npx-cli.js` 路径是 Node.js 标准安装后的位置。不同版本可能路径不同，用 `ls "D:/Nodejs/node_modules/npm/bin/npx-cli.js"` 确认文件存在。

### `hermes mcp list` 的已知 bug
`hermes mcp list` 可能报 `AttributeError: 'str' object has no attribute 'get'`，来自 `mcp_config.py:497`。**不影响实际功能** — MCP 服务器仍然列出并正常工作。报错出现在列表渲染后，是 `tools` 配置解析的 bug，可以忽略。

### 重启生效
添加/修改 MCP 服务器后，需要：
- CLI 模式：退出重启 `hermes`，或在会话中输入 `/reset`
- Gateway 模式：`hermes gateway restart`
- 中途加载：在会话中输入 `/reload-mcp`

### Windows 中文路径的坑
- PowerShell 脚本写中文会因编码问题报 `UnexpectedToken` / `TerminatorExpectedAtEndOfString`
- 推荐用纯 ASCII 英文写 PowerShell 脚本，或改用 `cmd.exe` 的 `setx`
- `setx /M` 需要管理员权限，且 PATH 过长可能截断
- 推荐用 `[Environment]::SetEnvironmentVariable("Path", $newPath, "User")` 但脚本必须无中文字符
