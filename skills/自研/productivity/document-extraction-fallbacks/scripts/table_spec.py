# -*- coding: utf-8 -*-
"""量取 PDF 里某张表的格式规格 —— 照抄原文件格式（列、表头分格、行高列宽、表外小字缩进）时用。

输出：行列网格、每格跨几列跨几行（靠 extract() 里的 None 判断合并）、列宽行高（pt 与 mm）、
     表格外框位置、表格外文字行（注/说明/备注那行）与表格左边缘的距离（＝缩进）。

用法：python table_spec.py <pdf路径> <页号(从1起)> [表序号，默认0]
"""
import sys, io
import fitz

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    pdf, page_no = sys.argv[1], int(sys.argv[2])
    tno = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    d = fitz.open(pdf)
    pg = d[page_no - 1]
    tabs = pg.find_tables()
    print(f'文件：{pdf}\n第 {page_no} 页：检出 {len(tabs.tables)} 张表')
    if not tabs.tables:
        return
    t = tabs.tables[tno]
    grid = t.extract()

    xs = sorted({round(c[0], 2) for c in t.cells} | {round(c[2], 2) for c in t.cells})
    ys = sorted({round(c[1], 2) for c in t.cells} | {round(c[3], 2) for c in t.cells})
    ncol = len(xs) - 1
    nrow = len(grid)
    print(f'网格：{nrow} 行 × {ncol} 列')
    print('列宽(pt=mm)：' + ', '.join(
        f'{xs[i+1]-xs[i]:.1f}={ (xs[i+1]-xs[i])*0.3528:.1f}mm' for i in range(ncol)))
    print('行高(pt=mm)：' + ', '.join(
        f'{ys[i+1]-ys[i]:.1f}={ (ys[i+1]-ys[i])*0.3528:.1f}mm' for i in range(nrow)))

    print('\n单元格文本（None＝被合并 / 续格：据此判断每格跨几列、跨几行）：')
    for r, row in enumerate(grid[:8]):
        print(f'  row{r}: {row}')

    x0, y0, x1, y1 = t.bbox
    print(f'\n表格外框：x0={x0:.1f} y0={y0:.1f} x1={x1:.1f} y1={y1:.1f} '
          f'(宽 {x1-x0:.1f}pt / {(x1-x0)*0.3528:.1f}mm)')
    print('表格外的文字行（找"注 / 说明 / 备注"那行；距表左距离 ÷ 字号 ≈ 首行缩进几个字符）：')
    for b in pg.get_text('dict')['blocks']:
        if b.get('type') != 0:
            continue
        for ln in b['lines']:
            txt = ''.join(s['text'] for s in ln['spans']).strip()
            if not txt:
                continue
            lx0, ly0 = ln['bbox'][0], ln['bbox'][1]
            inside = (x0 - 1 <= lx0 <= x1 + 1) and (y0 - 1 <= ly0 <= y1 + 1)
            if not inside:
                size = ln['spans'][0]['size']
                gap = lx0 - x0
                print(f'  x0={lx0:.1f}（距表左 {gap:+.1f}pt ≈ {gap/size:.1f} 字符）'
                      f' 字号={size:.1f} | {txt[:60]}')


main()
