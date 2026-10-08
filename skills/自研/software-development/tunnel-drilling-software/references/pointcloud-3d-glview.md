# 点云 3D 渲染——pyqtgraph GLViewWidget

## 用途

在 PyQt5 应用中嵌入交互式 3D 点云查看器，用于隧道掌子面激光扫描数据的可视化 + 超欠挖分析。

## 技术栈

- **PyQt5** — GUI 框架（已有）
- **PyOpenGL** — OpenGL 绑定（需额外安装：`pip install PyOpenGL PyOpenGL_accelerate`）
- **pyqtgraph.opengl** — GLViewWidget（pyqtgraph 自带，0.14.0+ 已验证）
- **numpy** — 点云数据处理（已有）

## 关键限制与设计原则

### ⚠️ 必须集成到主系统，不能单独开窗口

用户明确要求：**所有功能必须嵌入主系统的主窗口作为标签页**，不要另外启动一个独立窗口。

正确做法：
```python
# ✅ 在 MainWindow 的 QTabWidget 中加一个新 tab
self.cloud_panel = PointCloudPanel()
self.tabs.addTab(self.cloud_panel, '🎯 点云分析')
```

错误做法：
```python
# ❌ 不要另外启动一个 QApplication
app2 = QApplication(sys.argv)  
w2 = PointCloudViewer()
w2.show()
```

### 离线运行

GLViewWidget 的 3D 渲染完全本地运行，不依赖网络。点云数据由 numpy 加载，不存在云端处理。

### 性能

- 3 万点默认值，最高可到 20 万点
- 使用 `pxMode=True`（点大小以像素为单位，不随视角缩放变化）
- 点大小滑块范围 1~10

## 核心实现模式

### 1. 面板类结构

```python
from pyqtgraph.opengl import GLViewWidget, GLScatterPlotItem
import numpy as np

class PointCloudPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.points = None      # numpy array (N, 3)
        self.colors = None      # numpy array (N, 4) RGBA
        self.holes = []         # design hole positions
        self._setup()
    
    def _setup(self):
        layout = QHBoxLayout()
        # 左侧：GLViewWidget
        self.gl = GLViewWidget()
        self.gl.setBackgroundColor(QColor(20, 20, 30))
        self.gl.setCameraPosition(distance=12, elevation=25, azimuth=45)
        layout.addWidget(self.gl, 3)
        # 右侧：控制面板
        # ...
```

### 2. 点云渲染

```python
def _update(self):
    self.gl.clear()
    if self.points is None:
        return
    size = self.sl_size.value()
    # 添加点云散点图
    self.gl.addItem(GLScatterPlotItem(
        pos=self.points,
        color=self.colors,
        size=size,
        pxMode=True
    ))
    # 添加设计炮孔（用不同颜色的点）
    for h in self.holes:
        self.gl.addItem(GLScatterPlotItem(
            pos=np.array([h['pos']]),
            color=h['c'],
            size=8,
            pxMode=True
        ))
```

### 3. 颜色编码（超欠挖可视化）

| 偏差范围 | 颜色 | 含义 |
|:--------|:----|:-----|
| z ≤ -0.03m | 蓝色 [0.2, 0.5, 1.0] | 欠挖 |
| -0.03 < z ≤ 0.05 | 绿色 [0.3, 0.8, 0.3] | 合格 |
| 0.05 < z ≤ 0.15 | 橙色 [1.0, 0.7, 0.2] | 轻度超挖 |
| z > 0.15 | 红色 [1.0, 0.2, 0.2] | 严重超挖 |

### 4. 导入真实点云文件

支持 `.xyz` / `.txt` / `.csv` 格式（纯坐标文本，numpy.loadtxt 可读）：

```python
def _import(self):
    path, _ = QFileDialog.getOpenFileName(self, "导入", "", "点云(*.xyz *.txt *.csv)")
    if not path:
        return
    data = np.loadtxt(path, comments=['#', '//'])
    if data.shape[1] >= 3:
        self.points = data[:, :3]
        # 默认全部标为绿色
        self.colors = np.ones((len(data), 4)) * [0.3, 0.8, 0.3, 0.6]
        self._update()
```

### 5. 生成模拟点云（用于演示）

模拟隧道掌子面扫描数据，含超挖区域：

```python
def _gen_cloud(self):
    n = int(self.sp_pts.value())  # 默认 30000
    span = 6.0
    pts, cols = [], []
    # 模拟超挖区域
    overbreaks = [(1.5, 2.0, 0.6, 0.25), (-1.2, 1.5, 0.5, 0.18)]
    for _ in range(n):
        angle = random.uniform(-math.pi, math.pi)
        r = random.uniform(0, span/2) * math.sqrt(random.random())
        x = r*math.cos(angle)
        y = r*math.sin(angle) + 1.5
        z = random.gauss(0, 0.02)
        # 叠加超挖
        for sx, sy, sr, sev in overbreaks:
            d = math.sqrt((x-sx)**2 + (y-sy)**2)
            if d < sr:
                z = max(z, sev * (1 - d/sr))
        pts.append([x, y, z])
        # 颜色编码
        if z > 0.15: cols.append([1, 0.2, 0.2, 0.8])
        elif z > 0.05: cols.append([1, 0.7, 0.2, 0.7])
        elif z < -0.03: cols.append([0.2, 0.5, 1, 0.7])
        else: cols.append([0.3, 0.8, 0.3, 0.6])
    self.points = np.array(pts)
    self.colors = np.array(cols)
```

### 6. 实体表面模式（三角网格渲染）

除了点云模式，还支持通过三角剖分将点云渲染为**带颜色的实体三角网格表面**，视觉效果更接近 Revit/BIM。

需要额外依赖：`matplotlib.tri`（matplotlib 自带，无需额外安装）

#### 模式切换

在显示控制面板加一个 `QComboBox` 提供「点云模式」和「实体表面」切换：

```python
self.mode_combo = QComboBox()
self.mode_combo.addItems(['点云模式', '实体表面'])
self.mode_combo.currentTextChanged.connect(self._update)
```

#### 三角剖分实现

```python
import matplotlib.tri as mtri
from pyqtgraph.opengl import GLMeshItem, MeshData

def _render_mesh(self):
    pts = self.points
    # 对 XY 平面做 Delaunay 三角剖分
    tri = mtri.Triangulation(pts[:,0], pts[:,1])
    vertices = pts
    faces = tri.triangles

    # 每个三角面的平均 Z 值决定面颜色
    z_avg = np.mean(vertices[faces][:,:,2], axis=1)

    # 颜色映射（与点云一致）
    face_colors = np.zeros((len(faces), 4))
    for i, z in enumerate(z_avg):
        if z > 0.15:       face_colors[i] = [1.0, 0.2, 0.2, 0.7]  # 红-超挖
        elif z > 0.05:     face_colors[i] = [1.0, 0.7, 0.2, 0.7]  # 橙-轻度
        elif z < -0.03:    face_colors[i] = [0.2, 0.5, 1.0, 0.7]  # 蓝-欠挖
        else:              face_colors[i] = [0.3, 0.8, 0.3, 0.6]  # 绿-合格

    mesh_data = MeshData(vertexes=vertices, faces=faces, faceColors=face_colors)
    mesh_item = GLMeshItem(meshdata=mesh_data, smooth=False,
                           shader='shaded', glOptions='opaque')
    self.gl.addItem(mesh_item)
```

#### 性能注意

- 3 万点剖分产生约 6 万个三角面，现代 GPU 轻松处理
- `smooth=False` 保留三角面之间的棱角（显示单个面的偏差）
- `shader='shaded'` 启用基本光照，让表面有立体感
- 点大小滑块在实体表面模式下无效（不渲染点）

#### 混淆坑

- `matplotlib.tri.Triangulation` 要求 XY 输入**没有严格重复的点**。正常点云扫描数据有微小噪声，不会触发此问题
- `GLMeshItem` 的 `vertexes` 和 `faces` 必须用 **numpy 数组**，不能用 Python list
- 面颜色是 `(N_faces, 4)` 的 RGBA 数组，不是 `(N_vertices, 4)`
- 如果渲染后表面闪烁或部分透明，检查 `glOptions='opaque'` 参数

## 安装依赖

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

使用清华镜像加速：
```bash
pip install PyOpenGL PyOpenGL_accelerate -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 参考实现

完整代码见 `drill_design_v09.py` 中的 `PointCloudPanel` 类（集成版）。面板包含模式切换、点云渲染、三角网格渲染、设计炮孔叠加、设计轮廓线、实时统计面板。
