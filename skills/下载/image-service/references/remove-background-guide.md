# 命令行抠图指南（remove background）

## 适用场景

用户要求"抠图"、"去掉背景"、"去底"、"透明背景"时使用。

## ⚠️ 用户偏好（甄der）

- 发现 rembg/u2net 效果不够理想时，**不要反复调参试**，直接换更好的本地模型方案
- 边缘要求：**丝滑渐变 + 无橙色/背景色残留**，缺一不可
- 不要用阈值砍/腐蚀/收缩破坏原始 mask 的渐变过渡——这样会导致边缘锯齿
- 正确的做法：保留原始 mask 的渐变 alpha，额外用**颜色检测**在过渡区抹掉背景色像素
- 用户反感"瞎编效果描述"，直接告诉他最终路径让他自己看

## 安装

```bash
pip install "rembg[cpu]"
```

> 注意：`rembg` 依赖 `pymatting` → `numba`，而 **numba 与 Python 3.14 不兼容**，会报 `KeyError: 'BREAK_LOOP'`。此时需要使用下面的**纯 ONNX 方案**绕过。

## 方案一：rembg CLI（推荐，兼容性好时用）

```bash
rembg i input.png output.png
```

## 方案二：纯 ONNX + u2net（兼容性最佳，绕过多 numba）

当 `rembg` 因 numba 报错时使用。直接调用 onnxruntime 跑 u2net 模型。

```python
import onnxruntime as ort
import numpy as np
from PIL import Image
import os

model_path = os.path.expanduser('~/.u2net/u2net.onnx')
if not os.path.exists(model_path):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    import urllib.request
    urllib.request.urlretrieve(
        'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx',
        model_path
    )

session = ort.InferenceSession(model_path)
input_name = session.get_inputs()[0].name

img = Image.open('input.png').convert('RGB')
orig_w, orig_h = img.size

# 预处理：resize → 归一化 → 标准化
img_resized = img.resize((320, 320))
img_array = np.array(img_resized).astype(np.float32) / 255.0
img_array = (img_array - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
img_array = img_array.transpose(2, 0, 1)[np.newaxis, ...].astype(np.float32)

# 推理
result = session.run(None, {input_name: img_array})[0][0, 0]

# 后处理：mask → 叠加 alpha 通道
mask = (result * 255).astype(np.uint8)
mask_img = Image.fromarray(mask).resize((orig_w, orig_h), Image.LANCZOS)
img.putalpha(mask_img)
img.save('output.png')

## 方案三：纯 ONNX + 颜色感知边缘优化（边缘丝滑 + 去残留）

当 u2net 基础方案出现**橙色/背景色边缘残留**时使用。
原理：保留原始 mask 的渐变 alpha（保证边缘丝滑），额外用颜色检测在过渡区砍掉背景色像素（保证无残留）。

```python
import onnxruntime as ort
import numpy as np
from PIL import Image
import os

model_path = os.path.expanduser('~/.u2net/u2net.onnx')
session = ort.InferenceSession(model_path)
input_name = session.get_inputs()[0].name

img = Image.open('input.png').convert('RGBA')
orig_w, orig_h = img.size

# --- Step 1: u2net 出原始渐变 mask（保留丝滑边缘）---
img_rgb = img.convert('RGB')
img_resized = img_rgb.resize((320, 320))
img_array = np.array(img_resized).astype(np.float32) / 255.0
img_array = (img_array - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
img_array = img_array.transpose(2, 0, 1)[np.newaxis, ...].astype(np.float32)

result = session.run(None, {input_name: img_array})[0][0, 0]
raw_mask = Image.fromarray((result * 255).astype(np.uint8)).resize((orig_w, orig_h), Image.LANCZOS)

# --- Step 2: 颜色检测去残留 ---
img_np = np.array(img, dtype=np.float32)
mask_np = np.array(raw_mask, dtype=np.float32)
r, g, b = img_np[:,:,0], img_np[:,:,1], img_np[:,:,2]

# 检测背景色（根据实际背景调整阈值）
is_background = (
    ((r > 200) & (g > 150) & (b < 150)) |  # 橙色系
    ((r > 220) & (g > 200) & (b > 150)) |  # 米色/浅色
    ((r > 200) & (g > 180) & (b > 180))     # 白色
)

adjusted_mask = mask_np.copy()
adjusted_mask[mask_np < 30] = 0  # 低置信度清0
# 过渡区 + 颜色像背景 → 清掉
transition = (mask_np >= 30) & (mask_np < 150)
adjusted_mask[transition & is_background] = 0

final_mask = np.clip(adjusted_mask, 0, 255).astype(np.uint8)
img.putalpha(Image.fromarray(final_mask))
img.save('output.png')
```

**关键参数调优：**
| 参数 | 作用 | 调大 | 调小 |
|------|------|------|------|
| `mask_np < 30` | 低置信度清零阈值 | 更激进砍半透明 | 保留更多渐变 |
| `mask_np >= 30 & < 150` | 过渡区范围 | 颜色检测范围更大 | 更保守 |
| 颜色阈值 (r/g/b) | 背景色判断 | 砍掉更多颜色 | 保留更多颜色 |

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `KeyError: 'BREAK_LOOP'` | numba 不兼容 Python 3.14 | 用方案二纯 ONNX |
| `INVALID_ARGUMENT : Unexpected input data type` | 输入 numpy 数组类型不是 float32 | 加 `.astype(np.float32)` |
| 模型下载慢 | GitHub 被墙 | 手动下载后放到 `~/.u2net/u2net.onnx` |
