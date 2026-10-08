---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Manual MCP Protocol Interaction (When MCP Tools Aren't Directly Callable)

When Hermes's built-in MCP client has connected a server (`hermes mcp list` shows ✓ enabled) but the tools don't appear in your available tool list (e.g. in a CLI session), you can interact with the MCP server manually using JSON-RPC over stdin/stdout.

### The Pattern

```python
import subprocess, json, os, time

# 1. Start the MCP server as a subprocess
proc = subprocess.Popen(
    ["cmd.exe", "/c", "npx.cmd -y @taptap/maker"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    cwd="S:\\", text=True, bufsize=0  # use short path if Chinese chars
)

# 2. MCP standard initialize handshake
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "my-client", "version": "1.0"}
    }
}) + "\n")
proc.stdin.flush()
time.sleep(2)

# 3. Call a tool
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {
        "name": "maker_build_current_directory",
        "arguments": {"target_dir": "S:\\", "entry": "main.lua", ...}
    }
}) + "\n")
proc.stdin.flush()

# 4. Read responses (background thread recommended)
import threading
received = []
lock = threading.Lock()
def reader(stream):
    while True:
        line = stream.readline()
        if not line: break
        with lock: received.append(line.strip())

t = threading.Thread(target=reader, args=(proc.stdout,), daemon=True)
t.start()
```

### Key Rules

1. **Always `initialize` first** — MCP requires the standard initialization handshake (protocolVersion `2024-11-05`) before any tool call or list request.
2. **Use a background reader thread** — `stdout.readline()` is blocking. A daemon thread collects JSON-RPC responses as they arrive.
3. **Non-blocking read for peek** — use `os.set_blocking(fd, False)` to check pending output without blocking.
4. **Close stdin to signal end** — `proc.stdin.close()` or `process(action='close')` terminates the conversation.
5. **Remember MCP progress notifications** — some tools send progress via `$/progress` notifications before the final result.

### Chinese Path Workaround (Windows git-bash)

When the project path contains Chinese characters (e.g. `C:\Users\使用者\Desktop\合成大西瓜`), piping JSON-RPC through `cmd.exe` via git-bash will mangle characters. Use `subst`:

```python
import subprocess
subprocess.run(["cmd.exe", "/c", "subst", "S:", r"C:\Users\使用者\Desktop\合成大西瓜"])
# Then use S:\ as target_dir and cwd
proc = subprocess.Popen(
    ["cmd.exe", "/c", "npx.cmd -y @taptap/maker"],
    cwd="S:\\", ...
)
```

### Diagnostic: List Available Tools

```python
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
}) + "\n")
```

## Windows-Specific Guidance

On Windows, MCP server configuration has several pitfalls that don't occur on Linux/macOS, especially when using git-bash (MSYS) as the terminal:

### Path resolution: npx.cmd still needs node.exe on the system PATH

Even with an absolute path to `npx.cmd` in `command`, the `npx.cmd` launcher internally looks for `node.exe` through the **system PATH** (not git-bash's PATH). If the Node.js directory isn't in the system PATH, MCP subprocesses will fail silently.

**The reliable fix** — bypass `npx.cmd` entirely and invoke node directly:

```yaml
mcp_servers:
  example-server:
    command: "D:\\Nodejs\\node.exe"                          # direct path to node.exe
    args:
      - "D:\\Nodejs\\node_modules\\npm\\bin\\npx-cli.js"     # npx's JS entry point
      - -y
      - '@scope/package'
    env:
      PATH: "D:\\Nodejs;%PATH%"                               # ensure node is on PATH for npx internals
    enabled: true
```

**Why this works:** `npx.cmd` is just a batch file that runs `node npx-cli.js`. By passing the JS file directly to `node.exe`, you eliminate the system PATH dependency.

### MCP subprocesses don't inherit shell PATH

When Hermes spawns MCP server subprocesses, they get a **filtered environment** (see Security section). On Windows with git-bash, the subprocess gets the system environment, not the bash profile environment. This means:
- PATH from `~/.bashrc` or `~/.bash_profile` is **not** available
- Node/npm installed only in shell profile won't be found
- **Solution:** always use absolute paths or set `env.PATH` explicitly

### hermes mcp test and hermes mcp list have known bugs on Windows

- `hermes mcp test` crashes with `NameError: name 'StdioServerParameters' is not defined` — config IS saved, answer `y` to prompt.
- `hermes mcp list` may show `AttributeError: 'str' object has no attribute 'get'` — cosmetic, servers still work.

**Do not** rely on these CLI commands to verify MCP health on Windows. Verify by running the command directly:

```bash
# Manual verification: run the exact command Hermes would use
"D:\\Nodejs\\node.exe" "D:\\Nodejs\\node_modules\\npm\\bin\\npx-cli.js" -y @scope/package --help
```

### Hot-reload without restart

After modifying `mcp_servers` in `config.yaml`, use the in-session slash command:

```
/reload-mcp
```

This reloads MCP servers without closing the session. If the new tools still don't appear, a full `/reset` or restart may be needed.

### Full Windows MCP config reference

See the `hermes-agent` skill's `references/mcp-config-windows.md` for the complete troubleshooting guide:
- Python-based MCP connection testing with the `mcp` SDK
- Process-level verification (checking if the MCP subprocess started)
- Chinese Windows username encoding issues with PowerShell scripts
- Diagnostic decision tree for common failure modes

