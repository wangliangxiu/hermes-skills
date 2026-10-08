---
name: ai-agent-building
description: 搭AI Agent（function calling+工具循环+网页版部署）。
---

# 从零搭建 AI Agent（工具调用型）

用户自己搭建 Agent 时的完整模式。Agent = 大模型 + 工具函数 + 循环：
```
用户输入 → LLM 决定调用哪个工具 → 执行工具拿结果 → 结果回填 LLM → LLM 总结回复（循环直到没有 tool_calls）
```

## 什么时候用

- 用户想搭自己的 AI 助手 / Agent（查天气、整理桌面、写日报等）
- 用户目标是「Agentic Growth Engineer」类岗位，需要亲手做出 Agent 项目
- 需要把「本地脚本」升级为「后端服务」的练手路径

## 环境准备

- 运行时：`D:/python/python.exe`（用户的开发 Python）
- API Key：复用 `~/AppData/Local/hermes/.env` 里的 `DEEPSEEK_API_KEY`（读取函数见下）
- 不装 openai 库也行——直接用 urllib 调 OpenAI 兼容格式

```python
def load_api_key():
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key: return key
    for p in [os.path.expanduser("~/AppData/Local/hermes/.env"),
              os.path.expanduser("~/.hermes/.env")]:
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                m = re.match(r"DEEPSEEK_API_KEY=(\S+)", line.strip())
                if m: return m.group(1)
    return ""
```

## 核心：function calling 循环

DeepSeek `deepseek-chat` 支持 OpenAI 兼容的 tools 参数。每轮：
1. 请求带 `tools`（工具 JSON schema 列表）
2. 若返回 `message.tool_calls` → 逐个执行工具 → 把 `{"role":"tool","tool_call_id":...,"content":...}` 追加进 messages → 继续下一轮
3. 若无 tool_calls → 该 message.content 就是最终回复

```python
for _ in range(5):  # 最多5轮工具调用，防死循环
    msg = call_llm(messages)          # POST /v1/chat/completions, model=deepseek-chat
    tcs = msg.get("tool_calls")
    if tcs:
        messages.append(msg)
        for tc in tcs:
            fn = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"] or "{}")
            result = TOOL_FUNCS[fn](**args)
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
        continue
    print(msg["content"]); break
```

工具注册表 = TOOLS（schema 列表，给 LLM 看）+ TOOL_FUNCS（name→函数 映射）。系统提示词里用编号列表写明每个工具的触发词（如「用户说'X分钟后提醒我'时调用 reminder」），模型选工具更准。

### 系统提示词必须写明真实运行环境（防"沙盒幻觉"）

自建 Agent 直接跑在用户自己的电脑上、能操作真实文件系统，但 SYSTEM_PROMPT 若没说清处境，模型被问「你在哪运行/你是谁」时会按训练数据里的常见话术脑补**「我是运行在沙盒环境中的 AI 助手」**（2026-08 乖乖助手实测，用户差点被误导）。必须在 SYSTEM_PROMPT 里显式写：「你运行在使用者自己的 Windows 电脑上，直接操作使用者的桌面和文件，不是沙盒；调用工具要谨慎，别删东西。」同时提示模型：不知道/查不到就直说，别编造工具结果。

### 模型名要跟随官方换代

写死 `model="deepseek-chat"` 会在官方换代为 `deepseek-v4-flash`/`v4-pro`（2026-08 已换代）后失效或走旧接口。用 API 前核对官方最新模型名，别把旧名写死在代码里。

### 省钱认知（给用户讲课时用）

**工具免费 ≠ 对话免费**。天气（Open-Meteo）、搜索（必应）、记账（SQLite）、计算器都是本地/免费实现，不花钱；但「理解用户意图 + 决定调哪个工具 + 组织回复」这三步模型调用才烧 token——token 就是 API 的计费单位，不存在「花 token 不用 API」这回事。日常一句话约几分钱到一毛钱，与 Hermes 同一余额池。

## 常用工具实现模式（已验证可跑）

### 查天气 — Open-Meteo 免费 API（无需 key）
1. 地理编码：`https://geocoding-api.open-meteo.com/v1/search?name=<城市>&count=1&language=zh`
2. 天气：`https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FShanghai&forecast_days=3`
3. **坑：单字城市名查不到**（「本地」失败，「本地市」成功）→ 查不到时自动试 `城市+"市"` 再试一次

### 网页搜索 — 必应 HTML 解析
- `https://www.bing.com/search?q=<query>` + UA 头
- **坑：必应 HTML 结构经常变**。`<li class="b_algo">` 块内 `<h2><a href=...>` 的严格正则可能匹配不上（h2 和 a 之间有属性）。用宽松正则：`<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>` 直接全局扫 h2 链接，再过滤掉 bing.com 内部跳转链接。写完必须实测，必应会随机反爬（同一请求有时10条有时空），失败就重试一次

### 安全计算器 — AST 白名单
```python
allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
           ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
           ast.USub, ast.UAdd, ast.FloorDiv, ast.Load)
```
- **坑（Python 3.14）：`ast.Num` 已被移除**，用 `ast.Constant` 代替，否则 `AttributeError: module 'ast' has no attribute 'Num'`
- 用户习惯用 `^` 当幂运算 → 计算前 `expression.replace("^", "**")`

### 定时提醒 — 桌面版线程弹窗
`threading.Timer(seconds, func)` 后台线程 + `ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)` 弹窗。Timer 要 `daemon=True`。仅限桌面/本机版——部署到 Linux 服务器后 MessageBoxW 不存在，浏览器用户也看不到。

### 定时提醒 — 网页版（轮询推送模式，已验证）
**不要用 Flask dev server 的 SSE**：`Response(stream_with_context(gen()), mimetype='text/event-stream')` 实测**静默失败**——提醒明明进了队列，curl -N 和 urllib 连 SSE 端点多秒收不到任何帧，gen() 像没执行。排查代价大，**稳定方案 = 轮询**（每 1.5s 一次 GET，绝对可靠，HR 演示场景够用）：

```
后端：
- REMINDERS 列表（待触发 {id,message,due_at}）+ PENDING_PUSH 队列（已到期待推送）
- web_reminder(minutes,message) → uuid 加进 REMINDERS，返回"已设置+到点主动找你+可回复收到/推迟"
- 后台线程 _reminder_checker：每秒把 due_at<=now 的从 REMINDERS 移到 PENDING_PUSH（daemon=True）
- GET /api/check_reminders：加锁取出 PENDING_PUSH 并清空，返回 {reminders:[...]}
- POST /api/reminder/<rid>/respond {action: ack|delay, minutes}：
    ack → 从 REMINDERS 或 PENDING_PUSH 里删掉（到期后可能不在原列表，两个都查）
    delay → 不管找不找得到原提醒，直接创建一条新提醒（due_at=now+minutes）——最简单可靠

前端：
- setInterval(1500ms) fetch /api/check_reminders，有数据逐条 showReminder(r)
- showReminder：右下角 fixed 定位卡片（slideIn 动画）+ 聊天区同步一条 bot 消息 + WebAudio 蜂鸣提示
- 卡片两按钮：✅收到（ack）｜⏰推迟10分钟（delay），点击 fetch respond 后移除卡片
```

**Flask 注意**：`app.run(threaded=True)`——轮询并发请求多，不开多线程会排队卡住。提醒共享数据用 `threading.Lock()` 包住。

### 记账/数据存储 — SQLite
- **坑：sqlite3 的 `c.execute('''...''')` 多行 SQL 字符串里不能写 `#` 注释**，会报 `unrecognized token: "#"`。注释放 SQL 外面，SQL 内部保持纯净
- 文件放脚本同目录：`os.path.join(os.path.dirname(os.path.abspath(__file__)), "xxx.db")`

### 记忆功能 — JSON 文件
`save/recall/list` 三个 action，recall 支持模糊匹配（`key in k or k in key`）。

## 网页版（浏览器聊天界面）

Flask 版：`POST /api/chat` 接收 `{message}` → 跑同样的工具循环 → 返回 `{reply, tool_steps}`（tool_steps 给前端展示「🛠️ 调用工具」过程）。会话历史存 Flask `session`（`session['history'] = history[-40:]` 防爆）。

**坑：端口冲突。** 同一台机器上多个 Flask 服务都用 5000 会互相抢（第二个进程显示 Running 但请求全打到第一个）。给每个服务分配不同端口：炮孔网页版 5000、Agent 网页版 5001。bat 里 `start http://127.0.0.1:5001` 保持一致。

**子目录结构注意：** webapp/app.py 在子目录时，`from agent import ...` 找不到上级模块。需要同时把上级目录加进 sys.path：
```python
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(WEB_DIR)
sys.path.insert(0, PARENT_DIR); sys.path.insert(0, WEB_DIR)
```

## 部署（让别人/HR 能打开链接）

本地跑 = 只有自己能访问。要让别人（尤其简历里的链接）能打开：

| 方案 | 花费 | 24小时在线 | 适合 |
|:----|:----|:---------|:-----|
| cpolar/花生壳 内网穿透 | 免费 | ❌ 电脑要开着 | 当场演示 |
| 云服务器（腾讯/阿里轻量 2核2G Ubuntu） | ¥10-30/月 | ✅ | **简历链接首选** |

简历里的作品链接必须用云服务器部署，否则 HR 打开时你电脑关机 = 打不开。服务器需要用户实名认证购买（身份证+手机号），无法代劳；部署脚本可以写好交给用户。

## 验证流程（自己测完再交付）

1. 每个工具单独调用测一次（不通过 LLM）
2. 端到端测 LLM 循环：`call_llm` 带工具，验证「模型自己选对工具→执行→总结」
3. 多步场景：验证模型能**连续调用多个工具**（如「记一笔奶茶15块，再看看总共多少」→ 先 add 再 summary）
4. 网页版：起服务后 curl/Python 测首页 + `/api/chat` 两个接口
5. 沙箱（execute_code）缺 qrcode 等库时用 terminal 的 D:/python 测，两环境库不同

**网页版接口报 500 且服务日志不打印 traceback（debug=False）时**：用 Flask `test_client()` 复现并捕获异常，不需要起真实服务：
```python
client = app.test_client()
resp = client.post('/api/chat', json={'message': '...'})
print(resp.status_code, resp.get_data(as_text=True)[:300])
```
偶发 500 多为 DeepSeek 网络抖动（LLM 调用超时）而非代码 bug——连测 3 次确认稳定后再怀疑代码。

## 代码风格偏好（用户明确要求）

- 每行代码都加中文注释解释这行在干嘛（用户学习用，别嫌啰嗦）
- 工具返回用中文 + emoji 开头（🌤📁📄🌐⏰🧮📊🔍📖🎲🌍🧠🔗📝）
- 命令行版 + 网页版分开，共用工具函数文件

## 网页版交互设计偏好（用户两次纠正过，必须遵守）

用户原话：「别做成展示用的，要做的话就让对方能直接使用的，咱们把功能做好，给hr一个观感比较好的效果」「右上角那些是功能吗，为什么我点不了」

**核心原则：网页版是给 HR/访客直接上手用的完整产品，不是展示 demo。所有出现在页面上的元素必须真实可点、真实可用。**

- ❌ 禁止纯装饰性标签/徽章——用户或访客点了没反应 = 扣分项
- ✅ 快捷功能按钮（🌤天气/🌐搜索/🧮计算等）：`onclick` 填入示例提问并自动 `send()`，让访客零门槛体验，不用打字
- ✅ 欢迎卡片居中展示「N项工具，全部真实可用」+ 5个可点击的示例对话
- ✅ 工具调用过程透明化：聊天里用虚线气泡显示「🛠 调用 weather → 📦 返回结果预览」，让访客看到 Agent 真的在调工具，不是编的
- ✅ 顶栏放品牌 Logo（渐变圆角方块）+ 绿色呼吸灯「在线 · 实时响应」（@keyframes pulse）
- ✅ 底栏注明技术栈（如「DeepSeek 驱动 · Flask 后端 · 15项工具调用」），增强专业感
- ✅ 打字指示用三个跳动点（animation-delay 错开），比文字「思考中」观感好
- ✅ 输入框支持 Shift+Enter 换行、自动增高（textarea 高度自适应）
- ✅ 响应式适配手机（@media max-width 768px）
- 交付前把每个快捷按钮从头点一遍验证「真能用」，别只验证接口通不通

## 聊天界面实现要点（Flask + 原生 JS，无前端框架）

- `POST /api/chat` 返回 `{reply, tool_steps}`，tool_steps 是 [{name, args, result_preview}]，前端逐个渲染工具气泡再渲染最终回复
- 会话历史存 Flask `session`，注意 `session['history'] = history[-40:]` 防爆
- 前端 `fetch` 失败时显示「连接失败」而不是白屏；`sendBtn.disabled` 防连点

## 把 Agent 做成「通用内核 + 角色外壳」，不要做成单一功能

用户对项目的判断很准：一个方案巧妙与否，看他**内核是不是通用 agent，只换了一张皮**；把某个具体功能当成整个产品，天花板就被封死了（他会直接说"这个给功能限制死了"）。搭 agent 产品时按这个结构摆：

**内核 = 工具 + 记忆 + 定时 + 自主循环**（四件套）。缺了后两样，产品听起来就"像个功能"而不是"一个在跟你过日子的 agent"。
**外壳 = 角色**（形象、口吻、仪式感、文化元素），挂在内核外面。
**功能 = 入口**：发红包、记账、发券这类只是外壳上的一个按钮，不是项目本体。

### 记忆分两层，别混

- **客观事实层**（谁领了多少、何时领的、花到哪）——放可验证的外部账本/链上，对外可以拿来当凭证。
- **人情层**（来过几次、上次说过什么、上次所得、偏好）——放本地 SQLite，链下存。
- 给 LLM 用时不要丢 JSON 进去，先生成**一句人话**（如 `describe(addr)` 返回"第 2 次登门，此前共领过 73 次"），模型的语气和判断都会好一个档次；这条在演示里也是最抓人的细节。

### 定时任务写成「判定函数」而不是裸 Timer

不要 `Timer(秒数, 直接执行)`。写成可解释的规则函数，返回 `(要不要做, 理由)`：
```python
MIN_GAP, LOW_RATIO = 20*60, 0.30
def decide(al, pool):
    if al["hour_lucky"] != "吉":  return False, "此刻非吉时，不动手"
    if 距上次 < MIN_GAP:          return False, f"距上次仅 {gap//60} 分钟，缓一缓"
    if pool and pool["remaining"]/pool["total"] > LOW_RATIO:
                                  return False, "池子还满着，不必开"
    return True, "趁吉时补一包"
```
后台起一个 `asyncio.sleep(300)` 的循环定期调用它，再配一个 `/api/scheduler` 把**上次执行结果 + 判定依据**返回出来。好处有三个：规则能当场讲给人听（不是"到点自动重试"这种工程词）、演示时指着说"规矩真的在执行"、出错时一眼看得出卡在哪条规则。实际调用链上写操作的那一步要单独封装，方便用环境变量关掉自动执行（调试期不要它乱建资源）。

## 相关技能

- `pyqt5-desktop-app` — 桌面版 GUI（本技能是 CLI/Web 版）
- `tunnel-drilling-software` — 台车系统里的 Flask 网页版练手项目（flask-web-version.md 有局域网隔离坑）
- `references/coze-workflow-intro.md` — Coze/扣子拖拽式工作流平台入门（无代码路线，用户求职 AI 公司时向 HR 证明 workflow 能力的捷径）
- `references/dsh-deepseek-harness.md` — DeepSeek 官方 agent 框架 dsh 使用笔记（npm 直装/npx静默假象/dsh web 启动/插件管理 dsh plugin+schemastery 缺依赖坑/皮肤插件 dsh-web-ui 8款）
