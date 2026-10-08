---
name: taste-skill
description: Anti-slop frontend skill for landing pages, portfolios, and redesigns. The agent reads the brief, infers the right design direction, and ships interfaces that do not look templated. Real design systems when applicable, audit-first on redesigns, strict pre-flight check.
---

# tasteskill: Anti-Slop Frontend Skill

> Landing pages, portfolios, and redesigns. Not dashboards, not data tables, not multi-step product UI.
> Every rule below is **contextual**. None of it fires automatically. First read the brief, then pull only what fits.

---

## 0. BRIEF INFERENCE (Read the Room Before Anything Else)

Before touching code or tweaking dials, **infer what the user actually wants**. Most LLM design output is bad because the model jumps to a default aesthetic instead of reading the room.

### 0.A Read these signals first
1. **Page kind** - landing (SaaS / consumer / agency / event), portfolio (dev / designer / creative studio), redesign (preserve vs overhaul), editorial / blog.
2. **Vibe words** the user used - "minimalist", "calm", "Linear-style", "Awwwards", "brutalist", "premium consumer", "Apple-y", "playful", "serious B2B", "editorial", "agency-y", "glassy", "dark tech".
3. **Reference signals** - URLs they linked, screenshots they pasted, products they named, brands they're competing with.
4. **Audience** - B2B procurement panel vs. design-conscious consumer vs. recruiter scanning a portfolio. The audience picks the aesthetic, not your taste.
5. **Brand assets that already exist** - logo, color, type, photography. For redesigns, these are starting material, not optional input (see Section 11).
6. **Quiet constraints** - accessibility-first audiences, public-sector, regulated industries, trust-first commerce, kids' products. These constraints OVERRIDE aesthetic preference.

### 0.B Output a one-line "Design Read" before generating
Before any code, state in one line: **"Reading this as: <page kind> for <audience>, with a <vibe> language, leaning toward <design system or aesthetic family>."**

Example reads:
- *"Reading this as: B2B SaaS landing for technical buyers, with a Linear-style minimalist language, leaning toward Tailwind utilities + Geist + restrained motion."*
- *"Reading this as: solo designer portfolio for hiring managers, with an editorial / kinetic-type language, leaning toward native CSS + scroll-driven animation + custom typography."*
- *"Reading this as: redesign of a public-sector service site, with a trust-first language, leaning toward GOV.UK Frontend or USWDS."*

### 0.C If the brief is ambiguous, ask one question, do not guess
Ask exactly **one** clarifying question - never a multi-question dump - and only when the design read genuinely diverges.

### 0.D Anti-Default Discipline
Do not default to: AI-purple gradients, centered hero over dark mesh, three equal feature cards, generic glassmorphism on everything, infinite-loop micro-animations everywhere, Inter + slate-900.

---

## 1. THE THREE DIALS (Core Configuration)

After the design read, set three dials:

- **`DESIGN_VARIANCE: 8`** - 1 = Perfect Symmetry, 10 = Artsy Chaos
- **`MOTION_INTENSITY: 6`** - 1 = Static, 10 = Cinematic / Physics
- **`VISUAL_DENSITY: 4`** - 1 = Art Gallery / Airy, 10 = Cockpit / Packed Data

---

## 2. LAYOUT RULES (Gated by DIALS)

### 2.A Visual Density dictates breakpoint behavior
- DENSITY 1-3: generous whitespace, max 60-65ch text width, single-column below 1024px
- DENSITY 4-6: balanced, 70-80ch text width, two-column below 768px
- DENSITY 7-10: compact, 90ch+, multi-column down to 480px

### 2.B Variance dictates symmetry breaking
- VARIANCE 1-3: strict alignment, single-axis layouts, predictable grid
- VARIANCE 4-7: staggered grids, asymmetric hero, intentional overflow
- VARIANCE 8-10: overlapping elements, diagonal splits, broken grid, collage

### 2.C Density + Variance compose
High Variance + Low Density = editorial magazine layouts.
Low Variance + High Density = cockpit dashboards.

### 2.D Never do these by default
- Three identical feature cards in a row
- Centered hero with one headline + one CTA + one mockup below
- Full-width image row with text overlay (unless the brief actually calls for it)

---

## 3. TYPOGRAPHY & COLOR

### 3.A Font pairing rules
- One display, one body. Never three.
- Display: only for hero headings (48px+), section headings use body weight.
- Body: 16-18px for desktop, 15-17px mobile. Line height: 1.5-1.7.
- Avoid Inter as default. Reach for: Instrument Sans, Satoshi, Cabinet Grotesk, Space Grotesk, DM Sans, Geist, Plus Jakarta Sans, Degular, Sohne.

### 3.B Color discipline
- One accent. One surface. One text. One muted. (Neutrals are not accents.)
- Maximum 5 colors total, including black and white.
- Reds and greens WITHOUT luminosity contrast of 3.5+: add a tint/shade variant for accessibility.
- No AI-purple gradients unless the brief mentions it.

### 3.C Contrast requirements
- Body text on bg: minimum 5:1.
- Small text (under 18px bold / 14px regular): minimum 4.5:1.
- Decorative text (overlined, muted, captions): minimum 3:1.
- Interactive elements (focus rings, input borders, pressed states): minimum 3:1 against adjacent colors.

---

## 4. MOTION RULES (Gated by MOTION_INTENSITY dial)

### 4.A Intensity bands
- INTENSITY 1-3: zero motion. Everything static. Transitions are instant. No hover effects that change layout.
- INTENSITY 4-6: hover scale/opacity on interactive elements. Staggered fade-in on scroll. Max 200ms transforms.
- INTENSITY 7-10: cinematic entrance. Parallax, physics-based spring animations, scroll-driven timelines, SVG path reveals. Motion must serve narrative.

### 4.B Motion must serve a purpose
Never: sparkle trails on every hover, auto-rotating carousels, confetti on page load, loading animations for content under 1KB. Motion should direct attention, not distract.

### 4.C Respect reduced motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 5. IMAGE & ASSET DISCIPLINE

### 5.A Image quality baseline
- No stretched/photoshopped-looking imagery.
- Aspect ratio must be deliberate, not accidental.
- Hero images: minimum 1440px wide, properly compressed.
- Favicon: generate one. Don't leave the default Vite/Next.js icon.

### 5.B No fake dashboard screenshots
No mockups of "analytics dashboards," "real-time data widgets," or "user growth charts" in marketing pages. Replace with abstract geometric patterns, product photography, or real interfaces.

### 5.C Illustration style
All illustrations should share the same line weight, corner radius, color palette, and level of detail. No mixing flat icons with detailed 3D renders.

---

## 6. RESPONSIVE BASELINE

- Mobile-first: build for 375px, adjust for 768px, 1024px, 1440px.
- No horizontal scroll at any breakpoint.
- Touch targets: minimum 44x44px.
- Forms: native input styles, no custom-styled selects that break on mobile.

---

## 7. MICRO-INTERACTIONS & DETAIL

### 7.A State coverage
Every interactive element needs: default, hover, focus-visible, active, disabled. Focus-visible must be visibly different from hover (a focus ring that merely changes color is insufficient).

### 7.B Loading states
Content should never appear from nothing. Use skeleton screens for data, opacity transitions for static content. No spinners. No "Loading..." text.

---

## 8. STACK & TOOL CHOICE

- **No Tailwind required.** Plain CSS, CSS modules, styled-components, or vanilla extract are valid.
- **No heavy animation libraries** unless INTENSITY >= 7.
- **Accessibility**: semantic HTML, proper heading hierarchy, alt text on every image, aria labels on interactive controls.
- **Performance**: no layout shifts on load (CLS < 0.1). LCP under 2.5s.
- **If you generate an HTML file**: it should be a single self-contained .html with inline styles.

---

## 9. IMPORTING DESIGN SYSTEMS

Check if the brief maps to an existing system from the popular-web-designs catalog. If it does, load the template and use its tokens. If it doesn't, build custom from the Three Dials.

---

## 10. PRE-FLIGHT CHECK (Before calling the output done)

1. Are any colors below 4.5:1 for body text? Fix.
2. Is there focus-visible styling on interactive elements? Add.
3. Is there any horizontal scroll at 375px? Eliminate.
4. Is there a skill or library already imported that covers some of these rules? Check.
5. Does the page use Inter as default without a reason? Replace.
6. Are there three equal feature cards? Break them.
7. Is the hero centered with headline + CTA + mockup? Break it.
8. Is there reduced-motion CSS? Add it.

---

## 11. REDESIGN MODE

When the task is a **redesign** (user has an existing site and wants it improved):

1. **Audit first**: load the existing page. Identify 3 things that violate this skill's rules.
2. **Preserve**: brand colors, logo placement, core navigation pattern - unless they're broken.
3. **Improve**: apply this skill's rules to fix what's broken.
4. **Document**: state what you changed and why.
