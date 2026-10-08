# SenseNova-Skills（商汤）本机安装记录

上游：https://github.com/OpenSenseNova/SenseNova-Skills（MIT，33 个 sn-* 技能）

## 本机布局（关键：不能只把 skills/* 摊在根上）

- 完整克隆留在 `D:\hermes-skills-sensenova\Source\`（含 docs/ examples/ .env.example，仓库 147MB）
- Hermes 技能目录里每个技能是一条 junction：
  `C:\Users\<用户>\AppData\Local\hermes\skills\<sn-*>` → `D:\hermes-skills-sensenova\Source\skills\<sn-*>`
- **为什么不直接 junction 单个技能目录**：脚本里用相对层级定位上级目录——
  `Path(__file__).resolve().parents[2]` = skills 目录、`parents[3]` = 仓库根（要找 docs/）。
  junction 会被 `Path.resolve()` 解析到 D 盘真实路径，所以 D 盘那边必须保持 `<仓库根>/skills/<技能>/…` 的层级，
  这样 `parents[3]` 才落在有 docs/ 的那层。只拷贝 skills/* 到扁平目录会让 PPT 系列脚本找不到仓库资源。
- junction 批量建法：写 `.ps1` 脚本（纯 ASCII 内容 + 用 `$env:LOCALAPPDATA` 拼目标路径），
  `powershell -NoProfile -ExecutionPolicy Bypass -File <脚本>`。
  **不要在 git-bash 里把中文用户名写进 PowerShell 命令行参数**（编码会乱），也不要在命令里写 `$_`。

## Python 依赖（解释器：`python` = D:\python\python 3.14）

- 必需：`httpx pillow python-dotenv`（sn-image-base）
- PPT/文档：`python-pptx pypdf python-docx`
- 搜索：`requests beautifulsoup4 arxiv semanticscholar yfinance mootdx xhs`
- playwright 装了包但没下浏览器（几百 MB，按需再下 + `PLAYWRIGHT_BROWSERS_PATH` 指到 D 盘）
- 坑：`pip install mootdx[all]` 会把 httpx 降到 0.25.x，**破坏 Hermes 自带的 mcp（要 httpx>=0.27.1）**。
  装完必须 `pip install "httpx>=0.28"` 升回来，再 `python -c "import mcp"` 验证。
mootdx 在 httpx 0.28 下 import 正常，功能未逐项验证。

## API Key / .env 位置（容易踩）

- `sn-image-base/scripts/sn_image_base/configs.py` 的 `prepare_env()` 只读三处：
  1) 进程 CWD 的 `.env`  2) Windows 上写死 `~/.hermes/.env`（即 `C:\Users\<用户>\.hermes\.env`，**不是** `%LOCALAPPDATA%\hermes\.env`）
  3) 已有环境变量
- 所以 key 要放 `C:\Users\<用户>\.hermes\.env`：`SN_API_KEY=sk-xxx`（该目录默认不存在，需新建）
- 只要一个 `SN_API_KEY` 就够；`SN_BASE_URL`/`SN_CHAT_*`/`SN_IMAGE_GEN_*` 代码里已有默认值（内地 `https://token.sensenova.cn/v1`）
- 可选变量见仓库根 `.env.example`：SERPER_API_KEY（图片搜索）、GITHUB_TOKEN、ZHIHU_COOKIE 等

## 本机实测（2026-09 装完后）

- `hermes skills list`：33 个 sn-* 全部 `enabled`
- `python sn-image-doctor/scripts/check_environment.py --verbose`：Python 3.14 ✅、httpx/pillow/python-dotenv ✅、
  sn-image-base 已找到 ✅，仅报缺 SN_IMAGE_GEN_API_KEY（属预期，等 key）
- `python sn-search-academic/scripts/openalex_search.py "tunnel boring machine" -n 2`：返回真实文献 JSON ✅
- arXiv 公共 API 对本机 IP 报 HTTP 429（限流，非技能问题），过一会儿/换语义学术源即可
- 需要 key 的技能：sn-image-*、sn-infographic、sn-ppt-*；不需要 key：sn-search-*（OpenAlex/Crossref/PubMed 等）、
  sn-da-*（本地文件分析）

## 给用户看的资料

`C:\Users\<用户>\Desktop\SenseNova免费API Key申请步骤.txt`（Key 申请步骤 + 官方配置 + 报错对照）

## 验收实测（key 填好后）

- `python scripts/check_environment.py --verbose` → `✅ Environment is properly configured`，
  配置解析显示 SN_API_KEY / SN_CHAT_* / SN_IMAGE_GEN_*（含 `https://token.sensenova.cn/v1`）全部就位
- 直调对话接口 HTTP 200，模型自称“商量 / SenseNova 6.8 Flash Lite”（国产端点直连，不需代理）
- 生图实测：`python scripts/sn_agent_runner.py sn-image-generate --prompt "..." --aspect-ratio 4:3 -o json --save-path "D:/xxx.png"`
  → 29.12 秒产出 2368x1760 PNG（5.8MB），画面内容正确
  - `--save-path` 实测是“文件基名”：给目录会变成同级同名 .png（传 `D:/dir` 得到 `D:/dir.png`）

## 坑（本机实测踩过）

- **GUI 程序从 terminal 工具里起不来**：`Start-Process notepad` / `cmd /c start notepad` 能瞬起进程但马上被回收，
  用户看不到窗口（tasklist 先有后无）。需要用户手填文件时：让他按 Win+R → 粘贴完整路径 → 回车，
  **不要反复试 GUI 自动化，白耗轮次**。
- **curl 传文件必须带 `@` + 原生路径**：`--data-binary @"D:/x.json"`。
  漏掉 `@` 会把路径字符串当成请求体发出去，服务端返回 HTTP 400 `{"error":{"message":"invalid arguments"}}`，
  极易误判成 key 或模型有问题；MSYS 风格的 `/d/...` 路径原生 curl 读不了（报 reading a file 错）。
- **git-bash 里 `python -c` / heredoc 会触发用户批准**，可能被卡住；改用 `python <脚本文件>.py` 或纯 shell 工具。
- **模型返回的正文在 `message.content`**；`max_tokens` 太小时会被 `message.reasoning` 全吃光、`content` 为空或缺失，
  看起来像“调用失败”。要短答就加 `"reasoning_effort":"none"`（实测有效，会直接跳到答案）。
- 写 JSON 请求体用 `write_file` 落盘（utf-8 无 BOM）再用 `curl --data-binary @...`，比 shell 里拼引号可靠。
