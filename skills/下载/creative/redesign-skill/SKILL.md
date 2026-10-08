---
name: redesign-skill
description: Systematic approach to redesigning existing interfaces. Audit-first methodology, preserve what works, fix what doesn't.
---

# Protocol: Redesign Methodology

## Philosophy
A redesign is not a rebuild. Start by understanding what exists, preserve what works, and fix what doesn't. Every change must have a rationale.

## 1. Audit Phase (Required Before Any Design Work)

### 1.1 Load and analyze the existing page
1. Open the current site/app.
2. Identify the page type and user goal.
3. Take note of the existing brand assets (logo, colors, typography).

### 1.2 Audit checklist
- **Layout**: is information hierarchy clear? Is there wasted space or cramped content?
- **Typography**: is it readable? Are heading sizes consistent? Font choice appropriate?
- **Color**: does the palette feel cohesive? Are there accessibility issues?
- **Spacing**: is whitespace intentional or accidental?
- **Motion**: does it serve a purpose or is it decorative?
- **Responsive**: does it break at any viewport?
- **Consistency**: are buttons, inputs, cards consistent across the page?

### 1.3 Document 3 things to fix
Write down exactly 3 violations. These become the redesign brief.

## 2. Preserve Phase

### 2.1 What to keep
- Brand colors (unless they're actively harming readability)
- Logo placement and navigation pattern (unless broken)
- Core content structure that users expect

### 2.2 What to change
- Layout density and hierarchy
- Typography system (weights, sizes, pairing)
- Spacing and rhythm
- Component consistency
- Motion quality

## 3. Execute Phase

### 3.1 Apply the appropriate aesthetic skill
- If the brand is premium/minimal → use minimalist-ui
- If the brand wants raw/unpolished → use brutalist-ui
- If the brand needs warm/friendly → use soft-ui
- Default → use taste-skill (Three Dials approach)

### 3.2 Changes must be justified
Every change needs a one-line rationale. 
Bad: "Changed the button color."
Good: "Changed button color to increase contrast from 3.2:1 to 5.1:1 for WCAG AA compliance."

## 4. Output

### 4.1 Deliverables
1. Redesigned HTML/CSS page
2. Brief changelog: what changed and why

### 4.2 Quality gates
- Same or better accessibility score
- No broken layouts at 375px, 768px, 1024px, 1440px
- Load time not regressed
- Brand identity preserved (not replaced)
