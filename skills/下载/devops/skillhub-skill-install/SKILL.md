---
name: skillhub-skill-install
description: 用skillhub装第三方技能到Hermes（装D盘+junction）。触发词：skillhub安装、装技能。
---

# SkillHub 第三方技能安装（Hermes）

SkillHub（skillhub.cn）是国内技能商店，用户团队批量测试/安装第三方技能时用。

## 安装流程

1. 安装指南：`https://skillhub.cn/install/skillhub.md`
   （curl 看内容；install.sh 是标准安装器，`curl ... | bash -s -- --cli-only` 只装CLI）
2. 安装技能必须指定目录，否则装到 `./skills/` 不被识别：
   ```bash
   python3 "C:\\Users\\使用者\\.skillhub\\skills_store_cli.py" install <slug> --dir "D:\\hermes-skills"
   ```
   社区技能（`@namespace/slug`）装出来是**嵌套目录** `D:\\hermes-skills\\@namespace\\slug`，不是平铺；junction 目标要指到嵌套路径。
   `search 中文词` 常返回空——搜不到不代表装不了，直接 `install @ns/slug` 反而能成。
3. 装完在 Hermes skills 目录建 junction 让 Hermes 识别。
   **坑**：git-bash 里 `cmd //c mklink /J "..." "..."` 会**静默失败**（只回显一行提示符、链接不生成），中文路径更易被 MSYS 转义搞乱。
   稳妥做法：写一个 UTF-8 的 .py 再用 python 跑：
   ```python
   import subprocess, os
   link, target = r"C:\Users\使用者\AppData\Local\hermes\skills\<slug>", r"D:\hermes-skills\@ns\<slug>"
   subprocess.run(["cmd", "/c", "mklink", "/J", link, target], capture_output=True, text=True, encoding="gbk", errors="replace")
   ```
   验证：链接目录下能读到 `SKILL.md` 的 frontmatter 才算成功（不要把 mklink 的无输出当成功）。

   **用户习惯**：使用者把要装的技能**攒成清单一次性装**（“等我说了之后再一起统一安装”）；收到单条安装请求先等等清单齐，并回报每条落到哪个目录。技能自带的 pip 依赖（如 opencv-python-headless）也不要擅自装，报清体积再等确认。
4. 验证：`head -8 <skills目录>/<slug>/SKILL.md` 读得到 frontmatter 即可

## Windows 中文用户名的坑

- `~/.local/bin/skillhub` wrapper 里 `${HOME}/.skillhub/skills_store_cli.py` 的
  `$HOME` 在中文用户名下展开成乱码 → 报 "CLI not found" 假象
- **绕过**：直接调核心脚本（用 Windows 路径，不能用 /c/... MSYS 路径）：
  ```bash
  python3 "C:\\Users\\使用者\\.skillhub\\skills_store_cli.py" --version
  ```
- skillhub CLI 本体在 C 盘 `~/.skillhub/` + `~/.local/bin/`（几百KB，很小）

## 用户环境约束（重要）

- **新下载/安装的文件一律放 D 盘，不占 C 盘**（用户清理过 C 盘，
  对空间敏感；技能本体全部在 `D:\hermes-skills\`）
- 系统已有同名技能时先确认再装（如 humanizer 已有 humanizer-zh，
  装 hub 版会冲突）
- 新装的技能要**重启 Hermes 会话**才出现在技能列表（列表是启动时快照）

## 装前快速验真（别只看 description）

skillhub 上不少技能是 AI 生成的**骨架模板**，描述写得很好但跑不起来。装完先看一眼再决定是否挂 junction：

1. `grep -n "launch\|headless\|userDataDir\|storageState\|selectors" scripts/*.js`
   —— 发布/登录类：**没有 userDataDir / storageState = 每跑一次都是新浏览器，登录态根本不保留**（README 让你用 `npx playwright open` 登录也没用，那不是同一个 profile）。
2. 选择器是否全是 `input[placeholder*="标题"]`、`button:has-text("发布")`、`.editor-content` 这种泛泛样式 —— 真后台富文本常在 iframe 里，`page.fill` 根本填不进去。
3. 代码里是否硬编码一段示例文章（如散文“春天来了”）—— 说明是 demo，不是成品。
4. 是否要求别的 runtime 专属工具（如 “OpenClaw browser tool”）、是否自带没人跑过的依赖（playwright + chromium）。
5. **平台对不对路**：多平台发布类技能多是企鹅/搜狐/大鱼/新浪/一点/网易这类老牌图文号，**没有抖音/快手/小红书/公众号/知乎/B站**的官方写接口。
6. **直接跑一条命令看输出**：如果脚本只是回显一句 `"instruction": "请将以下内容适配为…"` + 把原文原样返回，那就是**把提示词包装成 CLI 的空壳**（既没调研也没产出）；这种连当参考价值都不高，本机已有更好的就删掉。
   实测踩过：`@user_638e256a/media-self-media`（15 条命令全是 instruction 回显）、`@user_b50eba52/multi-platform-publisher-pro`（选择器靠猜、登录态不保存）。
判定：证据不足就**不挂 junction**，先报结论让用户决定；不要因为“装上了”就当成“能干这事”。

## Windows 删除技能的坑：别 cd 进去

`rm -rf` 报 `Device or resource busy` / `PermissionError (WinError 32)`，但文件已经删光了 —— 原因是我自己的 shell **cd 进过那个目录**（或后台命令的 cwd 在那），Windows 不允许删掉被当作工作目录的目录。
- 先 `cd` 到中立目录（如 `$LOCALAPPDATA/Temp`）再删；仍不行就用 python `shutil.rmtree` 重试（分步删往往能过）；再不行就把残留空目录放那儿，会话结束后再清。
- 教训：**在目录里跑过命令后，删之前先 cd 出来**。

## GitHub 技能仓库手动安装（非 skillhub）

标准 Anthropic skills 仓库（如 cathrynlavery/diagram-design，结构：`skills/<name>/SKILL.md` + references/ + assets/ + scripts/）：

1. `git clone --depth 1 <url>`（GitHub 被墙：先 `export https_proxy=http://127.0.0.1:17890 http_proxy=http://127.0.0.1:17890`）
2. 确认 frontmatter 格式（name/description）符合 Hermes 要求
3. 复制技能本体到 D 盘：`cp -r <repo>/skills/<name> /d/hermes-skills/<name>`
4. 建 junction（同上方命令）
5. 验证：`head -8 <skills目录>/<name>/SKILL.md` 读到 frontmatter；如技能自带 self_check.py 可跑一遍
6. 清理临时 clone

## 生成文件给用户看的坑（Windows 中文路径）

- `cmd //c start` / `explorer.exe` 打开含中文文件名/路径的 html 经常静默失败（exit 1 或没反应）
- **解法**：先 `cp` 成 ASCII 文件名放桌面（如 architecture.html）再 `cmd //c start "" "C:\...\architecture.html"`，打开成功后再删副本；原文件仍保留在项目文件夹
- PowerShell 里用 `$_` 会被 bash 展开报错（`$_.Foo` 变 `2.Foo`）——避免在 git-bash 里写含 `$_` 的 PowerShell 命令

## 技能列表（D:\hermes-skills，均已建 junction）

2026-08：find-skills、pdf-image-text-extractor、word-docx、data-analysis、memory-setup、ui-ux-pro-max、self-improving-agent

2026-09（均为 `@namespace/slug` 嵌套目录）：
- `@user_ebee0fcc/bilibili-video-extractor`：扒 B站 数据（播放/弹幕/评论）+ 爆款拆解，带 get_video_content.py / comment_extractor.py / batch_extract.py
- `@laoxi/qushuiyin`：本地去水印（图片 OpenCV inpainting、视频 ffmpeg delogo/裁剪/模糊）；numpy 有、ffmpeg 有、**缺 opencv-python-headless**
- `@davtime/omni-content-matrix`：一人公司全平台内容矩阵手册（定位/平台选择/一源多发/周计划/选题评分/标题改写/复盘），带 references 四份 + scripts/main.py
