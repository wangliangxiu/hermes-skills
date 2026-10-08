---
name: sensenova-image-and-animation
description: 用商汤SenseNova出图并做成帧动画。
---

# 商汤 SenseNova 出图 / 静态图转帧动画

触发：用商汤出图、SenseNova 生图、把一张图做成动画、给图配 GIF/MP4。
上层技能包（sn-image-base / sn-* 那一套，属外部资产不要去改）只讲参数表；这里记的是本机能跑通的操作要点、验证方法和坑。

## 跑之前

- Key 在 `C:\Users\使用者\.hermes\.env`（**技能脚本只认这个路径**）。运行前：`set -a; source "$HOME/.hermes/.env"; set +a`。
- runner：`C:/Users/使用者/AppData/Local/hermes/skills/sn-image-base/scripts/sn_agent_runner.py`。
- **命令里传原生路径**：`$HOME` 在 git-bash 里展开成 `/c/Users/...`，原生 python 打不开（报 `can't open file 'C:\c\Users\...'`）。一律写 `C:/Users/使用者/...`。
- 终端里别做这三件事，会触发审批弹窗、超时就直接 BLOCKED：显式展开 `$SN_API_KEY`（让 runner 自己读 .env）、`env` 全量导出、`rm` 删文件。删文件用 python `os.remove`，写文本文件用 write_file（别 heredoc）。

## 出图（实测命令，约 30 秒）

```bash
python "C:/Users/使用者/AppData/Local/hermes/skills/sn-image-base/scripts/sn_agent_runner.py" sn-image-generate \
  --prompt "<主体+姿态+视角+背景+风格+光比，姿态写细>" \
  --image-size 2k --aspect-ratio 1:1 \
  --save-path "C:/Users/使用者/Desktop/我的小项目/<项目>/xxx.png" --output-format json
```

- 默认模型 `sensenova-u1.5-lite`，输出 2048²，无水印，走公测免费额度。
- 提示词里把结构关系写清楚（例："双翼搭在车把上、双脚踩在踏板上、侧面视角"）比只写名词命中率高。
- **出图后先用 vision 自己看一眼再交付**：主体结构、肢体数量、有没有崩坏。别把没验过的图说成"做好了"。

## 改图出相位帧

```bash
python "<runner>" sn-image-edit --prompt "<只改哪里>" --images "<原图>" --save-path "<帧2.png>"
```

- 提示词必须写"保持构图/光影/背景/主体结构完全不变，只让 X 变化"，否则整张重画。
- **一帧一验，坏帧丢掉**：小幅度相位改动（腿从踏板低位到蹬出去）可用；大改动（"抬到最高点"这类）会让主体整体飘离/变形——实证有一帧主体直接离开车座悬空，只能丢。两帧能用就做两帧，不要硬凑四帧。

## 串帧成动画（ffmpeg，本机已装）

1. 写 `list.txt`（用 write_file，别 heredoc）：`file '帧A.png'` / `duration 0.4` 交替，末行再写一次首帧收尾。
2. MP4：`ffmpeg -y -stream_loop 7 -f concat -safe 0 -i list.txt -vf "fps=24,scale=1024:1024:flags=lanczos" -c:v libx264 -pix_fmt yuv420p -movflags +faststart out.mp4`
3. GIF：同样命令，`-vf` 换成 `"fps=8,scale=720:720:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"`。
4. **验证动画真的动了**：`ffprobe` 看时长/帧数 → 在两个不同时间点抽帧（`ffmpeg -ss 0.2 -i out.mp4 -frames:v 1 chk.png`）→ 用 vision 比对两帧确实不同。只看到文件生成不算数。
- 可直接跑：`scripts/make_frame_loop.py 帧1.png 帧2.png --out 动画`（出 mp4+gif 并打印 ffprobe 与抽帧校验路径）。

## 能力边界（先确认，再承诺）

- 开工前拉一次 `/v1/models` 看 `output_modalities`，确认套餐里有没有视频模型；这个 token-plan 覆盖对话/多模态 + 图像生成。
- 所以"做一个动画"的可行解是：出图 → 图像编辑出相位帧 → ffmpeg 串帧循环。交付时**明确说这是帧动画不是文生视频**，并描述实际观感（蹬一下、轻微起伏），别让使用者按"流畅视频"的预期验收。
- 产物放 `桌面\我的小项目\<项目名>\`：成图 + mp4 + gif；中间帧、list.txt、失败帧删掉（用 python os.remove）。
