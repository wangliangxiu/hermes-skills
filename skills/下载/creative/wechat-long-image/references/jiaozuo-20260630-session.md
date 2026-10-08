# Session: Jiaozuo Railway Long-Image (June 30, 2026)

## Session context

The user wanted to create a WeChat Official Account long-image about Jiaozuo city's railway history (1902 to present). After multiple iterations, the final agreed direction:

- **Horizontal "train passing by" composition** (横版), not vertical long-scroll
- **Cartoon/illustration style** (卡通/绘本风) to avoid AI detail inaccuracies
- **Three transitions** through train doors/windows between eras
- **Low-angle ground-level perspective** (not aerial)
- **No text in images** — text added manually during assembly
- **WorkBuddy for image generation** — user pastes prompts, brings images back for assembly

## Files created on Desktop

1. `本地铁路_提示词.txt` — first version prompts (vertical, realistic, since superseded)
2. `本地铁路_绘本提示词.txt` — cartoon style prompts, 6 images + 5 transition pages
3. `本地铁路_过渡修改.txt` — separate prompt for adding rail tracks as transition element
4. `本地铁路_横版提示词.txt` — horizontal train-side composition prompts (10 windows)
5. `本地铁路_动画分镜.txt` — animation storyboard (first version, one-zoom-through)
6. `本地铁路_动画分镜v2.txt` — animation storyboard v2 (one-shot continuous tracking shot)

## Key design decisions from this session

- Railway is protagonist, city atmosphere is background — NOT specific landmarks
- Yueshan Station (月山站) excluded from images — only mentioned in text
- Steam-era freight trains had NO passenger windows
- Coal wagons with open doors serve as visual transition portals
- Three-act symmetrical passage structure through door/window frames
- Girl at window as emotional anchor in 1970 segment
- Pass-through-transitions replace hard cuts and color fades

## Session corrections received

**June 30, 2026 — DO NOT FABRICATE TRAIN DOOR DETAILS**
- User tested WorkBuddy prompts I wrote; the steam-era train door was wrong
- I had described it based on vague impressions, not actual knowledge
- The correct door for steam-era Jiaozuo coal wagons: "like a black shipping container" — black iron box body, heavy cargo doors, no passenger windows
- User gave a firm correction: "不要自己编，可以问我，但是不要自己编"
- Lesson: when writing prompts about a subject the user is a local expert on (their hometown, their hobby, their profession), always ask for reference descriptions rather than inventing details. Prompts with fabricated details waste their WorkBuddy credits.

**June 30, 2026 — SEARCH FIRST, DON'T ASK AGAIN**
- Later in same session user got frustrated: "你不用加形状，你直接照着搜同时期的运煤火车车厢不行吗"
- "以后都这样自己搜索，不要让我再告诉你了，有点累。你已经是个成熟的人工智障了，让我省点心吧"
- Lesson: When I don't know a visual detail, my first move should be WEB SEARCH — not asking the user. Search failed because my terminal couldn't reach image search results, but I should still TRY. Only if search genuinely fails should I ask a targeted question.
- Also: after the user DID teach me the correct carriage details, I saved them to `references/chinese-train-carriage-facts.md` so I never need to ask again.

**Correct workflow now encoded in the skill's Pitfalls section.**
