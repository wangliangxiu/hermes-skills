#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去水印 · 视频水印去除脚本 v1.0.0
==================================
基于 FFmpeg 去除视频中的台标 / Logo / 角标 / 滚动字幕 / 文字水印。
全程本地处理，不联网、不调用任何 API、完全免费。

三种模式:
  1. delogo 插值去标（默认）  — 台标、Logo、角落图标，从周围像素插值补全
     python3 remove_video_watermark.py in.mp4 --box x,y,w,h
  2. crop 裁剪去标            — 水印在画面边缘可整条裁掉、滚动字幕条
     python3 remove_video_watermark.py in.mp4 --crop 宽:高:x:y
  3. blur 局部模糊            — 大面积文字水印、不想留插值痕迹
     python3 remove_video_watermark.py in.mp4 --blur x,y,w,h

依赖: 本机安装 FFmpeg（brew install ffmpeg / apt install ffmpeg / winget install ffmpeg）
"""
import os
import sys
import shutil
import subprocess
import json

FFMPEG_HINTS = {
    "darwin": "brew install ffmpeg",
    "linux": "sudo apt-get install -y ffmpeg",
    "win32": "winget install Gyan.FFmpeg",
}


def _find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        # macOS homebrew 常见路径兜底
        for p in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg",
                  "/usr/bin/ffmpeg"):
            if os.path.exists(p):
                return p
    return exe


def _find_ffprobe():
    exe = shutil.which("ffprobe")
    if not exe:
        for p in ("/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe",
                  "/usr/bin/ffprobe"):
            if os.path.exists(p):
                return p
    return exe


def probe_video_size(ffprobe, path):
    try:
        out = subprocess.check_output([
            ffprobe, "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", path,
        ], stderr=subprocess.DEVNULL)
        data = json.loads(out.decode("utf-8"))
        s = data["streams"][0]
        return int(s["width"]), int(s["height"])
    except Exception:
        return None


def _parse_box(text):
    vals = [int(v) for v in text.split(",")]
    if len(vals) != 4:
        raise ValueError("x,y,w,h")
    return vals


def _parse_crop(text):
    # 宽:高:x:y
    vals = text.split(":")
    if len(vals) != 4:
        vals = text.split(",")
    if len(vals) != 4:
        raise ValueError("宽:高:x:y 或 宽,高,x,y")
    return [int(v) for v in vals]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        hint = FFMPEG_HINTS.get(sys.platform, "安装 FFmpeg 后重试")
        print(f"❌ 未找到 FFmpeg。请先安装：{hint}")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"❌ 输入文件不存在：{input_path}")
        sys.exit(1)

    # ---- 简单参数解析（保证无额外依赖） ----
    args = sys.argv[2:]
    mode = None
    box = crop = blur = None
    output = None
    crf = "18"
    preset = "veryfast"
    show = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--box":
            mode = "delogo"
            box = _parse_box(args[i + 1])
            i += 2
        elif a == "--crop":
            mode = "crop"
            crop = _parse_crop(args[i + 1])
            i += 2
        elif a == "--blur":
            mode = "blur"
            blur = _parse_box(args[i + 1])
            i += 2
        elif a in ("--output", "-o"):
            output = args[i + 1]
            i += 2
        elif a == "--crf":
            crf = args[i + 1]
            i += 2
        elif a == "--preset":
            preset = args[i + 1]
            i += 2
        elif a == "--show":
            show = True
            i += 1
        else:
            print(f"❌ 未知参数：{a}")
            sys.exit(1)

    if not mode:
        print("❌ 请指定处理模式：--box x,y,w,h / --crop 宽:高:x:y / --blur x,y,w,h")
        sys.exit(1)

    if not output:
        base, ext = os.path.splitext(input_path)
        output = f"{base}_nowm.mp4"

    ffprobe = _find_ffprobe()
    if ffprobe:
        size = probe_video_size(ffprobe, input_path)
    else:
        size = None
        print("⚠️ 未找到 ffprobe，无法校验坐标范围，坐标错误可能导致处理失败。")

    if size:
        w, h = size
        if mode in ("delogo", "blur"):
            x, y, bw, bh = box if mode == "delogo" else blur
            if x < 0 or y < 0 or x + bw > w or y + bh > h:
                print(f"⚠️ 水印区域超出画面范围（画面 {w}x{h}，区域 x={x} y={y} w={bw} h={bh}）")
                print("   已自动截断到画面内。")
                x = max(0, min(x, w - 1))
                y = max(0, min(y, h - 1))
                bw = min(bw, w - x)
                bh = min(bh, h - y)
                if mode == "delogo":
                    box = [x, y, bw, bh]
                else:
                    blur = [x, y, bw, bh]
        elif mode == "crop":
            cw, ch, cx, cy = crop
            if cx + cw > w or cy + ch > h or cx < 0 or cy < 0:
                print(f"⚠️ 裁剪区域超出画面范围（画面 {w}x{h}，裁剪 {cw}x{ch}@{cx},{cy}）")
                print("   已自动截断。")
                cx = max(0, min(cx, w - 1))
                cy = max(0, min(cy, h - 1))
                cw = min(cw, w - cx)
                ch = min(ch, h - cy)
                crop = [cw, ch, cx, cy]

    # ---- 构造 FFmpeg 滤镜 ----
    if mode == "delogo":
        x, y, bw, bh = box
        show_part = ":show=1" if show else ""
        vf = f"delogo=x={x}:y={y}:w={bw}:h={bh}{show_part}"
        desc = f"delogo 插值去除区域 ({x},{y},{bw}x{bh})"
    elif mode == "crop":
        cw, ch, cx, cy = crop
        vf = f"crop={cw}:{ch}:{cx}:{cy}"
        desc = f"裁剪保留区域 ({cw}x{ch}@{cx},{cy})"
    else:  # blur
        x, y, bw, bh = blur
        # 先模糊再叠回原区域
        vf = (
            f"split[a][b];"
            f"[b]crop={bw}:{bh}:{x}:{y},boxblur=20:5[c];"
            f"[a][c]overlay={x}:{y}"
        )
        desc = f"局部模糊区域 ({x},{y},{bw}x{bh})"

    cmd = [
        ffmpeg, "-y", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-crf", crf, "-preset", preset,
        "-c:a", "copy",
        "-movflags", "+faststart",
        output,
    ]

    print(f"🔄 处理中：{desc}")
    print(f"   输入：{input_path}")
    print(f"   输出：{output}")
    if size:
        print(f"   画面：{size[0]}x{size[1]}")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        hint = FFMPEG_HINTS.get(sys.platform, "安装 FFmpeg 后重试")
        print(f"❌ FFmpeg 无法执行，请先安装：{hint}")
        sys.exit(1)

    if proc.returncode != 0:
        print("❌ FFmpeg 处理失败：")
        print(proc.stderr[-3000:] if proc.stderr else "（无错误输出）")
        sys.exit(1)

    print(f"✅ 视频已处理完成：{output}")
    print(f"   处理方式：{desc}；原视频未改动。")


if __name__ == "__main__":
    main()
