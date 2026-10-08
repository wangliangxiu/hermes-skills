# -*- coding: utf-8 -*-
"""用 Visio COM 画组织机构图 → .vsdx（原生可编辑）+ PNG 预览。

画法（按用户要求）：每排"上横线进 + 下横线收 + 中间单线下接"；最底排不收口。
用法: python visio_org_chart.py <输出目录>
注意: 跑之前先关掉 Visio（Dispatch 会接管已打开的实例，结尾 Quit 会把用户窗口一起关掉）。
"""
import os
import sys

import win32com.client as wc

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
os.makedirs(OUT, exist_ok=True)
VSDX = os.path.join(OUT, '组织机构图.vsdx')

# ==================== 可改参数 ====================
PROJ = '××工程项目部'
LEAD = ['技术负责人\n（总工）', '安全负责人\n（安全总监）', '项目副经理', '总经济师', '总会计师', '总机械师']
DEPT = ['工程技术部', '安全质量部', '物资设备部', '计划合同部', '财务部', '综合办公室', '工地试验室', '测量队']
NGQ = 6                                     # 工区数：招标文件划几个就画几个
CN = list('一二三四五六七八九十')
GQ = [f'第{CN[i]}工区' for i in range(NGQ)]
CHAIN = ['工区经理', '工区领导班子', '工区各部室', '各施工队', '各作业班组']
NOTE = '说明：层级与岗位按招标文件要求与投标单位实际组织确定；没有的岗位不写。'
# =================================================

MM = 1 / 25.4                               # Visio 内部单位是英寸
PW, PH = 420, 297                           # A3 横向
MX, MY = 8, 8
UX, UY = 100.0, 74.0                        # 内部"格"坐标
X0, X1 = 8, 92
GAP = 1.1


def X(u):
    return (MX + u / UX * (PW - 2 * MX)) * MM


def Y(u):
    return (MY + u / UY * (PH - 2 * MY)) * MM


app = wc.Dispatch('Visio.Application')
app.Visible = False
try:
    app.AlertResponse = 7
except Exception:
    pass
doc = app.Documents.Add('')
try:
    FONT = str(doc.Fonts.ItemU('微软雅黑').ID)
except Exception:
    FONT = None


def rect(pg, cx, cy, w, h, text, fs=10, fill='RGB(255,255,255)', bold=False, round_mm='1.5 mm'):
    s = pg.DrawRectangle(X(cx - w / 2), Y(cy - h / 2), X(cx + w / 2), Y(cy + h / 2))
    s.Text = text
    s.CellsU('Rounding').FormulaU = round_mm
    s.CellsU('FillForegnd').FormulaU = fill
    s.CellsU('Char.Size').FormulaU = f'{fs} pt'
    if FONT:
        s.CellsU('Char.Font').FormulaU = FONT
    if bold:
        s.CellsU('Char.Style').FormulaU = '1'
    s.CellsU('VerticalAlign').FormulaU = '1'
    s.CellsU('Para.HorzAlign').FormulaU = '1'
    return s


def line(pg, x1, y1, x2, y2):
    return pg.DrawLine(X(x1), Y(y1), X(x2), Y(y2))


def row(pg, items, y, h, w, fs, fill, bus_top, lower_bus=True):
    """一排：上横线（进，每格接上）+ 下横线（收，每格接下）；返回 (xs, 下横线y)"""
    n = len(items)
    xs = [X0 + i * ((X1 - X0) / (n - 1)) for i in range(n)] if n > 1 else [(X0 + X1) / 2]
    bb = y - h / 2 - GAP
    for x, t in zip(xs, items):
        rect(pg, x, y, w, h, t, fs=fs, fill=fill)
        line(pg, x, bus_top, x, y + h / 2)
        if lower_bus:
            line(pg, x, y - h / 2, x, bb)
    line(pg, xs[0], bus_top, xs[-1], bus_top)
    if lower_bus:
        line(pg, xs[0], bb, xs[-1], bb)
    return xs, bb


pg = doc.Pages.Item(1)
pg.PageSheet.CellsU('PageWidth').FormulaU = f'{PW} mm'
pg.PageSheet.CellsU('PageHeight').FormulaU = f'{PH} mm'
pg.PageSheet.CellsU('PrintPageOrientation').FormulaU = '2'

rect(pg, 50, 72.4, 40, 3.6, '组织机构框图', fs=14, bold=True, round_mm='6 mm',
     fill='RGB(232,238,248)')
rect(pg, 50, 67.4, 56, 4.0, PROJ, fs=12, bold=True, fill='RGB(232,238,248)')
line(pg, 50, 65.4, 50, 63.4)
rect(pg, 50, 61.4, 20, 4.0, '项目经理', fs=12, bold=True, fill='RGB(220,230,245)')
line(pg, 50, 59.4, 50, 57.0)

_, bb = row(pg, LEAD, 53.6, 4.0, 14.6, 9.5, 'RGB(247,249,252)', bus_top=57.0)
line(pg, 50, bb, 50, 47.4)
_, bb = row(pg, DEPT, 44.0, 4.0, 11.0, 9, 'RGB(251,251,251)', bus_top=47.4)
line(pg, 50, bb, 50, 37.8)

xs_gq, _ = row(pg, GQ, 34.4, 4.0, 14.6, 11, 'RGB(232,238,248)', bus_top=37.8, lower_bus=False)
ys = [29.0 - i * 4.6 for i in range(len(CHAIN))]
for k, (name, y) in enumerate(zip(CHAIN, ys)):
    for x in xs_gq:
        rect(pg, x, y, 14.6, 3.2, name, fs=9.5,
             fill='RGB(234,240,250)' if k == 0 else 'RGB(255,255,255)')
        line(pg, x, (34.4 - 2.0 if k == 0 else ys[k - 1] - 1.6), x, y + 1.6)

rect(pg, 50, 2.2, 84, 2.6, NOTE, fs=9)

doc.SaveAs(VSDX)
print('已保存:', VSDX)
png = os.path.join(OUT, '组织机构图.png')
doc.Pages.Item(1).Export(png)
print('已导出:', png)
app.Quit()
