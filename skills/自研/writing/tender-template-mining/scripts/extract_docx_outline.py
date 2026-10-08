# -*- coding: utf-8 -*-
"""提取 .docx（含 100MB 级投标标书）的目录骨架与排版格式。

用法:  python extract_docx_outline.py <file.docx> [out.txt]
默认输出到与 docx 同目录的 <同名>_outline.txt

为什么不用 python-docx: 投标 docx 常带坏的关系项，python-docx 打开会抛
KeyError: "There is no item named 'word/NULL'"；这里直接读 word/document.xml
与 word/styles.xml，只依赖 zipfile + lxml。
"""
import os
import re
import sys
import zipfile
from collections import Counter

from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
DC = 'http://purl.org/dc/elements/1.1/'
CP = 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'

HEAD_RE = re.compile(r'^(?:heading|Heading|标题)\s*(\d)$')
TOC_RE = re.compile(r'^toc\s*(\d)$')
PAGE_RE = re.compile(r'^(.*?)(\d{1,3})$')
STYLE_KEEP_RE = re.compile(
    r'^(?:heading|Heading|标题)\s*\d$|^a$|^Normal$|^Title$|^toc\s*\d$|^Body Text$|表格|图表标题')


def qn(tag):
    return etree.QName(tag).localname


def at(el, name):
    return el.get(W + name) if el is not None else None


def style_summary(s):
    info = {'id': at(s, 'styleId')}
    nm = s.find(W + 'name')
    info['name'] = at(nm, 'val') if nm is not None else ''
    bo = s.find(W + 'basedOn')
    if bo is not None:
        info['basedOn'] = at(bo, 'val')
    rpr = s.find(W + 'rPr')
    if rpr is not None:
        f = rpr.find(W + 'rFonts')
        if f is not None:
            info['font'] = at(f, 'eastAsia') or at(f, 'ascii')
        sz = rpr.find(W + 'sz')
        if sz is not None:
            info['sz_half'] = at(sz, 'val')            # 半点制: 24 = 12pt = 小四
        b = rpr.find(W + 'b')
        if b is not None:
            info['bold'] = at(b, 'val') != '0'
    ppr = s.find(W + 'pPr')
    if ppr is not None:
        jc = ppr.find(W + 'jc')
        if jc is not None:
            info['jc'] = at(jc, 'val')
        sp = ppr.find(W + 'spacing')
        if sp is not None:
            info['spacing'] = {qn(k): v for k, v in sp.attrib.items()}
        ind = ppr.find(W + 'ind')
        if ind is not None:
            info['ind'] = {qn(k): v for k, v in ind.attrib.items()}
    return info


def extract(path, out_path=None):
    if out_path is None:
        out_path = os.path.splitext(path)[0] + '_outline.txt'
    z = zipfile.ZipFile(path)
    names = z.namelist()
    L = []

    def add(s=''):
        L.append(s)

    add('===== 文件 =====')
    add(path)

    add('')
    add('===== 文档属性（Pages/Words 反映体量；creator/lastModifiedBy 是暗标必清项）=====')
    if 'docProps/app.xml' in names:
        r = etree.fromstring(z.read('docProps/app.xml'))
        keep = ('Pages', 'Words', 'Characters', 'Paragraphs', 'TotalTime')
        add('  ' + '  '.join('%s=%s' % (qn(c.tag), (c.text or '').strip())
                             for c in r if isinstance(c.tag, str) and qn(c.tag) in keep))
    if 'docProps/core.xml' in names:
        r = etree.fromstring(z.read('docProps/core.xml'))
        add('  creator=%s' % ''.join(r.xpath('//dc:creator/text()', namespaces={'dc': DC})))
        add('  lastModifiedBy=%s' % ''.join(
            r.xpath('//cp:lastModifiedBy/text()', namespaces={'cp': CP})))

    root = etree.fromstring(z.read('word/document.xml'))   # 17MB XML 量级可直接解析

    add('')
    add('===== 页面设置 sectPr（twips：/20=pt，/567=cm）=====')
    for i, s in enumerate(root.iter(W + 'sectPr')):
        pg, mg = s.find(W + 'pgSz'), s.find(W + 'pgMar')
        d = {}
        if pg is not None:
            d['w'], d['h'], d['orient'] = at(pg, 'w'), at(pg, 'h'), at(pg, 'orient')
        if mg is not None:
            for k in ('top', 'right', 'bottom', 'left', 'header', 'footer'):
                d[k] = at(mg, k)
        add('  [%d] %s' % (i, d))

    add('')
    add('===== 样式表（重点样式；sz 是半点，24=小四 12pt，字体常靠 basedOn 链继承）=====')
    st = etree.fromstring(z.read('word/styles.xml'))
    names_map = {}
    for s in st.iter(W + 'style'):
        sid, nm = at(s, 'styleId'), s.find(W + 'name')
        if sid is not None and nm is not None:
            names_map[sid] = at(nm, 'val')
    for s in st.iter(W + 'style'):
        info = style_summary(s)
        if not STYLE_KEEP_RE.match(info['name'] or ''):
            continue
        add('  %s' % info)

    heads, toc, cnt = [], [], Counter()
    with z.open('word/document.xml') as f:
        for ev, el in etree.iterparse(f, events=('end',), tag=W + 'p'):
            txt = ''.join(t.text or '' for t in el.iter(W + 't')).strip()
            pr = el.find(W + 'pPr')
            sid = None
            if pr is not None:
                ps = pr.find(W + 'pStyle')
                if ps is not None:
                    sid = at(ps, 'val')
            nm = names_map.get(sid, '') if sid else ''
            if txt:
                m = HEAD_RE.match(nm)
                if m:
                    heads.append((int(m.group(1)), txt))
                else:
                    m = TOC_RE.match(nm)
                    if m:
                        toc.append((int(m.group(1)), txt))
            el.clear()
    with z.open('word/document.xml') as f:
        for ev, el in etree.iterparse(f, events=('end',)):
            if isinstance(el.tag, str):
                t = qn(el.tag)
                if t in ('tbl', 'drawing', 'pict'):
                    cnt[t] += 1
            el.clear()

    add('')
    add('===== 标题层级计数（正文实际层级；目录层数常少于它）=====')
    for lv in sorted({h[0] for h in heads}):
        add('  H%d: %d 条   例：%s' % (
            lv, sum(1 for h in heads if h[0] == lv),
            next(h[1] for h in heads if h[0] == lv)))
    add('  表格 %d 个，图形(drawing/pict) %d 个' % (cnt['tbl'], cnt['drawing'] + cnt['pict']))

    add('')
    add('===== 目录（toc 样式逐条；末尾数字是 Word 域记录的页码）=====')
    for lv, txt in toc:
        add('%sT%d %s' % ('  ' * (lv - 1), lv, txt))

    add('')
    add('===== 骨架（剥掉页码，可直接当模板用）=====')
    for lv, txt in toc:
        m = PAGE_RE.match(txt)
        body, page = (m.group(1).rstrip(), m.group(2)) if m else (txt, '')
        add('%s%s%s' % ('    ' * (lv - 1), body, ('   ....' + page) if page else ''))

    add('')
    add('===== 页眉页脚 =====')
    for n in names:
        if re.match(r'word/(header|footer)\d*\.xml$', n):
            r = etree.fromstring(z.read(n))
            add('  %s: %r' % (n, ''.join(t.text or '' for t in r.iter(W + 't')).strip()[:120]))

    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L))
    print('目录 %d 条，标题 %d 条，表格 %d 个' % (len(toc), len(heads), cnt['tbl']))
    print('已写出: %s' % out_path)
    return out_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
