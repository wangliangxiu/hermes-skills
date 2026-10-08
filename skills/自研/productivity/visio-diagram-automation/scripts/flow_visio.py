# -*- coding: utf-8 -*-
"""用 Visio COM 画管理流程图（竖向流程 + 判定 + 不合格反馈回路）→ .vsdx + PNG。

判定框（菱形）：优先从流程图模具 BASFLO_U.VSSX 取『判定』母版 page.Drop；
不用 DrawPolyline —— 传 list/tuple 都会报"无效的参数数目"。拿不到母版就退化成方框。
用法: python flow_visio.py <输出目录>
注意: 跑之前先关掉 Visio（Dispatch 会接管已打开的实例，Quit 会关掉用户的窗口）。
"""
import os
import sys

import win32com.client as wc

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
os.makedirs(OUT, exist_ok=True)
VSDX = os.path.join(OUT, '管理流程图.vsdx')

# ================= 可按项目改的流程内容 =================
QUALITY = [
    ('term', '质量目标（含创优目标）'),
    ('process', '建立质量保证体系、质量责任制与考核制度'),
    ('process', '图纸会审、施工方案编制与审批、技术交底'),
    ('process', '原材料、构配件、设备进场检验（含见证取样）'),
    ('decision', '检验合格？'),
    ('process', '工序施工（按方案、交底与作业标准）'),
    ('process', '班组自检 → 工序交接互检 → 专职质检员专检'),
    ('process', '报监理工程师验收（检验批、隐蔽工程）'),
    ('decision', '验收合格？'),
    ('process', '下道工序施工 / 分项、分部工程验收'),
    ('term', '单位工程验收、竣工资料移交与质量回访'),
]
SAFETY = [
    ('term', '安全目标（含文明施工、环保目标）'),
    ('process', '安全生产责任制与安全管理体系、管理制度'),
    ('process', '危险源辨识与风险分级管控（含危大工程清单）'),
    ('process', '专项施工方案编制、审批与专家论证（危大工程）'),
    ('process', '安全教育培训（三级教育、班前讲话、特种作业持证）'),
    ('process', '安全技术交底与作业票证管理'),
    ('process', '现场安全防护设施验收（临边、洞口、用电、机械）'),
    ('process', '日常、定期与专项安全检查、隐患排查'),
    ('decision', '隐患整改闭环？'),
    ('process', '安全考核奖惩、应急预案与演练'),
    ('term', '安全目标实现（事故为零、文明施工达标）'),
]
# 判定节点 → 回到第几段（下标从 0 起），画"否"的回路
LOOPS = {'quality': [(4, 3), (8, 5)], 'safety': [(8, 6)]}
# =====================================================

MM = 1 / 25.4
PW, PH = 297, 420                            # A3 纵向

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

DECISION_MASTER = None
try:
    st = app.Documents.OpenEx('BASFLO_U.VSSX', 64)      # visOpenDocked
    for nm in ('判定', 'Decision'):
        try:
            DECISION_MASTER = st.Masters.ItemU(nm)
            break
        except Exception:
            continue
except Exception:
    DECISION_MASTER = None


def style(s, fs=10, fill='RGB(255,255,255)', bold=False, round_mm=None):
    if round_mm:
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


def mm(v):
    return v * MM


def box(pg, cx, cy, w, h, text, kind='process', fs=10, fill='RGB(247,249,252)'):
    if kind == 'decision' and DECISION_MASTER is not None:
        s = pg.Drop(DECISION_MASTER, mm(cx), mm(cy))
        s.CellsU('Width').FormulaU = f'{w} mm'
        s.CellsU('Height').FormulaU = f'{h} mm'
        style(s, fs=fs, fill=fill)
    else:
        s = pg.DrawRectangle(mm(cx - w / 2), mm(cy - h / 2), mm(cx + w / 2), mm(cy + h / 2))
        style(s, fs=fs, fill=fill, round_mm='6 mm' if kind == 'term' else '1.5 mm',
              bold=(kind == 'term'))
    s.Text = text
    return s


def arrow(pg, x1, y1, x2, y2):
    s = pg.DrawLine(mm(x1), mm(y1), mm(x2), mm(y2))
    s.CellsU('EndArrow').FormulaU = '13'
    s.CellsU('LineWeight').FormulaU = '0.75 pt'
    return s


def label(pg, cx, cy, text, fs=9):
    s = pg.DrawRectangle(mm(cx - 9), mm(cy - 2.6), mm(cx + 9), mm(cy + 2.6))
    s.CellsU('LinePattern').FormulaU = '0'
    s.CellsU('FillPattern').FormulaU = '0'
    s.Text = text
    style(s, fs=fs)
    return s


def draw(pg, title, steps, loops):
    box(pg, PW / 2, PH - 18, 220, 10, title, kind='term', fs=14, fill='RGB(232,238,248)')
    top, gap, bw, bh = PH - 36, 26, 150, 15
    cx = PW / 2 + 18                     # 主体列右移，左边留回路通道
    ys = []
    for i, (kind, text) in enumerate(steps):
        h = bh + 6 if kind == 'decision' else bh
        y = top - i * gap
        box(pg, cx, y, bw if kind != 'decision' else 118, h, text, kind=kind)
        ys.append(y)
        if i:
            prev = steps[i - 1][0]
            y_from = ys[i - 1] - (bh + 6 if prev == 'decision' else bh) / 2
            arrow(pg, cx, y_from, cx, y + h / 2)
    for idx, back in loops:
        y_dec, y_back = ys[idx], ys[back]
        x_left = cx - (118 if steps[idx][0] == 'decision' else bw) / 2
        x_loop = 16 + idx * 14            # 不同回路走不同竖直通道，别叠在一条线上
        s1 = pg.DrawLine(mm(x_left), mm(y_dec), mm(x_loop), mm(y_dec))
        s1.CellsU('LineWeight').FormulaU = '0.75 pt'
        s2 = pg.DrawLine(mm(x_loop), mm(y_dec), mm(x_loop), mm(y_back))
        s2.CellsU('LineWeight').FormulaU = '0.75 pt'
        arrow(pg, x_loop, y_back, cx - bw / 2, y_back)
        label(pg, x_left - 8, y_dec + 11, '否')
        label(pg, cx + 10, ys[idx] - (bh + 6) / 2 - 6, '是')


pg = doc.Pages.Item(1)
pg.PageSheet.CellsU('PageWidth').FormulaU = f'{PW} mm'
pg.PageSheet.CellsU('PageHeight').FormulaU = f'{PH} mm'
pg.PageSheet.CellsU('PrintPageOrientation').FormulaU = '1'
draw(pg, '质量管理流程图（示意）', QUALITY, LOOPS['quality'])

pg2 = doc.Pages.Add()
pg2.PageSheet.CellsU('PageWidth').FormulaU = f'{PW} mm'
pg2.PageSheet.CellsU('PageHeight').FormulaU = f'{PH} mm'
draw(pg2, '安全管理流程图（示意）', SAFETY, LOOPS['safety'])

doc.SaveAs(VSDX)
print('已保存:', VSDX)
for i in (1, 2):
    p = os.path.join(OUT, f'管理流程图_第{i}页.png')
    doc.Pages.Item(i).Export(p)
    print('已导出:', p)
app.Quit()
