---
name: video-transcript-local
description: 无字幕视频要转写/拆解时用：音频+faster-whisper本地转。
---

# 无字幕视频本地转写

## 何时用
用户丢一个视频链接，要“总结 / 拆解 / 看讲了什么 / 能不能用”，而平台没给字幕（B站大多只有弹幕 XML）。

## 顺序：先便宜后贵，别跳步
1. **先想有没有现成技能**：能直接读的只有元数据/评论/弹幕（例如 skillhub 的 `bilibili-video-extractor`），**讲话内容一律要 ASR**，别声称有“不下载就能读正文”的技能。
2. 元数据直接走 API，不下载：
   ```bash
   curl -s -A "<浏览器UA>" "https://api.bilibili.com/x/web-interface/view?bvid=BVxxx"   # 标题/时长/播放/收藏/简介/cid/aid
   curl -s -A "<UA>" "https://api.bilibili.com/x/v2/reply?type=1&oid=<aid>&sort=2"  # 热评
   ```
3. 查字幕：`yt-dlp --list-subs URL`（B站基本只列 danmaku）。有 CC 字幕就下字幕，没有才进第 4 步。
4. 下**音频**（不要下整视频）+ 转写：
   ```bash
   yt-dlp -f bestaudio -o a.%(ext)s URL
   ffmpeg -y -i a.m4a -ac 1 -ar 16000 -vn a16k.wav
   ```
   6 分钟视频的音频只有 4MB 左右；下整视频是浪费。

## 本地 ASR（Windows）
- 依赖：`faster_whisper` + `ctranslate2` + `ffmpeg`。
- **模型选型**：别先试 large/turbo——本机 ctranslate2 调不起 CUDA（cuDNN 缺失），大模型白下 1.6G。直接 `Systran/faster-whisper-small`、CPU、`compute_type="int8"`、`cpu_threads=6`，速度≈1 倍实时。
- 下载走镜像：`export HF_ENDPOINT=https://hf-mirror.com`。
- **坑**：hf_hub 的快照常常只落 `model.bin`，缺 config/tokenizer → 加载报 `LocalEntryNotFoundError`。补：
  ```bash
  for f in config.json tokenizer.json vocabulary.txt; do curl -sL -o "<snapshot>/$f" \
    "https://hf-mirror.com/Systran/faster-whisper-small/resolve/main/$f"; done
  ```
  然后把本地快照目录直接传给 `WhisperModel(本地目录)`，绕开 HF 缓存查找。
- 参数：`language="zh", beam_size=5, vad_filter=True, initial_prompt="普通话技术讲解，涉及 <预期术语>"`（initial_prompt 能明显改善术语）。
- 输出逐段带时间戳写文件并每段 flush，长任务才有进度可看。

## 跑长任务的坑
- 后台跑**别用** `python x.py | tail`：管道缓冲，中途看不到任何输出。用 `python x.py > log 2>&1` 再 tail 日志。
- small 模型中文术语会飘（“导出字幕”会听成“早出字幕”）。要逐字原话就得换大模型或云端 ASR（Groq whisper-large-v3 之流，需 key）。
- 转写前先报预期耗时（音频时长 × 1 倍速 + 模型下载时间），别让用户干等。

## 交付
逐字稿只是素材，最终要按用户真正问的（总结 / 能不能用 / 哪些是吹的 / 哪些能搬过来）做拆解，不要把时间戳稿子当结论丢过去。
