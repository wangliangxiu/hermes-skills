#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章写作 Skill — 标题生成辅助工具
基于话题和文章核心内容，批量生成多风格爆款标题备选

用法：
    python generate_titles.py --topic "睡眠与记忆" --style all
    python generate_titles.py --topic "量子纠缠" --style number,reverse
"""

import argparse
import json
import sys


# ──────────────────────────────────────────────────────────
# 各风格的标题模板（科普/教育类）
# ──────────────────────────────────────────────────────────

TITLE_TEMPLATES = {
    'number': [
        '这{n}个关于{topic}的真相，99%的人都不知道',
        '{n}个被误解了几十年的{topic}知识，今天说清楚',
        '学了{n}年才搞懂的{topic}，原来这么简单',
        '关于{topic}，{n}个问题一次说清楚',
    ],
    'reverse': [
        '你以为自己懂{topic}？科学家说你根本没理解',
        '教科书上关于{topic}的说法，有一半是错的',
        '所有人都在用错的方式理解{topic}',
        '让{topic}颠覆你认知的，是这个你从没想到的角度',
    ],
    'suspense': [
        '一个关于{topic}的发现，让整个领域沉默了30年',
        '被刻意忽略的{topic}真相，今天才能告诉你',
        '没人告诉你的{topic}：一旦知道，你会后悔没早看',
        '{topic}背后，隐藏着一个改变历史的秘密',
    ],
    'practical': [
        '科学验证有效的{topic}方法，99%的人都做错了',
        '不懂这个{topic}原理，你的努力可能都白费了',
        '真正有效的{topic}：从今天起改变这一个习惯',
        '用对了{topic}，效率能提升3倍——这是有研究依据的',
    ],
    'emotion': [
        '我花了10年才明白：{topic}从来不需要天赋',
        '那些真正掌握{topic}的人，都有一个共同特点',
        '关于{topic}，我想对每一个普通人说',
        '为什么懂了{topic}，你的焦虑会少很多',
    ],
    'authority': [
        'MIT研究证明：关于{topic}，你的认知可能是错的',
        '诺贝尔奖得主的研究，彻底改变了我们对{topic}的理解',
        '《自然》杂志最新研究：{topic}的真相远比你想象的更有趣',
        '科学界已达成共识的{topic}：为什么你还不知道？',
    ],
    'story': [
        '一个{topic}的故事，让我重新理解了这个世界',
        '100年前的{topic}实验，至今仍让科学家震惊',
        '他用{topic}改变了世界，但教科书从来不提他的名字',
        '从一个{topic}的问题出发，竟然推翻了整个理论',
    ],
    'trend': [
        '2026年最值得关注的{topic}变化，来了',
        '{topic}正在悄悄改变，你准备好了吗？',
        '未来10年，{topic}会彻底不一样——现在是关键窗口',
        '现在不了解{topic}，5年后你会后悔',
    ],
}

STYLE_NAMES = {
    'number': '数字型',
    'reverse': '反差/纠偏型',
    'suspense': '悬念型',
    'practical': '实用型',
    'emotion': '情感型',
    'authority': '权威背书型',
    'story': '故事型',
    'trend': '趋势型',
}

DEFAULT_N = 3  # 数字模板默认用3


def generate_titles(topic: str, styles: list[str], n: int = DEFAULT_N) -> dict:
    """
    生成多风格标题。
    返回：{style_name: [title1, title2, ...]}
    """
    results = {}
    for style in styles:
        if style not in TITLE_TEMPLATES:
            continue
        templates = TITLE_TEMPLATES[style]
        generated = []
        for tpl in templates:
            title = tpl.format(topic=topic, n=n)
            generated.append(title)
        results[style] = generated
    return results


def print_titles(topic: str, title_map: dict):
    import sys
    out = sys.stdout
    # Windows 终端输出时避免 emoji 乱码，用 ASCII 替代
    def safe_print(s):
        try:
            print(s)
        except UnicodeEncodeError:
            print(s.encode('ascii', errors='replace').decode('ascii'))

    safe_print(f'\n{"="*60}')
    safe_print(f'[话题] {topic}')
    safe_print(f'{"="*60}')

    all_titles = []
    serial = 1
    for style, titles in title_map.items():
        style_label = STYLE_NAMES.get(style, style)
        safe_print(f'\n[{style_label}]')
        for t in titles:
            safe_print(f'  {serial:2d}. {t}')
            all_titles.append({'serial': serial, 'style': style_label, 'title': t})
            serial += 1

    safe_print(f'\n{"─"*60}')
    safe_print(f'共生成 {len(all_titles)} 个标题备选')
    safe_print('建议：优先测试"数字型"和"实用型"——在科普/教育领域传播率最高')
    safe_print(f'{"─"*60}\n')
    return all_titles


def main():
    parser = argparse.ArgumentParser(
        description='微信公众号爆款标题生成工具（科普/教育类）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
风格选项（逗号分隔，all = 全部）：
  {", ".join(TITLE_TEMPLATES.keys())}

使用示例：
  python generate_titles.py --topic "睡眠与记忆" --style all
  python generate_titles.py --topic "量子纠缠" --style number,story,authority
  python generate_titles.py --topic "专注力训练" --n 5 --json
        '''
    )
    parser.add_argument('--topic', '-t', required=True, help='文章核心话题')
    parser.add_argument(
        '--style', '-s', default='all',
        help='标题风格，逗号分隔或 all（默认：all）'
    )
    parser.add_argument('--n', type=int, default=DEFAULT_N, help='数字型标题中的数字（默认3）')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    args = parser.parse_args()

    if args.style.lower() == 'all':
        styles = list(TITLE_TEMPLATES.keys())
    else:
        styles = [s.strip() for s in args.style.split(',')]

    title_map = generate_titles(args.topic, styles, n=args.n)

    if args.json:
        output = {
            'topic': args.topic,
            'titles': []
        }
        for style, titles in title_map.items():
            for t in titles:
                output['titles'].append({
                    'style': STYLE_NAMES.get(style, style),
                    'title': t,
                })
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_titles(args.topic, title_map)


if __name__ == '__main__':
    main()
