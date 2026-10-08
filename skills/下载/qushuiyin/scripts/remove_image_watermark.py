#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去水印 · 图片水印去除脚本 v1.0.0
==================================
基于 OpenCV 图像修复（Inpainting）去除图片中指定区域的文字/Logo/角标水印。
全程本地处理，不联网、不调用任何 API、完全免费。

用法:
  单张（指定水印区域 x,y,宽,高）:
    python3 remove_image_watermark.py photo.jpg --box 820,40,180,60

  单张（角标预设，不知道精确坐标时）:
    python3 remove_image_watermark.py photo.jpg --corner tr --size 260,80

  单张（掩膜图，白色=要去除的区域）:
    python3 remove_image_watermark.py photo.jpg --mask mask.png --output clean.png

  批量（同一区域应用到整目录）:
    python3 remove_image_watermark.py ./in_dir --box 820,40,180,60 --output ./out_dir

  多个水印区域:
    python3 remove_image_watermark.py photo.jpg --box 820,40,180,60 --box 10,10,120,40

依赖: pip install opencv-python-headless numpy
"""
import os
import sys
import glob
import argparse

try:
    import numpy as np
    import cv2
except ImportError:
    print("⚠️ 缺少依赖，正在自动安装 opencv-python-headless numpy ...", file=sys.stderr)
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                               "opencv-python-headless", "numpy"])
        import numpy as np
        import cv2
    except Exception as e:
        print(f"❌ 依赖安装失败：{e}")
        print("   请手动执行：pip install opencv-python-headless numpy")
        sys.exit(1)


def _out_msg(msg: str) -> None:
    print(msg, flush=True)


def box_to_mask(shape, box):
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    x, y, bw, bh = [int(v) for v in box]
    x, y = max(0, x), max(0, y)
    x2, y2 = min(w, x + bw), min(h, y + bh)
    if x2 <= x or y2 <= y:
        return None
    mask[y:y2, x:x2] = 255
    return mask


def corner_to_box(shape, corner, size):
    h, w = shape[:2]
    sw, sh = [int(v) for v in size]
    sw, sh = min(sw, w), min(sh, h)
    corner = corner.lower()
    if corner == "tl":
        return (0, 0, sw, sh)
    if corner == "tr":
        return (w - sw, 0, sw, sh)
    if corner == "bl":
        return (0, h - sh, sw, sh)
    if corner == "br":
        return (w - sw, h - sh, sw, sh)
    raise ValueError(f"未知角标位置: {corner}（可选 tl/tr/bl/br）")


def remove_watermark(img, mask, radius=3, iterations=1):
    # 轻微膨胀掩膜，避免边缘残留
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    result = img.copy()
    for _ in range(max(1, iterations)):
        result = cv2.inpaint(result, mask, radius, cv2.INPAINT_TELEA)
    return result


def process_file(path, boxes, mask_path, corner, size, radius, iterations, out_path):
    img = cv2.imread(path)
    if img is None:
        return f"⚠️ 无法读取：{path}"

    masks = []
    if mask_path:
        m = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if m is None:
            return f"⚠️ 掩膜图无法读取：{mask_path}"
        m = cv2.resize(m, (img.shape[1], img.shape[0]))
        _, m = cv2.threshold(m, 10, 255, cv2.THRESH_BINARY)
        masks.append(m)
    else:
        for box in (boxes or []):
            m = box_to_mask(img.shape, box)
            if m is None:
                _out_msg(f"  ⚠️ 区域超出画面范围被忽略：{box}")
                continue
            masks.append(m)
        if corner:
            masks.append(box_to_mask(img.shape, corner_to_box(img.shape, corner, size)))

    if not masks:
        return f"⚠️ 未提供任何有效的水印区域：{path}（用 --box x,y,w,h 或 --mask 或 --corner）"

    # 合并所有掩膜
    mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
    for m in masks:
        mask = cv2.bitwise_or(mask, m)

    result = remove_watermark(img, mask, radius, iterations)
    cv2.imwrite(out_path, result)
    return f"✅ 已保存：{out_path}"


def main():
    ap = argparse.ArgumentParser(description="去水印 · 图片水印去除")
    ap.add_argument("input", help="图片文件或目录")
    ap.add_argument("--box", action="append", help="水印包围盒 x,y,宽,高（像素），可重复")
    ap.add_argument("--mask", help="掩膜图路径（白色=去除区域）")
    ap.add_argument("--corner", choices=["tl", "tr", "bl", "br"],
                    help="角标预设：tl左上 tr右上 bl左下 br右下")
    ap.add_argument("--size", default="260,80", help="角标预设区域宽高（像素），默认 260,80")
    ap.add_argument("--radius", type=int, default=3, help="修复半径，默认 3")
    ap.add_argument("--alpha", type=int, default=1,
                    help="迭代修复次数，默认 1；复杂背景可设 2~3")
    ap.add_argument("--output", "-o", help="输出路径（文件或目录）")
    args = ap.parse_args()

    boxes = None
    if args.box:
        boxes = []
        for b in args.box:
            try:
                vals = [int(v) for v in b.split(",")]
                assert len(vals) == 4
                boxes.append(vals)
            except Exception:
                print(f"❌ --box 格式应为 x,y,宽,高，例如 820,40,180,60（收到：{b}）")
                sys.exit(1)

    size = [int(v) for v in args.size.split(",")] if args.size else [260, 80]
    if len(size) != 2:
        print("❌ --size 格式应为 宽,高，例如 260,80")
        sys.exit(1)

    if os.path.isdir(args.input):
        out_dir = args.output or (args.input.rstrip("/\\") + "_clean")
        os.makedirs(out_dir, exist_ok=True)
        files = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
            files += glob.glob(os.path.join(args.input, ext))
        if not files:
            print("⚠️ 目录中未找到图片文件。")
            return
        print(f"🔄 批量处理 {len(files)} 张，输出到 {out_dir}")
        for f in files:
            name = os.path.basename(f)
            out_path = os.path.join(out_dir, name)
            print("  " + process_file(f, boxes, args.mask, args.corner, size,
                                      args.radius, args.alpha, out_path))
    else:
        out_path = args.output or (os.path.splitext(args.input)[0] + "_clean.png")
        print(process_file(args.input, boxes, args.mask, args.corner, size,
                           args.radius, args.alpha, out_path))


if __name__ == "__main__":
    main()
