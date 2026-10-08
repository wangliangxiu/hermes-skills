# -*- coding: utf-8 -*-
"""从超大/损坏的 docx 里按章取正文（zip + document.xml，绕开 python-docx 对断链关系项的报错）。

用法:
    python docx_text.py <docx 路径>                      # 列出所有以 "第…章" 开头的段落（章节目录）
    python docx_text.py <docx 路径> 第五章 40            # 第五章起 40 段
    python docx_text.py <docx 路径> 第五章 40 1          # 跳过前 1 处命中（目录里那次），落到正文
"""
import sys, io, re, zipfile

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def paragraphs(path):
    """返回正文段落列表（已剔除目录域行）。"""
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', errors='replace')
    out = []
    for p in xml.split('</w:p>'):
        if 'PAGEREF _Toc' in p:          # 目录域行
            continue
        t = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, flags=re.S))
        t = re.sub(r'<[^>]+>', '', t).strip()
        if t:
            out.append(t)
    return out, len(xml)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    key = sys.argv[2] if len(sys.argv) > 2 else None
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    skip = int(sys.argv[4]) if len(sys.argv) > 4 else 1

    paras, xml_len = paragraphs(path)
    print(f'document.xml {xml_len} 字符；正文段落 {len(paras)} 段')

    if not key:                          # 列章节目录
        for i, t in enumerate(paras):
            if re.match(r'^第[一二三四五六七八九十百]+章', t) and len(t) < 60:
                print(f'{i:6d}  {t}')
        return

    hits = [i for i, t in enumerate(paras) if key in t[:40]]
    print(f'“{key}” 命中 {len(hits)} 处，索引 {hits[:8]}')
    if not hits:
        return
    start = hits[min(skip, len(hits) - 1)]
    for t in paras[start:start + limit]:
        print(t[:200])


if __name__ == '__main__':
    main()
