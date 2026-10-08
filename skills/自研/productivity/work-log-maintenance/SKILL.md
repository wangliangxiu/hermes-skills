---
name: work-log-maintenance
description: 记录最近做的事/整理工作日志时用。维护近期工作记录txt与台车项目推进日志。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
---

# 工作日志维护 (Work Log Maintenance)

使用者有"记录最近做过的事"的习惯，两类日志是长期约定：

| 日志 | 位置 | 用途 |
| --- | --- | --- |
| 近期工作记录.txt | 桌面根目录 | 通用工作记录，按日期倒序整理近期会话 |
| 项目推进日志.txt | 台车项目文件夹内 | 台车项目每次新进展主动追加，格式固定 |

## 触发条件

- "记录一下最近做的事 / 记录一下别忘了"
- "整理一下日志 / 工作记录"
- 台车项目有新进展（追加《项目推进日志.txt》）
- 使用者想回顾自己这几天干了啥

## 流程：记录"最近做了啥"

1. `session_search()` 不带参数 browse 最近会话（返回最近 3 个会话：标题+预览+时间）
2. 对关键会话用 `session_search(session_id=...)` 读详情（或只看 bookend 首尾），提取每个会话的主题、产出物、关键决策
2.5 **当天是一条超长会话（几百条消息、十几万字）时，别整体读** —— session_search 一次性灌进来会吃掉大半个上下文。直接查会话库 `HERMES_HOME/state.db`（只读打开 `file:...?mode=ro`），按角色过滤导出到 Temp 下的 txt，再分段 read_file：
   ```python
   con = sqlite3.connect("file:" + os.path.expanduser(r"~\AppData\Local\hermes\state.db") + "?mode=ro", uri=True)
   rows = con.execute("SELECT id, role, content, timestamp FROM messages WHERE session_id=? ORDER BY id", (sid,)).fetchall()
   ```
   只想知道使用者说了什么 → 过滤 `role='user'`（一天的原话通常才一万多字）；要抠细节再加 `assistant`；`tool` 角色的全是工具输出，默认丢掉。导出时滤掉噪音，见「坑」。
3. 先查桌面/项目文件夹有没有已存在的日志文件（search_files target='files'，pattern 如 *日志*.txt / *记录*.txt），避免重复建
4. 有旧文件 → read_file 读内容，按日期倒序更新/追加；无 → 新建
5. write_file 写 .txt（使用者要求 txt 不要 md），分隔线 ═══ 开头
6. 每日期段：日期 + 主题 + 做了什么（要点化，附产出物绝对路径）
7. 底部留「后续约定」段（未完成事项、待办、承诺过的事）
8. 回复使用者时给出文件绝对路径

## 格式要点

- 文件开头：═══ 分隔线 + 标题 + 记录时间
- 按日期倒序（最近在上），一天多主题分点
- 每条写清产出物路径（如 桌面\考研备考计划_河南理工土木学硕.txt）
- 待办/后续约定单独成段，别混在完成事项里
- 只留最新版：更新旧日志用 write_file 整体重写，不另存副本
- 台车项目推进日志固定格式：日期/主题/背景/做了什么/产出物/关键思考/下一步

## 坑

- 不要用 memory 存工作记录——任务进度/完成日志一周后就过期，是 session_search 的职责；memory 只存长期复用的偏好与事实
- 使用者说"别忘了"= 落到桌面 txt + 告知路径，不是口头答应
- 临时脚本（生成/更新日志用的 .py）用完即删，不留桌面
- 日期用会话真实时间（session_search 的 when 字段），不猜不编
- **`role='user'` 的消息里混着系统通知**：后台进程完成/退出通知（正文含 `Background process`）、`Operation interrupted: ...`。做"原话记录"时必须滤掉，否则日志里全是噪音
- **带 `[OUT-OF-BAND USER MESSAGE]` 的其实是使用者当场追加的话** —— 不是噪音，别连它一起滤掉；剥掉标记、改写成「（当场追加）…」放进记录
- **上下文压缩会让同一段回话在消息表里重复出现**（还会留下 `[CONTEXT COMPACTION ...]` 标记）→ 阅读时略过，统计条数/去重时按 (role, content) 去重
- 导出/生成的 txt 与目录里已有 txt 保持同一编码（UTF-8；要 Windows 记事本排版好看就 newline="\r\n"）
- 写作铁律同样适用：拿不准的事件细节（时间、数字）宁可不写或写"待确认"

## 验证

- 写完后 read_file 确认内容完整、路径正确
- 回复中给出绝对路径（如 C:\Users\使用者\Desktop\近期工作记录.txt）
