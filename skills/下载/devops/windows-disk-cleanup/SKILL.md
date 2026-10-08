---
name: windows-disk-cleanup
description: Windows C盘空间排查与安全清理。触发词：C盘满了、磁盘空间、清理缓存、DriverStore、WinSxS。
---

# Windows 磁盘空间排查与安全清理

适用：Windows 11 中文系统（用户 C 盘经常接近满，238G 用 95% 是常态）。
铁律：只清缓存，不碰用户数据；系统目录只用官方工具，绝不手动删。

## 一、排查命令（MSYS/bash 环境）

### du 在 Windows 大目录会超时
- MSYS 的 `du -sh` 遍历 WinSxS/用户目录等几十万文件目录会卡死超时
- **改用 PowerShell 原生统计**（快得多）：
```bash
powershell.exe -NoProfile -Command 'foreach($p in @($env:LOCALAPPDATA, $env:APPDATA, "C:\ProgramData", ($env:USERPROFILE+"\Downloads"))){ $s=(Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; Write-Output ("{0,-50} {1,8:N2} GB" -f $p, ($s/1GB)) }'
```
- 看细分（Top 目录）：
```bash
powershell.exe -NoProfile -Command 'Get-ChildItem $env:LOCALAPPDATA -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object { $s=(Get-ChildItem $_.FullName -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum; [PSCustomObject]@{Dir=$_.Name; GB=[math]::Round($s/1GB,2)} } | Sort-Object GB -Descending | Select-Object -First 10 | Format-Table -AutoSize'
```

### 中文用户名传给 PowerShell 会乱码
- `C:\Users\使用者\...` 通过 bash 传给 powershell.exe 时中文丢失（变量变空、路径乱码）
- **用环境变量代替硬编码中文路径**：`$env:LOCALAPPDATA` / `$env:APPDATA` /
  `$env:USERPROFILE`，且整个 -Command 参数用单引号包住防 bash 展开 `$`

## 二、系统目录知识（用户常问，必须答对）

### C:\Windows\System32\DriverStore\FileRepository（驱动仓库）
- 存放所有驱动程序的安装副本（当前+历史+更新自动下载），几 GB 正常
- **不能手动删文件夹**——删了驱动失效（显卡驱动没了分辨率乱）
- 安全清理：磁盘清理 → 清理系统文件 → 勾选"设备驱动程序包"（系统自动删不再用的旧驱动）

### C:\Windows\WinSxS（Windows 组件存储）
- 存放系统组件多版本副本，支持更新回滚/按需功能，**绝对不能删**
- 安全清理旧版本组件（管理员 CMD）：
  ```
  Dism /Online /Cleanup-Image /StartComponentCleanup
  ```
- 注意：WinSxS 显示大小含硬链接，实际占用比显示的小

### 其他可安全处理的系统项
- `hiberfil.sys`：休眠文件，不用休眠可 `powercfg /h off` 释放几 GB
- `C:\Windows.old`：升级残留，磁盘清理可删
- `C:\Windows\SoftwareDistribution\Download`：Windows 更新缓存，磁盘清理会处理

## 三、用户层可清理清单（按收益排序）

| 位置 | 常见大小 | 清理方式 |
|:--|:--|:--|
| AppData\Roaming\Tencent（微信/QQ） | 5~10 GB | 微信设置→存储空间→清缓存（聊天记录别勾） |
| AppData\Local\NetEase（网易云等） | 5~10 GB | app 内清缓存 |
| Downloads | 几 GB~几十 GB | 用户自己判断删除 |
| AppData\Roaming\Trae CN 等 IDE | 3~6 GB | IDE 设置里清缓存/索引 |
| AppData\Local\JianyingPro（剪映） | 3~6 GB | 剪映设置清草稿/缓存 |
| temp / pip cache / Chrome cache | 几十 MB~1 GB | 可安全删（pip cache purge 等） |

实测参考（2026-08）：Local 35GB(网易8.7/剪映5.6/微软4.2/软件本体3+)、
Roaming 17.8GB(腾讯8.0/Trae 5.7)、Downloads 9.4GB、ProgramData 8.5GB。

## 四、微信数据迁移到D盘（用户要求"复制再删除"时走完整流程）

### 前置铁律
- **微信/QQ 运行中禁止复制或删除其数据目录**（文件占用会损坏）——先查进程：
  `powershell Get-Process -Name Weixin,WeChat,WeChatAppEx -ErrorAction SilentlyContinue`
- 让用户"托盘图标右键→退出"（只关窗口不算退出），确认进程没了再动手
- 工作工具（WXWork企业微信/WeMeet会议/TIM）可能含聊天记录/会议文件，
  删除必须**单独确认**，绝不默认一起删；日志/游戏类（Logs/WeGame/QQ/游戏辅助）
  是纯缓存可直接删

### 迁移流程（每一步验证）
```powershell
# 1) 确认微信已退出，D盘建目录
New-Item -ItemType Directory -Path "D:\微信数据备份" -Force

# 2) robocopy 复制（/E 子目录 /COPY:DAT 数据+属性+时间戳）
#    robocopy exit code 1 = 成功复制了文件，不是错误！（0=无变化，1=有复制）
robocopy "$env:APPDATA\Tencent\xwechat" "D:\微信数据备份\xwechat" /E /COPY:DAT /R:2 /W:1

# 3) 验证完整性：对比 C/D 两边的 文件数 + 总大小，必须完全一致才允许删
function Stat($p){ $f=Get-ChildItem $p -Recurse -Force -File -ErrorAction SilentlyContinue; $s=($f | Measure-Object -Property Length -Sum).Sum; [PSCustomObject]@{Path=$p; Files=$f.Count; GB=[math]::Round($s/1GB,3)} }
Stat "$env:APPDATA\Tencent\xwechat"; Stat "D:\微信数据备份\xwechat"

# 4) 验证一致后才删 C 盘原件
Remove-Item "$env:APPDATA\Tencent\xwechat" -Recurse -Force
```

### 关键知识点
- 微信4.0 数据在 `Roaming\Tencent\xwechat`，旧版在 `Roaming\Tencent\WeChat`，都要迁
- **迁移后必须提醒用户**：打开微信→设置→文件管理→存储位置改到备份目录
  （如 `D:\微信数据备份\`），否则微信重新初始化空目录、聊天记录"消失"；
  若登录后显示空，把路径指到 `D:\微信数据备份\xwechat` 再重启
- 建议用户对重要聊天记录再做微信自带"备份与迁移"双保险（D盘硬盘故障风险）
- 汇报格式：✅清了什么（大小）+ 共腾出多少G + ⚠️需要用户做的事（改路径）

## 五、建议顺序
1. 系统级磁盘清理（开始菜单搜"磁盘清理"→清理系统文件→勾选更新清理/临时文件/设备驱动包）——零风险
2. 微信/网易等 app 缓存（收益最大，先问用户确认）
3. Downloads 用户自己挑
4. 需要时 powercfg /h off、DISM 清 WinSxS 旧组件

## 五、边界
- 永远不替用户删除 Downloads 或聊天记录里的具体文件——列清单给用户选
- 系统目录（DriverStore/WinSxS）只给官方清理方法，不直接操作
