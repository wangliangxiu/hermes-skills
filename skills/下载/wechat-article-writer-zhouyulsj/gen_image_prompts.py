#!/usr/bin/env python3
"""
配图 Prompt 智能生成器
读取文章 Markdown，分析每个插图位置的上下文，
结合配图风格生成针对性的 AI 绘图 prompt。

用法:
python3 gen_image_prompts.py article.md [-s 风格名] [-o output.yaml]

风格选项（styles/image/ 下）:
  ai_play       —  ✏️ 手绘蓝紫（默认）
  hand_drawn    —  🖊️ 手绘草图
  minimalist    —  ➖ 极简线条
  flat_design   —  🎨 扁平彩色
  photo_real    —  📷 写实摄影

文章中用以下方式标记插图位置：
  【配图：图片描述文字】
  或
  ![图片描述](placeholder)

第一张自动作为头图，其余为插图。
"""

import argparse
import os
import re
import sys
import json
import yaml

# Windows GBK 环境兼容
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def safe_print(text):
    """在 Windows GBK 环境下安全打印"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('gbk', errors='replace').decode('gbk'))

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLES_DIR = os.path.join(ROOT_DIR, "styles")
IMAGE_STYLES_DIR = os.path.join(STYLES_DIR, "image")
DEFAULT_STYLE = "ai_play"


def load_image_styles():
    """加载所有可用插图风格"""
    styles = {}
    if not os.path.exists(IMAGE_STYLES_DIR):
        return styles
    for f in os.listdir(IMAGE_STYLES_DIR):
        if f.endswith(".yaml") and not f.startswith("_"):
            path = os.path.join(IMAGE_STYLES_DIR, f)
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            name = f.replace(".yaml", "")
            styles[name] = data
    return styles


def list_available_styles():
    """列出所有可用风格"""
    styles = load_image_styles()
    if not styles:
        print("⚠️  未找到风格文件，请先创建 styles/image/*.yaml")
        return
    print("\n📋 可用配图风格：")
    print("-" * 40)
    for name, data in styles.items():
        desc = data.get("description", "")
        print(f"  {name:<15} — {desc}")
    print()


def extract_image_slots(md_text):
    """
    从 Markdown 中提取插图位置信息。
    支持两种标记格式：
      【配图：描述】
      ![描述](placeholder)
    """
    slots = []

    # 方法1：提取【配图：描述】格式
    pattern1 = re.compile(r'【配图[：:]([^】]+)】')
    for match in pattern1.finditer(md_text):
        alt = match.group(1).strip()
        pos = match.start()
        ctx_before = md_text[max(0, pos - 600):pos].strip()
        ctx_after = md_text[pos:pos + 600].strip()
        slots.append({
            "marker": match.group(0),
            "alt": alt,
            "position": pos,
            "context_before": clean_markdown(ctx_before[-300:]),
            "context_after": clean_markdown(ctx_after[:300]),
        })

    # 方法2：提取 ![描述](placeholder) 格式
    pattern2 = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    for match in pattern2.finditer(md_text):
        alt = match.group(1).strip()
        pos = match.start()
        # 跳过已有的【配图】槽位（避免重复）
        if any(abs(pos - s["position"]) < 10 for s in slots):
            continue
        ctx_before = md_text[max(0, pos - 600):pos].strip()
        ctx_after = md_text[pos:pos + 600].strip()
        slots.append({
            "marker": match.group(0),
            "alt": alt if alt else "",
            "position": pos,
            "context_before": clean_markdown(ctx_before[-300:]),
            "context_after": clean_markdown(ctx_after[:300]),
        })

    # 按位置排序
    slots.sort(key=lambda x: x["position"])
    return slots


def clean_markdown(text):
    """去除 Markdown 标记，保留纯文本"""
    patterns = [
        (r'#{1,3}\s+', ''),       # 标题标记
        (r'\*\*([^*]+)\*\*', r'\1'),  # 粗体
        (r'\*([^*]+)\*', r'\1'),       # 斜体
        (r'`[^`]+`', ''),              # 行内代码
        (r'>\s+', ''),                 # 引用
        (r'\[([^\]]+)\]\([^)]+\)', r'\1'),  # 链接
        (r'\n+', ' '),                 # 换行变空格
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text.strip()


def extract_title(md_text):
    """尝试从 Markdown 中提取文章标题"""
    patterns = [
        r'^#\s+(.+)$',
        r'^##\s+(.+)$',
    ]
    for pattern in patterns:
        m = re.search(pattern, md_text, re.MULTILINE)
        if m:
            return m.group(1).strip()
    return ""


def generate_cover_prompt(slot, cover_style, article_title=""):
    """根据头图风格生成封面 prompt"""
    tmpl = cover_style.get("prompt_template", {})
    sizes = cover_style.get("sizes", {})
    size_cfg = sizes.get("cover", {"width": 900, "height": 383})

    # 内容描述：优先用文章标题，其次用 alt
    content = article_title or slot.get("alt", "") or "article cover"

    parts = [
        f"Cover image for article: {content}",
        tmpl.get("subject", ""),
        tmpl.get("style", ""),
        tmpl.get("background", ""),
        tmpl.get("composition", ""),
        tmpl.get("text_element", ""),
    ]

    prompt = ", ".join(p for p in parts if p)
    negative = tmpl.get("negative", "")

    return {
        "prompt": prompt,
        "negative": negative,
        "width": size_cfg.get("width", 900),
        "height": size_cfg.get("height", 383),
        "size": f"{size_cfg.get('width', 900)}x{size_cfg.get('height', 383)}",
    }


def generate_illustration_prompt(slot, image_style):
    """根据插图风格生成文章内配图 prompt"""
    tmpl = image_style.get("prompt_template", {})
    sizes = image_style.get("sizes", {})
    size_cfg = sizes.get("illustration", {"width": 1024, "height": 768})

    # 内容描述：优先用 alt，其次从上下文提取
    content_desc = slot.get("alt", "")
    if not content_desc or content_desc == "placeholder":
        context = slot.get("context_before", "") + " " + slot.get("context_after", "")
        content_desc = context[:120].strip() if context else "illustration"

    parts = [
        content_desc,
        tmpl.get("style", ""),
        tmpl.get("elements", ""),
        tmpl.get("background", ""),
        tmpl.get("color_scheme", ""),
        tmpl.get("composition", ""),
        "4:3 aspect ratio, high quality illustration",
    ]

    prompt = ". ".join(p for p in parts if p)
    negative = tmpl.get("negative", "")

    return {
        "prompt": prompt,
        "negative": negative,
        "width": size_cfg.get("width", 1024),
        "height": size_cfg.get("height", 768),
        "size": f"{size_cfg.get('width', 1024)}x{size_cfg.get('height', 768)}",
    }


def main():
    parser = argparse.ArgumentParser(
        description="配图 Prompt 智能生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("input", nargs="?", default=None, help="文章 Markdown 文件路径")
    parser.add_argument("-s", "--style", default=DEFAULT_STYLE,
                        help=f"插图风格名称（默认: {DEFAULT_STYLE}）")
    parser.add_argument("-o", "--output", default=None,
                        help="输出 YAML/JSON 路径（默认: output/image_prompts.yaml）")
    parser.add_argument("--list", action="store_true",
                        help="列出所有可用风格")

    args = parser.parse_args()

    # 列出风格
    if args.list:
        list_available_styles()
        return

    # 需要输入文件时必须提供
    if not args.input:
        print("❌ 请提供文章 Markdown 文件路径")
        print("   或使用 --list 查看可用风格")
        list_available_styles()
        sys.exit(1)

    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 加载风格
    styles = load_image_styles()
    if args.style not in styles:
        print(f"❌ 未知风格: {args.style}")
        print(f"   可用风格: {', '.join(styles.keys()) or '（无）'}")
        list_available_styles()
        sys.exit(1)

    style_cfg = styles[args.style]
    article_title = extract_title(md_text)
    slots = extract_image_slots(md_text)

    if not slots:
        print("⚠️  文章中没有找到插图标记")
        print("   请在需要配图的位置添加：")
        print("   【配图：图片描述文字】")
        print("   或")
        print("   ![图片描述](placeholder)")
        sys.exit(0)

    print(f"\n📄 分析文章: {args.input}")
    print(f"🎨 配图风格: {args.style} — {style_cfg.get('description', '')}")
    print(f"📝 发现 {len(slots)} 个配图位置\n")

    results = []
    output_parts = []

    for i, slot in enumerate(slots):
        is_cover = (i == 0)
        img_type = "cover" if is_cover else f"illustration_{i}"

        if is_cover:
            prompt_data = generate_cover_prompt(slot, style_cfg, article_title)
        else:
            prompt_data = generate_illustration_prompt(slot, style_cfg)

        filename = f"cover.png" if is_cover else f"illustration_{i}.png"

        result = {
            "index": i,
            "type": img_type,
            "alt": slot.get("alt", ""),
            "context": slot.get("context_before", "")[-100:] + " ... " + slot.get("context_after", "")[:100],
            "filename": filename,
            "size": prompt_data["size"],
            "width": prompt_data["width"],
            "height": prompt_data["height"],
            "prompt": prompt_data["prompt"],
            "negative": prompt_data["negative"],
        }
        results.append(result)

        tag = "🖼️ 头图" if is_cover else f"📷 插图{i}"
        print(f"{tag} ({filename})")
        print(f"   描述: {slot.get('alt', '(从上下文提取)')}")
        print(f"   尺寸: {prompt_data['size']}")
        print(f"   Prompt: {prompt_data['prompt'][:80]}...")
        if prompt_data.get("negative"):
            print(f"   Negative: {prompt_data['negative'][:60]}...")
        print()

    # 输出文件
    output_path = args.output or os.path.join(ROOT_DIR, "output", "image_prompts.yaml")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 支持 YAML 或 JSON 输出
    ext = os.path.splitext(output_path)[1].lower()
    with open(output_path, "w", encoding="utf-8") as f:
        if ext == ".json":
            json.dump(results, f, ensure_ascii=False, indent=2)
        else:
            yaml.dump(results, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ 已生成 {len(results)} 个配图 prompt")
    print(f"📁 输出: {output_path}")
    print(f"\n💡 提示: 将 prompt 复制到图像生成工具（如 Midjourney、DALL-E、Stable Diffusion）即可生成配图")


if __name__ == "__main__":
    main()
