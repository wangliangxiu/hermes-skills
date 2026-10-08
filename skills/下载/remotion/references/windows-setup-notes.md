# Remotion on Windows — Setup Notes

## Project creation (non-interactive)

On Windows, `npx create-video@latest` may stall at the interactive template picker (arrow keys don't work in non-PTY environments). Workaround: **manually create the project structure** instead.

```bash
# Instead of:
npx create-video@latest --yes --template blank my-video

# Do this:
mkdir D:/Projects/my-video
cd D:/Projects/my-video
npm init -y
npm install react react-dom remotion @remotion/cli @remotion/renderer
npm install --save-dev typescript @types/react
```

Then manually create:
- `tsconfig.json`
- `src/index.ts` — `registerRoot`
- `src/Root.tsx` — `Composition` definition
- `src/ZhengWuVideo.tsx` — main video component
- `src/scenes/` — scene components
- `src/components/` — reusable components

## Chrome / browser requirement

Remotion Studio (`npx remotion studio`) and rendering both require Chrome or Chromium. If not found:
- Local rendering falls back to checking `CHROME_PATH` env var, then default install locations
- On headless/CI environments, Remotion auto-downloads Chromium during `npm install`

## Rendering checklist

```bash
# 1. Check if Chrome is available
npx remotion browser ensure

# 2. Studio preview (requires GUI browser)
npx remotion studio

# 3. Render (may fail without Chrome — see above)
npx remotion render <composition-id> out/final.mp4
```

## Install to non-C drive

On systems where C: space is limited:

```bash
# Set npm cache to D:
npm config set cache D:/npm-cache

# Or per-project:
npm install --cache D:/npm-cache
```

The project itself lives on D: drive. All node_modules and cache are D:-local.
