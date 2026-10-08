---
name: taptap-maker
description: "Develop, build, and debug TapTap Maker mobile games (合成大西瓜, etc.) — project init, MCP interaction, cloud builds on Windows, runtime debugging."
version: 1.5.0
author: Hermes Agent
platforms: [windows]
metadata:
  hermes:
    tags: [taptap, maker, mobile-games, lua, mcp]
    related_skills: [native-mcp, windows-software-install]
---

# TapTap Maker Game Development

TapTap Maker is a mobile game development platform where games are written in Lua using UrhoX engine (Box2D physics, NanoVG UI, 2D sprites). Projects are managed via `npx -y @taptap/maker` CLI and an MCP server.

## When to Use

Use this skill whenever you need to:
- Init a new TapTap Maker project
- Write game code (Lua) for Maker games
- Trigger cloud builds via MCP
- Debug build failures or runtime issues (no visual rendering, physics not working)
- Read and understand Maker project structure

## Project Structure

```
项目根目录/
├── scripts/main.lua          # 入口脚本（游戏代码放这里）
├── assets/                   # 图片/音频/模型资源
├── templates/                # 脚手架模板（如 scaffold-2d-physics.lua）
├── examples/                 # 官方示例
├── urhox-libs/               # UI 等高层库
├── engine-docs/              # 引擎文档
├── .emmylua/                 # 引擎 API 类型定义
├── .maker-mcp/config.json    # MCP 项目配置（project_id, user_id）
├── AGENTS.md                 # AI 编码规则（必须遵守！）
└── .maker/logs/runtime/      # 运行时日志（watcher）
```

## Common Task: Trigger a Cloud Build

### Prerequisites
- Project is initialized with `taptap-maker init`
- Code is committed locally
- `mcp_servers.tapmaker` is configured in Hermes config.yaml with `cwd` pointing to project root

### Method 1: Via Hermes MCP Client (if tools are registered)

If `hermes mcp list` shows `tapmaker ✓ enabled` and the MCP tools are registered as Hermes tools, just call the tool directly. Tool names follow the pattern `mcp_tapmaker_maker_build_current_directory`.

### Method 2: Use the build script (recommended for CLI sessions)

Use `scripts/trigger-build.py` — a self-contained Python script that handles MCP initialization, subst drive mapping for Chinese paths, and waits for the build result:

```python
from hermes_tools import terminal
result = terminal("python scripts/trigger-build.py 'C:/Users/User/Desktop/项目路径'")
# result["output"] contains the build result with maker_url
```

Or call from a terminal:
```bash
python /c/Users/.../hermes/skills/gaming/taptap-maker/scripts/trigger-build.py "project_dir"
```

The script:
1. Creates `subst S:` drive mapping if the path has Chinese characters
2. Starts `npx.cmd -y @taptap/maker` as MCP server
3. Sends initialize handshake + tool call
4. Waits and parses the JSON-RPC response
5. Returns the build result with `maker_url`

**Manual fallback (if script doesn't work):** See the `native-mcp` skill's "Manual MCP Protocol Interaction" section.

**Available MCP tools (from `maker_status_lite` / `maker_build_current_directory`):**
- `maker_status_lite` — diagnostic status (git, Python, Lua LSP, auth, build availability)
- `maker_build_current_directory` — commit + push + trigger remote cloud build

### Build Result

A successful build returns a result containing:
```
✓ Maker project submitted, then remote Maker build finished
- project_id: ...
- maker_url: https://maker.taptap.cn/app/{project_id}?localDev=1
- elapsed_ms: ...
- last_progress: [remote_build] 100% 构建流程全部完成
```

The build automatically starts a runtime log watcher (`taptap-maker logs watch`) that polls every 5s.

## Common Bug: No Visual Rendering for Physics Objects

**Symptom**: Game loads, physics walls work, but clicking does nothing visually. Fruits are actually being created and falling — they just have no renderable graphics.

**Root cause**: `CreateFruit()` only creates `RigidBody2D` + `CollisionCircle2D` (physics), but has NO visual component.

See `references/suika-no-visual-debug.md` for the full debugging walkthrough.

### Fix Option 1 (Deprecated): StaticSprite2D

**This is unreliable on TapTap's cloud build — `Urho2D/Box.png` may not exist in the remote resource pack, causing a silent failure.** Prefer Option 2 (NanoVG).

```lua
local sprite = node:CreateComponent("StaticSprite2D")
sprite.sprite = cache:GetResource("Sprite2D", "Urho2D/Box.png")
```

### ⚠️ Fix Option 2 (Partial — Remote Cloud Build): Independent NVG Context + NanoVGRender Event

**This is the only approach confirmed to render custom NanoVG DRAWING in TapTap Maker's remote cloud build environment as of 2026-07.** `UI.QueueOverlay` (Option 3) silently does nothing on the remote build — callbacks queue but never execute.

⚠️ **Known limitation as of 2026-07-09: Text/emoji rendering via nvgText() does NOT work in the independent NVG context on remote builds.** Geometry (circles, rects) renders fine, but all nvgText() calls produce nothing — even ASCII at fixed screen coordinates. Font is loaded via `nvgCreateFont(nvg_, "sans", "Fonts/MiSans-Regular.ttf")` but text doesn't appear. Root cause unknown — may be a remote-build NVG implementation that strips text rendering, or a font-path issue. **For now, use geometry (circles/rects) instead of text in independent NVG context on remote builds.**

**Key principle:** Create a **separate** NVG context in `Start()`, subscribe its `NanoVGRender` event, and **manually** call `nvgBeginFrame`/`nvgEndFrame` inside the callback. This creates an independent render pass.

```lua
-- In global scope:
local nvg_ = nil

function Start()
    -- Create independent NVG context (NOT managed by UI system)
    nvg_ = nvgCreate(1)
    
    -- Continue with normal setup...
    UI.Init({ ... })
    -- ... scene, camera, UI widgets ...
    
    -- Subscribe to the independent NVG context's render event
    SubscribeToEvent(nvg_, "NanoVGRender", "HandleNanoVGRender")
end

function Stop()
    -- Clean up
    if nvg_ then nvgDelete(nvg_); nvg_ = nil end
    UI.Shutdown()
end

-- NanoVGRender callback — manually manage frame lifecycle
function HandleNanoVGRender(eventType, eventData)
    local vpW = graphics:GetWidth()
    local vpH = graphics:GetHeight()
    local dpr = graphics:GetDPR()
    local lw = vpW / dpr  -- logical width
    local lh = vpH / dpr  -- logical height
    
    -- MUST call nvgBeginFrame / nvgEndFrame manually
    nvgBeginFrame(nvg_, lw, lh, dpr)
    
    -- World-to-screen conversion for orthographic camera
    local ortho = CONFIG.BoxHeight + 2.0  -- camera.orthoSize
    local cx = CONFIG.BoxWidth / 2       -- camera X
    local cy = CONFIG.BoxHeight / 2      -- camera Y
    local scale = lh / ortho
    
    for _, node in ipairs(fruits) do
        local pos = node.position2D
        local sx = (pos.x - cx) * scale + lw / 2
        local sy = lh - ((pos.y - cy) * scale + lh / 2)
        local sr = radius * scale
        
        nvgBeginPath(nvg_)
        nvgCircle(nvg_, sx, sy, sr)
        nvgFillColor(nvg_, nvgRGBA(r255, g255, b255, 220))
        nvgFill(nvg_)
    end
    
    nvgEndFrame(nvg_)
end
```

**⚠️ NanoVG color values**: `nvgRGBA(r, g, b, a)` expects **0-255 integers**, not 0-1 floats. Convert:
```lua
nvgFillColor(nvg, nvgRGBA(
    math.floor(color[1] * 255),
    math.floor(color[2] * 255),
    math.floor(color[3] * 255),
    220
))
```

**⚠️ Text/emoji NOT available**: As of 2026-07-09, `nvgText()` does not render on remote builds even with font loaded. Use geometry (circles, rects, gradients) for all visual elements. For UI text that must appear, use UI.Label widgets (they render fine) rather than NVG text calls.

See `references/suika-no-visual-debug.md` for full diagnostic walkthrough and the layered test approach used to isolate these issues.

### Fix Option 3 (Deprecated — does NOT work on remote build): UI.QueueOverlay

**⚠️ Confirmed non-functional on remote cloud build as of 2026-07.** UI system's own widgets (labels, panels) render fine, but custom NVG drawing queued via `UI.QueueOverlay` silently produces nothing.

```lua
-- This WILL NOT render on remote build:
UI.QueueOverlay(function(nvg)
    nvgBeginPath(nvg)
    nvgCircle(nvg, 200, 300, 60)
    nvgFillColor(nvg, nvgRGBA(255, 0, 0, 200))
    nvgFill(nvg)
end)
```

**Use Option 2 (independent NVG context) instead for all remote build scenarios.**

### Diagnostic Techniques

1. **Confirm code execution via runtime logs.** Add `print()` statements and check `.maker/logs/runtime/runtime.log` (via watcher).
2. **Test with a fixed-position primitive** (e.g. red circle at `lw/2, lh/2`) before adding world-coordinate logic.
3. **If UI widgets render but QueueOverlay does not** → switch to independent NVG context (Option 2).

## Suika (合成大西瓜) Game-Specific Pitfalls

### ⚠️ FRUIT_TYPES must have `emoji` field

When generating a Suika-style game, the FRUIT_TYPES table definition must include an `emoji` field if the render code references `fd.emoji`:

```lua
-- ✅ CORRECT: emoji field present
local FRUIT_TYPES = {
    { name = "葡萄", radius = 0.3,  color = { 0.4, 0.2, 0.8 }, score = 1,  emoji = "🍇" },
    { name = "樱桃", radius = 0.38, color = { 0.9, 0.1, 0.1 }, score = 2,  emoji = "🍒" },
    { name = "橘子", radius = 0.48, color = { 1.0, 0.6, 0.0 }, score = 4,  emoji = "🍊" },
    { name = "柠檬", radius = 0.55, color = { 1.0, 0.9, 0.2 }, score = 8,  emoji = "🍋" },
    { name = "猕猴桃", radius = 0.65, color = { 0.5, 0.7, 0.2 }, score = 16, emoji = "🥝" },
    { name = "番茄", radius = 0.75, color = { 0.9, 0.3, 0.1 }, score = 32, emoji = "🍅" },
    { name = "桃子", radius = 0.88, color = { 1.0, 0.7, 0.5 }, score = 64, emoji = "🍑" },
    { name = "菠萝", radius = 1.0,  color = { 0.9, 0.7, 0.1 }, score = 128, emoji = "🍍" },
    { name = "椰子", radius = 1.15, color = { 0.5, 0.3, 0.1 }, score = 256, emoji = "🥥" },
    { name = "半西瓜", radius = 1.35, color = { 0.3, 0.7, 0.2 }, score = 512, emoji = "🍉" },
    { name = "大西瓜", radius = 1.6,  color = { 0.2, 0.6, 0.1 }, score = 1024, emoji = "🍉" },
}
```

Missing this field causes a **silent failure**: `fd.emoji` returns `nil`, `nvgText(nvg_, sx, sy, nil)` renders nothing, and fruits show as blank colored circles. The Lua runtime won't error because `nvgText` accepts nil as text and just draws nothing.

### Screen coordinate sync in HandleUpdate

When using independent NVG context for rendering, store the initial `WorldToScreen` output when creating a fruit, then update `f.sx, f.sy` every frame in `HandleUpdate`:

```lua
-- When creating a fruit:
local sx, sy, _, _, scale = WorldToScreen(physX, physY)
table.insert(fruits, {
    node = node,
    r255 = ..., g255 = ..., b255 = ...,
    sr = fd.radius * scale,
    -- sx, sy will be updated per-frame, no need to store initial
})

-- Every frame in HandleUpdate:
for _, f in ipairs(fruits) do
    if f.node and f.node:IsEnabled() then
        local p = f.node.position2D
        if p then f.sx, f.sy = WorldToScreen(p.x, p.y) end
    end
end
```

Note: the first frame after creation has no `f.sx/f.sy` — that's fine, the NanoVG render skips nil entries and the next frame updates them.

## AGENTS.md Rules (Must Follow)

TapTap Maker projects come with an `AGENTS.md` that defines hard rules for AI agents. Key ones:
1. **Length units are meters** — physics uses meters, convert with PixelPerUnit
2. **Code goes in `scripts/`** — never create files at project root
3. **Start from scaffold** — use `templates/scaffold-2d-physics.lua` for Box2D physics games
4. **Use maker_build_current_directory to submit** — no manual `git commit` + `git push` for builds

## ⚠️ Board-Style Merge Game Patterns (棋盘合成游戏)

When generating a grid-based merge game (like Merge Dragons, 四季合合) — no Box2D physics, grid-based merge mechanics — use `templates/scaffold-2d.lua` (not the physics scaffold).

The game has TWO interaction modes; **prefer drag (v2)** unless the user requests click-to-select (v1):

### Interaction Mode A: Click-to-Select (v1)

1. **Click → select** item → yellow highlight ring
2. **Click empty cell** → move item there
3. **Click same-level item** → merge into level+1
4. **Click different item** → switch selection
5. **Click outside** → deselect

### ✅ Interaction Mode B: Drag-to-Move (v2 — Preferred)

Subscribe to three mouse events:
```lua
SubscribeToEvent("MouseButtonDown", "HandleMouseDown")
SubscribeToEvent("MouseMove", "HandleMouseMove")
SubscribeToEvent("MouseButtonUp", "HandleMouseUp")
```

State variables:
```lua
local dragging = false
local dragFromR, dragFromC   -- source grid cell
local dragPosX, dragPosY     -- finger position (logical pixels)
local dragItemLevel = 0
```

**MouseDown**: if click is on an item → `dragging=true`, record source.
**MouseMove**: update `dragPosX/Y` for render.
**MouseUp**: `ScreenToGrid()` to find target → `DoMoveOrMerge()`.

**Rendering**: In the item render loop, skip the cell being dragged (`isDragSrc`). After the loop, draw the dragged item at `dragPosX/Y` with 1.15x scale + drop shadow + season glow border.

### Data Structure

```lua
local rows, cols = 6, 6
local board = {}  -- board[row][col] = { level = n } or nil
```

### Core Logic Loop

1. **On drop** (mouse up on a valid target cell): move or merge
2. **Merge**: destroy both same-level items, spawn level+1 at target cell, score points
3. **Chain merge**: scan 4-direction neighbors for same-level pairs → repeat until none
4. **Refill**: if chain stops, spawn 1-3 level-1 items in random empty cells
5. **Post-refill scan**: refilled items may auto-merge → scan again
6. **Game over**: no empty cells AND no mergeable pairs → show overlay, click to restart

### Screen Coordinate → Grid Cell

```lua
function ScreenToGrid(logX, logY)
    if cellSize <= 0 then return -1, -1 end
    local col = math.floor((logX - boardLX) / cellSize) + 1
    local row = math.floor((logY - boardLY) / cellSize) + 1
    return row, col
end
```

### Chain Merge (连锁合成)

Use a `while` loop with max 10 passes. Collect new merge candidates in a `pendingItems` table to avoid recursion:

```lua
local pendingItems = {}  -- { r, c } entries to check

function ProcessPendingMerges()
    local maxPasses = 10
    while #pendingItems > 0 and maxPasses > 0 do
        maxPasses = maxPasses - 1
        local newPending = {}
        for _, item in ipairs(pendingItems) do
            local r, c = item.r, item.c
            local src = board[r][c]
            if src and src.level < MAX_LEVEL then
                for _, d in ipairs({{-1,0},{1,0},{0,-1},{0,1}}) do
                    local nr, nc = r+d[1], c+d[2]
                    if IsInsideBoard(nr, nc) then
                        local nb = board[nr][nc]
                        if nb and nb.level == src.level then
                            -- merge: new level at neighbor, clear source
                            board[nr][nc] = { level = src.level + 1 }
                            board[r][c] = nil
                            -- add animation + score
                            table.insert(newPending, { r=nr, c=nc })
                            break
                        end
                    end
                end
            end
        end
        pendingItems = newPending
    end
end
```

### ⚠️ Double `local` Declaration Produces Shadowed Table Bug

**Symptom**: A table that is shared between two functions (e.g. `MergeCreateFruit` writes to it, `HandleNanoVGRender` reads from it) appears empty in one of them — merge effects/spawn animations never render.

**Root cause**: The same variable name is declared with `local` **twice** in the same file, at different locations. Lua's `local` declaration shadows the earlier one, but which one each function captures depends on where the function body **is defined**, not where it runs:

```lua
-- ❌ WRONG: mergeEffects declared twice
local mergeEffects = {}  -- [A] table A

function MergeCreateFruit(...)
    table.insert(mergeEffects, { ... })  -- writes to [A]
end

local mergeEffects = {}  -- [B] NEW local - shadows [A]!

function HandleNanoVGRender(...)
    for _, ef in ipairs(mergeEffects) do  -- reads from [B] — always empty!
    end
end
```

**Fix**: Delete the **second** `local` declaration. Keep only one, placed **before any function that uses it**:

```lua
-- ✅ CORRECT: only one local declaration, before all consumers
local mergeEffects = {}

function MergeCreateFruit(...)
    table.insert(mergeEffects, { ... })
end

function HandleNanoVGRender(...)
    for _, ef in ipairs(mergeEffects) do ... end  -- reads same table
end
```

**Quick check**: Search for the same variable name with two `local` declarations in one file. The second one should almost always be a bare assignment (`mergeEffects = {}`), not a re-declaration.

### Lua Variable Declaration Order (⚠️ Critical Pitfall)

**All functions that reference `board`, `rows`, `cols`, or other local-upvalues must be defined AFTER those variables are declared with `local`.** Lua `local` declarations are not hoisted — using a `local` variable before its declaration line results in `nil`, which causes hard-to-debug errors like `attempt to index a nil value (global 'board')`.

```lua
-- ❌ WRONG: function uses `board` and `rows` before they're declared
function GetRefillCount()
    for r = 1, rows do ...   -- rows is nil here!
        local item = board[r][c]  -- board is nil here!
    end
end

local rows, cols = CONFIG.Rows, CONFIG.Cols
local board = {}

-- ✅ CORRECT: declare locals first, then define functions
local rows, cols = CONFIG.Rows, CONFIG.Cols
local board = {}

function GetRefillCount()
    for r = 1, rows do ... end  -- works
end
```

This is a **frequent source of runtime errors** because the code loads without a syntax error — the nil is only discovered when the function first runs at runtime. When debugging `"bad 'for' limit (number expected, got nil)"` or `"attempt to index a nil value (global 'board')"`, always check function ordering relative to `local` declarations.

### ✅ NVG Rendering: Option A — PNG Sprite Images via nvgImagePattern (Remote Build, Preferred)

**Newly confirmed (2026-07-10)**: `nvgCreateImage` + `nvgImagePattern` works on remote cloud builds for rendering PNG sprites. This is the preferred approach over geometry-only rendering because it allows AI-generated artwork.

Use Maker MCP's `generate_image` or `batch_generate_images` to create sprites, then render via NVG:

```lua
-- Load images at Start()
for lvl = 1, MAX_LEVEL do
    local img = nvgCreateImage(nvg_, "assets/image/item_" .. name .. ".png", 0)
    if img >= 0 then itemImages[lvl] = img end
end

-- Render in HandleNanoVGRender
if imgId and imgId >= 0 then
    local scale2 = (drawHalf * 2) / 128  -- 128 = source image size
    nvgSave(nvg_)
    nvgTranslate(nvg_, cx - drawHalf, cy - drawHalf)
    nvgScale(nvg_, scale2, scale2)
    nvgBeginPath(nvg_)
    nvgRect(nvg_, 0, 0, 128, 128)
    nvgFillPaint(nvg_, nvgImagePattern(nvg_, 0, 0, 128, 128, 0, imgId, 1.0))
    nvgFill(nvg_)
    nvgRestore(nvg_)
end
```

#### Using Maker MCP `batch_generate_images` for Game Sprites

Tool: `batch_generate_images` — generates 2-10 images in parallel from the Maker MCP tool list.

Required params: `prompt` (Chinese, ≤50KB), `name` (filename prefix), `target_size`.

Recommended settings for game sprites:
```json
{
  "prompt": "绿色种子，发芽的小种子图标，游戏物品贴图",
  "name": "item_seed",
  "aspect_ratio": "1:1",
  "target_size": "128x128",
  "transparent": true
}
```

Output includes `previewUrl`, `localPath` (e.g. `assets/image/item_seed_20260710.png`), `absolutePath`. Images auto-download.

8 items → 8 parallel requests via `batch_generate_images` (input `images` array). Each returns independently.

**⚠️ Image naming**: Generated filenames include a timestamp. Reference exact paths in `nvgCreateImage` calls (or rename to stable names after generation).

**⚠️ `nvgDeleteImage` in Stop()**: Always clean up loaded images:
```lua
function Stop()
    for lvl = 1, MAX_LEVEL do
        if itemImages[lvl] and itemImages[lvl] >= 0 then
            nvgDeleteImage(nvg_, itemImages[lvl])
        end
    end
    if nvg_ then nvgDelete(nvg_); nvg_ = nil end
    UI.Shutdown()
end
```

### ⚠️ NVG Rendering: Option B — Geometry Only (Fallback if images not available)

**Critical**: `nvgText()` does NOT render on remote cloud builds (2026-07 confirmed). All item graphics must be drawn with geometric primitives:

```lua
-- ✅ DO: draw items as geometric shapes
local ITEM_TYPES = {
    { name = "种子", color = {0.5,0.85,0.3}, score = 1, 
      draw = function(nvg, cx, cy, h, r, g, b)
          nvgEllipse(nvg_, cx, cy+h*0.05, h*0.5, h*0.6)
          -- ... nvgQuadTo for sprout ...
      end
    },
    ...
}

-- ❌ DON'T: rely on nvgText or emoji strings
nvgText(nvg_, cx, cy, "🌱")  -- won't render on remote build
nvgText(nvg_, cx, cy, tostring(level))  -- won't render on remote build
```

**8 Item Geometry Recipes** (see `references/siji-merge-game-patterns.md` for full code):

| 物品 | 形状方案 |
|------|---------|
| 种子 | 椭圆 + 顶部三角形小芽 |
| 花苗 | 5 × 圆形花瓣 + 黄色花心 |
| 水珠 | 水滴形 (quadTo) + 白色高光小圆 |
| 浪花 | 3 层色差递减的波浪线 (quadTo) |
| 落叶 | 3 尖枫叶形 + 中心叶脉 |
| 丰 | 橙色圆 + 5 条棱线 + 绿柄 |
| 雪花 | 6 角 + 12 小分支 + 发光中心 |
| 冰晶 | 大菱形 + 内菱形 + 外围光晕 |

Draw function signature: `fn(nvg, cx, cy, half, r255, g255, b255)`

### Merge Animation

Use `os.clock()` for timing. Elastic ease: `0.5 → 1.2 → 1.0` over 0.3s.

**⚠️ Critical pitfall**: Do NOT use a global `mergeAnims` table with per-frame cleanup. Timestamps can linger due to floating-point precision, causing items to render permanently at wrong scale.

**✅ Correct pattern**: Store `mergeTime` directly on the board data object. Each render frame checks the cell's own timestamp and clears on expiry:

```lua
-- When merging: store mergeTime in the destination cell
board[toR][toC] = { level = newLevel, mergeTime = os.clock() }

-- In render loop:
local item = board[r][c]
if item and item.mergeTime then
    local elapsed = os.clock() - item.mergeTime
    if elapsed < CONFIG.MergeAnimTime then
        -- Animating: apply elastic scale
        local p = elapsed / CONFIG.MergeAnimTime
        if p < 0.4 then animScale = 0.5 + 0.7*(p/0.4)
        else animScale = 1.2 - 0.2*((p-0.4)/0.6) end
    else
        item.mergeTime = nil  -- expired, clear in-place
    end
end
```

### Render Pipeline (HandleNanoVGRender)

1. Calculate cellSize, boardLX, boardLY
2. Board background (dark rounded rect)
3. Filter expired `mergeAnims`
4. Loop cells: empty→dim bg / occupied→season glow arc → item.draw() → merge flash
5. Draw dragged item (layer above grid)
6. Game over overlay (if applicable)

### See also

`references/siji-merge-game-patterns.md` — full annotated reference implementation with v2 drag+geometry patterns.

## Debugging Etiquette (用户偏好)

**"能跑就不要轻易改文件"** — When diagnosing a runtime error:
1. Find the root cause
2. Fix ONLY the minimum necessary code to resolve it
3. Do NOT "improve" nearby code, refactor, or fix cosmetic issues
4. Explain what changed and why, and offer to fix secondary issues separately
5. Let the user decide if they want further changes

This user prefers minimal surgical fixes over cleanup-driven changes.

## Common Task: Create a New Maker Project (from scratch)

When the user wants a **brand new** project that doesn't exist on Maker yet (not cloning an existing one):

```bash
# 1. Create a new empty directory
mkdir -p /path/to/project

# 2. Run init with --create --name
npx.cmd -y @taptap/maker init --create --name "项目名" --target-dir . --skip-confirm
```

This creates the project on Maker's remote, generates `.maker-mcp/config.json` with a real UUID, clones the scaffold, and sets up git with correct remote. The `--create` flag is essential — without it, `init` expects to select from existing apps.

**⚠️ Must use an empty/unbound directory**: `init --create --name` will fail if the target directory is already bound to a Maker project (even a partial one). If you get `"Current directory is already bound to Maker project"`, either:
- Use a fresh empty directory, or
- Delete the stale `.maker-mcp/config.json` and try again

**⚠️ Branch must be `main`, not `master`**: Maker's remote **only accepts `main` branch**. If your local repo has `master`:
```bash
git branch -m master main
```

**⚠️ `.maker-mcp/config.json` is gitignored**: The scaffold `.gitignore` ignores `.maker-mcp/`. Force-add it:
```bash
git add -f .maker-mcp/config.json
```

**⚠️ First push may get `remote_rejected` (diverged)**: If you init'd via `--create` then re-used files from another project, remote has an init commit while local has different commits. Fix:
```bash
git fetch origin main
git rebase origin/main
git push origin main --force-with-lease
```

## Troubleshooting

### Build failed: "pre-receive hook declined"

TapTap rejects pushes containing files matching forbidden patterns (`.log` files, etc.). Check git status — undo any accidental commit:

```bash
git reset --soft HEAD~1   # undo last commit
git restore --staged *.log # unstage forbidden files
```

### Project archived as .zip (desktop cleanup)

The user may have compressed a Maker project into a .zip (e.g. during desktop cleanup). When the user asks you to "fix the game" but the project directory doesn't exist:

1. Search for the zip: `search_files(target="files", pattern="*合成*")` or `*西瓜*` or the project name
2. Unzip: `unzip -o "<zip_path>" -d "<target_dir>"`
3. Proceed with git pull + build as normal

### "Subst" drive not working in new session

The `subst` mapping is per-session. Re-run `subst S: ...` in each new execute_code or terminal call.

### Runtime log watcher shows "pulled: 0" forever

The watcher polls remote logs but gets nothing — either the game has no `print()` output, or the game script crashed before any output was generated. Check `watcher.err.log` and `state.json` in `.maker/logs/runtime/`.

### Chinese path encoding in git-bash

Piping through `cmd.exe` with Chinese characters produces garbled output. Always use `subst S:` drive mapping before starting MCP servers from within git-bash.

### Per-Frame Physics → Screen Position Sync (Remote Build Workflow)

**⚠️ Pitfall: Merge/combine logic needs a dedicated creation function**

When implementing merge detection (e.g. Suika game), the function that creates a new merged fruit **must not** go through the user-drop path. The user-drop function typically checks `canDrop`, consumes `currentType`/`nextType`, and sets cooldowns — all of which are wrong for merge-spawned fruits:

```lua
-- ❌ WRONG: merging calls DropFruit which checks canDrop and swaps currentType
for _, info in ipairs(toCreate) do DropFruit(info.x, info.y) end

-- ✅ CORRECT: dedicated merge creation function
function MergeCreateFruit(ftype, wx, wy)
    local fd = FRUIT_TYPES[ftype]
    local node = scene_:CreateChild("M" .. #fruits)
    node.position2D = Vector2(wx, wy)
    node:SetVar("fruitType", ftype)
    -- ... physics setup ...
    table.insert(fruits, { node = node, ... })
end

-- In HandlePostUpdate:
for _, info in ipairs(toCreate) do MergeCreateFruit(info.type, info.x, info.y) end
```

When using the independent NVG context for rendering physics objects on remote builds, structure your data like this:

```lua
-- Store physics nodes + render properties in one table
local fruits = {}  -- { node, r255, g255, b255, sr, sx=nil, sy=nil }

function CreateFruit(ftype, wx, wy)
    local node = scene_:CreateChild("F_"..#fruits)
    node.position2D = Vector2(wx, wy)
    -- ... physics setup ...
    local fd = FRUIT_TYPES[ftype]
    fruits[#fruits+1] = {
        node = node,
        r255 = math.floor(fd.color[1]*255),
        g255 = math.floor(fd.color[2]*255),
        b255 = math.floor(fd.color[3]*255),
        sr = fd.radius * scale,  -- approximate, update per-frame
    }
end

-- Update screen positions every frame in HandleUpdate
function HandleUpdate(eventType, eventData)
    for _, f in ipairs(fruits) do
        if f.node and f.node:IsEnabled() then
            local pos = f.node.position2D
            if pos then
                f.sx = (pos.x - camX) * scale + lw / 2
                f.sy = lh - ((pos.y - camY) * scale + lh / 2)
            end
        end
    end
end

-- Render in NanoVGRender using pre-computed screen coords
function HandleNanoVGRender(eventType, eventData)
    nvgBeginFrame(nvg_, lw, lh, dpr)
    for _, f in ipairs(fruits) do
        if f.node and f.node:IsEnabled() and f.sx then
            nvgCircle(nvg_, f.sx, f.sy, f.sr)
            nvgFillColor(nvg_, nvgRGBA(f.r255, f.g255, f.b255, 220))
            nvgFill(nvg_)
        end
    end
    nvgEndFrame(nvg_)
end
```

### DPR Handling for Touch/Mouse Input

`eventData["X"]:GetInt()` returns **physical pixels**, not logical pixels. NanoVG operates in **logical pixels** (divided by DPR). Always divide input coordinates by DPR before world-coordinate conversion.

⚠️ **Use `GetFloat()` not `GetInt()`** — input coords may have sub-pixel precision. `GetInt()` truncates, causing subtle positional offset:

```lua
function HandleClick(eventType, eventData)
    -- Use GetFloat() for precision
    local physX = eventData["X"]:GetFloat()  -- NOT GetInt()
    local dpr = graphics:GetDPR()
    local logX = physX / dpr                    -- logical pixels
    -- ...
end
```

⚠️ **World-to-screen inverse must be exact** — the click handler must use the **exact algebraic inverse** of `WorldToScreen()`, not a re-derived formula. Even slight differences in constants (e.g. `BoxWidth` vs `BoxWidth + 2.0`) cause the fruit to appear offset from the click point by a wrong ratio:

```lua
-- WorldToScreen (rendering):
-- sx = (wx - camX) * scale + lw / 2

-- HandleClick inverse (correct):
-- worldX = (logX - lw/2) / scale + camX

-- HandleClick inverse (WRONG — different formula produces offset):
-- worldX = (ratio - 0.5) * (BoxWidth + 2.0) + BoxWidth/2
```

**Always derive the click handler as the exact inverse of WorldToScreen: `worldX = (logX - lw/2) / scale + camX`**

Without DPR division, rendered positions are offset rightward by DPR× pixels.

### NanoVG Color Values

`nvgRGBA(r, g, b, a)` expects **0-255 integers**. Convert 0-1 floats:
```lua
nvgFillColor(nvg_, nvgRGBA(
    math.floor(color[1] * 255),
    math.floor(color[2] * 255),
    math.floor(color[3] * 255),
    220
))
```

### NanoVG Text Rendering NOT Available on Remote Build (2026-07)

As of 2026-07-09, `nvgText()` does NOT render on remote cloud builds even with font loaded. Geometry (circles, rects) works fine. UI.Label widgets work fine (they use a different render path). For text that must appear on remote builds, use UI.Label widgets.

### 合成大西瓜专用调试笔记

详见 `references/suika-no-visual-debug.md`。包含完整的诊断步骤、方案对比、每帧坐标同步技巧和 DPR 处理。
