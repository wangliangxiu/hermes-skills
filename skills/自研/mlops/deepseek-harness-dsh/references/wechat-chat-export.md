# 微信聊天记录提取（dot-skill 素材准备，2026-08-14 实测）

使用者想用 dot-skill 把某个人"蒸馏"成角色技能，素材源=微信聊天记录。实测现状与路径：

## 数据位置（本机 Windows）

| 位置 | 内容 | 可用性 |
|:---|:---|:---|
| `D:\微信数据备份\WeChat\`、`D:\微信数据备份\xwechat\` | 旧迁移备份 | ❌ 只有缓存/小程序/MMKV 配置，**无聊天记录库** |
| `D:\xwechat_files\Backup\wxid_xxx\<hash>\files\1\` | 微信官方"备份到电脑"的备份 | ⚠️ 加密专有格式（ChatPackage/Index/Media/*.tar.enc），**只有微信能还原**，第三方读不了 |
| `D:\xwechat_files\<wxid>_<hash>\db_storage\message\message_0~N.db` | **聊天记录本体数据库** | ⚠️ SQLCipher 加密（文件头随机字节，非 `SQLite format 3`），需密钥 |

- 微信数据根目录 = `D:\xwechat_files\`（账号目录形如 `wxid_vdzc8nun1idr22_7dcb`）
- 判断是否加密：读文件头前16字节——随机字节=加密；`SQLite format 3\0`=明文
- 手机"聊天记录迁移与备份→备份到电脑"产出的是 `Backup\` 下的官方格式，**不是**可直接读的文本

## 导出路径（需要工具+登录态）

1. 电脑微信**保持登录**（密钥在微信进程内存里，退出就没了）
2. 下载 **WeChatMsg（留痕 / MemoTrace）**：github.com/LC044/WeChatMsg（4万+ star）
   - 本机 github.com 被墙 → 让用户浏览器打开 release 页下载 Windows 安装包
     （`MemoTrace_xxx_win64_setup.exe` 或 `WeChatMsg_xxx_win.zip`，100~200MB）
   - 官网 memotrace.cn 也可（本机 curl 不通时浏览器试）
3. 运行工具 → 自动检测微信 → 选账号 → 导出聊天记录为 txt / HTML / Word / CSV
4. 导出的文本喂给 dot-skill 蒸馏

## 注意
- 微信 4.x/5.x 新版数据库（xwechat_files/db_storage/message_*.db）的密钥提取
  与老版（WeChat Files\wxid\Msg\Multi\MSG.db）不同，工具版本要支持新版微信
- 两个账号：`wxid_vdzc8nun1idr22`（5个message分片，主号）、`wxid_b5hban9leqpj22`（1个分片）
