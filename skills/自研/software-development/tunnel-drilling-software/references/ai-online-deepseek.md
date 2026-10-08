# v0.12 AI在线版 + 自动联网模式：DeepSeek 接入（单版本）

2026-08-13 实证。使用者先拍板"直接做两个版本"（离线版现场用 + AI版演示用），
加完"自动判断联网"后使用者拍板**合并为单版本**：一个 exe 自动识别——有网走在线
大模型、没网自动切离线规则、不填 key 就是纯离线。触发背景：用户问"把资料库
里的公式都列出来"，离线关键词检索只回一句引言（答非所问）——离线只能片段命中，
罗列/归纳类问题必须整库喂大模型。

## 文件结构

```
ai_online.py               — DeepSeek 在线层（纯逻辑，无GUI可单测）
ai_agent_tab.py            — 面板：状态标签 + key设置 + 自动模式（网络探测线程）
ai_config.json             — 运行时配置（软件目录，用户可写；key 存这里）
_pkg_online/ai_config.json  — 打包内嵌（mode=online，api_key 空）
智能炮孔设计系统.spec        — 单版本打包（datas 含资料库 + _pkg_online 配置）
```

## DeepSeek API 要点

- 端点：`https://api.deepseek.com/v1/chat/completions`（OpenAI 兼容）
- 请求：requests POST，header `Authorization: Bearer sk-xxx`，
  body `{"model":"deepseek-chat","messages":[...],"temperature":0.3,"stream":false}`
- 参数解析用 `"response_format":{"type":"json_object"}`（DeepSeek 支持 json mode，
  prompt 里要含"JSON"字样）；温度 0.1 保稳定
- 响应：`data['choices'][0]['message']['content']`
- 401 = key 无效/缺失（无 key 测连通性会得 HTTP 401，属正常）
- 非 200 抛 `RuntimeError(f'DeepSeek API 返回 {code}: {text[:200]}')`
- 资料库整库 ~18.7KB 5 个 txt，作为上下文远低于 deepseek-chat 上下文上限；
  保险截断 24000 字符

## 在线参数解析（parse_design_online）

1. `chat_once_json(PARSE_SYSTEM, f'用户需求：{text}')` 让模型提取 JSON
2. 清洗：strip 代码块 ```json```；json.loads 失败则取首尾 `{}` 再试
3. 过滤 null/空值字段
4. **与离线 parse_all 合并：`{**off['params'], **merged}`（在线结果优先，离线兜底）**
   ——在线漏掉的字段由离线正则补上，双向保险
5. 复用离线缺参检查 + 默认值合并 → blast_design 引擎出报告

## 在线知识问答（qa_online）

- 资料库整库拼成 `【文件名】\n内容` 文本，作为 user 消息上下文 + 提问
- QA_SYSTEM 强调：列出所有公式/全部内容时**完整列出**；资料库没覆盖就明说
  "资料库未覆盖"，不编造
- 失败返回错误文本（面板降级离线检索）

## 配置与 key 安全

```python
def load_config():  # exe同级 -> _MEIPASS内嵌 -> 默认 {'mode':'offline','api_key':''}
def save_config(cfg):  # 写 exe同级 ai_config.json（用户可写位置）
def is_online(cfg): return cfg['mode']=='online' and bool(cfg['api_key'])
def check_network(timeout=2.0):  # socket TCP 连 api.deepseek.com:443，不耗 token
```

- **API key 只存本地配置，绝不打进 exe**（exe 会发给小伙伴，key 泄露=使用者的
  DeepSeek 余额被白嫖）
- 首次运行：UI 显示 key 输入框（QLineEdit.Password），保存后写 exe 同级
- exe 放 Program Files 等不可写位置时 save_config 失败 → 提示用户换可写目录
- 网络探测是 TCP 握手不是 API 调用：零成本、不耗 token，2s 超时

## 面板逻辑（ai_agent_tab.py）——自动模式

- `__init__` 读配置 → `self.net_ok=False; self.ui_mode='auto'` →
  `self.online = self._effective_online()`；mode=online 时启动
  `QTimer(12s)` + 立即 `_check_net()` 一次
- `_NetCheckThread(QThread)`：后台跑 `ai_online.check_network(2.0)`，
  `pyqtSignal(bool)` 回传（**必须用线程，2s socket 超时放主线程会卡 UI**）；
  `_check_net` 防线程堆积（isRunning 则跳过）
- `_effective_online()`：mode!=online→False；强制off→False；无key→False；
  强制on→True；auto→net_ok（**核心：有效在线 = 配置online + 有key + (强制或网络通)**）
- 模式下拉（`mode_combo`）：自动/强制在线/强制离线，默认自动；切换时对话区提示
- 状态标签：🟢在线(自动/手动) / 🟡未填key（暂走本地）/ ⚪离线(手动强制) /
  ⚪离线(无网络自动切换)；网络状态变化（_on_net changed）时更新标签+对话区提示
  "已恢复在线/已自动切换离线"
- `_send`：按 `self.online` 分流；online → `_handle_design_online/_handle_qa_online`
  （try/except 捕获 → 提示"已切换本地规则" → `self.online=False` → 走离线
  `_finish_design` 统一渲染）
- key 格式合法（非空）就显示 🟢，真假只有请求时才暴露——401 自然走降级，合理
- 离线版（mode=offline）不渲染 key 框/模式下拉，纯离线行为不变

## 单版本打包（一个 spec）

```python
datas = [('C:/Users/使用者/Desktop/我的小项目/凿岩台车Agent资料库',
          '凿岩台车Agent资料库'),
         ('C:/Users/使用者/Desktop/我的小项目/智能炮孔设计系统/_pkg_online/ai_config.json', '.')]
```

- dest `'.'` = _MEIPASS 根目录 → load_config 能读到内嵌 ai_config.json
  （mode=online 34B，archive_viewer 可验证）
- spec 加 `hiddenimports=['requests']`（ai_online 里 `import requests`
  在函数内部，静态分析一般能抓到，但显式声明保险）
- 打包：`"D:/python/python.exe" -m PyInstaller --clean --noconfirm 智能炮孔设计系统.spec`
  约 5 分钟，后台跑 + notify_on_complete；改代码必须重打

## 验证清单

- 离线模式：面板构建 online=False、无 key_edit 无 mode_combo、设计缺参提示、问答命中
- 在线模式（假 key）：构建有 key_edit+mode_combo、等 _check_net 真实探测结果
  （有网 → net_ok=True → online=True → 🟢在线(自动)）
- 自动模式切换：mode_combo 强制离线 → online=False → ⚪离线(手动强制)；
  `_on_net(False)` 模拟断网 → ⚪离线(无网络自动切换)；`_on_net(True)` 恢复 → 🟢
- 降级路径：假 key（sk-test-...）发设计请求 → 401 → online=False → "已切换本地
  规则" + 缺参提示，ERR_COUNT=0
- 开发默认：项目目录不留 ai_config.json（删除测试配置），保证默认 offline

## 教训

1. **离线关键词检索的边界**：只能返回命中的片段，罗列/归纳类问题（"把公式都
   列出来"）必然答非所问——离线版靠扩大 top_k（12段）缓解，根治靠在线大模型
   整库归纳
2. **面板代码重构时小心删掉被引用的方法**：把 `_handle_design` 替换成 online
   版本时把定义删了但 `_send` 离线分支还在调 → AttributeError。改完 grep
   `_handle_design|_handle_qa` 确认定义齐全
3. **UI 布局代码一次写对**：模式分支里 addLayout 重复/遗漏（`if False else None`
   这种脏写法）——先画分支结构再写代码，两个模式都要 addLayout 一次
4. **API key 获取**：Hermes 的 deepseek key 在 Windows 凭据管理器/系统深处
   （auth.json 只有 sha256 指纹），cmdkey /list 也搜不到——不要浪费时间找，
   让用户在软件里填自己的 key 即可
5. **功能能自动区分时别做两个 exe**：先做了双版本（两个 spec 各打 5 分钟），
   自动模式上线后使用者一句"一个版本不就好了"全部推翻重打——自动识别联网后
   单版本天然覆盖双场景，打包前先问使用者"合并成一个？"
6. **网络探测用 socket 而不是 API 调用**：TCP 握手零成本不耗 token；放
   QThread 里跑防 UI 卡顿（2s 超时在主线程会冻结界面）
