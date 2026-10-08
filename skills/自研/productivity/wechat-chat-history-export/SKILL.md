---
name: wechat-chat-history-export
description: 微信4.x聊天记录解密导出。触发词：微信聊天记录、解密微信、导出聊天、wx_key、miyu。
---

# 微信4.x 聊天记录解密与导出

微信4.x（数据目录 `xwechat_files`，内核 radium）的聊天记录库是 SQLCipher/WCDB 加密的。本技能记录完整链路：定位数据库 → 提取密钥 → 解密 → 查询导出 TXT。

## 1. 数据位置与结构

- 微信数据根目录：`D:\xwechat_files\`（或 `Documents\xwechat_files`）
- 账号目录：`D:\xwechat_files\<wxid>_<hash>\`（如 `wxid_vdzc8nun1idr22_7dcb`）
- 数据库目录：`db_storage\`，关键子目录：
  - `message\message_0.db ~ message_N.db`（消息分片库）、`message_fts.db`（全文索引）
  - `contact\contact.db`（联系人：username/remark/nick_name）
  - `session\session.db`（会话）
- 加密特征：文件头是随机字节（不是 `SQLite format 3`）
- **微信官方"备份到电脑"格式（`Backup\<wxid>\<hash>\files\1\`，含 ChatPackage/Media/*.tar.enc）解不开**，只有微信自己能还原，别浪费时间。

## 2. 提取数据库密钥（关键步骤）

密钥在微信进程内存里，登录/读库时出现。工具链曾被 DMCA 打击（wx_key、wechat-decrypt、WeFlow 都被删代码），**当前可用方案：CipherTalk CLI（miyu）**。

### 2.1 安装 miyu

```bash
npm install -g ciphertalk-cli --registry https://registry.npmmirror.com
```

### 2.2 提密钥（必须趁微信重启/登录时）

**核心坑：微信的数据库密钥只在"登录/首次读库"时被读取**——微信开太久就抓不到（报"等待密钥超时"）。正确流程：

1. 关掉微信全部进程：`taskkill /F /IM Weixin.exe` + `WeChatAppEx.exe`
2. 重新打开微信并登录
3. 登录完成后立刻（60秒内）在微信里点开几个聊天窗口触发读库，同时跑：
   ```bash
   miyu key get --save
   ```
   成功返回 64 位 hex 密钥并自动保存到 `~/.miyu/config.json`。

**坑：wx_key.dll 校验调用者 CompanyName**——用 Python ctypes 调用 DLL 会报 `Invalid CompanyName: Python Software Foundation`；miyu（node 环境）能通过。不要手写 Python 调 DLL 提密钥，直接用 miyu。

**坑：密钥只在登录期出现**——如果 miyu 报"等待密钥超时(60s)"而不是"Hook失败"，说明 Hook 成功但错过了读库时机，重启微信再试。

### 2.3 配置数据库路径

miyu 的 `config set --db-path` 参数在 git-bash 下可能不生效，直接手写 `~/.miyu/config.json`：

```json
{
  "keyHex": "<64位hex>",
  "dbPath": "D:/xwechat_files/<wxid>_<hash>/db_storage",
  "wxid": "<wxid>_<hash>"
}
```

## 3. 解密数据库（纯 Python，不依赖 miyu/WCDB）

miyu 打开数据库可能报 `wcdb_init() 错误码 -1006`（微信占用/版本不兼容），**改用独立解密脚本**（算法来自 wechat-export-toolkit 的 wxManager）：

- 算法：每页 4096 字节独立 AES-256-CBC；密钥 = PBKDF2(密钥hex, 文件头16字节盐, 256000次, SHA512)；HMAC key = PBKDF2(解密key, 盐^0x3a, 2次, SHA512)；每页末尾保留区（IV + HMAC 截断 + 填充）
- 依赖：`pip install pycryptodome`
- 脚本：`scripts/decrypt_v4_db.py`（传入密钥、源 db_storage、输出目录）
- 输出为标准 SQLite 文件（"SQLite format 3"头）

## 4. 查询与导出

解密后直接用 `sqlite3`：

- 联系人：`contact.db` 的 `contact` 表（`username`=wxid，`remark`=备注，`nick_name`=昵称）；群聊在 `chat_room` 表
- 会话表：`message_N.db` 中每会话一张表 `Msg_<hash>`（`sqlite_master` 里 `name LIKE 'Msg_%'`）
- 找某人的会话：`message_content LIKE '%<wxid>%'` 扫描各 `Msg_` 表（Name2Id 表无直接映射，不可靠）
- 文本消息：`local_type=1`；`message_content` 格式 = 第一行发送者 wxid（`wxid_xxx:`）+ 换行 + 消息正文；`create_time` 是 unix 秒
- 图片/语音等：`local_type=3/34/47` 等，`message_content` 是压缩 blob（不易读）
- 导出格式参考：`[%Y-%m-%d %H:%M] 内容`，按时间排序

## 5. 关键坑汇总

- 官方备份格式（Backup 目录）≠ 可读数据，别解
- 密钥只在登录期出现 → 先杀微信再登录再提
- 提密钥用 miyu（node），不要用 Python ctypes 调 DLL（CompanyName 校验）
- DLL/工具目录避免中文路径（Windows DLL 加载问题）
- 解密脚本里不要硬编码密钥（用完即清）；密钥用完删除 `~/.miyu/config.json`
- GitHub 被墙时：`curl -x http://127.0.0.1:17890 <github url>`（使用者电脑本地代理）

## 6. 相关工具链

- CipherTalk（miyu）：https://github.com/ILoveBingLu/miyu（活跃，2026-08 仍更新）
- wechat-export-toolkit：https://github.com/week-wyk/wechat-export-toolkit（解密+导出 TXT，含算法参考）
- 被 DMCA 删代码不可用：wx_key（ycccccccy，fork takeaway1 保留源码）、wechat-decrypt、WeFlow
