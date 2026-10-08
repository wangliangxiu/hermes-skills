#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章写作 Skill — 素材加载器
用法：python load_materials.py <素材目录路径> [--json]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 可选：图片分析（需要 pillow）
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ──────────────────────────────────────────
# 文件类型分类
# ──────────────────────────────────────────
TEXT_EXTENSIONS = {'.md', '.txt', '.docx', '.doc'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff'}
TEMPLATE_KEYWORDS = ['template', '模板', 'Template', 'TEMPLATE']
OUTLINE_KEYWORDS = ['outline', '大纲', '提纲', 'Outline', 'OUTLINE']
REFERENCE_KEYWORDS = ['ref', 'reference', '参考', '文献', 'Reference']


def classify_file(filepath: Path) -> str:
    """判断文件类型"""
    suffix = filepath.suffix.lower()
    name = filepath.stem.lower()

    if suffix in IMAGE_EXTENSIONS:
        return 'image'

    if suffix in TEXT_EXTENSIONS:
        # 进一步细分文字文件
        for kw in TEMPLATE_KEYWORDS:
            if kw.lower() in name:
                return 'template'
        for kw in OUTLINE_KEYWORDS:
            if kw.lower() in name:
                return 'outline'
        for kw in REFERENCE_KEYWORDS:
            if kw.lower() in name:
                return 'reference'
        return 'text'

    return 'other'


def read_text_file(filepath: Path, max_chars: int = 3000) -> str:
    """读取文本文件内容（前 max_chars 字符）"""
    encodings = ['utf-8', 'gbk', 'utf-8-sig', 'gb2312']
    for enc in encodings:
        try:
            content = filepath.read_text(encoding=enc)
            if len(content) > max_chars:
                return content[:max_chars] + f'\n\n... [内容已截断，原文共 {len(content)} 字]'
            return content
        except (UnicodeDecodeError, PermissionError):
            continue

    # 尝试 docx
    if filepath.suffix.lower() in ('.docx', '.doc'):
        try:
            import docx
            doc = docx.Document(str(filepath))
            text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
            return text[:max_chars] + ('...' if len(text) > max_chars else '')
        except Exception:
            return '[无法读取 Word 文档，请手动提供文本内容]'

    return '[文件读取失败]'


def analyze_image(filepath: Path) -> dict:
    """分析图片基本信息"""
    info = {
        'filename': filepath.name,
        'size_kb': round(filepath.stat().st_size / 1024, 1),
        'dimensions': None,
        'description': f'图片文件：{filepath.name}',
    }
    if PIL_AVAILABLE:
        try:
            with Image.open(filepath) as img:
                info['dimensions'] = f'{img.width}×{img.height}'
                info['mode'] = img.mode
                info['description'] = (
                    f'图片：{filepath.name}，尺寸 {img.width}×{img.height}，'
                    f'大小 {info["size_kb"]}KB'
                )
        except Exception:
            pass
    return info


def scan_directory(directory: str) -> dict:
    """
    扫描素材目录，返回结构化的素材摘要。
    """
    root = Path(directory)
    if not root.exists():
        return {'error': f'目录不存在：{directory}'}
    if not root.is_dir():
        return {'error': f'路径不是目录：{directory}'}

    result = {
        'directory': str(root.resolve()),
        'scanned_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'templates': [],
            'outlines': [],
            'texts': [],
            'images': [],
            'references': [],
            'others': [],
        },
        'total_files': 0,
        'writing_hints': [],
    }

    # 递归扫描（不超过2层深度）
    for filepath in sorted(root.rglob('*')):
        if not filepath.is_file():
            continue
        # 跳过隐藏文件
        if filepath.name.startswith('.'):
            continue

        result['total_files'] += 1
        ftype = classify_file(filepath)
        file_info = {
            'path': str(filepath),
            'name': filepath.name,
            'size_kb': round(filepath.stat().st_size / 1024, 1),
        }

        if ftype == 'template':
            file_info['content'] = read_text_file(filepath)
            result['summary']['templates'].append(file_info)
        elif ftype == 'outline':
            file_info['content'] = read_text_file(filepath)
            result['summary']['outlines'].append(file_info)
        elif ftype == 'text':
            file_info['content'] = read_text_file(filepath, max_chars=2000)
            result['summary']['texts'].append(file_info)
        elif ftype == 'image':
            file_info.update(analyze_image(filepath))
            result['summary']['images'].append(file_info)
        elif ftype == 'reference':
            file_info['content'] = read_text_file(filepath, max_chars=1500)
            result['summary']['references'].append(file_info)
        else:
            result['summary']['others'].append(file_info)

    # 生成写作建议
    s = result['summary']
    if s['templates']:
        result['writing_hints'].append(
            f'✅ 发现 {len(s["templates"])} 个模板文件，写作时将严格遵循模板结构。'
        )
    if s['outlines']:
        result['writing_hints'].append(
            f'✅ 发现 {len(s["outlines"])} 个大纲文件，将以此为骨架展开正文。'
        )
    if s['images']:
        result['writing_hints'].append(
            f'🖼️  发现 {len(s["images"])} 张图片素材，写作时将在合适位置标注配图。'
        )
    if s['texts']:
        result['writing_hints'].append(
            f'📄 发现 {len(s["texts"])} 个文字素材，已提取关键内容。'
        )
    if s['references']:
        result['writing_hints'].append(
            f'📚 发现 {len(s["references"])} 个参考文献文件，将用于支撑文中数据和结论。'
        )
    if not any([s['templates'], s['outlines'], s['texts'], s['images']]):
        result['writing_hints'].append('⚠️  未发现可识别的素材文件，建议直接提供主题进行创作。')

    return result


def print_report(data: dict):
    """打印人类可读的素材报告"""
    if 'error' in data:
        print(f'❌ 错误：{data["error"]}')
        return

    print(f'\n{"="*60}')
    print(f'📁 素材目录：{data["directory"]}')
    print(f'🕐 扫描时间：{data["scanned_at"]}')
    print(f'📊 共发现 {data["total_files"]} 个文件')
    print(f'{"="*60}\n')

    s = data['summary']

    if s['templates']:
        print(f'【模板文件】×{len(s["templates"])}')
        for f in s['templates']:
            print(f'  📋 {f["name"]} ({f["size_kb"]}KB)')
            print(f'     前200字：{f["content"][:200].strip()}\n')

    if s['outlines']:
        print(f'【大纲文件】×{len(s["outlines"])}')
        for f in s['outlines']:
            print(f'  📝 {f["name"]} ({f["size_kb"]}KB)')
            print(f'     内容：{f["content"][:300].strip()}\n')

    if s['texts']:
        print(f'【文字素材】×{len(s["texts"])}')
        for f in s['texts']:
            print(f'  📄 {f["name"]} ({f["size_kb"]}KB)')
            print(f'     摘要：{f["content"][:200].strip()}\n')

    if s['images']:
        print(f'【图片素材】×{len(s["images"])}')
        for f in s['images']:
            dims = f.get('dimensions', '未知尺寸')
            print(f'  🖼️  {f["name"]} | {dims} | {f["size_kb"]}KB')

    if s['references']:
        print(f'\n【参考文献】×{len(s["references"])}')
        for f in s['references']:
            print(f'  📚 {f["name"]}')

    print(f'\n{"─"*60}')
    print('✍️  写作建议：')
    for hint in data['writing_hints']:
        print(f'  {hint}')
    print(f'{"─"*60}\n')


def main():
    parser = argparse.ArgumentParser(
        description='微信公众号文章素材加载器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例：
  python load_materials.py C:\\我的素材\\气候变化
  python load_materials.py C:\\我的素材\\量子纠缠 --json
        '''
    )
    parser.add_argument('directory', help='素材目录路径')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出（供程序调用）')
    args = parser.parse_args()

    data = scan_directory(args.directory)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_report(data)


if __name__ == '__main__':
    main()
