# -*- coding: utf-8 -*-
"""按「章节细化表」结构，把 JSON 知识点数据写成 Excel 工作表（追加进已有工作簿）。

用法：
    python generate_chapter_sheets.py <配置文件.json>

配置文件（路径都用原生写法 C:/Users/...，不要用 bash 的 $HOME 展开）：
{
  "workbook_dir": "C:/Users/xxx/Desktop/备考计划",
  "backup_dir":   "C:/Users/xxx/AppData/Local/Temp/planwork/backup_original",
  "maps": [
    {"data": "C:/.../data_math.json",     "workbook": "01-数学一.xlsx", "subject": "数学一"},
    {"data": "C:/.../data_english.json",  "workbook": "02-英语一.xlsx", "subject": "英语一"}
  ],
  "index": {"workbook": "00-总表.xlsx", "sheet": "考研备考计划总表", "code_col": 2}
}

数据文件 schema：
{
  "subject": "数学一",
  "sheets": [
    {"id": "M8", "name": "无穷级数",
     "score": "选择或填空 1 题 + 解答 1 题，约 10—17 分",
     "order": "先定义与基本性质 → 正项级数判别法 → ……",
     "points": [{"no": 1, "point": "常数项级数收敛的定义", "req": "理解",
                 "freq": "高", "pass": "能给级数判敛散并说出依据", "note": "通项趋于 0 是必要非充分"}],
     "traps": ["调和级数发散但通项趋于 0"]}
  ]
}

注意：本脚本产出的是“约定结构 + 样式”，**首次用于一批新数据时要逐表核对**（表数、条数、章末区、跳转列、没有空表），
不要没看一眼就交付。
"""
import os, sys, json, shutil
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

# ---- 样式 ----
NAVY = PatternFill('solid', fgColor='1E3A5F')      # 已有工作簿的表头色；从零新建可换 1F4E79
LBLUE = PatternFill('solid', fgColor='D9E2F3')
YELLOW = PatternFill('solid', fgColor='FFF2CC')
F_HDR = Font(name='微软雅黑', size=11, bold=True, color='FFFFFF')
F_SUB = Font(name='微软雅黑', size=10.5, bold=True, color='1E3A5F')
F_BODY = Font(name='微软雅黑', size=10)
F_LINK = Font(name='微软雅黑', size=10, color='0563C1', underline='single')
SIDE = Side(style='thin', color='B4C6E7')
BORDER = Border(left=SIDE, right=SIDE, top=SIDE, bottom=SIDE)
CEN = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT = Alignment(horizontal='left', vertical='center', wrap_text=True)

HEADERS = ['序号', '知识点', '考纲要求', '真题频率', '掌握标志（能做什么题）', '完成✓', '完成日期', '备注']
WIDTHS = {'A': 6, 'B': 46, 'C': 10, 'D': 10, 'E': 44, 'F': 8, 'G': 12, 'H': 26}
USAGE = [
    ('第 1 步', '先看总表确认现在学哪一章（编号）', '总表'),
    ('第 2 步', '点「细化表」列的章名跳到该章的知识点清单', '总表'),
    ('第 3 步', '学完一条在「完成✓」里选 ✓，并填完成日期', '各章节表'),
    ('第 4 步', '「掌握标志」是自测标准：做不到就先别勾', '各章节表'),
    ('第 5 步', '章末「易错提醒」是本章最容易丢分的地方，考前只刷这些也行', '各章节表'),
    ('说明', '「考纲要求」用大纲原话：了解 < 理解 < 掌握 < 会', '各章节表'),
    ('说明', '「真题频率」高/中/低 是按历年真题出现次数给的，不是感觉', '各章节表'),
    ('红线', '知识点表只列要学什么，不代替做题；每章配套题至少过一遍', '各章节表'),
]


def style_cell(c, font=None, fill=None, align=None):
    if font:
        c.font = font
    if fill:
        c.fill = fill
    c.alignment = align or LEFT
    c.border = BORDER


def build_usage(wb, subject):
    title = '使用说明'
    if title in wb.sheetnames:
        del wb[title]
    ws = wb.create_sheet(title, 0)
    ws.merge_cells('A1:C1')
    c = ws['A1']
    c.value = '%s · 使用说明' % subject
    c.font = Font(name='微软雅黑', size=12, bold=True, color='FFFFFF')
    c.fill = NAVY
    c.alignment = CEN
    c.border = BORDER
    for i, h in enumerate(['步骤', '做什么', '在哪张表'], 1):
        style_cell(ws.cell(2, i, h), F_SUB, LBLUE, CEN)
    for r, (a, b, c3) in enumerate(USAGE, 3):
        ws.cell(r, 1, a)
        ws.cell(r, 2, b)
        ws.cell(r, 3, c3)
        style_cell(ws.cell(r, 1), F_BODY, None, CEN)
        style_cell(ws.cell(r, 2), F_BODY, None, LEFT)
        style_cell(ws.cell(r, 3), F_BODY, None, CEN)
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 74
    ws.column_dimensions['C'].width = 18
    ws.freeze_panes = 'A3'
    ws.row_dimensions[1].height = 24


def build_chapter(wb, subject, ch):
    title = ('%s %s' % (ch['id'], ch['name']))[:31]
    if title in wb.sheetnames:        # 可重复运行
        del wb[title]
    ws = wb.create_sheet(title)
    ws.merge_cells('A1:H1')
    t = ws['A1']
    t.value = '%s · %s %s' % (subject, ch['id'], ch['name'])
    if ch.get('score'):
        t.value += '　　（%s）' % ch['score']
    t.font = Font(name='微软雅黑', size=12, bold=True, color='FFFFFF')
    t.fill = NAVY
    t.alignment = CEN
    t.border = BORDER
    ws.row_dimensions[1].height = 26
    for i, h in enumerate(HEADERS, 1):
        style_cell(ws.cell(2, i, h), F_HDR, NAVY, CEN)
    ws.row_dimensions[2].height = 22
    r = 3
    for p in ch['points']:
        ws.cell(r, 1, p.get('no'))
        ws.cell(r, 2, p.get('point'))
        ws.cell(r, 3, p.get('req'))
        ws.cell(r, 4, p.get('freq'))
        ws.cell(r, 5, p.get('pass'))
        ws.cell(r, 6, None)
        ws.cell(r, 7, None)
        ws.cell(r, 8, p.get('note', ''))
        for col, al in ((1, CEN), (2, LEFT), (3, CEN), (4, CEN), (5, LEFT), (6, CEN), (7, CEN), (8, LEFT)):
            style_cell(ws.cell(r, col), F_BODY, YELLOW if col in (6, 7) else None, al)
        r += 1
    r += 1
    if ch.get('order'):
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
        c = ws.cell(r, 1, '学习顺序：' + ch['order'])
        c.font = F_SUB
        c.fill = LBLUE
        c.alignment = LEFT
        c.border = BORDER
        ws.row_dimensions[r].height = 20
        r += 1
    if ch.get('traps'):
        r += 1
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
        c = ws.cell(r, 1, '易错提醒（考前重点看这几条）')
        c.font = F_HDR
        c.fill = NAVY
        c.alignment = CEN
        c.border = BORDER
        r += 1
        for i, tp in enumerate(ch['traps'], 1):
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
            c = ws.cell(r, 1, '%d. %s' % (i, tp))
            c.font = F_BODY
            c.fill = YELLOW
            c.alignment = LEFT
            c.border = BORDER
            ws.row_dimensions[r].height = 18
            r += 1
    for col, w in WIDTHS.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = 'A3'
    dv = DataValidation(type='list', formula1='"✓,×"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add('F3:F%d' % max(3, r))


def add_index_links(path, sheet_name, owner, code_col=2):
    """总表加「细化表（点章名跳转）」列：owner = {章号: (工作簿文件名, 表名, 本章分值)}

    已有行只补链接；总表里没有的章号（如新拆出的章节）自动追加一行，避免“新表没登记”。
    """
    wb = openpyxl.load_workbook(path)
    ws = wb[sheet_name]
    col = ws.max_column + 1 if ws.cell(1, ws.max_column).value else ws.max_column
    for r in range(1, ws.max_row + 1):
        ws.cell(r, col).value = None
        ws.cell(r, col).hyperlink = None
    c = ws.cell(1, col, '细化表（点章名跳转）')
    style_cell(c, F_HDR, NAVY, CEN)
    n = 0
    seen = set()
    for r in range(2, ws.max_row + 1):
        b = ws.cell(r, code_col).value
        if not b:
            continue
        code = str(b).split(' ')[0].strip()
        if code in owner:
            wbf, sheet_title, _score = owner[code]
            cell = ws.cell(r, col, sheet_title)
            cell.hyperlink = "%s#'%s'!A1" % (wbf, sheet_title)
            cell.font = F_LINK
            cell.alignment = CEN
            cell.border = BORDER
            seen.add(code)
            n += 1
    # 补齐总表里没有的章号
    r = ws.max_row + 1
    while r > 2 and not ws.cell(r - 1, code_col).value:
        r -= 1
    for code, (wbf, sheet_title, score) in owner.items():
        if code in seen:
            continue
        ws.cell(r, 1, wbf.split('-')[-1].split('.')[0])   # 阶段列：数学一/英语一/…
        ws.cell(r, code_col, sheet_title)
        ws.cell(r, code_col + 2, score or '')
        cell = ws.cell(r, col, sheet_title)
        cell.hyperlink = "%s#'%s'!A1" % (wbf, sheet_title)
        for i in range(1, col + 1):
            cc = ws.cell(r, i)
            cc.border = BORDER
            cc.alignment = CEN if i != code_col + 2 else LEFT
            cc.font = F_LINK if i == col else F_BODY
        n += 1
    wb.save(path)
    return n


def main():
    cfg = json.load(open(sys.argv[1], encoding='utf-8'))
    wdir = cfg['workbook_dir']
    bdir = cfg.get('backup_dir')
    if bdir:
        os.makedirs(bdir, exist_ok=True)
        for fn in os.listdir(wdir):
            if fn.endswith('.xlsx'):
                shutil.copy2(os.path.join(wdir, fn), os.path.join(bdir, fn))
        print('原件已备份到', bdir)
    data, owner = {}, {}
    for m in cfg['maps']:
        d = json.load(open(m['data'], encoding='utf-8'))
        data[m['workbook']] = (m['subject'], d, m)
        for ch in d['sheets']:
            owner[ch['id']] = (m['workbook'], ('%s %s' % (ch['id'], ch['name']))[:31],
                               ch.get('score', ''))
    for wbf, (subject, d, m) in data.items():
        path = os.path.join(wdir, wbf)
        wb = openpyxl.load_workbook(path)
        build_usage(wb, subject)
        for ch in d['sheets']:
            build_chapter(wb, subject, ch)
        wb.save(path)
        print('%-16s 新增/更新 %d 张章节表，%d 条知识点' %
              (wbf, len(d['sheets']), sum(len(c['points']) for c in d['sheets'])))
    idx = cfg.get('index')
    if idx:
        n = add_index_links(os.path.join(wdir, idx['workbook']), idx['sheet'], owner,
                            idx.get('code_col', 2))
        print('总表：加跳转列 %d 条' % n)


if __name__ == '__main__':
    main()
