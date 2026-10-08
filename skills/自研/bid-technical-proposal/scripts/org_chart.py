# -*- coding: utf-8 -*-
"""投标文件组织机构框图生成器（示意样例，两张图）
 图1 项目部（总承包部）组织机构框图：
      项目名称 → 项目经理 → 领导班子 → 各部室 → 各工区（横向，有几个画几个）→
      每个工区下面纵向逐层：工区经理 → 工区领导班子 → 工区各部室 → 各施工队 → 各作业班组
 图2 工区项目部组织机构框图（工区内部详图，以一个工区为例）：
      工区经理 → 工区领导班子 → 工区各部室 → 各施工队（土方/桩基/主体/附属…）→ 各作业班组
改"可改参数"区即可复用。用法: python org_chart.py [输出目录]
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager

for f in ['msyh.ttc', 'simhei.ttf', 'simsun.ttc']:
    p = os.path.join(r'C:\Windows\Fonts', f)
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
        plt.rcParams['font.sans-serif'] = [font_manager.FontProperties(fname=p).get_name()]
        break
plt.rcParams['axes.unicode_minus'] = False

outdir = sys.argv[1] if len(sys.argv) > 1 else os.environ['LOCALAPPDATA'] + r'\Temp'
os.makedirs(outdir, exist_ok=True)

# ==================== 可改参数 ====================
PROJ = '××城际铁路××标段工程项目部'
LEAD = ['技术负责人\n（总工）', '安全负责人\n（安全总监）', '项目副经理', '总经济师', '总会计师', '总机械师']
DEPT = ['工程技术部', '安全质量部', '物资设备部', '计划合同部', '财务部', '综合办公室', '工地试验室', '测量队']
NGQ  = 6
CN   = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
GQ   = [f'第{CN[i]}工区' for i in range(NGQ)]

GQ_LEAD  = ['工区技术负责人', '工区安全负责人', '工区生产副经理', '工区综合管理员']
GQ_DEPT  = ['工程技术组', '安全质量组', '物资设备组', '计划财务组', '工地试验室', '综合办公室']
GQ_TEAM  = ['土方施工队', '桩基施工队', '主体结构施工队', '附属结构施工队']
GQ_CLASS = ['钢筋班', '模板班', '混凝土班', '防水班', '土方运输班', '装饰装修班']
# =================================================

EC, GAP = '#333333', 1.1

def box(ax, x, y, w, h, text, fs=10, bold=False, fc='#ffffff'):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h,
                 boxstyle='round,pad=0.0,rounding_size=0.35', linewidth=1.2,
                 edgecolor=EC, facecolor=fc))
    ax.text(x, y, text, ha='center', va='center', fontsize=fs,
            fontweight='bold' if bold else 'normal', linespacing=1.45)

def line(ax, x1, y1, x2, y2, dash=False):
    ax.plot([x1, x2], [y1, y2], color=EC, lw=1.1, solid_capstyle='butt',
            linestyle=(0, (3, 2)) if dash else 'solid')

def row(ax, items, y, h, w, fs, fc, x0=8, x1=92, bus=True):
    """一行：等距排开；每格竖线接到上方横线。返回 (x列表, 上方横线y)"""
    n = len(items)
    xs = [x0 + i * ((x1 - x0) / (n - 1)) for i in range(n)] if n > 1 else [(x0 + x1) / 2]
    bt = y + h/2 + GAP
    for x, t in zip(xs, items):
        box(ax, x, y, w, h, t, fs=fs, fc=fc)
        line(ax, x, bt, x, y + h/2)
    if bus:
        line(ax, xs[0], bt, xs[-1], bt)
    return xs, bt

# ============================ 图1：项目部（总承包部） ============================
fig, ax = plt.subplots(figsize=(16.5, 11.9))       # A3 横向
ax.set_xlim(0, 100); ax.set_ylim(0, 74); ax.axis('off')
ax.text(50, 71.8, '项目部组织机构框图（示意）', ha='center', fontsize=17, fontweight='bold')

box(ax, 50, 66.6, 56, 4.2, PROJ, fs=12.5, bold=True, fc='#e8eef8')   # 项目名称
line(ax, 50, 64.5, 50, 62.4)
box(ax, 50, 60.2, 20, 4.2, '项目经理', fs=12.5, bold=True, fc='#dce6f5')
line(ax, 50, 58.1, 50, 55.7)

_, bus_lead = row(ax, LEAD, 52.5, 4.2, 14.6, 9.5, '#f7f9fc')          # 领导班子
line(ax, 50, bus_lead, 50, 45.8)
_, bus_dep = row(ax, DEPT, 42.6, 4.2, 11.0, 9, '#fbfbfb', bus=False)  # 各部室
line(ax, 8, bus_dep, 92, bus_dep)
line(ax, 50, bus_dep, 50, 35.3)
xs_gq, bus_gq = row(ax, GQ, 32.1, 4.2, 14.6, 11, '#e8eef8', bus=False)  # 各工区横向
line(ax, 8, bus_gq, 92, bus_gq)

CHAIN = ['工区经理', '工区领导班子', '工区各部室', '各施工队', '各作业班组']
ys = [26.6 - i * 4.6 for i in range(len(CHAIN))]
for k, (name, y) in enumerate(zip(CHAIN, ys)):
    for x in xs_gq:
        box(ax, x, y, 14.6, 3.2, name, fs=9.5, fc='#eaf0fa' if k == 0 else '#ffffff')
        line(ax, x, (30.0 if k == 0 else ys[k-1] - 1.6), x, y + 1.6)
ax.text(50, 1.8, '说明：层级与岗位按本次招标文件要求与投标单位实际组织确定；没有的岗位不写；'
                 '不是总承包制就不出现"总承包部"；工区按招标文件划分的数量横向画（示意为 %d 个）；'
                 '工区内部各层详见图2。' % NGQ, ha='center', fontsize=9.5, color='#555555')
plt.tight_layout()
fig.savefig(os.path.join(outdir, '组织机构框图1_项目部.png'), dpi=200, bbox_inches='tight')
fig.savefig(os.path.join(outdir, '组织机构框图1_项目部.svg'), bbox_inches='tight')
print('出图: 组织机构框图1_项目部.png / .svg')

# ============================ 图2：工区项目部 ============================
fig2, ax2 = plt.subplots(figsize=(16.5, 11.9))
ax2.set_xlim(0, 100); ax2.set_ylim(0, 74); ax2.axis('off')
ax2.text(50, 71.8, '工区项目部组织机构框图（以第××工区为例，示意）', ha='center',
         fontsize=17, fontweight='bold')

box(ax2, 50, 66, 26, 4.2, '工区经理', fs=13, bold=True, fc='#dce6f5')
line(ax2, 50, 63.9, 50, 61.1)
_, bus = row(ax2, GQ_LEAD, 57.9, 4.2, 17, 10.5, '#f7f9fc', x0=11, x1=89)   # 工区领导班子
line(ax2, 50, bus, 50, 50.9)
_, bus = row(ax2, GQ_DEPT, 47.7, 4.2, 12.6, 10, '#fbfbfb')    # 工区各部室
line(ax2, 50, bus, 50, 41.3)

xs_team, bus_team = row(ax2, GQ_TEAM, 38.1, 4.2, 17, 10.5, '#e8eef8', x0=11, x1=89)  # 各施工队
line(ax2, 11, 35.0, 89, 35.0)                                    # 队伍下面的横线
for x in xs_team:
    line(ax2, x, 36.0, x, 35.0)
line(ax2, 50, 35.0, 50, 31.9)
row(ax2, GQ_CLASS, 28.5, 4.2, 13, 10, '#ffffff', x0=10, x1=90)   # 各作业班组
ax2.text(50, 21.0, '注：① 施工队按本标段实际设置的专业队伍划分 —— 例：土方队、桩基队、主体结构队、附属结构队，\n'
                   '有盾构的加盾构掘进队、有桥梁的加桥梁作业队；每支队伍下设若干作业班组（图中班组为示例）。\n'
                   '② 工区领导班子成员、部室设置按本次招标文件要求确定，招标文件没有的岗位不设。',
         ha='center', fontsize=10, color='#444444', linespacing=1.8)
plt.tight_layout()
fig2.savefig(os.path.join(outdir, '组织机构框图2_工区.png'), dpi=200, bbox_inches='tight')
fig2.savefig(os.path.join(outdir, '组织机构框图2_工区.svg'), bbox_inches='tight')
print('出图: 组织机构框图2_工区.png / .svg')
