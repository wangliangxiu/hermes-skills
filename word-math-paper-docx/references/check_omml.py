# -*- coding: utf-8 -*-
"""公式体检：用 lxml 解析 docx，抽每段 m:oMath 内的文字，查 LaTeX 宏名残留。
抓的是「反斜杠被吃 / 非 raw 字符串转义 / 分词器把公式当文字」这类静默失败。
用法：python check_omml.py <docx ...>
"""
import sys, zipfile, re
from lxml import etree

NS = {'m': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
MT = '{%s}t' % NS['m']
MO = '{%s}oMath' % NS['m']

MACROS = ['dfrac', 'tfrac', 'frac', 'mathrm', 'times', 'cdot', 'div', 'sigma', 'tau',
          'lambda', 'theta', 'mu', 'rho', 'alpha', 'beta', 'gamma', 'delta',
          'varepsilon', 'varphi', 'pi', 'leq', 'geq', 'neq', 'approx', 'partial',
          'sqrt', 'int', 'oint', 'iint', 'iiint', 'sum', 'prod', 'overline',
          'underline', 'vec', 'hat', 'notin', 'infty', 'quad', 'qquad', 'text',
          'limits', 'displaystyle', 'left', 'right']


def check(path):
    xml = zipfile.ZipFile(path).read('word/document.xml')
    root = etree.fromstring(xml)
    bad = []
    oms = list(root.iter(MO))
    for i, om in enumerate(oms):
        s = ''.join(t.text or '' for t in om.iter(MT))
        hit = [m for m in MACROS if re.search(r'(?<![A-Za-z])' + m + r'(?![A-Za-z])', s)]
        if hit:
            bad.append((i, hit, s[:70]))
    print(path)
    print('  公式段数 = %d，宏名残留 = %d' % (len(oms), len(bad)))
    for i, hit, s in bad[:12]:
        print('    [第%d段] 命中 %s <- %s' % (i, ','.join(hit), s))
    return len(bad)


if __name__ == '__main__':
    total = sum(check(p) for p in sys.argv[1:])
    print('\n合计宏名残留 %d 处（必须为 0）' % total)
