# 装 gh 并登录（Windows，供提交 issue/评论用）

## 1. 拿下载直链（不需要 gh 自己）

```
https://api.github.com/repos/cli/cli/releases/latest
```

挑 `name` 以 `windows_amd64.zip` 结尾的 asset，用它的 `browser_download_url`，并记下 `size` 用来比对。

**下载和查 API 都用 python urllib，不要用 curl**：本机 MSYS 里 curl 常取不到响应正文（直连/代理都可能是 0 字节），
也看不到实时速率，容易误判成「网断了」。几十 MB 前台直连下就行（实测 5 MB/s 上下）；
几百 MB 或明显慢的加代理 `HTTPS_PROXY=http://127.0.0.1:17890 HTTP_PROXY=... ALL_PROXY=...` 并放后台。

```python
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=25) as r, open(dest, "wb") as f:
    while True:
        b = r.read(262144)
        if not b:
            break
        f.write(b)
```

校验：`zipfile.ZipFile(z).testzip() is None` 才算完整；解压完删掉安装包。

## 2. 解压到 D 盘 + 加用户 PATH（winreg 精确改，别用 setx）

解压到 `D:\tools\gh\`，可执行文件在 `D:\tools\gh\bin\gh.exe`。

```python
import winreg, ctypes
entry = r"D:\tools\gh\bin"
k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                   winreg.KEY_READ | winreg.KEY_WRITE)
cur, typ = winreg.QueryValueEx(k, "Path")          # 原值类型通常是 REG_EXPAND_SZ
if entry.lower() not in [p.lower() for p in cur.split(";")]:
    rest = [p for p in cur.split(";") if p.strip()]
    winreg.SetValueEx(k, "Path", 0, typ, ";".join([entry] + rest))   # 插到最前，避免被旧目录抢先
ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, "Environment", 0x0002, 5000,
                                         ctypes.byref(ctypes.c_long()))
```

- **必须沿用查询到的 `typ`**：把 `REG_EXPAND_SZ` 写成 `REG_SZ`，PATH 里的 `%USERPROFILE%` 之类就不再展开。
- 别用 `setx`：会截断长 PATH，`/M` 还要管理员。
- 改完当前已开着的终端仍是旧环境；要立刻用就写绝对路径调 `D:\tools\gh\bin\gh.exe`，新窗口才认裸命令名。
- 验证：`"D:/tools/gh/bin/gh.exe" --version`。

## 3. 设备码登录（agent 能代办到用户授权那一步为止）

直连 `github.com/login/device/code` 会超时（`api.github.com` 通、登录那个 IP 不通）→ **该条命令单独挂代理**：

```bash
HTTPS_PROXY=http://127.0.0.1:17890 HTTP_PROXY=http://127.0.0.1:17890 ALL_PROXY=http://127.0.0.1:17890 \
GH_BROWSER=none "D:/tools/gh/bin/gh.exe" \
  auth login --hostname github.com --git-protocol https --web --skip-ssh-key
```

- 这是交互式 CLI：用 `terminal(background=true, pty=true)` 起，再用 `process(action="submit")` 回答问句
  （`Authenticate Git with your GitHub credentials?` → `y`）。回车必须用 submit：Windows PTY 上 `write` 加 `\n`
  不会被当成行结束，提示会一直不返回。
- 它随后打印一次性码（形如 `XXXX-XXXX`）并等授权。从 `process(action="log")` 读出来告诉用户
  （`poll` 只给预览、可能看不全），让他自己打开 `https://github.com/login/device` 输码。
  一次性码是 gh 明确打印给用户的东西，可以转述。
- `GH_BROWSER=none` 会让它开不了浏览器（这是故意的，防止在 agent 环境里乱弹窗），
  它会改成提示"请手动打开这个 URL"并继续轮询，不影响登录。
- **账号密码永不代填、也不要索取**；用户没有 GitHub 账号就让他先注册再输码。
- 授权成功后先 `gh auth status` 读回确认，再开始提交。
