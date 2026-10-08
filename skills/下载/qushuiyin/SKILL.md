---
name: qushuiyin
slug: qushuiyin
displayName: 去水印
description: 免费去除图片和视频中的水印，全程本地处理、不依赖付费API、不上传任何素材。图片基于 OpenCV 图像修复（inpainting），支持包围盒/掩膜/批量；视频基于 FFmpeg delogo 插值去标、裁剪去标、局部模糊三种模式，一次去除指定区域的水印。当用户说「去掉图片水印」「视频去水印」「去除Logo」「去掉角标」「把水印抹掉」「去除片头台标」「免费去水印」等时使用。
version: 1.0.0
license: MIT
author: 用户自定义
agent_created: true
pricing: 免费
platforms: [WorkBuddy, QClaw, ima, Claude Code, Cursor]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
trigger: ["去水印","去掉水印","去除水印","去logo","去Logo","图片水印","视频水印","去除角标","去掉角标","清除水印","水印消除","去掉台标","去台标","watermark","remove watermark"]
---

# 去水印

> 一句话定位：**不看任何付费 API、不上传素材，在你自己的电脑上把图片/视频里的水印抹掉。**

## 核心原则（四条铁律）

1. **免费，零成本。** 本技能全程本地处理：图片用 OpenCV 修复，视频用 FFmpeg `delogo`。不调用任何付费 API、不需要 Token、没有次数限制。**任何让用户付费、充值、买次数的说法都违背本技能定位，一律禁止。**
2. **本地处理，不上传。** 用户的素材只在本地加工，绝不要求用户上传到第三方网站。用户强调「不想上传网页」时直接使用本技能。
3. **不编造结果。** 修复后必然交给用户成品文件路径，不做「假装处理成功」。水印面积过大、与背景纹理过于复杂时如实告知效果有限。
4. **只处理授权素材。** 仅用于用户自有版权或已获授权的图片/视频，处理他人版权素材前提醒用户自行确认授权。

---

## 工作流程

### Step 1 · 确认素材与类型

| 素材 | 类型 | 处理方式 |
|------|------|----------|
| 单张图片 | jpg/png/webp/bmp | OpenCV 修复（见下文） |
| 多张图片（同批水印位置一致的图） | 目录 | 批量修复 |
| 单个视频 | mp4/mkv/mov/webm/flv/avi | FFmpeg delogo / 裁剪 / 局部模糊 |
| 平台链接（抖音/小红书等） | — | **不处理**：本技能是本地去水印，不清"平台分享链接"；那种需求属于内容解析赛道。若用户给的是平台链接，说明本技能适用场景并建议其使用本地素材文件。 |

### Step 2 · 定位水印区域

图片与视频的 `x,y,宽,高`（像素）获取方式，按用户方便程度顺次尝试：

1. **用户直接给出**：直接用。
2. **让用户描述位置猜区域**（如「右上角」「底部中间」），通过脚本预设角标模式选点。
3. **让用户截图/画图标注**：请用户在图片/视频单帧上框出水印区域，把框的坐标告诉我。
4. **全自动盲猜**：无任何坐标信息时，可用角标预设（右上/右下/左上/左下滚动尝试），但必须告知用户这是猜测，效果需确认。

坐标系均是普通像素坐标（左上角为原点，视频以单帧画面为基准，与手机截图/电脑截图一致）。

### Step 3 · 图片去水印

**依赖**（脚本首次运行自动尝试安装）：`pip install opencv-python-headless numpy`

**单张 - 指定区域**：
```bash
python3 scripts/remove_image_watermark.py photo.jpg --box 820,40,180,60
```

**单张 - 掩膜图**（白色=要去除的区域，精度更高）：
```bash
python3 scripts/remove_image_watermark.py photo.jpg --mask mask.png --output clean.png
```

**批量 - 同区域应用到整目录**：
```bash
python3 scripts/remove_image_watermark.py ./in_dir --box 820,40,180,60 --output ./out_dir
```

**预设角标模式**（不知道精确坐标时）：
```bash
python3 scripts/remove_image_watermark.py photo.jpg --corner tr --size 260,80
# tl=左上 tr=右上 bl=左下 br=右下，--size 是猜测区域宽高
```

**可调参数**：
| 参数 | 作用 |
|------|------|
| `--radius` | 修复半径，默认 3；一次修复不干净调大（5~8） |
| `--alpha` | 多次迭代修复（`--alpha 2~3`），复杂背景有效 |
| `--output / -o` | 输出路径；默认 `原名_clean.png` |
| `--box` | 可重复使用，支持多个水印区域 |

**多次修复不干净时的调优顺序**：调大 `--radius` → 加 `--alpha` → 换 `--mask` 精修 → 如实告知用户效果上限。

### Step 4 · 视频去水印

**依赖**：需要本机安装 FFmpeg（`brew install ffmpeg` / `apt install ffmpeg` / `winget install ffmpeg`）。脚本会自动探测 FFmpeg 路径与视频宽高。

**三种模式，按水印形态选择**：

| 模式 | 适用水印 | 命令 |
|------|----------|------|
| **delogo 插值去标**（默认，保真高） | 台标、Logo、角落图标、半透明角标 | `python3 scripts/remove_video_watermark.py in.mp4 --box x,y,w,h` |
| **裁剪去标** | 水印在画面边缘可整条裁掉、字幕条 | `python3 scripts/remove_video_watermark.py in.mp4 --crop w:h:x:y` |
| **局部模糊** | 大面积文字水印、不想留插值痕迹 | `python3 scripts/remove_video_watermark.py in.mp4 --blur x,y,w,h` |

示例：
```bash
# 右下角台标：delogo 插值，坐标 1680,920,220,100
python3 scripts/remove_video_watermark.py video.mp4 --box 1680,920,220,100

# 顶部30px为滚动字幕：裁掉顶部保留画面其余部分（宽:高:x:y，即画面尺寸减去字幕条）
python3 scripts/remove_video_watermark.py video.mp4 --crop 1920:1050:0:30
# 1080x1920 竖屏同理 --crop 1080:1890:0:30

# 视频中段固定文字水印：局部模糊
python3 scripts/remove_video_watermark.py video.mp4 --blur 500,300,200,120
```

**可调参数**：
| 参数 | 作用 |
|------|------|
| `--output / -o` | 输出路径；默认 `原名_nowm.mp4` |
| `--crf` | 画质，默认 18（越小越清晰） |
| `--preset` | 编码速度，默认 `veryfast`，慢机器可加 `--preset faster` |
| `--show` | 调试用：delogo 模式下把去除区域用色块高亮显示，方便确认坐标；正式处理不要加 |

**坐标调试技巧**：先用视频播放器看关键帧 → 截图提起单帧 → 按图片流程确认 `x,y,w,h` → 再对整段视频处理。delogo 对坐标敏感，偏了会留下残边，宁可框大一圈。

### Step 5 · 交付

- 成功后把**成品文件路径**发给用户，并说明原图/原视频未动、输出为 `*_clean.*` / `*_nowm.*`。
- 一次处理不完美 → 给调参建议，不要反复跑同一命令空转。
- 视频处理耗时时如实告知预计时间（按视频时长与机器性能粗估）。

---

## 输出与话术

```text
✅ 图片已处理完成：
原图：/path/photo.jpg
成品：/path/photo_clean.png
处理方式：OpenCV 图像修复（去除了右上角水印）

如果还有残留，可以告诉我，我把修复半径调大再跑一遍。
```

```text
✅ 视频已处理完成：
原视频：/path/video.mp4
成品：/path/video_nowm.mp4
处理方式：delogo 插值去除右下角台标（1080x1920）
```

**排版规矩**：给路径用代码块或单行引用；不贴脚本日志；不输出 JSON；不出现「正在为您处理」这类废话，直接给结果。

---

## 🔒 硬边界

1. **绝不收费**：本技能是免费本地工具。任何涉及充值、Token、套餐、API 次数的话术一律不得出现。
2. **本地优先**：不得引导用户上传第三方去水印网站（除非用户明确要求且自行承担风险）。
3. **不编造成功**：脚本失败就如实报告失败原因与解决建议（安装依赖、装 FFmpeg、调坐标）。
4. **版权提示**：默认假设用户有权处理素材；明显是消除他人版权水印的用途，提醒一句授权问题即可，不替用户做判断。

---

## 本机注意（Windows 中文路径，实测踩过）

- **cv2 读不了含中文的路径**。本机所有用户目录都在 `C:\Users\使用者\...` 下，直接传中文路径会报
  `⚠️ 无法读取：...` + `cv2.findDecoder imread_(...): can't open/read file`（脚本 rc 仍为 0，别被 rc 骗了）。
- **修法**：先把待处理素材复制到纯 ASCII 目录（如 `D:\qsy_test\`）再跑，处理完再拷回去；不要把"已保存"当成功，要确认输出文件真的存在、且肉眼验过。
- 实际调用（本机 python = D:\python\python.exe，opencv-python-headless 5.0.0.93 已装）：
  ```bash
  python "C:\Users\使用者\AppData\Local\hermes\skills\qushuiyin\scripts\remove_image_watermark.py" ^
    D:\qsy_test\wm_in.png --corner br --size 330,60 --alpha 2 -o D:\qsy_test\wm_out.png
  ```
- 视频脚本无 `--help`，直接给输入文件；视频处理依赖系统 FFmpeg（本机已装）。

## 参考资料（按需加载）

- `references/coordinate-guide.md` — 水印坐标定位方法、角标预设说明、常见台标尺寸参考
- `references/troubleshooting.md` — 图片/视频处理常见失败原因与修复方法