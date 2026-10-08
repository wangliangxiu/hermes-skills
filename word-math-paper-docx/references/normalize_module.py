# -*- coding: utf-8 -*-
"""内容模块归一化：① 两连反斜杠压成一个；② 含反斜杠的非 raw 字符串改成 raw。
用法：python normalize_module.py paper_m3.py
（有矩阵/分段函数需要 \\\\ 的模块别用本工具，或先确认没有误伤）
"""
import sys, re

def fix(path):
    t = open(path, encoding='utf-8').read()
    if '\\begin{' in t:
        print('注意：该模块含 \\\\begin{} 环境，矩阵行分隔符需要两连反斜杠，本工具会跳过压缩。')
        only_raw = True
    else:
        only_raw = False
    n = t.count(chr(92) * 2)
    if not only_raw:
        t = t.replace(chr(92) * 2, chr(92))
    cnt = [0]   # 不再自动补 r 前缀（会把转义引号改坏），非 raw 字符串靠排版前护栏拦住
    open(path, 'w', encoding='utf-8').write(t)
    print('%s：压缩两连反斜杠 %d 处；非 raw 字符串改 raw %d 处' % (path, n, cnt[0]))
    print('  复查：剩余两连反斜杠 =', open(path, encoding='utf-8').read().count(chr(92) * 2))

if __name__ == '__main__':
    for p in sys.argv[1:]:
        fix(p)
