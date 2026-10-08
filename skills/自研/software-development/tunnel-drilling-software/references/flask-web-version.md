# 炮孔设计系统 · Flask 网页版（练手项目）

## 背景

用户对月之暗面「Agentic Growth Engineer」岗位感兴趣，想从"本地脚本"（A类）升级到"后端服务"（B类）。本练手项目把炮孔设计系统的核心逻辑搬上 Flask + SQLite，让朋友在同一 WiFi 下能用浏览器访问。

项目位置：`桌面\我的小项目\炮孔设计网页版\`
- `app.py` — Flask 后端 + SQLite 存储
- `templates/index.html` — 网页前端（canvas 画布 + 参数表单 + 历史记录）
- `启动网页版.bat` — 双击启动并自动开浏览器

## 核心结构（每行代码加中文注释——用户要求）

```
app.py
├── init_db()           # 建表：designs(id, span, rock, hole_count, params, result, created_at)
├── calc_holes()        # 核心布孔逻辑（从桌面版 PyQt5 搬来）
├── GET  /              # 返回 index.html
├── POST /api/design    # 收参数→算孔→存SQLite→返回JSON
├── GET  /api/history   # 查最近50条历史
├── DELETE /api/design/<id>  # 删记录
└── app.run(host='0.0.0.0', port=5000)  # 0.0.0.0 = 局域网可访问
```

## 关键要点

1. **SQLite 的 SQL 字符串里不能写 `#` 注释** — 会报 `sqlite3.OperationalError: unrecognized token: "#"`。多行 SQL 里的注释只能放 SQL 外面（Python 侧），或干脆不加。

2. **curl 带中文 JSON 会 400** — 测试 POST 接口不要用 curl -d，用 Python urllib 把 json.dumps(...).encode('utf-8') 发过去，避免编码问题。

3. **0.0.0.0 监听** — `app.run(host='0.0.0.0')` 让同一 WiFi 的朋友能通过 `http://你的IP:5000` 访问（本机是 127.0.0.1:5000）。启动时打印两个地址方便用户。

4. **测试顺序**：先 `python -c "from app import calc_holes; print(len(calc_holes(6.0,'Ⅲ')))"` 验证核心逻辑 → 后台启动 `python app.py` → urllib 测 POST/GET/DELETE → 全通才告诉用户打开浏览器。

5. **Flask 已装**（D:/python），FastAPI 没有。优先用 Flask 做这类练手。

## ⚠️ 局域网访问的坑（本会话验证）

**`http://192.168.x.x:5000` 只对同一网段有效。** 办公环境常见隔离：
- 用户连 WiFi，同事插网线 → 两边经常不在同一网段（VLAN 隔离 / AP 隔离），**同事打不开**
- 手机 4G/5G 流量 → 也打不开（不在内网）
- 所以「同 WiFi 能用」这个说法只适用于家里/小路由器场景，办公网不可靠

### 让外网/同事能访问的方案（按场景选）

| 方案 | 花费 | 特点 | 适合 |
|:----|:----|:-----|:-----|
| **cpolar / 花生壳**（内网穿透） | 免费版够用 | 给一个公网地址（如 xxxx.cpolar.cn），全世界能开；**电脑必须开着**，免费版地址会变 | 当场演示、临时分享 |
| **云服务器部署**（腾讯云/阿里云轻量） | ¥10-30/月（新用户价） | 24小时在线，地址稳定，还能配域名 | **简历链接首选**（HR 随时能点开） |
| 免费部署平台（PythonAnywhere 等） | 免费 | 无需自己电脑，但国内访问可能慢 | 预算为 0 |

**简历里放链接必须先部署**：用户电脑关机/断网，简历链接就失效；HR 点开是"无法访问"，比不放还糟。

## 与桌面版的关系

- 桌面版（PyQt5）继续保留：隧道无网，桌面版才是现场能用的。
- 网页版纯粹练"后端服务"技能（招聘岗位看重的技能），不替代桌面版。
- 跟用户讲清楚这个区别，避免误以为网页版能上工地。

## 用户的学习路径背景

- 用户想做"后端玩具"以接近月之暗面 Agentic Growth Engineer 岗。
- 该岗位 JD 要点：增长链路自动化、Agentic Infra、AI 深度使用 + 工程底子。
- 练手项目就是「把本地脚本升级成后端服务」的第一步（DS 给的评估任务：A类本地脚本 vs B类后端服务）。
- **用户明确说「要确定自己能做出来这些」**——网页版要按桌面版完整功能逐步做全（3D视图用 Three.js 等），这是能力验证，不是赶工。做全后简历里写"独立开发了完整 Web 版炮孔设计系统"。
