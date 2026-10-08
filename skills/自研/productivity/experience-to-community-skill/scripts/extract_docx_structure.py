# -*- coding: utf-8 -*-
"""超大 .docx 的结构与格式速取（标书这类百 MB 级文件）。

为什么不直接用 python-docx：文件内里的关系项可能指向不存在的部件（例：关系表里挂着 word/NULL），
python-docx 一加载就 KeyError；直接读 zip 里的 word/document.xml 更稳，也更快。

用法：
  python extract_docx_structure.py <docx>                  概览：页数/字数、页面设置、标题层级统计
  python extract_docx_structure.py <docx> toc              目录（toc 1/2/3 样式段落 = 真实目录）
  python extract_docx_structure.py <docx> chap 起 [止]      抽正文（按一级标题关键词定位，止可为空）
  python extract_docx_structure.py <docx> kw 词1 [词2 ...]  按关键词找段落（改稿时定位用）
"""
import re
import sys
import zipfile

from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
HEAD = re.compile(r'^(?:heading|Heading|标题)\s*(\d)$')
TOC = re.compile(r'^toc\s*(\d)$')


def style_names(z):
    """styleId -> 样式名（heading 1 / toc 2 / Normal …）"""
    names = {}
    for s in etree.fromstring(z.read('word/styles.xml')).iter(W + 'style'):
        sid, n = s.get(W + 'styleId'), s.find(W + 'name')
        if sid is not None and n is not None:
            names[sid] = n.get(W + 'val')
    return names


def iter_paras(z):
    """逐段产出 (styleId, 文本)。iterparse + clear 控内存，十几 MB 的 XML 也不炸。"""
    with z.open('word/document.xml') as f:
        for _ev, el in etree.iterparse(f, events=('end',), tag=W + 'p'):
            txt = ''.join(t.text or '' for t in el.iter(W + 't')).strip()
            pr = el.find(W + 'pPr')
            sid = None
            if pr is not None:
                ps = pr.find(W + 'pStyle')
                if ps is not None:
                    sid = ps.get(W + 'val')
            yield sid, txt
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]


def overview(z, names):
    try:
        app = etree.fromstring(z.read('docProps/app.xml'))
        d = {etree.QName(e).localname: (e.text or '') for e in app}
        print('页数 %s / 字数 %s / 字符 %s' % (d.get('Pages'), d.get('Words'), d.get('Characters')))
    except KeyError:
        pass
    doc = etree.fromstring(z.read('word/document.xml'))
    for i, s in enumerate(doc.iter(W + 'sectPr')):
        pg, mg = s.find(W + 'pgSz'), s.find(W + 'pgMar')

        def g(e, k):
            return e.get(W + k) if e is not None else '?'

        print('sectPr[%d] 纸型 %sx%s twips，边距 上%s 左%s（1cm=567twips）'
              % (i, g(pg, 'w'), g(pg, 'h'), g(mg, 'top'), g(mg, 'left')))
    cnt = {}
    for sid, txt in iter_paras(z):
        m = HEAD.match(names.get(sid, '') or '')
        if m and txt:
            lv = int(m.group(1))
            cnt[lv] = cnt.get(lv, 0) + 1
    print('标题层级统计（级:条数）', dict(sorted(cnt.items())))
    print('提示：标题样式常不写字体字号，靠 basedOn 继承正文——查格式要顺 basedOn 链')


def dump_toc(z, names):
    for sid, txt in iter_paras(z):
        m = TOC.match(names.get(sid, '') or '')
        if m and txt:
            print('%s%s' % ('  ' * (int(m.group(1)) - 1), txt))


def dump_chap(z, names, start, end):
    on = False
    for sid, txt in iter_paras(z):
        nm = names.get(sid, '') or ''
        m = HEAD.match(nm)
        lv = int(m.group(1)) if m else 0
        if lv == 1:
            if on and end and end in txt:
                break
            on = start in txt
        if on and txt:
            print(('#' * lv + ' ' + txt) if lv else txt)


def grep(z, kws):
    n = 0
    for _sid, txt in iter_paras(z):
        if txt and any(k in txt for k in kws):
            print('[段]', txt[:400])
            n += 1
    print('匹配段落数', n)


def main():
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else ''
    z = zipfile.ZipFile(path)
    names = style_names(z)
    if mode == 'toc':
        dump_toc(z, names)
    elif mode == 'chap':
        dump_chap(z, names, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else '')
    elif mode == 'kw':
        grep(z, sys.argv[3:])
    else:
        overview(z, names)


if __name__ == '__main__':
    main()
