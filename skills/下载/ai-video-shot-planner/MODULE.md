# AI Video Shot Planner（模块索引）

> 本模块完整规则见同目录 [SKILL.md](./SKILL.md)。本文件只做角色定位与导航。

## 角色

当用户要把文案拆成镜头表时使用，负责估算时长与镜头数量、拆解 narration 节奏，并分配 visual_carrier 与画面轨重点。

## 关键 references

- 暂无独立 references；完整规则见 [SKILL.md](./SKILL.md)。

## 上下游

上游：`ai-short-video-pipeline` / 下游：`ai-video-image-prompts`、`ai-video-motion-prompts`。
