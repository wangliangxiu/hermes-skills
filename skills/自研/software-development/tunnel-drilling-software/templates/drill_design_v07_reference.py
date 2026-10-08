# -*- coding: utf-8 -*-
"""
智能炮孔设计系统 v0.7 完整源码（移植版）
—— 2D布孔图 + matplotlib 3D模型
用于 skill 快速搭建新项目时参考
"""

import sys, math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox,
    QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')


class HoleCanvas(QWidget):
    """2D断面布孔图画布"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.span = 6.0
        self.holes = []
        self.hole_colors = {
            '掏槽眼': QColor(255,80,80), '辅助眼': QColor(255,180,50),
            '周边眼': QColor(50,200,50), '底板眼': QColor(80,80,255),
        }
        
    def plot(self, span, holes):
        self.span = span
        self.holes = holes
        self.update()
        
    def paintEvent(self, ev):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(30,30,40))
        cx, cy = w//2, h//2
        r = min(w,h)//2 - 40
        
        p.setPen(QPen(QColor(50,50,60),1,Qt.DotLine))
        for i in range(0, w, 20): p.drawLine(i,0,i,h)
        for i in range(0, h, 20): p.drawLine(0,i,w,i)
        
        p.setPen(QPen(QColor(100,200,255),2))
        p.setBrush(QBrush(QColor(40,50,60,100)))
        p.drawEllipse(cx-r, cy-r, r*2, r*2)
        
        p.setPen(QPen(QColor(80,160,200),1,Qt.DashLine))
        p.drawLine(cx-r-10, cy, cx+r+10, cy)
        p.drawLine(cx, cy-r-10, cx, cy+r+10)
        
        scale = r / (self.span/2)
        for hole in self.holes:
            px = int(cx + hole['x'] * scale)
            py = int(cy + hole['y'] * scale)
            color = self.hole_colors.get(hole['type'], QColor(200,200,200))
            p.setPen(QPen(color,2))
            p.setBrush(QBrush(QColor(color.red(),color.green(),color.blue(),120)))
            p.drawEllipse(px-5, py-5, 10, 10)
            p.setPen(QPen(color,4))
            p.drawPoint(px, py)
        
        p.setFont(QFont('微软雅黑',9))
        for i,(name,color) in enumerate(self.hole_colors.items()):
            y = 20 + i*20
            p.fillRect(10, y, 10, 10, color)
            p.setPen(QColor(200,200,200))
            p.drawText(25, y+9, name)


class Mpl3DView(QWidget):
    """matplotlib 3D视图"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        self.fig = Figure(figsize=(5,4), dpi=100, facecolor='#1e1e28')
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#1e1e28')
        self.span = 6.0; self.holes = []
        
    def plot3d(self, span, holes):
        self.span = span; self.holes = holes
        self.ax.clear()
        self.ax.set_facecolor('#1e1e28')
        r = span / 2
        colors_map = {'掏槽眼':'#FF5050','辅助眼':'#FFB432','周边眼':'#32C832','底板眼':'#5050FF'}
        for h in holes:
            c = colors_map.get(h['type'], '#888888')
            depth = h.get('depth', 3.0)
            x = [h['x'], h['x']]
            y = [h['y'], h['y']]
            z = [0, depth * 0.3]
            self.ax.plot(x, y, z, color=c, linewidth=1.5, alpha=0.7)
            self.ax.scatter(h['x'], h['y'], 0, color=c, s=20)
        # 隧道轮廓
        th = [math.radians(i) for i in range(0, 181, 5)]
        tx = [r * math.cos(t) for t in th]
        ty = [r * math.sin(t) for t in th]
        self.ax.plot(tx, ty, 0, color='#64C8FF', linewidth=1.5, alpha=0.6)
        self.ax.plot(tx, ty, 3, color='#64C8FF', linewidth=1.5, alpha=0.3, linestyle='--')
        for i in range(0, len(th), 4):
            self.ax.plot([tx[i],tx[i]],[ty[i],ty[i]],[0,3], color='#64C8FF', lw=0.5, alpha=0.2)
        # 底板
        bx = [r*math.cos(t) for t in [math.radians(90), math.radians(270)]]
        by = [r*math.sin(t) for t in [math.radians(90), math.radians(270)]]
        self.ax.plot(bx, by, 0, color='#64C8FF', lw=1, alpha=0.4)
        # 视角
        self.ax.set_xlim(-r*1.3, r*1.3)
        self.ax.set_ylim(-r*1.3, r*1.3)
        self.ax.set_zlim(0, 4)
        self.ax.view_init(elev=25, azim=-60)
        self.fig.tight_layout()
        self.canvas.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('炮孔设计 v0.7 - 2D+3D')
        self.setMinimumSize(1400, 700)
        cw = QWidget(); self.setCentralWidget(cw)
        ml = QHBoxLayout(cw)
        # 参数面板（简化）
        pp = QWidget(); pl = QVBoxLayout(pp)
        self.span_sb = QDoubleSpinBox(); self.span_sb.setRange(2,20); self.span_sb.setValue(6.0)
        pl.addWidget(QLabel('跨度:')); pl.addWidget(self.span_sb)
        self.hc = HoleCanvas(); self.m3d = Mpl3DView()
        btn = QPushButton('生成'); btn.clicked.connect(self.update_all)
        pl.addWidget(btn)
        ml.addWidget(pp, 1); ml.addWidget(self.hc, 2); ml.addWidget(self.m3d, 2)
        self.update_all()
        
    def update_all(self):
        span = self.span_sb.value()
        holes = []
        for i in range(8):  # 示例掏槽眼
            a = math.radians(i*45)
            holes.append({'x':0.6*math.cos(a),'y':0.6*math.sin(a),'type':'掏槽眼','depth':3})
        r = span/2
        for i in range(13):  # 示例周边眼
            a = math.radians(i*15-90)
            holes.append({'x':r*math.cos(a),'y':r*math.sin(a),'type':'周边眼','depth':3})
        self.hc.plot(span, holes)
        self.m3d.plot3d(span, holes)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec_())
