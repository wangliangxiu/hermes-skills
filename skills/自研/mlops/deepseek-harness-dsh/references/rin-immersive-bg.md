# 凛皮肤沉浸式背景改造配方（2026-08-14 实证）

背景：使用者反馈凛皮肤"像 XP"（桌面框架风：标题栏+状态栏）不满意，要求沉浸背景风
（参考 whale-song）。使用者自搜 7 张远坂凛图放桌面「我的小项目\远坂凛皮肤包」（6 竖
1 横，横图 c177381d92d698c7e5425a965d3c8327.jpg 4096x2304 青蓝调，使用者选定做主背景）。

## 完整流程

1. **图片处理**（PIL）：
   ```python
   from PIL import Image
   im = Image.open(横图).convert('RGB')
   w, h = im.size
   im2 = im.resize((2560, int(h*2560/w)), Image.LANCZOS)
   im2.save(皮肤包/assets/rin-bg.webp, 'WEBP', quality=82, method=6)
   ```
   → q82 宽 2560 ≈ 252KB，base64 ≈ 336KB（client.js 从 35KB 涨到 ~720KB，可接受，
   只有 try-on/apply 时才解析，与 whale-song ~700KB 内嵌同理）。

2. **build 脚本生成新 client.js**（`皮肤包/build_rin_bg.py`）：
   - **SRC 必须固定指向 `lib/client.js.bak`（原始版）**——本会话踩坑：第一次生成后
     client.js 被新版覆盖，再跑脚本找不到 titlebar 锚点直接 `ValueError: substring
     not found`。生成前先 `cp client.js client.js.bak` 留底，脚本永远从 .bak 读。
   - 切块：head（`const css = \`` 前）＋变量色板段（`/* ---- 静态色板` 到
     `/* ---- 标题栏` 前，保留全部 --dsw-static/--dsw-alias/--aion 变量 light+dark）
     ＋分栏段（正则把 sidebar/conversation/details/header 背景改 rgba 半透明，
     **必须改，否则不透明色块盖住背景图**）＋滚动条~gitgraph 段＋新基础段＋精简 apply。
   - 新基础段（替换原 body 背景行 + root 面板）：
     ```css
     body[data-dsh-rin]{background-image:linear-gradient(rgba(12,6,8,.42),rgba(12,6,8,.42)),
       url("data:image/webp;base64,XXX");background-size:cover;background-position:center;
       background-attachment:fixed}
     body[data-dsh-rin][data-ds-dark-theme]{...rgba(5,3,4,.6) 更深遮罩...}
     body[data-dsh-rin] [id=root]{background:rgba(253,241,242,.52);
       backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
     ```
   - **apply 精简**：删掉 titlebar/statusbar 的 createElement/append，保留
     `body.dataset.dshRin=""` + favicon + `document.title=SKIN_TITLE`；disposer 相应
     精简。STATUS_CELLS/TITLEBAR_GLYPHS/CLS/cls 常量一起删。
   - **结尾结构**：`return module.exports; } });`（factory 闭 `}` + load 闭 `});`）——
     本会话第一次漏了末尾 `} });` 导致 `SyntaxError: Unexpected end of input`。
   - 写出时 `newline="\n"`（LF）。

3. **验证**：
   - `node --check client.js` 语法必须过
   - grep `data:image/webp;base64` ≥2（light+dark）
   - grep `backdrop-filter` ≥2；grep 无 `.gRin_titlebar{`/`.gRin_statusbar{` 规则
     （批量字体选择器里残留一个 `.gRin_titlebarBtn` 无害，元素已不存在）
   - `cp lib/client.js → profiles/web/node_modules/@linxin666/dsh-skins/skins/rin/lib/client.js`
     （junction 只链目录，文件改动不自动同步，必须手动 cp）
   - 重启 dsh → `/api/skin-center/bundle/rin` 200、`/api/skin-center/state` active=rin
   - 浏览器 Ctrl+Shift+R 硬刷新（client.js 有 rev 缓存，普通 F5 不换）

4. **ad-hoc 验证脚本正则坑**（验证脚本本身容易踩，不是产物问题）：
   - 生成文件是 LF；但若读到的文件是 CRLF，`\r?\n}` 匹配不到（`}` 在行尾 `\r` 前），
     应写成 `\}\r?\n`（找"`}` 后跟换行"）
   - 函数签名 `function apply(ctx) {` 的 `{` 前有空格，正则要 `apply\(ctx\)\s*\{`

## 5. 使用者视觉参数微调（2026-08-14 第二轮反馈，直接可作沉浸风默认值）

使用者看效果后两条反馈：「中间操作台挡住看不到背景图」「最左边设置那块红色刺眼，
跟最右边 details 一样浅粉」。对应调整（都改在 build 脚本里，重跑生成保证可复现）：

- **conversation（中间操作台）透明度**：light `rgba(255,253,253,.55)` → `rgba(255,253,253,.35)`，
  dark `.6` → `rgba(18,10,12,.4)`；其 header light `.42` → `.28`、dark `.46` → `.32`
  （半透明面板要让背景图透出来，.35 级别才够）
- **sidebar（最左）红色改浅粉**：背景统一成 details 的 `rgba(250,240,241,.5)`
  （light）/`rgba(23,11,14,.58)`（dark）；**红色主要来自色板变量
  `--dsw-specific-sidebar-fill:#c7000b`**（sidebar 组件用变量，改色板变量即可，
  不用碰组件 CSS）——在 CSS 尾部追加覆盖段（优先级高于色板定义）：
  ```css
  body[data-dsh-rin] [data-pane=sidebar]{--dsw-specific-sidebar-fill:#f6e4e6;
    --dsw-specific-sidebar-nav-item-active-accent:#e97f89;
    --dsw-specific-sidebar-nav-item-active:#f9d6d9;
    --dsw-specific-sidebar-nav-item-hover:#fbe7e9}
  body[data-dsh-rin][data-ds-dark-theme] [data-pane=sidebar]
    {--dsw-specific-sidebar-fill:#4a262c;...暗色同系}
  ```
- 调完重跑 build（SRC 仍是 .bak，幂等：重生成产物 md5 一致）、`node --check`、
  cp 同步、重启、硬刷新

## 6. 最终态：照抄 Blue Fantasy 骨架（2026-08-14 第三轮，取代 §2-§5 的 rgba 方案）

使用者看 §5 效果后明确：「Blue Fantasy 你照着这个改吧，别照着 XP 改了」——rgba 手写
方案透明度反复调不到满意，最终路线改为**直接复制官方皮肤的实现当骨架**。这是做
自制皮肤的最快路径，蓝本选 blue-fantasy（全透明面板 + 组件级 blur + scrim 遮罩，
视觉最精致）。

**为什么 blue-fantasy 面板透明效果好**（和 §2 的 rgba 方案本质区别）：
- `[id=root]{background:0 0}` 完全透明，不挡背景图
- 面板不设背景（sidebar/conversation/details 无 background 规则），透出背景图
- 半透明靠**色板变量自带 alpha**（`--dsw-alias-bg-base:#ffffff73`、
  `--dsw-specific-sidebar-fill:#f2f5fa80`、`--aion-bg-2:#e9edf79e`）
- 毛玻璃 `backdrop-filter:blur(12px/14px)` 挂在组件层 `.aionui-root/.aionui-dialog/
  .aionui-menu/.aionui-toast`
- 背景图在 apply 里动态写 body.style：`backdrop = linear-gradient(rgba(16,22,42,
  var(--dsw-skin-scrim,0))...), SCRIM_LIGHT/DARK, url(ART)` + MutationObserver 监听
  `data-ds-dark-theme` 切遮罩（`--dsw-skin-scrim` 是皮肤中心背景滑块可调的变量）

**转换脚本 `build_rin_bf.py` 步骤**（复制官方皮肤当新皮肤的通用法）：
1. `cp blue-fantasy/lib/client.js → 新皮肤/lib/client.js`（源文件要 cp 留 .bak）
2. 正则替换背景图常量：`const WHALE_ART = "data:image/[^"]*";` → 新图 base64
   （webp 也支持：`data:image/webp;base64,...`，浏览器认得）
3. 正则替换 favicon 常量：`const WHALE_ICON = "[^"]*";` → 自己的图标
   （凛用红宝石 SVG data URL）
4. 全局字符串替换标识（**4 类，漏一类都出事**）：
   - CSS 选择器：`data-dsh-blue-fantasy` → `data-dsh-rin`（约 100+ 处）
   - JS dataset：`dataset.dshBlueFantasy` → `dataset.dshRin`
   - **模块 ID（最关键，漏了加载即崩）**：`@linxin666/dsh-client-ui-skin-blue-fantasy`
     → `@linxin666/dsh-client-ui-skin-rin`——`__ModuleLoader__.load({id:...})` 里
     的包名必须换。本会话漏这步，使用者浏览器报
     `Failed to load plugins: ... loaded without registering
     "@linxin666/dsh-client-ui-skin-rin" via __ModuleLoader__.load`（bundle 通过
     /plugins/@linxin666/dsh-client-ui-skin-rin/client.js 加载，注册的 id 对不上就崩）
   - tagId 文件名：`blue-fantasy.module.css` → `rin.module.css`（CSS 去重 tag，
     不换不崩但规范）
   - dispose 描述：`ui-skin-blue-fantasy: whale backdrop` → `ui-skin-rin: ...`
   验证：`head -c 200 client.js` 应显示 `id: "@linxin666/dsh-client-ui-skin-rin"`；
   grep `dsh-client-ui-skin-blue-fantasy` 残留必须 = 0（纯注释里的 blue-fantasy
   字样残留无害）；`grep -c "dataset.dshRin"` ≥2（设置+删除）
5. **所有替换必须写进 build 脚本**：本会话先手动改 tagId（脚本没这步），重跑脚本
   又把 tagId 还原 → ad-hoc 幂等校验 hash 不一致。幂等校验前先确保当前文件是
   "脚本刚产出的状态"（先跑一次脚本再对比），否则校验方向反了误报 FAIL。
6. `node --check` 验语法 → `cp` 同步到 dsh-skins/skins/<id>/lib/ → 重启 dsh
   → 硬刷新

**改完看不到效果的根因 = bundle 被浏览器缓存**（§3 的硬刷新在 bundle 端点不生效）：
`/api/skin-center/bundle/<id>` 响应头没有 Cache-Control，浏览器启发式缓存旧 skin。
修复（node_modules 补丁）：
`profiles/web/node_modules/@linxin666/dsh-client-ui-skin-center/lib/index.js` 的
`bundleRoute()` 里 `res.writeHead(200, { "content-type": "text/javascript; charset=utf-8" })`
→ 加 `"cache-control": "no-cache, no-store, must-revalidate"`。pnpm install 会还原，
重装后重打。验证：`curl -s -D - -o /dev/null .../bundle/rin` 应看到 cache-control 头。

**skin.json bodyAttr 注意**：保持自己独有 id（data-dsh-rin），不能复用官方皮肤
的 data-dsh-blue-fantasy，否则两皮肤 CSS 同时作用打架。

## 一句话

给 dsh 自制皮肤换图/换风格 = 图压缩 webp→base64 → build 脚本（从 .bak 读、
删桌面框架、半透明面板）→ node --check → cp 同步 → 重启 dsh → 硬刷新。
