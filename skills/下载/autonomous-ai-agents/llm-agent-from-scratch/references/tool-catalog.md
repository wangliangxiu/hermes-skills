# 乖乖助手 Agent · 扩展工具目录（v2.0）

12 个新增工具的实现要点与完整代码骨架。放在 `tools_extra.py`，由 `agent.py` 合并注册。

## 注册方式

```python
# agent.py 里
from tools_extra import EXTRA_TOOLS, EXTRA_TOOL_FUNCS
TOOLS = TOOLS + EXTRA_TOOLS
TOOL_FUNCS.update(EXTRA_TOOL_FUNCS)
```

## 1. 网页搜索（必应）

```python
import requests, urllib.parse, re

def tool_web_search(query="", num=5):
    url = "https://www.bing.com/search?q=" + urllib.parse.quote(query)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.encoding = "utf-8"
    html = resp.text
    # 宽松正则：新版必应 <h2> 与 <a> 之间可能有属性
    items = re.findall(r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
    results = []
    for link, title_html in items[:num]:
        if "bing.com" in link and "search" not in link:
            continue  # 跳过必应内部跳转链接
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        if title:
            results.append(f"{title}\n  {link}")
    return f"🔍 搜索结果（{query}）：\n" + "\n".join(results) if results else f"搜索「{query}」没有找到结果"
```

**坑：** 旧正则 `<li class="b_algo">...<h2><a href=...>` 在新版必应失效（h2 带属性、结构变化）。调试时打印真实 HTML 片段确认结构，不要假设。

## 2. 定时提醒

```python
import threading, ctypes
from datetime import datetime

def _popup(title, text):
    ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)

def tool_reminder(minutes=30, message="时间到了"):
    t = threading.Timer(max(1, int(minutes)) * 60,
                        _popup, args=("⏰ 提醒", message))
    t.daemon = True  # 守护线程，不阻塞主循环
    t.start()
    when = datetime.fromtimestamp(datetime.now().timestamp() + minutes * 60).strftime("%H:%M:%S")
    return f"✅ 已设置提醒：{minutes}分钟后（{when}）提醒你：{message}"
```

## 3. 安全计算器（AST 白名单）

```python
import ast

def _safe_eval(expr):
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
               ast.USub, ast.UAdd, ast.FloorDiv, ast.Load)
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError("表达式包含不允许的内容")
    return eval(compile(tree, "<safe>", "eval"), {"__builtins__": {}}, {})

def tool_calculator(expression="1+1"):
    expr = expression.replace("^", "**")  # ^ 在 Python 是异或，不是幂
    result = _safe_eval(expr)
    return f"🧮 {expression} = {result}"
```

**坑：** Python 3.14 移除了 `ast.Num`（用 `ast.Constant` 替代），白名单里写 `ast.Num` 会报 `module 'ast' has no attribute 'Num'`。

## 4. 记账本（SQLite）

```python
import sqlite3
LEDGER_DB = "ledger.db"  # 与脚本同目录

def _init():
    conn = sqlite3.connect(LEDGER_DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT, amount REAL, kind TEXT, created_at TEXT)""")
    conn.commit(); conn.close()
_init()

def tool_ledger(action="add", item="", amount=0.0):
    conn = sqlite3.connect(LEDGER_DB)
    if action == "summary":
        rows = conn.execute("SELECT kind, SUM(amount) FROM ledger GROUP BY kind").fetchall()
        conn.close()
        return "📊 记账本：" + " ".join(f"{k}：¥{v:.2f}" for k, v in rows)
    kind = "支出" if amount >= 0 else "收入"
    conn.execute("INSERT INTO ledger (item, amount, kind, created_at) VALUES (?,?,?,?)",
                 (item, abs(amount), kind, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()
    return f"✅ 已记账：{kind} {item} ¥{abs(amount):.2f}"
```

## 5. 文件查找

```python
def tool_find_file(keyword="", folder=None):
    folder = folder or os.path.expanduser("~/Desktop")
    found = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "AppData"]
        for f in files:
            if keyword.lower() in f.lower():
                found.append(os.path.join(root, f))
        if len(found) >= 20:
            break
    return "🔍 找到：" + "\n".join(f"  • {f}" for f in found) if found else f"没找到含「{keyword}」的文件"
```

## 6. 百科查询（百度百科 + 必应兜底）

```python
def tool_knowledge(query=""):
    url = "https://baike.baidu.com/item/" + urllib.parse.quote(query)
    resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
    resp.encoding = "utf-8"
    m = re.search(r'<meta name="description" content="([^"]+)"', resp.text)
    if m and len(m.group(1)) > 10:
        return f"📖 {query}：{m.group(1)[:300]}"
    return tool_web_search(f"{query} 是什么", num=3)  # 403 反爬时兜底
```

**坑：** 百度百科对脚本请求常返回 403「百度安全验证」，必须加搜索兜底。

## 7. 决策助手

```python
import random
def tool_decide(options="今天吃啥"):
    if "骰" in options: return f"🎲 {random.randint(1, 6)}"
    if "硬币" in options: return f"🪙 {random.choice(['正面','反面'])}"
    if "还是" in options or "或者" in options:
        parts = [p.strip() for p in re.split(r"还是|或者|、|,|，", options) if p.strip()]
        if len(parts) >= 2: return f"🎯 我选：{random.choice(parts)}"
    if "吃啥" in options:
        return f"🍽️ {random.choice(['米饭套餐','面条','饺子','麻辣烫','汉堡','烧烤','火锅'])}"
    return f"🎯 {random.choice(['就这个吧','没问题','冲！'])}"
```

## 8. 网络查询

```python
import socket
def tool_network_info():
    public_ip = requests.get("https://api.ipify.org?format=json", timeout=10).json().get("ip", "未知")
    hostname = socket.gethostname()
    local_ips = [i[4][0] for i in socket.getaddrinfo(hostname, None, socket.AF_INET)
                 if not i[4][0].startswith("127.")]
    return f"🌍 公网IP：{public_ip}\n💻 本机IP：{', '.join(local_ips)}"
```

## 9. 简单记忆（JSON 文件）

```python
MEMORY_FILE = "memory.json"
def _load(): return json.load(open(MEMORY_FILE, encoding="utf-8")) if os.path.exists(MEMORY_FILE) else {}
def tool_memory(action="recall", key="", value=""):
    data = _load()
    if action == "save":
        data[key] = value
        json.dump(data, open(MEMORY_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return f"🧠 记住了：{key} = {value}"
    if action == "list":
        return "🧠 " + "\n".join(f"• {k}: {v}" for k, v in data.items()) if data else "记忆库是空的"
    return f"🧠 记得：{key} = {data[key]}" if key in data else f"没找到「{key}」的记忆"
```

## 10. 文件夹统计

```python
def tool_folder_stats(path=""):
    path = path or os.path.expanduser("~/Desktop")
    total_size = total_files = 0
    ext_count = {}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "AppData"]
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
            total_files += 1
            ext = os.path.splitext(f)[1].lower() or "(无)"
            ext_count[ext] = ext_count.get(ext, 0) + 1
    top = sorted(ext_count.items(), key=lambda x: -x[1])[:5]
    return (f"📁 {path}\n  文件数：{total_files}\n  总大小：{total_size/1024/1024:.1f} MB\n"
            f"  主要类型：{' '.join(f'{e}({n})' for e, n in top)}")
```

## 11. 二维码

```python
def tool_qrcode(text="https://example.com"):
    import qrcode
    img = qrcode.make(text)
    fpath = os.path.join(os.path.expanduser("~/Desktop"), f"二维码_{datetime.now().strftime('%H%M%S')}.png")
    img.save(fpath)
    return f"✅ 二维码已生成：{fpath}"
```

**坑：** 需要 `pip install qrcode`。沙箱 execute_code 是另一个解释器没有这库，验证必须用 `D:/python/python.exe`。

## 12. 文本存文件

```python
def tool_save_text(content="", filename=""):
    filename = filename or f"笔记_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    out_dir = os.path.join(os.path.expanduser("~/Desktop"), "我的文档")
    os.makedirs(out_dir, exist_ok=True)
    fpath = os.path.join(out_dir, filename)
    open(fpath, "w", encoding="utf-8").write(content)
    return f"✅ 已保存：{fpath}"
```

## 工具注册表（JSON schema 模板）

```python
EXTRA_TOOLS = [
    {"type": "function", "function": {
        "name": "web_search",
        "description": "网页搜索，返回结果标题和链接。用户问新闻/资讯/不知道的事时使用",
        "parameters": {"type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词"}},
            "required": ["query"]}}},
    # ... 其余工具同理
]
EXTRA_TOOL_FUNCS = {
    "web_search": tool_web_search,
    # ...
}
```

## SYSTEM_PROMPT 必须同步

每加一个工具，SYSTEM_PROMPT 里加一行触发说明，例如：
`7. 记账：用户说"记一笔/花了多少钱/查账"时，调用 ledger`
否则模型永远不知道啥时候调这个工具。

## 验证清单

- [ ] 每个工具函数单独跑一遍（用 D:/python/python.exe，不是沙箱）
- [ ] 完整循环测试：模拟用户输入 → 模型决定调工具 → 结果回填 → 最终回复
- [ ] 多工具连续调用测试（如"记一笔 + 查账"应触发两次 ledger）
- [ ] 工具失败时返回人话而不是抛异常
