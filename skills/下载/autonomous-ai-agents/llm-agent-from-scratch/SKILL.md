---
name: llm-agent-from-scratch
description: 自建 LLM Agent，用 OpenAI 兼容 API 实现 function calling 工具调用。
---

# 从零搭建自己的 LLM Agent

用 OpenAI 兼容 API（DeepSeek / 通义 / GLM 等）从零实现一个能调用工具干活的 Agent，不依赖任何 Agent 框架，不装 openai 库。

## 适用场景

- 用户想"自己搭一个 Agent"（求职 AI 岗位、学习 Agent 原理、练手）
- 需要给现有程序加"让大模型决定调用工具"的能力
- 解释 Agent 工作原理（LLM 决策 + 工具执行 + 循环）

## 核心概念：Agent = 大模型 + 工具 + 循环

```
用户说"查天气"
  → 调大模型（带工具清单）
  → 模型返回 tool_calls: 调 weather({city:"本地"})
  → 执行工具函数，拿到结果
  → 把结果塞回消息历史，再调一次模型
  → 模型生成最终回复 → 返回给用户
  （循环直到模型不再要调工具）
```

**Agent 的"大脑"永远在云端（API）**，本地只做：发请求、执行工具、存数据。硬件需求极低——普通笔记本就够，不需要 GPU；本地跑开源大模型才需要好显卡。

## 关键实现模式（DeepSeek，纯 urllib）

### 1. API 调用（OpenAI 兼容格式）

```python
import urllib.request, json, ssl
API_URL = "https://api.deepseek.com/v1/chat/completions"

def call_llm(messages):
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "tools": TOOLS,            # 工具清单（JSON schema）
        "max_tokens": 2000,
    }
    req = urllib.request.Request(API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    resp = urllib.request.urlopen(req, timeout=60, context=ssl_ctx)
    return json.loads(resp.read())["choices"][0]["message"]
```

API Key 读取：优先环境变量 `DEEPSEEK_API_KEY`，其次读 Hermes 的 `~/AppData/Local/hermes/.env`（用户已有 key，不用让用户重新填）。

### 2. 工具注册表（两个部分配套）

```python
TOOLS = [   # 告诉模型有哪些工具可用（JSON schema）
    {"type": "function", "function": {
        "name": "weather",
        "description": "查询指定城市的天气",
        "parameters": {"type": "object",
            "properties": {"city": {"type": "string", "description": "城市名"}},
            "required": ["city"]}}},
]

TOOL_FUNCS = {   # 工具名 → 实际函数
    "weather": tool_weather,
}
```

### 3. Agent 主循环（核心骨架）

```python
messages = [{"role": "system", "content": SYSTEM_PROMPT}]
messages.append({"role": "user", "content": user_input})

for _ in range(5):                      # 最多5轮工具调用，防死循环
    msg = call_llm(messages)
    tool_calls = msg.get("tool_calls")
    if tool_calls:
        messages.append(msg)            # 模型的工具调用请求加入历史
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"] or "{}")
            result = TOOL_FUNCS[fn_name](**args)   # 执行工具
            messages.append({"role": "tool",       # 结果以 role=tool 回填
                             "tool_call_id": tc["id"],
                             "content": str(result)})
        continue                        # 继续让模型基于结果生成回复
    print(msg["content"])               # 没有 tool_calls → 最终回复
    break
```

**两个关键点：**
- 模型的 tool_calls 消息要 `append` 回历史（角色是 assistant）
- 工具结果用 `role: "tool"` + `tool_call_id` 回填，否则模型不知道结果是谁的

## 免费工具配方（无需 API key）

### 天气（Open-Meteo，免费无key）

```python
# 城市名 → 经纬度
"https://geocoding-api.open-meteo.com/v1/search?name=本地市&count=1&language=zh&format=json"
# 经纬度 → 天气
"https://api.open-meteo.com/v1/forecast?latitude=35.24&longitude=113.24&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FShanghai&forecast_days=3"
```

**坑：中文城市名查不到时自动补"市"重试** — "本地"查不到但"本地市"能查到。循环尝试 `[city, city+"市", city.replace("市","")]`。天气代码（weathercode）要映射成中文（0晴/1基本晴/61小雨/95雷雨…）。

### 整理桌面
按扩展名分类移动文件（图片/文档/压缩包/安装包/音视频/代码），**只移动不删除**，跳过文件夹和 `~$` 开头的 Office 临时文件，同名文件加 `_1` 后缀。分类规则用 dict 映射 ext → 文件夹名。

### 写日报
把用户输入的工作内容写入 `桌面/我的日报/日报_YYYY-MM-DD.txt`，用固定模板（今日工作/明日计划/问题需求三块）。

## 扩展工具集（12个新工具，v2.0）

在 `tools_extra.py` 里实现，agent.py 里 `TOOLS = TOOLS + EXTRA_TOOLS` + `TOOL_FUNCS.update(EXTRA_TOOL_FUNCS)` 合并。SYSTEM_PROMPT 里要逐条列出每个工具触发条件，模型才知道啥时候调。

| 工具 | 关键实现 | 备注 |
|:----|:---------|:-----|
| web_search | requests 抓必应HTML，宽松正则提取标题链接 | 见常见坑（必应改版）|
| reminder | `threading.Timer(minutes*60, func)` + `ctypes.windll.user32.MessageBoxW` 弹窗 | 守护线程，别阻塞主循环 |
| calculator | AST 安全求值（白名单节点），`^`→`**` | 防注入：`eval` 白名单 |
| ledger | SQLite 表 ledger(item, amount, kind, created_at)，kind=支出/收入 | 负数=收入 |
| find_file | os.walk 递归搜索文件名关键词 | 跳过隐藏目录 |
| knowledge | 百度百科 + 必应兜底 | 见常见坑（403）|
| decide | 正则拆选项：`A还是B`→随机选，掷骰子/硬币/今天吃啥 | 无网络 |
| network_info | ipify.org 查公网IP + socket.getaddrinfo 查本机IP | 免费无key |
| memory | JSON 文件存 `{key: value}`，save/recall/list | 简单记忆够用 |
| folder_stats | os.walk 统计大小/文件数/扩展名Top5 | — |
| qrcode | `pip install qrcode`，`qrcode.make(text)` 存PNG | 沙箱没这库，用 D:/python 验证 |
| save_text | 文本写 `桌面/我的文档/xxx.txt` | 给写长内容用 |

完整代码见 `references/tool-catalog.md`。

**工具设计要点：**
- 每个工具函数**必须自带兜底返回**（查不到/失败 → 返回一句人话，别抛异常），否则模型会卡死
- 工具返回字符串要带 emoji 前缀（🌤📁📄🧮📊），模型回复时会复述，观感好
- 新增工具后 SYSTEM_PROMPT 必须同步加一行触发说明，否则模型永远不调它

## 自测方法（不要直接让用户双击验证）

跑完代码必须自己先测工具函数 + 完整循环：

```python
import sys, json
sys.path.insert(0, r"项目路径")
import agent
# 1. 单测工具
print(agent.tool_weather("本地"))
# 2. 测完整循环（模拟用户输入）
messages = [{"role": "system", "content": agent.SYSTEM_PROMPT},
            {"role": "user", "content": "帮我查一下本地的天气"}]
for _ in range(5):
    msg = agent.call_llm(messages)
    ...  # 同主循环逻辑
```

## 常见坑

| 坑 | 解决 |
|:---|:-----|
| SQLite 的 SQL 字符串里写 `#` 注释 | 抛 `unrecognized token: "#"` — SQL 里不能有注释，删掉 |
| curl -d 传中文 POST 到 Flask | 编码乱导致 400 — 用 Python urllib 测试，别用 curl |
| 终端工具把 `pip install uvicorn` 当服务器拦截 | 拆开装 + 用引号 `pip install "uvicorn[standard]"` |
| 模型反复要调工具停不下来 | 主循环加 `for _ in range(5)` 上限 |
| Python 3.14 用 `ast.Num` | 已移除，报 `module 'ast' has no attribute 'Num'` — 用 `ast.Constant` |
| 计算器 `^` 不表示幂 | Python 里 `^` 是异或 — 先 `expression.replace("^", "**")` 再算 |
| 必应搜索结果解析不出来 | 新版HTML结构变了：`<li class="b_algo">...<h2><a` 正则失效 — 用宽松正则 `<h2[^>]*>\s*<a[^>]*href="([^"]+)"`，并跳过含 bing.com 的内部链接 |
| 百度百科返回403「百度安全验证」 | 有反爬 — knowledge 工具加必应搜索兜底 |
| 沙箱 execute_code 与 D:/python 是不同解释器 | 依赖（如 qrcode）装在 D:/python 但沙箱没有 — 用 `D:/python/python.exe` 跑验证，别只在 execute_code 里测 |
| 同一段正则单独跑有结果、包进工具函数就没结果 | 别假设目标HTML结构 — 打印真实HTML片段看结构再改正则（必应/百度都会改版） |
| Flask dev server 的 SSE 推送收不到 | werkzeug 缓冲长连接 — 别用 SSE，改用轮询（后台线程+队列+`/api/check_reminders` 每1.5s拉一次），交互端点"推迟"直接创建新提醒。详见 `references/flask-backend-basics.md` |
| 同一台机器跑多个 Flask 应用 | 端口冲突（都默认5000）— 用不同端口（5000/5001），app.run 必须 threaded=True |
| 真实 HTTP 偶发 500 但 test_client 返回 200 | DeepSeek API 网络抖动 — 重试即可，不是代码 bug |
| 模型被问身份/运行环境时幻觉自称"沙盒" | SYSTEM_PROMPT 必须写明真实运行环境（如"你运行在用户自己的 Windows 电脑上，直接操作桌面和文件"），否则模型按训练数据脑补成"运行在沙盒环境中的AI助手"——这是 LLM 最常见的身份幻觉，2026-08 在乖乖助手上实证。补一句身份说明即可修正 |

## 升级方向（用户求职用）

- 加新工具：日历/快递查询/文件搜索
- 把 Agent 包成 Flask 网页服务 → 浏览器对话（见 `references/flask-backend-basics.md`）
- 加"记忆"：把多轮对话存 SQLite，下次启动恢复
- 让 Agent 自己规划任务（把大任务拆成子步骤循环执行）

## 参考资料

| 文件 | 说明 |
|:---|:---|
| `references/flask-backend-basics.md` | 本地脚本 → Flask 网页服务升级（A类→B类），SQLite + 局域网访问 + 部署方案 |
| `references/tool-catalog.md` | 12个扩展工具的完整代码骨架（搜索/提醒/计算/记账/记忆/二维码等）+ 注册方式 + 验证清单 |
