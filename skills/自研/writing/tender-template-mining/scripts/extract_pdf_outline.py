# -*- coding: utf-8 -*-
"""招标文件 PDF 的结构与文本提取（pymupdf / fitz）。

用法：
  python extract_pdf_outline.py info <文件.pdf>
  python extract_pdf_outline.py dump <文件.pdf> <out.txt> [起页] [止页]
  python extract_pdf_outline.py find <文件.pdf> <关键词> [关键词...]

info：页数、内置书签（前 60 条）、文本量极低的页（多半是扫描图/空白表）
dump：按 "===== PAGE n =====" 分页落盘 UTF-8 文本
find：在逐页文本里找关键词，打印页码与命中行
"""
import sys

import fitz


def cmd_info(path):
    doc = fitz.open(path)
    print('页数', doc.page_count)
    toc = doc.get_toc()
    print('内置书签', len(toc))
    for lv, title, pg in toc[:60]:
        print('%s%s -> p%s' % ('  ' * (lv - 1), title[:80], pg))
    thin = [i + 1 for i in range(doc.page_count)
            if len(doc[i].get_text().strip()) < 20]
    print('文本量极低的页', len(thin), thin[:30])


def cmd_dump(path, out, a=1, b=None):
    doc = fitz.open(path)
    b = b or doc.page_count
    chunks = []
    for i in range(a - 1, min(b, doc.page_count)):
        chunks.append('\n===== PAGE %d =====\n' % (i + 1) + doc[i].get_text())
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(''.join(chunks))
    print(out, len(chunks), '页')


def cmd_find(path, kws):
    doc = fitz.open(path)
    for i in range(doc.page_count):
        hits = [ln.strip() for ln in doc[i].get_text().splitlines()
                if any(k in ln for k in kws)]
        if hits:
            print('p%d:' % (i + 1), ' | '.join(hits[:6]))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    mode, path = sys.argv[1], sys.argv[2]
    if mode == 'info':
        cmd_info(path)
    elif mode == 'dump':
        a = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        b = int(sys.argv[5]) if len(sys.argv) > 5 else None
        cmd_dump(path, sys.argv[3], a, b)
    elif mode == 'find':
        cmd_find(path, sys.argv[3:])
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
