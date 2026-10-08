---
name: wechat-chat-record-extraction
description: 提取/解密/导出微信4.x聊天记录。触发词：微信聊天记录、导出微信、解密微信库、dot-skill素材、miyu。
---

# 微信聊天记录提取（4.x，2026-08 现状）

当用户要"把微信聊天记录导出来/喂给 dot-skill/分析聊天"时使用。核心链路：
**本地加密库 → 密钥（微信进程内存）→ 解密 → TXT**。

## 数据位置（Windows 新版微信 4.x/5.x）
- 当前数据根目录：`D:\xwechat_files\`，按账号分 `wxid_xxx_<hash>\`
- **聊天记录库**：`<root>\<wxid>\db_storage\message\message_0.db~N.db`
  + `message_fts.db`（全文索引）+ `message_resource.db` —— **SQLCipher/AES 加密**，
  文件头是随机字节（非 `SQLite format 3`），直接打开是乱码
- 官方"备份到电脑"产物：`<root>\Backup\<wxid>\<hash>\files\1\`，含
  ChatPackage/Index/Media/*.tar.enc（1.7GB 量级）——**只有微信自己能还原**，
  第三方工具读不了，别白费劲
- 陷阱：某些"迁移/备份"目录（radium/users、mmkv、小程序缓存）**没有聊天库**，
  先确认 db_storage/message 存在再继续

## 工具生态现状（被 DMCA 反复打击，2026-08）
- `LC044/WeChatMsg`（留痕）：**已停更**，只适配老版微信 3.x；GitHub 无 release
- `ycccccccy/wx_key`：代码被删（README 是讽刺文）；**fork 保留源码+DLL**
  （如 takeaway1/wx_key，40MB，assets/dll/wx_key.dll）——但官方版 DLL 特征码
  只支持到微信 4.1.5
- `ylytdeng/wechat-decrypt`：下载返回 **HTTP 451**（法律原因）
- `WeFlow`/`EchoTrace`：README 只剩讽刺声明，代码删光
- **当前可用**：`ciphertalk-cli`（密语 CipherTalk 的 CLI，npm 发布，内置
  win32-x64/wx_key.dll 支持新版微信，实测 hook 成功 4.1.11.55）

## 推荐流程：miyu（ciphertalk-cli）
```bash
npm install -g ciphertalk-cli --registry https://registry.npmmirror.com
miyu status                 # 看配置/数据库状态
miyu key get --save         # 从微信进程提 64 位密钥（自动存 ~/.miyu/config.json）
miyu sessions               # 列会话；miyu messages <session> 查消息
miyu export [session]       # 导出聊天数据
```
- **关键坑：`miyu key get` 报"等待密钥超时(60s)" ≠ 失败**——`InitializeHook`
  已成功（DLL 注入+特征码匹配），只是微信没触发"读数据库"所以没截到密钥。
  解决：提取跑着的时候，**让微信实际点开聊天窗口**（触发读库）即可捕获。
  报 "Hook 微信进程失败...请尝试以管理员身份运行" 才是权限问题（UAC 弹窗需
  用户点"是"）；报 "模式匹配失败，找到0个结果" 才是版本不兼容
- 配置文件 `~/.miyu/config.json`；`miyu key set <64位hex>` 手动填密钥

## 手动提密钥（wx_key.dll 直调，无 CLI 时兜底）
DLL 接口（C 风格，x64）：`InitializeHook(pid)` → 轮询 `PollKeyData(buf,65)`
拿 64 位 HEX → 结束 `CleanupHook()`（必须调，否则微信内残留 shellcode 可能
导致后续崩溃）。Python ctypes 可调。
- **DLL 与脚本路径不能含中文字符**（README 明确：中文路径 DLL 加载失败）——
  复制到 `D:\tools\wxkey\` 这类纯英文路径
- 微信进程名 `Weixin.exe`，多 PID 取内存最大的主进程
- `tasklist` 输出是 GBK：`subprocess.run(..., encoding='gbk', errors='ignore')`
- **CompanyName 校验大坑**：CipherTalk 版 wx_key.dll 校验调用进程的
  CompanyName——Python.exe（"Python Software Foundation"）会被拒
  （`Invalid CompanyName`），node 进程（miyu）可通过。所以提密钥一律走
  `miyu key get`，不要用 Python 直调 CipherTalk 的 DLL

## 版本对照（2026-08 实测）
- 微信 4.1.11.55（本机）→ CipherTalk 内置 wx_key.dll 可 hook ✓
- ycccccccy 官方 wx_key.dll → 只到 4.1.5，新版特征码失配 ✗

## 解密后导出 TXT（wechat-export-toolkit）
- `week-wyk/wechat-export-toolkit`：`01_decrypt_v4.py`（解密 4.x 库，可
  `--wechat-dir` 指定数据根）→ `02_export_txt_identified.py`（导出带
  `[我]/[对方]` 标记的 TXT），正好喂 dot-skill 类角色蒸馏
- 密钥来自 miyu key get 或手动 set

## 纯 Python 解密（实测成功：26库解密、620会话29万条文本，2026-08-14）
即使 miyu 连接报 `wcdb_init() 错误码 -1006`（WCDB 库不兼容/微信占用），
**照样能用独立 Python 脚本解密**——算法见 `references/decrypt-v4-python.md`，
可复用脚本 `scripts/decrypt_wechat_v4.py`：
1. 每库读前 16 字节盐 salt；`mac_salt = salt 异或 0x3a`
2. `key = PBKDF2(passphrase=密钥hex字节, salt, 32字节, 256000次, SHA512)`
3. `mac_key = PBKDF2(key, mac_salt, 32字节, 2次, SHA512)`
4. 逐页解密（页 4096B，第 1 页含盐）：AES-256-CBC，IV 在页尾，
   HMAC-SHA512(数据+页号) 校验，输出标准 SQLite（写 `SQLite format 3` 头）
依赖仅 `pycryptodome`（pip install pycryptodome）
- 本机已解好：`D:\tools\wxkey\decrypted\`（保持 db_storage 子目录结构）；
  密钥在 `~/.miyu/config.json` 的 keyHex

## 解密后查询（sqlite3 直接读）
- `decrypted\message\message_0~N.db`：每个会话一张表 `Msg_<hash>`，
  列含 `local_type`（1=文本）、`create_time`（unix秒）、`real_sender_id`、
  `message_content`；文本消息 content 格式：第一行 `wxid:\n` + 消息正文
- `decrypted\contact\contact.db`：`contact` 表（username/remark/nick_name），
  找联系人备注/昵称；`chat_room` 表看群
- 多库合并导出：5 个 message 分片分别查后按 create_time 排序合并

## 密钥提取最佳时机（2026-08-14 实测）
微信**已登录很久**时 `miyu key get` 大概率超时（库早读完，hook 截不到）。
最可靠：**退出微信（taskkill /F /IM Weixin.exe + WeChatAppEx.exe）→ 重新登录**，
登录瞬间跑 `miyu key get --save`，登录过程微信必读库、必截到。

## 按联系人提取全部发言 + 人物画像（dot-skill 素材实战，2026-08-14）
场景：使用者要"读取XX的聊天记录"（为 dot-skill 蒸馏人物备料）→ 三步：
1. **定位人**：`contact.db` 的 `contact` 表按 `remark LIKE '%名%'` 找 username（wxid）；
   注意昵称≠备注，都要搜
2. **找会话表**：多库遍历 `sqlite_master` 里 `Msg_%` 表，
   `SELECT COUNT(*) WHERE message_content LIKE '%<wxid>%'` 命中>0 即该人参与的表
   （大群会几万条，个人发言只是其中一部分；别以为整表都是 TA 的）
3. **提取发言**：`message_content` 以 `<wxid>:` 开头的行 = 该人发言
   （消息格式第一行就是发送者 wxid）；多库按 `create_time` 排序合并。
   只取 `isinstance(content, str)` 的行——bytes 是压缩/图片消息，跳过
- 产出：`桌面/XX聊天记录_N条.txt`（时间戳+内容，存档/喂 dot-skill）
- 人物画像：jieba（`pip install jieba -i 清华源`）词频 + TF-IDF 关键词 +
  月份/钟点分布 + 微信表情 `\[([^\[\]]+)\]` 统计 + 风格印象（短句/爱调侃/自称等），
  生成 `桌面/XX人物画像.txt`
- 密钥用后可清理：`~/.miyu/config.json` 直接删（miyu 会重建），
  脚本里硬编码 hex 删掉；解密好的库与桌面文件不受影响，要再解就重新
  `miyu key get --save`（微信重启时机见上）

## 输出用途
- dot-skill / colleague-skill 素材：TXT（时间戳 + [我]/[对方] + 内容）
- 注意隐私：这些工具都是本地运行，别把聊天内容贴进公开仓库/对话

## 人物分身蒸馏的第二个素材源：Hermes 会话库（2026-08-14 使用者分身实战）
给**自己/使用者/常聊天的人**做"数字分身"时，别只挖微信库——Hermes 自己的
会话库 `C:\Users\使用者\AppData\Local\hermes\state.db` 里 `messages` 表
`role='user'` 就是使用者跟 AI 说话的原话（2300+ 条，2026-06 起），是"他会
怎么说"最真实的样本。完整提取/过滤/画像/技能模板见
`references/hermes-session-distill.md`。
