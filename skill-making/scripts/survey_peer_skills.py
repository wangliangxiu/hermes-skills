# -*- coding: utf-8 -*-
"""清点已装技能：SKILL.md 大小分布 + 每个技能的支持文件，用来决定新技能该怎么组织。
用法：python survey_peer_skills.py [技能目录 ...]
默认扫本机两个技能目录。"""
import os, sys, io, statistics

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

roots = sys.argv[1:] or [
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'hermes', 'skills'),
    r'D:\a2e-skills',
]

rows = []
for root in roots:
    if not os.path.isdir(root):
        print('(缺)', root)
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        if 'SKILL.md' not in filenames:
            continue
        rel = os.path.relpath(dirpath, root)
        if rel.count(os.sep) > 2:          # 只看到二级目录
            continue
        txt = open(os.path.join(dirpath, 'SKILL.md'), encoding='utf-8', errors='replace').read()
        sup = []
        for d in sorted(os.listdir(dirpath)):
            full = os.path.join(dirpath, d)
            if os.path.isdir(full):
                sup.append(f'{d}/:{sum(len(f) for _, _, f in os.walk(full))}')
            elif d != 'SKILL.md':
                sup.append(d)
        rows.append((len(txt), txt.count('\n') + 1, rel, sup))

rows.sort(reverse=True)
print(f'共 {len(rows)} 个技能\n')
print('字符数   行数  技能                                支持文件/目录')
print('-' * 120)
for nchar, nline, rel, sup in rows:
    print(f'{nchar:8d} {nline:5d}  {rel[:36]:36s} {" ".join(sup)[:64]}')

chars = [r[0] for r in rows]
if chars:
    print('\nSKILL.md 字符数：中位数 %d，均值 %d，最大 %d，最小 %d' % (
        statistics.median(chars), statistics.mean(chars), max(chars), min(chars)))
    print('超过 10K 的 %d 个；超过 20K 的 %d 个' % (
        sum(1 for c in chars if c > 10000), sum(1 for c in chars if c > 20000)))
