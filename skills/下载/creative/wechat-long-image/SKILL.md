---
name: wechat-long-image
description: "Create WeChat Official Account (公众号) long-scroll image articles — picture-heavy, text-light vertical compositions using HTML/CSS mockups as previews. Covers section structure, placeholder workflow, and interactive elements (SVG slide comparisons, tap-to-reveal)."
version: 2.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, long-image, 公众号, 长图, design, social-media]
    related_skills: [sketch, claude-design, baoyu-infographic, excalidraw, image-service, card-generator, wechat-article-writer-zhouyulsj, geek-skills-wechat-article-writer, de-ai-writing, humanizer-zh]
---

# WeChat Long-Image Article (公众号长图)

Create vertical long-scroll image compositions for WeChat Official Accounts. The user's design philosophy is **picture-heavy, text-light** — images do the storytelling, text is minimal (1-2 short lines per section).

## When to use this skill

- User asks for "公众号长图" or "公众号推文"
- User wants a "图片为主" (image-first) vertical layout
- User mentions "长图预览" (long-image preview)
- User wants WeChat article mockups with section-based storytelling

## Core design philosophy

This is NOT a PowerPoint deck, NOT a blog post with pictures, and NOT an infographic. It's a **scrollable image story** where each section is ONE full-bleed image with a ONE-line caption overlaid at the bottom. The entire composition feels like flipping through a photo book, not reading a slide presentation.

### ⚠️ CRITICAL ANTI-PATTERNS (recurring user rejections)

These mistakes were discovered across multiple iterations. Avoid ALL of them:

1. **❌ NO PPT-style layouts** — White background + centered text + title bar + body text = PowerPoint slide. This is the #1 rejection. Images must bleed edge-to-edge with NO card borders, NO side margins, NO white-background text sections.

2. **❌ NO text in separate cards between images** — Text always lives ON the image via a bottom gradient overlay (`.caption-overlay`). A text block between two images looks like a slide footnote and will be rejected.

3. **❌ NO descriptive captions** — A caption like "这是一张月山站的俯瞰图" is redundant when the image is right there. Keep captions interpretive, evocative, or short factual labels — never descriptive of what's on screen.

4. **❌ NO long paragraphs** — The user explicitly rejects text-heavy designs. One line per section maximum. If you're writing more than 15-20 characters of body text, you're writing too much.

5. **❌ NO planning narration before building** — When the user says "先做出来看看" or "做出来一个我看看", they want to SEE the output immediately. Build first, explain on feedback. Lengthy planning ("第一步我们做封面，第二步做历史篇...") frustrates the user.

6. **❌ NO 3 variants** — Unlike `sketch` skill conventions, for a WeChat long-image the user wants ONE focused pass they can react to. Produce the best single version, get feedback, iterate.

7. **❌ NO numbered section headers as separate text** — Don't put "01 / 道清铁路 · 1902" as a title bar before the image. It reads as a slide header. Embed the context INTO the image block (year badge, small tag overlay).

8. **✅ DO ask for a reference article/screenshot early** — A single good example saves 3+ rounds of iteration. The user is happy to provide one if asked directly. Say: "你有没有参考的样板？给我看看风格，我来照着做。"

---

## Workflow

### Step 1: Understand the topic
- Ask what the article is about (location, theme, angle)
- Establish the narrative arc: what story are you telling across the images?

### Step 2: Ask for reference
**Always ask for a reference example before building.** Say:
"有没有参考的样板公众号长图？截个图给我看看风格～"
This single step saves 2-3 rounds of iteration.

**If the user shares a WeChat link as reference:** use `urllib` with mobile MicroMessenger UA to extract the `js_content` HTML element. See `references/wechat-scraping.md` for the technique and Python code. Desktop UA triggers verification, mobile UA works.

### Step 3: Build one focused HTML preview
Produce a single, self-contained HTML file that simulates the WeChat reading experience (max-width 420px, mobile-first). Place it on the user's Desktop.
- Do NOT narrate your building plan to the user before building — they want to SEE the output, not hear about it
- Do NOT produce 3 variants — one focused pass, then iterate on feedback
- Section context (year, number, title) goes IN the image block via overlays, never as a separate text card between images

### Step 4: Explain clearly what to replace
After building, tell the user:
"What you need to do: 把每张图的色块替换成真实照片，然后用截图工具滚动截屏导出成一张长图就可以用了。"

---

## Template structure

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, max-scale=1.0">
  <title>{主题} · 长图预览</title>
  <style>
    /* Canvas: mobile width, no side margins */
    .canvas { max-width: 420px; margin: 0 auto; background: #fff; overflow: hidden; }

    /* Image blocks: full-bleed, various aspect ratios */
    .img-block {
      width: 100%; aspect-ratio: 4/3;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      position: relative; overflow: hidden;
    }

    /* Caption: gradient overlay at bottom of image */
    .img-block .caption-overlay {
      position: absolute; bottom: 0; left: 0; right: 0;
      padding: 40px 24px 20px;
      background: linear-gradient(transparent, rgba(0,0,0,0.6));
      font-size: 14px; color: #fff; letter-spacing: 2px;
    }

    /* Tag badge: small label overlaid on image */
    .img-block .tag {
      font-size: 12px; color: rgba(255,255,255,0.7);
      letter-spacing: 3px;
      border: 1px solid rgba(255,255,255,0.2);
      padding: 4px 16px; border-radius: 2px;
      position: relative; z-index: 1;
    }

    /* Section gap: thin separator between full-bleed images */
    .gap { height: 6px; background: #f5f0eb; }

    /* Section number: faint large number in corner for decoration only */
    .big-num {
      position: absolute; right: 20px; top: 16px;
      font-size: 48px; font-weight: 700;
      color: rgba(255,255,255,0.06);
      pointer-events: none;
    }

    /* CTA interaction section */
    .interact-section {
      width: 100%; aspect-ratio: 3/2;
      background: linear-gradient(135deg, #f8f4ef, #f0e8dd);
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      padding: 20px;
    }
    .interact-section h3 {
      font-size: 18px; color: #2c2c2c;
      font-weight: 600; letter-spacing: 4px;
    }
    .interact-section p {
      font-size: 12px; color: #aaa;
      letter-spacing: 2px; margin-top: 8px;
    }
    .interact-section .btn-area span {
      padding: 6px 20px; border: 1px solid #b87333;
      border-radius: 20px; font-size: 12px; color: #b87333;
      letter-spacing: 2px; display: inline-block;
    }
    .interact-section .btn-area span.filled {
      background: #b87333; color: #fff;
    }

    /* Footer */
    .footer-section {
      width: 100%; padding: 36px 24px;
      background: #1a1a2e; text-align: center;
    }
    .footer-section .qr {
      width: 90px; height: 90px; margin: 0 auto 14px;
      background: repeating-linear-gradient(45deg,
        #fff 0, #fff 3px, #000 3px, #000 7px, ...);
      border: 3px solid #fff; border-radius: 3px;
    }
    .footer-section .name {
      font-size: 14px; color: #e8d5b7;
      letter-spacing: 3px; font-weight: 600;
    }
    .footer-section .tip {
      font-size: 11px; color: rgba(255,255,255,0.4);
      letter-spacing: 2px; margin-top: 6px;
    }
  </style>
</head>
<body>
<div class="canvas">
  <!-- Cover -->
  <div class="img-block cover-bg">
    ...texture overlays...
    <h1>标题</h1>
    <div class="sub">副标题</div>
  </div>
  <div class="gap"></div>

  <!-- Section N (repeat for each) -->
  <div class="img-block section-bg">
    <div class="big-num">0N</div>
    <div class="tag">标签文字</div>
    <div class="caption-overlay">一句话说明</div>
  </div>
  <div class="gap"></div>

  <!-- CTA -->
  <div class="interact-section">...</div>

  <!-- Footer -->
  <div class="footer-section">...</div>
</div>
</body>
</html>
```

## Section design patterns with color palettes

### 1. Cover
- Aspect ratio: 3/4 (portrait-first feel)
- Dark/atmospheric gradient background
- Minimal text: title + subtitle only
- Decorative elements: grid texture, animated lights, track lines
- Color: deep navy (#0f0c1a → #1a1a3e → #0f3460)

### 2. Historical
- Color palette: sepia / brown (#3d2b1f, #6b4c3b, #8b6914)
- Add a timeline strip (thin vertical lines with years)
- Caption: single evocative sentence
- Background texture grid overlay

### 3. Feature/Hub
- Color: industrial slate blue (#1a2a3a, #2c4a6a, #3a6b8f)
- Radiating lines or network patterns (SVG overlay)
- Can use a comparison block (old vs new)

### 4. Scenery
- Color: nature greens (#1a3d2a, #2d5a3d, #4a7c5c)
- SVG scenic silhouettes (mountains, sunset circles)
- Two variants: wide landscape (16/10) or tall portrait (4/3)

### 5. Human/Emotion
- Color: warm orange-brown (#6b3a1a, #8b5e3c, #c48b5e)
- Followed by an interaction CTA section

### 6. Future
- Color: cool tech blue (#0a1628, #1a3a5c, #2d6a9f)
- Speed lines, glowing dots, clean geometric patterns
- Tagline: hopeful, forward-looking

### 7. CTA Footer
- QR code placeholder (CSS-generated checkerboard)
- "长按识别二维码关注"
- Dark background, gold accent text

## Decorative SVG overlays (in-place patterns)

### Radiating rail lines (for hub/transit sections)
```html
<svg width="100%" height="100%" viewBox="0 0 200 130"
     preserveAspectRatio="xMidYMid slice" style="position:absolute;inset:0;opacity:0.15;">
  <line x1="100" y1="130" x2="10" y2="10" stroke="#e8d5b7" stroke-width="0.5"/>
  <line x1="100" y1="130" x2="50" y2="10" stroke="#e8d5b7" stroke-width="0.5"/>
  <!-- repeat for more lines -->
</svg>
```

### Mountain silhouette (for scenery sections)
```html
<svg width="100%" height="100%" viewBox="0 0 200 150"
     preserveAspectRatio="xMidYMid slice" style="position:absolute;bottom:0;opacity:0.2;">
  <path d="M0,150 L20,130 L40,140 L60,110 L80,125 L100,95 L120,110 L140,80 L160,100 L180,75 L200,90 L200,150 Z" fill="#0a1a0a"/>
</svg>
```

### Speed lines (for future/speed sections)
```html
<svg width="100%" height="100%" viewBox="0 0 200 150"
     preserveAspectRatio="xMidYMid slice" style="position:absolute;inset:0;opacity:0.1;">
  <line x1="80" y1="75" x2="20" y2="75" stroke="#fff" stroke-width="0.5"/>
  <!-- repeat for more lines at different Y positions -->
</svg>
```

### Track pattern (for cover bottom edge)
```css
.s-cover .track-bottom {
  position: absolute; bottom: 0; height: 70px; left: 0; right: 0;
  background: repeating-linear-gradient(90deg,
    transparent 0%, transparent 8%, rgba(232,213,183,0.12) 8%, rgba(232,213,183,0.12) 9%,
    transparent 9%, transparent 17%, rgba(232,213,183,0.12) 17%, /* repeat for full width */
  );
}
```

### Timeline strip (compact, on-image)
```html
<div style="display:flex;justify-content:space-between;width:85%;">
  <div style="text-align:center;">
    <div style="width:2px;height:24px;background:#b87333;margin:0 auto 4px;"></div>
    <div style="font-size:11px;color:#e8d5b7;font-weight:600;">1902</div>
  </div>
  <!-- repeat for each year -->
</div>
<div style="position:absolute;top:13px;left:6%;width:88%;height:1px;background:linear-gradient(90deg,rgba(232,213,183,0.3),rgba(232,213,183,0.3),transparent);"></div>
```

### Section-side vertical text decoration
```css
.vert-text {
  position: absolute; left: 12px; top: 50%;
  transform: translateY(-50%);
  writing-mode: vertical-rl;
  font-size: 11px; color: rgba(255,255,255,0.08);
  letter-spacing: 4px;
}
```

## Interactive elements (visual simulation only)

**These are visual simulations for the HTML preview.** The real production deliverable is a static image.

### SVG slide comparison (old vs new)
```html
<div class="compare-wrapper" id="compare1">
  <div class="compare-inner">
    <div class="img-old">{old photo placeholder}</div>
    <div class="img-new" id="slider1">{new photo placeholder}</div>
    <div class="drag-hint">‹ 左右滑动对比 ›</div>
  </div>
</div>
```
JS: mouse + touch drag to resize the "new" layer's width percentage.

### Tap button simulation
```html
<div class="btn" onclick="this.textContent='✅ 感谢留言！'">✍️ 写留言</div>
```

## Placeholder strategy

Use CSS gradients for colored placeholders with text hints:

```css
.bg-historical { background: linear-gradient(135deg, #3d2b1f, #6b4c3b, #8b6914); }
```

Text hint inside: `🚂 老道清铁路 · 历史插画风格`

When the user replaces with real photos:
1. Open the HTML file
2. Replace each `.img-block` background/gradient with `<img src="实际照片路径.jpg" class="img-full" style="width:100%;height:100%;object-fit:cover;">`
3. Adjust aspect ratio to match the photo's natural crop
4. Export as a single tall image。**优先用系统自带 Chrome 的无头模式直接出 PNG**——比手动滚动截屏稳、可批量、可 2x 高清，而且不用装 playwright（本机 `C:/Program Files/Google/Chrome/Application/chrome.exe` 已实测可用，Edge 同在 `C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`，参数相同）：

   ```bash
   "C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --hide-scrollbars \
     --force-device-scale-factor=2 --window-size=420,4200 \
     --screenshot="D:/out/长图.png" "file:///D:/out/长图.html"
   ```

   `--window-size` 的高度必须给足整页高度，否则底部会被截掉（截出来的空白/缺失都是这个原因）；中文路径用 `file:///` + 正斜杠传给 Chrome 没有转义问题。
   这套命令对**任何本机 HTML 产物**都通用（长图、公众号排版页、逻辑图/配图、小红书图文页），不限于本技能。
   出图后自己看图确认（中文有无乱码、文字有无溢出、元素有没有被截断）再交付。
   FastStone 之类的滚动截屏工具只作为备选。

## Transition pages between sections

Multi-image narratives need **transition pages** between sections to avoid jarring jumps. See `references/transition-page-design.md` for the full technique.

Key rules:
1. Transition pages are **half-height** compared to main images
2. Background color **gradients** from the previous section's tone to the next section's tone
3. A single **directional element** (wheel, railroad tie, curtain, speed lines, floating ticket) visually signals time passing
4. No text on transition pages — text lives only on main images
5. This creates a cohesive story feel: "like flipping through a picture book"

Example sequence for a railway history long-image:
```
封面 (暖黄) → 车轮(暖黄→棕褐) → 1902 (棕褐) → 枕木(棕褐→军绿) → 1970 (军绿) → 窗帘(军绿→暖橙) → 2000 (暖橙) → 风景拉长(暖橙→蓝白) → 高铁 (蓝白) → 车票(蓝白→暖黄) → 互动
```

This transition chain was validated with a Jiaozuo railway user — it was well received.

### Image generation via external tools (prompt-and-assemble pattern)

When this user needs images but the active model can't generate them (e.g. DeepSeek), follow the **prompt-and-assemble** workflow:

1. **Plan** the narrative arc and image list
2. **Write detailed prompts** using the technique in `references/image-prompt-generation.md`
3. **Save to Desktop as `.txt` file** — save as `{主题}_提示词.txt` (NOT .md). The user explicitly rejected .md files because Windows sometimes doesn't associate them with an editor. .txt opens correctly in Notepad. Always use .txt extension for prompt files delivered to this user.
   - **Reference.** When writing the narrative script to accompany images, also use `.txt`.
     The script itself is the story framework — NOT a final article. It anchors each image's emotional direction in 1-2 lines and provides the narrative flow that transitions between sections. Keep it at ~600 words total for a 12-16 image piece. For a validated example structure (Jiaozuo railway, 4 eras + transitions, 17 panels), see `references/narrative-script-example.md`.
4. **User generates images** externally and brings them back
5. **Assemble** into the long-image HTML once images are ready

Each prompt must include: perspective/framing, three-layer scene composition (近景/中景/远景), color/tone, text overlay specs, and aspect ratio (3:4 for WeChat).

## 卡通/绘本风格 vs 写实风格

When writing image prompts, prefer **illustration/storybook style** over photorealistic for narrative long-images:
- 卡通/绘本风对画面细节的容错率更高（"卡通嘛，艺术加工～"）
- 写实照片有明显的地标/时代细节，一旦出错观众就会出戏
- 卡通/绘本风的色调和风格统一性更易控制
- **This is a deliberate strategy the user discovered through trial and error** — WorkBuddy images were too realistic and detail-inaccurate. Cartoon style is the recommended default for AI-generated narrative content.

Follow the same prompt structure but append style directives like:
- "手绘插画/绘本风，不追求写实"
- "简笔画小人，氛围感优先"
- "色彩温暖，有年代感"

## 横版「列车侧影」叙事手法 (horizontal train-side POV)

An alternative to the vertical long-scroll: a **horizontal composition showing the side of a train**, with each carriage window showing a different era. The viewer stands beside the track as the train passes from right to left.

### Composition

- Train is seen from the side, the viewer's line-of-sight is perpendicular to the train's direction
- Locomotive at the front, followed by carriages representing different eras
- Each carriage has windows showing scenes from that era
- The train's livery evolves along its length (black steam → green → red/white → white high-speed)
- The viewer's eyes travel from right (past) to left (present)

### Key narrative device: 「穿越车门/车窗」transition

The most effective transition between eras is **passing through a train door or window** — the "frame within a frame" device:

1. **Era A** (e.g. 1902): Camera faces coal wagons with open side-doors. Coal wagon① full, ② half-full, ③ empty with doors wide open.
2. **Camera passes through** the empty wagon's open door — the door frame fills the screen briefly, then opens into the new scene.
3. **Era B** (e.g. 1970): Low-angle perspective, standing on ground beside the track. A green train is visible below/in the foreground. The background shows the next era's city silhouette.
4. **Camera zooms in** on one window — a girl leaning on the sill, looking out.
5. **Focus shifts** to another window behind the girl.
6. **Camera passes through** that window — same "frame fill" transition.
7. **Era C** (e.g. 2000): Emerges on the other side — new train below, new city background. Same low-angle perspective.

**Critical rules for this technique:**
- Camera perspective: **low angle, eye-level, perpendicular to the train's direction**
- NOT aerial/overhead — the viewer is standing on the ground beside/ below the track
- The "passing through" moment IS the transition — it replaces hard cuts or color fades
- The door/window frame briefly fills the screen, then opens into the new scene
- Each emergence reveals: a train (new era) + city background (new era) in one shot
- Pre-1970 freight trains have NO passenger windows (historically correct — 运煤车). Use open side-doors as the transition portal.
- After 1970, passenger trains have windows, so windows become the transition portal.

### Symmetrical three-act structure

```
🚪 Pass through coal wagon door (1902)
    ↓
🚃 Green train + old city skyline (1970)
    ↓ zoom to girl at window → focus shift to another window →
🪟 Pass through that window
    ↓
🚄 New train + newer city skyline (2000)
    ↓
🪟 Pass through again (optional)
    ↓
🚄 High-speed train + modern city
```

Each act uses the same low-angle, ground-level perspective. The consistent framing is: **train body crossing the frame horizontally + city silhouette in the background**.

### Content accuracy rules for Chinese railway history
- 🚫 **DO NOT include Yueshan Station (月山站) in image content** — it's outside the city in a remote mountain area, doesn't fit the "urban change by railway" narrative. May appear in text captions but NOT in image prompts or visual content.
- 🚫 **DO NOT use specific building names** (Wanda Plaza, postal building, trade center) unless the user explicitly provided them. Use generic terms: "city skyline", "modern buildings", "old brick buildings".
- ✅ **Railway is the protagonist, city atmosphere is the background** — the narrative is about how railway development changed the city's character over time.
- ✅ **1902 steam trains carried coal, not passengers** — no passenger windows. Use open side-doors of coal wagons as the visual transition portal.
- ✅ **Caption/location references are fine in text copy** — Yueshan Station name can appear in narrative text added later, just not in the generated images.

## "车窗视角" narrative technique (window-perspective POV)

A validated creative framing for timeline/city-evolution stories: see `references/window-perspective-narrative.md` for the full technique.

Core idea: each image uses the same "seat behind a window" perspective. The **window frame evolves** across the sequence (wood → green painted metal → plastic → curved modern → wide high-speed), signaling the era without text. The view outside shows the changing world.

Three-layer composition per image:
1. **近景 Foreground** — window frame + interior detail (seat, curtain, tray table)
2. **中景 Midground** — the main scene (station, tracks, city)
3. **远景 Background** — sky, mountains, distant silhouette

## User preferences (this user)

Recorded in memory and this skill's version history. Critical ones:
- 🚫 **Absolutely NO text-heavy designs** — text is labels and 1-line captions only
- 🚫 **NO PPT-style white background layouts** — images must be full-bleed, no card borders
- 🚫 **NO separate text sections between images** — text goes on the image overlay only
- 🚫 **NO 色块+文字标签占位** — use atmospheric gradients with decorative SVG elements as placeholders, not obvious "put photo here" boxes
- 🚫 **NO "plan narration" before building** — the user says "做出来一个我看看" and wants the OUTPUT, not a description of what you're about to make. Build first, explain on feedback.
- 🚫 **NO 3-variant comparison** — unlike the `sketch` skill pattern, for a WeChat long-image produce ONE focused pass, get feedback, iterate.
- 🚫 **NO numbered section headers as separate text/cards between images** — context (year, section number) belongs ON the image block via overlays (badge, tag, faint big number in corner). A "01 / 标题" in its own white card reads as a PowerPoint slide header.
- 🚫 **NO text in image prompts** — text is added later manually, never baked into AI-generated images
- ✅ **Picture-heavy, image-first**
- ✅ **Ask for a reference before building** — ask directly: "有没有参考的样板公众号长图？截个图给我看看风格～" This saves 3+ rounds.
- ✅ **Build ONE version, get feedback, iterate**
- ✅ **Text MUST live on the image overlay** (`.caption-overlay` bottom gradient), never in a separate card between images
- ✅ **Captions must be evocative, not descriptive** — don't say "这是一张月山站的俯瞰图" when the image is right there; say something interpretive or short
- ✅ **External reference: taste-skill** — the user found and downloaded https://github.com/Leonxlnx/taste-skill which contains agent skills for frontend design taste. Available at C:\\Users\\使用者\\Desktop\\taste-skill\\. Useful as a design reference.
- ✅ **External reference: popular-web-designs skill** — Available as a Hermes skill (`popular-web-designs`). Contains 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS. Load via `skill_view(name='popular-web-designs')` for design inspiration.
- ✅ **External reference: open-design** — also cloned to Desktop at C:\\Users\\使用者\\Desktop\\open-design\\. Large Node.js project with 259+ skills and 142+ design systems. Not actively used.
- ✅ **Installed wechat writing skills (July 2026, 7 new)** — the user installed these for structured wechat article writing and editing:
  • **`wechat-article-writer-zhouyulsj`** — FULL wechat article writing engine (best for content creation). 4 content types: 科普类(DingXiangYiShi style), 历史叙事类(LuKewen style), 学校宣传类, 论文速递类. Has 4 Python scripts (format_article.py, gen_image_prompts.py, generate_titles.py, load_materials.py), 5 style yamls (ai_play, flat_design, hand_drawn, minimalist, photo_real), 4 references (commands, style_guide, etc), image_prompts.yaml. Sub-commands: `topic`, `title`, `outline`, `write`, `polish`, `format`, `load`, `start`, `gen_image`. **Load this FIRST for structured wechat article writing.** The 历史叙事类 style is most relevant for this user's railway/history narratives — it uses story-driven structure, emotional cadence, and grounded realism.
  • **`geek-skills-wechat-article-writer` (staruhub)** — Alternative wechat writing skill. 4 styles (Corporate/官方, Tech Blog/个人技术, Event Review/活动回顾, Product Review/评测对比). Has anti-translation-chic post-processing (L4 polish), quality checklist, emoji library (8539 bytes), template structure reference. The **Tech Blog style** matches this user's voice best (personal, opinionated, grounded). **Use for: personal brand articles, technical story-driven content, railway narrative with personal POV.** The anti-translation-chic section is its unique differentiator.
  • **`wechat-pipeline`** — 3-stage pipeline (Write → Cover → Release) with checkpoint gates. Depends on external sub-skills `wechat-article-writer`, `code-to-image`, `md2wechat`. Requires Node.js + Puppeteer + WeChat API keys. **Only for production auto-publishing flows, not for content drafting.** Skip unless user explicitly wants to publish via API.
  • **`de-ai-writing`** — Comprehensive 5-step de-AI process (Detect → Delete → Voice Calibration → Rewrite → Cross-check). 11-class AI-trace detection with scoring system. **Best for final polish pass** after content is written. Higher quality than `humanizer-zh` but slower.
  • **`humanizer-zh`** — Lightweight Chinese text humanization (6 files, 13KB). AI pattern catalog, style & soul, workflow & output references. **Use for quick touch-ups**, `de-ai-writing` for deep cleans.
  • **`card-generator`** — Card-style HTML webpage generator, 11 template styles (tech-gradient, minimal-clean, dark-terminal, vibrant-pop, business-pro, glass-morphism, luxury-gold, geometric-bauhaus, nature-fresh, retro-vaporwave, shadow-stacked). **Useful for WeChat cover images and summary cards.** Generates single HTML with JSZip download.
  • **`product-video-creator`** — Multi-agent product video pipeline. Has `video_composer.py` requiring moviepy/opencv-python. Only relevant if user is making video ads.
  • **`image-service`** (christophacham, July 2026) — Multi-modal image processing: text-to-image, image-to-image, OCR, long-image merge, marketing materials pack. Has 5 Python scripts with configurable API endpoint. **Directly useful for the wechat long-image workflow** — the `merge_long_image.py` script can stitch images vertically, and `text_to_image.py` can generate section images if an API key is configured. References include `long-image-guide.md`, `marketing-templates.md`, and `text-rendering-guide.md`.
  • **`seedance-video`** (openakita, July 2026) — Complete Hermes plugin for 即梦/Seedance video generation via 火山引擎 Ark API. 37 files, 794KB. Supports text-to-video, image-to-video, video editing, long video pipeline (shot decomposition + concat). Requires `ARK_API_KEY` env var. **Relevant if the user pursues the animation/storyboard direction** — their 18-shot Jiaozuo railway storyboard could use this.

  **Recommended writing workflow for this user:**  
  1. Load `wechat-article-writer-zhouyulsj` → use `start` or `write` with 历史叙事类 (for railway) or 科普类 (for general)  
  2. After content draft is ready, load `de-ai-writing` → run 5-step polish  
  3. If making cover/ending cards, load `card-generator` for HTML card creation  
  4. If generating section images via API, load `image-service` → use `text_to_image.py`  
  5. `wechat-pipeline` only if publishing to WeChat backend API  
  6. `geek-skills-wechat-article-writer` as alternative if the zhouyulsj style doesn't fit — its 个人技术博客 style may suit autobiographical content better  
  7. `seedance-video` only if the user is making video/animation from the storyboard

- ✅ **Installed AI video/storyboard skills (June 2026, 11 new)** — the user installed these for structured video/storyboard prompt writing. Relevant ones for long-image planning:
  • `ai-video-shot-planner` — script analysis to shot table with spatial anchoring cards (scene layout, character positioning, axis management). Good for planning multi-scene narratives before writing prompts.
  • `director-narrative-flow` — shot sequencing rules (establishing wide -> medium -> close-up -> resolution), 180-degree axis, eye-line matching, pacing control (alternate shot scales)
  • `seedance-storyboard-generator` — full "script-assets-video-edit" pipeline with character profile prompts, triple-view asset generation, voice/sound design
  • `video-prompt-generator` — 7-layer prompt structure (Subject/Action/Environment/Camera/Lighting/Style/Tech), professional camera movement terminology (Dolly vs Zoom), JSON Prompting format
  • `ai-camera-director` — professional camera movement prompts with 4-section structure (Header/Camera Movement/Subject & Action/Environment & Mood), single-shot and storyboard modes
  • `wan2-2-flf2v-pipeline` — Wan2.2 first/last frame to video interpolation pipeline; useful for understanding "what happens between frame A and frame B" when planning scene progression
  • `novel-language-style` — writing style spectrum (7 types: 白描/华丽/口语化/文艺/中二/翻译腔/新媒体风), narrative perspective selection, cinematography techniques for text
  • Other installed but less directly relevant: `storyboard-director`, `video-analysis` (needs vision), `seedance-product-360`, `dream-video-prompt-generator`, `visual-language`, `libtv-skill`
  When planning a long-image narrative, consider loading `ai-video-shot-planner` first for spatial anchoring, then `director-narrative-flow` for shot rhythm.
- ✅ **WorkBuddy prompt-and-assemble workflow** — this user uses WorkBuddy (腾讯 CodeBuddy) for image generation. Hermes plans + writes prompts → user pastes into WorkBuddy → user brings images back → Hermes assembles.
- ✅ **"车窗视角" narrative technique** — validated creative framing. See `references/window-perspective-narrative.md`.

## Pitfalls

- ❌ **DO NOT fabricate domain-specific visual details** — This is the #1 rule. If you're writing prompts about something the user knows well (e.g. their hometown's railway history, local landmarks, historical vehicles), and you're unsure about a visual detail (train door design, carriage type, building facade, era-appropriate clothing), do NOT invent, do NOT "infer", do NOT "fill in reasonably". The user explicitly corrected: "以后不要自己编，可以问我，但是不要自己编" and later "你已经是个成熟的人工智障了，让我省点心吧。"
  **Correct workflow for unknown visual details:**
  1. FIRST: **search the web** for reference images, Wikipedia articles, or authoritative descriptions. Use keywords like "{object} old photograph side view 1900 vintage China".
  2. If search succeeds, incorporate the real visual details into the prompt.
  3. If search fails (blocked, no results found), state what you're missing concisely and ask a targeted question. Don't ask expansively. Example: "搜不到那个年代的运煤车照片，你知道大概长啥样吗？说两句就行。"
  4. When the user provides details, **save them as a reference file immediately** under the skill so you don't ask again.
  This applies to ALL prompt writing, not just railway topics. Fabricated details waste the user's credits, time, and trust.
- ❌ Don't write paragraphs — user rejects text-heavy immediately
- ❌ Don't produce 3 variants — one focused pass is preferred
- ❌ Don't narrate your building plan first — just build it
- ❌ Don't treat HTML as final product — it's a disposable preview
- ❌ Don't call yourself "瞎" or "笨" when vision fails — say "乖乖现在还不能看图，等你以后给我加了摄像头就能看到啦！" (使用者不喜欢自贬)
- ❌ Don't retry vision API calls if they fail — the model doesn't support image input. Ask for a verbal description instead.
- ❌ Don't use placeholders that look like 色块 with text labels — the user rejected this style as looking like PPT. Use atmospheric CSS gradients with subtle SVG decorative elements (radiating lines, mountain silhouettes, speed lines, timeline strips) instead. The placeholder should feel like it COULD be the final image, not a put-photo-here sign.
- ❌ Don't use character-count abbreviation in Chinese class names (`.s-cover`, `.s-hub`) — use readable full names (`.section-cover`, `.section-hub`). Abbreviated names make maintenance harder especially in Chinese context.
- ❌ Don't over-plan or describe your build plan to the user before building — they want to SEE the output, not hear about the plan. Build first, explain on feedback.
- ✅ Add `.gap` elements (6px) between sections for visual breathing room
- ✅ Keep the .canvas at max-width 420px (WeChat article width)
- ✅ Add vertical text decoration for section-side labels
- ✅ Color palettes must be meaningful, not decorative
- ✅ If vision fails, ask the user to describe verbally — don't keep retrying
- ✅ Remove text from image prompts — user adds text manually later
