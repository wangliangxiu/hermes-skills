# PyQt5 炮孔设计 3D可视化模式

## Matplotlib 3D嵌入PyQt5

```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')

class Mpl3DView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.fig = Figure(figsize=(5,4), dpi=100, facecolor='#1e1e28')
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#1e1e28')
```

## 绘制隧道炮孔3D

```python
# 画炮孔：从掌子面(0)向里延伸
for h in holes:
    x = [h['x'], h['x']]
    y = [h['y'], h['y']]
    z = [0, depth * 0.3]  # 深度简化
    ax.plot(x, y, z, color=c, linewidth=1.5, alpha=0.7)
    ax.scatter(h['x'], h['y'], 0, color=c, s=20)

# 画隧道轮廓
th = [math.radians(i) for i in range(0, 181, 5)]
tx = [r * math.cos(t) for t in th]
ty = [r * math.sin(t) for t in th]
ax.plot(tx, ty, 0, color='#64C8FF', linewidth=1.5, alpha=0.6)
```

## PyQt5 闪退排查清单

1. 删除 `ctypes.windll.shcore.SetProcessDpiAwareness(2)` — 这条在部分Windows版本上导致platform DLL加载失败
2. `drawText()` 所有坐标参数必须显式 `int()` 转换，不能依赖隐式转换
3. tkinter不支持8位RGB颜色码（如`#64C8FF99`），只能用6位（`#64C8FF`）
4. tkinter颜色码只能有6位（RRGGBB），不能带透明度（RRGGBBAA）

## 2D+3D分栏布局

```python
# 主窗口三栏布局
ml = QHBoxLayout()
ml.addWidget(参数面板, 1)    # 左
ml.addWidget(2D画布, 2)      # 中
ml.addWidget(3D视图, 2)      # 右
```
