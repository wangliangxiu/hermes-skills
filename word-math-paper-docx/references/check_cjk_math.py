# -*- coding: utf-8 -*-
"""排版前必跑：检查内容模块的 $...$ 公式里是否夹了汉字。
（公式按 Cambria Math 渲染，没汉字 → Word 回退到 MS Mincho，PDF 里会出现怪字/方框）

用法：python check_cjk_math.py paper6 paper7
命中必须为 0 才能排版。

注意：一定要落盘成 .py 再跑。内联 python -c 或 heredoc 里的 \$ 与反斜杠会被 shell 吃掉一层，
会得到假阴性（实战：内联版报告 0 处，落盘版才查出真问题）。
"""
import re, sys, importlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.getcwd())
sys.path.insert(0, HERE)
CJK = re.compile('[\u4e00-\u9fff]')


def segs(s):
    """按 $ 切成文字段/公式段，返回公式段"""
    parts = str(s).split('$')
    return [parts[i] for i in range(1, len(parts), 2)]


def scan(mod):
    m = importlib.import_module(mod)
    bad = []

    def chk(tag, s):
        if not isinstance(s, str):
            return
        for seg in segs(s):
            if CJK.search(seg):
                bad.append((tag, seg.strip()[:70]))

    for t in getattr(m, 'HEAD', []):
        chk('HEAD', t if isinstance(t, str) else t[-1])
    for attr in ('CHOICE', 'FILL', 'SOLVE'):
        for q in getattr(m, attr, []):
            chk(attr + '.stem', q.get('stem', ''))
            for o in q.get('opts', []):
                chk(attr + '.opt', o)
            for s in q.get('sol', []):
                chk(attr + '.sol', s)
            chk(attr + '.ans', q.get('ans'))
    print('=== %s：公式里夹中文 %d 处' % (mod, len(bad)))
    for t, s in bad:
        print('   [%s] %s' % (t, s))
    return len(bad)


if __name__ == '__main__':
    tot = sum(scan(m) for m in sys.argv[1:])
    print('\n合计 %d 处（必须全部为 0）' % tot)
