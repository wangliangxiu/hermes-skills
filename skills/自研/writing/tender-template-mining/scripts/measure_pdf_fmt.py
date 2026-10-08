#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""量一份 PDF（招标文件 / 投标文件）里的格式，用于"照格式原封不动搬"。

用法：
    python measure_pdf_fmt.py <file.pdf> <页码> [<页码2> ...]      # 页码从 1 开始
    python measure_pdf_fmt.py <file.pdf> --toc 280 300             # 只印这个页区间内的书签

输出三块：
  1) 书签（get_toc）——先用它定位章节，别整本灌进上下文
  2) 该页文本 + 每行文字起始 x 与字号（算缩进：字符数 = (该行 x0 - 基准 x0) / 字号）
  3) 该页每张表：网格大小、extract() 的行内容（None = 被合并格占用的续接位）、
     每格推断出的 colspan/rowspan、以及按 bbox 量出的列宽与行高（pt，1pt=0.3528mm）

说明：fitz 的 table.cells 给的是网格单元的 bbox，合并信息在 extract() 的 None 里；
None 表示该格被左邻（横合并）或上邻（纵合并）占用，本脚本按"左邻有值→H、上邻有值→V"推断，
两侧都有值时标成 HV 让人工再看一眼——所以数字报给用户前，跟页面对一眼。
只读，不改原文件；脚本放 $LOCALAPPDATA/Temp，跑完删。
"""
import sys

import fitz  # PyMuPDF

PT2MM = 0.3528


def dump_toc(doc, lo, hi):
    print(f"== 书签（p{lo}-p{hi}）==")
    for lvl, title, page in doc.get_toc():
        if lo <= page <= hi:
            print(f"  p{page}  {'  ' * (lvl - 1)}{title}")


def dump_lines(page):
    dd = page.get_text("dict")
    rows = []
    for block in dd["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            txt = "".join(span["text"] for span in line["spans"])
            if txt.strip():
                size = line["spans"][0]["size"]
                rows.append((line["bbox"][0], size, txt))
    if not rows:
        return
    base = min(r[0] for r in rows)          # 本页最靠左的文字起点，当缩进基准
    for x0, size, txt in rows:
        indent = (x0 - base) / size if size else 0
        print(f"  x0={x0:6.1f} 号={size:4.1f} 缩进={indent:4.1f}字 | {txt[:60]}")


def dump_tables(page):
    tables = page.find_tables()
    if not tables.tables:
        print("  （这一页没识别到表格）")
        return
    for ti, table in enumerate(tables.tables):
        grid = table.extract()
        nrows = len(grid)
        ncols = max(len(r) for r in grid)
        print(f"\n  --- 表 {ti + 1}：{nrows} 行 × {ncols} 列 ---")
        for r, row in enumerate(grid):
            print(f"    row{r}: {row}")

        # 合并推断：None 往左/往上找非空邻居
        print("    合并推断（格 = 行,列 从 0 计）：")
        for r in range(nrows):
            for c in range(ncols):
                val = grid[r][c] if c < len(grid[r]) else None
                if val is None:
                    continue
                colspan = 1
                while (c + colspan < ncols and c + colspan < len(grid[r])
                       and grid[r][c + colspan] is None):
                    colspan += 1
                rowspan = 1
                while (r + rowspan < nrows and c < len(grid[r + rowspan])
                       and grid[r + rowspan][c] is None):
                    rowspan += 1
                if colspan > 1 or rowspan > 1:
                    name = str(val).replace("\n", "")[:16]
                    print(f"      ({r},{c}) {name} → {colspan} 列宽 × {rowspan} 行高")

        xs = sorted({round(cc[0], 2) for cc in table.cells} |
                    {round(cc[2], 2) for cc in table.cells})
        ys = sorted({round(cc[1], 2) for cc in table.cells} |
                    {round(cc[3], 2) for cc in table.cells})
        print("    列宽：" + " / ".join(
            f"{xs[i + 1] - xs[i]:.1f}pt({(xs[i + 1] - xs[i]) * PT2MM:.1f}mm)"
            for i in range(len(xs) - 1)))
        print("    行高：" + " / ".join(
            f"{ys[i + 1] - ys[i]:.1f}pt" for i in range(len(ys) - 1)))
        print(f"    表左边缘 x={xs[0]:.1f}pt（表后"注"的缩进拿它或页边距当基准比）")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    path = argv[1]
    doc = fitz.open(path)
    if argv[2] == "--toc":
        lo, hi = int(argv[3]), int(argv[4])
        dump_toc(doc, lo, hi)
        return 0
    for arg in argv[2:]:
        idx = int(arg) - 1
        page = doc[idx]
        print(f"\n===== PDF 第 {arg} 页（页面 {page.rect.width:.0f}×{page.rect.height:.0f}pt）=====")
        print("-- 文本行与缩进 --")
        dump_lines(page)
        print("-- 表格 --")
        dump_tables(page)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
