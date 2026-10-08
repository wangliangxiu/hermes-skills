# 四季合合 — Board Merge Game Reference Implementation

> Full annotated reference for grid-based merge games on TapTap Maker.
> Updated 2026-07-10: v11 stable — drag with isDragSrc skip, no image scaling, mergeTime on cell.

## Data Model

```lua
local board = {}  -- board[row][col] = { level = n, mergeTime = nil/f32 } or nil
local rows, cols = 6, 6

-- Item definitions: ITEMS[lvl] = { name, season={r,g,b}, score }
```

Items are stored as a flat array indexed by level (1..MAX_LEVEL).

## Core Loop

```
User drag (MouseDown → Move → MouseUp)
  → DoMoveOrMerge(fromR,fromC, toR,toC)
    → if target empty: move
    → if target same-level: merge (level+1, score, mergeTime on cell)
  → ProcessPendingMerges() (chain merge loop, max 10 passes)
  → RefillBoard() (spawn items, count decreases as max level rises)
    → No auto-chain merge on refill (let player manually drag)
  → CheckGameOver()
```

## Merge Animation

**DO NOT** use a global mergeAnims table. Store mergeTime directly on the cell:

```lua
-- When merging:
board[toR][toC] = { level = newLevel, mergeTime = os.clock() }

-- In render loop:
local item = board[r][c]
if item and item.mergeTime then
    local elapsed = os.clock() - item.mergeTime
    if elapsed < 0.3 then
        local p = elapsed / 0.3
        if p < 0.4 then animScale = 0.5 + 0.7*(p/0.4)
        else animScale = 1.2 - 0.2*((p-0.4)/0.6) end
    else
        item.mergeTime = nil  -- expired, no orphaned state
    end
end
```

## Drag Interaction (Mouse Events)

Three events:
```lua
SubscribeToEvent("MouseButtonDown", "HandleMouseDown")
SubscribeToEvent("MouseMove", "HandleMouseMove")
SubscribeToEvent("MouseButtonUp", "HandleMouseUp")
```

State:
```lua
local dragging = false
local dragFromR, dragFromC
local dragPosX, dragPosY     -- logical pixels (physical / DPR)
local dragItemLevel = 0
```

### HandleMouseDown
```lua
local logX = ed["X"]:GetFloat() / graphics:GetDPR()
local logY = ed["Y"]:GetFloat() / graphics:GetDPR()
-- ScreenToGrid → row, col
if board[row][col] ~= nil then
    dragging = true; dragFromR = row; dragFromC = col
    dragItemLevel = board[row][col].level
    dragPosX = logX; dragPosY = logY
    -- DO NOT clear board[row][col] here!
    -- Source cell is retained; render skips it via isDragSrc
end
```

### HandleMouseMove
```lua
if not dragging then return end
local dpr = graphics:GetDPR()
dragPosX = ed["X"]:GetFloat() / dpr
dragPosY = ed["Y"]:GetFloat() / dpr
```

### HandleMouseUp
```lua
-- Convert coords same as MouseDown → row, col
if IsInsideBoard(row, col) and (row ~= dragFromR or col ~= dragFromC) then
    DoMoveOrMerge(dragFromR, dragFromC, row, col)
    -- DoMoveOrMerge handles board[fr][fc] = nil on success
end
-- If outside board: source cell is still there (no harm)
dragging = false; dragItemLevel = 0
```

### Render Skip (isDragSrc)

In the item-drawing branch of the render loop:
```lua
local isDragSrc = dragging and dragFromR == r and dragFromC == c

if board[r][c] ~= nil and not isDragSrc then
    -- draw item normally
end
```

After the grid loop, draw the dragged item at finger position:
```lua
if dragging then
    local hh = cellSize * 0.42 * 1.15  -- 15% larger
    -- shadow: nvgCircle drop+3
    -- season glow ring
    -- item image/shape
end
```

The key insight: **never clear the source cell on MouseDown**. The source cell data stays in `board[][]` so if the drag ends outside the board (invalid drop), the item reappears naturally when `dragging` becomes false and `isDragSrc` stops skipping. `DoMoveOrMerge` clears `board[fr][fc]` only on successful move/merge.

## ScreenToGrid

```lua
function ScreenToGrid(logX, logY)
    if cellSize <= 0 then return -1, -1 end
    local col = math.floor((logX - boardLX) / cellSize) + 1
    local row = math.floor((logY - boardLY) / cellSize) + 1
    return row, col
end
```

Board origin calculated each frame:
```lua
local margin = lw * 0.15
local boardW = lw - margin * 2
local boardH = lh - margin * 2 - 60
cellSize = math.min(boardW / cols, boardH / rows)
boardLX = (lw - cellSize*cols) / 2
boardLY = (lh - cellSize*rows) / 2 + 10
```

## Dynamic Refill Count

```lua
function GetRefillCount()
    local maxLvl = 0
    for r = 1, rows do for c = 1, cols do
        local item = board[r][c]
        if item and item.level > maxLvl then maxLvl = item.level end
    end end
    if maxLvl <= 2 then return 3
    elseif maxLvl <= 4 then return 2
    else return 1 end
end
```

**⚠️ Function must be defined AFTER `board` / `rows` / `cols` are declared as `local`** — Lua local hoisting is NOT available; accessing a local before its declaration line yields nil.

## NVG Image Rendering (Stable Pattern)

```lua
-- Load at Start:
local img = nvgCreateImage(nvg_, "assets/image/filename.png", 0)

-- Draw each frame:
if imgId and imgId >= 0 then
    nvgSave(nvg_)
    nvgBeginPath(nvg_)
    nvgArc(nvg_, cx, cy, drawHalf, 0, math.pi*2, 0)
    nvgClosePath(nvg_)
    nvgFillPaint(nvg_, nvgImagePattern(nvg_,
        cx-drawHalf, cy-drawHalf, drawHalf*2, drawHalf*2,
        0, imgId, 1.0))
    nvgFill(nvg_)
    nvgRestore(nvg_)
end
```

**Avoid nvgScale/nvgTranslate for rendering sprites** — these alter the NVG global matrix and can cause permanent scaling bugs on remote builds. nvgImagePattern accepts explicit source rect, so just pass target coordinates directly.

## Maker MCP Image Generation

`batch_generate_images` accepts up to 10 parallel requests:

```json
{
  "images": [
    {"prompt": "绿色种子图标", "name": "item_seed",
     "aspect_ratio": "1:1", "target_size": "128x128", "transparent": true},
    ...
  ]
}
```

Returns per-image: `previewUrl`, `localPath` → `assets/image/{name}_{timestamp}.png`, `absolutePath`, `download.success`. Images auto-download.

## Debugging Checklist

When a new Maker project won't build:

1. **Branch name**: must be `main`, not `master`
2. **.maker-mcp/config.json**: must have real UUID (not Chinese chars), force-add to git
3. **scripts/main.lua**: must exist at that exact path in the repo
4. **CRLF warnings**: harmless, ignore
5. **Runtime errors**: check `.maker/logs/runtime/runtime.log` via watcher
6. **No visual output**: confirm print() in Start() to verify code executes
7. **"board is nil" / "rows is nil"**: function defined before local variable declaration — reorder
