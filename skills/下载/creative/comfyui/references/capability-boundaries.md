# AI Video Generation — Capability Boundaries & Alternatives

What AI video tools can and cannot do, with pragmatic alternatives for
requests that exceed current limits. Use this when a user asks for a
video that's beyond what current tools can produce.

## Quick Assessment Matrix

| Requirement | AI Video (ComfyUI/Hunyuan/Wan) | Traditional Production |
|-------------|----------------------------------|------------------------|
| Short clip (5-30s), abstract/stylized | ✅ Excellent | ✅ Overkill |
| Single shot, simple scene | ✅ Good | ✅ Good |
| Multi-actor narrative with consistent characters | ❌ No (no character persistence) | ✅ Yes |
| Spoken dialogue between specific characters | ❌ No (no voice-lip sync for custom characters) | ✅ Yes |
| 4K resolution | ⚠️ Up to 1080p typically; 4K possible via upscalers | ✅ Standard |
| Professional narration + synchronized subtitles | ❌ No built-in support | ✅ Yes |
| Smooth dolly/pan/zoom multi-shot sequence | ❌ Shots are independent, no shot-to-shot continuity | ✅ Yes |
| Realistic human actors with consistent appearance | ❌ AI-generated humans vary per frame; "face drift" | ✅ Yes (real people) |
| Multiple scenes, locations, lighting setups | ❌ Each scene is a separate generation | ✅ Seamless transitions |
| Brand-safe / compliant content | ⚠️ AI may add unwanted artifacts; no strict control | ✅ Full control |
| Long-form (3+ minutes) | ❌ Max ~30s per generation | ✅ Standard |

## Common High-End Request Types

### 1. "4K promotional / documentary-style video"
**User thinks:** "AI can make videos now, so it can make my company's promotional video."
**Reality:** AI generates short abstract/stylized clips. Multi-shot narrative
with consistent characters, locations, and voiceover is not possible.

**Best alternative:** Hire a local video production team. AI can assist with:
- Background B-roll generation (nature footage, establishing shots)
- Mood board / visual reference generation
- Storyboard creation via image gen
- Draft script and narration text generation

### 2. "Animated explainer with consistent characters"
**User thinks:** "AI animation tools can make my tutorial video with a recurring mascot."
**Reality:** Tools like AnimateDiff can do short loops with the same character,
but cannot maintain identity across different scenes and poses.

**Best alternative:** Use Manim (code-driven animations) for abstract
explanations, or traditional 2D animation tools (After Effects, Blender).

### 3. "Movie / short film with dialogue and plot"
**User thinks:** "Sora/Runway can make videos, so I can make a short film."
**Reality:** Current AI video is best at single-shot vibe clips. No dialogue
control, no plot consistency, no coherent multi-scene narrative.

**Best alternative:** Traditional filmmaking pipelines. AI can assist with
VFX, style transfer, and post-production augmentation.

## When to Offer AI Video

AI video tools (ComfyUI with AnimateDiff/Wan/HunyuanVideo) are genuinely
good for:

- **Background footage / B-roll:** Cityscapes, nature, abstract textures,
  establishing shots — things where consistent character identity doesn't matter
- **Concept visualization:** "Show me what this scene would look like" —
  quick visual exploration
- **Social media clips:** Short (5-15s) stylized LoRA-driven clips for
  TikTok/Reels/Shorts
- **Music visualizers:** Abstract or atmospheric video synced to music
- **Product showcase:** Short rotating / orbiting shots of objects
- **Transitions / intro sequences:** Short atmospheric clips used as
  section headers in longer productions

## Alternative Recommendation Framework

When a user requests a video, use this decision tree:

```
User wants a video
├── Short (<30s), stylized, no dialogue → AI video (ComfyUI/AnimateDiff/Hunyuan)
├── Short, abstract, code-driven → Manim (math/animation)
├── Short, web-based, HTML/CSS → Remotion or HyperFrames
├── Long-form, realistic, narrative → Professional production (hire a team)
├── Slideshow-style with voiceover → PowerPoint/Keynote with narration export
├── Animated explainer (consistent character) → Traditional animation tools
└── Combination (AI clips + editing) → AI for B-roll + human editing in Premiere/DaVinci
```

## What to Say to the User

Template for declining a request that exceeds AI video capabilities:

> "I appreciate the detailed vision. Unfortunately, current AI video tools
> can't handle [specific limitation: character consistency / dialogue /
> multi-shot continuity / 4K resolution]. They're best for short (5-30s)
> stylized clips without narrative continuity.
>
> For your project, the most practical approach would be:
> 1. **[Best option]** — [e.g., Hire a local video production team]
> 2. **[AI-assisted option]** — [e.g., Use AI for B-roll + human editing]
> 3. **[DIY option]** — [e.g., PowerPoint with narration, exported as video]
>
> Would you like me to help with any of these approaches?"
