# -*- coding: utf-8 -*-
"""厚 PDF（招标文件这类）速取：页数、书签目录、扫描页检测、按页抽文本、找词。

用 pymupdf（import fitz）。招标文件正文通常有文字层，可直接提取；
书签（get_toc）往往就是现成的章节索引，比翻页快得多。

用法：
  python extract_pdf_outline.py <pdf>                 概览：页数、书签数、文字量异常低（疑似扫描）的页
  python extract_pdf_outline.py <pdf> toc [层级]       列书签（默认到二级）
  python extract_pdf_outline.py <pdf> pages 35 59     抽指定页范围，按 "===== PAGE n =====" 分段
  python extract_pdf_outline.py <pdf> kw 评标 废标      逐页找关键词
"""
import sys

import fitz


def main():
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else ''
    doc = fitz.open(path)

    if mode == 'toc':
        top = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        for lv, title, pg in doc.get_toc():
            if lv <= top:
                print('%s%s -> p%s' % ('  ' * (lv - 1), title[:90], pg))
        return

    if mode == 'pages':
        a, b = int(sys.argv[3]), int(sys.argv[4])
        for p in range(a, min(b, doc.page_count) + 1):
            print('\n===== PAGE %d =====' % p)
            print(doc[p - 1].get_text().strip())
        return

    if mode == 'kw':
        kws = sys.argv[3:]
        for i in range(doc.page_count):
            t = doc[i].get_text()
            hits = [l.strip() for l in t.splitlines() if any(k in l for k in kws)]
            if hits:
                print('p%d: %s' % (i + 1, ' / '.join(hits)[:300]))
        return

    print('页数', doc.page_count, '书签数', len(doc.get_toc()))
    thin = [i + 1 for i in range(doc.page_count) if len(doc[i].get_text().strip()) < 20]
    print('文字量很低的页（疑似扫描/整页图）', len(thin), thin[:30])
    for lv, title, pg in doc.get_toc():
        if lv <= 2:
            print('%s%s -> p%s' % ('  ' * (lv - 1), title[:80], pg))


if __name__ == '__main__':
    main()
