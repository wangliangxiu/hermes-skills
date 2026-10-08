---
name: install-external-skills
description: 从GitHub等外部仓库安装第三方技能到Hermes。触发词：装技能、安装skill、GitHub技能。
---

# 安装外部技能（GitHub / 手动来源）

从 GitHub 等来源安装标准 SKILL.md 格式的第三方技能。**SkillHub.cn 来源**走 skillhub-skill-install 技能；本技能管 GitHub / 手动来源。

## 识别技能仓库

- 标准 Agent 技能仓库：`skills/<name>/SKILL.md`（可能带 references/ assets/ scripts/ 子目录）
- Claude Code 插件仓库常见结构：`.claude-plugin/plugin.json`、`.codex-plugin/`、`commands/`、`prompts/`
- **关键**：SKILL.md 必须有 YAML frontmatter（name + description）才符合 Hermes 技能格式
- 只需复制 `skills/<name>/` 整个目录；commands/、prompts/ 是 Claude Code 的 slash 命令，Hermes 不需要
- **另一种结构：仓库根就是技能** —— SKILL.md 直接躺在仓库根，旁边还有 `template/` `reference/` `examples/` 等大块素材（例：anything2explainer）。这种没有 `skills/<name>/` 可挑，**整个仓库（去掉 .git）就是技能本体**，装完技能里的相对路径才成立；这类仓库常有几十 MB，照样放 D 盘再 junction / external_dirs 挂过去

## 安装步骤

1. 克隆仓库（GitHub 被墙需代理）：
   ```bash
   export https_proxy=http://127.0.0.1:17890 http_proxy=http://127.0.0.1:17890
   cd /tmp && git clone --depth 1 <repo_url> && cd <repo>
   ```
2. 检查同名冲突：`ls /d/hermes-skills/` 与 `~/AppData/Local/hermes/skills/` 是否有同名技能
3. 复制技能本体到 D 盘（用户约定：技能本体放 D:\hermes-skills，不占 C 盘）：
   ```bash
   cp -r /tmp/<repo>/skills/<name> /d/hermes-skills/<name>
   ```
4. 建 junction（无需管理员权限；目标已存在则跳过）：
   ```bash
   powershell -NoProfile -Command "if (Test-Path '<hermes-skills>\<name>') { 'EXISTS' } else { New-Item -ItemType Junction -Path '<hermes-skills>\<name>' -Target 'D:\hermes-skills\<name>' | Out-Null; 'CREATED' }"
   ```
   其中 `<hermes-skills>` = `C:\Users\<用户名>\AppData\Local\hermes\skills`
   若 `New-Item` 报 `PermissionDenied`（访问被拒绝）或环境不允许建 junction，不要反复重试——改用 Hermes 原生的 **external_dirs**：
   ```bash
   # 布局必须是 <外部技能根>/<技能名>/SKILL.md，所以先把技能放到自己的根目录下
   hermes config set skills.external_dirs '["D:/hermes-skills"]'
   hermes config get skills.external_dirs          # 回读确认
   hermes skills list | grep <name>                # 显示 "<name> | local | enabled" 即成功
   ```
   external_dirs 里的技能对 Hermes 是**只读**的（不能 skill_manage 改），config 改动**新会话**才生效。
5. 验证：
   - `head -8 <hermes-skills>/<name>/SKILL.md` 能读到 frontmatter
   - 用 skill_view(name='<name>') 能加载、linked_files 齐全即完整
6. 清理临时 clone：`rm -rf /tmp/<repo>`

## 交付形式：技能包（文件夹 + 压缩包）

使用者除了"装上能用"，还常要**拿到手的一份包**（"做成技能包""压缩文件或文件夹那种形式"）。两份都要给，别只给一份：

1. **装好、能用**：技能放进 `skills/<分类>/<name>/`（重库放 D 盘 + junction/external_dirs），用 `hermes skills list | grep <name>` 验证到 `enabled`。
2. **可带走的一份包**：`桌面\我的小项目\<名字>技能包\`（按 desktop-organization-rules 归位，别散在桌面），结构：
   ```
   <名字>技能包/
     <skill-name>/SKILL.md          技能本体（与已装的那份逐字一致：拷过去后对比一下）
     <skill-name>/_meta.json        {slug,name,version,source,author,origin,packagedAt,skills[]}
     <skill-name>/README.txt        中文通俗说明：是什么/能干什么/怎么用/怎么装到别处/目录里有什么/注意事项
     <skill-name>/references/*.txt  原文素材（如原作者提示词照抄）与示例输出
     <名字>技能包.zip               解压后第一层就是 <skill-name>/，直接丢进 skills/ 即可
   ```
   打包用 python `zipfile`，`os.path.relpath(fp, PACK)` 做 arcname，解压即得可直接安装的目录。
   **包好要验**：解压到临时目录 → 按 `_validate_frontmatter` 的规则逐条验（首字节 `---`、name≤64、description≤60、正文非空、总长≤100k），再 `hermes skills list` 回读一次。

## 交付要求

用户是技术小白：装完必须给**中文通俗说明**——这是什么技能、能干什么、怎么用（触发话术示例）、有哪些注意事项（如首次使用会问配色定制、自带示例文件位置）。

## 评估：能不能用（推荐/报进方案前先核验，别拿 README 当依据）

使用者会当场追问"你确定能应用吗 / 这个能补上那个洞吗"。只读 README、只看 GitHub 页面渲染就推荐＝会被打回，更糟的是把用不了的东西报进了合作方案或工期里。

四步核验（命令、grep 清单、结论写法见 `references/external-skill-vetting.md`）：

1. **clone 下来看真身**，并查 `LICENSE*` 文件是否真存在——README 徽章写 MIT 不等于仓库有许可文件
2. **grep 三类硬依赖**：绑特定 runtime 内置工具的（换 runtime 就要改接口）、要第三方 key/私有接口的、数据来自作者自建域名的
3. **跑最上游那一步脚本**，看后端是否还活着（解析失败/超时/返回 000 ＝ 这条链路已经断了）
4. **产出侧自己出一次成品再说话**，把成品路径交给用户看

结论分三档交付，并说明它填的是哪一半、填不了哪一半、依赖谁：

- **能确定用**（已实测，零外部依赖）——附实测证据
- **要改造成能用**（成本不大但要动手）——写清改哪一步
- **现在就是断的**（别指望）——写清死因，且**不计入工期、不写进承诺**

半个能用的仓库，结论就是半个，不要为了推荐把半边说成整边。报告里必须能区分"我实测过"和"文档说"。

## 已装过的外部技能（本机笔记）

- SenseNova-Skills（商汤 33 个 sn-* 技能）：布局、依赖、httpx 冲突、.env 位置、实测结果见
  `references/sensenova-skills-install.md`
- mcncarl 的 yichen-skills（21 个技能）+ jianying-headless（剪映引擎，公开仓库）：
  只装了实测能跑的 2 个到 `D:\hermes-skills\`——`yichen-jianying-edit`（Windows FFmpeg 后端可出片，
  核心引擎另存 `D:\hermes-skills\jianying-headless`，需设 `JIANYING_HEADLESS_ROOT`）和
  `yichen-x-slicer`（本机只有 `--source-only` 可用）。其余 19 个绑作者自己的 macOS + Codex + OpenCLI
  + 付费 API，未装。教训：**这类"作者自用全家桶"型仓库要逐个技能扫硬依赖再挑，别整仓装**；
  扫完还要真跑最上游那一步——`yichen-x-slicer` 静态看是 Playwright 依赖，实跑发现抓取阶段不需要它。

## 坑

- **用户发的"skill"常常只是一段提示词，不是 skill 文件**：判据是看开头——`你现在是一名……你的任务是……` = 角色扮演式系统提示（贴哪都能用），没有 frontmatter 和配套文件。这种情况下"做成技能"只需要**套壳**（加 name + 一句 ≤60 字的 description → 落成 SKILL.md），正文照用，不要重新总结一遍；同时把原文单独存一份 `references/原始提示词.txt` 供他整段复制。
- GitHub 被墙：clone 必须带代理 127.0.0.1:17890
- 只复制 skills/<name>，不要把整个仓库（含 .git、commands、docs）都复制进 D 盘
- 同名冲突要先查；装完 skill_view 验证，别只看目录在
- 系统提示里的技能列表是启动时快照，新技能 skill_view 可直接加载（按名读文件），但列表要重启会话才刷新
- 技能自带的 check 脚本可能是"生成后产物检查"（需要文件参数），不是安装完整性检查，别误用为安装验证
- **改 Hermes 配置不要用 patch/write_file**：写 config.yaml 会被拒（"Agent cannot modify security-sensitive configuration"）。一律走 `hermes config set <key> '<JSON值>'`，改完用 `hermes config get <key>` 回读
- **装完必须真跑一遍它的最小流程，不能只看"目录在 + 能加载"**：第三方技能大量假设 macOS（zsh / rsync / `sed -i ''`），在本机直接跑会失败。跑通的最小动作 + 实测输出写进技能里的本机说明，跑不通就先修脚本再交付。改法与清单见 `references/windows-script-porting.md`
- **跑最小流程要按上游的阶段顺序**：先跑"生成数据"的那一步，再跑消费它的那一步。跳过生成步骤，下游报的错看不出根因——Remotion 类项目表现为 `Cannot read properties of undefined (reading 'from')`（模板时间轴是空占位，得先跑它的 tts/配音脚本）、以及"config 引用了不存在的句 id"。见到这类报错先查"生成脚本跑没跑、示例数据够不够长"，别怀疑工具链装坏了
- **给技能加的本机说明必须能从 SKILL.md 找到**：在技能 SKILL.md 末尾加一节指向 `local/本机适配说明.md`（或同类文件）——否则下个会话 SkillView 读到的只有上游正文，根本不知道这个文件存在
