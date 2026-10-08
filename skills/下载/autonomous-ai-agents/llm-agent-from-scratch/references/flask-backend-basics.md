# 本地脚本 → Flask 网页服务升级（A类 → B类）

把"双击运行、只有自己能用"的本地脚本升级成"24小时待命、浏览器访问"的网页服务。这是求职 AI 岗位（如月之暗面 Agentic Growth Engineer）看重的"后端玩具"能力。

## 两类东西的本质区别

| 维度 | A类：本地脚本 | B类：后端服务 |
|:----|:-------------|:-------------|
| 运行方式 | 双击/命令行，跑完就结束 | 常驻监听端口，等人来敲门 |
| 访问入口 | 只有自己能用 | 浏览器输网址（http://127.0.0.1:5000）谁都能用 |
| 数据存储 | txt/csv 或程序一关就没了 | SQLite 数据库，重启还在 |
| 核心逻辑 | 输入→处理→输出 | 请求-响应循环（客服模式） |

## 最小 Flask 骨架（每行中文注释）

```python
from flask import Flask, request, jsonify, render_template
import sqlite3, datetime, json, os

app = Flask(__name__)                                    # 创建应用
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'designs.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS designs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            span REAL NOT NULL,
            rock TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')                                                 # ⚠️ SQL 里不能写 # 注释！
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')                 # 网页界面

@app.route('/api/design', methods=['POST'])
def api_design():
    data = request.get_json()                            # 接收前端 JSON
    # ... 业务逻辑 ...
    # 存数据库
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO designs (span, rock, created_at) VALUES (?,?,?)',
              (span, rock, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'total': n})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)      # 0.0.0.0=局域网可访问
```

## 关键技术点

1. **host='0.0.0.0'** — 让同一网络的朋友能访问（本机用 127.0.0.1）
2. **前端**：HTML + canvas 画布可视化 + fetch 调 API（POST JSON → 画图 → 刷新历史）
3. **启动脚本 .bat**：`start http://127.0.0.1:5000` 自动开浏览器
4. **测试用 Python urllib，不用 curl** — curl 传中文参数到 Flask 会编码乱导致 400
   ```python
   import urllib.request, json
   payload = json.dumps({"span": 8.0, "rock": "Ⅳ"}).encode("utf-8")
   req = urllib.request.Request("http://127.0.0.1:5000/api/design",
       data=payload, headers={"Content-Type": "application/json"})
   print(urllib.request.urlopen(req).read())
   ```

## ⚠️ 局域网隔离大坑（本会话踩过）

**同事用网线、你用 WiFi → 局域网链接同事打不开！** 办公室网络经常把 WiFi 和有线分成不同网段（或开 AP 隔离），`192.168.x.x` 地址跨网段不通。

解决方案（按用途选）：

| 方案 | 花费 | 同事能开 | 电脑要开吗 | 适合 |
|:----|:----|:--------|:----------|:-----|
| cpolar / 花生壳 内网穿透 | 免费版够用 | ✅ 全世界 | ⚠️ 要开着 | 临时演示 |
| 云服务器（腾讯/阿里轻量） | ¥10-30/月 | ✅ 24小时 | ❌ | 简历链接 |
| PythonAnywhere 免费部署 | 免费 | ✅ | ❌ | 预算0 |

**简历链接一定要用云服务器/免费部署**——你电脑关机链接就废了，HR 点开是"无法访问"。

## 测试流程（自己跑完再交付）

1. 后台启动：`python app.py`（background=true）
2. urllib 测 GET / → 200
3. urllib 测 POST /api/design → 返回数据
4. urllib 测 GET /api/history → 看到入库记录
5. 确认 SQLite 落盘后，再告诉用户"浏览器打开 http://127.0.0.1:5000"

## 网页版主动推送/提醒（交互模式，本会话验证）

**Flask 开发服务器 (werkzeug) 的 SSE 不靠谱** — `stream_with_context` + `text/event-stream` 长连接在 dev server 下会被缓冲，浏览器收不到推送（curl -N 连 25s 无数据、EventSource 一直空等）。别再试 SSE，改用轮询。

**可靠模式：后台线程 + 队列 + 轮询端点 + 交互端点**

```python
import threading, time, uuid
REMINDERS = []      # 待触发的提醒 {id, message, due_at}
PENDING_PUSH = []   # 已到期，等浏览器取走
reminder_lock = threading.Lock()

def web_reminder(minutes=30, message="时间到了"):
    rid = uuid.uuid4().hex[:8]
    due_at = time.time() + int(minutes) * 60
    with reminder_lock:
        REMINDERS.append({"id": rid, "message": message, "due_at": due_at})
    return f"✅ 已设置：{minutes}分钟后提醒，到点我会主动找你"

# 后台线程：每秒把到期提醒移入 PENDING_PUSH
def _checker():
    while True:
        now = time.time()
        with reminder_lock:
            due = [r for r in REMINDERS if r["due_at"] <= now]
            for r in due:
                REMINDERS.remove(r); PENDING_PUSH.append(r)
        time.sleep(1)
threading.Thread(target=_checker, daemon=True).start()

# 轮询端点（前端每1.5s fetch 一次）
@app.route('/api/check_reminders')
def check_reminders():
    with reminder_lock:
        due = list(PENDING_PUSH); PENDING_PUSH.clear()
    return jsonify({"reminders": due})

# 交互端点：收到=关闭；推迟=直接创建新提醒（原提醒到期后已不在列表里，别去找）
@app.route('/api/reminder/<rid>/respond', methods=['POST'])
def respond(rid):
    data = request.get_json() or {}
    if data.get("action") == "delay":
        minutes = max(1, int(data.get("minutes", 10)))
        with reminder_lock:
            REMINDERS.append({"id": uuid.uuid4().hex[:8],
                              "message": data.get("message", "时间到了"),
                              "due_at": time.time() + minutes * 60})
        return jsonify({"success": True, "message": f"好，{minutes}分钟后再提醒你"})
    return jsonify({"success": True, "message": "收到，提醒已关闭"})
```

前端：`setInterval(async () => { const d = await (await fetch('/api/check_reminders')).json(); ... }, 1500)`，收到后右下角弹通知卡片（含 收到/推迟10分钟 按钮），按钮再 fetch respond 端点。可加网页提示音（AudioContext 短蜂鸣）。

**要点：**
- 提醒到期后已从 REMINDERS 移走，respond 的"推迟"要**直接创建新提醒**，别去找原提醒
- `app.run(host='0.0.0.0', port=5001, threaded=True)` 必须开，否则轮询请求排队卡死
- 端口冲突：一个机器跑多个 Flask 应用用不同端口（5000/5001），别都用 5000
- 偶发 500：Flask test_client 返回 200 但真实 HTTP 偶发 500（DeepSeek API 网络抖动）→ 重试即可，不是代码 bug
