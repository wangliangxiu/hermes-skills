#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章写作 Skill — 排版格式化工具
将普通 Markdown 文稿转换为符合公众号规范的排版版本

用法：
    python format_article.py <输入文件> [--output 输出文件]
    python format_article.py --text "文章内容..." [--output 输出文件]
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# 排版规则配置
# ──────────────────────────────────────────────────────────────
INTERACTION_FOOTER = """
---

> 💬 **看完有什么想说的？欢迎在留言区告诉我～**
> 觉得有用的话，顺手转发给需要的朋友 👇
"""

MAX_PARAGRAPH_LENGTH = 150  # 超过此长度的段落给出警告


def format_headings(text: str) -> str:
    """
    统一标题层级：
    - 文章标题（# 级别）保留但加注释提醒
    - 一级小节用 ##
    - 二级小节用 ###
    避免出现 #### 及更深层级（公众号不建议）
    """
    lines = text.split('\n')
    result = []
    for line in lines:
        # 超过4级标题的，拍平到 ###
        if line.startswith('####'):
            line = '###' + line.lstrip('#')
        result.append(line)
    return '\n'.join(result)


def ensure_heading_spacing(text: str) -> str:
    """确保标题前后有空行"""
    # 标题前加空行
    text = re.sub(r'([^\n])\n(#{1,3} )', r'\1\n\n\2', text)
    # 标题后加空行
    text = re.sub(r'(#{1,3} [^\n]+)\n([^\n#])', r'\1\n\n\2', text)
    return text


def split_long_paragraphs(text: str) -> str:
    """
    检测过长段落（超过150字的纯文本段落），
    尝试在句号/感叹号/问号处自动断行，给出提示。
    """
    paragraphs = text.split('\n\n')
    result = []
    warnings = []

    for i, para in enumerate(paragraphs):
        # 跳过标题、代码块、列表、引用
        stripped = para.strip()
        if (stripped.startswith('#') or stripped.startswith('```')
                or stripped.startswith('-') or stripped.startswith('>')
                or stripped.startswith('|') or stripped.startswith('!')):
            result.append(para)
            continue

        # 计算纯文字长度（去掉 Markdown 标记）
        clean = re.sub(r'\*{1,2}|_{1,2}|`', '', stripped)
        if len(clean) > MAX_PARAGRAPH_LENGTH:
            warnings.append(
                f'⚠️  第 {i+1} 段落长度 {len(clean)} 字，超过建议上限 {MAX_PARAGRAPH_LENGTH} 字'
            )
            # 尝试在句尾标点处断行
            split_para = re.sub(r'([。！？])\s*(?=[^）\s])', r'\1\n\n', stripped)
            result.append(split_para)
        else:
            result.append(para)

    if warnings:
        result.insert(0, '<!-- 排版警告（发布前请检查）\n' + '\n'.join(warnings) + '\n-->\n')

    return '\n\n'.join(result)


def normalize_emphasis(text: str) -> str:
    """
    检查加粗使用是否过度：
    每段最多2处加粗，超出的加注释提示。
    """
    paragraphs = text.split('\n\n')
    result = []
    for para in paragraphs:
        bold_count = len(re.findall(r'\*\*[^*]+\*\*', para))
        if bold_count > 2:
            # 在段落末加提示
            para += f'  <!-- ⚠️ 本段加粗 {bold_count} 处，建议保留最重要的 1-2 处 -->'
        result.append(para)
    return '\n\n'.join(result)


def add_interaction_footer(text: str) -> str:
    """确保文章末尾有互动引导语（避免重复添加）"""
    footer_marker = '💬'
    if footer_marker not in text:
        text = text.rstrip() + '\n\n' + INTERACTION_FOOTER
    return text


def check_image_placeholders(text: str) -> list:
    """
    检查文中是否有未替换的图片占位符：
    【配图：XXX】 格式
    """
    placeholders = re.findall(r'【配图：([^】]+)】', text)
    return placeholders


def count_words(text: str) -> int:
    """统计正文字数（去掉 Markdown 标记和注释）"""
    # 去掉 HTML 注释
    clean = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # 去掉 Markdown 标记
    clean = re.sub(r'#{1,6} ', '', clean)
    clean = re.sub(r'\*{1,2}|_{1,2}|`{1,3}', '', clean)
    clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean)
    clean = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', clean)
    clean = re.sub(r'[-*>|]', '', clean)
    # 去掉空白字符
    clean = re.sub(r'\s', '', clean)
    return len(clean)


def format_article(text: str) -> tuple[str, dict]:
    """
    执行完整排版流程，返回 (格式化后文本, 报告字典)
    """
    original_words = count_words(text)

    # 依次执行各项排版规则
    text = format_headings(text)
    text = ensure_heading_spacing(text)
    text = split_long_paragraphs(text)
    text = normalize_emphasis(text)
    text = add_interaction_footer(text)

    final_words = count_words(text)
    placeholders = check_image_placeholders(text)

    report = {
        'original_words': original_words,
        'final_words': final_words,
        'image_placeholders': placeholders,
        'image_placeholder_count': len(placeholders),
        'formatted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    return text, report


def print_format_report(report: dict):
    print('\n' + '─' * 50)
    print('📊 排版报告')
    print('─' * 50)
    print(f'  正文字数：{report["final_words"]} 字（原稿 {report["original_words"]} 字）')
    if report['image_placeholders']:
        print(f'\n  🖼️  图片占位符（共 {report["image_placeholder_count"]} 处，发布前替换为实际图片）：')
        for ph in report['image_placeholders']:
            print(f'    ▸ 【配图：{ph}】')
    else:
        print('  ✅ 无未替换的图片占位符')
    print('─' * 50 + '\n')


def main():
    parser = argparse.ArgumentParser(
        description='微信公众号文章排版格式化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例：
  python format_article.py draft.md
  python format_article.py draft.md --output final.md
        '''
    )
    parser.add_argument('input', nargs='?', help='输入 Markdown 文件路径')
    parser.add_argument('--text', help='直接传入文章文本（与 input 二选一）')
    parser.add_argument('--output', '-o', help='输出文件路径（默认打印到终端）')
    args = parser.parse_args()

    # 读取输入
    if args.text:
        raw_text = args.text
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f'❌ 文件不存在：{args.input}')
            sys.exit(1)
        raw_text = input_path.read_text(encoding='utf-8')
    else:
        # 从 stdin 读取
        print('请输入文章内容（Ctrl+Z 结束）：')
        raw_text = sys.stdin.read()

    formatted, report = format_article(raw_text)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(formatted, encoding='utf-8')
        print(f'✅ 已保存到：{output_path}')
    else:
        print(formatted)

    print_format_report(report)


if __name__ == '__main__':
    main()
