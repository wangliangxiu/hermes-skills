# Animation Storyboard Method (for AI-prompted video)

## When to use this

When the user wants to create a **narrative animation** (3+ minute story) from AI-generated images — not editing real footage, but planning shot-by-shot imagery for an external image/video generator (WorkBuddy, Midjourney, Runway, etc.).

## Core narrative pattern: "Pass-through" transitions

The most effective device for timeline/travel stories: **the camera passes through a door, window, or frame to enter the next era**.

The "frame within a frame" device works because:
- The frame briefly fills the screen → natural cut point
- Emerging on the other side = new scene established instantly
- No hard cuts or color fades needed — the pass-through IS the transition
- Works for any transportation/history/city-evolution narrative

## Fixed camera rules

- **Perspective:** low angle, eye-level, perpendicular to travel direction. NOT overhead/aerial.
- The viewer is "standing beside the track" watching the journey pass by.
- Consistent perspective across all shots — this is the binding device.
- The composition is always: vehicle (crossing frame horizontally) + background (skyline/landscape).

## Three-act structure (proven pattern)

This was validated with a Jiaozuo railway animation storyboard (~57s, 17 shots, 3 transitions):

### Act 1 — 1902 (earliest era, industrial/raw)

```
[Steam locomotive → Coal wagon① (full mound) → Coal wagon② (half) → Coal wagon③ (empty)]
```

**Period detail:** Pre-1970 freight trains had NO passenger windows. Use open side-doors on freight wagons as the transition portal.

**Visual sequence:**
1. Wide establishing shot: steam locomotive emerging from morning mist
2. Pan right: three coal wagons with doors open, coal decreasing: full → half → empty
3. Sunlight shines through the empty wagon, illuminating coal-dust residue on the floor

**Transition:** Camera passes through the empty wagon's open side-door. Door frame fills screen → opens into Act 2.

### Act 2 — 1970/80s (middle era, passenger trains, changing city)

```
[Green train (绿皮车) crossing the frame + old city skyline in background]
```

**After transition:** Same low-angle ground-level perspective. Green train visible below. Background: brick buildings, factory chimneys, hazy sky.

**Zoom and focus sequence:**
1. Camera slowly zooms toward one window of the green train
2. Reveals a young girl at the window — chin on folded arms, looking outward
3. While still zooming, focus shifts to **another window behind the girl** (further along the train)
4. This creates a "push-through" feeling without moving the camera

**Transition:** Camera passes through that second window. Window frame fills screen → opens into Act 3.

### Act 3 — 2000+ (modern era)

```
[Modern train (AC/high-speed) crossing the frame + modern city skyline]
```

Same low-angle perspective, new vehicle and background. Repeat the pass-through pattern for additional acts.

### Optional: Closing sequence

Instead of another pass-through, end with:

1. Zoom to a close-up of the modern vehicle's side
2. A floating object enters frame (old ticket, letter, photograph) — drifting like a leaf
3. Object slowly fills the screen, becoming the final image
4. The object carries the ending message: a modified train ticket where the "destination" field reads as a timeline endpoint, and the "date" field reads as the city name

This creates an emotional, reflective ending without requiring another transition.

## Content accuracy rules for Chinese railway/city narratives

- 🚫 **DO NOT include Yueshan Station (月山站) in AI-generated images** — it's in a remote mountain area outside the city. May appear in text captions but NOT in visual prompts.
- 🚫 **DO NOT use specific building names** (Wanda, specific malls/towers) unless the user provided them.
- ✅ **Railway is the protagonist, city atmosphere is the background** — the narrative is about how railway development changed the city's character, not about specific landmarks.
- ✅ **1902 steam trains carried coal, not passengers** — historically accurate: no passenger windows on freight trains.

## Visual density across shots

To convey the passage of time through visual density alone:

| Era | Visual density | Atmosphere |
|:---|:---------------|:-----------|
| Earliest | Low (open landscape, few buildings) | Misty, sepia, muted |
| Middle | Medium (factories, brick buildings appearing) | Warmer, industrial haze |
| Modern | High (dense skyline, clean streets) | Clear, bright, blue sky |

Each era should be a distinct color key — the transition carries the color from the previous era into the next via the frame-fill moment.

## Detailed prompt structure (for external AI image generator)

Each prompt must include ALL of these sections:

### 1. Perspective / Framing
- "低角度平视" (low angle, eye-level)
- Camera position relative to subject (e.g. "站在铁路旁看列车驶过")

### 2. Three-layer composition
- **近景 (Foreground):** what's closest to camera
- **中景 (Midground):** the main subject
- **远景 (Background):** environment, sky, city silhouette

### 3. Specific color / tone
- "色调：棕褐色系"
- "暖橙＋淡紫晚霞"
- "军绿＋灰黄＋暖棕"

### 4. Light source
- "晨雾中" / "黄昏斜阳" / "蓝天白云下"
- Direction of light and its effect

### 5. Style directive
- For narrative: "手绘插画/绘本风，不追求写实"
- This is recommended over photorealistic — AI image generators struggle with era-accurate details, and cartoon style forgives inaccuracies

### 6. Aspect ratio
- 3:4 for portrait vertical
- 16:9 for landscape/cinematic
- For single-shot video frames, match the target video aspect ratio

## File conventions

- Save completed storyboard to Desktop as `{主题}_动画分镜.txt`
- Save detailed image prompts to Desktop as `{主题}_提示词.txt`
- Transition-only edits: `{主题}_过渡修改.txt`
- Version increment: `{主题}_动画分镜v2.txt`
