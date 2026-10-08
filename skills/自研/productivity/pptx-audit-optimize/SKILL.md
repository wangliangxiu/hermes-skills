---
name: pptx-audit-optimize
description: PPT程序化体检与优化。触发词：优化PPT、PPT体检、报名PPT、改版、文字溢出、图片统一。
---

# PPT 程序化体检与优化

当用户让"优化/检查/改版/调PPT"（参赛PPT、报名PPT、汇报PPT等）时使用。核心思路：**程序化体检 → 安全修复 → 复验全绿**，不靠肉眼猜。

## 环境前提
- 本机 Office16：`C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE` + win32com（python-pptx 无法渲染/测量文本，必须用 COM）
- `D:/python/python.exe` 装有 python-pptx / win32com / PIL
- 体检脚本现成：`scripts/ppt_health_check.py <pptx> [导出目录]`

## 工作流

### 1. 体检（三查）
- **布局查**：python-pptx dump 每页形状（类型/坐标/尺寸/文本），找：
  - 同页多图/多卡片尺寸不一致（如三张图 2.23in vs 2.13in）
  - 说明框 y 坐标错位、底部不对齐
  - 残留空 run（小字号空文本，无视觉影响但可清理）
- **渲染查**：COM `slide.Export(..., 'PNG', 1280, 720)` 导出 → PIL 像素统计（均亮/白底%/深色%）：大片白底=白屏图；封面/尾页深色、内页浅色=正常主题
- **溢出查**：COM `TextRange.BoundHeight` vs `shape.Height - MarginTop - MarginBottom`，`bh > usable + 4` 判定溢出

### 2. 修复（安全三则）
- **数字/文字**：先备份到 TEMP（`shutil.copy2`）；替换必须匹配**完整旧串**（子串匹配会误伤其他含关键词的段落）；用"清空 runs 只留第一个、保留其格式"法重写；改完**对比备份的 run 结构（字号/粗体/字体）**验证格式无损
- **图片统一**：保持宽高比用**居中裁剪**（`pic.crop_top/crop_bottom`），绝不拉伸变形
  - 裁剪量：`half = (1 - (现宽/现高)/(目标宽/目标高)) / 2`，目标宽高比=与其他图一致
- **图片替换（换真实截图）**：新图先裁剪到 shape 目标比例（cur_ratio<目标→裁高，>→裁宽）防拉伸 → 用 r:embed 定位真实 media 路径 → zipfile 换 blob（见 `references/media-swap-and-live-screenshot.md`）→ 读回 md5 验证
- **数字口径**：PPT 里的市场/财务数字一律对照**定稿文档**（BP/合同），不自行编造；发现括号明细与总额不符（如 4.8+1.5+3.6+0.4+1.5=11.8 ≠ 首年10.3万）以定稿口径为准修正
- **多文档口径统一（BP/QA/路演稿/PPT 一次改全）**：财务/团队口径改版时（4人→3人、买断模型调整等），旧数字会残留在多处——BP 的成本结构/盈利预测/市场规模节、QA 题库财务题、路演稿商业模式段、PPT 财务页（实测：BP 4.3 还写"4人×1万×2月=8万"而 4.4 已是"3人6万"；QA 还写"16.2万/9.1万/明工"）。动 PPT 前先 search_files 扫全库旧口径关键词（团队人数/成员姓名/旧金额/订阅字样），把 BP/QA/路演稿一并修掉再改 PPT；**关键财务数字先 clarify 与用户对齐再动手**（财务是 BP 核心，改错=瞎编）——一次问清：买断价、维保续费年费、收入排布、TAM/SAM/SOM 是否保留（买断制不涉渗透率时全删）、订阅制去留；财务预测保持简单直接（如"一年卖一家"），不做复杂逐年扩张表。审计清单见 `references/multi-file-口径-unification.md`

### 3. 复验
- 重新导出 PNG + 重新跑溢出检测，**全绿才交付**；数据修改再读回文本确认

## 坑（实测）
- **COM BoundWidth 不可信**：文本 218pt 宽、框 255pt 却仍换行——先查文本框左右内边距（默认各 7.2pt），MarginLeft/Right 归零 + 加宽框往往解决；判断是否真换行用 `TextRange.Lines().Count`（尾字落单行=换行），不要只看 BoundHeight
- **中文全角字符粗体大字号下比估算宽**（30pt 微软雅黑"万"≈30pt，"1,650万~4,950万"13字符≈218-236pt），别用字符数估行宽
- 子串匹配误伤（"固定成本"命中副标题/毛利段）→ 被误处理段落对比备份逐一确认
- 用户偏好"统一的啊"：同页图片尺寸、字号、卡片位置必须统一；优化时主动找不统一处
- 用户等久了会问"好了吗"：修复卡壳超 2 轮就交付当前成果 + 说明剩余问题，别无限迭代
- 命令被拦截 ≠ 用户拒绝：可能是确认框用户还没点（"我还没选择呢"）；不重试被拒命令，等用户明示
- **python-pptx `sh.image.filename` 不可用于定位 media 文件**：返回的是 basename（如 "image.png"），PPT 里多张图可能同名，zipfile 替换会**连坐所有引用者**（本次 6 图全指向 "image.png"）。正确定位：`blip = sh._element.find('.//' + qn('a:blip'))` → `rId = blip.get(qn('r:embed'))` → `slide.part.rels[rId].target_ref`（如 `../media/image2.png`）；替换前遍历全 PPT 所有图片 shape 的 r:embed→target，确认目标只被一个 shape 引用
- **文本关键词定位 shape 会误伤横幅**：`'3D 点云' in t` 会把底部横幅（"3D 点云分析 · 围岩智能识别 · …"）一起匹配移动，横幅从 y=5.60 被挪到 y=4.28 盖住正文说明。移动/改位置前先打印所有候选形状确认唯一，或加长度/完整匹配条件
- **按位置删卡片/形状组会漏删偏移形状**（团队页删人卡片实证）：一张人卡片 6 个形状——卡片背景/头像圆（无文本）+ 单字 + 名字/角色/描述文本框。位置启发式（left≈0.6/0.95）只删到 3 个，名字/角色/描述在 left=2.55（卡片内偏移量不同）全漏掉。做法：无文本形状按位置、有文本形状按**文本匹配**（'明工'/'设备研发管理'等）分别收集再删；删完**全量 dump 该页所有形状**验证残留 0 才保存。删卡片后剩余卡片要做 2+1 布局：第二行居中 left=(页面宽−卡片宽)/2（13.33in 页、5.9in 卡 ⇒ 3.715in），卡片内各元素按与卡片 left 的相对偏移同步平移
- **截图必须与标签真实对应**：像素深色占比 >50% ≈ 3D 渲染图，浅色+大量文字 ≈ 对话框。标签写"AI 设计助手"就必须放真实 AI 对话截图（🧑提问→🤖回复）；发现不符（标签下是深色渲染图）就真机重截，别用假图糊弄
- **真机截图软件界面（2026-08-14 血泪教训）**：
  - **优先用 `widget.grab()` 自渲染**（PyQt 把窗口内容直接渲染成 QPixmap，不经屏幕）——屏幕截屏法（ImageGrab.grab(bbox)）在窗口未置顶/被其他窗口遮挡时会**截到别的窗口内容**（本次真实事故：截到了使用者屏幕上的游戏画面，使用者当场识破\\\"你弄得是我的游戏截图，不是软件\\\"）
  - 只有 GL/OpenGL 内容（offscreen 无 GPU 上下文）才必须真机截屏，且要 SetForegroundWindow 确保置前、别让其他窗口挡着
  - `ctypes.windll.user32.GetWindowRect` 返回 int 不是结构体（AttributeError）——用 `win32gui.GetWindowRect`
  - 流程：启动主程序 → 切目标 Tab → 填输入/调内部 `_send()` → 轮询界面文本出现完成标记（`'✅ 设计完成' in dlg.toPlainText()`）→ widget.grab() 或置前截屏；窗口会闪现，截完立即 close
- **PPT 文本框整框匹配会漏改**（P12/P13 实证）：`sh.text_frame.text` 是整框拼接文本，用整框 startswith 判断只改到首段，框内后续段落（p3/p4）漏改。多段落文本框必须按段落级循环：`for para in sh.text_frame.paragraphs: t="".join(r.text for r in para.runs)` 逐段匹配替换
- **docx/pptx 文本可能集中在"软换行大段"**：docx 一个 w:p 内多个 w:br 软换行，read_file 显示多行、python-docx 是一个 paragraph。定位必须用 `contains`（find_contains）而非 startswith，否则漏改（BP 4.3固定成本/4.4盈利/7.1营收 实证）；改完读回 XML 全量搜关键字验证 0 残留
- **insert_paragraph_before 循环插入顺序**：`for txt in lines: paras[k].insert_paragraph_before(txt)` 正序循环即保持顺序；**禁止** reversed() 反转列表（SOW 六条变 ⑥⑤④③②① 倒序实证）
- **按范围删段落前先 dump 边界**：按 `range(title_idx, title_idx+n)` 删段可能误删相邻章节（误删 4.3 成本结构整节实证，靠从备份重跑脚本重建）。删除前打印待删每段文本确认，删完全量 dump 该区域验证；破坏性修改前先备份到 TEMP
- **git-bash /tmp ≠ Python 路径**：bash 的 /tmp 映射到 D:\Temp\UserTemp（MSYS），Python 脚本里写 /tmp/... 报 FileNotFoundError。脚本内用 Windows 路径（r"D:\Temp\UserTemp\..."），或先 `cygpath -w /tmp`
- **COM 打开过的文件删除报 busy**：Word/PowerPoint COM 退出后文件可能仍被锁（删旧版报 "Device or resource busy"）。删前 `sleep 2` 重试，或确保 COM app.Quit() 后再删
- **用 Word COM 验证 docx 完整性**：python-docx 改写 docx 后，`word.Documents.Open(path, ReadOnly=True)` + `ComputeStatistics(2/0)` + `len(doc.InlineShapes)` 验证页数/字数/图片数（BP 21页/7741字/12图 实证），确认没损坏文档

## 验证清单
- [ ] 溢出复查 0 项
- [ ] 同页图片/卡片尺寸统一
- [ ] 数字与定稿文档一致
- [ ] 备份对比：run 格式无损
- [ ] 重新导出 PNG 无异常（无白屏）

## 支持文件
- `scripts/ppt_health_check.py` — 一键体检（布局dump + COM导出 + 溢出检测 + 像素统计）
- `references/fix-recipes-20260814.md` — 实战修复配方（财务口径/图片裁剪/换行修复）
- `references/media-swap-and-live-screenshot.md` — media 图片替换（r:embed 定位 + zipfile）与 PyQt5 真机截图配方
- `references/multi-file-口径-unification.md` — 比赛材料多文档口径统一审计清单（BP/QA/路演稿/PPT 改版同步）
