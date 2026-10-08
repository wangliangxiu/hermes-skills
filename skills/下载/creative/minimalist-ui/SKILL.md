---
name: minimalist-ui
description: Clean editorial-style interfaces. Warm monochrome palette, typographic contrast, flat bento grids, muted pastels. No gradients, no heavy shadows.
---

# Protocol: Premium Utilitarian Minimalism UI Architect

## 1. Protocol Overview
Name: Premium Utilitarian Minimalism & Editorial UI
Description: An advanced frontend engineering directive for generating highly refined, ultra-minimalist, "document-style" web interfaces. Enforces high-contrast warm monochrome palette, bespoke typographic hierarchies, macro-whitespace, bento-grid layouts, and ultra-flat component architecture.

## 2. Absolute Negative Constraints (Banned Elements)
- DO NOT use "Inter", "Roboto", or "Open Sans" typefaces.
- DO NOT use thin-line icon libraries like "Lucide", "Feather", or standard "Heroicons".
- DO NOT use Tailwind's default heavy drop shadows (shadow-md/lg/xl).
- DO NOT use primary colored backgrounds for large elements or sections.
- DO NOT use gradients, neon colors, or 3D glassmorphism (beyond subtle navbar blurs).
- DO NOT use rounded-full for large containers, cards, or primary buttons.
- DO NOT use emojis in code, markup, or alt text. Replace with proper icons or clean SVG primitives.

## 3. Core Design Tokens

### 3.1 Color Palette: Warm Monochrome + Muted Pastels
- **Surface:** #fbf9f7 (warm white), #f5f2ed (soft stone), #ebe6de (warm gray)
- **Text:** #1a1a1a (near-black), #4a4543 (body), #8a8580 (muted)
- **Accent:** #dcb584 (warm gold), #b8a08e (warm taupe), #a8c5b6 (sage green)
- **Muted:** #e8e3dc (border), #d4cec6 (divider)
- **Alert:** #c44c3e (red, minimal use)

### 3.2 Typography
- **Display:** Space Grotesk, Cabinet Grotesk, or Satoshi (headings)
- **Body:** DM Sans, Plus Jakarta Sans, or Source Serif 4 (long-form)
- **Mono:** JetBrains Mono (code/data)
- Weights: Display 500-700, Body 400, Muted 400-500

### 3.3 Spacing System
Base unit: 8px. Margins/padding in multiples: 16, 24, 32, 48, 64, 96, 128.
Section gap: minimum 64px between major sections.

## 4. Layout Patterns

### 4.1 Bento Grid
- Asymmetric grid cells with deliberate size variance
- No equal-height cards in the same row (unless content demands it)
- Gap: 16-24px between cells
- Border-radius: 8-12px max

### 4.2 Hero Section
- Left-aligned headline (48-64px), right-aligned or offset visual
- No centered CTAs. CTA sits within text column, inline or below
- Subtitle: 18-20px, muted color, max 60ch

### 4.3 Content Sections
- Max text width: 65-72ch
- Section titles: 24-28px, regular weight, letter-spacing: -0.01em
- Body: 16-17px, 1.6-1.7 line-height

## 5. Component Styles

### 5.1 Buttons
- Flat, no shadow, border-radius: 6px
- Primary: text color bg (near-black on light, white on dark)
- Secondary: bordered (1px solid border color)
- Ghost: transparent, hover: subtle bg change

### 5.2 Cards
- Background: one step lighter than section bg
- No shadow. Border: 1px solid muted/border color (optional)
- Padding: 24-32px

### 5.3 Navigation
- Flat, transparent bg, left logo + right links
- Active state: small dot indicator or subtle weight change
- Mobile: hamburger with full-screen overlay

## 6. Imagery & Icons
- Icons: outlined, 1.5-2px stroke, rounded corners 1-2px
- No boxed icons (icons inside colored squares)
- Photography: warm-toned, desaturated, editorial style
- Illustrations: monochrome line art, same stroke weight as icons

## 7. Motion
- Subtle only. Fade-in on scroll, hover:opacity or slight y-offset
- Max duration: 200-300ms
- No parallax, no physics, no spring animations
