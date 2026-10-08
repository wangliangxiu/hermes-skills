---
name: hermes-backup-migration
description: "备份/迁移Hermes全部数据到另一台电脑、或只把某个任务的进展打包交给另一台机器的 Hermes 接着干时用。含打包清单、SQLite一致性备份、任务级交接包、恢复步骤。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [hermes, backup, migration, data]
---

# Hermes 数据备份与迁移

## 触发场景
- 用户要把 Hermes 的所有信息打包带走（"做个压缩包放桌面""迁移到另一台电脑""另一台电脑上也想用你"）
- 恢复/还原 Hermes 数据到新安装
- 定期备份 HERMES_HOME

## 关键路径 (Windows)
- HERMES_HOME = `C:\Users\<用户名>\AppData\Local\hermes`（不是 ~/.hermes！Windows 上在 AppData\Local）
- 记忆: `memories/MEMORY.md` + `memories/USER.md`
- 人设: `SOUL.md`
- 会话: `sessions/*.json`（旧格式）+ `state.db`（SQLite 主库，可能 160MB+）
- 技能: `skills/`（40MB+，上千文件，走 os.walk 时搜索/统计会慢）
- 定时任务: `cron/jobs.json`
- 配置与密钥: `config.yaml`、`.env`、`auth.json`
- 其他: `kanban.db`、`channel_directory.json`、`gateway_state.json`、`processes.json`、`mcp_request.json`、`verification_evidence.db`

## 打包清单
包含: memories/、skills/、sessions/、cron/、config.yaml、.env、auth.json、SOUL.md、kanban.db、state.db（一致性备份版）+ 上述零散 json。

排除（新电脑重装就有 / 缓存 / 运行时文件）:
- `hermes-agent/`（源码）、`bin/`（程序本体）
- `logs/`、`cache/`、`audio_cache/`、`image_cache/`、`images/`、`pastes/`、`lsp/`、`sandboxes/`、`whatsapp/`、`workspace/`、`state-snapshots/`、`__pycache__/`
- `state.db-wal` / `state.db-shm`（SQLite 运行时文件，不能用，用 backup API 代替）
- `*.lock`、`config.yaml.bak`

## 步骤
1. 确认桌面路径存在（os.makedirs）
2. **state.db 正在使用（WAL 模式）**，直接复制会损坏/不完整。用 sqlite3 backup API 做一致性快照：
   ```python
   con = sqlite3.connect(src); out = sqlite3.connect(tmp)
   con.backup(out); out.close(); con.close()
   ```
3. **zip 根目录用 `hermes/` 前缀** — 解压后内容直接对应新机 HERMES_HOME，覆盖粘贴即可，不需要用户再挪目录
4. 验证（必须做）: 用 `collections.Counter(zipfile.ZipFile(path).namelist())` 检查**无重复条目**；确认关键文件都在（memories/MEMORY.md、SOUL.md、config.yaml、.env、auth.json、state.db、cron/jobs.json、skills/ 有内容）
5. 用完即删临时脚本（用户规矩：临时脚本不留）

## 恢复步骤（新电脑）
1. 装好 Hermes（`curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash`）
2. 解压 zip 得到 `hermes/` 文件夹
3. 把 `hermes/` 内容整个覆盖到新电脑 `C:\Users\<新用户名>\AppData\Local\hermes\`
4. 启动 hermes — 记忆/技能/会话/人设全都在

## 坑（都踩过）
- **Python zipfile 重复条目警告** ("Duplicate name"): 同一文件被显式添加 + os.walk 各加一次 → 只保留一个来源。用 os.walk 统一处理顶层文件，显式添加过的文件必须加进 EXCLUDE_FILES
- **state.db 双重添加**: db_backup 写入 `hermes/state.db` 后 os.walk 又扫到原文件 → EXCLUDE_FILES 必须含 `"state.db"`（连同 -wal/-shm）
- **中文用户名在 git-bash 里 $HOME 乱码**（`cd $HOME/...` 报 No such file）→ 用正斜杠 `"C:/Users/使用者/AppData/Local/hermes"` 或 `$HERMES_HOME` 环境变量（该变量值正确）
- **du 全目录超时**: `hermes-agent/` 源码目录大，`du -sh` 整个 HERMES_HOME 会卡 60s+ → 分目录统计（`du -sh memories skills sessions`），别一次扫全部
- **包内含 API 密钥（.env/auth.json）和全部聊天记录** → 交付时提醒用户走可信渠道传输（U盘/网盘私有分享），别发公开链接
- 压缩后通常比原始小很多（465MB → 134MB），zip 压缩 JSON/文本效果好

## 任务级交接包（只交一个任务、不全量迁移时）

使用者换机器接着干时说"把今天做的东西整理一下打成包放桌面，我回家让台式机的 hermes 去完成后面的内容"
—— 交的是**一个任务的进展与产出**，不是整台机器。这时**不要**套用上面的全量清单，包长这样：

```
<任务名>交接包_<日期>\          桌面根目录，再出同名 .zip 方便拷走
00_交接说明_先看这个.txt     接手方读这一份就够：任务背景 / 本阶段做了什么 / 进度到哪 /
                             接手步骤 / 红线与口径 / 文件地图 / 下一步
01_<谁>口述的原话.txt        "说了多少记录多少" = 一字不改的原话，按时间顺序（上午/下午分段）
02_会话完整记录.txt          双方对话（含自己的回话），抠细节用
03_产出文件清单.txt          按 mtime 盘点出的新建/改动文件 + 一句话用途
技能_装到<机器>\             相关技能整目录（SKILL.md + references/ + scripts/），接手方直接拷进 skills/
素材_进度记录\               进度索引、串讲稿、待补清单等
资产\                        图库、模板、可复用产出
```

- 技能目录**工作副本与已装副本都要带上/对一遍**（`diff -rq` 确认一致），包里的那份是给目标机拷进 `skills/` 的
- 交付时一并说清：参照资料在哪个外设上（移动硬盘路径）、技能装到目标机哪个目录、接着干该说哪句启动语
- 复原"本阶段做了什么"、盘点产出物、打包验证的具体做法 → `references/任务交接包.md`

### 同一台机器上的会话接力（上下文过长 / 被 503 挡住时，不换机器）

会话太长会被 API 服务端挡回来（DeepSeek 报 503 "Service is too busy"，日志里带 msg 数与 token 数）。
别硬撑、也别让使用者重开会话从零解释——写一份交接说明放**项目文件夹里**（跟着项目走，
不放桌面根目录），文件名 `<项目名>_交接说明.txt`，与项目自己的状态文件（项目大纲、项目说明、
素材库）并列。六块结构，缺一块接手方就得问：

1. 这是什么项目：赛道/截止时间/slogan/最终定下的结构/合规红线
2. 现在做到哪了：每个模块一行 + 实测结论 + 已知问题（待改的明写"待改"）
3. 环境与怎么跑：虚拟环境路径、已装依赖、启动命令顺序、密钥从哪读、测试账号/钱包地址
4. 坑：踩过的（原生程序处理不了中文路径、缓存覆盖样式这类），一句一条，别写成长篇
5. 待办：拆成「卡在使用者身上的」和「我这边要做的」，各自标优先级
6. 跟使用者协作的规矩

接力步骤（新会话这边）：
1. 使用者说"刚才交接的东西找一下"时，**先按文件名搜**（`search_files` 匹配 `*交接*`），一到三个候选
   连绝对路径一次报给他点；`session_search` 搜"交接"也能一次给出文件绝对路径。
   **别在桌面全树跑 mtime/内容扫描**（项目目录下上千文件，命令会卡成后台任务让使用者干等）。
2. 读文件，**简短复述**现状 + 待办，让使用者点头——别一上来重跑环境、重读一遍代码。
3. 使用者接着逐条给设计决策时：**只记录，不改代码，也别提前读代码探路**。他会用"别动手"
   "等我说完"来拦，听到立刻停手，等他一句"开工/动手"再动。
4. 决策攒够、动过手之后，用 `patch` 追加/修交接说明（`write_file` 是整体覆盖，会吃掉原文）。

## 支持文件
- `scripts/backup_hermes.py` — 通用打包脚本，改顶部 HERMES_HOME / DESKTOP 即可直接跑
- `references/任务交接包.md` — 任务级交接包的复原、盘点、打包与验证细节（含查 state.db 导出会话记录的代码）
