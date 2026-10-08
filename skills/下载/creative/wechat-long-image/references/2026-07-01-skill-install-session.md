# Skill Installation: July 1, 2026 — Bulk WeChat & Writing Skills

**Context.** User had base skills installed (42 bundled + creative/dev/novel-language etc.). This session added 11 new skills for wechat article writing, de-AI post-processing, card generation, image service, and seedance video.

## Skills installed

| Skill | Source | Files | Notes |
|-------|--------|-------|-------|
| `humanizer-zh` | qianleigood/crawclaw | 6 (13KB) | Lightweight Chinese de-AI. Quick touch-ups. |
| `de-ai-writing` | renky1025/agent-skills | 1 (16KB) | Full 5-step de-AI: detect, delete, voice-calibrate, rewrite, cross-check. |
| `card-generator` | diegosouzapw/awesome-omni-skill | 2 (6KB) | HTML card pages, 11 templates. Useful for wechat covers/summary cards. |
| `product-video-creator` | anbeime/skill | 5 (45KB) | Multi-agent product video pipeline. Requires moviepy. Only for video ads. |
| `wechat-pipeline` | aAAaqwq/AGI-Super-Team | 3 (11KB) | 3-stage pipeline: write → cover → release. Needs external sub-skills `wechat-article-writer`, `code-to-image`, `md2wechat` which may not be installed. Only for auto-publishing. |
| `wechat-article-writer-zhouyulsj` | zhouyulsj/wechat-article-writer | 15 (82KB) | **Primary wechat writing engine.** 4 content types, 4 Python scripts, 5 style YAMLs, 4 references. Sub-commands: topic, title, outline, write, polish, format, load, start, gen_image. |
| `geek-skills-wechat-article-writer` | staruhub/ClaudeSkills | 8 (68KB) | Alternative wechat writing. 4 styles (corporate/tech blog/event review/product review). Has anti-translation-chic L4 polish. |
| `image-service` | christophacham/agent-skills-library | 14 (129KB) | Multi-modal image processing. Has merge_long_image.py for stitching. Needs API key config in settings.json. |
| `content-illustration-strategy` | aAAaqwq/AGI-Super-Team | 4 (28KB) | Article image placement decisions. Not directly useful for railway narrative work. |
| `seedance-video` | openakita/openakita | 37 (794KB) | Full Hermes plugin for 即梦 video generation via 火山引擎 Ark API. Needs ARK_API_KEY env. |
| `intelligent-prompt-generator` | huangserva/skill-prompt-generator | 1 (very large) | Prompt generation framework with 7-category structure. NO Python backend — standalone text skill only. |

## Recommended workflow for this user

1. **Content outline + draft** → `wechat-article-writer-zhouyulsj` (use 历史叙事类 for railway/evolution stories)
2. **Polish de-AI** → `de-ai-writing` (deep) or `humanizer-zh` (quick)
3. **Cover/ending cards** → `card-generator`
4. **Section images via API** → `image-service` (text_to_image.py)
5. **Video/animation** → `seedance-video` (if pursuing storyboard direction)
6. **Auto-publish** → `wechat-pipeline` (only if user has WeChat API creds)

## Known gaps

- `wechat-pipeline` references `code-to-image` and `md2wechat` sub-skills that were NOT installed — pipeline will fail at Stage 2 and 3
- `wechat-article-writer-zhouyulsj` references `scripts/format_article.py` and `scripts/gen_image_prompts.py` — these exist in the skill dir but may need dependency installation
- `intelligent-prompt-generator` references non-existent Python modules (`core.cross_domain_generator`, `framework_loader`, `intelligent_generator`) — it's a standalone text skill only
- `seedance-video` is a Hermes plugin (plugin.py, 109KB) not a regular skill — may need to be loaded via the plugin system, not skills directory
