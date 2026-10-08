# 合成大西瓜 - 无视觉渲染调试记录

## 症状

游戏通过 TapTap Maker 云构建成功，手机/网页预览:
- UI 文字（分数、提示）正常显示
- 点击屏幕没有水果掉落视觉效果
- 运行时日志确认水果被创建、物理正常运行

## 关键发现 (2026-07-09)

### 1. `UI.QueueOverlay` 在远程云构建中完全不工作

经过彻底测试:
- ✅ UI 系统自己的控件（Label、Panel）渲染正常
- ✅ 游戏逻辑正常执行（print 日志确认 DropFruit、CreateFruit 被调用）
- ✅ 物理模拟正常
- ❌ `UI.QueueOverlay(callback)` 中的 NanoVG 绘制命令完全不执行——即使画一个固定位置的大红圆也不显示
- ❌ 多次迭代尝试无效

**结论：QueueOverlay 回调的渲染队列在远程构建中被静默忽略。**

### 2. 独立 NVG 上下文 + NanoVGRender 事件 — 几何图形能渲染

使用 `nvgCreate(1)` 创建独立 NVG 上下文 + `SubscribeToEvent(nvg_, "NanoVGRender", ...)`：

- ✅ **几何图形**（nvgCircle + nvgFillColor）正常渲染
- ❌ **文字/emoji**（nvgText）完全不显示——即使在固定像素坐标（100,100）画 ASCII 文字"Hello Test"
- ❌ **MiSans-Regular.ttf** 已加载到独立 NVG 上下文但文字不显示

**截至2026-07-09，nvgText() 在远程构建中完全不工作。** 纯色圆能显示但文字不行。

### 3. 世界坐标 → 屏幕坐标转换

已验证正确的转换：

```lua
local orthoSize = CONFIG.BoxHeight + 2.0  -- camera.orthoSize
local camX = CONFIG.BoxWidth / 2
local camY = CONFIG.BoxHeight / 2
local scale = lh / orthoSize

local sx = (pos.x - camX) * scale + lw / 2
local sy = lh - ((pos.y - camY) * scale + lh / 2)  -- Y 轴翻转
```

### 4. 点击坐标转换必须用 WorldToScreen 的精确逆运算

❌ **错误做法**：用不同的公式重新算一遍（比如直接用 `ratio * orthoW`），会导致水果出现在点击位置右侧偏移（比例不对）

✅ **正确做法**：从 `WorldToScreen` 的公式代数逆推：

```lua
-- WorldToScreen: sx = (wx - camX) * scale + lw/2
-- 逆运算: wx = (sx - lw/2) / scale + camX
-- 点击时: worldX = (logX - lw/2) / scale + camX
```

### 5. GetFloat() 优于 GetInt()

`eventData["X"]:GetInt()` 会丢掉小数精度。使用 `GetFloat()` 避免位置偏移。

### 6. 合并逻辑需要专用创建函数

合并产生的新水果**不能走用户点击的 DropFruit 路径**（它会检查 canDrop、消耗 currentType/nextType、设置冷却）。需要写一个专门的 `MergeCreateFruit` 函数。

## 正确方案（已验证）：独立 NVG 上下文 + 每帧同步物理位置

```lua
-- 全局
local nvg_ = nil
local fruits = {}  -- { node, r255, g255, b255, sr, sx=nil, sy=nil }

function Start()
    nvg_ = nvgCreate(1)
    nvgCreateFont(nvg_, "sans", "Fonts/MiSans-Regular.ttf")
    -- ... 其他初始化（UI, 场景, 相机） ...
    SubscribeToEvent(nvg_, "NanoVGRender", "HandleNanoVGRender")
end

function Stop()
    if nvg_ then nvgDelete(nvg_); nvg_ = nil end
    UI.Shutdown()
end

-- 每帧更新物理位置到屏幕坐标
function HandleUpdate(eventType, eventData)
    for _, f in ipairs(fruits) do
        if f.node and f.node:IsEnabled() then
            local pos = f.node.position2D
            if pos then
                f.sx = (pos.x - camX) * scale + lw/2
                f.sy = lh - ((pos.y - camY) * scale + lh/2)
            end
        end
    end
end

-- 渲染（必须手动管理 BeginFrame/EndFrame）
function HandleNanoVGRender(eventType, eventData)
    local vpW, vpH = graphics:GetWidth(), graphics:GetHeight()
    local dpr = graphics:GetDPR()
    local lw, lh = vpW/dpr, vpH/dpr
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

-- 点击坐标逆运算
function HandleClick(et, ed)
    local physX = ed["X"]:GetFloat()
    local dpr = graphics:GetDPR()
    local logX = physX / dpr
    local vpW = graphics:GetWidth()
    local lw = vpW / dpr
    local ortho = CONFIG.BoxHeight + 2.0
    local camX = CONFIG.BoxWidth / 2
    local scale = lh / ortho
    -- 精确逆运算
    local worldX = (logX - lw/2) / scale + camX
    -- ...
end
```

## 诊断步骤总结

### 1. 用 print() 确认代码是否运行
在关键函数加 print，检查 `.maker/logs/runtime/runtime.log`。

### 2. 分层测试法

| 层次 | 测试内容 | 独立 NVG 上下文 | QueueOverlay |
|------|---------|----------------|--------------|
| 1 | 固定位置大红圆 | ✅ 能显示 | ❌ 不能 |
| 2 | ASCII 文字 | ❌ 不能 | ❌ 不能 |
| 3 | 几何圆 + 坐标转换 | ✅ 能显示 | ❌ 不能 |

### 3. 颜色值范围
`nvgRGBA(r, g, b, a)` 接受 **0-255 整数**。

### 4. 字体加载
独立 NVG 上下文不共享 UI 系统的字体，必须手动加载：
```lua
nvg_ = nvgCreate(1)
nvgCreateFont(nvg_, "sans", "Fonts/MiSans-Regular.ttf")
```
但即使加载了，nvgText() 在远程构建仍不工作。

## 未解决问题
1. ⚠️ **独立 NVG 上下文中 nvgText() 不渲染任何文字（ASCII 和 emoji 均不显示）**
   - 远程构建的 NVG 实现可能裁剪了文本渲染路径
   - 或 `Fonts/MiSans-Regular.ttf` 在远程资源包中不存在
2. ⚠️ **emoji 需要支持彩色字体的渲染引擎** — 标准 NanoVG 不支持
