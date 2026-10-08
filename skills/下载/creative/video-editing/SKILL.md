---
name: video-editing
description: AI-assisted video editing workflows for cutting, structuring, and augmenting real footage. Covers the full pipeline from raw capture through FFmpeg, Remotion, ElevenLabs, fal.ai, and final polish in Descript or CapCut. Use when the user wants to edit video, cut footage, create vlogs, or build video content.
---

# Video Editing

AI-assisted editing for real footage. Not generation from prompts. Editing existing video fast.

## When to Activate
- User wants to trim, cut, merge, or split video files
- User wants to add subtitles, captions, or转录
- User wants to extract audio or frames from video
- User wants to compress, transcode, or convert format
- User wants to create a vlog, montage, or compilation
- User has raw footage and wants a structured edit

## Tool Chain

### 1. FFmpeg (core tool)
Used for all mechanical operations: trim, cut, merge, transcode, extract audio, extract frames, resize, compress, add subtitles.

Key commands:
```bash
# Trim video (keep between 00:01:00 and 00:02:30)
ffmpeg -i input.mp4 -ss 00:01:00 -to 00:02:30 -c copy output.mp4

# Merge multiple videos (create filelist.txt first)
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4

# Extract audio
ffmpeg -i input.mp4 -q:a 0 -map a output.mp3

# Extract frames (1 per second)
ffmpeg -i input.mp4 -vf fps=1 frames/frame_%04d.png

# Add subtitles (burn in)
ffmpeg -i input.mp4 -vf subtitles=subtitles.srt output.mp4

# Compress for web
ffmpeg -i input.mp4 -vcodec libx264 -crf 28 -preset fast output.mp4
```

### 2. Remotion (programmatic video)
Use when the user wants data-driven, template-based, or programmatic video creation. React components rendered to video frames. Good for:
- Dynamic text overlays on footage
- Data visualizations as video
- Template-based social media clips
- Slideshow-style videos

### 3. ElevenLabs (voiceover / narration)
- Generate voiceover from script
- Clone voice from sample
- Add narration to silent footage

### 4. fal.ai (video models)
- Runway Gen-3, Kling, or other video models
- Extend footage, generate B-roll, create transitions

### 5. Descript / CapCut (final polish)
For the final pass: color grade, audio cleanup, transitions, effects. These are GUI tools — guide the user on what to do in them rather than trying to automate.

## Workflow

### Quick Edit (under 5 min)
1. Trim start/end → 2. Cut middle sections → 3. Add crossfade → 4. Export

### Vlog / Talking Head
1. Raw capture → 2. Remove silence/pauses → 3. Add intro/outro → 4. Add captions → 5. Color grade → 6. Export

### Montage / Compilation
1. Gather clips → 2. Trim each → 3. Merge → 4. Add transitions → 5. Add background music → 6. Add title cards → 7. Export

## Narrative Animation Storyboard (for AI-generated video)

When creating an animated story from AI-generated images (not real footage), use the storyboard technique documented in `references/animation-storyboard-method.md`. This covers:

- **Three-act symmetrical structure** with "pass-through" transitions (穿过车门/车窗 as portal device)
- **Fixed camera perspective rules** — low-angle ground-level, perpendicular to train/travel direction
- **Era-accurate vehicle detailing** — e.g. pre-1970 freight trains had NO passenger windows
- **Transition page design** between eras using color gradients and directional elements
- **Closing device** — a floating object (ticket, letter, photo) drifting into frame to signal the ending

This is the AI-prompt workflow: agent writes the storyboard → agent writes detailed image prompts → user generates images externally (WorkBuddy, Midjourney, etc.) → agent assembles into video or long-image.

## Quality Checklist
- [ ] Audio levels: -14 LUFS (spoken word) or -9 LUFS (music-heavy)
- [ ] No clipped audio peaks
- [ ] Captions: readable font, 2.5s minimum for full line, sync checked
- [ ] Export: H.264, 1080p, 30fps for web; ProRes 422 for further editing
- [ ] File naming: project-name_yyyymmdd_v1.mp4

## Safety Notes
- Always keep original footage untouched. Work on copies.
- Use lossless cuts (`-c copy`) when possible to avoid re-encoding.
- FFmpeg with `-c copy` is instantaneous; re-encoding takes time proportional to video length.
