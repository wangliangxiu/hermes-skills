# .lnk 快捷方式解析技术笔记

## 背景

Windows 快捷方式 (.lnk) 文件是 Shell Link Binary File Format，结构复杂，包含目标路径、命令行参数、工作目录、图标位置等信息。深入理解可以帮助追踪捆绑软件的来源。

## 快速解析方法（推荐）

使用 Python 直接提取 .lnk 文件中的 ASCII 路径字符串：

```python
import re
with open('path/to/shortcut.lnk', 'rb') as f:
    data = f.read()

for m in re.finditer(rb'[\x20-\x7e]{8,}', data):
    s = m.group().decode('ascii', errors='replace')
    if ('\\' in s or ':' in s) and not s.startswith('--'):
        print(s)
```

**原理：** Windows .lnk 文件存储路径时使用 UTF-16LE 编码，路径中的字母在 UTF-16LE 中每个字符的低字节就是 ASCII 本身（高字节为0）。`re.finditer(rb'[\x20-\x7e]{8,}', data)` 能提取出所有连续 8 个以上可打印 ASCII 字符的区域，这些区域恰好就是 UTF-16LE 编码的 ASCII 字符串。

**注意：** 这种方法会漏掉纯 ASCII 以外的路径（如带中文的路径），但对于大多数软件安装路径（全是英文/数字/符号）已经足够。

## 解析 --config 参数

360 软件管家的 SeAppService.exe 启动时带 `--config=<base64>` 参数。这个 base64 编码的 JSON 包含：
- 推广软件的实际名称（displayName）
- 下载链接（downloadUrl）
- 安装参数（installArgs）
- 等等

解码方法：
```python
import base64, json
# 取出 base64 字符串（去掉 = padding 问题）
b64 = "从 .lnk 提取的 base64 字符串"
padding = 4 - len(b64) % 4
if padding != 4:
    b64 += '=' * padding
decoded = base64.b64decode(b64).decode('utf-8')
config = json.loads(decoded)
print(json.dumps(config, indent=2, ensure_ascii=False))
```

## 文件名约定

使用独立的 `.py` 脚本文件来解析（临时写桌面或 AppData 目录下），避免在命令行里写复杂 Python 时被转义问题困扰。

## 实际案例

### 案例 1：无尽冬日（Whiteout Survival）

用户：使用者，Windows 11 中文系统

**症状：** 桌面上多了「无尽冬日.lnk」，用户不知从何而来。

**分析方法：**
1. 用 `ls -la /c/Users/使用者/Desktop/` 找到 `.lnk` 文件
2. 用 Python 的 regex 方法（见上）提取路径 → `E:\360se6\Application\components\seapp\SeAppService.exe`
3. 确认捆绑源：**360安全浏览器的软件管家**（SeAppService.exe）
4. 进一步搜索发现游戏通过 360 游戏大厅（gamehall）启动

**关键发现：**
- 注册表无该游戏的安装记录（确认是 360 平台启动的云游戏/页游类）
- 360 软件横跨 C/D/E 三个盘符：
  - C:\: Program Files (x86)\360（空壳） + ProgramData\360SD（数据）
  - D:\: 360Safe（安全卫士本体）、360zip、360DrvMgr 等
  - E:\: 360se6（浏览器组件含 seapp/gamehall/gameplugin/gamespace）
- 快捷方式的 `config=` 参数包含 base64 编码的推广信息

### 案例 2：360 全家桶彻底移除

**用户操作流程：**
1. 用户先要求删捆绑游戏 → 发现是 360 塞的 → 用户进一步要求连 360 一起删
2. 杀掉 360 进程（`Stop-Process -Name '*360*' -Force`）
3. 尝试 uninst.exe /quiet 卸载 → 失败（git-bash 下 Permission denied；cmd 弹窗但无静默卸载）
4. 改用 `takeown + icacls 夺权 + rm -rf` 强删
5. 成功清除 D:\360Safe（96个文件/目录全部清空）
6. 浏览器游戏组件（seapp/gamehall/gameplugin/gamespace）全部清空成功
7. **遗留问题：** seapp 下的 webmsg.zip 因 `Device or resource busy` 无法删除
   - 尝试查进程占用：无相关进程
   - 尝试 Rename-Item 改名：失败
   - 尝试 schtasks 注册开机自删：权限不足"拒绝访问"
   - 结论：需要重启后才能释放删除，**单文件残留无需纠缠**
8. 最终清理后只剩不愿全面删除的组件：360zip、360DrvMgr、360Downloads 等

## 已知局限

1. 纯 ASCII 提取法会漏掉含中文/Unicode 字符的路径
2. 部分 .lnk 文件使用相对路径而非绝对路径，需要结合快捷方式的工作目录推断
3. 如果快捷方式指向的是 cmd.exe /c start 或类似的间接启动方式，需要额外分析
