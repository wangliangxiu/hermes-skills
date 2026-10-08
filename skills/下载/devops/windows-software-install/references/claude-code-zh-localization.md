# Claude Code 界面汉化（简体中文）— 2026.8 实证

## 背景
- Claude Code 官方无中文界面。要汉化需用社区插件（会 patch 官方文件，
  选项目必须看信誉和安全机制）。
- 2026.8 用 GitHub API 搜索 `claude code 汉化` 验证过的真实项目，
  只推 taekchef/claude-code-zh-cn（680★，MIT）。来源：
  https://github.com/taekchef/claude-code-zh-cn
- ⚠️ 别混淆：op7418/Humanizer-zh（15k★）是"消除AI痕迹"的 skills 汉化，
  不是 Claude Code 界面汉化。

## 推荐安装方式（插件市场，三平台通用，Windows 也行）
前置：已有 `claude` 命令（npm 全局装即可）且装了 Node.js。

```bash
claude plugin marketplace add --scope user https://github.com/taekchef/claude-code-zh-cn
claude plugin install claude-code-zh-cn@claude-code-zh-cn --scope user
```

装完**重启一次 Claude Code** 生效。验证：spinner 出现"思考中""光合作用中"
等中文 = 成功（Layer 1~3 生效）。

## 安全性机制（为什么敢推荐）
- 修改前自动备份原文件；启动自检；patch/重打包失败自动恢复原文件
- 新版本不在验证窗口内会自动降级——翻不了的部分保持英文，CLI 不会坏
- 四层机制：设置注入 + Hook 系统 + 插件系统 + CLI Patch

## 版本支持（2026.8 快照）
- npm 装的 cli.js 最完整
- native 二进制（官方安装器/新版 npm 包装）：Windows 已验证
  2.1.113 – 2.1.220，需 `npm install -g node-lief`（提取 JS→翻译→写回）
- 支持矩阵：https://github.com/taekchef/claude-code-zh-cn/blob/main/docs/support-matrix.md
- 遇到比支持矩阵更高的版本：照装，插件自检降级，不影响使用

## 验证登录态（汉化前先确认 claude 本身能用）
```bash
claude --version          # 版本，需 v2.x
claude auth status        # JSON；loggedIn: false = 没登录
```
没有 Claude 账号（Pro/Max 订阅或 Anthropic API key）前，装不装汉化
都用不了，先解决账号/登录问题。
