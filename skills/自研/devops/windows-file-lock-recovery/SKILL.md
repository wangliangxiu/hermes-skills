---
name: windows-file-lock-recovery
description: "Windows 装包/更新报文件被占用（os error 32）时用：定位占用+绕开装卸+交付一键bat。"
version: 1.0.0
author: agent
---

# Windows 文件占用导致装包/更新失败

用来处理这一类问题：**pip / uv / 更新脚本删不掉或覆盖不了某个文件**，报
`os error 32` / 「另一个程序正在使用此文件，进程无法访问」/ `PermissionError: another process
is holding it open`。典型元凶是**正在运行的 .exe（启动器）**和**已被加载的 .pyd/.dll**。

本机最常复现的场景是 `hermes update` 装依赖失败 —— 完整案例（症状链、marker 重试上限、
如何验证新代码真的能跑）见 `references/hermes-update-windows-lock.md`。
交付给用户的一键 `.bat` 怎么写、怎么自测，见 `references/windows-bat-from-bash.md`。

## 第一步：定位到底是谁占着文件

```bash
# 1) 从 uv/pip 的报错里拿到确切路径（它会直接写出 failed to remove file ...）
# 2) 验证这个文件真的被锁（改名是最小验证；失败即被占用）
mv path/to/x.exe x_test.exe      # MSYS
powershell -NoProfile -Command "Rename-Item -LiteralPath 'path\to\x.exe' -NewName 'x_t.exe'"
# 症状：'Device or resource busy' / 「另一个程序正在使用此文件」
# 3) 找到持有者：按映像名（.exe）列出，别猜
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -like '*<name>*' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine | Format-List"
```

判读要点：

- **运行中的 .exe 既不能删、也不能改名**（Windows 锁住映像文件）。所以「先改名再装」这类
  绕法在 Windows 上不成立，别浪费时间去试。
- **锁的具体粒度是文件，不是目录**：同一个启动器在多处存在时，只有"正在跑的那个路径"被锁。
  例：`venv\Scripts\hermes.exe` 在跑时被锁，而 `bin\hermes.exe` 是同一份文件的另一拷贝、
  完全可写 —— 所以换一个启动路径就能绕开。
- `.pyd` / `.dll` 只被"从该 venv 解释器起、且已经 import 它"的进程锁住。全新进程在 import
  之前做安装，通常锁不上 —— 这正是很多工具把修复动作放在"启动早期/导入之前"的原因。
- `tasklist` 会把名字截断到 25 字符，写过滤器时用 `*` 模糊匹配，否则会漏进程。

## 第二步：三条通用出路（按可靠度）

1. **换一个不占用该文件的进程去装**：用解释器直接跑（不经启动器 .exe）。
   例：`venv/Scripts/python.exe -m hermes_cli.main update -y` 而不是 `hermes update`。
2. **只装不冲突的那部分**，把项目自身的重装留到以后：
   `--dry-run` 先列出真正缺的包 → 逐包安装时**排除被锁的那个包本身**。
   依赖装上了，功能就恢复了；被锁的往往只是一个 console-script stub / 元数据刷新。
3. **交给"下一次干净启动"或一个延后标记**：很多安装器有 defer-via-marker 机制
   （失败后写 marker，下次启动在导入原生扩展之前补装）。要注意这类机制通常有**重试上限**，
   反复"启动看看好没好"会把次数耗光 —— 想看状态就读 marker 文件，别启动程序。

## 第三步：给用户交付一键脚本

用户自己不方便敲命令时，做桌面一键 `.bat`（生成即可执行，无需他复制命令）。
写法与自测坑位见 `references/windows-bat-from-bash.md`。骨架：
先查进程占用（守卫）→ 用解释器直接跑修复命令 → 清 marker + 打印版本验证 → `pause` 留在屏幕上。

## Pitfalls

- **别用"启动一次看看"验证修复**：会消耗重试额度、还可能留下半装状态。读日志/marker。
- **别 export 一个不存在的代理到 shell**：terminal 工具的 shell 会跨调用保留环境变量，
  之后所有 curl 返回 `000`、装包也全失败。先 `env | grep -i proxy`，
  再 `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY` 排查。同一个进程里
  "自带下载器忽略代理、uv 却遵守代理"会造成极迷惑的"能下载但装不上"。
- **别急着下"环境坏了"的结论**：这类失败通常只卡在一个文件上，其余全部正常。
  先确认"只有一个文件失败"，再决定绕法。
- 安装器回退路径（如 git→ZIP 整包下载）可能很慢且不解决锁问题；能定位到根因就别陪着等。
