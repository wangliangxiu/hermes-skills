# -*- coding: utf-8 -*-
"""用 Visio（COM 自动化）画组织机构框图 → .vsdx（Visio 原生，可继续编辑）+ PNG 预览。
画法（按使用者教的）：
  每一排：上方一根横线（由上一排单线喂进来），每格方块竖线接到它；
          方块下面再加一根横线把这一排"收"起来，每格方块底边竖线接到它；
          从下面这根横线的中间往下走一根单线，接到下一排的上面那根横线。
  → 上下一排排都能连通，且中间干线不会穿过方块。
第 1 页：项目部组织机构框图（含各工区，工区下面纵向逐层）
第 2 页：工区项目部组织机构框图（工区领导班子 / 部室 / 施工队 / 班组）
用法: python org_chart_visio.py <输出目录>
"""
import sys, os, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import win32com.client as wc

outdir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.environ['LOCALAPPDATA'] + r'\Temp')
os.makedirs(outdir, exist_ok=True)
VSDX = os.path.join(outdir, '组织机构框图.vsdx')
PNGS = [os.path.join(outdir, f'组织机构框图_Visio_第{i}页.png') for i in (1, 2)]

# ==================== 可改参数 ====================
PROJ = '××城际铁路××标段工程项目部'
LEAD = ['技术负责人\n（总工）', '安全负责人\n（安全总监）', '项目副经理', '总经济师', '总会计师', '总机械师']
DEPT = ['工程技术部', '安全质量部', '物资设备部', '计划合同部', '财务部', '综合办公室', '工地试验室', '测量队']
NGQ  = 6
CN   = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
GQ   = [f'第{CN[i]}工区' for i in range(NGQ)]
CHAIN = ['工区经理', '工区领导班子', '工区各部室', '各施工队', '各作业班组']
GQ_LEAD  = ['工区技术负责人', '工区安全负责人', '工区生产副经理', '工区综合管理员']
GQ_DEPT  = ['工程技术组', '安全质量组', '物资设备组', '计划财务组', '工地试验室', '综合办公室']
GQ_TEAM  = ['土方施工队', '桩基施工队', '主体结构施工队', '附属结构施工队']
GQ_CLASS = ['钢筋班', '模板班', '混凝土班', '防水班', '土方运输班', '装饰装修班']
# =================================================

MM = 1 / 25.4
PW, PH = 420, 297            # A3 横向
MX, MY = 8, 8
UX, UY = 100.0, 74.0
G = 1.1                      # 横线离方块的距离（格）

def X(u): return (MX + u / UX * (PW - 2 * MX)) * MM
def Y(u): return (MY + u / UY * (PH - 2 * MY)) * MM

app = None
try:
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

    def new_page(idx):
        pg = doc.Pages.Item(1) if idx == 1 else doc.Pages.Add()
        pg.PageSheet.CellsU('PageWidth').FormulaU = f'{PW} mm'
        pg.PageSheet.CellsU('PageHeight').FormulaU = f'{PH} mm'
        pg.PageSheet.CellsU('PrintPageOrientation').FormulaU = '2'
        return pg

    def rect(pg, cx, cy, w, h, text, fs=10, fill='RGB(255,255,255)', bold=False):
        s = pg.DrawRectangle(X(cx - w/2), Y(cy - h/2), X(cx + w/2), Y(cy + h/2))
        s.Text = text
        s.CellsU('Rounding').FormulaU = '1.2 mm'
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

    def row(pg, items, y, h, w, fs, fill, x0=8, x1=92, bold=False, lower_bus=True):
        """一横排：上方横线（进）+ 下方横线（收）；返回 (xs, 上横线y, 下横线y)"""
        n = len(items)
        xs = [x0 + i * ((x1 - x0) / (n - 1)) for i in range(n)] if n > 1 else [(x0 + x1) / 2]
        bt, bb = y + h/2 + G, y - h/2 - G
        for x, t in zip(xs, items):
            rect(pg, x, y, w, h, t, fs=fs, fill=fill, bold=bold)
            line(pg, x, bt, x, y + h/2)          # 上接
            if lower_bus:
                line(pg, x, y - h/2, x, bb)      # 下收
        line(pg, xs[0], bt, xs[-1], bt)          # 上横线
        if lower_bus:
            line(pg, xs[0], bb, xs[-1], bb)      # 下横线
        return xs, bt, bb

    # ---------------- 第1页：项目部 ----------------
    pg = new_page(1)
    rect(pg, 50, 72.4, 40, 3.6, '项目部组织机构框图（示意）', fs=14, bold=True)
    rect(pg, 50, 67.4, 56, 4.0, PROJ, fs=12, bold=True, fill='RGB(232,238,248)')
    line(pg, 50, 65.4, 50, 63.4)
    rect(pg, 50, 61.4, 20, 4.0, '项目经理', fs=12, bold=True, fill='RGB(220,230,245)')
    line(pg, 50, 59.4, 50, 57.0)
    _, bt_l, bb_l = row(pg, LEAD, 53.6, 4.0, 14.6, 9.5, 'RGB(247,249,252)')       # 领导班子
    line(pg, 50, bb_l, 50, 47.4)                                                  # 单线中接
    _, bt_d, bb_d = row(pg, DEPT, 44.0, 4.0, 11.0, 9, 'RGB(251,251,251)')         # 各部室
    line(pg, 50, bb_d, 50, 37.8)
    xs_gq, bt_g, _ = row(pg, GQ, 34.4, 4.0, 14.6, 11, 'RGB(232,238,248)', lower_bus=False)  # 各工区
    ys = [29.0 - i * 4.6 for i in range(len(CHAIN))]
    for k, (name, y) in enumerate(zip(CHAIN, ys)):
        for x in xs_gq:
            rect(pg, x, y, 14.6, 3.2, name, fs=9.5,
                 fill='RGB(234,240,250)' if k == 0 else 'RGB(255,255,255)')
            line(pg, x, (y + 1.6 + 3.0 if k == 0 else ys[k-1] - 1.6), x, y + 1.6)
    rect(pg, 50, 2.2, 84, 2.6,
         '说明：层级与岗位按本次招标文件要求与投标单位实际组织确定；没有的岗位不写；'
         '不是总承包制就不出现"总承包部"；工区按招标文件划分数量横向画；工区内部各层详见图2。',
         fs=9)

    # ---------------- 第2页：工区项目部 ----------------
    pg = new_page(2)
    rect(pg, 50, 73.0, 50, 3.0, '工区项目部组织机构框图（以第××工区为例，示意）', fs=14, bold=True)
    rect(pg, 50, 69.0, 40, 3.2, '××项目部（上级）', fs=11.5, bold=True, fill='RGB(232,238,248)')
    line(pg, 50, 67.4, 50, 65.4)
    rect(pg, 50, 63.4, 26, 3.8, '工区经理', fs=12, bold=True, fill='RGB(220,230,245)')
    line(pg, 50, 61.5, 50, 60.7)
    _, bt, bb = row(pg, GQ_LEAD, 57.6, 4.0, 17, 10.5, 'RGB(247,249,252)', x0=11, x1=89)
    line(pg, 50, bb, 50, 51.1)
    _, bt, bb = row(pg, GQ_DEPT, 48.0, 4.0, 12.6, 10, 'RGB(251,251,251)')
    line(pg, 50, bb, 50, 41.5)
    xs_team, bt_t, bb_t = row(pg, GQ_TEAM, 38.4, 4.0, 17, 10.5, 'RGB(232,238,248)', x0=11, x1=89)
    line(pg, 50, bb_t, 50, 31.9)
    row(pg, GQ_CLASS, 28.8, 4.0, 13, 10, 'RGB(255,255,255)', x0=10, x1=90, lower_bus=False)  # 最底排：不再收口
    rect(pg, 50, 19.6, 84, 6.2,
         '注：① 施工队按本标段实际设置的专业队伍划分 —— 例：土方队、桩基队、主体结构队、附属结构队，'
         '有盾构的加盾构掘进队、有桥梁的加桥梁作业队；每支队伍下设若干作业班组（图中班组为示例）。\n'
         '② 工区领导班子成员、部室设置按本次招标文件要求确定，招标文件没有的岗位不设。', fs=9.5)

    doc.SaveAs(VSDX)
    print('已保存:', VSDX)
    for i, p in enumerate(PNGS, start=1):
        doc.Pages.Item(i).Export(p)
        print('已导出:', p)
finally:
    if app is not None:
        try:
            app.Quit()
            print('Visio 已退出')
        except Exception as e:
            print('退出 Visio 失败:', e)
