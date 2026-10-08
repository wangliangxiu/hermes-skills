# dsh / DeepSeek Harness 使用笔记（2026-08-14 实证）

DeepSeek 官方出的 agent 框架（GitHub: deepseek-ai/deepseek-harness，6万star，
副标题 "Everything is a Plugin"）。用户求职 AI 公司，dsh 是"DeepSeek 官方 agent
长什么样"的活教材 + 可玩工具。

## 是什么

- `dsh` = DeepSeek Harness 的 CLI；`dsh web` = `--profile web` 别名，启动**网页版 agent**
  （浏览器界面：对话 + 工具执行 + 会话持久化）。另有 `--profile headless "任务"`（命令行
  一次性）和 tui profile 示例。
- 插件化架构：agent 循环、bash/fs/web 工具、子代理、技能、沙箱、MCP、LLM 接入
  （deepseek 系模型）全是独立 @deepseek-ai/dsh-* 包拼装。
- 运行目录 = 默认 workspace 根；要让它在哪干活就在哪启动。
- 本地地址 http://127.0.0.1:3080（默认端口，`--port` 可改）；127.0.0.1 = 仅本机能访问。

## 安装（npm 直装，别用 npx 撞运气）

```bash
npm install @deepseek-ai/dsh     # 528 个包，约 5 分钟（国内官方源偏慢）
node node_modules/@deepseek-ai/dsh/lib/bin.js web   # 启动 → http://127.0.0.1:3080
```

- **npx 在 git-bash 下"静默失败"假象**：npx 下载大包期间几乎无输出，再配
  `timeout N ... | head` 管道会把输出全吞掉、exit code 变 0 → 误判"卡死/失败"。
  诊断口诀：**管道+timeout 看真实状态不可靠，直接 `npm install` 前台跑看完整输出**。
- 启动用 background 进程（server 长期运行），`process poll` 看 "dsh web: http://..."。

## 插件（皮肤/任务看板等）

- 管理命令：`dsh plugin --profile web add <npm包>`——**转发给 pnpm**，先 `npm install -g pnpm`。
  插件装到 `~/.dsh/profiles/web/node_modules`（Windows 的 $DSH_HOME 默认在用户主目录 .dsh）。
- **装完必须重启 dsh web 才生效**（侧边栏才有入口）。
- 生态：GitHub topic `dsh-plugin`（857 仓库，鱼龙混杂，认官方/大star/活跃维护）。
  官方主仓库 deepseek-ai/deepseek-harness；第三方 dsh-web-ui（zhu1090093659，
  npm @linxin666 scope）：
  - `@linxin666/dsh-skins` = 只要皮肤（8款：Windows XP/Minecraft/鲸吟/交易终端/QQ2008等，
    皮肤中心支持"先试穿再应用"）
  - `@linxin666/dsh-web-ui-all` = 全家桶（皮肤+任务看板+Git图谱+右侧面板+鲸鱼娘宠物+
    令牌统计+SSH远程）

## 排错（实证）

1. **装皮肤插件后 dsh 启动崩溃** `ERR_MODULE_NOT_FOUND: Cannot find package 'schemastery'
   imported from ...@linxin666/dsh-client-ui-skin-center\lib\index.js`：
   皮肤中心插件缺 peer 依赖 → 在 profile 目录补装：`cd ~/.dsh/profiles/web && pnpm add schemastery`，
   再重启 dsh web。
2. **npm allow-scripts 警告**（koffi/node-pty/cloudflared/ssh2 等原生模块 install 脚本
   被 npm 安全策略拦）：装全家桶/SSH 相关功能报错时，按 README 把包加进 profile 的
   pnpm-workspace.yaml `allowBuilds` 或用 `npm approve-scripts` 放行；纯皮肤一般用不到。
3. 装完插件"UI 不显示"：多半是没重启；重启用 `--dump-config` 确认插件配置层已挂载。

## 对使用者的用法

- 学习：DeepSeek 官方 agent 架构（工具循环/插件/沙箱/会话）——面试谈资。
- 玩：`dsh web` 开网页版，皮肤中心换肤。
- 注意：dsh 用的模型走 DeepSeek（可能要登录/配 key）；与用户自建 Agent（ai-agent-building
  主技能）不同——那是自己用 function calling 搭，dsh 是现成框架直接用。
