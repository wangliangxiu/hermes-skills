---
name: deepseek-harness-dsh
description: dsh（DeepSeek Harness）网页agent使用与插件/技能管理。触发：dsh、dot-skill。
---

# DeepSeek Harness (dsh) 使用与运维

DeepSeek 官方的开源 agent 框架（GitHub: deepseek-ai/deepseek-harness，口号 "Everything is a Plugin"）。`dsh` 是它的 CLI，`dsh web` 启动网页版 agent 界面。使用者（2026-08-14 起）已在本机装好并在玩。

## 关键事实（本机现状）

- **入口**：`dsh web` = 网页版 agent，默认端口 **http://127.0.0.1:3080**（可 `--port N` 换端口）
- **CLI 本体（2026-08-14 最终态）**：**全局安装在 `D:\Nodejs\node_modules\@deepseek-ai\dsh`**，
  `D:\Nodejs\dsh.cmd` 全局可用 → 终端直接敲 `dsh web` 即可（全局版是桌面端装的；
  之前 npm 装到 D:/tools/dsh 的临时目录已删）。桌面《dsh一键启动.bat》已指向全局版：
  先 curl 检查 3080，没起就 `start "dsh服务" /min dsh web`，8 秒后
  `start http://127.0.0.1:3080` 自动开浏览器（已在跑就直接开页面，不重复启动）
- **配置目录**：`C:\Users\使用者\.dsh\`（`profiles\web\` = web profile；`storages\` 会话存储；设了 `DSH_HOME` 环境变量则用 `$DSH_HOME`）
- **已装插件**：`@linxin666/dsh-skins`（0.1.11 皮肤全家桶：皮肤中心 + 全部皮肤资产
  内置在 skins/ 目录，qq98/ths/xp/blue-fantasy/dragon-heir/minecraft/miku/trading，
  无需每皮肤独立 npm 包）+ `@linxin666/dsh-client-ui-skin-center`（皮肤中心 GUI）+
  `@linxin666/dsh-web-ui-all`（0.1.12 功能全家桶：task-board 任务看板 / git-graph /
  pet 宠物 / live-stats 实时token统计 / ssh / remote-web-ui / aionui-panel /
  web-ui-settings）
- **已装技能**：dot-skill（colleague-skill）→ `~/.dsh/skills/dot-skill`（dsh 原生发现 filesystem skill，输入 `/dot-skill` 调用）
- **依赖**：Node.js（D:\Nodejs）+ pnpm（已全局装，dsh plugin 依赖它）

## 安装与启动

```bash
# 方式A：npx 临时跑（首次会下载 500+ 包，很慢）
npx -y @deepseek-ai/dsh web

# 方式B（推荐，可控）：npm 装到临时目录后 node 直启
mkdir -p <dir> && cd <dir> && npm install @deepseek-ai/dsh --registry=https://registry.npmmirror.com
node node_modules/@deepseek-ai/dsh/lib/bin.js web   # 后台跑，notify_on_complete

# 方式C（2026-08-14 实测：dsh 本体"找不到"时）
症状：`where dsh` 无、npm 全局无 @deepseek-ai/dsh、npx 缓存 _npx/* 下无 @deepseek-ai、
~/.dsh/profiles/web/node_modules 只有插件包（bundles 机制：package.json 里
dsh.profile.bundles 声明 @deepseek-ai/dsh-base/web-app，但 CLI 本体不在 profiles 下）。
做法：直接 npm install @deepseek-ai/dsh 到固定目录（如 D:/tools/dsh，加镜像源），
node node_modules/@deepseek-ai/dsh/lib/bin.js web 直启。
使用者体验优化：桌面"dsh一键启动.bat" = 启动 dsh web + `start http://127.0.0.1:3080`
自动开浏览器，用户不用每次敲地址（使用者 2026-08-14 抱怨过"每次都要输入那个网络地址"）。
```

启动成功标志：输出 `dsh web: http://127.0.0.1:3080`，curl 该地址返回 200。
**⚠️ 启动慢是常态（2026-08-17 实证）：插件多时 3080 端口要等 1 分多钟才监听**，
期间 node 进程活着但无任何输出、curl 000。使用者"dsh打不开了"最常见原因不是坏了，
是 bat 只等 8 秒就开浏览器，浏览器打开时服务还没起来。
修复：桌面《dsh一键启动.bat》已改为循环等待（每5秒 curl 一次 3080，最多 2 分钟）再开浏览器。
**⚠️ bat 文件必须 GBK(ANSI) 编码 + CRLF + 无 BOM**：用 UTF-8 或带 BOM 写会被 cmd
按 GBK 解析成乱码命令（报"不是内部或外部命令"）。write_file 默认 UTF-8，改 bat 要用
python `open(path,'wb')` 写 `.encode('gbk')`，且避免 heredoc+newline 双重转换出 \r\r\n。

## 插件管理

```bash
# 装插件（进 web profile）
node .../lib/bin.js plugin --profile web add @linxin666/dsh-web-ui-all   # 全家桶
node .../lib/bin.js plugin --profile web add @linxin666/dsh-skins        # 只要皮肤

# 卸载
node .../lib/bin.js plugin --profile web remove @linxin666/dsh-web-ui-all

# 验证插件挂载（不启动）
node .../lib/bin.js --profile web --dump-config   # 搜包名出现 = 已挂载
```

- 插件装进 `~/.dsh/profiles/web/node_modules/`，重启 dsh web 生效
- **⚠️ `dsh plugin add` 只把包装进 dependencies，不自动注册 bundle！** 必须手动把包名
  加进 `~/.dsh/profiles/web/package.json` 的 `dsh.profile.bundles` 数组，否则插件的
  cordis.patch.yml 不生效（组件不进页面 __DSH_BOOT__.entries）。装全家桶 2026-08-14
  实测：`plugin add @linxin666/dsh-web-ui-all` 后包在 node_modules 但 boot entries
  只有 skin-center，把 `@linxin666/dsh-web-ui-all` 加进 bundles 后组件全出现
- **⚠️ 全家桶 0.1.12 与 dsh-skins 都 insert `ui-skin-center` → 启动崩
  `duplicate loader entry id: ui-skin-center`**。修复：编辑
  `profiles/web/node_modules/@linxin666/dsh-web-ui-all/cordis.patch.yml`，
  删掉末尾 `# from ../skins/skin-center (via ../dsh-skins)` 的 insert 段（
  dsh-skins bundle 已提供），重启即好。注意 pnpm install 会还原该文件，重装后再删
- **⚠️ pnpm 11 allowBuilds**：装全家桶后 `pnpm install` 会尝试编译
  cloudflared/cpu-features/ssh2 原生模块（SSH/隧道用），卡很久。
  不编译不影响主功能（task-board/pet/live-stats 纯 JS），可直接把
  `pnpm-workspace.yaml` 里 allowBuilds 段注释掉跳过（报 ERR_PNPM_IGNORED_BUILDS
  只是警告）。使用者等不及/不耐烦时（原话 2026-08-14："能装吗，不能装就算了，
  我自己装"）果断放弃长耗时步骤，先保证主功能可用，高级功能（SSH 原生模块等）
  以后再说，别让使用者干等
- 验证全家桶加载：curl 页面后解析 `__DSH_BOOT__.entries`（JSON 对象括号配对），
  应含 ui-task-board/ui-git-graph/pet/live-stats/ssh/remote-web-ui/skin-center 等
- **插件入口位置**：UI 插件（如皮肤中心）注册在**设置页面**的分区（`installSettingsSection`），不在侧边栏——用户找不到入口时先让硬刷新（Ctrl+Shift+R）+ 去设置/插件列表找；服务端 boot 配置（页面 HTML 里 `__DSH_BOOT__.entries`）含插件 id 即加载正常
- **皮肤中心精确入口（2026-08-14 使用者按"设置页找皮肤"找不到后确认）**：
  设置（齿轮）→ **插件配置** → 「Web UI 插件」分组 → 「Skin Center / 皮肤中心」卡片
  （client.js 用 `ctx.slots.inject("web-ui.plugin.item", ...)` 注入到插件配置分组，
  不是叫"皮肤"的菜单项，设置里直接搜"皮肤"找不到）。卡片内：官方默认 + 所有已装皮肤，
  可 Try on（实时试穿，退出即恢复）/ Apply（应用）。皮肤应用走 host `/api/skin-center`
  API（dsh-skin use，热生效不用重启）；互斥由 `~/.dsh/cordis.patch.yml` managed 区段管理。
  注意 dsh CLI 无 skin 子命令（`dsh --help` 只有 web/plugin），换皮肤只能走 GUI
- 新装插件 UI 不显示三查：①浏览器硬刷新了吗；②入口在设置/插件列表而不是侧边栏；③插件是否在插件列表里处于未启用状态

## 自制皮肤插件（皮肤包开发，2026-08-14 远坂凛皮肤实证）

皮肤 = 一个 npm 包形态的目录，放进 dsh 的皮肤扫描路径即可被发现，**不用改任何源码**。完整结构/schema/CSS变量体系/验证脚本见 `references/skin-development.md` + `scripts/verify-dsh-skin.py`，要点：

- **皮肤资产放真实目录** `node_modules/@linxin666/dsh-skins/skins/<id>/`（与官方 9 个皮肤平级，皮肤中心 bundled-carrier 扫描会找到；注意 scoped 直接扫描会**跳过符号链接**，所以资产必须是真目录，不能只放个 junction）
- 再建 junction `node_modules/@linxin666/dsh-client-ui-skin-<id>` → `dsh-skins/skins/<id>`（apply 时 checkResolvable 要求该路径 package.json name 匹配 + main 存在；皮肤中心 apply 会 ensureSymlink 自动建，但手动建更稳）
- **skin.json 必备字段**（readSkinMeta 校验，缺了整个皮肤被跳过）：`id`（小写字母数字-）、`package`、`wiring.id`（ui-skin-<id>）、`wiring.bundleWired`；可选 name/nameEn/tagline/description/accent/bodyAttr/order
- **bodyAttr = `data-dsh-<id>`**，所有 CSS 必须作用域到它（含标题栏/状态栏类名——别学 qq98 用 hash 类名裸奔，短类名必须显式加前缀，用验证脚本查）
- **CSS 变量四套体系**：`--dsw-static-*`（色板，deepseek/blue=品牌色）、`--dsw-alias-*`（语义别名）、`--dsw-specific-*`（sidebar/bubble/input…）、`--aion-*`（aionui 组件）；每套都要写 light + `[data-ds-dark-theme]` 两份
- **client.js 契约**：`window.__ModuleLoader__.load({id, factory})`，factory 内 `<style>` 注入（带 data-plugin-css 去重），`exports.apply = apply`；apply(ctx) 里 `body.dataset.dsh<Id>=""` + 挂标题栏/状态栏 DOM + `ctx.effect(()=>()=>{清理})`（disposer 里 delete dataset + remove 元素 + 还原 document.title）
- **验证链路**：`GET /api/skin-center/bundle/<id>` 应返回完整 client.js（HTTP 200 有内容）；`GET /api/skin-center/state` 看当前激活；`POST /api/skin-center/apply {skin:"<id>"}` 热切换（写 ~/.dsh/cordis.patch.yml managed 区段，不用重启）
- **GUI 显示坑**：API/apply 全通 ≠ 皮肤中心 GUI 能看到该皮肤——GUI 列表是 client.js 硬编码的 `SKIN_CENTER_ENTRIES`（见踩坑10），自制皮肤要插条目 + 重启 + 硬刷新才显示
- 皮肤包源码项目留桌面「我的小项目」，改完 lib/client.js 要 **cp 同步到 dsh-skins/skins/<id>/lib/**（junction 只链目录，文件改动不自动同步）＋重跑验证脚本
- **皮肤风格两流派**（使用者 2026-08-14 反馈：凛"像XP"不满意）：①桌面框架风=顶部标题栏+底部状态栏+模拟桌面（XP/qq98/凛都是），结构统一但换配色；②沉浸背景风=全屏背景图垫底+半透明面板+随明暗切换的遮罩（whale-song/blue-fantasy）。使用者偏好后者。凛皮肤往沉浸风改造的**完整配方**（图片压缩 webp base64、build 脚本从 .bak 固定源生成、删 titlebar/statusbar、半透明毛玻璃、cp 同步、验证正则 CRLF/LF 坑）见 `references/rin-immersive-bg.md`：真图素材放桌面「我的小项目\远坂凛皮肤包」（使用者自搜的 jpg/png），流程=挑主背景图→背景图 base64 内嵌 client.js→半透明面板+遮罩→cp 同步→node --check→重启 dsh→硬刷新
- **最终态（2026-08-14 第三轮）：使用者明确"照着 Blue Fantasy 改，别照着 XP"——直接 cp 官方皮肤的 client.js 当骨架**（比自写 build_rin_bg.py 的 rgba 方案更精致：root `background:0 0` 全透明、毛玻璃 blur 在组件层 aionui-root/dialog、遮罩走 `--dsw-skin-scrim` 变量 + SCRIM_LIGHT/DARK 渐变、面板半透明靠色板变量自带 alpha）。批量替换 4 类：`data-dsh-<官方id>`→`data-dsh-<新id>`、`dataset.dsh<Xxx>`→`dataset.dsh<新id驼峰>`、**模块 ID `@linxin666/dsh-client-ui-skin-<官方id>`→`<新id>`（__ModuleLoader__.load 里，漏了报 loaded without registering ... via __ModuleLoader__.load 崩）+ tagId 文件名**、背景图常量（WHALE_ART）→新图 base64、favicon 常量（WHALE_ICON）→自己图标、disposer 描述。**所有替换必须写进 build 脚本**（手动改会被重跑还原，幂等校验会 FAIL）。转换脚本见皮肤包 `build_rin_bf.py`，recipe 见 `references/rin-immersive-bg.md` §6
- **改完皮肤看不到效果 = bundle 被浏览器缓存（2026-08-14 凛皮肤实证）**：
  `/api/skin-center/bundle/<id>` 响应无 Cache-Control 头，浏览器缓存旧 skin，
  普通刷新/重开标签都拿旧版（此时 server 端 curl 验证已是新版，就是浏览器缓存）。
  修复：skin-center 插件 `lib/index.js` 的 `bundleRoute()` 里
  `res.writeHead(200, {...})` 加 `"cache-control": "no-cache, no-store, must-revalidate"`
  （node_modules 补丁，pnpm install 会还原，重装后要重打）。之后改皮肤只需
  重启 dsh + Ctrl+Shift+R，不用每次清浏览器缓存

## 技能安装（filesystem skill）

dsh 原生发现 `~/.dsh/skills/<name>`（全局）或 `<项目>/.dsh/skills/<name>`（项目级）下的技能目录（含 SKILL.md）。装完在 dsh 里输入 `/技能名` 调用。dot-skill 就是这样装的（git clone 或复制仓库目录过去即可）。

## 踩坑（2026-08-14 实证）
0. **启动入口找不到时，先问用户/先给最简方案，别反复 npm/npx 重装折腾**（使用者原话
   "为啥感觉你做的这个这么麻烦，没有其他方法了吗"）：dsh 打不开时正确顺序是——
   ① 先问使用者平时怎么打开的（他能用=有可行入口，只是我不知道）；② 给零成本兜底：
   浏览器收藏 `http://127.0.0.1:3080`，dsh 开着时点书签就进，不用敲地址；
   ③ 确定要装再走方式C。实测本次 `npm install @deepseek-ai/dsh` 后
   `node_modules/@deepseek-ai/` 为空（rc 包镜像未同步/网络），`npx -y @deepseek-ai/dsh web`
   exit 127——遇到就先停下来问，别把用户晾在一边等重装。
## 踩坑（2026-08-14 实证）0. **npx 启动不稳定**：`npx -y @deepseek-ai/dsh web` 会因
   npm ECOMPROMISED（lock 校验失败）/退出码127/静默卡死而失败。最稳方案：
   **npm 装到固定目录再 node 直启**：`mkdir -p D:/tools/dsh && cd D:/tools/dsh &&
   npm install @deepseek-ai/dsh --registry=https://registry.npmmirror.com --no-audit --no-fund`
   （约5分钟500+包，期间无输出别中断），然后
   `node node_modules/@deepseek-ai/dsh/lib/bin.js web`（后台跑）。注意 npm install
   接 `| tail` 会吞掉真实错误（管道 exit 取 tail），要看错误别接管道
1. **npx 反复"静默失败"**：终端里 `npx ... | head` 或 `timeout npx` 组合，超时杀掉进程后管道 exit=0 无输出，npm 缓存（`AppData\Local\npm-cache\_npx`）不增长=下载卡死（npm 官方源慢）。绕过：直接 `npm install` 到临时目录（5分钟528包）再 `node bin.js` 直启。判断是否真在下载：看 `_npx` 缓存目录大小是否增长
2. **npm/npx 命令无输出不代表死了**：`npm --version`、`npm view 包名 version` 正常返回=环境OK；装包时别用 timeout+管道吃输出
3. **缺依赖导致启动崩溃**：插件缺 peer/schemastery 之类依赖时 `dsh web` 启动即退（`ERR_MODULE_NOT_FOUND`）。修复：`cd ~/.dsh/profiles/web && pnpm add <缺的包>` 后重启
   - 特例（2026-08-14 实测）：`ERR_MODULE_NOT_FOUND '@linxin666/dsh-client-ui-skin-xp'` ——
     dsh-skins 皮肤子包在 profiles/web/node_modules/@linxin666/ 下是**坏符号链接**
     （之前用 npm 而非 pnpm 装导致），`ls` 能看到但 `cat package.json` 为空。
     修复：`cd ~/.dsh/profiles/web && rm -rf node_modules/@linxin666/dsh-client-ui-skin-xp
     && pnpm add @linxin666/dsh-client-ui-skin-xp`（pnpm 会正确重建链接）
4. **pnpm 未装**：`npm install -g pnpm`（dsh plugin 内部转发给 pnpm 管理 profile 依赖）
5. **皮肤中心入口找不到**：见"插件管理"第2条——入口在设置→插件配置→Web UI 插件→
   Skin Center 卡片，且必须硬刷新；设置里直接搜"皮肤"是找不到的
6. **`~/.dsh/cordis.patch.yml` 残留旧皮肤 id 报 not found（无害警告）**：
   `--dump-config` 时见 `patch: entry "ui-skin-xxx" not found`（blue-fantasy/dragon-heir/
   miku/minecraft/qq98/ths/trading/whale-song）——旧版 dsh-skins 每皮肤一个独立 npm 包，
   新版 0.1.11 把皮肤资产整合进 skins/ 目录，旧引用失效。**最终正确状态：文件清成 `[]`**
   （2026-08-14 实测）：① 纯注释不算数组，会报 `must be a top-level YAML array`；
   ② 若保留 `- insert: ui-skin-xp` 且皮肤包 bundle patch 也自动插了同 id，启动即崩
   `TypeError: duplicate loader entry id: ui-skin-xp`——皮肤由 @linxin666/dsh-skins
   bundle 自动加载，用户 patch 保持空数组即可；③ 删掉 managed 区段的 not-found id 与
   冗余 insert 后需**重启 dsh 才生效**（杀 node 进程再 `dsh web`）
7. **工作目录=启动目录**：`dsh web` 的默认 workspace 是启动命令时所在目录；想让 agent 在目标项目里干活，就从那个目录启动
9. **换皮肤后 dsh 打不开（2026-08-14 实证，使用者换 whale-song 后崩）**：
   - 根因：皮肤中心 apply 会把 managed 区段（disabled 其他皮肤 + insert 目标皮肤）写进
     `~/.dsh/cordis.patch.yml`。若文件里已有 `[]`（旧踩坑6 让清成 []），写后变成
     `[]` + 顶层数组项 = **非法 YAML**，dsh 重启 parse 直接崩：`failed to parse patches
     cordis.patch.yml: YAMLException: end of the stream or a document separator is
     expected`，3080 打不开（服务在跑着换皮肤时热生效正常，一重启就崩）
   - 合法状态两种：① 纯 `[]`（皮肤全默认）；② 纯 managed 区段（disabled 其他皮肤 +
     insert 目标皮肤，**文件里绝不能有 [] 前缀**）
   - **0.1.11 整合版 bundleWired=false 的皮肤（如 whale-song/鲸吟）必须靠 insert 加载**，
     dsh-skins bundle 默认只 insert `ui-skin-center`，不加载具体皮肤；所以带 insert 的
     纯 managed 区段不会 duplicate 崩（旧踩坑6 的 duplicate 是旧版每皮肤独立包+bundle
     自动接线的场景，别混淆）
   - **自愈**：已写 `~/.dsh/fix-patch.ps1`（抽离 managed 区段、去掉 [] 前缀、异常重置
     []），桌面《dsh一键启动.bat》启动前自动调用 → 以后使用者换皮肤崩了，双击 bat 自愈。
     手动修复可直接把 `~/.dsh/cordis.patch.yml` 改写为纯 managed 区段（含 insert）再重启
10. **皮肤中心 GUI 列表是硬编码的，自制皮肤不显示（2026-08-14 凛皮肤实证）**：
   - GUI（`profiles/web/node_modules/@linxin666/dsh-client-ui-skin-center/lib/client.js`）
     的皮肤列表 = 文件顶部硬编码数组 `SKIN_CENTER_ENTRIES`（构建时生成的官方清单，
     0.1.11 含 9 个：qq98/ths/xp/blue-fantasy/dragon-heir/trading/miku 等），
     **不是动态扫描**——自制皮肤（如 rin）即使 skin.json/资产都在、API 能 apply，
     GUI 也不显示
   - server 端（同包 lib/index.js）才是动态注册表：`resolveSkinsDir` →
     `listSkinDirCandidates` 扫描直接子目录（**符号链接被跳过**，lstatSync
     isSymbolicLink 即 continue）+ bundled carrier `dsh-skins/skins/<id>`；
     /api/skin-center/apply|state|bundle/<id> 都走动态注册表 → API 切换一切正常
   - **修复**：手动把皮肤条目（数据抄该皮肤 skin.json：id/name/nameEn/tagline/
     description/tags/accent/bodyAttr/package/order）插进 client.js 的
     SKIN_CENTER_ENTRIES 数组末尾（上一个条目 `}` 后加 `,` 再接新对象），
     `node --check` 验语法，重启 dsh，浏览器 Ctrl+Shift+R 硬刷新后 GUI 显示该皮肤
     卡片（client.js 有 rev 缓存，必须重启服务才取到新 rev）
   - 注意：pnpm install 会还原 node_modules 里的 client.js，重装后需重插
   - 界面结构（使用者 2026-08-14 确认）：装了全家桶后，设置→插件配置下
     「Web UI 插件」与「皮肤中心（Skin Center）」是**并列同级**的模块卡片
8. **网络限制（本机实测）**：github.com 直连超时（被墙）、api.github.com 时通时不通；
   **本机有本地代理 `127.0.0.1:17890`**（Clash 类：注册表 ProxyServer 有此值但
   ProxyEnable=0，代理软件实际在跑）——`curl -x http://127.0.0.1:17890 https://github.com/...`
   可通（API 与网页/下载都行）；GitHub API 未认证限流 429 时，改用
   `github.com/<user>/<repo>/archive/refs/heads/main.zip` 直接下载；npm 官方源慢时
   临时加 `--registry=https://registry.npmmirror.com`（阿里镜像，不必改全局配置）；
   用户浏览器网络通，大文件下载可让用户浏览器下

## 插件生态速查（GitHub topic: dsh-plugin，800+ 仓库，鱼龙混杂）

- 官方：deepseek-ai/deepseek-harness（6万+ star）
- dsh-web-ui（zhu1090093659）：任务看板/Git图谱/右侧面板/鲸鱼娘宠物/实时token统计/SSH远程/8款皮肤（XP/Minecraft/鲸吟/交易终端等），聚合包 `@linxin666/dsh-web-ui-all`，皮肤包 `@linxin666/dsh-skins`，BSD-3 开源
- modlens：DSH 视觉插件（"看图"）
- 装插件认准：官方/大 star/活跃维护，README 明确写支持 dsh

## 支持文件
- `references/wechat-chat-export.md` — dot-skill 素材准备：微信聊天记录位置（D:\xwechat_files\db_storage 加密库 vs 官方备份格式）、WeChatMsg 导出流程；微信4.x 完整解密/导出（miyu/ciphertalk-cli 提密钥、wx_key.dll 直调、版本矩阵、DMCA 生态）见独立技能 `wechat-chat-record-extraction`
