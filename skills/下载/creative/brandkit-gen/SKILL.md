---
name: brandkit-gen
description: Generate brand identity guidelines — color palette, typography system, logo usage, tone of voice, and application examples.
---

# Protocol: Brand Kit Generation

## Philosophy
A brand kit ensures every design touchpoint feels like it belongs to the same family. Generate a cohesive system, not a collection of unrelated assets.

## 1. Brief Inference

Collect or infer:
1. **Industry** — tech, fashion, food, education, healthcare, etc.
2. **Vibe** — premium, playful, serious, warm, edgy, trustworthy
3. **Audience** — consumer, enterprise, children, designers, executives
4. **Competitors** — 2-3 reference brands

## 2. Color System

### 2.1 Palette structure (5 colors max)
- **Primary** (1): main brand color. Use for CTAs, links, key accents.
- **Secondary** (1): supporting color. Use for secondary actions, highlights.
- **Surface** (1): background color. White, off-white, or dark.
- **Text** (1): primary text color. High contrast on surface.
- **Muted** (1): secondary text, borders, dividers.

### 2.2 Each color needs
- Hex value
- Usage description (e.g. "Primary CTAs, active states")
- At least one accessible pairing (text on bg, minimum 4.5:1)

## 3. Typography System

### 3.1 Font pairing (max 2)
- **Display** (headings): personality font. Use at 32px+ only.
- **Body** (paragraphs, labels): highly readable. Use at 14-18px.

### 3.2 Scale
- H1: 48-64px / H2: 32-40px / H3: 24-28px / Body: 16-18px / Small: 13-14px

## 4. Logo & Iconography

### 4.1 Logo guidelines
- Minimum clear space: height of the logo mark
- Do not: recolor, stretch, add effects, place on low-contrast bg
- Provide: full logo, icon-only, horizontal, vertical

### 4.2 Icon style
- Outlined vs filled, stroke weight, corner radius
- Consistency is everything — all icons share the same visual properties

## 5. Tone of Voice

- **Personality** — 3 adjectives describing the brand voice
- **Do** — example phrases and language patterns
- **Don't** — language to avoid
- **Audience** — how the tone shifts for different segments

## 6. Application Examples

Show the system applied to:
1. A landing page hero section
2. A card / content component
3. A button + form input
4. A navigation bar

## 7. Output

Generate as a single HTML page (brand guide) or SKILL.md for agent consumption.
