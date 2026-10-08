# 运镜 / 景别 / 转场 对照表（照片转视频用）

## 运镜术语（提示词里用左列的英文标准词，别用自然语言口语）

| 术语 | 效果 | 适合的镜头 | 错误写法 |
|------|------|-----------|---------|
| Static / Locked-off | 固定机位 | 只想让画面内元素动（灯笼摆、香烟升） | Camera doesn't move |
| Slow Dolly In | 机位物理前移，透视改变、背景更远 | 建立镜头、正殿正面、门洞穿框 | Camera gets closer / 推近 |
| Zoom In | 焦距变化、背景压缩、平面感 | 强调细节的紧张感 | Zoom（不写方向） |
| Tilt Up / Down | 机位不动，镜头上下旋 | 仰视雕像、收尾露出上檐 | Camera looks up |
| Pan Left / Right | 机位不动，镜头左右旋 | 横幅展示、长廊 | Camera turns left |
| Truck Left / Right | 整机横移 | 沿廊柱横移、前景物滑出 | Camera moves left |
| Tracking Shot | 跟随主体 | 有人物走动时 | Follow the character |
| FPV / 第一人称 | 走动感、代入感 | 甬道/桥上向殿推进（人眼高、极轻微自然起伏） | Bird's eye view |
| Rack Focus | 焦点前后转移 | 前景石雕 → 背景建筑 | 前后都清晰 |

Dolly In 与 Zoom In 的区别写进提示词再选：要立体感用 Dolly In，要平面压迫感用 Zoom In。

## 景别与节奏

- 建立：大远景/全景（正面中轴对称、低机位）
- 中段：中景（第一人称推进）、中近景（框景）
- 情绪/细节峰值：特写（石狮、雕塑细部——**AI 伪字除外，别给文字特写**）
- **禁连续三镜同景别**；同类建筑不要连着排三镜全景

## 转场

| 转场 | 用在哪 |
|------|--------|
| 淡入 | 开场第一镜 |
| 叠化 | 时间/空间跳跃、收束段（如 全景→长廊） |
| 硬切 | 同一动线内连续推进 |

## 时长

- 单镜 4–5s（图生视频单次生成上限内），8 镜≈40s；
- 短版 15–20s：留建立、主体、第一人称、高潮、离场五镜。

## 负向提示词（每条都加）

变形、扭曲、物体消失、画面静止、背景冻结、水印、文字、镜头抖动、闪烁、画幅变化、分辨率变化
（morphing, distortion, disappearing objects, static image, frozen background, watermark, text,
jittery camera, flickering, aspect ratio change, resolution change）
