# -*- coding: utf-8 -*-
"""按章抽取超大 docx 的正文（不依赖 python-docx，绕开坏关系项）。

用法（给原生 python 传 Windows 原生路径，别传 /f/... 这种 MSYS 路径）：
  python extract_docx_chapter.py <标书.docx> <起章关键词> <止章关键词> <out.txt>
例：python extract_docx_chapter.py 某施组.docx "第一章" "第二章" ch1.txt
止章关键词传 "-" 表示抽到文末。标题行输出成 # / ## / ### 前缀，正文段原样。
"""
import re
import sys
import zipfile

from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def style_names(z):
    names = {}
    root = etree.fromstring(z.read('word/styles.xml'))
    for s in root.iter(W + 'style'):
        sid = s.get(W + 'styleId')
        n = s.find(W + 'name')
        if sid is not None and n is not None:
            names[sid] = n.get(W + 'val')
    return names


def main():
    path, start_kw, end_kw, out = sys.argv[1:5]
    z = zipfile.ZipFile(path)
    names = style_names(z)
    lines, on = [], False
    with z.open('word/document.xml') as f:
        # 逐段 iterparse；每段处理完清元素并回删前驱，否则十几 MB 的 XML 会吃内存
        for ev, el in etree.iterparse(f, events=('end',), tag=W + 'p'):
            txt = ''.join(t.text or '' for t in el.iter(W + 't')).strip()
            pr = el.find(W + 'pPr')
            sid = None
            if pr is not None:
                ps = pr.find(W + 'pStyle')
                if ps is not None:
                    sid = ps.get(W + 'val')
            nm = (names.get(sid, '') if sid else '') or ''
            m = re.match(r'^(?:heading|Heading|标题)\s*(\d)$', nm)
            lv = int(m.group(1)) if m else 0
            if lv == 1:
                if on and end_kw not in ('-', '') and end_kw in txt:
                    on = False
                elif start_kw in txt:
                    on = True
            if on and txt:
                lines.append('#' * lv + ' ' + txt if lv else txt)
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines))
    print(out, len(lines), '段', sum(len(x) for x in lines), '字')


if __name__ == '__main__':
    main()
