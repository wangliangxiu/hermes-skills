---
name: html-video-presentation
description: "Create animated video presentations as single-file HTML using Canvas + requestAnimationFrame — for product promos, event recaps, campaign reels, explainers, and demo reels. NOT for UI mockups (use sketch) or data dashboards (use markdown-viewer)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, canvas, animation, video, presentation, promotion, campaign, explainer]
    related_skills: [sketch, claude-design, manim-video, remotion]
    category: creative
---

# HTML Video Presentation

Create animated video presentations as single-file HTML. Uses Canvas 2D + `requestAnimationFrame` for smooth 60fps continuous animation — NOT CSS-transition slides or paginated decks.

Load this when the user says: "make a video about X", "create a promo reel", "generate a campaign video", "I need a short animated presentation", "make it look like a real video not a slideshow", or similar.

## When to use vs alternatives

| This skill | Alternative |
|---|---|
| Short animated videos (30s-5min) | `manim-video` for math/science animations |
| Promo, campaign, event recap | `remotion` for production-grade React video files |
| Explainer, demo reel | `sketch` for UI mockups |
| Social media clip | `comfyui` for AI-generated video |
| 党政/政务宣传片 (government propaganda videos) | Use this skill — political/government-themed work requires 沉稳庄重 (solemn/dignified) tone, restrained color palette, formal language, official seals/emblems |

## Architecture: The core pattern

```
Single HTML file
├── <canvas>          # 1280x720 for HD, or 1920x1080 for full HD
├── <script>
│   ├── Global state: t (time in seconds), playing flag
│   ├── Segment array: [{start, end, title}]
│   ├── Per-segment render functions (renderScene0..N)
│   ├── requestAnimationFrame loop: calls render(t) then t += 1/60
│   ├── Subtitle system: getSubtitle(t) returns current text
│   ├── Controls: play/pause, restart, keyboard shortcuts
│   └── Utility functions: lerp, easeInOut, roundRect, drawSubtitle
```

## Step-by-step

### 1. Gather requirements

Ask the user about:
- **Theme/topic** — what is the video about?
- **Duration** — typical lengths: 30s (social), 90s (promo), 3min (explainer)
- **Tone** — solemn, energetic, educational, cinematic, celebratory
- **Color palette** — ask for 2-3 keywords or references
- **Audience** — who is this for?
- **Script/outline** — do they have one, or should you write it?
- **Realism** — if they expect photorealistic video (真人实拍), be honest: Canvas HTML cannot do that. Offer to make a stylized animated version instead.

### 2. Plan the structure

Define segments as an array of time ranges:

```javascript
const SEGMENTS = [
  {start:0, end:15, title:'Opening'},
  {start:15, end:40, title:'Chapter 1'},
  // ...
];
```

Total video length is typically 90-180 seconds. Each scene 15-40 seconds.

### 3. Build per-scene render functions

Each `renderSceneN(t)` function:
1. Fills background with scene colors
2. Animates elements in/out using `t - sceneStart` as local time
3. Uses `easeInOut(clamp((lt - delay) / duration, 0, 1))` for smooth entrances
4. Draws decorative elements (lines, glows, gradients)
5. Calls `drawSubtitle(t)` at the end

### 4. The subtitle system

```javascript
function getSubtitle(t){
  if(t<20) return 'Opening subtitle';
  if(t<50) return 'Chapter 1 subtitle';
  // ...
}

function drawSubtitle(t){
  const text = getSubtitle(t);
  // Semi-transparent bottom bar
  ctx.fillStyle = 'rgba(7,18,32,0.85)';
  ctx.fillRect(0, H-65, W, 65);
  // Gold accent line on top of bar
  ctx.fillStyle = 'rgba(201,168,76,0.3)';
  ctx.fillRect(0, H-65, W, 1);
  // Bold subtitle text
  ctx.font = 'bold 18px "Microsoft YaHei","SimHei",sans-serif';
  ctx.fillStyle = 'rgba(232,213,163,0.9)';
  ctx.fillText(text, W/2, H-32);
}
```

### 5. Controls and UX

Always include:
- **Play/Pause** button (toggle)
- **Restart/Replay** button
- **Keyboard**: Space = play/pause, ← → = skip segment
- **Click seek**: click on canvas to jump to that position
- **Progress display**: "MM:SS / MM:SS"
- **Subtitle bar**: always visible at bottom

### 6. Output and feedback

Write the file to the user's Desktop or project directory. Tell them:
1. Open in browser
2. Click **▶ Play** to watch
3. Show the keyboard shortcuts table

## Utility functions (always include)

```javascript
function lerp(a,b,p){ return a+(b-a)*p; }
function clamp(v,m,M){ return Math.max(m,Math.min(M,v)); }
function easeInOut(t){ return t<0.5?2*t*t:1-Math.pow(-2*t+2,2)/2; }

function roundRect(ctx,x,y,w,h,r){
  ctx.beginPath();
  ctx.moveTo(x+r,y);
  ctx.lineTo(x+w-r,y);
  ctx.quadraticCurveTo(x+w,y,x+w,y+r);
  ctx.lineTo(x+w,y+h-r);
  ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
  ctx.lineTo(x+r,y+h);
  ctx.quadraticCurveTo(x,y+h,x,y+h-r);
  ctx.lineTo(x,y+r);
  ctx.quadraticCurveTo(x,y,x+r,y);
  ctx.closePath();
}
```

## Decision tree for presentation type

| User says | Approach |
|---|---|
| "真人实拍" / "写实" / "photorealistic" | Be honest: Canvas cannot do this. Offer stylized animation or suggest real video production. |
| "宣传片" / "promo" / "campaign" | Full HTML video with Canvas. Multiple scenes, narration subtitles, music (Web Audio optional). |
| "短视频" / "short clip" / "reel" | Keep under 60s. Few scenes, punchy visuals, fast transitions. |
| "PPT风格" / "slides" | If they say "像PPT了", that's a signal you're doing it wrong — animate continuously, don't page-switch. |

## Pitfalls

1. **CSS slides ≠ video — DO NOT make a slideshow.** If the user says "这不是视频,像PPT" or "跟PPT一样", it means you used CSS transitions on divs or paginated scene switches instead of continuous Canvas animation. This is the #1 failure mode of this skill. Fix by: (a) switching to Canvas + requestAnimationFrame exclusively; (b) making elements animate in/out **within** a scene rather than switching whole scenes; (c) using the segment-based architecture where scenes flow into each other imperceptibly.

2. **"小视频" means "short continuous video", NOT "翻页PPT".** When the user asks for "短视频" or "小视频", they expect smooth, continuous motion — elements sliding in, camera-like pans, staggered entries, and natural fade-outs — not discrete page turns or card fly-ins that pop into existence. Every element should have an entrance animation (easeInOut, spring-like) that lasts at least 0.5s. Card fly-ins with gaps between them are still "翻页" if they arrive one-at-a-time with nothing else happening.

3. **Don't fake it.** Canvas animation is NOT real video. If the user insists on 真人实拍 (real-person footage), say so upfront — don't overpromise. Offer stylized animation or suggest professional video production.

4. **Performance.** 1280x720 canvas is safe for most machines. 1920x1080 may lag on older hardware. Default to 1280x720.

5. **Font rendering.** Chinese text on Canvas uses system fonts. Ensure the font-family stack includes common Chinese fallback fonts.

6. **Subtitle visibility.** Always use a dark semi-transparent bottom bar with gold-accented top border. White text directly on video content is unreadable.

7. **Scene transitions are invisible.** Each scene is just a different render function — no CSS transition, no page turn. Elements animate in/out within the scene; scene boundaries are imperceptible to the viewer. If you find yourself switching the whole scene at once, you're building a slideshow, not a video.

8. **Test in browser.** Always write the file and tell the user to open it — don't just describe it.

## Recording to video file

The HTML Canvas animation can be recorded to a real WebM video file using the MediaRecorder API. Add this to the script block:

```javascript
// Recording
function startRecording(){
  var stream = canvas.captureStream(30);   // 30 fps
  var chunks = [];
  var recorder = new MediaRecorder(stream, {mimeType: 'video/webm;codecs=vp9'});
  recorder.ondataavailable = function(e){
    if(e.data.size>0) chunks.push(e.data);
  };
  recorder.onstop = function(){
    var blob = new Blob(chunks, {type:'video/webm'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'video_' + Date.now() + '.webm';
    a.click();
    URL.revokeObjectURL(url);
  };
  recorder.start(1000);   // collect data every 1s
}
```

Pair this with a toggle button that starts/stops recording. The user opens the HTML in Chrome, clicks play + record, and gets a .webm file when done.

## Animation curve selection

| Effect | Function | Use case |
|--------|----------|----------|
| Smooth entrance | `easeInOut(t) = t<0.5 ? 2*t² : 1-(-2t+2)²/2` | Cards, text, people appearing |
| Spring-bounce | `1 - Math.pow(1-t, 3)` for fast settle; or use CSS-like spring | Title slams, emphasis elements |
| Subtle float | `Math.sin(t * freq)` + small amplitude | Background glow, decorative pulse |
| Linear drift | Direct `lerp` with no easing | Camera pans, slow scroll |

**Rule of thumb:** if an element starts at opacity 0 and ends at opacity 1, also animate its Y position by 20-40px (from below) so it "drifts in" rather than fading in place. Elements that just fade in feel static and "PPT-like".

## Animation density checklist

Before delivering a video presentation, check:

- [ ] Every scene element has an entrance animation (not just opacity:0→1)
- [ ] Elements enter with staggered timing (0.3-0.5s apart), not all at once
- [ ] At any given moment, something on screen is either moving in, fading out, or pulsing
- [ ] Dialogue appears character-by-character or with a typing feel, not a full block
- [ ] Scene transitions are invisible — no blank screens, no hard cuts between cards
- [ ] Subtitle bar stays visible with smooth text crossfades
- [ ] Background has subtle motion (radial gradient pulse, slow light sweep)
- [ ] If a user previously called it "像PPT了", the above checklist was NOT met — redo
