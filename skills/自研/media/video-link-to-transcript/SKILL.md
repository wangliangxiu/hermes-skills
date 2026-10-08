---
name: video-link-to-transcript
description: 用户给视频链接要总结/拆解/拉字幕时用。先取元数据，无字幕再下音频转写。
---

# 视频链接 → 字幕/拆解（先读数据，再决定要不要转写）

适用：用户丢一个视频链接说"总结一下/拆解一下/看看讲了什么"。

## 铁律：先问"能不能不下载"

按这个顺序试，**不要一上来就下视频**（使用者会说"你怎么还下载视频"）。

### 第 0 步：先查已有技能
- `bilibili-video-extractor`（skillhub 装，D 盘）：`scripts/get_video_content.py --url <链接> --mode full --format markdown`，直接给元数据 + 弹幕 + 评论，**不需要下载**，B站首选。
- `creator-buddy`（D:\creator-buddy）：`video-Skills/space-video-transcript` 是"链接转字幕"，但它内部也是 yt-dlp 下音频 + ASR。
- `sn-search-social-cn`：B站/知乎/抖音**搜索**（不是取单个视频正文）。

### 第 1 步：元数据（秒级，不用下载）
```bash
UA="Mozilla/5.0 ... Chrome/126.0 Safari/537.36"   # 不带 UA 会被 412
curl -s -A "$UA" "https://api.bilibili.com/x/web-interface/view?bvid=BVxxxx"
# 取 title/owner/pubdate/duration/stat/cid/aid；评论：
curl -s -A "$UA" "https://api.bilibili.com/x/v2/reply?type=1&oid=<aid>&sort=2&ps=20"
```
临时文件放 `"$LOCALAPPDATA/Temp"`（本机没有 /tmp）。

### 第 2 步：探测有没有现成字幕
```bash
yt-dlp --no-warnings --list-subs "<url>"
```
B站 绝大多数视频**没有 CC 字幕**（只列 danmaku xml）→ 必须走 ASR。
有字幕就 `--write-subs --write-auto-subs --sub-langs "zh.*,ai-zh" --skip-download`，结束，别下音频。

### 第 3 步：只要音频，不要视频
```bash
yt-dlp --no-warnings -f "bestaudio/best" -o "audio.%(ext)s" "<url>"
ffmpeg -y -loglevel error -i audio.* -ac 1 -ar 16000 -vn audio16k.wav
```

### 第 4 步：ASR（本机 = faster-whisper CPU）
优先云 ASR：creator-buddy 的 `asr.py` 支持 `GROQ_API_KEY`（whisper-large-v3，快且准）。没 key 才本地。

本机本地转写的四个坑（都踩过）：
1. **ctranslate2 用不了 CUDA**：`get_cuda_device_count()` 返回 1，但加载就报 `LocalEntryNotFoundError`。**别下 large-v3-turbo（1.6G 白下）**，直接 `device="cpu", compute_type="int8"`。
2. **HF 只下 model.bin，缺配套文件** → `LocalEntryNotFoundError`。修法：手动补齐并从本地目录加载
   ```bash
   D="$LOCALAPPDATA/Temp/models/models--Systran--faster-whisper-small/snapshots/<hash>"
   for f in config.json tokenizer.json vocabulary.txt; do
     curl -sL -m 90 -o "$D/$f" "https://hf-mirror.com/Systran/faster-whisper-small/resolve/main/$f"; done
   ```
   然后 `WhisperModel(r"<那个 snapshots 目录>", device="cpu", compute_type="int8", cpu_threads=6)`，绕开 HF cache 查找。
3. **速度 ≈ 1x 实时**（small/int8/6线程）：6 分 25 秒音频约 6 分钟。要估时并**开跑前告诉用户**。
4. **small 模型会错中文术语**（"导出字幕"→"早出字幕"、"爆款"→"报款"、"PPT"→"PVT"、"Computer Use"→"Confirm Use"），交付时按上下文纠正并标注。

### 第 5 步：交付
- 转写存 txt（每行 `[起-止] 文本`，逐行 flush，便于中途查看）
- 清理：模型留 small（464M，可复用），音频/wav 询问后再删；**删任何 >100MB 的东西先单独报一句**（使用者敏感）
- 结论给三件：元数据表现、内容流程拆解、哪些能落地

## Pitfalls
- 后台跑 python 别 `| tail`（管道缓冲看不到进度），重定向到日志文件再 tail
- 用 `process_manage` 轮询看 `uptime_seconds` 判断耗时，别靠 date 错觉
