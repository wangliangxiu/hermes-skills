# Claude Code 汉化安装实战（2026-08，Windows，github.com 直连不通）

环境：Windows 11，中文用户名（使用者），Claude Code 2.1.227（npm 全局装，
native 二进制 D:\Nodejs\node_modules\@anthropic-ai\claude-code\bin\claude.exe），
代理 127.0.0.1:17890，github.com 直连 000 但 api.github.com 直连 200。

## 检索真实项目（不瞎编，先验证存在）
GitHub API 搜汉化项目（需 UA header）：
`curl "https://api.github.com/search/repositories?q=claude+code+汉化&sort=stars&per_page=8" -H "User-Agent: curl"`
命中：taekchef/claude-code-zh-cn（680★，MIT）。README 摘要：简体中文本地化插件，
支持 macOS/Linux/WSL/Windows，四层机制（设置注入 + Hook + 插件系统 + CLI Patch），
修改前自动备份、启动自检、失败恢复原文件；native 二进制需要 node-lief。

## 最终成功路径（git clone 全挂，走 zip 兜底）
1. `claude plugin marketplace add --scope user https://github.com/taekchef/claude-code-zh-cn`
   → 失败：git clone github.com 443 连不上（没走代理）
2. export 代理后重试 → 仍失败：`not a git repository` / `git-submodule cannot be used
   without a working tree`（clone 中途崩，还留下 marketplaces/temp_* 残留目录要清）
3. 放弃 git clone。Python urllib + ProxyHandler 走代理下载 codeload zip：
   `https://codeload.github.com/taekchef/claude-code-zh-cn/zip/refs/heads/main`
   （7.6MB，224 条目）
4. zipfile 解压到 `C:/Users/使用者/.claude/plugins/marketplaces/claude-code-zh-cn`，
   确认 `.claude-plugin/marketplace.json` 存在（市场结构必须完整）
5. `claude plugin marketplace add --scope user <本地路径>` → 秒成功（支持本地目录）
6. `claude plugin install claude-code-zh-cn@claude-code-zh-cn --scope user` → 成功
7. 安装形态检查：`which claude` → sh 包装脚本 → 真实入口是 native claude.exe，
   故装 node-lief：`npm install -g node-lief`（需 export 代理 env，npm 才走代理）
8. 生效机制：登录 Claude 后启动会话，session-start hook 自动把中文配置合并进
   ~/.claude/settings.json（spinner 动词/tips/界面文字）。未登录跑 `claude -p "hi"`
   只会输出 "Not logged in · Please run /login"，hook 不触发

## 验证状态
- 安装成功的标志：settings.json 出现 extraKnownMarketplaces（source=directory 指向
  本地市场）+ enabledPlugins（claude-code-zh-cn@claude-code-zh-cn: true）
- `claude plugin list` 显示 claude-code-zh-cn v2.10.2 Status: enabled

## 坑
- 未登录用户装汉化只能装到"注册完成"，界面实际生效要等登录+启动会话
- 版本高于插件支持矩阵（如 2.1.227 > 验证窗口 2.1.220）时插件会自动降级，
  翻不了的部分保持英文，CLI 不会坏——可放心装
- **第三方仓库自带脚本（install.ps1 等）执行前必须先征得使用者同意**：
  本案例使用者拦下了 install.ps1（虽是官方推荐的手动合并配置脚本）。
  不要因为"插件已装好"就默认可以跑仓库里的任何脚本，先问。
